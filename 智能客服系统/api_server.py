# -*- coding: utf-8 -*-
# 高端母婴智能客服系统 - FastAPI后端服务
# 基于LangGraph + RAG + 多Agent协作

import sys
import os

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import json
from datetime import datetime

# 导入现有的系统组件
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心系统
cs_system = None  # 全局变量，将在startup中初始化

# 导入新的 Supervisor + Worker 系统
try:
    from agents.supervisor_agent import supervisor_app
except ImportError as e:
    print(f"警告: 无法导入supervisor_app: {e}")
    supervisor_app = None

try:
    from agents.qa_worker import qa_worker_app
except ImportError as e:
    print(f"警告: 无法导入qa_worker_app: {e}")
    qa_worker_app = None

from langchain_core.messages import AIMessage, HumanMessage


def _looks_like_internal_worker_comment(s: str) -> bool:
    """判断是否为模型误输出的路由/worker 自我评价（不应展示给终端用户）。"""
    s = s.strip()
    if not s:
        return False
    markers = (
        "qa_worker",
        "product_recommendation_worker",
        "order_worker",
        "refund_worker",
        "payment_worker",
        "logistics_worker",
        "human_worker",
        "Worker能够",
        "分配给",
    )
    return any(m in s for m in markers)


def _strip_internal_preface_from_reply(text: str) -> str:
    """部分模型会把内部说明与正文用 --- 拼在同一字符串里，去掉前半段。"""
    text = text.strip()
    if not text:
        return text
    for sep in (" --- ", "\n---\n", "\n---\n\n"):
        if sep not in text:
            continue
        head, tail = text.split(sep, 1)
        head, tail = head.strip(), tail.strip()
        if tail and _looks_like_internal_worker_comment(head):
            return tail
    return text


def _extract_user_facing_reply(messages: List[Any]) -> Optional[str]:
    """从 LangGraph 的 messages 中取应展示给用户的助手正文。

    优先使用最后一条 AIMessage 的 `.text`（只拼接 type 为 text 的块），避免在 reasoning/thinking
    模型或块式 content 下把思维链误当作对用户回复；也不应简单取 `messages[-1]`（顺序不一定是助手最后说话）。
    """
    if not messages:
        return None
    for msg in reversed(messages):
        if not isinstance(msg, AIMessage):
            continue
        text = getattr(msg, "text", None)
        if text is not None:
            s = str(text).strip()
            if s:
                return _strip_internal_preface_from_reply(s)
        content = getattr(msg, "content", None)
        if isinstance(content, str) and content.strip():
            return _strip_internal_preface_from_reply(content.strip())
    return None

# 导入其他组件
from data.baby_products import ProductDatabase, ProductCategory

try:
    from rag.vector_store import BabyKnowledgeVectorStore
except ImportError as e:
    print(f"警告: 无法导入BabyKnowledgeVectorStore: {e}")
    BabyKnowledgeVectorStore = None

