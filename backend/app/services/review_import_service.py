from typing import Dict, Any, List, Optional
import logging
import os
import json
import glob
import re
from datetime import datetime
from app.repositories.amazon_review_repository import AmazonReviewRepository
from app.database.connection import get_supabase_service_client

logger = logging.getLogger(__name__)

class ReviewImportService:
    """评论数据导入服务"""
    
    def __init__(self):
        # 获取Supabase客户端
        self.supabase_client = get_supabase_service_client()
        
        # 初始化评论仓库
        self.review_repository = AmazonReviewRepository(self.supabase_client)
        
        # 评论文件目录
        self.review_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "data", "scraped", "amazon", "review"
        )
    
    def _discover_batch_review_files(self, batch_id: int) -> List[str]:
        """
        发现批次相关的评论文件
        
        Args:
            batch_id: 批次ID
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            pattern = os.path.join(self.review_dir, f"batch_{batch_id}_*_reviews.json")
            files = glob.glob(pattern)
            
            logger.info(f"发现批次 {batch_id} 的评论文件: {len(files)} 个")
            for file_path in files:
                logger.info(f"  - {os.path.basename(file_path)}")
            
            return files
            
        except Exception as e:
            logger.error(f"发现批次文件时出错: {e}")
            return []
    
    def _extract_rating_number(self, rating_str: str) -> Optional[float]:
        """
        从评分字符串中提取数字
        
        Args:
            rating_str: 评分字符串，如 "4.0 out of 5 stars"
            
        Returns:
            Optional[float]: 评分数字
        """
        if not rating_str:
            return None
            
        try:
            # 使用正则表达式提取数字
            match = re.search(r'(\d+\.?\d*)', str(rating_str))
            if match:
                rating = float(match.group(1))
                # 确保评分在合理范围内
                if 0 <= rating <= 5:
                    return rating
            return None
        except (ValueError, AttributeError):
            return None
    
    def _parse_review_date(self, date_str: str) -> Optional[str]:
        """
        解析评论日期字符串
        
        Args:
            date_str: 日期字符串
            
        Returns:
            Optional[str]: 标准化的日期字符串 (YYYY-MM-DD)
        """
        if not date_str:
            return None
            
        try:
            # 提取日期部分，处理 "Reviewed in the United States on May 23, 2025" 格式
            if " on " in date_str:
                date_part = date_str.split(" on ")[-1].strip()
            else:
                date_part = date_str.strip()
            
            # 尝试各种日期格式
            date_formats = [
                "%B %d, %Y",      # "May 23, 2025"
                "%b %d, %Y",      # "May 23, 2025" (abbreviated month)
                "%m/%d/%Y",       # "05/23/2025"
                "%Y-%m-%d",       # "2025-05-23"
                "%d %B %Y",       # "23 May 2025"
                "%d %b %Y"        # "23 May 2025" (abbreviated month)
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_part, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    async def _process_review_file(self, file_path: str, batch_id: int) -> List[Dict[str, Any]]:
        """
        处理单个评论文件
        
        Args:
            file_path: 文件路径
            batch_id: 批次ID
            
        Returns:
            List[Dict[str, Any]]: 转换后的评论记录列表
        """
        try:
            logger.info(f"正在处理评论文件: {os.path.basename(file_path)}")
            
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取元数据
            metadata = data.get('scrape_metadata', {})
            reviews_data = data.get('reviews_data', {})
            reviews = reviews_data.get('reviews', [])
            
            if not reviews:
                logger.warning(f"文件 {file_path} 中没有评论数据")
                return []
            
            # 转换评论数据
            records = []
            asin = metadata.get('asin')
            
            for review in reviews:
                # 验证必要字段
                review_id = review.get('reviewId')
                if not review_id or not asin:
                    continue
                
                # 构建数据库记录（根据实际表结构调整字段名）
                record = {
                    # 批次字段
                    'scrape_batch_id': int(batch_id),  # 确保是整数类型
                    'scrape_date': metadata.get('scrape_date'),
                    'source': metadata.get('source', 'amazon_axesso_apify_api'),
                    'scraper_version': metadata.get('scraper_version', '3.0'),
                    
                    # 核心标识字段
                    'asin': asin,
                    'review_id': review_id,
                    
                    # 产品级元数据
                    'product_title': review.get('productTitle'),
                    'count_reviews': review.get('countReviews'),  # 从review中获取
                    'count_ratings': review.get('countRatings'),  # 从review中获取
                    'product_rating': review.get('productRating'),  # 从review中获取
                    'review_summary': review.get('reviewSummary'),  # 从review中获取
                    
                    # 评论内容字段
                    'review_text': review.get('text'),
                    'review_title': review.get('title'),
                    'rating': str(self._extract_rating_number(review.get('rating')) or ''),  # 转换为字符串以匹配表结构
                    'review_date': self._parse_review_date(review.get('date')),
                    'verified': review.get('verified', False),  # 字段名修正
                    'number_of_helpful': review.get('numberOfHelpful', 0),  # 修正字段名
                    'vine': review.get('vine', False),  # 字段名修正
                    
                    # 评论者信息
                    'user_name': review.get('userName'),  # 字段名修正
                    
                    # 其他字段
                    'status_code': review.get('statusCode'),
                    'status_message': review.get('statusMessage'),
                    'current_page': review.get('currentPage'),
                    'sort_strategy': review.get('sortStrategy'),
                    'domain_code': review.get('domainCode', 'com'),
                    'filters': review.get('filters'),
                    'variation_id': review.get('variationId')
                }
                
                # 数据验证
                if self._validate_review_record(record):
                    records.append(record)
                else:
                    logger.warning(f"跳过无效评论记录: {review_id}")
            
            logger.info(f"文件 {os.path.basename(file_path)} 处理完成，有效记录: {len(records)}")
            return records
            
        except Exception as e:
            logger.error(f"处理评论文件 {file_path} 时出错: {e}")
            return []
    
    def _validate_review_record(self, record: Dict[str, Any]) -> bool:
        """
        验证评论记录的有效性
        
        Args:
            record: 评论记录
            
        Returns:
            bool: 是否有效
        """
        # 检查必填字段
        required_fields = ['scrape_batch_id', 'asin', 'review_id']
        if not all(record.get(field) is not None for field in required_fields):
            return False
        
        # 检查批次ID是否为有效整数
        batch_id = record.get('scrape_batch_id')
        if not isinstance(batch_id, int) or batch_id <= 0:
            return False
        
        # 检查ASIN格式
        asin = record.get('asin', '')
        if not re.match(r'^B[0-9A-Z]{9}$', asin):
            return False
        
        # 检查评分范围
        rating = record.get('rating')
        if rating is not None and rating != 'None':
            try:
                rating_num = float(rating) if isinstance(rating, str) else rating
                if not (1 <= rating_num <= 5):
                    return False
            except (ValueError, TypeError):
                # 如果无法转换为数字，跳过评分验证
                pass
        
        # 检查评论文本长度
        review_text = record.get('review_text', '')
        if len(review_text) > 10000:  # 限制过长的评论
            record['review_text'] = review_text[:10000] + "..."
        
        return True
    
    async def import_batch_reviews(self, batch_id: int) -> Dict[str, Any]:
        """
        导入指定批次的评论数据
        
        Args:
            batch_id: 批次ID
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        try:
            logger.info(f"开始导入批次 {batch_id} 的评论数据...")
            
            # 1. 发现批次文件
            review_files = self._discover_batch_review_files(batch_id)
            
            if not review_files:
                logger.warning(f"批次 {batch_id} 没有找到评论文件")
                return {
                    "status": "warning",
                    "message": f"批次 {batch_id} 没有找到评论文件",
                    "batch_id": batch_id,
                    "files_processed": 0,
                    "records_imported": 0
                }
            
            # 2. 处理所有文件，收集评论记录
            all_records = []
            processed_files = 0
            
            for file_path in review_files:
                records = await self._process_review_file(file_path, batch_id)
                all_records.extend(records)
                processed_files += 1
            
            if not all_records:
                logger.warning(f"批次 {batch_id} 没有有效的评论数据")
                return {
                    "status": "warning",
                    "message": f"批次 {batch_id} 没有有效的评论数据",
                    "batch_id": batch_id,
                    "files_processed": processed_files,
                    "records_imported": 0
                }
            
            # 3. 批量插入数据库
            logger.info(f"准备插入 {len(all_records)} 条评论记录到数据库...")
            success = await self.review_repository.batch_insert_reviews(all_records)
            
            if success:
                logger.info(f"批次 {batch_id} 评论数据导入成功")
                return {
                    "status": "success",
                    "message": f"成功导入批次 {batch_id} 的评论数据",
                    "batch_id": batch_id,
                    "files_processed": processed_files,
                    "records_imported": len(all_records)
                }
            else:
                logger.error(f"批次 {batch_id} 评论数据导入失败")
                return {
                    "status": "error",
                    "message": f"批次 {batch_id} 评论数据导入失败",
                    "batch_id": batch_id,
                    "files_processed": processed_files,
                    "records_imported": 0
                }
            
        except Exception as e:
            logger.error(f"导入批次 {batch_id} 评论数据时出现异常: {e}")
            return {
                "status": "error",
                "message": f"导入异常: {str(e)}",
                "batch_id": batch_id,
                "files_processed": 0,
                "records_imported": 0
            }
    
    async def get_import_status(self, batch_id: int) -> Dict[str, Any]:
        """
        获取批次导入状态
        
        Args:
            batch_id: 批次ID
            
        Returns:
            Dict[str, Any]: 导入状态信息
        """
        try:
            # 统计数据库中的评论数量
            db_count = await self.review_repository.count_reviews_by_batch(batch_id)
            
            # 发现文件数量
            review_files = self._discover_batch_review_files(batch_id)
            
            return {
                "batch_id": batch_id,
                "files_found": len(review_files),
                "reviews_in_database": db_count,
                "status": "imported" if db_count > 0 else "pending"
            }
            
        except Exception as e:
            logger.error(f"获取批次 {batch_id} 导入状态时出错: {e}")
            return {
                "batch_id": batch_id,
                "error": str(e),
                "status": "error"
            } 