# -*- coding: utf-8 -*-
# Product Agent兼容层

from typing import Dict, Any

class ProductAgent:
    """商品Agent兼容类"""

    def __init__(self):
        self.name = "ProductAgent"
        print("⚠️ ProductAgent兼容层已加载")

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理商品相关请求"""
        return {
            "response": "请使用product_recommendation_worker系统进行商品查询",
            "agent_used": "product_agent_compat",
            "confidence": 0.5
        }