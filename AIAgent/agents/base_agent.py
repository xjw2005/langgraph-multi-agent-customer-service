from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from core.states import CustomerServiceState
from config.settings import settings
import time

class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.model = init_chat_model(
            model=settings.OPENAI_MODEL,
            model_provider="openai",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            max_retries=settings.MAX_RETRIES,
        )

    @abstractmethod
    def process(self, state: CustomerServiceState) -> Dict[str, Any]:
        """处理用户请求的抽象方法"""
        pass

    def _record_processing_step(self, state: CustomerServiceState, step: str) -> list:
        """记录处理步骤"""
        processing_steps = state.get("processing_steps", [])
        processing_steps.append(f"{self.agent_name}: {step}")
        return processing_steps

    def _update_agent_chain(self, state: CustomerServiceState) -> list:
        """更新Agent调用链"""
        agent_chain = state.get("agent_chain", [])
        if self.agent_name not in agent_chain:
            agent_chain.append(self.agent_name)
        return agent_chain

    def _measure_performance(self, start_time: float) -> float:
        """测量处理性能"""
        return time.time() - start_time

    def _generate_response(self, system_prompt: str, user_context: str) -> str:
        """生成AI响应"""
        try:
            full_prompt = f"{system_prompt}\n\n用户情况：{user_context}"
            response = self.model.invoke([HumanMessage(content=full_prompt)])
            return response.content
        except Exception as e:
            print(f"❌ {self.agent_name} 生成响应失败: {e}")
            return f"抱歉，{self.agent_name}暂时无法处理您的请求，请稍后重试。"

    def _extract_user_message(self, state: CustomerServiceState) -> str:
        """提取用户消息"""
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            return last_message.content if hasattr(last_message, 'content') else str(last_message)
        return ""

    def _build_context_summary(self, state: CustomerServiceState) -> str:
        """构建上下文摘要"""
        context_parts = []

        # 用户信息
        user_id = state.get("user_id", "未知用户")
        context_parts.append(f"用户ID: {user_id}")

        # 当前意图
        intent = state.get("current_intent", "未知")
        context_parts.append(f"用户意图: {intent}")

        # 相关业务数据
        if state.get("order_info"):
            context_parts.append(f"订单信息: {state['order_info']}")

        if state.get("product_info"):
            context_parts.append(f"商品信息: {state['product_info']}")

        # 历史处理步骤
        processing_steps = state.get("processing_steps", [])
        if processing_steps:
            context_parts.append(f"处理历史: {'; '.join(processing_steps[-3:])}")  # 最近3步

        return "\n".join(context_parts)

    def _should_escalate(self, confidence: float) -> bool:
        """判断是否需要升级"""
        return confidence < settings.DEFAULT_CONFIDENCE_THRESHOLD

    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "error_message": error_msg,
            "requires_human": True,
            "processing_confidence": 0.0,
            "messages": [AIMessage(content=f"抱歉，处理您的请求时遇到问题：{error_msg}。正在为您转接人工客服。")]
        }