import os
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Settings:
    """应用配置设置"""
    
    # API 设置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 模型设置
    # MODEL_ID: str = os.getenv("MODEL_ID", "google/gemini-2.5-flash-preview-05-20")
    MODEL_ID: str = os.getenv("MODEL_ID", "google/gemini-2.5-pro-preview")
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    API_KEY: str = os.getenv("api_key")
    
    # MCP 设置
    MCP_ACCESS_TOKEN: str = os.getenv("MCP_ACCESS_TOKEN")
    
    # CORS 设置
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # 日志设置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 监控设置
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Customer-Success")
    PHOENIX_ENDPOINT: Optional[str] = os.getenv("PHOENIX_ENDPOINT")
    
    # Agent 设置
    MAX_RESPONSE_LENGTH: int = int(os.getenv("MAX_RESPONSE_LENGTH", "2000"))
    STREAM_DELAY: float = float(os.getenv("STREAM_DELAY", "0.2"))
    AGENT_TIMEOUT: float = float(os.getenv("AGENT_TIMEOUT", "120.0"))
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))  # Agent最大迭代次数

settings = Settings() 