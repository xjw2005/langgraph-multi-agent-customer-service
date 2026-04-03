import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    """系统配置类"""

    # OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 数据库配置
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/customer_service.db")

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/customer_service.log")

    # 系统配置
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
    DEFAULT_CONFIDENCE_THRESHOLD = float(os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "0.7"))
    ENABLE_HUMAN_HANDOFF = os.getenv("ENABLE_HUMAN_HANDOFF", "true").lower() == "true"

    # Agent 配置
    AGENT_TIMEOUT = 30  # 秒
    MAX_RETRIES = 3

    # 意图识别配置
    INTENT_CONFIDENCE_THRESHOLD = 0.8

    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")

        # 创建必要的目录
        os.makedirs(os.path.dirname(cls.DATABASE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)

# 全局配置实例
settings = Settings()