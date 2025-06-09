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
    MODEL_ID: str = os.getenv("MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3")
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    API_KEY: str = os.getenv("api_key")
    
    # CORS 设置
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # 日志设置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Agent 设置
    MAX_RESPONSE_LENGTH: int = int(os.getenv("MAX_RESPONSE_LENGTH", "2000"))
    STREAM_DELAY: float = float(os.getenv("STREAM_DELAY", "0.2"))

settings = Settings() 