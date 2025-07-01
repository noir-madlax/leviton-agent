"""Amazon Category API Client - Rainforest API Integration"""

import aiohttp
import asyncio
import logging
import requests
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import json

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
import sys
sys.path.insert(0, str(current_dir))

from category_config import CategoryFetcherConfig
from models import APIResponse


logger = logging.getLogger(__name__)


class RainforestCategoryAPI:
    """Rainforest API客户端，专门用于获取亚马逊类别"""
    
    def __init__(self, api_key: Optional[str] = None, delay_seconds: float = 1.0):
        """
        初始化API客户端
        
        Args:
            api_key: Rainforest API密钥
            delay_seconds: API调用间隔时间
        """
        self.api_key = api_key or CategoryFetcherConfig.RAINFOREST_API_KEY
        self.base_url = CategoryFetcherConfig.RAINFOREST_API_URL
        self.delay_seconds = max(delay_seconds, CategoryFetcherConfig.MIN_API_DELAY)
        self.last_request_time = 0
        
        if not self.api_key:
            raise ValueError("Rainforest API key is required")
        
        logger.info(f"Initialized Rainforest API client with {delay_seconds}s delay")
    
    def _wait_for_rate_limit(self):
        """等待以遵守API限流"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.delay_seconds:
            sleep_time = self.delay_seconds - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict[str, Any]) -> requests.Response:
        """
        发起API请求
        
        Args:
            params: 请求参数
            
        Returns:
            requests.Response: 响应对象
            
        Raises:
            requests.RequestException: 请求失败
        """
        self._wait_for_rate_limit()
        
        # 添加API密钥
        params["api_key"] = self.api_key
        
        logger.debug(f"Making API request with params: {params}")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_root_categories(self, domain: str = "amazon.com") -> APIResponse:
        """
        获取根级别类别
        
        Args:
            domain: 亚马逊域名
            
        Returns:
            APIResponse: API响应记录
        """
        params = {
            "domain": domain
        }
        
        try:
            response = self._make_request(params)
            response_data = response.json()
            
            return APIResponse(
                category_id="root",
                timestamp=time.time(),
                success=True,
                response_data=response_data
            )
            
        except Exception as e:
            logger.error(f"Failed to get root categories: {e}")
            return APIResponse(
                category_id="root",
                timestamp=time.time(),
                success=False,
                error_message=str(e)
            )
    
    def get_category_children(self, parent_id: str, domain: str = "amazon.com") -> APIResponse:
        """
        获取指定类别的子类别
        
        Args:
            parent_id: 父类别ID
            domain: 亚马逊域名
            
        Returns:
            APIResponse: API响应记录
        """
        params = {
            "domain": domain,
            "parent_id": parent_id
        }
        
        try:
            response = self._make_request(params)
            response_data = response.json()
            
            return APIResponse(
                category_id=parent_id,
                timestamp=time.time(),
                success=True,
                response_data=response_data
            )
            
        except Exception as e:
            logger.error(f"Failed to get children for category {parent_id}: {e}")
            return APIResponse(
                category_id=parent_id,
                timestamp=time.time(),
                success=False,
                error_message=str(e)
            )
    
    def save_response_to_file(self, api_response: APIResponse, file_path: Path) -> bool:
        """
        保存API响应到文件
        
        Args:
            api_response: API响应对象
            file_path: 保存路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 准备保存的数据
            save_data = {
                "category_id": api_response.category_id,
                "timestamp": api_response.timestamp,
                "success": api_response.success,
                "response_data": api_response.response_data,
                "error_message": api_response.error_message
            }
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            # 更新API响应对象的文件路径
            api_response.file_path = str(file_path)
            
            logger.debug(f"Saved API response to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save API response to {file_path}: {e}")
            return False
    
    def load_response_from_file(self, file_path: Path) -> Optional[APIResponse]:
        """
        从文件加载API响应
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[APIResponse]: API响应对象或None
        """
        try:
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return APIResponse(
                category_id=data["category_id"],
                timestamp=data["timestamp"],
                success=data["success"],
                response_data=data.get("response_data"),
                error_message=data.get("error_message"),
                file_path=str(file_path)
            )
            
        except Exception as e:
            logger.error(f"Failed to load API response from {file_path}: {e}")
            return None
    
    def parse_categories_from_response(self, api_response: APIResponse) -> List[Dict[str, Any]]:
        """
        从API响应中解析类别信息
        
        Args:
            api_response: API响应对象
            
        Returns:
            List[Dict[str, Any]]: 类别信息列表
        """
        if not api_response.success or not api_response.response_data:
            return []
        
        try:
            categories = []
            response_data = api_response.response_data
            
            # 根据API响应结构解析类别
            if "categories" in response_data:
                for category in response_data["categories"]:
                    category_info = {
                        "category_id": category.get("id", ""),
                        "name": category.get("name", ""),
                        "link": category.get("link", ""),
                        "parent_id": category.get("parent_id"),
                        "is_leaf": category.get("is_leaf", False)
                    }
                    categories.append(category_info)
            
            logger.debug(f"Parsed {len(categories)} categories from response")
            return categories
            
        except Exception as e:
            logger.error(f"Failed to parse categories from response: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("Testing Rainforest API connection...")
            response = self.get_root_categories()
            
            if response.success:
                logger.info("API connection test successful")
                return True
            else:
                logger.error(f"API connection test failed: {response.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"API connection test failed with exception: {e}")
            return False 