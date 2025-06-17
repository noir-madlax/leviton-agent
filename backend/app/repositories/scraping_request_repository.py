from typing import Optional, Dict, Any
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class ScrapingRequestRepository:
    """爬取请求数据访问仓库"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    async def create_scraping_request(self, request_data: Dict[str, Any]) -> Optional[int]:
        """
        创建爬取请求记录
        
        Args:
            request_data: 包含爬取请求信息的字典
            
        Returns:
            Optional[int]: 创建成功返回请求ID，失败返回None
        """
        try:
            result = self.client.table('scraping_requests').insert(request_data).execute()
            
            if result.data and len(result.data) > 0:
                request_id = result.data[0]['id']
                logger.info(f"成功创建爬取请求记录，ID: {request_id}")
                return request_id
            else:
                logger.error("创建爬取请求记录失败：返回数据为空")
                return None
                
        except Exception as e:
            logger.error(f"创建爬取请求记录时出错: {e}")
            return None
    
    async def update_request_status(self, request_id: int, status: str, 
                                   additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新爬取请求状态
        
        Args:
            request_id: 请求ID
            status: 新状态
            additional_data: 额外更新的数据
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            update_data = {"status": status, "updated_at": "NOW()"}
            if additional_data:
                update_data.update(additional_data)
            
            result = self.client.table('scraping_requests').update(update_data).eq('id', request_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"成功更新爬取请求状态，ID: {request_id}, 状态: {status}")
                return True
            else:
                logger.error(f"更新爬取请求状态失败，ID: {request_id}")
                return False
                
        except Exception as e:
            logger.error(f"更新爬取请求状态时出错: {e}")
            return False
    
    async def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取爬取请求记录
        
        Args:
            request_id: 请求ID
            
        Returns:
            Optional[Dict[str, Any]]: 请求记录或None
        """
        try:
            result = self.client.table('scraping_requests').select("*").eq('id', request_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                logger.warning(f"未找到爬取请求记录，ID: {request_id}")
                return None
                
        except Exception as e:
            logger.error(f"获取爬取请求记录时出错: {e}")
            return None 