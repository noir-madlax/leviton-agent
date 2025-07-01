"""Configuration management for Amazon Category Fetcher"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class CategoryFetcherConfig:
    """类别获取器配置"""
    
    # API配置
    RAINFOREST_API_KEY: str = os.getenv("RAINFOREST_API_KEY", "")
    RAINFOREST_API_URL: str = "https://api.rainforestapi.com/categories"
    
    # 项目路径配置
    PROJECT_ROOT = Path(__file__).parent.parent.parent  # backend目录
    SCRAPING_ROOT = PROJECT_ROOT / "scraping"
    CATEGORY_ROOT = SCRAPING_ROOT / "amazon-cat"
    DATA_ROOT = PROJECT_ROOT / "data" / "scraped" / "amazon" / "categories"
    
    # 数据存储路径
    RUNS_DIR = DATA_ROOT / "runs"
    CURRENT_RUN_LINK = DATA_ROOT / "current_run"
    RUNS_SUMMARY_FILE = DATA_ROOT / "runs_summary.txt"
    
    # 默认配置值
    DEFAULT_DOMAIN = "amazon.com"
    DEFAULT_API_DELAY = 1.0  # 秒
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_MAX_DEPTH = 10
    DEFAULT_SKIP_EXISTING = True
    
    # 进度文件名
    PROGRESS_FILE = "progress.txt"
    CONFIG_FILE = "config.json"
    LOG_FILE = "execution.log"
    RAW_API_DIR = "raw_api"
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # API限流配置
    MIN_API_DELAY = 0.5  # 最小延迟
    MAX_API_DELAY = 5.0  # 最大延迟
    
    # 文件大小限制 (MB)
    MAX_API_RESPONSE_SIZE = 10
    MAX_LOG_FILE_SIZE = 50
    
    @classmethod
    def ensure_directories(cls):
        """确保所有必要的目录存在"""
        dirs_to_create = [
            cls.DATA_ROOT,
            cls.RUNS_DIR,
        ]
        
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_run_directory(cls, run_id: str) -> Path:
        """获取运行目录路径"""
        return cls.RUNS_DIR / run_id
    
    @classmethod
    def get_raw_api_directory(cls, run_id: str) -> Path:
        """获取原始API响应目录路径"""
        return cls.get_run_directory(run_id) / cls.RAW_API_DIR
    
    @classmethod
    def get_progress_file_path(cls, run_id: str) -> Path:
        """获取进度文件路径"""
        return cls.get_run_directory(run_id) / cls.PROGRESS_FILE
    
    @classmethod
    def get_config_file_path(cls, run_id: str) -> Path:
        """获取配置文件路径"""
        return cls.get_run_directory(run_id) / cls.CONFIG_FILE
    
    @classmethod
    def get_log_file_path(cls, run_id: str) -> Path:
        """获取日志文件路径"""
        return cls.get_run_directory(run_id) / cls.LOG_FILE
    
    @classmethod
    def validate_api_key(cls) -> bool:
        """验证API密钥是否存在"""
        return bool(cls.RAINFOREST_API_KEY)
    
    @classmethod
    def get_supported_domains(cls) -> list:
        """获取支持的亚马逊域名列表"""
        return [
            "amazon.com",      # 美国
            "amazon.ca",       # 加拿大
            "amazon.co.uk",    # 英国
            "amazon.de",       # 德国
            "amazon.fr",       # 法国
            "amazon.es",       # 西班牙
            "amazon.it",       # 意大利
            "amazon.co.jp",    # 日本
            "amazon.com.au",   # 澳大利亚
            "amazon.in",       # 印度
            "amazon.com.br",   # 巴西
            "amazon.com.mx",   # 墨西哥
        ]
    
    @classmethod
    def is_valid_domain(cls, domain: str) -> bool:
        """检查域名是否有效"""
        return domain in cls.get_supported_domains() 