# 创建FastAPI应用
app = FastAPI(
    title="高端母婴智能客服系统",
    description="基于LangGraph + RAG + 多Agent协作的专业母婴客服API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"✅ 静态文件挂载成功: {static_dir}")
else:
    print(f"⚠️ static目录不存在: {static_dir}")

# 全局变量
product_db = None
vector_store = None

# 商品 JSON：与 api_server 同级的 data 目录（不依赖进程 cwd）
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_PRODUCT_JSON_FILES = (
    "extended_products.json",
    "products.json",
)


def _load_product_catalog(db: ProductDatabase) -> None:
    """从 data 目录加载商品 JSON（export_to_json / init_products_extended 格式）。"""
    loaded_any = False
    for name in _PRODUCT_JSON_FILES:
        path = os.path.join(_DATA_DIR, name)
        if not os.path.isfile(path):
            continue
        if db.load_from_json(path):
            loaded_any = True
    if not loaded_any:
        print(
            f"⚠️ 未找到商品数据文件，请将商品 JSON 放入: {_DATA_DIR} "
            f"（支持: {', '.join(_PRODUCT_JSON_FILES)}），或运行 init_products_extended.py 生成。"
        )

# 请求/响应模型
class ChatMessage(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    agent_used: str
    confidence: float
    requires_human: bool
    processing_time: float
    processing_steps: List[str]
    product_recommendations: Optional[List[Dict]] = None

class UserProfile(BaseModel):
    user_id: str
    baby_age_months: int
    feeding_type: str
    preferred_brands: List[str] = []
    budget_range: str = "中端"
    concerns: List[str] = []
    allergies: List[str] = []

class ProductQuery(BaseModel):
    category: Optional[str] = None
    age_months: Optional[int] = None
    budget_range: Optional[str] = None
    keywords: Optional[str] = None
    limit: int = 10

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化系统"""
    global product_db, vector_store, cs_system

    print("🚀 启动高端母婴智能客服系统...")

    try:
        # 初始化商品数据库（从 data/*.json 加载）
        product_db = ProductDatabase()
        _load_product_catalog(product_db)
        print("✅ 商品数据库初始化完成")

        # 初始化向量存储
        if BabyKnowledgeVectorStore:
            vector_store = BabyKnowledgeVectorStore()
            print("✅ 向量存储初始化完成")
        else:
            print("⚠️ 向量存储不可用")

        # 初始化核心系统（可选组件）
        try:
            # 尝试导入并初始化CustomerServiceSystem
            from core.main_graph import CustomerServiceSystem
            cs_system = CustomerServiceSystem()
            print("✅ 核心客服系统初始化完成")
        except ImportError as e:
            print(f"⚠️ 核心客服系统不可用（缺少依赖）: {e}")
            cs_system = None
        except Exception as e:
            print(f"⚠️ 核心客服系统初始化失败: {e}")
            cs_system = None

        print("🎉 系统启动完成！")
        if supervisor_app:
            print("✅ 使用 Supervisor + Worker 架构")
        else:
            print("⚠️ Supervisor 系统不可用，将使用降级模式")

    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        raise

# API路由

@app.get("/")
async def root():
    """根路径 - 重定向到聊天界面"""
    return RedirectResponse(url="/static/index.html")

@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "message": "🍼 高端母婴智能客服系统",
        "version": "1.0.0",
        "status": "运行中",
        "features": [
            "多Agent协作",
            "RAG知识问答",
            "智能商品推荐",
            "实时对话",
            "用户画像"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_ready": cs_system is not None
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """处理聊天消息 - 使用新的 Supervisor + Worker 系统"""
    try:
        # 使用新的 Supervisor 系统处理消息
        config = {"configurable": {"thread_id": message.session_id or f"session_{message.user_id}"}}

        # 构建状态
        state = {
            "messages": [HumanMessage(content=message.message)],
            "user_name": message.user_profile.get("name", "用户") if message.user_profile else "用户",
            "user_id": message.user_id,
            "session_id": message.session_id or f"session_{message.user_id}",
            "message_count": 0
        }

        # 如果有用户画像，添加到状态中
        if message.user_profile:
            # 提取用户事实
            facts = []
            if "baby_age_months" in message.user_profile:
                age = message.user_profile["baby_age_months"]
                facts.append(f"有一个{age}个月大的宝宝")
            if "feeding_type" in message.user_profile:
                facts.append(f"喂养方式: {message.user_profile['feeding_type']}")

            # 提取用户偏好
            preferences = {}
            if "preferred_brands" in message.user_profile:
                preferences["品牌偏好"] = ", ".join(message.user_profile["preferred_brands"])
            if "budget_range" in message.user_profile:
                preferences["预算范围"] = message.user_profile["budget_range"]

            state["learned_facts"] = facts
            state["preferences"] = preferences

        # 调用 Supervisor 系统
        if supervisor_app:
            result = supervisor_app.invoke(state, config=config)
        else:
            raise Exception("Supervisor系统不可用")

        # 提取响应（勿用 messages[-1]，以免取到非 AIMessage 或 reasoning 块）
        response_text = _extract_user_facing_reply(result.get("messages", [])) or "抱歉，我暂时无法回答您的问题。"

        # 构建响应
        return ChatResponse(
            response=response_text,
            session_id=config["configurable"]["thread_id"],
            intent=result.get("user_intent_analysis", {}).get("intent", "general"),
            agent_used=result.get("selected_worker", "supervisor"),
            confidence=result.get("user_intent_analysis", {}).get("confidence", 0.8),
            requires_human=result.get("requires_human", False),
            processing_time=0.0,  # 可以添加时间统计
            processing_steps=result.get("processing_steps", []),
            product_recommendations=None  # 可以后续添加商品推荐
        )

    except Exception as e:
        print(f"聊天处理错误: {e}")
        # 降级到原有系统
        if cs_system:
            try:
                result = cs_system.process_message(
                    user_id=message.user_id,
                    message=message.message,
                    session_id=message.session_id
                )

                return ChatResponse(
                    response=result["response"],
                    session_id=result["session_id"],
                    intent=result.get("intent", ""),
                    agent_used=result.get("agent_used", "fallback"),
                    confidence=result.get("confidence", 0.0),
                    requires_human=result.get("requires_human", False),
                    processing_time=result.get("processing_time", 0.0),
                    processing_steps=result.get("processing_steps", []),
                    product_recommendations=None
            )
            except:
                pass

        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")

@app.get("/products")
async def get_products(query: ProductQuery = None):
    """获取商品列表"""
    if not product_db:
        raise HTTPException(status_code=503, detail="商品数据库未就绪")

    try:
        # 构建搜索条件
        category = None
        if query and query.category:
            category_mapping = {cat.value: cat for cat in ProductCategory}
            category = category_mapping.get(query.category)

        # 搜索商品
        products = product_db.search_products(
            category=category,
            max_price=None  # 可以根据budget_range设置
        )

        # 转换为字典格式
        result = []
        for product in products[:query.limit if query else 10]:
            product_dict = product.to_dict()
            result.append(product_dict)

        return {
            "products": result,
            "total": len(result),
            "query": query.dict() if query else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取商品失败: {str(e)}")

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """获取单个商品详情"""
    if not product_db:
        raise HTTPException(status_code=503, detail="商品数据库未就绪")

    product = product_db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    return product.to_dict()

@app.post("/users/{user_id}/profile")
async def update_user_profile(user_id: str, profile: UserProfile):
    """更新用户画像"""
    # 这里可以保存到数据库
    # 暂时返回成功响应
    return {
        "message": "用户画像更新成功",
        "user_id": user_id,
        "profile": profile.dict()
    }

@app.get("/users/{user_id}/history")
async def get_user_history(user_id: str, limit: int = 20):
    """获取用户对话历史"""
    if not cs_system:
        raise HTTPException(status_code=503, detail="系统未就绪")

    try:
        # 获取用户对话摘要
        summary = cs_system.get_user_summary(user_id)
        return {
            "user_id": user_id,
            "summary": summary,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@app.get("/knowledge/search")
async def search_knowledge(q: str, domain: Optional[str] = None, limit: int = 5):
    """搜索知识库"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="知识库未就绪")

    try:
        results = vector_store.search(
            query=q,
            domain=domain,
            top_k=limit
        )

        return {
            "query": q,
            "domain": domain,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/chat/supervisor")
async def chat_supervisor_direct(message: ChatMessage):
    """直接使用 Supervisor 系统处理消息（测试端点）"""
    try:
        if not supervisor_app:
            return {"error": "Supervisor系统不可用", "type": "ImportError"}

        config = {"configurable": {"thread_id": message.session_id or f"session_{message.user_id}"}}

        state = {
            "messages": [HumanMessage(content=message.message)],
            "user_name": message.user_profile.get("name", "用户") if message.user_profile else "用户",
            "user_id": message.user_id,
            "session_id": message.session_id or f"session_{message.user_id}",
            "message_count": 0
        }

        # 调用 Supervisor 系统
        result = supervisor_app.invoke(state, config=config)

        return {
            "supervisor_result": {
                "selected_worker": result.get("selected_worker"),
                "is_completed": result.get("is_completed"),
                "learned_facts": result.get("learned_facts", []),
                "preferences": result.get("preferences", {}),
                "message_count": len(result.get("messages", [])),
                "context_summary": result.get("context_summary", "")
            },
            "response": _extract_user_facing_reply(result.get("messages", [])) or "无回复",
            "raw_result": str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
        }

    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/test/system")
async def test_system():
    """测试系统各组件状态"""
    status = {
        "supervisor_available": False,
        "qa_worker_available": False,
        "cs_system_available": cs_system is not None,
        "product_db_available": product_db is not None,
        "vector_store_available": vector_store is not None
    }

    # 测试 Supervisor
    try:
        if supervisor_app:
            _ = supervisor_app.invoke({
                "messages": [HumanMessage(content="测试")],
                "user_name": "测试用户",
                "user_id": "test",
                "session_id": "test_session",
                "message_count": 0
            }, config={"configurable": {"thread_id": "test"}})
            status["supervisor_available"] = True
            status["supervisor_test"] = "成功"
        else:
            status["supervisor_test"] = "Supervisor系统未导入"
    except Exception as e:
        status["supervisor_test"] = f"失败: {str(e)}"

    # 测试 QA Worker
    try:
        if qa_worker_app:
            _ = qa_worker_app.invoke({
                "messages": [HumanMessage(content="测试")],
                "user_name": "测试用户",
                "user_id": "test",
                "learned_facts": [],
                "preferences": {},
                "session_id": "test_session",
                "message_count": 0
            }, config={"configurable": {"thread_id": "qa_test"}})
            status["qa_worker_available"] = True
            status["qa_worker_test"] = "成功"
        else:
            status["qa_worker_test"] = "QA Worker系统未导入"
    except Exception as e:
        status["qa_worker_test"] = f"失败: {str(e)}"

    return status
    """获取系统统计信息"""
    stats = {}

    if cs_system:
        stats.update(cs_system.get_system_stats())

    if product_db:
        stats["total_products"] = len(product_db.products)
        stats["product_categories"] = len(product_db.category_index)

    if vector_store:
        stats["knowledge_stats"] = vector_store.get_all_stats()

    return stats

# WebSocket支持实时聊天
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket实时聊天"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 处理消息
            if supervisor_app:
                # 使用supervisor系统处理
                config = {"configurable": {"thread_id": f"ws_{user_id}"}}
                state = {
                    "messages": [HumanMessage(content=message_data["message"])],
                    "user_name": "用户",
                    "user_id": user_id,
                    "session_id": message_data.get("session_id", f"ws_{user_id}"),
                    "message_count": 0
                }

                try:
                    result = supervisor_app.invoke(state, config=config)
                    response_text = _extract_user_facing_reply(result.get("messages", [])) or "抱歉，我暂时无法回答您的问题。"

                    await manager.send_personal_message(
                        json.dumps({"response": response_text}, ensure_ascii=False),
                        user_id
                    )
                except Exception as e:
                    await manager.send_personal_message(
                        json.dumps({"error": f"处理失败: {str(e)}"}, ensure_ascii=False),
                        user_id
                    )
            elif cs_system:
                result = cs_system.process_message(
                    user_id=user_id,
                    message=message_data["message"],
                    session_id=message_data.get("session_id")
                )

                # 发送响应
                await manager.send_personal_message(
                    json.dumps(result, ensure_ascii=False),
                    user_id
                )
            else:
                await manager.send_personal_message(
                    json.dumps({"error": "系统未就绪"}, ensure_ascii=False),
                    user_id
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# 启动服务器
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )