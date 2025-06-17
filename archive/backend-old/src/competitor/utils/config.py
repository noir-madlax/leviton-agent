"""
Configuration management utilities for competitor analysis scripts.

Provides centralized configuration management for:
- Directory structure setup
- Model configuration
- Rate limiting parameters
- Processing parameters
- File paths
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ConfigManager:
    """Centralized configuration manager for competitor analysis scripts"""
    
    def __init__(self, script_name: str, subdirectory: Optional[str] = None):
        """
        Initialize configuration manager for a specific script
        
        Args:
            script_name: Name of the script (e.g., "product_segment", "review_mro", "scrape_reviews")
            subdirectory: Optional subdirectory for outputs
        """
        self.script_name = script_name
        self.subdirectory = subdirectory
        self._setup_directories()
        self._setup_model_config()
        self._setup_claude_sonnet_4_rate_limits()
        self._setup_processing_params()
    
    def _setup_directories(self):
        """Setup directory structure"""
        self.ROOT_DIR = Path(__file__).parent.parent.parent.parent
        self.PROMPT_DIR = self.ROOT_DIR / "prompt"
        self.DATA_DIR = self.ROOT_DIR / "data"
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H")
        if self.subdirectory:
            self.OUTPUT_ROOT_DIR = self.DATA_DIR / "result" / self.script_name / self.subdirectory / timestamp
        else:
            self.OUTPUT_ROOT_DIR = self.DATA_DIR / "result" / self.script_name / timestamp
            
        self.LOG_DIR = self.DATA_DIR / "llm_log" / self.script_name / timestamp
        self.CACHE_DIR = self.OUTPUT_ROOT_DIR / "llm_cache"
        self.RESULT_CACHE_DIR = self.OUTPUT_ROOT_DIR / "result_cache"
        
        # Create directories
        for directory in [self.OUTPUT_ROOT_DIR, self.LOG_DIR, self.CACHE_DIR, self.RESULT_CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_model_config(self):
        """Setup LLM model configuration"""
        self.MODEL_NAME = "claude-sonnet-4-20250514"
        self.MODEL_TEMPERATURE = 0.15
        self.MODEL_MAX_TOKENS = 4096
    
    def _setup_claude_sonnet_4_rate_limits(self):
        """Setup rate limiting configuration for Claude Sonnet 4"""
        self.MAX_REQUESTS_PER_MINUTE = 1900  # Slightly below 2000 limit
        self.MAX_INPUT_TOKENS_PER_MINUTE = 75000  # Slightly below 80000 limit  
        self.MAX_OUTPUT_TOKENS_PER_MINUTE = 30000  # Slightly below 32000 limit
        self.MAX_CONCURRENT_REQUESTS = 20  # Concurrent request limit
    
    def _setup_processing_params(self):
        """Setup default processing parameters"""
        self.DEFAULT_BATCH_SIZE = 40
        self.DEFAULT_SEED = 42
        self.DEFAULT_MAX_RETRIES = 3
        self.RATE_LIMIT_DELAY = 0.1  # seconds
    
    def get_file_path(self, filename: str, subdirectory: str = "") -> Path:
        """Get full file path within the output directory"""
        if subdirectory:
            return self.OUTPUT_ROOT_DIR / subdirectory / filename
        return self.OUTPUT_ROOT_DIR / filename
    
    def get_data_path(self, *path_parts: str) -> Path:
        """Get path within the data directory"""
        return self.DATA_DIR.joinpath(*path_parts)
    
    def get_prompt_path(self, filename: str, subdirectory: str = "") -> Path:
        """Get path to prompt file"""
        if subdirectory:
            return self.PROMPT_DIR / subdirectory / filename
        return self.PROMPT_DIR / filename
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/caching"""
        return {
            "script_name": self.script_name,
            "model_name": self.MODEL_NAME,
            "model_temperature": self.MODEL_TEMPERATURE,
            "model_max_tokens": self.MODEL_MAX_TOKENS,
            "max_requests_per_minute": self.MAX_REQUESTS_PER_MINUTE,
            "max_input_tokens_per_minute": self.MAX_INPUT_TOKENS_PER_MINUTE,
            "max_output_tokens_per_minute": self.MAX_OUTPUT_TOKENS_PER_MINUTE,
            "max_concurrent_requests": self.MAX_CONCURRENT_REQUESTS,
            "default_batch_size": self.DEFAULT_BATCH_SIZE,
            "default_seed": self.DEFAULT_SEED,
            "default_max_retries": self.DEFAULT_MAX_RETRIES,
            "rate_limit_delay": self.RATE_LIMIT_DELAY,
            "root_dir": str(self.ROOT_DIR),
            "output_root_dir": str(self.OUTPUT_ROOT_DIR),
            "log_dir": str(self.LOG_DIR),
        }


# Convenience factory functions for common configurations
def get_segment_config(subdirectory: str = "combined_products_cleaned") -> ConfigManager:
    """Get configuration for product segmentation"""
    return ConfigManager("product_segment", subdirectory)

def get_process_review_config() -> ConfigManager:
    """Get configuration for MRO review processing"""
    return ConfigManager("process_review")

def get_scrape_config() -> ConfigManager:
    """Get configuration for review scraping"""
    config = ConfigManager("scrape_reviews")
    
    # Add scraping-specific configurations
    config.SCRAPE_RECENCY_DAYS = 30
    config.DAYS_PER_MONTH = 30
    config.DEFAULT_COVERAGE_MONTHS = 6
    config.MIN_REVIEW_YEAR = 2010
    config.MAX_REVIEW_YEAR = datetime.now().year
    config.DEFAULT_REVIEWS_PER_PAGE = 10
    config.MAX_PAGES_PER_ASIN = 5
    
    # Override directories for scraping
    config.OUTPUT_ROOT_DIR = config.DATA_DIR / "scraped" / "amazon" / "review"
    config.OUTPUT_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    
    return config 