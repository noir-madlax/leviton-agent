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
    
    async def import_batch_reviews(self, batch_id: int) -> Dict[str, Any]:
        """
        导入批次评论数据 - 从文件读取并插入数据库
        
        Args:
            batch_id: 批次ID
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        import os
        import json
        from pathlib import Path
        
        try:
            logger.info(f"开始处理批次 {batch_id} 的评论文件...")
            
            # 构造评论文件目录路径
            script_dir = Path(__file__).parent.parent.parent  # backend目录
            review_dir = script_dir / "scraping" / "data" / "scraped" / "amazon" / "review"
            
            if not review_dir.exists():
                logger.error(f"评论目录不存在: {review_dir}")
                return {"reviews_imported": 0, "error": "Review directory not found"}
            
            # 查找批次相关的评论文件
            review_files = []
            for file_path in review_dir.glob("*.json"):
                # 排除汇总文件
                if "summary" not in file_path.name.lower():
                    review_files.append(file_path)
            
            if not review_files:
                logger.warning(f"批次 {batch_id} 没有找到评论文件")
                return {"reviews_imported": 0, "message": "No review files found"}
            
            total_reviews_imported = 0
            processed_files = 0
            
            # 处理每个评论文件
            for file_path in review_files:
                try:
                    logger.info(f"处理评论文件: {file_path.name}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        review_data = json.load(f)
                    
                    # 提取评论并转换为数据库格式
                    reviews_for_db = await self._convert_reviews_to_db_format(
                        review_data, batch_id, file_path.name
                    )
                    
                    if reviews_for_db:
                        # 批量插入评论
                        success = await self.batch_insert_reviews(reviews_for_db)
                        if success:
                            count = len(reviews_for_db)
                            total_reviews_imported += count
                            processed_files += 1
                            logger.info(f"文件 {file_path.name} 导入成功: {count} 条评论")
                        else:
                            logger.error(f"文件 {file_path.name} 导入失败")
                    else:
                        logger.warning(f"文件 {file_path.name} 没有有效的评论数据")
                        
                except Exception as file_error:
                    logger.error(f"处理文件 {file_path.name} 时出错: {file_error}")
                    continue
            
            logger.info(f"批次 {batch_id} 评论导入完成: 处理了 {processed_files} 个文件，导入了 {total_reviews_imported} 条评论")
            
            return {
                "reviews_imported": total_reviews_imported,
                "files_processed": processed_files,
                "total_files": len(review_files)
            }
            
        except Exception as e:
            logger.error(f"导入批次 {batch_id} 评论时出错: {e}")
            return {"reviews_imported": 0, "error": str(e)}
    
    async def _convert_reviews_to_db_format(self, review_data: Dict[str, Any], 
                                          batch_id: int, filename: str) -> List[Dict[str, Any]]:
        """
        将评论数据转换为数据库格式
        
        Args:
            review_data: 原始评论数据
            batch_id: 批次ID
            filename: 文件名
            
        Returns:
            List[Dict[str, Any]]: 转换后的评论数据列表
        """
        from datetime import datetime
        
        try:
            reviews_for_db = []
            
            # 提取ASIN
            asin = review_data.get('asin', '')
            if not asin:
                logger.warning(f"文件 {filename} 缺少ASIN信息")
                return []
            
            # 提取产品信息
            product_info = review_data.get('product', {})
            product_title = product_info.get('title', '')
            product_rating = str(product_info.get('rating', ''))
            count_ratings = product_info.get('ratings_total', 0)
            count_reviews = len(review_data.get('reviews', []))
            
            # 处理每个评论
            reviews = review_data.get('reviews', [])
            for review in reviews:
                if not isinstance(review, dict):
                    continue
                
                review_record = {
                    'scrape_batch_id': batch_id,
                    'scrape_date': datetime.now().isoformat(),  # 转换为ISO格式字符串
                    'source': 'amazon_api',
                    'scraper_version': '1.0',
                    'asin': asin,
                    'review_id': review.get('reviewId', ''),  # 修复：使用正确的字段名 reviewId
                    'product_title': product_title,
                    'count_reviews': count_reviews,
                    'count_ratings': count_ratings,
                    'product_rating': product_rating,
                    'review_summary': review,  # 存储完整的评论JSON
                    'review_text': review.get('text', ''),  # 修复：使用正确的字段名 text
                    'review_title': review.get('title', ''),
                    'rating': str(review.get('rating', '')),
                    'review_date': review.get('date', ''),
                    'verified': review.get('verified', False),  # 修复：使用正确的字段名 verified
                    'user_name': review.get('userName', ''),  # 修复：使用正确的字段名 userName
                    'number_of_helpful': review.get('numberOfHelpful', 0),  # 修复：使用正确的字段名 numberOfHelpful
                    'vine': review.get('vine', False),
                    'status_code': review.get('statusCode', 200),  # 使用实际的状态码
                    'status_message': review.get('statusMessage', 'success'),  # 使用实际的状态信息
                    'current_page': review.get('currentPage', 1),
                    'sort_strategy': review.get('sortStrategy', 'recent'),
                    'domain_code': review.get('domainCode', 'com'),
                    'filters': review.get('filters', {}),
                    'variation_id': review.get('variationId', '')  # 修复：使用正确的字段名 variationId
                }
                
                reviews_for_db.append(review_record)
            
            logger.info(f"转换了 {len(reviews_for_db)} 条评论数据")
            return reviews_for_db
            
        except Exception as e:
            logger.error(f"转换评论数据时出错: {e}")
            return [] 