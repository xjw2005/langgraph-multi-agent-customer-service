from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from core.states import CustomerServiceState, Intent, AgentType, ConversationStage
from config.settings import settings
import json
import re

class RouterAgent:
    """路由Agent - 负责意图识别和Agent选择"""

    def __init__(self):
        self.model = init_chat_model(
            model=settings.OPENAI_MODEL,
            model_provider="openai",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            max_retries=settings.MAX_RETRIES,
        )

    def route_message(self, state: CustomerServiceState) -> Dict[str, Any]:
        """路由用户消息到合适的Agent"""
        print("🧭 路由Agent开始分析用户意图...")

        messages = state.get("messages", [])
        if not messages:
            return self._handle_greeting(state)

        last_message = messages[-1]
        user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)

        # 意图识别
        intent_result = self._identify_intent(user_message, state)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]

        print(f"🎯 识别意图: {intent} (置信度: {confidence:.2f})")

        # 选择合适的Agent
        selected_agent = self._select_agent(intent)

        # 更新处理步骤
        processing_steps = state.get("processing_steps", [])
        processing_steps.append(f"路由Agent: 识别意图为 {intent}, 选择 {selected_agent}")

        return {
            "current_intent": intent,
            "selected_agent": selected_agent,
            "routing_confidence": confidence,
            "conversation_stage": ConversationStage.PROCESSING,
            "processing_steps": processing_steps,
            "agent_chain": [AgentType.ROUTER]
        }

    def _identify_intent(self, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """识别用户意图"""

        # 构建上下文信息
        context = self._build_context(state)

        system_prompt = f"""
你是一个专业的客服意图识别专家。请分析用户消息，识别其真实意图。

可能的意图类型：
1. order_query - 订单查询（查询订单状态、物流、修改订单等）
2. product_info - 商品咨询（商品详情、价格、库存、推荐等）
3. refund_request - 退款申请（退货、换货、退款等）
4. payment_issue - 支付问题（支付失败、退款、账单等）
5. logistics_query - 物流查询（配送状态、地址修改、配送时间等）
6. complaint - 投诉建议（服务投诉、产品问题、建议等）
7. general_inquiry - 一般咨询（政策咨询、使用帮助等）
8. human_handoff - 人工服务（明确要求人工客服）

上下文信息：
{context}

用户消息："{user_message}"

请返回严格的JSON格式：
{{
    "intent": "意图类型",
    "confidence": 0.0-1.0,
    "reasoning": "判断理由",
    "extracted_entities": {{
        "order_id": "订单号（如果有）",
        "product_name": "商品名称（如果有）",
        "amount": "金额（如果有）"
    }}
}}
"""

        try:
            response = self.model.invoke([HumanMessage(content=system_prompt)])
            result = json.loads(response.content)

            # 验证结果
            if result["intent"] not in [Intent.ORDER_QUERY, Intent.PRODUCT_INFO, Intent.REFUND_REQUEST,
                                      Intent.PAYMENT_ISSUE, Intent.LOGISTICS_QUERY, Intent.COMPLAINT,
                                      Intent.GENERAL_INQUIRY, Intent.HUMAN_HANDOFF]:
                result["intent"] = Intent.GENERAL_INQUIRY
                result["confidence"] = 0.5

            return result

        except Exception as e:
            print(f"❌ 意图识别失败: {e}")
            return {
                "intent": Intent.GENERAL_INQUIRY,
                "confidence": 0.3,
                "reasoning": "意图识别失败，使用默认意图",
                "extracted_entities": {}
            }

    def _select_agent(self, intent: str) -> str:
        """根据意图选择合适的Agent"""
        agent_mapping = {
            Intent.ORDER_QUERY: AgentType.ORDER,
            Intent.PRODUCT_INFO: AgentType.PRODUCT,
            Intent.REFUND_REQUEST: AgentType.REFUND,
            Intent.PAYMENT_ISSUE: AgentType.PAYMENT,
            Intent.LOGISTICS_QUERY: AgentType.LOGISTICS,
            Intent.COMPLAINT: AgentType.HUMAN,
            Intent.GENERAL_INQUIRY: AgentType.PRODUCT,  # 默认商品Agent处理一般咨询
            Intent.HUMAN_HANDOFF: AgentType.HUMAN,
        }

        return agent_mapping.get(intent, AgentType.PRODUCT)

    def _build_context(self, state: CustomerServiceState) -> str:
        """构建上下文信息"""
        context_parts = []

        # 用户信息
        if state.get("user_profile"):
            context_parts.append(f"用户信息: {state['user_profile']}")

        # 历史对话
        messages = state.get("messages", [])
        if len(messages) > 1:
            recent_messages = messages[-3:]  # 最近3条消息
            context_parts.append("最近对话:")
            for msg in recent_messages[:-1]:  # 排除当前消息
                role = "用户" if isinstance(msg, HumanMessage) else "客服"
                content = msg.content if hasattr(msg, 'content') else str(msg)
                context_parts.append(f"  {role}: {content}")

        # 当前业务数据
        if state.get("order_info"):
            context_parts.append(f"相关订单: {state['order_info']}")

        return "\n".join(context_parts) if context_parts else "无上下文信息"

    def _handle_greeting(self, state: CustomerServiceState) -> Dict[str, Any]:
        """处理初始问候"""
        return {
            "current_intent": Intent.GENERAL_INQUIRY,
            "selected_agent": AgentType.PRODUCT,
            "routing_confidence": 1.0,
            "conversation_stage": ConversationStage.GREETING,
            "processing_steps": ["路由Agent: 处理初始问候"],
            "agent_chain": [AgentType.ROUTER]
        }

    def should_escalate_to_human(self, state: CustomerServiceState) -> bool:
        """判断是否需要升级到人工客服"""

        # 检查置信度
        if state.get("routing_confidence", 1.0) < settings.DEFAULT_CONFIDENCE_THRESHOLD:
            return True

        # 检查处理结果
        if state.get("processing_confidence", 1.0) < settings.DEFAULT_CONFIDENCE_THRESHOLD:
            return True

        # 检查错误状态
        if state.get("error_message"):
            return True

        # 检查明确的人工请求
        if state.get("current_intent") == Intent.HUMAN_HANDOFF:
            return True

        # 检查复杂投诉
        if state.get("current_intent") == Intent.COMPLAINT:
            return True

        return False