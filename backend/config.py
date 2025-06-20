import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件
load_dotenv()

# Get project root directory (parent of backend directory)
PROJECT_ROOT = Path(__file__).parent.parent

class Settings:
    """应用配置设置"""
    
    # API 设置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Storage settings
    STORAGE_ROOT: Path = Path(os.getenv("STORAGE_ROOT", str(PROJECT_ROOT / "data" / "llm_logs")))
    
    # 模型设置
    #测试过程中，便宜考虑用这个flash
    # MODEL_ID: str = os.getenv("MODEL_ID", "google/gemini-2.5-flash-preview-05-20")
    # 生成可以用 pro
    MODEL_ID: str = os.getenv("MODEL_ID", "google/gemini-2.5-pro-preview")
    
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    API_KEY: str = os.getenv("API_KEY")
    
    # MCP 设置
    MCP_ACCESS_TOKEN: str = os.getenv("MCP_ACCESS_TOKEN")
    
    # Supabase 设置
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") 
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")  # 用于服务端操作
    
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
    AGENT_TIMEOUT: float = float(os.getenv("AGENT_TIMEOUT", "480.0"))
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))  # Agent最大迭代次数

settings = Settings() 