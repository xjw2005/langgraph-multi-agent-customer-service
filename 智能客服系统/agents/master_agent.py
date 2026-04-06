# -*- coding: utf-8 -*-
# MasterAgent兼容层 - 为了兼容CustomerServiceSystem
# 实际功能由supervisor_agent提供

from typing import Dict, Any

class MasterAgent:
    """MasterAgent兼容类，实际功能由supervisor_agent提供"""

    def __init__(self):
        self.name = "MasterAgent"
        print("⚠️ MasterAgent兼容层已加载，实际功能由supervisor_agent提供")

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求的兼容方法"""
        return {
            "response": "请使用supervisor_agent系统进行处理",
            "agent_used": "master_agent_compat",
            "confidence": 0.5,
            "requires_human": False
        }

    def classify_intent(self, message: str) -> Dict[str, Any]:
        """意图分类兼容方法"""
        return {
            "intent": "general",
            "confidence": 0.5,
            "category": "unknown"
        }