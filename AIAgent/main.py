from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
from core.main_graph import CustomerServiceSystem

# 初始化数据
def initialize_system_data():
    """初始化系统数据"""
    try:
        # 初始化知识库
        if os.path.exists("init_knowledge.py"):
            print("🧠 初始化知识库...")
            from init_knowledge import initialize_baby_knowledge
            initialize_baby_knowledge()

        # 初始化商品数据
        if os.path.exists("init_products.py"):
            print("🛍️ 初始化商品数据...")
            from init_products import initialize_product_database
            initialize_product_database()

        print("✅ 系统数据初始化完成")
    except Exception as e:
        print(f"⚠️ 数据初始化失败: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="母婴智能客服系统",
    description="基于LangGraph的母婴智能客服API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化系统数据
initialize_system_data()

# 初始化客服系统
cs_system = CustomerServiceSystem()

# 请求模型
class ChatMessage(BaseModel):
    user_id: str = "user_001"
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: Optional[str] = None
    agent_used: Optional[str] = None
    confidence: Optional[float] = None
    requires_human: bool = False
    processing_time: Optional[float] = None
    processing_steps: Optional[List[str]] = None
    products: Optional[List[Dict[str, Any]]] = None

# API路由
@app.get("/")
async def root():
    return {"message": "母婴智能客服系统API", "status": "运行中"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "system": "母婴智能客服系统"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """处理聊天消息"""
    try:
        result = cs_system.process_message(
            user_id=message.user_id,
            message=message.message,
            session_id=message.session_id
        )

        return ChatResponse(
            response=result.get("response", ""),
            session_id=result.get("session_id", ""),
            intent=result.get("intent"),
            agent_used=result.get("agent_used"),
            confidence=result.get("confidence"),
            requires_human=result.get("requires_human", False),
            processing_time=result.get("processing_time"),
            processing_steps=result.get("processing_steps", []),
            products=result.get("products", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """获取聊天历史"""
    try:
        history = cs_system.get_conversation_history(session_id)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@app.post("/api/chat/continue/{session_id}")
async def continue_chat(session_id: str, user_input: Optional[str] = None):
    """继续中断的对话"""
    try:
        result = cs_system.continue_conversation(session_id, user_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"继续对话失败: {str(e)}")

@app.get("/api/system/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        stats = cs_system.get_system_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

# 静态文件服务（如果需要）
if os.path.exists("frontend/build"):
    app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )