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

# Data transformation integration
from data_transformation.services.transformation_service import DataTransformationService
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
        
        # 初始化数据库访问
        self.supabase_client = get_supabase_service_client()
        self.request_repository = ScrapingRequestRepository(self.supabase_client)
    
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
            
            product_scrape_result = await self.product_scraper.scrape_from_url(url, max_products)
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
            
            if product_scrape_result.get("status") != "success":
                result["overall_status"] = "product_scraping_failed"
                result["execution_stats"]["end_time"] = datetime.now().isoformat()
                result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
                return result
            
            # Phase 2: 导入商品数据
            logger.info("Phase 2: 开始导入商品数据...")
            phase2_start = time.time()
            
            json_file_path = product_scrape_result.get("file_path")
            if not json_file_path:
                result["overall_status"] = "no_product_file"
                result["execution_stats"]["end_time"] = datetime.now().isoformat()
                result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
                return result
            
            product_import_result = await self.product_importer.import_products(json_file_path)
            result["products_phase"]["importing"] = product_import_result
            
            phase2_duration = time.time() - phase2_start
            result["execution_stats"]["phase_durations"]["product_importing"] = round(phase2_duration, 2)
            
            if product_import_result.get("status") != "success":
                result["overall_status"] = "product_importing_failed"
                result["execution_stats"]["end_time"] = datetime.now().isoformat()
                result["execution_stats"]["total_duration"] = round(time.time() - start_time, 2)
                return result
            
            batch_id = product_import_result.get("batch_id")
            if not batch_id:
                result["overall_status"] = "no_batch_id"
                return result
            
            result["batch_id"] = batch_id
            
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
                
                review_scrape_result = await self.review_scraper.scrape_for_batch(
                    batch_id, review_coverage_months
                )
                result["reviews_phase"]["scraping"] = review_scrape_result
                
                phase3_duration = time.time() - phase3_start
                result["execution_stats"]["phase_durations"]["review_scraping"] = round(phase3_duration, 2)
                
                # 统计评论API调用次数
                if review_scrape_result.get("status") in ["success", "partial_success"]:
                    reviews_api_calls = review_scrape_result.get("products_processed", 0)
                    result["execution_stats"]["api_calls"]["reviews_api"] = reviews_api_calls
                    result["execution_stats"]["api_calls"]["total"] += reviews_api_calls
                
                if review_scrape_result.get("status") in ["success", "partial_success"]:
                    # Phase 4: 导入评论数据
                    logger.info(f"Phase 4: 开始导入批次 {batch_id} 的评论数据...")
                    phase4_start = time.time()
                    
                    review_import_result = await self.review_importer.import_batch_reviews(batch_id)
                    result["reviews_phase"]["importing"] = review_import_result
                    
                    phase4_duration = time.time() - phase4_start
                    result["execution_stats"]["phase_durations"]["review_importing"] = round(phase4_duration, 2)
                    
                    # 更新评论状态到 scraping_requests 表
                    request_id = product_import_result.get("request_id")
                    if request_id:
                        await self._update_review_status_in_db(
                            request_id, 
                            review_scrape_result, 
                            review_import_result
                        )
                    
                    if review_import_result.get("status") == "success":
                        result["overall_status"] = "completed"
                    else:
                        result["overall_status"] = "review_importing_failed"
                else:
                    # 评论爬取失败，记录失败状态
                    result["overall_status"] = "review_scraping_failed"
                    request_id = product_import_result.get("request_id")
                    if request_id:
                        # 创建失败的导入结果
                        failed_import_result = {
                            "status": "not_attempted",
                            "message": "Import not attempted due to scraping failure"
                        }
                        await self._update_review_status_in_db(
                            request_id, 
                            review_scrape_result, 
                            failed_import_result
                        )
            else:
                result["overall_status"] = "products_only_completed"
            
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
            
            if import_result.get("status") != "success":
                return {
                    "status": "importing_failed",
                    "scraping_result": scrape_result,
                    "importing_result": import_result
                }
            
            batch_id = import_result.get("batch_id")
            
            # 数据转换
            transformation_result = await self._transform_batch_data(batch_id, import_result.get("request_id"))
            
            return {
                "status": "success" if transformation_result.get("success") else "transformation_failed",
                "scraping_result": scrape_result,
                "importing_result": import_result,
                "transformation_result": transformation_result,
                "batch_id": batch_id
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
            
            # 更新数据库状态
            request_id = await self._get_request_id_by_batch_id(batch_id)
            if request_id:
                await self._update_review_status_in_db(request_id, scrape_result, import_result)
            
            return {
                "status": "success" if import_result.get("status") == "success" else "importing_failed",
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
            logger.info(f"✅ 数据转换服务初始化成功")
            
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