from typing import Optional, List, Dict, Any
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class AmazonProductRepository:
    """Amazon产品数据访问仓库"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    async def batch_insert_products(self, products: List[Dict[str, Any]], 
                                   batch_id: int) -> bool:
        """
        批量插入产品数据
        
        Args:
            products: 产品数据列表
            batch_id: 批次ID (对应scraping_requests.id)
            
        Returns:
            bool: 插入成功返回True，失败返回False
        """
        try:
            # 为每个产品添加批次ID
            for product in products:
                product['batch_id'] = batch_id
            
            result = self.client.table('amazon_products').insert(products).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"成功批量插入 {len(result.data)} 个产品，批次ID: {batch_id}")
                return True
            else:
                logger.error("批量插入产品失败：返回数据为空")
                return False
                
        except Exception as e:
            logger.error(f"批量插入产品时出错: {e}")
            return False
    
    async def get_products_by_request(self, batch_id: int) -> List[Dict[str, Any]]:
        """
        根据批次ID获取产品列表 (兼容旧方法名)
        
        Args:
            batch_id: 批次ID
            
        Returns:
            List[Dict[str, Any]]: 产品列表
        """
        return await self.get_products_by_batch(batch_id)
    
    async def check_product_exists(self, platform_id: str) -> bool:
        """
        检查产品是否已存在
        
        Args:
            platform_id: 产品平台ID (ASIN)
            
        Returns:
            bool: 存在返回True，不存在返回False
        """
        try:
            result = self.client.table('amazon_products').select("id").eq('platform_id', platform_id).execute()
            
            return result.data and len(result.data) > 0
                
        except Exception as e:
            logger.error(f"检查产品是否存在时出错: {e}")
            return False
    
    async def get_product_by_asin(self, asin: str) -> Optional[Dict[str, Any]]:
        """
        根据ASIN获取产品信息
        
        Args:
            asin: Amazon产品ASIN
            
        Returns:
            Optional[Dict[str, Any]]: 产品信息或None
        """
        try:
            result = self.client.table('amazon_products').select("*").eq('platform_id', asin).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                logger.warning(f"未找到产品，ASIN: {asin}")
                return None
                
        except Exception as e:
            logger.error(f"获取产品信息时出错: {e}")
            return None
    
    async def get_products_by_batch(self, batch_id: int) -> List[Dict[str, Any]]:
        """
        根据批次ID获取产品列表
        
        Args:
            batch_id: 批次ID
            
        Returns:
            List[Dict[str, Any]]: 产品列表
        """
        try:
            result = self.client.table('amazon_products').select("*").eq('batch_id', batch_id).execute()
            
            if result.data:
                logger.info(f"获取到 {len(result.data)} 个产品，批次ID: {batch_id}")
                return result.data
            else:
                logger.warning(f"未找到产品数据，批次ID: {batch_id}")
                return []
                
        except Exception as e:
            logger.error(f"获取批次产品数据时出错: {e}")
            return []
    
    async def get_product_batches_by_asin(self, asin: str) -> List[Dict[str, Any]]:
        """
        根据ASIN获取该产品的所有批次记录
        
        Args:
            asin: Amazon产品ASIN
            
        Returns:
            List[Dict[str, Any]]: 产品的所有批次记录
        """
        try:
            result = self.client.table('amazon_products')\
                .select("*")\
                .eq('platform_id', asin)\
                .order('batch_id', desc=True)\
                .execute()
            
            if result.data:
                logger.info(f"获取到 {len(result.data)} 个批次记录，ASIN: {asin}")
                return result.data
            else:
                logger.warning(f"未找到产品批次记录，ASIN: {asin}")
                return []
                
        except Exception as e:
            logger.error(f"获取产品批次记录时出错: {e}")
            return []
    
    async def check_recent_products_by_criteria(self, category_metadata: dict = None, 
                                              min_products: int = 100, 
                                              hours_threshold: int = 24) -> Dict[str, Any]:
        """
        检查最近是否有符合条件的产品批次
        
        Args:
            category_metadata: 类别元数据字典，用于匹配
            min_products: 最小产品数量
            hours_threshold: 时间阈值（小时）
            
        Returns:
            Dict[str, Any]: 检查结果
        """
        try:
            from datetime import datetime, timedelta
            
            # 计算时间阈值
            threshold_time = datetime.now() - timedelta(hours=hours_threshold)
            threshold_iso = threshold_time.isoformat()
            
            # 查询最近的批次 - 按created_at降序排列
            # 注意：这里假设amazon_products表有created_at字段
            # 如果没有，可能需要从scraping_requests表关联查询
            
            result = self.client.table('amazon_products')\
                .select("batch_id, created_at")\
                .gte('created_at', threshold_iso)\
                .order('created_at', desc=True)\
                .execute()
            
            if not result.data:
                return {
                    "has_recent_products": False,
                    "reason": "no_recent_batches",
                    "threshold_hours": hours_threshold
                }
            
            # 统计每个批次的产品数量
            batch_counts = {}
            for product in result.data:
                batch_id = product['batch_id']
                if batch_id not in batch_counts:
                    batch_counts[batch_id] = 0
                batch_counts[batch_id] += 1
            
            # 检查是否有批次满足最小产品数量要求
            for batch_id, count in batch_counts.items():
                if count >= min_products:
                    logger.info(f"找到最近的符合条件的产品批次: batch_id={batch_id}, 产品数={count}")
                    return {
                        "has_recent_products": True,
                        "batch_id": batch_id,
                        "product_count": count,
                        "threshold_hours": hours_threshold,
                        "reason": f"recent_batch_sufficient ({count} >= {min_products})"
                    }
            
            return {
                "has_recent_products": False,
                "reason": f"recent_batches_insufficient (max: {max(batch_counts.values()) if batch_counts else 0} < {min_products})",
                "threshold_hours": hours_threshold,
                "batch_counts": batch_counts
            }
                
        except Exception as e:
            logger.error(f"检查最近产品批次时出错: {e}")
            return {
                "has_recent_products": False,
                "reason": f"error_checking_recent_products: {e}",
                "threshold_hours": hours_threshold
            } 