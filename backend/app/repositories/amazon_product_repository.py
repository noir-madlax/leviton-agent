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