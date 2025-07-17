import json
import os
import asyncio
import aiofiles
import math
from datetime import datetime
from apify_client import ApifyClient
from typing import Dict, Any, List, Optional
import logging

from core.database.connection import get_supabase_service_client
from core.repositories.amazon_product_repository import AmazonProductRepository
from core.repositories.amazon_review_repository import AmazonReviewRepository

logger = logging.getLogger(__name__)

# 获取scraping模块的data目录路径
SCRAPING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SCRAPING_DIR, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "scraped")
AMAZON_REVIEW_DIR = os.path.join(OUTPUT_DIR, "amazon", "review")

# 确保目录存在
os.makedirs(AMAZON_REVIEW_DIR, exist_ok=True)

# Apify API Configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
AXESSO_ACTOR_ID = "ZebkvH3nVOrafqr5T"

# Amazon Review Scraper Configuration (constant across all requests)
DEFAULT_REVIEWS_PER_PAGE = 10  # Default number of reviews per page when currentPage is missing

def _calculate_max_pages(max_reviews: int) -> int:
    """Calculate the maximum pages needed based on requested reviews"""
    return math.ceil(max_reviews / DEFAULT_REVIEWS_PER_PAGE)

AMAZON_REVIEW_CONFIG = {
    "domainCode": "com",           # Amazon.com (US marketplace)
    "sortBy": "recent",            # Sort by most recent reviews
    # maxPages will be set dynamically based on max_reviews
    "filterByStar": None,          # No star filter (all ratings)
    "filterByKeyword": None,       # No keyword filter
    "reviewerType": "verified_reviews",  # Only verified purchase reviews
    "formatType": "current_format",      # Use current Amazon review format
    "mediaType": "all_contents"          # Include all content types
}

# Configuration constants
RATE_LIMIT_DELAY = 0.1  # seconds - 100ms delay between individual requests
MAX_CONCURRENT_REQUESTS = 32  # Maximum concurrent API requests
SCRAPE_RECENCY_DAYS = 30  # Days to consider a scrape "recent"
DAYS_PER_MONTH = 30  # Approximation for months to days conversion
DEFAULT_COVERAGE_MONTHS = 36  # Default months of review coverage required

# Review date filtering constants
MIN_REVIEW_YEAR = 2010  # Earliest acceptable review year
MAX_REVIEW_YEAR = datetime.now().year  # Latest acceptable review year (current year)


