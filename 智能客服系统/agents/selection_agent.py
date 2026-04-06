# -*- coding: utf-8 -*-
# Selection Agent兼容层

from typing import Dict, Any

class SelectionAgent:
    """商品选择Agent兼容类"""

    def __init__(self):
        self.name = "SelectionAgent"
        print("⚠️ SelectionAgent兼容层已加载")

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理商品选择请求"""
        return {
            "response": "请使用product_recommendation_worker系统进行商品推荐",
            "agent_used": "selection_agent_compat",
            "confidence": 0.5
        }