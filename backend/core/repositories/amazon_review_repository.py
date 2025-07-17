from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
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
            total_skipped = 0
            
            logger.info(f"开始批量插入 {len(reviews)} 条评论数据到 {self.table_name} 表")
            
            # 分批插入
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i + batch_size]
                
                logger.info(f"正在插入第 {i//batch_size + 1} 批，共 {len(batch)} 条记录...")
                
                try:
                    # 执行插入
                    result = self.supabase_client.table(self.table_name).insert(batch).execute()
                    
                    if result.data:
                        batch_inserted = len(result.data)
                        total_inserted += batch_inserted
                        logger.info(f"第 {i//batch_size + 1} 批插入成功：{batch_inserted} 条记录")
                    else:
                        logger.warning(f"第 {i//batch_size + 1} 批插入没有返回数据")
                        
                except Exception as batch_error:
                    # 如果是重复键错误，记录但继续处理
                    error_str = str(batch_error)
                    if "duplicate key" in error_str or "already exists" in error_str:
                        total_skipped += len(batch)
                        logger.warning(f"第 {i//batch_size + 1} 批包含重复数据，跳过: {len(batch)} 条记录")
                    else:
                        logger.error(f"第 {i//batch_size + 1} 批插入出现其他错误: {batch_error}")
                        # 对于非重复错误，我们仍然继续处理其他批次
                        continue
            
            logger.info(f"批量插入完成，总共插入 {total_inserted} 条评论数据，跳过 {total_skipped} 条重复数据")
            return True  # 只要有部分成功就返回True
            
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
            
            # 查找批次相关的评论文件 - 修复：根据批次ID查找
            review_files = []
            batch_pattern = f"batch_{batch_id}_*_reviews.json"
            
            for file_path in review_dir.glob(batch_pattern):
                # 只要评论文件，排除汇总文件
                if "summary" not in file_path.name.lower():
                    review_files.append(file_path)
            
            logger.info(f"找到批次 {batch_id} 的评论文件: {[f.name for f in review_files]}")
            
            if not review_files:
                logger.warning(f"批次 {batch_id} 没有找到评论文件")
                return {"reviews_imported": 0, "files_processed": 0, "total_files": 0, "message": "No review files found"}
            
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
                        # 使用批量UPSERT策略，避免重复数据
                        success = await self.batch_upsert_reviews(reviews_for_db)
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
            return {"reviews_imported": 0, "files_processed": 0, "total_files": 0, "error": str(e)}
    
    async def batch_upsert_reviews(self, reviews: List[Dict[str, Any]], batch_size: int = 1000) -> bool:
        """
        批量UPSERT评论数据 - 手动去重处理
        
        Args:
            reviews: 评论数据列表
            batch_size: 批次大小
            
        Returns:
            bool: 插入是否成功
        """
        try:
            total_processed = 0
            total_skipped = 0
            
            logger.info(f"开始批量UPSERT {len(reviews)} 条评论数据到 {self.table_name} 表")
            
            # 1. 获取数据库中已存在的review_id (for this ASIN)
            asins_in_batch = list(set(r.get('asin') for r in reviews if r.get('asin')))
            existing_review_ids = set()
            
            for asin in asins_in_batch:
                try:
                    existing_result = self.supabase_client.table(self.table_name)\
                        .select('asin, review_id')\
                        .eq('asin', asin)\
                        .execute()
                    
                    for row in existing_result.data:
                        existing_review_ids.add(f"{row['asin']}:{row['review_id']}")
                        
                except Exception as e:
                    logger.warning(f"Error checking existing reviews for {asin}: {e}")
                    continue
            
            # 2. Filter out duplicates 
            unique_reviews = []
            for review in reviews:
                asin = review.get('asin')
                review_id = review.get('review_id')
                
                if not asin or not review_id:
                    continue
                    
                composite_key = f"{asin}:{review_id}"
                if composite_key not in existing_review_ids:
                    unique_reviews.append(review)
                    existing_review_ids.add(composite_key)  # Add to set to avoid within-batch duplicates
                else:
                    total_skipped += 1
            
            logger.info(f"去重完成: {len(reviews)} -> {len(unique_reviews)} (跳过 {total_skipped} 个重复)")
            
            if not unique_reviews:
                logger.info("没有新的唯一评论需要插入")
                return True
            
            # 3. 分批插入唯一评论
            for i in range(0, len(unique_reviews), batch_size):
                batch = unique_reviews[i:i + batch_size]
                
                logger.info(f"正在插入第 {i//batch_size + 1} 批，共 {len(batch)} 条唯一记录...")
                
                try:
                    result = self.supabase_client.table(self.table_name).insert(batch).execute()
                    
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
            
            logger.info(f"批量UPSERT完成，总共插入 {total_processed} 条新评论数据，跳过 {total_skipped} 条重复数据")
            return True
            
        except Exception as e:
            logger.error(f"批量UPSERT评论数据失败: {e}")
            return False
    
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
    
    async def check_recent_reviews_by_asin(self, asin: str, min_reviews: int = 30, 
                                         coverage_months: int = 6, 
                                         hours_threshold: int = 24) -> Dict[str, Any]:
        """
        检查ASIN最近是否有足够的评论
        
        Args:
            asin: 产品ASIN
            min_reviews: 最小评论数量
            coverage_months: 覆盖月数要求
            hours_threshold: 时间阈值（小时）
            
        Returns:
            Dict[str, Any]: 检查结果
        """
        try:
            from datetime import timedelta
            
            # 计算时间阈值
            threshold_time = datetime.now() - timedelta(hours=hours_threshold)
            threshold_iso = threshold_time.isoformat()
            
            # 查询该ASIN最近导入的评论
            result = self.supabase_client.table(self.table_name)\
                .select("*")\
                .eq("asin", asin)\
                .gte('scrape_date', threshold_iso)\
                .order('scrape_date', desc=True)\
                .execute()
            
            if not result.data:
                return {
                    "has_sufficient_reviews": False,
                    "reason": "no_recent_reviews",
                    "threshold_hours": hours_threshold,
                    "existing_count": 0
                }
            
            reviews = result.data
            review_count = len(reviews)
            
            # 检查数量是否足够
            if review_count < min_reviews:
                return {
                    "has_sufficient_reviews": False,
                    "reason": f"insufficient_count ({review_count} < {min_reviews})",
                    "threshold_hours": hours_threshold,
                    "existing_count": review_count
                }
            
            # 检查覆盖时间范围
            latest_review_date = None
            valid_dates_count = 0
            
            for review in reviews:
                review_date_str = review.get("review_date", "")
                if self._is_valid_review_date_simple(review_date_str):
                    parsed_date = self._parse_review_date_simple(review_date_str)
                    if parsed_date:
                        valid_dates_count += 1
                        if not latest_review_date or parsed_date > latest_review_date:
                            latest_review_date = parsed_date
            
            if not latest_review_date:
                return {
                    "has_sufficient_reviews": False,
                    "reason": "no_valid_review_dates",
                    "threshold_hours": hours_threshold,
                    "existing_count": review_count
                }
            
            # 计算覆盖月数
            now = datetime.now()
            days_difference = (now - latest_review_date).days
            latest_reviews_months = days_difference / 30  # 简化为30天一个月
            
            if latest_reviews_months <= coverage_months:
                logger.info(f"ASIN {asin} 有足够的最近评论: {review_count} 条, 最新评论 {latest_reviews_months:.1f} 个月前")
                return {
                    "has_sufficient_reviews": True,
                    "reason": f"sufficient_recent_reviews ({review_count} reviews, {latest_reviews_months:.1f} months)",
                    "threshold_hours": hours_threshold,
                    "existing_count": review_count,
                    "latest_review_months": latest_reviews_months,
                    "valid_dates_count": valid_dates_count
                }
            else:
                return {
                    "has_sufficient_reviews": False,
                    "reason": f"reviews_too_old ({latest_reviews_months:.1f} months > {coverage_months})",
                    "threshold_hours": hours_threshold,
                    "existing_count": review_count,
                    "latest_review_months": latest_reviews_months
                }
                
        except Exception as e:
            logger.error(f"检查ASIN {asin} 最近评论时出错: {e}")
            return {
                "has_sufficient_reviews": False,
                "reason": f"error_checking_recent_reviews: {e}",
                "threshold_hours": hours_threshold,
                "existing_count": 0
            }
    
    def _is_valid_review_date_simple(self, date_str: str) -> bool:
        """简化版的评论日期验证"""
        if not date_str or not isinstance(date_str, str):
            return False
        return len(date_str.strip()) > 0
    
    def _parse_review_date_simple(self, date_str: str) -> Optional[datetime]:
        """简化版的评论日期解析"""
        try:
            # 尝试多种日期格式
            formats = [
                "%Y-%m-%d",
                "%m/%d/%Y", 
                "%d/%m/%Y",
                "%B %d, %Y",
                "%b %d, %Y",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S"
            ]
            
            date_str = date_str.strip()
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # 如果所有格式都失败，返回None
            logger.debug(f"无法解析日期格式: {date_str}")
            return None
            
        except Exception as e:
            logger.debug(f"解析评论日期时出错: {e}")
            return None
    
    async def get_asin_review_summary(self, asin: str) -> Dict[str, Any]:
        """
        获取ASIN的评论汇总信息（使用唯一评论计数）
        
        Args:
            asin: 产品ASIN
            
        Returns:
            Dict[str, Any]: 评论汇总信息
        """
        try:
            # 获取该ASIN的所有评论
            result = self.supabase_client.table(self.table_name)\
                .select('review_id, scrape_context')\
                .eq('asin', asin)\
                .execute()
            
            if not result.data:
                return {
                    "total_reviews": 0,
                    "unique_reviews": 0,
                    "max_previous_max_reviews": 0,
                    "asin": asin
                }
            
            # 计算唯一评论数量
            unique_review_ids = set()
            max_previous_max_reviews = 0
            
            for row in result.data:
                # 添加唯一评论ID
                review_id = row.get('review_id')
                if review_id:
                    unique_review_ids.add(review_id)
                
                # 从scrape_context中获取之前的max_reviews设置
                # 注意：这里假设scrape_context是JSON字段，可能需要解析
                # 如果数据库结构不同，可能需要调整
                
            unique_reviews = len(unique_review_ids)
            total_reviews = len(result.data)
            
            logger.info(f"ASIN {asin} 评论汇总: {total_reviews} 总计, {unique_reviews} 唯一")
            
            return {
                "total_reviews": total_reviews,
                "unique_reviews": unique_reviews,
                "max_previous_max_reviews": max_previous_max_reviews,
                "asin": asin
            }
            
        except Exception as e:
            logger.error(f"获取ASIN {asin} 评论汇总时出错: {e}")
            return {
                "total_reviews": 0,
                "unique_reviews": 0,
                "max_previous_max_reviews": 0,
                "asin": asin,
                "error": str(e)
            } 