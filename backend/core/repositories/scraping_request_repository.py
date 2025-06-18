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
            logger.info(f"开始创建爬取请求记录，数据: {request_data}")
            
            # 验证必要字段
            if not request_data.get('request_type'):
                logger.error("request_data缺少必要字段 'request_type'")
                return None
                
            # 记录插入前的调试信息
            logger.debug(f"准备插入到scraping_requests表的数据: {request_data}")
            
            result = self.client.table('scraping_requests').insert(request_data).execute()
            
            logger.debug(f"数据库插入原始结果: {result}")
            
            if result.data and len(result.data) > 0:
                request_id = result.data[0]['id']
                logger.info(f"成功创建爬取请求记录，ID: {request_id}")
                return request_id
            else:
                logger.error(f"创建爬取请求记录失败：返回数据为空。原始响应: {result}")
                return None
                
        except Exception as e:
            logger.error(f"创建爬取请求记录时出错: {e}")
            logger.error(f"错误类型: {type(e)}")
            logger.error(f"请求数据: {request_data}")
            
            # 如果是Supabase相关错误，记录更多信息
            if hasattr(e, 'details'):
                logger.error(f"Supabase错误详情: {e.details}")
            if hasattr(e, 'hint'):
                logger.error(f"Supabase错误提示: {e.hint}")
            if hasattr(e, 'code'):
                logger.error(f"Supabase错误代码: {e.code}")
                
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
    
    async def update_review_status(self, request_id: int, review_status: str, 
                                  reviews_scraped: int = 0,
                                  review_metadata: Optional[Dict[str, Any]] = None,
                                  set_completed_time: bool = False) -> bool:
        """
        更新评论爬取状态
        
        Args:
            request_id: 请求ID
            review_status: 评论爬取状态 (pending, processing, completed, failed, error)
            reviews_scraped: 成功爬取的评论数量
            review_metadata: 评论爬取的详细元数据
            set_completed_time: 是否设置完成时间
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            update_data = {
                "review_status": review_status,
                "reviews_scraped": reviews_scraped,
                "updated_at": "NOW()"
            }
            
            if review_metadata:
                update_data["review_metadata"] = review_metadata
            
            if review_status == "processing" and not set_completed_time:
                update_data["review_started_at"] = "NOW()"
            elif set_completed_time or review_status in ["completed", "failed", "error"]:
                update_data["review_completed_at"] = "NOW()"
            
            result = self.client.table('scraping_requests').update(update_data).eq('id', request_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"成功更新评论爬取状态，ID: {request_id}, 状态: {review_status}, 评论数: {reviews_scraped}")
                return True
            else:
                logger.error(f"更新评论爬取状态失败，ID: {request_id}")
                return False
                
        except Exception as e:
            logger.error(f"更新评论爬取状态时出错: {e}")
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