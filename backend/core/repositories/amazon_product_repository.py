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
            
            # 如果提供了category_metadata，需要从scraping_requests表中获取符合条件的batch_id
            if category_metadata and category_metadata.get('category_id'):
                category_id = category_metadata.get('category_id')
                logger.info(f"添加category_id过滤条件: {category_id}")
                
                # 首先从scraping_requests表中查找符合category_id的批次
                category_batches_result = self.client.table('scraping_requests')\
                    .select("id")\
                    .eq('category_id', category_id)\
                    .gte('created_at', threshold_iso)\
                    .execute()
                
                if not category_batches_result.data:
                    logger.info(f"数据库中未找到category_id={category_id}在{hours_threshold}小时内的爬取请求")
                    return {
                        "has_recent_products": False,
                        "reason": f"no_recent_requests_for_category_{category_id}",
                        "threshold_hours": hours_threshold
                    }
                
                # 获取符合条件的batch_id列表
                valid_batch_ids = [batch['id'] for batch in category_batches_result.data]
                logger.info(f"找到符合category_id={category_id}的批次: {valid_batch_ids}")
                
                # 查询这些批次下的产品
                result = self.client.table('amazon_products')\
                    .select("batch_id, created_at")\
                    .in_('batch_id', valid_batch_ids)\
                    .gte('created_at', threshold_iso)\
                    .order('created_at', desc=True)\
                    .execute()
            else:
                # 如果没有category_metadata，查询所有最近的批次
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
            
            # 统计每个批次的唯一产品数量 (by platform_id)
            batch_unique_products = {}
            for product in result.data:
                batch_id = product['batch_id']
                if batch_id not in batch_unique_products:
                    batch_unique_products[batch_id] = set()
                
                # Get unique products for this batch
                batch_result = self.client.table('amazon_products')\
                    .select("platform_id")\
                    .eq('batch_id', batch_id)\
                    .execute()
                
                unique_asins = set(p['platform_id'] for p in batch_result.data if p.get('platform_id'))
                batch_unique_products[batch_id] = unique_asins
            
            # 检查是否有批次满足最小唯一产品数量要求
            for batch_id, unique_asins in batch_unique_products.items():
                unique_count = len(unique_asins)
                if unique_count >= min_products:
                    logger.info(f"找到最近的符合条件的产品批次: batch_id={batch_id}, 唯一产品数={unique_count}")
                    return {
                        "has_recent_products": True,
                        "batch_id": batch_id,
                        "product_count": unique_count,
                        "threshold_hours": hours_threshold,
                        "reason": f"recent_batch_sufficient ({unique_count} unique >= {min_products})"
                    }
            
            max_unique_count = max(len(asins) for asins in batch_unique_products.values()) if batch_unique_products else 0
            return {
                "has_recent_products": False,
                "reason": f"recent_batches_insufficient (max: {max_unique_count} unique < {min_products})",
                "threshold_hours": hours_threshold,
                "batch_unique_counts": {bid: len(asins) for bid, asins in batch_unique_products.items()}
            }
                
        except Exception as e:
            logger.error(f"检查最近产品批次时出错: {e}")
            return {
                "has_recent_products": False,
                "reason": f"error_checking_recent_products: {e}",
                "threshold_hours": hours_threshold
            }
    
    async def batch_upsert_products(self, products: List[Dict[str, Any]], batch_id: int, batch_size: int = 1000) -> bool:
        """
        批量UPSERT产品数据 - 手动去重处理
        
        Args:
            products: 产品数据列表
            batch_id: 批次ID
            batch_size: 批次大小
            
        Returns:
            bool: 插入是否成功
        """
        try:
            total_processed = 0
            total_skipped = 0
            
            logger.info(f"开始批量UPSERT {len(products)} 条产品数据到 amazon_products 表")
            
            # 1. 获取数据库中已存在的platform_id (ASINs)
            existing_result = self.client.table('amazon_products')\
                .select('platform_id')\
                .execute()
            
            existing_asins = set(row['platform_id'] for row in existing_result.data if row.get('platform_id'))
            
            # 2. Filter out duplicates and add batch_id
            unique_products = []
            for product in products:
                asin = product.get('platform_id')
                
                if not asin:
                    continue
                    
                if asin not in existing_asins:
                    product['batch_id'] = batch_id  # Ensure batch_id is set
                    unique_products.append(product)
                    existing_asins.add(asin)  # Add to set to avoid within-batch duplicates
                else:
                    total_skipped += 1
            
            logger.info(f"去重完成: {len(products)} -> {len(unique_products)} (跳过 {total_skipped} 个重复)")
            
            if not unique_products:
                logger.info("没有新的唯一产品需要插入")
                return True
            
            # 3. 分批插入唯一产品
            for i in range(0, len(unique_products), batch_size):
                batch = unique_products[i:i + batch_size]
                
                logger.info(f"正在插入第 {i//batch_size + 1} 批，共 {len(batch)} 条唯一记录...")
                
                try:
                    result = self.client.table('amazon_products').insert(batch).execute()
                    
                    if result.data:
                        batch_processed = len(result.data)
                        total_processed += batch_processed
                        logger.info(f"第 {i//batch_size + 1} 批插入成功：{batch_processed} 条记录")
                    else:
                        logger.warning(f"第 {i//batch_size + 1} 批插入没有返回数据")
                        
                except Exception as batch_error:
                    logger.error(f"第 {i//batch_size + 1} 批插入失败: {batch_error}")
                    # Continue with other batches even if one fails
                    continue
            
            logger.info(f"批量UPSERT完成，总共插入 {total_processed} 条新产品数据，跳过 {total_skipped} 条重复数据")
            return True
            
        except Exception as e:
            logger.error(f"批量UPSERT产品数据失败: {e}")
            return False 