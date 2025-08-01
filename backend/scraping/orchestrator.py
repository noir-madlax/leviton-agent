import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional

from .products.scraper import ProductScraper
from .products.importer import ProductImporter
from .reviews.scraper import ReviewScraper
from .reviews.importer import ReviewImporter
from .common.quality_analyzer import DataQualityAnalyzer

# 类别修复功能
import importlib.util
from pathlib import Path

def _import_category_extractor():
    """动态导入CategoryExtractor"""
    category_fix_path = Path(__file__).parent / "rerun-failed-request" / "category-fix" / "extract_categories_from_json.py"
    spec = importlib.util.spec_from_file_location("extract_categories_from_json", category_fix_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CategoryExtractor

# Data transformation integration
from data_transformation.services.transformation_service import DataTransformationService
from data_transformation.services.review_transformation_service import ReviewTransformationService
from data_transformation.models import TransformationConfig

# Database access
from core.database.connection import get_supabase_service_client
from core.repositories.scraping_request_repository import ScrapingRequestRepository

logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """爬取流程编排器 - 统一管理商品和评论的爬取流程"""
    
    def __init__(self):
        # 初始化各个组件
        self.product_scraper = ProductScraper()
        self.product_importer = ProductImporter()
        self.review_scraper = ReviewScraper()
        self.review_importer = ReviewImporter()
        self.quality_analyzer = DataQualityAnalyzer()
        
        # 初始化类别修复组件
        CategoryExtractor = _import_category_extractor()
        self.category_extractor = CategoryExtractor()
        
        # 初始化数据库访问
        self.supabase_client = get_supabase_service_client()
        self.request_repository = ScrapingRequestRepository(self.supabase_client)
    
    async def process_url(self, url: str, max_products: int = 100, 
                         scrape_reviews: bool = True, 
                         review_coverage_months: int = 6, max_reviews: int = 30,
                         force_scrape_reviews: bool = False, force_scrape_products: bool = False,
                         force_import: bool = False, force_transformation: bool = False) -> Dict[str, Any]:
        """
        完整的URL处理流程：爬取商品 → 导入商品 → 爬取评论 → 导入评论
        
        Args:
            url: Amazon URL
            max_products: 最大商品数量
            scrape_reviews: 是否爬取评论
            review_coverage_months: 评论覆盖月数
            max_reviews: 最大评论数量限制
            force_scrape_reviews: 是否强制爬取评论，忽略现有文件和数据库记录
            force_scrape_products: 是否强制爬取商品，忽略现有文件和数据库记录
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        start_time = time.time()
        logger.info(f"开始处理URL: {url}")
        
        # 初始化结果和统计
        result = {
            "url": url,
            "products_phase": {},
            "reviews_phase": {},
            "overall_status": "pending",
            "execution_stats": {
                "start_time": datetime.now().isoformat(),
                "phase_durations": {},
                "api_calls": {
                    "category_api": 0,
                    "product_details_api": 0,
                    "reviews_api": 0,
                    "total": 0
                }
            },
            "data_quality": {}
        }
        
        try:
            # Phase 1: 爬取商品
            logger.info("Phase 1: 开始爬取商品...")
            phase1_start = time.time()
            
            product_scrape_result = await self.product_scraper.scrape_from_url(
                url, max_products, 
                force_scrape=force_scrape_products,
                force_import=force_import,
                force_transformation=force_transformation
            )
            result["products_phase"]["scraping"] = product_scrape_result
            
            phase1_duration = time.time() - phase1_start
            result["execution_stats"]["phase_durations"]["product_scraping"] = round(phase1_duration, 2)
            
            # 统计API调用次数
            if product_scrape_result.get("status") == "success":
                # Category API调用1次，Product Details API调用N次（N=产品数量）
                products_count = product_scrape_result.get("products_scraped", 0)
                result["execution_stats"]["api_calls"]["category_api"] = 1
                result["execution_stats"]["api_calls"]["product_details_api"] = products_count
                result["execution_stats"]["api_calls"]["total"] += (1 + products_count)
            
            # 记录跳过的详细信息到日志
            if product_scrape_result.get("status") == "skipped":
                skip_details = product_scrape_result.get("skip_details", {})
                logger.info(f"🔄 产品爬取已智能跳过 - {skip_details.get('data_source', '未知来源')}: "
                           f"{skip_details.get('existing_products_count', 0)}/{skip_details.get('target_products', 0)} 产品")
            
            # Only exit early if product scraping actually failed (not just skipped)
            # When products are skipped, we should still attempt review scraping for individual ASIN requests
            if product_scrape_result.get("status") not in ["success", "skipped"]:
                result["overall_status"] = "product_scraping_failed"
                result["execution_stats"]["end_time"] = datetime.now().isoformat()
                result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
                return result
            
            # Phase 2: 导入商品数据
            logger.info("Phase 2: 开始导入商品数据...")
            phase2_start = time.time()
            
            json_file_path = product_scrape_result.get("file_path")
            should_import = force_import or product_scrape_result.get("status") == "success"
            
            # Handle force import scenario - get existing batch_id if available
            existing_batch_id = product_scrape_result.get("batch_id")
            
            if not json_file_path and not force_import:
                result["overall_status"] = "no_product_file"
                result["execution_stats"]["end_time"] = datetime.now().isoformat()
                result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
                return result
            elif not json_file_path and force_import:
                # Handle case where scraping was skipped but we want to force import
                logger.info("强制导入: 尝试使用现有文件路径或跳过的结果")
                json_file_path = product_scrape_result.get("existing_file_path")
            
            if should_import and json_file_path:
                product_import_result = await self.product_importer.import_products(
                    json_file_path, request_id=None, force_import=force_import
                )
                result["products_phase"]["importing"] = product_import_result
            elif force_import and existing_batch_id:
                # Use existing batch_id when scraping was skipped but we have database records
                logger.info(f"跳过导入，使用现有批次ID: {existing_batch_id}")
                product_import_result = {
                    "status": "success", 
                    "message": f"Using existing batch_id {existing_batch_id}",
                    "batch_id": existing_batch_id,
                    "request_id": existing_batch_id
                }
                result["products_phase"]["importing"] = product_import_result
            else:
                # 提供更详细的跳过信息
                if product_scrape_result.get("status") == "skipped":
                    skip_details = product_scrape_result.get("skip_details", {})
                    logger.info(f"🔄 智能跳过商品导入 - 数据已存在: {skip_details.get('data_source', '')}中已有{skip_details.get('existing_products_count', 0)}个产品")
                    import_message = f"Smart skip - data exists ({skip_details.get('data_source', 'unknown source')})"
                else:
                    logger.info("跳过商品导入 (没有文件或未强制导入)")
                    import_message = "Import skipped - no file or force_import not set"
                
                product_import_result = {
                    "status": "skipped",
                    "message": import_message,
                    "batch_id": existing_batch_id,  # Preserve existing batch_id if available
                    "request_id": existing_batch_id
                }
                result["products_phase"]["importing"] = product_import_result
            
            phase2_duration = time.time() - phase2_start
            result["execution_stats"]["phase_durations"]["product_importing"] = round(phase2_duration, 2)
            
            should_continue_transformation = (
                force_transformation or 
                product_import_result.get("status") == "success"
            )
            
            # Allow workflow to continue to reviews even if transformation is skipped for individual ASINs
            should_continue_to_reviews = scrape_reviews and product_import_result.get("batch_id") is not None
            
            if not should_continue_transformation and not should_continue_to_reviews:
                if not force_transformation:
                    # 检查是否是智能跳过的情况
                    if (product_scrape_result.get("status") == "skipped" and 
                        product_import_result.get("status") == "skipped"):
                        logger.info("🔄 完整流程智能跳过 - 数据已存在，无需重复处理")
                        
                        # 构建详细的跳过状态信息
                        skip_details = product_scrape_result.get("skip_details", {})
                        skip_type = product_scrape_result.get("skip_type", "unknown")
                        data_source = skip_details.get("data_source", "unknown")
                        existing_count = skip_details.get("existing_products_count", 0)
                        target_count = skip_details.get("target_products", 0)
                        
                        if skip_type == "local_file":
                            result["overall_status"] = f"Smart Skip - Local File Exists ({existing_count}/{target_count} products)"
                        elif skip_type == "database":
                            batch_id = skip_details.get("batch_id", "N/A")
                            result["overall_status"] = f"Smart Skip - Database Exists (batch {batch_id}: {existing_count}/{target_count} products)"
                        else:
                            result["overall_status"] = f"Smart Skip - Data Exists ({existing_count} products)"
                            
                        result["skip_reason"] = {
                            "scraping": product_scrape_result.get("skip_details", {}),
                            "importing": "Data exists in database"
                        }
                    else:
                        result["overall_status"] = "product_importing_failed"
                    result["execution_stats"]["end_time"] = datetime.now().isoformat()
                    result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
                    return result
                else:
                    logger.info("强制执行转换，尽管导入可能失败")
            
            batch_id = product_import_result.get("batch_id")
            if not batch_id and not force_transformation:
                result["overall_status"] = "no_batch_id"
                return result
            
            result["batch_id"] = batch_id
            
            # Phase 2.1: 导入类别信息
            logger.info("Phase 2.1: 开始导入类别信息...")
            phase21_start = time.time()
            
            category_import_result = await self._import_categories_from_json(json_file_path)
            result["categories_phase"] = category_import_result
            
            phase21_duration = time.time() - phase21_start
            result["execution_stats"]["phase_durations"]["category_importing"] = round(phase21_duration, 2)
            
            # 注意：类别导入失败不阻断主流程，只记录日志
            if category_import_result.get('status') != 'success':
                logger.warning(f"类别导入未完全成功，但继续主流程: {category_import_result.get('message', 'Unknown error')}")
            
            # Phase 2.5: 数据转换 (新增)
            logger.info(f"Phase 2.5: 开始转换批次 {batch_id} 的数据...")
            phase25_start = time.time()
            
            transformation_result = await self._transform_batch_data(batch_id, product_import_result.get("request_id"))
            result["transformation_phase"] = transformation_result
            
            phase25_duration = time.time() - phase25_start
            result["execution_stats"]["phase_durations"]["data_transformation"] = round(phase25_duration, 2)
            
            if not transformation_result.get("success"):
                result["overall_status"] = "transformation_failed"
                result["execution_stats"]["end_time"] = datetime.now().isoformat()
                result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
                return result
            
            # Phase 2.6: 数据质量分析
            logger.info("Phase 2.6: 开始数据质量分析...")
            await self._analyze_data_quality(result, json_file_path, product_import_result)
            
            # Phase 3: 爬取评论 (如果启用)
            if scrape_reviews:
                logger.info(f"Phase 3: 开始爬取批次 {batch_id} 的评论...")
                phase3_start = time.time()
                
                # For individual product URLs/ASINs, we should attempt review scraping even if product scraping was skipped
                # This ensures that when users specify specific ASINs, they get the reviews they requested
                review_batch_id = batch_id
                if batch_id is None and product_scrape_result.get("status") == "skipped":
                    # If product scraping was skipped but we have an existing batch_id from the skip result, use it
                    existing_batch_id = product_scrape_result.get("batch_id")
                    if existing_batch_id:
                        logger.info(f"产品爬取被跳过，但找到现有批次 {existing_batch_id}，将用于评论爬取")
                        review_batch_id = existing_batch_id
                
                if review_batch_id is not None:
                    review_scrape_result = await self.review_scraper.scrape_for_batch(
                        review_batch_id, review_coverage_months, 
                        force_scrape=force_scrape_reviews, 
                        max_reviews=max_reviews
                    )
                    
                    phase3_duration = time.time() - phase3_start
                    result["execution_stats"]["phase_durations"]["review_scraping"] = round(phase3_duration, 2)
                    result["review_scraping_result"] = review_scrape_result
                    
                    # 导入评论数据 (如果启用)
                    if review_scrape_result.get("status") in ["success", "partial_success"]:
                        logger.info(f"Phase 4: 开始导入评论数据...")
                        phase4_start = time.time()
                        
                        review_import_result = await self.review_importer.import_batch_reviews(review_batch_id)
                        
                        phase4_duration = time.time() - phase4_start
                        result["execution_stats"]["phase_durations"]["review_importing"] = round(phase4_duration, 2)
                        result["review_importing_result"] = review_import_result
                        
                        # 🔥 修复：更新数据库状态 - 无论导入成功还是失败都要更新
                        request_id = await self._get_request_id_by_batch_id(review_batch_id)
                        if request_id:
                            await self._update_review_status_in_db(request_id, review_scrape_result, review_import_result)
                        else:
                            logger.warning(f"⚠️ 无法找到批次 {review_batch_id} 对应的请求ID，跳过状态更新")
                        
                        logger.info(f"✅ 评论导入完成: {review_import_result}")
                    else:
                        logger.warning(f"⚠️ 评论爬取状态不成功，跳过导入: {review_scrape_result.get('status')}")
                        result["review_importing_result"] = {
                            "status": "skipped",
                            "reason": "review_scraping_failed"
                        }
                        
                        # 🔥 修复：爬取失败时也要更新状态
                        request_id = await self._get_request_id_by_batch_id(review_batch_id)
                        if request_id:
                            failed_import_result = {"status": "skipped", "reason": "review_scraping_failed"}
                            await self._update_review_status_in_db(request_id, review_scrape_result, failed_import_result)
                else:
                    logger.warning("⚠️ 无法确定批次ID，跳过评论爬取")
                    result["review_scraping_result"] = {
                        "status": "skipped",
                        "reason": "no_batch_id_available"
                    }
            else:
                logger.info("⏩ 跳过评论爬取 (scrape_reviews=False)")
            
            # 添加完成时间统计
            result["execution_stats"]["end_time"] = datetime.now().isoformat()
            result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
            
            logger.info(f"URL处理完成: {result['overall_status']}, 总耗时: {result['execution_stats']['total_duration']}秒")
            return result
            
        except Exception as e:
            logger.error(f"URL处理过程中出现异常: {e}")
            result["overall_status"] = "exception"
            result["error"] = str(e)
            result["execution_stats"]["end_time"] = datetime.now().isoformat()
            result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
            return result
    
    async def scrape_products_only(self, url: str, max_products: int = 100, 
                                  force_scrape: bool = False,
                                  force_import: bool = False, 
                                  force_transformation: bool = False) -> Dict[str, Any]:
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
            scrape_result = await self.product_scraper.scrape_from_url(
                url, max_products, 
                force_scrape=force_scrape,
                force_import=force_import,
                force_transformation=force_transformation
            )
            
            should_import = force_import or scrape_result.get("status") == "success"
            if not should_import:
                return {
                    "status": "scraping_failed",
                    "scraping_result": scrape_result
                }
            
            # 导入商品
            json_file_path = scrape_result.get("file_path") or scrape_result.get("existing_file_path")
            if json_file_path:
                import_result = await self.product_importer.import_products(
                    json_file_path, request_id=None, force_import=force_import
                )
            else:
                import_result = {
                    "status": "skipped",
                    "message": "No file available for import",
                    "batch_id": None,
                    "request_id": None
                }
            
            should_transform = force_transformation or import_result.get("status") == "success"
            if not should_transform:
                return {
                    "status": "importing_failed",
                    "scraping_result": scrape_result,
                    "importing_result": import_result
                }
            
            batch_id = import_result.get("batch_id")
            
            # 类别导入
            if json_file_path:
                category_import_result = await self._import_categories_from_json(json_file_path)
            else:
                category_import_result = {"status": "skipped", "message": "No JSON file path available"}
            
            # 数据转换
            if batch_id or force_transformation:
                transformation_result = await self._transform_batch_data(
                    batch_id, import_result.get("request_id")
                )
            else:
                transformation_result = {
                    "success": False,
                    "error": "No batch_id available for transformation"
                }
            
            return {
                "status": "success" if transformation_result.get("success") else "transformation_failed",
                "scraping_result": scrape_result,
                "importing_result": import_result,
                "category_import_result": category_import_result,
                "transformation_result": transformation_result,
                "batch_id": batch_id
            }
            
        except Exception as e:
            logger.error(f"仅处理商品时出现异常: {e}")
            return {
                "status": "exception",
                "error": str(e)
            }
    
    async def scrape_reviews_only(self, batch_id: int, review_coverage_months: int = 6, force_scrape: bool = False, max_reviews: int = 30) -> Dict[str, Any]:
        """
        仅爬取和导入评论（商品已存在）
        
        Args:
            batch_id: 批次ID
            review_coverage_months: 评论覆盖月数
            force_scrape: 是否强制爬取，忽略现有文件
            max_reviews: 最大评论数量限制
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"开始仅处理评论: batch_id={batch_id}, force_scrape={force_scrape}, max_reviews={max_reviews}")
        
        try:
            # 爬取评论
            scrape_result = await self.review_scraper.scrape_for_batch(batch_id, review_coverage_months, force_scrape=force_scrape, max_reviews=max_reviews)
            
            if scrape_result.get("status") not in ["success", "partial_success"]:
                # 需要获取request_id来更新状态
                request_id = await self._get_request_id_by_batch_id(batch_id)
                if request_id:
                    failed_import_result = {
                        "status": "not_attempted", 
                        "message": "Import not attempted due to scraping failure"
                    }
                    await self._update_review_status_in_db(request_id, scrape_result, failed_import_result)
                
                return {
                    "status": "scraping_failed",
                    "scraping_result": scrape_result,
                    "batch_id": batch_id
                }
            
            # 导入评论
            import_result = await self.review_importer.import_batch_reviews(batch_id)
            
            # 转换评论数据 (如果导入成功)
            if import_result.get("status") == "success":
                logger.info(f"开始转换批次 {batch_id} 的评论数据...")
                request_id = await self._get_request_id_by_batch_id(batch_id)
                transformation_result = await self._transform_review_data(batch_id, request_id)
                
                # 更新数据库状态
                if request_id:
                    await self._update_review_status_in_db(request_id, scrape_result, import_result)
                
                return {
                    "status": "success" if transformation_result.get("success") else "transformation_failed",
                    "scraping_result": scrape_result,
                    "importing_result": import_result,
                    "transformation_result": transformation_result,
                    "batch_id": batch_id
                }
            else:
                # 更新数据库状态
                request_id = await self._get_request_id_by_batch_id(batch_id)
                if request_id:
                    await self._update_review_status_in_db(request_id, scrape_result, import_result)
                
                return {
                    "status": "importing_failed",
                    "scraping_result": scrape_result,
                    "importing_result": import_result,
                    "batch_id": batch_id
                }
            
        except Exception as e:
            logger.error(f"仅处理评论时出现异常: {e}")
            # 尝试更新异常状态
            try:
                request_id = await self._get_request_id_by_batch_id(batch_id)
                if request_id:
                    exception_scrape_result = {
                        "status": "error",
                        "message": f"Exception during review processing: {str(e)}",
                        "error": str(e)
                    }
                    failed_import_result = {
                        "status": "not_attempted",
                        "message": "Import not attempted due to exception"
                    }
                    await self._update_review_status_in_db(request_id, exception_scrape_result, failed_import_result)
            except Exception as update_error:
                logger.error(f"更新异常状态时出错: {update_error}")
            
            return {
                "status": "exception",
                "error": str(e),
                "batch_id": batch_id
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
    
    async def create_async_task(self, url: str, max_products: int = 100,
                              scrape_reviews: bool = True,
                              review_coverage_months: int = 6,
                              max_reviews: int = 30) -> Optional[int]:
        """
        创建异步爬取任务
        
        Args:
            url: Amazon URL
            max_products: 最大商品数量
            scrape_reviews: 是否爬取评论
            review_coverage_months: 评论覆盖月数
            max_reviews: 最大评论数量
            
        Returns:
            Optional[int]: 任务ID（request_id），失败返回None
        """
        try:
            logger.info(f"创建异步爬取任务: {url}")
            
            # 🔥 从URL推断请求类型 - 使用数据库约束允许的值
            request_type = 'search'  # 默认使用已知有效的类型
            search_term = None
            category_id = None
            
            if '/dp/' in url or '/gp/product/' in url:
                request_type = 'product'
            elif '/s?' in url:
                request_type = 'search'
                # 尝试从URL提取搜索词
                if 'k=' in url:
                    import urllib.parse
                    parsed_url = urllib.parse.urlparse(url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    search_term = query_params.get('k', [None])[0]
            elif 'node=' in url or '/b?' in url:
                # 🔥 临时使用 'search' 类型避免约束错误
                request_type = 'search'
                # 从URL提取category_id
                import re
                node_match = re.search(r'node=(\d+)', url)
                if node_match:
                    category_id = node_match.group(1)
            
            # 创建初始的爬取请求记录
            request_data = {
                'request_type': request_type,
                'search_term': search_term,
                'category_id': category_id,
                'amazon_domain': 'amazon.com',
                'products_scraped': 0,
                'request_metadata': {
                    'url': url,
                    'max_products': max_products,
                    'scrape_reviews': scrape_reviews,
                    'review_coverage_months': review_coverage_months,
                    'max_reviews': max_reviews
                },
                'status': 'pending',  # 🔥 修复：初始状态必须是 pending
                'workflow_stage': 'pending'
            }
            
            # 创建请求记录
            request_id = await self.request_repository.create_scraping_request(request_data)
            
            if not request_id:
                logger.error("创建爬取请求记录失败")
                return None
            
            # 🔥 在后台启动异步任务
            asyncio.create_task(self._execute_background_task(
                request_id, url, max_products, scrape_reviews, 
                review_coverage_months, max_reviews
            ))
            
            logger.info(f"异步爬取任务已创建，task_id: {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"创建异步爬取任务失败: {e}")
            return None
    
    async def _execute_background_task(self, request_id: int, url: str, 
                                     max_products: int, scrape_reviews: bool,
                                     review_coverage_months: int, max_reviews: int):
        """
        在后台执行爬取任务（带实时状态更新）
        
        Args:
            request_id: 任务ID
            url: Amazon URL
            max_products: 最大商品数量
            scrape_reviews: 是否爬取评论
            review_coverage_months: 评论覆盖月数
            max_reviews: 最大评论数量
        """
        try:
            logger.info(f"开始执行后台爬取任务 {request_id}: {url}")
            
            # Phase 1: 爬取商品
            # 在后台任务开始时，将状态从 'pending' 更新为 'processing'（数据库约束允许的状态）
            await self.request_repository.update_request_status(
                request_id, 'processing', 
                additional_data={'workflow_stage': 'product_scraping'}
            )
            
            product_scrape_result = await self.product_scraper.scrape_from_url(
                url, max_products
            )
            
            if product_scrape_result.get("status") not in ["success", "skipped"]:
                await self.request_repository.update_request_status(
                    request_id, 'failed',
                    additional_data={
                        'workflow_stage': 'failed',
                        'error_message': '产品爬取失败'
                    }
                )
                return
            
            # Phase 2: 导入商品数据
            # 只更新 workflow_stage，不更新主状态
            await self.request_repository.update_request_status(
                request_id, None,
                additional_data={'workflow_stage': 'product_importing'}
            )
            
            json_file_path = product_scrape_result.get("file_path")
            product_import_result = None
            
            if json_file_path and product_scrape_result.get("status") == "success":
                # 🔥 修复：传入 request_id 以更新现有记录，避免重复创建
                product_import_result = await self.product_importer.import_products(json_file_path, request_id)
                
                if product_import_result.get("status") != "success":
                    await self.request_repository.update_request_status(
                        request_id, 'failed',
                        additional_data={
                            'workflow_stage': 'failed',
                            'error_message': f'产品导入失败: {product_import_result.get("message", "未知错误")}'
                        }
                    )
                    return
            elif product_scrape_result.get("status") == "skipped":
                # 🔥 修复：处理跳过的情况，确保有有效的batch_id
                batch_id = product_scrape_result.get("batch_id")
                existing_file_path = product_scrape_result.get("existing_file_path")
                
                if batch_id:
                    # 如果有batch_id（数据库跳过），直接使用
                    product_import_result = {
                        "status": "success", 
                        "batch_id": batch_id,
                        "message": "使用现有数据库产品数据"
                    }
                elif existing_file_path:
                    # 如果有文件路径（本地文件跳过），执行导入获取batch_id
                    logger.info(f"🔄 智能跳过检测到本地文件，执行导入以获取batch_id: {existing_file_path}")
                    product_import_result = await self.product_importer.import_products(existing_file_path, request_id)
                else:
                    # 兜底方案：无batch_id也无文件，记录为智能跳过完成
                    logger.warning(f"⚠️  智能跳过但无有效batch_id或文件路径，将标记为完成")
                    await self.request_repository.update_request_status(
                        request_id, 'completed',
                        additional_data={
                            'workflow_stage': 'completed',
                            'products_scraped': product_scrape_result.get("products_scraped", 0),
                            'skip_reason': product_scrape_result.get("reason", "智能跳过")
                        }
                    )
                    return
            
            if not product_import_result or not product_import_result.get("batch_id"):
                await self.request_repository.update_request_status(
                    request_id, 'failed',
                    additional_data={
                        'workflow_stage': 'failed',
                        'error_message': '无法获取有效的batch_id'
                    }
                )
                return
            
            # 更新产品数量信息（🔥 移除无效字段）
            products_scraped = product_scrape_result.get("products_scraped", 0)
            await self.request_repository.update_request_status(
                request_id, None,
                additional_data={
                    'workflow_stage': 'transforming',
                    'products_scraped': products_scraped
                }
            )
            
            # Phase 3: 数据转换
            batch_id = product_import_result.get("batch_id")
            if batch_id:
                transform_result = await self._transform_batch_data(batch_id, request_id)
                
                if not transform_result.get("success", False):
                    await self.request_repository.update_request_status(
                        request_id, 'failed',
                        additional_data={
                            'workflow_stage': 'failed',
                            'error_message': '数据转换失败'
                        }
                    )
                    return
                
                # 🔥 修复：转换时间为整数类型，避免数据类型错误
                duration_seconds = transform_result.get("duration_seconds", 0)
                if isinstance(duration_seconds, float):
                    duration_seconds = int(round(duration_seconds))
                
                await self.request_repository.update_request_status(
                    request_id, None,
                    additional_data={
                        'workflow_stage': 'review_scraping' if scrape_reviews else 'completed',
                        'products_transformed': transform_result.get("processed_count", 0),
                        'transformation_duration_seconds': duration_seconds
                    }
                )
            
            # Phase 4: 爬取评论（如果需要）
            if scrape_reviews:
                await self.request_repository.update_request_status(
                    request_id, None,
                    additional_data={'workflow_stage': 'review_scraping'}
                )
                
                review_scrape_result = await self.review_scraper.scrape_for_batch(
                    product_import_result.get("batch_id"), 
                    review_coverage_months,
                    max_reviews=max_reviews
                )
                
                if review_scrape_result.get("status") in ["success", "partial_success"]:
                    # Phase 5: 导入评论数据
                    await self.request_repository.update_request_status(
                        request_id, None,
                        additional_data={'workflow_stage': 'review_importing'}
                    )
                    
                    review_import_result = await self.review_importer.import_batch_reviews(
                        product_import_result.get("batch_id")
                    )
                    
                    # Phase 6: 转换评论数据
                    if review_import_result.get("status") == "success":
                        await self.request_repository.update_request_status(
                            request_id, None,
                            additional_data={'workflow_stage': 'review_transformation'}
                        )
                        
                        review_transformation_result = await self._transform_review_data(
                            product_import_result.get("batch_id"), request_id
                        )
                        
                        # 🔥 新增：在数据库中保存评论转换的数量和耗时
                        if review_transformation_result.get("success"):
                            await self.request_repository.update_request_status(
                                request_id, None,
                                additional_data={
                                    'reviews_transformed': review_transformation_result.get('processed_count', 0),
                                    'review_transformation_duration_seconds': int(review_transformation_result.get('duration_seconds', 0))
                                }
                            )
                        
                        logger.info(f"✅ 评论转换完成: {review_transformation_result}")
                    
                    # 更新评论统计（🔥 移除无效字段）
                    reviews_scraped = review_scrape_result.get("total_reviews_scraped", 0)
                    await self.request_repository.update_request_status(
                        request_id, None,
                        additional_data={
                            'workflow_stage': 'review_transformation' if review_import_result.get("status") == "success" else 'review_importing',
                            'reviews_scraped': reviews_scraped,
                            'review_status': 'completed' if review_scrape_result.get("status") == "success" else 'partial'
                        }
                    )
            
            # 🔥 最终状态更新：只有在这里才更新主状态为 'completed'
            await self.request_repository.update_request_status(
                request_id, 'completed',
                additional_data={'workflow_stage': 'completed'}
            )
            
            logger.info(f"后台爬取任务 {request_id} 执行完成")
            
        except Exception as e:
            logger.error(f"后台爬取任务 {request_id} 执行失败: {e}")
            
            # 更新失败状态
            await self.request_repository.update_request_status(
                request_id, 'failed',
                additional_data={
                    'workflow_stage': 'failed',
                    'error_message': str(e)
                }
            )
    
    async def get_process_status(self, batch_id: Optional[int] = None, 
                               request_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取处理状态（增强版，支持实时进度查询）
        
        Args:
            batch_id: 批次ID
            request_id: 请求ID
            
        Returns:
            Dict[str, Any]: 详细状态信息
        """
        try:
            task_id = batch_id or request_id
            if not task_id:
                return {"error": "batch_id 或 request_id 必须提供一个"}
            
            # 从数据库获取任务详细状态
            request_data = await self.request_repository.get_request_by_id(task_id)
            if not request_data:
                return {"error": f"任务 {task_id} 不存在"}
            
            # 构建状态响应
            status = {
                "task_id": str(task_id),
                "batch_id": task_id,
                "url": request_data.get('request_metadata', {}).get('url', ''),
                "overall_status": request_data.get('status', 'unknown'),
                "workflow_stage": request_data.get('workflow_stage', 'unknown'),
                "created_at": request_data.get('created_at', ''),
                "updated_at": request_data.get('updated_at', ''),
            }
            
            # 根据workflow_stage构建阶段状态
            current_stage = request_data.get('workflow_stage', 'unknown')
            
            # 产品阶段状态
            if current_stage == 'product_scraping':
                status["products_phase"] = {
                    "scraping": {"status": "running", "message": "正在爬取产品数据..."},
                    "importing": {"status": "pending", "message": "等待中"},
                }
            elif current_stage == 'product_importing':
                status["products_phase"] = {
                    "scraping": {"status": "success", "products_scraped": request_data.get('products_scraped', 0)},
                    "importing": {"status": "running", "message": "正在导入产品数据..."},
                }
            elif current_stage in ['product_transformation', 'transforming']:
                status["products_phase"] = {
                    "scraping": {"status": "success", "products_scraped": request_data.get('products_scraped', 0)},
                    "importing": {"status": "success", "message": "产品导入完成"},
                }
                status["transformation_phase"] = {
                    "status": "running", 
                    "message": "正在转换产品数据..."
                }
            elif current_stage == 'review_scraping':
                status["products_phase"] = {
                    "scraping": {"status": "success", "products_scraped": request_data.get('products_scraped', 0)},
                    "importing": {"status": "success", "message": "产品处理完成"},
                }
                status["transformation_phase"] = {
                    "status": "success",
                    "processed_count": request_data.get('products_transformed', 0)
                }
                status["reviews_phase"] = {
                    "scraping": {"status": "running", "message": "正在爬取评论数据..."},
                    "importing": {"status": "pending", "message": "等待中"},
                }
            elif current_stage == 'review_importing':
                status["products_phase"] = {
                    "scraping": {"status": "success", "products_scraped": request_data.get('products_scraped', 0)},
                    "importing": {"status": "success", "message": "产品处理完成"},
                }
                status["transformation_phase"] = {
                    "status": "success",
                    "processed_count": request_data.get('products_transformed', 0)
                }
                status["reviews_phase"] = {
                    "scraping": {"status": "success", "reviews_scraped": request_data.get('reviews_scraped', 0)},
                    "importing": {"status": "running", "message": "正在导入评论数据..."},
                }
            elif current_stage == 'review_transformation':
                status["products_phase"] = {
                    "scraping": {"status": "success", "products_scraped": request_data.get('products_scraped', 0)},
                    "importing": {"status": "success", "message": "产品处理完成"},
                }
                status["transformation_phase"] = {
                    "status": "success",
                    "processed_count": request_data.get('products_transformed', 0)
                }
                status["reviews_phase"] = {
                    "scraping": {"status": "success", "reviews_scraped": request_data.get('reviews_scraped', 0)},
                    "importing": {"status": "success", "message": "评论导入完成"},
                    "transformation": {"status": "running", "message": "正在转换评论数据..."}
                }
            
            # 当任务完成时，构建一个包含所有统计数据的最终报告
            if current_stage == 'completed':
                # 基础信息
                status["products_phase"] = {
                    "scraping": {"status": "success", "products_scraped": request_data.get('products_scraped', 0)},
                    "importing": {"status": "success", "message": "产品处理完成", "products_imported": request_data.get('products_scraped', 0)},
                }
                status["transformation_phase"] = {
                    "status": "success",
                    "processed_count": request_data.get('products_transformed', 0)
                }
                status["reviews_phase"] = {
                    "scraping": {"status": "success", "reviews_scraped": request_data.get('reviews_scraped', 0)},
                    "importing": {"status": "success", "message": "评论处理完成", "reviews_imported": request_data.get('reviews_scraped', 0)},
                    "transformation": {"status": "success", "message": "评论转换完成", "processed_count": request_data.get('reviews_transformed', 0)}
                }
                status["overall_status"] = "completed"

                # 完整执行统计
                total_duration = (request_data.get('updated_at') - request_data.get('created_at')).total_seconds() if request_data.get('updated_at') and request_data.get('created_at') else 0
                
                # 安全地获取阶段耗时
                def get_duration(key):
                    val = request_data.get(key)
                    return val if isinstance(val, (int, float)) else 0

                status['execution_stats'] = {
                    'total_duration': total_duration,
                    'phase_durations': {
                        'product_scraping': get_duration('product_scraping_duration_seconds'),
                        'product_importing': get_duration('product_importing_duration_seconds'),
                        'data_transformation': get_duration('transformation_duration_seconds'),
                        'review_scraping': get_duration('review_scraping_duration_seconds'),
                        'review_importing': get_duration('review_importing_duration_seconds'),
                        'review_transformation': get_duration('review_transformation_duration_seconds'),
                    },
                    'api_calls': status.get('execution_stats', {}).get('api_calls', {})
                }
                
                # 数据质量报告
                if request_data.get('data_quality_report'):
                    status['data_quality'] = request_data['data_quality_report']

            elif current_stage == 'failed':
                status["overall_status"] = "failed"
                status["error"] = request_data.get('error_message', '任务执行失败')
            
            # API 调用统计 (对所有状态通用)
            products_scraped = request_data.get('products_scraped', 0)
            reviews_scraped = request_data.get('reviews_scraped', 0)
            category_api_calls = 1 if products_scraped > 0 else 0
            product_details_api_calls = products_scraped
            reviews_api_calls = reviews_scraped // 20 + (1 if reviews_scraped % 20 > 0 else 0) if reviews_scraped > 0 else 0
            
            if 'execution_stats' not in status:
                 status['execution_stats'] = {}
            status['execution_stats']['api_calls'] = {
                "category_api": category_api_calls,
                "product_details_api": product_details_api_calls,
                "reviews_api": reviews_api_calls,
                "total": category_api_calls + product_details_api_calls + reviews_api_calls
            }
            
            # 元数据信息
            if request_data.get('request_metadata'):
                metadata = request_data['request_metadata']
                status["max_products"] = metadata.get('max_products', 0)
                status["max_reviews"] = metadata.get('max_reviews', 0)
            
            return status
            
        except Exception as e:
            logger.error(f"获取处理状态时出错: {e}")
            return {"error": str(e)}
    

    
    async def _transform_batch_data(self, batch_id: int, request_id: Optional[int] = None) -> Dict[str, Any]:
        """调用数据转换服务处理批次数据"""
        logger.info(f"🔄 开始数据转换 - batch_id: {batch_id}, request_id: {request_id}")
        
        try:
            # 使用保守的配置，避免跳过已存在的记录（因为是新批次）
            config = TransformationConfig(
                skip_existing=False,  # 新批次不跳过
                validate_calculations=True,
                dry_run=False,
                batch_size=50  # 使用较小的批次大小
            )
            
            logger.info(f"📋 数据转换配置: skip_existing={config.skip_existing}, validate_calculations={config.validate_calculations}, dry_run={config.dry_run}")
            
            transformation_service = DataTransformationService(config)
            logger.info("✅ 数据转换服务初始化成功")
            
            result = await transformation_service.transform_batch_for_orchestrator(batch_id, request_id)
            
            logger.info(f"🎯 数据转换完成 - batch_id: {batch_id}")
            logger.info(f"📊 转换结果: success={result.success}, processed={result.processed_count}, errors={result.error_count}")
            logger.info(f"⏱️  转换耗时: {result.duration_seconds:.2f}秒")
            
            if result.errors:
                logger.warning(f"⚠️  转换过程中发现错误: {result.errors[:3]}")  # 只显示前3个错误
            
            return {
                "success": result.success,
                "processed_count": result.processed_count,
                "error_count": result.error_count,
                "duration_seconds": result.duration_seconds,
                "summary": result.summary,
                "errors": result.errors[:5] if result.errors else []  # 限制错误数量
            }
            
        except ImportError as e:
            error_msg = f"数据转换模块导入失败: {e}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "processed_count": 0,
                "error_count": 1
            }
        except Exception as e:
            error_msg = f"数据转换调用失败: {e}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "processed_count": 0,
                "error_count": 1
            }
    
    async def _transform_review_data(self, batch_id: int, request_id: Optional[int] = None) -> Dict[str, Any]:
        """调用评论转换服务处理批次评论数据"""
        logger.info(f"🔄 开始评论转换 - batch_id: {batch_id}, request_id: {request_id}")
        
        try:
            # 使用和产品转换相同的配置
            config = TransformationConfig(
                skip_existing=True,  # 跳过已存在的评论
                validate_calculations=True,
                dry_run=False,
                batch_size=100  # 评论可以使用更大的批次
            )
            
            logger.info(f"📋 评论转换配置: skip_existing={config.skip_existing}, validate_calculations={config.validate_calculations}, dry_run={config.dry_run}")
            
            review_transformation_service = ReviewTransformationService(config)
            logger.info("✅ 评论转换服务初始化成功")
            
            result = await review_transformation_service.transform_batch_for_orchestrator(batch_id, request_id)
            
            logger.info(f"🎯 评论转换完成 - batch_id: {batch_id}")
            logger.info(f"📊 转换结果: success={result.success}, processed={result.processed_count}, errors={result.error_count}")
            logger.info(f"⏱️  转换耗时: {result.duration_seconds:.2f}秒")
            
            if result.errors:
                logger.warning(f"⚠️  评论转换过程中发现错误: {result.errors[:3]}")  # 只显示前3个错误
            
            return {
                "success": result.success,
                "processed_count": result.processed_count,
                "error_count": result.error_count,
                "duration_seconds": result.duration_seconds,
                "summary": result.summary,
                "errors": result.errors[:5] if result.errors else []  # 限制错误数量
            }
            
        except ImportError as e:
            error_msg = f"评论转换模块导入失败: {e}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "processed_count": 0,
                "error_count": 1
            }
        except Exception as e:
            error_msg = f"评论转换调用失败: {e}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "processed_count": 0,
                "error_count": 1
            }

    async def _update_review_status_in_db(self, request_id: int, 
                                         scrape_result: Dict[str, Any], 
                                         import_result: Dict[str, Any]):
        """更新评论状态到 scraping_requests 表"""
        try:
            # 从抓取结果中提取评论数量信息
            reviews_scraped = 0
            review_status = "failed"
            workflow_stage = "failed"
            
            # 解析抓取结果
            if scrape_result.get("status") in ["success", "partial_success"]:
                # 从抓取结果中获取评论数量
                if "total_reviews_scraped" in scrape_result:
                    reviews_scraped = scrape_result["total_reviews_scraped"]
                elif "reviews_scraped" in scrape_result:
                    reviews_scraped = scrape_result["reviews_scraped"]
                else:
                    # 如果没有直接的数量，从产品结果中累计
                    products_results = scrape_result.get("products_results", [])
                    reviews_scraped = sum(
                        product.get("reviews_scraped", 0) 
                        for product in products_results
                    )
                
                # 根据导入结果确定最终状态
                if import_result.get("status") == "success":
                    review_status = "completed"
                    workflow_stage = "completed"
                    # 优先使用导入结果中的数量（更准确）
                    if "reviews_imported" in import_result:
                        reviews_scraped = import_result["reviews_imported"]
                else:
                    review_status = "import_failed"
                    workflow_stage = "failed"
            else:
                review_status = "scraping_failed"
                workflow_stage = "failed"
            
            # 构建元数据，包含详细的错误信息
            review_metadata = {
                "scrape_status": scrape_result.get("status"),
                "import_status": import_result.get("status"),
                "scrape_summary": scrape_result.get("summary", {}),
                "import_summary": import_result.get("summary", {}),
                "files_processed": import_result.get("files_processed", 0),
                "updated_at": datetime.now().isoformat()
            }
            
            # 添加错误信息到元数据
            if scrape_result.get("status") not in ["success", "partial_success"]:
                review_metadata["scrape_error"] = scrape_result.get("message", "Unknown scraping error")
                if "error" in scrape_result:
                    review_metadata["scrape_error_details"] = scrape_result["error"]
            
            if import_result.get("status") != "success":
                review_metadata["import_error"] = import_result.get("message", "Unknown import error")
                if "error" in import_result:
                    review_metadata["import_error_details"] = import_result["error"]
            
            # 更新数据库状态，包括workflow_stage
            success = await self.request_repository.update_review_status_with_workflow(
                request_id=request_id,
                review_status=review_status,
                reviews_scraped=reviews_scraped,
                review_metadata=review_metadata,
                workflow_stage=workflow_stage,
                set_completed_time=True
            )
            
            if success:
                logger.info(f"✅ 成功更新评论状态: request_id={request_id}, review_status={review_status}, workflow_stage={workflow_stage}, count={reviews_scraped}")
            else:
                logger.error(f"❌ 更新评论状态失败: request_id={request_id}")
                
        except Exception as e:
            logger.error(f"❌ 更新评论状态异常: {e}", exc_info=True)
    
    async def _get_request_id_by_batch_id(self, batch_id: int) -> Optional[int]:
        """根据batch_id获取对应的request_id"""
        try:
            # 从amazon_products表获取对应的request_id
            result = self.supabase_client.table('amazon_products').select('batch_id').eq('batch_id', batch_id).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                # batch_id在amazon_products表中对应scraping_requests表的id
                return batch_id
            else:
                logger.warning(f"未找到batch_id {batch_id} 对应的记录")
                return None
                
        except Exception as e:
            logger.error(f"获取request_id时出错: {e}")
            return None
    
    async def _analyze_data_quality(self, result: Dict[str, Any], json_file_path: str, product_import_result: Dict[str, Any]):
        """分析数据质量并添加到结果中"""
        try:
            logger.info("🔍 开始数据质量分析...")
            
            # 使用result_processor处理JSON数据，获得正确的字段映射
            from .common.result_processor import ScrapingResultProcessor
            processor = ScrapingResultProcessor()
            
            # 处理爬取结果，获得经过映射的产品数据
            request_data, processed_products = await processor.process_scraping_result(json_file_path)
            
            if processed_products:
                # 使用质量分析器分析处理后的数据
                quality_report = self.quality_analyzer.analyze_products_quality(processed_products)
                result["data_quality"] = quality_report
                
                logger.info(f"✅ 数据质量分析完成: 总体评分 {quality_report['overall_quality_score']}/100")
                logger.info(f"📊 关键字段覆盖率: ASIN {quality_report['field_coverage'].get('platform_id', {}).get('coverage_percent', 0)}%, "
                           f"品牌 {quality_report['field_coverage'].get('brand', {}).get('coverage_percent', 0)}%, "
                           f"销量 {quality_report['field_coverage'].get('recent_sales', {}).get('coverage_percent', 0)}%")
            else:
                result["data_quality"] = {
                    "total_products": 0,
                    "field_coverage": {},
                    "overall_quality_score": 0.0,
                    "error": "No processed product data found"
                }
                
        except Exception as e:
            logger.error(f"❌ 数据质量分析失败: {e}")
            result["data_quality"] = {
                "error": f"Data quality analysis failed: {str(e)}",
                "overall_quality_score": 0.0
            }
    
    async def _import_categories_from_json(self, json_file_path: str) -> Dict[str, Any]:
        """
        从JSON文件导入类别信息
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        try:
            logger.info(f"开始从JSON文件导入类别信息: {json_file_path}")
            
            # 使用CategoryExtractor处理JSON文件
            result = await self.category_extractor.process_json_file(json_file_path)
            
            # 记录结果
            if result.get('status') == 'success':
                categories_inserted = result.get('categories_inserted', 0)
                categories_extracted = result.get('categories_extracted', 0)
                logger.info(f"类别导入完成: 提取{categories_extracted}个, 新增{categories_inserted}个类别")
            else:
                logger.warning(f"类别导入结果: {result.get('message', 'Unknown result')}")
            
            return result
            
        except Exception as e:
            logger.error(f"类别导入过程中出现异常: {e}")
            return {
                'status': 'error',
                'message': f'类别导入失败: {str(e)}',
                'categories_extracted': 0,
                'categories_inserted': 0
            } 

    async def process_products_list(self, product_urls=None, asins=None, max_reviews=30, review_start_date=None, review_end_date=None, import_to_db=True, use_async=True, retry_failed=True, log_level="INFO", force_reviews=False, force_products=False, force_import=False, force_transformation=False, **kwargs):
        """
        Process a list of product URLs or ASINs: scrape product info and reviews for each, aggregate results.
        Args:
            product_urls (list[str]): List of Amazon product URLs.
            asins (list[str]): List of Amazon product ASINs.
            max_reviews (int): Maximum number of reviews per product.
            review_start_date (str): Only scrape reviews after this date (YYYY-MM-DD).
            review_end_date (str): Only scrape reviews before this date (YYYY-MM-DD).
            import_to_db (bool): Whether to import data to DB after scraping.
            use_async (bool): Whether to use asyncio for concurrent scraping.
            retry_failed (bool): Whether to retry failed scraping tasks.
            log_level (str): Logging level.
            **kwargs: Other parameters (ignored).
        Returns:
            dict: Aggregated results for all products.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)

        results = []
        errors = []
        tasks = []

        # Helper to process a single product URL
        async def process_single_url(url):
            try:
                return await self.process_url(url, max_products=1, scrape_reviews=True, review_coverage_months=6, max_reviews=max_reviews, force_scrape_reviews=force_reviews, force_scrape_products=force_products, force_import=force_import, force_transformation=force_transformation)
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                return {"url": url, "status": "error", "error": str(e)}

        # Helper to process a single ASIN
        async def process_single_asin(asin):
            try:
                url = f"https://www.amazon.com/dp/{asin}"
                return await self.process_url(url, max_products=1, scrape_reviews=True, review_coverage_months=6, max_reviews=max_reviews, force_scrape_reviews=force_reviews, force_scrape_products=force_products, force_import=force_import, force_transformation=force_transformation)
            except Exception as e:
                logger.error(f"Error processing ASIN {asin}: {e}")
                return {"asin": asin, "status": "error", "error": str(e)}

        if product_urls:
            if use_async:
                tasks = [process_single_url(url) for url in product_urls]
                results = await asyncio.gather(*tasks, return_exceptions=False)
            else:
                for url in product_urls:
                    results.append(await process_single_url(url))
        elif asins:
            if use_async:
                tasks = [process_single_asin(asin) for asin in asins]
                results = await asyncio.gather(*tasks, return_exceptions=False)
            else:
                for asin in asins:
                    results.append(await process_single_asin(asin))
        else:
            raise ValueError("Either product_urls or asins must be provided.")

        return {"results": results, "errors": errors, "count": len(results)} 