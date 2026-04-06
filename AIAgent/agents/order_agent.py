# -*- coding: utf-8 -*-
# Order Agent兼容层

from typing import Dict, Any

class OrderAgent:
    """订单处理Agent兼容类"""

    def __init__(self):
        self.name = "OrderAgent"
        print("⚠️ OrderAgent兼容层已加载")

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理订单相关请求"""
        return {
            "response": "订单处理功能暂时不可用",
            "agent_used": "order_agent_compat",
            "confidence": 0.5
        }