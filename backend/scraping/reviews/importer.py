import logging
from typing import Dict, Any, Optional
from core.repositories.amazon_review_repository import AmazonReviewRepository
from core.database.connection import get_supabase_service_client

logger = logging.getLogger(__name__)

class ReviewImporter:
    """评论数据导入器 - 负责将评论爬取结果导入到数据库"""
    
    def __init__(self):
        # 获取Supabase客户端
        self.supabase_client = get_supabase_service_client()
        
        # 初始化评论仓库
        self.review_repository = AmazonReviewRepository(self.supabase_client)
    
    async def import_batch_reviews(self, batch_id: int) -> Dict[str, Any]:
        """
        导入批次评论数据到数据库
        
        Args:
            batch_id: 批次ID
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        try:
            logger.info(f"开始导入批次 {batch_id} 的评论数据...")
            
            # 调用评论仓库的批量导入方法
            result = await self.review_repository.import_batch_reviews(batch_id)
            
            logger.info(f"批次 {batch_id} 评论导入完成: {result}")
            
            return {
                "status": "success",
                "message": f"成功导入批次 {batch_id} 的评论数据",
                "batch_id": batch_id,
                **result
            }
            
        except Exception as e:
            logger.error(f"导入批次 {batch_id} 评论数据时出错: {e}")
            return {
                "status": "error",
                "message": f"导入失败: {str(e)}",
                "batch_id": batch_id,
                "reviews_imported": 0
            }
    
    async def import_single_review_file(self, json_file_path: str, batch_id: Optional[int] = None) -> Dict[str, Any]:
        """
        导入单个评论文件到数据库
        
        Args:
            json_file_path: JSON文件路径
            batch_id: 批次ID（可选）
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        try:
            logger.info(f"开始导入评论文件: {json_file_path}")
            
            # 单文件导入暂不支持，建议使用批量导入
            raise NotImplementedError("单文件导入暂不支持，请使用批量导入功能")
            
            logger.info(f"评论文件导入完成: {result}")
            
            return {
                "status": "success",
                "message": f"成功导入评论文件",
                "file_path": json_file_path,
                "batch_id": batch_id,
                **result
            }
            
        except Exception as e:
            logger.error(f"导入评论文件时出错: {e}")
            return {
                "status": "error",
                "message": f"导入失败: {str(e)}",
                "file_path": json_file_path,
                "batch_id": batch_id,
                "reviews_imported": 0
            }
    
    async def get_import_status(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """
        获取批次评论导入状态
        
        Args:
            batch_id: 批次ID
            
        Returns:
            Optional[Dict[str, Any]]: 状态信息
        """
        try:
            # 获取批次评论统计
            review_count = await self.review_repository.count_reviews_by_batch(batch_id)
            reviews = await self.review_repository.get_reviews_by_batch(batch_id)
            
            if review_count == 0:
                return None
            
            # 基础统计信息
            stats = {
                "total_reviews": review_count,
                "unique_asins": len(set(r.get('asin', '') for r in reviews if r.get('asin'))),
                "average_rating": 0,
                "latest_review_date": None,
                "earliest_review_date": None
            }
            
            # 计算平均评分和日期范围
            if reviews:
                ratings = [float(r.get('rating', 0)) for r in reviews if r.get('rating') and str(r.get('rating')).replace('.', '').isdigit()]
                if ratings:
                    stats["average_rating"] = sum(ratings) / len(ratings)
                
                dates = [r.get('review_date', '') for r in reviews if r.get('review_date')]
                if dates:
                    dates_sorted = sorted(dates)
                    stats["earliest_review_date"] = dates_sorted[0]
                    stats["latest_review_date"] = dates_sorted[-1]
            
            # stats 已经在上面构建了，不需要检查
            
            return {
                "batch_id": batch_id,
                "total_reviews": stats.get("total_reviews", 0),
                "unique_asins": stats.get("unique_asins", 0),
                "average_rating": stats.get("average_rating", 0),
                "latest_review_date": stats.get("latest_review_date"),
                "earliest_review_date": stats.get("earliest_review_date")
            }
            
        except Exception as e:
            logger.error(f"获取导入状态时出错: {e}")
            return None
    
    async def retry_import(self, batch_id: int, max_retries: int = 3) -> Dict[str, Any]:
        """
        重试导入机制
        
        Args:
            batch_id: 批次ID
            max_retries: 最大重试次数
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试导入批次 {batch_id} (第 {attempt + 1} 次)")
                result = await self.import_batch_reviews(batch_id)
                
                if result.get("status") == "success":
                    logger.info(f"导入成功 (第 {attempt + 1} 次尝试)")
                    return result
                else:
                    last_error = result.get("message", "Unknown error")
                    logger.warning(f"导入失败 (第 {attempt + 1} 次): {last_error}")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"导入尝试 {attempt + 1} 出现异常: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"等待后重试...")
                import asyncio
                await asyncio.sleep(2)  # 等待2秒后重试
        
        return {
            "status": "error",
            "message": f"重试 {max_retries} 次后仍然失败: {last_error}",
            "batch_id": batch_id,
            "reviews_imported": 0
        } 