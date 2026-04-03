from typing import Dict, Any
from langchain_core.messages import AIMessage
from agents.base_agent import BaseAgent
from core.states import CustomerServiceState, AgentType
from services.database_service import DatabaseService
import json
import time

class OrderAgent(BaseAgent):
    """订单处理Agent"""

    def __init__(self):
        super().__init__(AgentType.ORDER)
        self.db_service = DatabaseService()

    def process(self, state: CustomerServiceState) -> Dict[str, Any]:
        """处理订单相关请求"""
        start_time = time.time()
        print(f"📦 {self.agent_name} 开始处理订单请求...")

        try:
            user_message = self._extract_user_message(state)
            user_id = state.get("user_id")

            # 分析订单操作类型
            operation_type = self._analyze_order_operation(user_message)
            print(f"🔍 订单操作类型: {operation_type}")

            # 提取订单ID
            order_id = self._extract_order_id(user_message, state)

            # 根据操作类型处理
            if operation_type == "query":
                result = self._handle_order_query(order_id, user_id, state)
            elif operation_type == "modify":
                result = self._handle_order_modify(order_id, user_id, user_message, state)
            elif operation_type == "cancel":
                result = self._handle_order_cancel(order_id, user_id, state)
            elif operation_type == "list":
                result = self._handle_order_list(user_id, state)
            else:
                result = self._handle_general_order_inquiry(user_message, user_id, state)

            # 记录性能
            processing_time = self._measure_performance(start_time)
            result["processing_time"] = processing_time

            # 更新处理步骤
            result["processing_steps"] = self._record_processing_step(
                state, f"完成订单{operation_type}操作，耗时{processing_time:.2f}秒"
            )
            result["agent_chain"] = self._update_agent_chain(state)

            return result

        except Exception as e:
            print(f"❌ 订单Agent处理失败: {e}")
            return self._create_error_response(f"订单处理失败: {str(e)}")

    def _analyze_order_operation(self, user_message: str) -> str:
        """分析订单操作类型"""
        message_lower = user_message.lower()

        if any(keyword in message_lower for keyword in ["查询", "查看", "状态", "进度", "怎么样"]):
            return "query"
        elif any(keyword in message_lower for keyword in ["修改", "更改", "改", "换"]):
            return "modify"
        elif any(keyword in message_lower for keyword in ["取消", "删除", "不要"]):
            return "cancel"
        elif any(keyword in message_lower for keyword in ["所有", "全部", "列表", "我的订单"]):
            return "list"
        else:
            return "general"

    def _extract_order_id(self, user_message: str, state: CustomerServiceState) -> str:
        """提取订单ID"""
        # 从消息中提取订单号
        import re
        order_pattern = r'(ORD\d+|订单号?\s*[：:]\s*(\w+)|\b\w{6,}\b)'
        matches = re.findall(order_pattern, user_message, re.IGNORECASE)

        if matches:
            # 取第一个匹配的订单号
            for match in matches:
                if isinstance(match, tuple):
                    order_id = match[0] or match[1]
                else:
                    order_id = match
                if order_id and len(order_id) >= 3:
                    return order_id.strip()

        # 从状态中获取
        if state.get("order_info", {}).get("order_id"):
            return state["order_info"]["order_id"]

        return ""

    def _handle_order_query(self, order_id: str, user_id: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理订单查询"""
        if not order_id:
            return self._request_order_id(state)

        # 查询订单信息
        order_info = self.db_service.get_order_by_id(order_id)
        if not order_info:
            response = f"抱歉，没有找到订单号 {order_id} 的相关信息。请检查订单号是否正确。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.8,
                "order_info": {"order_id": order_id, "status": "not_found"}
            }

        # 验证订单归属
        if order_info.get("user_id") != user_id:
            response = "抱歉，您只能查询自己的订单信息。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.9,
                "requires_human": True
            }

        # 获取物流信息
        logistics_info = self.db_service.get_logistics_by_order_id(order_id)

        # 生成详细响应
        response = self._generate_order_query_response(order_info, logistics_info)

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.95,
            "order_info": order_info,
            "logistics_info": logistics_info or {}
        }

    def _handle_order_modify(self, order_id: str, user_id: str, user_message: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理订单修改"""
        if not order_id:
            return self._request_order_id(state)

        order_info = self.db_service.get_order_by_id(order_id)
        if not order_info or order_info.get("user_id") != user_id:
            response = "抱歉，无法找到或修改该订单。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.8,
                "requires_human": True
            }

        # 检查订单状态是否允许修改
        if order_info.get("status") in ["已发货", "已完成", "已取消"]:
            response = f"订单 {order_id} 当前状态为 {order_info.get('status')}，无法修改。如需帮助，请联系人工客服。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.9,
                "requires_human": True
            }

        # 分析修改类型
        modify_type = self._analyze_modify_type(user_message)
        response = f"订单 {order_id} 当前状态为 {order_info.get('status')}，支持修改。关于{modify_type}修改，我正在为您转接专业客服处理。"

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.7,
            "requires_human": True,
            "order_info": order_info
        }

    def _handle_order_cancel(self, order_id: str, user_id: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理订单取消"""
        if not order_id:
            return self._request_order_id(state)

        order_info = self.db_service.get_order_by_id(order_id)
        if not order_info or order_info.get("user_id") != user_id:
            response = "抱歉，无法找到该订单。"
            return {
                "messages": [AIMessage(content=response)],
                "processingnfidence": 0.8
            }

        # 检查是否可以取消
        if order_info.get("status") in ["已发货", "已完成"]:
            response = f"订单 {order_id} 已经 {order_info.get('status')}，无法直接取消。请联系客服处理退货事宜。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.9,
                "requires_human": True
            }

        # 模拟取消订单
        success = self.db_service.update_order_status(order_id, "已取消")
        if success:
            response = f"订单 {order_id} 已成功取消。如果已经付款，退款将在3-5个工作日内到账。"
            confidence = 0.95
        else:
            response = f"订单 {order_id} 取消失败，请联系人工客服。"
            confidence = 0.6

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": confidence,
            "order_info": order_info,
            "requires_human": not success
        }

    def _handle_order_list(self, user_id: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理订单列表查询"""
        orders = self.db_service.get_orders_by_user_id(user_id)

        if not orders:
            response = "您暂时没有任何订单记录。"
            return {
                "messages": [AIMessage(content=response)],
                "processing_confidence": 0.9
            }

        # 生成订单列表响应
        response = self._generate_order_list_response(orders)

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.95,
            "order_info": {"orders": orders}
        }

    def _handle_general_order_inquiry(self, user_message: str, user_id: str, state: CustomerServiceState) -> Dict[str, Any]:
        """处理一般订单咨询"""
        system_prompt = """
你是专业的订单客服，请根据用户的问题提供帮助。

常见问题处理：
1. 如何下单 - 引导用户到商品页面
2. 订单支付 和流程
3. 订单政策 - 介绍退换货政策
4. 订单问题 - 提供解决方案或转人工

请提供专业、友好的回复。
"""

        context = self._build_context_summary(state)
        response = self._generate_response(system_prompt, f"用户问题: {user_message}\n{context}")

        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.8
        }

    def _request_order_id(self, state: CustomerServiceState) -> Dict[str, Any]:
        """请求用户提供订单号"""
        response = "请提供您的订单号，我来帮您查询订单信息。订单号通常以 ORD 开头，例如：ORD001。"
        return {
            "messages": [AIMessage(content=response)],
            "processing_confidence": 0.9
        }

    def _analyze_modify_type(self, user_message: str) -> str:
        """分析修改类型"""
        message_lower = user_message.lower()
        if "地址" in message_lower:
            return "收货地址"
        elif "数量" in message_lower:
            return "商品数量"
        elif "规格" in message_lower or "型号" in message_lower:
            return "商品规格"
        else:
            return "订单信息"

    def _generate_order_query_response(self, order_info: dict, logistics_info: dict) -> str:
        """生成订单查询响应"""
        response_parts = [
            f"📦 订单信息查询结果：",
            f"订单号：{order_info.get('order_id')}",
            f"商品：{order_info.get('product_name')} × {order_info.get('quantity')}",
            f"金额：¥{order_info.get('price')}",
            f"状态：{order_info.get('status')}",
            f"下单时间：{order_info.get('created_at')}"
        ]

        if logistics_info:
            response_parts.extend([
                "",
                "🚚 物流信息：",
                f"物流状态：{logistics_info.get('status')}",
                f"当前位置：{logistics_info.get('current_location')}",
                f"预计送达：{logistics_info.get('estimated_delivery')}"
            ])

        return "\n".join(response_parts)

    def _generate_order_list_response(self, orders: list) -> str:
        """生成订单列表响应"""
        response_parts = ["📋 您的订单列表："]

        for i, order in enumerate(orders[:5], 1):  # 最多显示5个订单
            response_parts.append(
                f"{i}. {order.get('order_id')} - {order.get('product_name')} "
                f"(¥{order.get('price')}) - {order.get('status')}"
            )

        if len(orders) > 5:
            response_parts.append(f"... 还有 {len(orders) - 5} 个订单")

        response_parts.append("\n如需查询具体订单详情，请提供订单号。")
        return "\n".join(response_parts)