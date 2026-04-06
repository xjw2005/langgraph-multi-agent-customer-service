# -*- coding: utf-8 -*-
# QA Agent兼容层

from typing import Dict, Any

class ProfessionalQAAgent:
    """专业问答Agent兼容类"""

    def __init__(self):
        self.name = "ProfessionalQAAgent"
        print("⚠️ ProfessionalQAAgent兼容层已加载")

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理专业问答请求"""
        return {
            "response": "请使用qa_worker系统进行专业问答",
            "agent_used": "qa_agent_compat",
            "confidence": 0.5
        }