class ReviewScraper:
    """评论爬取器 - 负责Amazon评论数据的爬取"""
    
    def __init__(self):
        self.review_dir = AMAZON_REVIEW_DIR
    
    async def scrape_for_batch(self, batch_id: int, review_coverage_months: int = DEFAULT_COVERAGE_MONTHS, force_scrape: bool = False, max_reviews: int = 30) -> Dict[str, Any]:
        """
        为特定批次的产品爬取评论数据
        
        Args:
            batch_id: 批次ID (对应scraping_requests.id)
            review_coverage_months: 评论覆盖月数
            force_scrape: 是否强制爬取，忽略现有文件
            max_reviews: 最大评论数量限制
            
        Returns:
            Dict[str, Any]: 爬取结果
        """
        logger.info(f"🚀 开始为批次 {batch_id} 爬取评论数据...")
        
        try:
            # 获取数据库客户端
            supabase_client = get_supabase_service_client()
            product_repository = AmazonProductRepository(supabase_client)
            
            # 从数据库获取该批次的产品列表
            logger.info(f"📊 从数据库获取批次 {batch_id} 的产品列表...")
            products = await product_repository.get_products_by_batch(batch_id)
            
            if not products:
                logger.warning(f"⚠️  批次 {batch_id} 中没有找到产品数据")
                return {
                    "status": "warning",
                    "message": f"批次 {batch_id} 中没有产品数据",
                    "batch_id": batch_id,
                    "total_asins": 0,
                    "successful": 0,
                    "skipped": 0,
                    "errors": 0,
                    "total_reviews_scraped": 0,
                    "products_processed": 0
                }
            
            # 提取ASIN列表
            asins = []
            for product in products:
                platform_id = product.get('platform_id')
                if platform_id:
                    asins.append(platform_id)
            
            logger.info(f"📦 找到 {len(asins)} 个ASIN需要爬取评论")
            
            if not asins:
                logger.warning(f"⚠️  批次 {batch_id} 中没有有效的ASIN")
                return {
                    "status": "warning", 
                    "message": f"批次 {batch_id} 中没有有效的ASIN",
                    "batch_id": batch_id,
                    "total_asins": 0,
                    "successful": 0,
                    "skipped": 0,
                    "errors": 0,
                    "total_reviews_scraped": 0,
                    "products_processed": 0
                }
            
            max_pages_per_asin = _calculate_max_pages(max_reviews)
            logger.info("\n📋 评论爬取配置:")
            logger.info(f"   • 批次ID: {batch_id}")
            logger.info(f"   • ASIN数量: {len(asins)}")
            logger.info(f"   • 评论覆盖月数: {review_coverage_months}")
            logger.info(f"   • 最大并发请求: {MAX_CONCURRENT_REQUESTS}")
            logger.info(f"   • 每个ASIN最大页数: {max_pages_per_asin}")
            logger.info(f"   • 数据保存目录: {AMAZON_REVIEW_DIR}")
            
            # 创建信号量进行并发控制
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
            
            # 为所有ASIN创建爬取任务
            tasks = [
                self._scrape_product_reviews(asin, semaphore, review_coverage_months, batch_id, force_scrape, max_reviews) 
                for asin in asins
            ]
            
            # 执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
            skipped = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "skipped")
            errors = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error")
            exceptions = sum(1 for r in results if not isinstance(r, dict))
            
            # 计算总的评论数量
            total_reviews_scraped = sum(
                r.get("reviews_count", 0) 
                for r in results 
                if isinstance(r, dict) and r.get("status") == "success"
            )
            
            logger.info(f"\n📊 批次 {batch_id} 评论爬取汇总:")
            logger.info(f"   ✅ 成功: {successful}")
            logger.info(f"   ⏩ 跳过: {skipped}")
            logger.info(f"   ❌ 错误: {errors}")
            logger.info(f"   🚫 异常: {exceptions}")
            logger.info(f"   📝 总评论数: {total_reviews_scraped}")
            logger.info(f"   📁 文件保存位置: {AMAZON_REVIEW_DIR}")
            
            # 生成批次汇总报告
            summary_data = {
                "batch_scrape_session": {
                    "timestamp": datetime.now().isoformat(),
                    "batch_id": batch_id,
                    "total_asins": len(asins),
                    "successful": successful,
                    "skipped": skipped,
                    "errors": errors,
                    "exceptions": exceptions,
                    "total_reviews_scraped": total_reviews_scraped,
                    "review_coverage_months": review_coverage_months,
                    "configuration": {
                        "rate_limit_delay": RATE_LIMIT_DELAY,
                        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
                        "scrape_recency_days": SCRAPE_RECENCY_DAYS,
                        "max_pages_per_asin": max_pages_per_asin,
                        "min_review_year": MIN_REVIEW_YEAR,
                        "max_review_year": MAX_REVIEW_YEAR
                    }
                },
                "asins_list": asins,
                "results": [r for r in results if isinstance(r, dict)]
            }
            
            # 保存批次汇总
            summary_file = os.path.join(
                AMAZON_REVIEW_DIR, 
                f"batch_{batch_id}_review_scrape_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            async with aiofiles.open(summary_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(summary_data, indent=2, ensure_ascii=False))
            
            logger.info(f"📄 批次汇总保存到: {summary_file}")
            
            # 判断整体状态
            if successful + skipped == len(asins):
                status = "success"
                message = f"批次 {batch_id} 评论爬取完成"
            elif successful > 0:
                status = "partial_success"
                message = f"批次 {batch_id} 评论爬取部分成功"
            else:
                status = "error"
                message = f"批次 {batch_id} 评论爬取失败"
            
            return {
                "status": status,
                "message": message,
                "batch_id": batch_id,
                "total_asins": len(asins),
                "successful": successful,
                "skipped": skipped,
                "errors": errors,
                "exceptions": exceptions,
                "total_reviews_scraped": total_reviews_scraped,
                "products_processed": successful,
                "summary_file": summary_file,
                "data_directory": AMAZON_REVIEW_DIR
            }
            
        except Exception as e:
            logger.error(f"批次 {batch_id} 评论爬取时出现异常: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"批次 {batch_id} 评论爬取异常: {str(e)}",
                "batch_id": batch_id,
                "total_asins": 0,
                "successful": 0,
                "skipped": 0,
                "errors": 0,
                "total_reviews_scraped": 0,
                "products_processed": 0
            }
    
    async def _scrape_product_reviews(self, asin: str, semaphore: asyncio.Semaphore, 
                                     review_coverage_months: int, batch_id: Optional[int] = None, force_scrape: bool = False, max_reviews: int = 30) -> Dict[str, Any]:
        """
        爬取单个产品的评论
        
        Args:
            asin: 产品ASIN
            semaphore: 并发控制信号量
            review_coverage_months: 评论覆盖月数
            batch_id: 批次ID（可选）
            force_scrape: 是否强制爬取，忽略现有文件
            max_reviews: 最大评论数量限制
            
        Returns:
            Dict[str, Any]: 爬取结果
        """
        async with semaphore:
            try:
                logger.info(f"🎯 开始处理ASIN: {asin}")
                
                # 检查是否需要跳过 (除非强制爬取)
                if not force_scrape:
                    skip_action = await self._determine_skip_action(asin, review_coverage_months, max_reviews)
                    
                    if skip_action["should_skip"]:
                        logger.info(f"⏩ 跳过ASIN {asin}: {skip_action['reason']}")
                        unique_analysis = skip_action.get("unique_analysis", {})
                        return {
                            "status": "skipped",
                            "asin": asin,
                            "reason": skip_action["reason"],
                            "unique_analysis": unique_analysis,
                            "message": f"ASIN {asin} 被跳过: {skip_action['reason']}"
                        }
                    
                    # Use intelligent recommendation for how many reviews to actually scrape
                    recommended_max_reviews = skip_action.get("recommended_max_reviews", max_reviews)
                    unique_analysis = skip_action.get("unique_analysis", {})
                    
                    logger.info(f"🎯 智能调整ASIN {asin}的爬取参数:")
                    logger.info(f"   - 原始请求: {max_reviews} 评论")
                    logger.info(f"   - 智能推荐: {recommended_max_reviews} 评论")
                    logger.info(f"   - 实际需要: {unique_analysis.get('unique_reviews_needed', 0)} 唯一评论")
                    
                    # Use the intelligent recommendation
                    actual_max_reviews = recommended_max_reviews
                else:
                    logger.info(f"🔥 强制爬取ASIN {asin} (忽略现有文件)")
                    actual_max_reviews = max_reviews

                # 爬取评论
                logger.info(f"🔍 爬取ASIN {asin} 的评论 (请求 {actual_max_reviews} 条)...")
                reviews_data = await asyncio.to_thread(self._get_amazon_reviews_apify, asin, actual_max_reviews)
                
                if not reviews_data.get("success"):
                    error_msg = reviews_data.get("error", "未知错误")
                    logger.error(f"❌ ASIN {asin} 爬取失败: {error_msg}")
                    return {
                        "status": "error",
                        "asin": asin,
                        "error": error_msg,
                        "message": f"ASIN {asin} 爬取失败: {error_msg}"
                    }
                
                # 生成文件名并保存
                filepath = await self._generate_filename(asin, batch_id)
                
                # 分析是否获取了最早的评论
                earliest_reviews_fetched = False
                if reviews_data.get("fetched_all_available_reviews"):
                    earliest_reviews_fetched = True
                
                # 保存评论数据
                max_pages_calculated = _calculate_max_pages(actual_max_reviews)
                await self._save_reviews_with_context(
                    asin, reviews_data, filepath, 
                    earliest_reviews_fetched=earliest_reviews_fetched,
                    max_pages_info={
                        "max_pages_requested": reviews_data.get("max_pages_requested", max_pages_calculated),
                        "max_pages_reached": reviews_data.get("max_pages_reached", 0)
                    },
                    max_reviews=actual_max_reviews
                )
                
                reviews_count = reviews_data.get("total_reviews", 0)
                logger.info(f"✅ ASIN {asin} 完成: {reviews_count} 条评论已保存到 {filepath}")
                
                # 添加延迟以避免请求过于频繁
                if RATE_LIMIT_DELAY > 0:
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                
                return {
                    "status": "success",
                    "asin": asin,
                    "reviews_count": reviews_count,
                    "filepath": filepath,
                    "message": f"ASIN {asin} 成功爬取 {reviews_count} 条评论"
                }
                
            except Exception as e:
                logger.error(f"🚫 ASIN {asin} 处理异常: {str(e)}")
                return {
                    "status": "error",
                    "asin": asin,
                    "error": str(e),
                    "message": f"ASIN {asin} 处理异常: {str(e)}"
                }
    
    async def _get_existing_review_files(self, asin: str) -> List[str]:
        """获取ASIN已有的评论文件"""
        existing_files = []
        for filename in os.listdir(AMAZON_REVIEW_DIR):
            # 检查旧命名约定
            if filename.startswith(f"{asin}_") and filename.endswith("_reviews.json"):
                existing_files.append(os.path.join(AMAZON_REVIEW_DIR, filename))
            # 检查新命名约定
            elif filename.startswith("batch_") and f"_{asin}_" in filename and filename.endswith("_reviews.json"):
                existing_files.append(os.path.join(AMAZON_REVIEW_DIR, filename))
        return existing_files
    
    def _get_amazon_reviews_apify(self, asin: str, max_reviews: int) -> Dict[str, Any]:
        """使用Apify API获取Amazon产品评论"""
        if not APIFY_API_TOKEN:
            raise ValueError("APIFY_API_TOKEN environment variable is required")
        
        # 初始化ApifyClient
        client = ApifyClient(APIFY_API_TOKEN)
        
        # 创建输入配置
        max_pages = _calculate_max_pages(max_reviews)
        config = AMAZON_REVIEW_CONFIG.copy()
        config["asin"] = asin
        config["maxPages"] = max_pages
        
        run_input = {"input": [config]}
        
        try:
            logger.info(f"   🔄 启动Apify actor for ASIN {asin}, max_pages={max_pages}...")
            run = client.actor(AXESSO_ACTOR_ID).call(run_input=run_input)
            
            # 从运行的数据集获取结果
            all_items = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                all_items.append(item)
            
            if not all_items:
                return {
                    "reviews": [],
                    "total_reviews": 0,
                    "max_pages_requested": max_pages,
                    "max_pages_reached": 0,
                    "fetched_all_available_reviews": True,
                    "success": True
                }
            
            # 提取评论并确定实际到达的页数
            all_reviews = []
            max_current_page = 0
            has_current_page_info = False
            
            for item in all_items:
                # 每个item应该有currentPage并且是一个评论
                if "currentPage" in item:
                    current_page = item.get("currentPage", 1)
                    max_current_page = max(max_current_page, current_page)
                    has_current_page_info = True
                
                # 如果item有评论字段，则该item本身就是一个评论
                if "reviewId" in item or "text" in item:
                    all_reviews.append(item)
            
            # 确定是否已获取所有可用页面
            if has_current_page_info:
                fetched_all_available_reviews = (max_current_page >= max_pages or 
                                               len(all_reviews) < max_pages * DEFAULT_REVIEWS_PER_PAGE)
            else:
                expected_reviews_for_max_pages = max_pages * DEFAULT_REVIEWS_PER_PAGE
                fetched_all_available_reviews = len(all_reviews) < expected_reviews_for_max_pages
                max_current_page = min(max_pages, max(1, len(all_reviews) // DEFAULT_REVIEWS_PER_PAGE))
            
            return {
                "reviews": all_reviews,
                "total_reviews": len(all_reviews),
                "max_pages_requested": max_pages,
                "max_pages_reached": max_current_page,
                "fetched_all_available_reviews": fetched_all_available_reviews,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"   ❌ Apify API error: {str(e)}")
            return {
                "reviews": [],
                "total_reviews": 0,
                "max_pages_requested": max_pages,
                "max_pages_reached": 0,
                "fetched_all_available_reviews": False,
                "success": False,
                "error": str(e)
            }
    
    def _parse_review_date(self, date_str: str) -> Optional[datetime]:
        """解析评论日期字符串"""
        if not date_str:
            return None
        
        # 从Axesso格式中提取日期部分: "Reviewed in [Country] on [Date]"
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
                return datetime.strptime(date_part, fmt)
            except ValueError:
                continue
        
        logger.warning(f"无法解析日期字符串: {date_str}")
        return None
    
    def _is_valid_review_date(self, review_date_str: str) -> bool:
        """验证评论日期是否有效"""
        parsed_date = self._parse_review_date(review_date_str)
        if not parsed_date:
            return False
        
        year = parsed_date.year
        return MIN_REVIEW_YEAR <= year <= MAX_REVIEW_YEAR
    
    async def _calculate_unique_reviews_needed(self, asin: str, target_unique_reviews: int = 200) -> Dict[str, Any]:
        """
        Calculate how many unique reviews we actually need for an ASIN
        
        Args:
            asin: Product ASIN
            target_unique_reviews: Target number of unique reviews needed
            
        Returns:
            Dict with unique counts and recommendations
        """
        try:
            # 1. Get unique reviews from database
            supabase_client = get_supabase_service_client()
            result = supabase_client.table('amazon_reviews')\
                .select('review_id')\
                .eq('asin', asin)\
                .execute()
            
            unique_reviews_in_db = len(set(r['review_id'] for r in result.data if r.get('review_id')))
            
            # 2. Get unique reviews from existing files
            existing_files = await self._get_existing_review_files(asin)
            unique_reviews_in_files = set()
            
            for filepath in existing_files:
                try:
                    async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        data = json.loads(content)
                    
                    reviews = data.get("reviews", [])
                    for review in reviews:
                        review_id = review.get("reviewId") or review.get("review_id")
                        if review_id:
                            unique_reviews_in_files.add(review_id)
                            
                except Exception as e:
                    logger.warning(f"Error reading review file {filepath}: {e}")
                    continue
            
            # 3. Calculate total unique reviews available
            # Combine DB and file review IDs (union to avoid double counting)
            db_review_ids = set()
            if result.data:
                db_review_ids = set(r['review_id'] for r in result.data if r.get('review_id'))
            
            total_unique_reviews = len(db_review_ids.union(unique_reviews_in_files))
            unique_reviews_needed = max(0, target_unique_reviews - total_unique_reviews)
            
            # 4. Estimate pages needed (with buffer for duplicates)
            # Since we might get some duplicates, request extra pages
            if unique_reviews_needed > 0:
                # Add 50% buffer for potential duplicates/overlaps
                estimated_reviews_needed = int(unique_reviews_needed * 1.5)
                estimated_pages_needed = _calculate_max_pages(estimated_reviews_needed)
            else:
                estimated_reviews_needed = 0
                estimated_pages_needed = 0
            
            logger.info(f"ASIN {asin} unique review analysis:")
            logger.info(f"  - Unique in DB: {unique_reviews_in_db}")
            logger.info(f"  - Unique in files: {len(unique_reviews_in_files)}")
            logger.info(f"  - Total unique available: {total_unique_reviews}")
            logger.info(f"  - Target: {target_unique_reviews}")
            logger.info(f"  - Unique needed: {unique_reviews_needed}")
            logger.info(f"  - Estimated scrape needed: {estimated_reviews_needed} reviews ({estimated_pages_needed} pages)")
            
            return {
                "unique_reviews_in_db": unique_reviews_in_db,
                "unique_reviews_in_files": len(unique_reviews_in_files),
                "total_unique_available": total_unique_reviews,
                "target_unique_reviews": target_unique_reviews,
                "unique_reviews_needed": unique_reviews_needed,
                "estimated_reviews_to_scrape": estimated_reviews_needed,
                "estimated_pages_needed": estimated_pages_needed,
                "should_skip": unique_reviews_needed == 0,
                "skip_reason": f"already_have_sufficient_unique_reviews ({total_unique_reviews}/{target_unique_reviews})" if unique_reviews_needed == 0 else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating unique reviews for {asin}: {e}")
            return {
                "unique_reviews_in_db": 0,
                "unique_reviews_in_files": 0,
                "total_unique_available": 0,
                "target_unique_reviews": target_unique_reviews,
                "unique_reviews_needed": target_unique_reviews,
                "estimated_reviews_to_scrape": target_unique_reviews,
                "estimated_pages_needed": _calculate_max_pages(target_unique_reviews),
                "should_skip": False,
                "skip_reason": None,
                "error": str(e)
            }

    async def _determine_skip_action(self, asin: str, review_coverage_months: int, max_reviews: int) -> Dict[str, Any]:
        """确定是否应该跳过ASIN的爬取，基于唯一评论数量分析"""
        
        # Use intelligent unique review calculation instead of simple file/DB checks
        unique_analysis = await self._calculate_unique_reviews_needed(asin, target_unique_reviews=max_reviews)
        
        if unique_analysis["should_skip"]:
            return {
                "should_skip": True,
                "reason": unique_analysis["skip_reason"],
                "unique_analysis": unique_analysis
            }
        
        # If we need reviews, adjust the max_reviews to what we actually need
        estimated_scrape_needed = unique_analysis["estimated_reviews_to_scrape"]
        
        return {
            "should_skip": False,
            "reason": f"need_{unique_analysis['unique_reviews_needed']}_more_unique_reviews",
            "unique_analysis": unique_analysis,
            "recommended_max_reviews": estimated_scrape_needed
        }
    
    async def _check_existing_review_files(self, asin: str, review_coverage_months: int, max_reviews: int) -> Dict[str, Any]:
        """检查本地评论文件"""
        existing_files = await self._get_existing_review_files(asin)
        
        if not existing_files:
            return {"should_skip": False, "reason": "no_existing_files"}
        
        # 分析现有评论文件 - 使用唯一评论计数
        unique_review_ids = set()
        max_previous_max_reviews = 0
        most_recent_scrape_date = None
        
        for filepath in existing_files:
            try:
                async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                
                # 获取唯一评论ID
                reviews = data.get("reviews", [])
                for review in reviews:
                    review_id = review.get("reviewId") or review.get("review_id")
                    if review_id:
                        unique_review_ids.add(review_id)
                
                # 获取之前请求的max_reviews
                scrape_context = data.get("scrape_context", {})
                previous_max_reviews = scrape_context.get("max_reviews_requested", 0)
                max_previous_max_reviews = max(max_previous_max_reviews, previous_max_reviews)
                
                # 获取爬取时间
                scrape_timestamp = scrape_context.get("scraped_at")
                if scrape_timestamp:
                    try:
                        scrape_date = datetime.fromisoformat(scrape_timestamp.replace('Z', '+00:00'))
                        if not most_recent_scrape_date or scrape_date > most_recent_scrape_date:
                            most_recent_scrape_date = scrape_date
                    except ValueError:
                        pass
                
            except Exception as e:
                logger.warning(f"读取文件时出错 {filepath}: {e}")
                continue
        
        unique_existing_reviews = len(unique_review_ids)
        
        # Smart force logic: if current max_reviews > unique existing reviews, we should scrape more
        if max_reviews > unique_existing_reviews:
            return {
                "should_skip": False, 
                "reason": f"need_more_unique_reviews (requesting {max_reviews}, have {unique_existing_reviews} unique, prev_max {max_previous_max_reviews})"
            }
        
        # 检查是否有最近的爬取（避免频繁重复爬取）
        if most_recent_scrape_date:
            days_since_scrape = (datetime.now() - most_recent_scrape_date).days
            if days_since_scrape <= SCRAPE_RECENCY_DAYS:
                return {
                    "should_skip": True,
                    "reason": f"sufficient_recent_unique_reviews ({unique_existing_reviews} unique reviews, max_req {max_reviews}, scraped {days_since_scrape}d ago)"
                }
        
        # 如果没有最近的爬取信息，检查覆盖要求
        all_reviews_analysis = await self._analyze_all_existing_reviews(existing_files, review_coverage_months)
        
        if all_reviews_analysis["meets_coverage_requirement"]:
            return {
                "should_skip": True,
                "reason": f"sufficient_coverage ({unique_existing_reviews} unique reviews, {all_reviews_analysis['latest_reviews_months']:.1f} months)"
            }
        else:
            return {
                "should_skip": False,
                "reason": f"insufficient_coverage ({all_reviews_analysis['latest_reviews_months']:.1f} months)"
            }
    
    async def _check_existing_reviews_in_db(self, asin: str, review_coverage_months: int, max_reviews: int) -> Dict[str, Any]:
        """检查数据库中的现有评论"""
        try:
            # 获取数据库客户端
            supabase_client = get_supabase_service_client()
            review_repository = AmazonReviewRepository(supabase_client)
            
            # 检查现有评论数量和之前的max_reviews设置（使用唯一计数）
            existing_reviews_info = await review_repository.get_asin_review_summary(asin)
            unique_existing_count = existing_reviews_info.get("unique_reviews", 0)
            total_existing_count = existing_reviews_info.get("total_reviews", 0)
            previous_max_reviews = existing_reviews_info.get("max_previous_max_reviews", 0)
            
            # Smart force logic: if requesting more unique reviews than we have
            if max_reviews > unique_existing_count:
                return {
                    "should_skip": False,
                    "reason": f"need_more_unique_reviews_db (requesting {max_reviews}, have {unique_existing_count} unique of {total_existing_count} total, prev_max {previous_max_reviews})"
                }
            
            # 使用新的repository方法检查最近的评论
            recent_check = await review_repository.check_recent_reviews_by_asin(
                asin=asin,
                min_reviews=max_reviews,
                coverage_months=review_coverage_months,
                hours_threshold=24  # 检查最近24小时内的导入
            )
            
            if recent_check.get("has_sufficient_reviews"):
                logger.info(f"数据库中找到足够的最近评论: ASIN {asin}, {recent_check.get('reason')}")
                return {
                    "should_skip": True,
                    "reason": f"recent_db_reviews ({recent_check.get('reason')})"
                }
            else:
                return {
                    "should_skip": False,
                    "reason": f"insufficient_recent_db_reviews ({recent_check.get('reason')})"
                }
                
        except Exception as e:
            logger.error(f"检查数据库评论时出错: {e}")
            return {"should_skip": False, "reason": f"error_checking_database: {e}"}
    
    async def _analyze_all_existing_reviews(self, filepaths: List[str], review_coverage_months: int) -> Dict[str, Any]:
        """分析所有现有评论文件"""
        all_reviews = []
        most_recent_scrape_date = None
        file_scrape_dates = []
        # Use default if review_coverage_months is None
        if review_coverage_months is None:
            review_coverage_months = DEFAULT_COVERAGE_MONTHS
        
        for filepath in filepaths:
            try:
                async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                
                # 获取文件的爬取日期
                scrape_timestamp = data.get("scrape_context", {}).get("scraped_at")
                if scrape_timestamp:
                    try:
                        scrape_date = datetime.fromisoformat(scrape_timestamp.replace('Z', '+00:00'))
                        file_scrape_dates.append(scrape_date)
                        if not most_recent_scrape_date or scrape_date > most_recent_scrape_date:
                            most_recent_scrape_date = scrape_date
                    except ValueError:
                        logger.warning(f"无法解析爬取时间戳: {scrape_timestamp}")
                
                # 收集评论
                reviews = data.get("reviews", [])
                if isinstance(reviews, list):
                    all_reviews.extend(reviews)
                
            except Exception as e:
                logger.warning(f"读取文件时出错 {filepath}: {e}")
                continue
        
        if not all_reviews:
            return {
                "meets_coverage_requirement": False,
                "recent_scrape_exists": False,
                "latest_reviews_months": 0,
                "total_reviews": 0,
                "file_count": len(filepaths)
            }
        
        # 解析并过滤评论日期
        valid_review_dates = []
        for review in all_reviews:
            date_str = review.get("date", "")
            if self._is_valid_review_date(date_str):
                parsed_date = self._parse_review_date(date_str)
                if parsed_date:
                    valid_review_dates.append(parsed_date)
        
        if not valid_review_dates:
            return {
                "meets_coverage_requirement": False,
                "recent_scrape_exists": False,
                "latest_reviews_months": 0,
                "total_reviews": len(all_reviews),
                "file_count": len(filepaths)
            }
        
        # 计算覆盖范围
        now = datetime.now()
        newest_review_date = max(valid_review_dates)
        oldest_review_date = min(valid_review_dates)
        
        # 计算最新评论的月数差
        days_difference = (now - newest_review_date).days
        latest_reviews_months = days_difference / DAYS_PER_MONTH
        
        # 检查是否满足覆盖要求
        meets_coverage_requirement = latest_reviews_months <= review_coverage_months
        
        # 检查是否有最近的爬取
        recent_scrape_exists = False
        if most_recent_scrape_date:
            days_since_scrape = (now - most_recent_scrape_date).days
            recent_scrape_exists = days_since_scrape <= SCRAPE_RECENCY_DAYS
        
        return {
            "meets_coverage_requirement": meets_coverage_requirement,
            "recent_scrape_exists": recent_scrape_exists,
            "latest_reviews_months": latest_reviews_months,
            "total_reviews": len(all_reviews),
            "valid_reviews": len(valid_review_dates),
            "newest_review_date": newest_review_date.isoformat(),
            "oldest_review_date": oldest_review_date.isoformat(),
            "file_count": len(filepaths),
            "most_recent_scrape": most_recent_scrape_date.isoformat() if most_recent_scrape_date else None
        }
    
    async def _generate_filename(self, asin: str, batch_id: Optional[int] = None) -> str:
        """生成评论文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if batch_id is not None:
            filename = f"batch_{batch_id}_{asin}_{timestamp}_reviews.json"
        else:
            filename = f"{asin}_{timestamp}_reviews.json"
        
        return os.path.join(AMAZON_REVIEW_DIR, filename)
    
    async def _save_reviews_with_context(self, asin: str, reviews_data: Dict[str, Any], 
                                       filepath: str, earliest_reviews_fetched: bool = False,
                                       max_pages_info: Optional[Dict[str, Any]] = None, max_reviews: int = 30) -> None:
        """保存评论数据"""
        # 构建完整的数据结构
        complete_data = {
            "asin": asin,
            "scrape_context": {
                "scraped_at": datetime.now().isoformat(),
                "scraper_version": "apify_axesso_v1",
                "total_reviews_fetched": reviews_data.get("total_reviews", 0),
                "earliest_reviews_fetched": earliest_reviews_fetched,
                "max_pages_info": max_pages_info or {},
                "max_reviews_requested": max_reviews, # 添加max_reviews_requested
                "configuration": {
                    "max_pages_per_asin": _calculate_max_pages(max_reviews),
                    "reviews_per_page_default": DEFAULT_REVIEWS_PER_PAGE,
                    "sort_by": AMAZON_REVIEW_CONFIG["sortBy"],
                    "reviewer_type": AMAZON_REVIEW_CONFIG["reviewerType"],
                    "format_type": AMAZON_REVIEW_CONFIG["formatType"],
                    "media_type": AMAZON_REVIEW_CONFIG["mediaType"]
                }
            },
            "reviews": reviews_data.get("reviews", []),
            "api_response_metadata": {
                "success": reviews_data.get("success", False),
                "max_pages_requested": reviews_data.get("max_pages_requested", _calculate_max_pages(max_reviews)),
                "max_pages_reached": reviews_data.get("max_pages_reached", 0),
                "fetched_all_available_reviews": reviews_data.get("fetched_all_available_reviews", False)
            }
        }
        
        # 如果有错误，也保存错误信息
        if "error" in reviews_data:
            complete_data["api_response_metadata"]["error"] = reviews_data["error"]
        
        # 保存到文件
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(complete_data, indent=2, ensure_ascii=False)) 