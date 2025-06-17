import logging
import asyncio
from typing import Dict, Any, Optional

from .products.scraper import ProductScraper
from .products.importer import ProductImporter
from .reviews.scraper import ReviewScraper
from .reviews.importer import ReviewImporter

logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """爬取流程编排器 - 统一管理商品和评论的爬取流程"""
    
    def __init__(self):
        # 初始化各个组件
        self.product_scraper = ProductScraper()
        self.product_importer = ProductImporter()
        self.review_scraper = ReviewScraper()
        self.review_importer = ReviewImporter()
    
    async def process_url(self, url: str, max_products: int = 100, 
                         scrape_reviews: bool = True, 
                         review_coverage_months: int = 6) -> Dict[str, Any]:
        """
        完整的URL处理流程：爬取商品 → 导入商品 → 爬取评论 → 导入评论
        
        Args:
            url: Amazon URL
            max_products: 最大商品数量
            scrape_reviews: 是否爬取评论
            review_coverage_months: 评论覆盖月数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"开始处理URL: {url}")
        
        result = {
            "url": url,
            "products_phase": {},
            "reviews_phase": {},
            "overall_status": "pending"
        }
        
        try:
            # Phase 1: 爬取商品
            logger.info("Phase 1: 开始爬取商品...")
            product_scrape_result = await self.product_scraper.scrape_from_url(url, max_products)
            result["products_phase"]["scraping"] = product_scrape_result
            
            if product_scrape_result.get("status") != "success":
                result["overall_status"] = "product_scraping_failed"
                return result
            
            # Phase 2: 导入商品数据
            logger.info("Phase 2: 开始导入商品数据...")
            json_file_path = product_scrape_result.get("file_path")
            if not json_file_path:
                result["overall_status"] = "no_product_file"
                return result
            
            product_import_result = await self.product_importer.import_products(json_file_path)
            result["products_phase"]["importing"] = product_import_result
            
            if product_import_result.get("status") != "success":
                result["overall_status"] = "product_importing_failed"
                return result
            
            batch_id = product_import_result.get("batch_id")
            if not batch_id:
                result["overall_status"] = "no_batch_id"
                return result
            
            result["batch_id"] = batch_id
            
            # Phase 3: 爬取评论 (如果启用)
            if scrape_reviews:
                logger.info(f"Phase 3: 开始爬取批次 {batch_id} 的评论...")
                review_scrape_result = await self.review_scraper.scrape_for_batch(
                    batch_id, review_coverage_months
                )
                result["reviews_phase"]["scraping"] = review_scrape_result
                
                if review_scrape_result.get("status") in ["success", "partial_success"]:
                    # Phase 4: 导入评论数据
                    logger.info(f"Phase 4: 开始导入批次 {batch_id} 的评论数据...")
                    review_import_result = await self.review_importer.import_batch_reviews(batch_id)
                    result["reviews_phase"]["importing"] = review_import_result
                    
                    if review_import_result.get("status") == "success":
                        result["overall_status"] = "completed"
                    else:
                        result["overall_status"] = "review_importing_failed"
                else:
                    result["overall_status"] = "review_scraping_failed"
            else:
                result["overall_status"] = "products_only_completed"
            
            logger.info(f"URL处理完成: {result['overall_status']}")
            return result
            
        except Exception as e:
            logger.error(f"URL处理过程中出现异常: {e}")
            result["overall_status"] = "exception"
            result["error"] = str(e)
            return result
    
    async def scrape_products_only(self, url: str, max_products: int = 100) -> Dict[str, Any]:
        """
        仅爬取和导入商品（不包括评论）
        
        Args:
            url: Amazon URL
            max_products: 最大商品数量
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"开始仅处理商品: {url}")
        
        try:
            # 爬取商品
            scrape_result = await self.product_scraper.scrape_from_url(url, max_products)
            
            if scrape_result.get("status") != "success":
                return {
                    "status": "scraping_failed",
                    "scraping_result": scrape_result
                }
            
            # 导入商品
            json_file_path = scrape_result.get("file_path")
            import_result = await self.product_importer.import_products(json_file_path)
            
            return {
                "status": "success" if import_result.get("status") == "success" else "importing_failed",
                "scraping_result": scrape_result,
                "importing_result": import_result,
                "batch_id": import_result.get("batch_id")
            }
            
        except Exception as e:
            logger.error(f"仅处理商品时出现异常: {e}")
            return {
                "status": "exception",
                "error": str(e)
            }
    
    async def scrape_reviews_only(self, batch_id: int, review_coverage_months: int = 6) -> Dict[str, Any]:
        """
        仅爬取和导入评论（商品已存在）
        
        Args:
            batch_id: 批次ID
            review_coverage_months: 评论覆盖月数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"开始仅处理评论: batch_id={batch_id}")
        
        try:
            # 爬取评论
            scrape_result = await self.review_scraper.scrape_for_batch(batch_id, review_coverage_months)
            
            if scrape_result.get("status") not in ["success", "partial_success"]:
                return {
                    "status": "scraping_failed",
                    "scraping_result": scrape_result
                }
            
            # 导入评论
            import_result = await self.review_importer.import_batch_reviews(batch_id)
            
            return {
                "status": "success" if import_result.get("status") == "success" else "importing_failed",
                "scraping_result": scrape_result,
                "importing_result": import_result,
                "batch_id": batch_id
            }
            
        except Exception as e:
            logger.error(f"仅处理评论时出现异常: {e}")
            return {
                "status": "exception",
                "error": str(e)
            }
    
    async def retry_failed_import(self, json_file_path: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        重试失败的商品导入
        
        Args:
            json_file_path: JSON文件路径
            max_retries: 最大重试次数
            
        Returns:
            Dict[str, Any]: 重试结果
        """
        return await self.product_importer.retry_import(json_file_path, max_retries)
    
    async def retry_failed_review_import(self, batch_id: int, max_retries: int = 3) -> Dict[str, Any]:
        """
        重试失败的评论导入
        
        Args:
            batch_id: 批次ID
            max_retries: 最大重试次数
            
        Returns:
            Dict[str, Any]: 重试结果
        """
        return await self.review_importer.retry_import(batch_id, max_retries)
    
    async def get_process_status(self, batch_id: Optional[int] = None, 
                               request_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取处理状态
        
        Args:
            batch_id: 批次ID
            request_id: 请求ID
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            status = {}
            
            if batch_id or request_id:
                # 获取商品导入状态
                product_status = await self.product_importer.get_import_status(batch_id or request_id)
                if product_status:
                    status["products"] = product_status
                
                # 获取评论导入状态
                if batch_id:
                    review_status = await self.review_importer.get_import_status(batch_id)
                    if review_status:
                        status["reviews"] = review_status
            
            return status
            
        except Exception as e:
            logger.error(f"获取处理状态时出错: {e}")
            return {"error": str(e)} 