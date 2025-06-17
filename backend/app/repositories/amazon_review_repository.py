from typing import List, Dict, Any, Optional
import logging
from supabase import Client

logger = logging.getLogger(__name__)

class AmazonReviewRepository:
    """Amazon评论数据仓库"""
    
    def __init__(self, supabase_client: Client):
        self.supabase_client = supabase_client
        self.table_name = 'amazon_reviews'
    
    async def batch_insert_reviews(self, reviews: List[Dict[str, Any]], batch_size: int = 1000) -> bool:
        """
        批量插入评论数据
        
        Args:
            reviews: 评论数据列表
            batch_size: 批次大小
            
        Returns:
            bool: 插入是否成功
        """
        try:
            total_inserted = 0
            
            logger.info(f"开始批量插入 {len(reviews)} 条评论数据到 {self.table_name} 表")
            
            # 分批插入
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i + batch_size]
                
                logger.info(f"正在插入第 {i//batch_size + 1} 批，共 {len(batch)} 条记录...")
                
                # 执行插入
                result = self.supabase_client.table(self.table_name).insert(batch).execute()
                
                if result.data:
                    batch_inserted = len(result.data)
                    total_inserted += batch_inserted
                    logger.info(f"第 {i//batch_size + 1} 批插入成功：{batch_inserted} 条记录")
                else:
                    logger.error(f"第 {i//batch_size + 1} 批插入失败，没有返回数据")
                    return False
            
            logger.info(f"批量插入完成，总共插入 {total_inserted} 条评论数据")
            return True
            
        except Exception as e:
            logger.error(f"批量插入评论数据失败: {e}")
            return False
    
    async def get_reviews_by_batch(self, batch_id: int) -> List[Dict[str, Any]]:
        """
        根据批次ID获取评论数据
        
        Args:
            batch_id: 批次ID
            
        Returns:
            List[Dict[str, Any]]: 评论数据列表
        """
        try:
            result = self.supabase_client.table(self.table_name)\
                .select("*")\
                .eq("scrape_batch_id", batch_id)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"获取批次 {batch_id} 评论数据失败: {e}")
            return []
    
    async def get_reviews_by_asin(self, asin: str) -> List[Dict[str, Any]]:
        """
        根据ASIN获取评论数据
        
        Args:
            asin: 产品ASIN
            
        Returns:
            List[Dict[str, Any]]: 评论数据列表
        """
        try:
            result = self.supabase_client.table(self.table_name)\
                .select("*")\
                .eq("asin", asin)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"获取ASIN {asin} 评论数据失败: {e}")
            return []
    
    async def count_reviews_by_batch(self, batch_id: int) -> int:
        """
        统计批次中的评论数量
        
        Args:
            batch_id: 批次ID
            
        Returns:
            int: 评论数量
        """
        try:
            result = self.supabase_client.table(self.table_name)\
                .select("id", count="exact")\
                .eq("scrape_batch_id", batch_id)\
                .execute()
            
            return result.count if result.count else 0
            
        except Exception as e:
            logger.error(f"统计批次 {batch_id} 评论数量失败: {e}")
            return 0
    
    async def delete_reviews_by_batch(self, batch_id: int) -> bool:
        """
        删除指定批次的评论数据
        
        Args:
            batch_id: 批次ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            result = self.supabase_client.table(self.table_name)\
                .delete()\
                .eq("scrape_batch_id", batch_id)\
                .execute()
            
            logger.info(f"删除批次 {batch_id} 的评论数据成功")
            return True
            
        except Exception as e:
            logger.error(f"删除批次 {batch_id} 评论数据失败: {e}")
            return False 