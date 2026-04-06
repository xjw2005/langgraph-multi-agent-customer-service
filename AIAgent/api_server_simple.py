# -*- coding: utf-8 -*-
# 简化版智能客服系统 - FastAPI后端服务

import sys
import os
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_server.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心组件
try:
    from agents.supervisor_agent import supervisor_app
    logger.info("✅ 成功导入supervisor_app")
except ImportError as e:
    logger.error(f"❌ 无法导入supervisor_app: {e}")
    supervisor_app = None

from langchain_core.messages import HumanMessage, AIMessage

# 创建FastAPI应用
app = FastAPI(title="智能客服系统", version="1.0.0")

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求开始
    logger.info(f"📥 收到请求: {request.method} {request.url}")

    # 如果是聊天请求，记录更多详情
    if request.url.path == "/chat":
        logger.info(f"💬 聊天请求 - 客户端IP: {request.client.host if request.client else 'unknown'}")

    response = await call_next(request)

    # 记录请求完成
    process_time = time.time() - start_time
    logger.info(f"📤 请求完成: {request.method} {request.url.path} - 状态码: {response.status_code} - 耗时: {process_time:.3f}s")

    return response

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✅ CORS中间件已配置")

# 挂载静态文件
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    logger.info(f"✅ 静态文件挂载成功: {static_path}")
else:
    logger.warning(f"⚠️ 静态文件目录不存在: {static_path}")

# 简单的请求模型
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    session_id: str = None

# 简单的响应模型
class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str = "success"

def extract_ai_response(result):
    """提取AI回复内容"""
    logger.debug(f"🔍 开始提取AI回复，result类型: {type(result)}")

    if not result:
        logger.warning("⚠️ result为空，返回默认回复")
        return "抱歉，我暂时无法回答您的问题。"

    if "messages" in result and len(result["messages"]) > 0:
        logger.debug(f"📝 找到 {len(result['messages'])} 条消息")
        last_msg = None
        for i, msg in enumerate(reversed(result["messages"])):
            if hasattr(msg, "content"):
                last_msg = msg.content
                logger.debug(f"✅ 找到AI回复内容 (消息索引: {len(result['messages'])-1-i})")
                break
            elif isinstance(msg, dict) and "content" in msg:
                last_msg = msg["content"]
                logger.debug(f"✅ 找到AI回复内容 (字典格式, 消息索引: {len(result['messages'])-1-i})")
                break

        if last_msg:
            logger.info(f"💬 AI回复内容: {last_msg[:100]}{'...' if len(last_msg) > 100 else ''}")
            return last_msg
        else:
            logger.warning("⚠️ 未找到有效的AI回复内容")

    logger.warning("⚠️ 无法提取AI回复，返回默认回复")
    return "抱歉，我暂时无法回答您的问题。"

@app.get("/")
async def root():
    """根路径 - 重定向到聊天界面"""
    return RedirectResponse(url="/static/index.html")

@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "message": "🍼 智能客服系统",
        "version": "1.0.0",
        "status": "运行中",
        "supervisor_available": supervisor_app is not None
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"💬 收到聊天请求 - 用户ID: {request.user_id}, 消息: {request.message[:50]}{'...' if len(request.message) > 50 else ''}")

    try:
        if not supervisor_app:
            logger.error("❌ supervisor_app不可用")
            return ChatResponse(
                response="系统暂时不可用，请稍后重试。",
                session_id=request.session_id or f"session_{request.user_id}",
                status="error"
            )

        # 生成会话ID
        session_id = request.session_id or f"session_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.debug(f"🔑 会话ID: {session_id}")

        # 构建状态
        state = {
            "messages": [HumanMessage(content=request.message)],
            "user_name": "用户",
            "user_id": request.user_id,
            "session_id": session_id,
            "message_count": 0,
            "learned_facts": [],
            "preferences": {}
        }
        logger.debug(f"📋 构建状态完成，消息数量: {len(state['messages'])}")

        # 调用supervisor系统
        logger.info("🤖 调用supervisor系统处理请求...")
        config = {"configurable": {"thread_id": session_id}}
        result = supervisor_app.invoke(state, config=config)
        logger.info("✅ supervisor系统处理完成")

        # 提取回复
        response_text = extract_ai_response(result)

        logger.info(f"🎯 聊天处理成功 - 会话ID: {session_id}")
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            status="success"
        )

    except Exception as e:
        logger.error(f"❌ 聊天处理错误: {e}", exc_info=True)
        return ChatResponse(
            response=f"处理消息时出现错误: {str(e)}",
            session_id=request.session_id or f"session_{request.user_id}",
            status="error"
        )

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "supervisor_available": supervisor_app is not None
    }

if __name__ == "__main__":
    logger.info("🚀 启动简化版智能客服系统...")
    logger.info(f"📊 系统状态:")
    logger.info(f"  - Supervisor可用: {supervisor_app is not None}")
    logger.info(f"  - 静态文件路径: {static_path}")
    logger.info(f"  - 日志文件: api_server.log")
    logger.info("🌐 服务器将在 http://0.0.0.0:8001 启动")
    uvicorn.run(app, host="0.0.0.0", port=8001)