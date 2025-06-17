import json
import os
import asyncio
import aiofiles
import pandas as pd
from datetime import datetime, timedelta
from apify_client import ApifyClient
from typing import Dict, Any, List, Optional
import logging

from core.database.connection import get_supabase_service_client
from core.repositories.amazon_product_repository import AmazonProductRepository

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
MAX_PAGES_PER_ASIN = 5  # Maximum pages to scrape per ASIN in single API call
DEFAULT_REVIEWS_PER_PAGE = 10  # Default number of reviews per page when currentPage is missing

AMAZON_REVIEW_CONFIG = {
    "domainCode": "com",           # Amazon.com (US marketplace)
    "sortBy": "recent",            # Sort by most recent reviews
    "maxPages": MAX_PAGES_PER_ASIN,  # Maximum pages per request
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
DEFAULT_COVERAGE_MONTHS = 6  # Default months of review coverage required

# Review date filtering constants
MIN_REVIEW_YEAR = 2010  # Earliest acceptable review year
MAX_REVIEW_YEAR = datetime.now().year  # Latest acceptable review year (current year)


class ReviewScraper:
    """评论爬取器 - 负责Amazon评论数据的爬取"""
    
    def __init__(self):
        self.review_dir = AMAZON_REVIEW_DIR
    
    async def scrape_for_batch(self, batch_id: int, review_coverage_months: int = DEFAULT_COVERAGE_MONTHS) -> Dict[str, Any]:
        """
        为特定批次的产品爬取评论数据
        
        Args:
            batch_id: 批次ID (对应scraping_requests.id)
            review_coverage_months: 评论覆盖月数
            
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
                    "errors": 0
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
                    "errors": 0
                }
            
            logger.info(f"\n📋 评论爬取配置:")
            logger.info(f"   • 批次ID: {batch_id}")
            logger.info(f"   • ASIN数量: {len(asins)}")
            logger.info(f"   • 评论覆盖月数: {review_coverage_months}")
            logger.info(f"   • 最大并发请求: {MAX_CONCURRENT_REQUESTS}")
            logger.info(f"   • 每个ASIN最大页数: {MAX_PAGES_PER_ASIN}")
            logger.info(f"   • 数据保存目录: {AMAZON_REVIEW_DIR}")
            
            # 创建信号量进行并发控制
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
            
            # 为所有ASIN创建爬取任务
            tasks = [
                self._scrape_product_reviews(asin, semaphore, review_coverage_months, batch_id) 
                for asin in asins
            ]
            
            # 执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
            skipped = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "skipped")
            errors = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error")
            exceptions = sum(1 for r in results if not isinstance(r, dict))
            
            logger.info(f"\n📊 批次 {batch_id} 评论爬取汇总:")
            logger.info(f"   ✅ 成功: {successful}")
            logger.info(f"   ⏩ 跳过: {skipped}")
            logger.info(f"   ❌ 错误: {errors}")
            logger.info(f"   🚫 异常: {exceptions}")
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
                    "review_coverage_months": review_coverage_months,
                    "configuration": {
                        "rate_limit_delay": RATE_LIMIT_DELAY,
                        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
                        "scrape_recency_days": SCRAPE_RECENCY_DAYS,
                        "max_pages_per_asin": MAX_PAGES_PER_ASIN,
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
                "errors": 0
            }
    
    async def _scrape_product_reviews(self, asin: str, semaphore: asyncio.Semaphore, 
                                     review_coverage_months: int, batch_id: Optional[int] = None) -> Dict[str, Any]:
        """
        爬取单个产品的评论
        
        Args:
            asin: 产品ASIN
            semaphore: 并发控制信号量
            review_coverage_months: 评论覆盖月数
            batch_id: 批次ID（可选）
            
        Returns:
            Dict[str, Any]: 爬取结果
        """
        async with semaphore:
            try:
                logger.info(f"🎯 开始处理ASIN: {asin}")
                
                # 检查是否需要跳过
                skip_action = await self._determine_skip_action(asin, review_coverage_months)
                
                if skip_action["should_skip"]:
                    logger.info(f"⏩ 跳过ASIN {asin}: {skip_action['reason']}")
                    return {
                        "status": "skipped",
                        "asin": asin,
                        "reason": skip_action["reason"],
                        "message": f"ASIN {asin} 被跳过: {skip_action['reason']}"
                    }
                
                # 爬取评论
                logger.info(f"🔍 爬取ASIN {asin} 的评论...")
                reviews_data = await asyncio.to_thread(self._get_amazon_reviews_apify, asin)
                
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
                await self._save_reviews_with_context(
                    asin, reviews_data, filepath, 
                    earliest_reviews_fetched=earliest_reviews_fetched,
                    max_pages_info={
                        "max_pages_requested": reviews_data.get("max_pages_requested", MAX_PAGES_PER_ASIN),
                        "max_pages_reached": reviews_data.get("max_pages_reached", 0)
                    }
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
    
    def _get_amazon_reviews_apify(self, asin: str) -> Dict[str, Any]:
        """使用Apify API获取Amazon产品评论"""
        if not APIFY_API_TOKEN:
            raise ValueError("APIFY_API_TOKEN environment variable is required")
        
        # 初始化ApifyClient
        client = ApifyClient(APIFY_API_TOKEN)
        
        # 创建输入配置
        config = AMAZON_REVIEW_CONFIG.copy()
        config["asin"] = asin
        
        run_input = {"input": [config]}
        
        try:
            logger.info(f"   🔄 启动Apify actor for ASIN {asin}, max_pages={MAX_PAGES_PER_ASIN}...")
            run = client.actor(AXESSO_ACTOR_ID).call(run_input=run_input)
            
            # 从运行的数据集获取结果
            all_items = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                all_items.append(item)
            
            if not all_items:
                return {
                    "reviews": [],
                    "total_reviews": 0,
                    "max_pages_requested": MAX_PAGES_PER_ASIN,
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
                fetched_all_available_reviews = (max_current_page >= MAX_PAGES_PER_ASIN or 
                                               len(all_reviews) < MAX_PAGES_PER_ASIN * DEFAULT_REVIEWS_PER_PAGE)
            else:
                expected_reviews_for_max_pages = MAX_PAGES_PER_ASIN * DEFAULT_REVIEWS_PER_PAGE
                fetched_all_available_reviews = len(all_reviews) < expected_reviews_for_max_pages
                max_current_page = min(MAX_PAGES_PER_ASIN, max(1, len(all_reviews) // DEFAULT_REVIEWS_PER_PAGE))
            
            return {
                "reviews": all_reviews,
                "total_reviews": len(all_reviews),
                "max_pages_requested": MAX_PAGES_PER_ASIN,
                "max_pages_reached": max_current_page,
                "fetched_all_available_reviews": fetched_all_available_reviews,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"   ❌ Apify API error: {str(e)}")
            return {
                "reviews": [],
                "total_reviews": 0,
                "max_pages_requested": MAX_PAGES_PER_ASIN,
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
    
    async def _determine_skip_action(self, asin: str, review_coverage_months: int) -> Dict[str, Any]:
        """确定是否应该跳过ASIN的爬取"""
        existing_files = await self._get_existing_review_files(asin)
        
        if not existing_files:
            return {"should_skip": False, "reason": "no_existing_files"}
        
        # 分析现有评论
        all_reviews_analysis = await self._analyze_all_existing_reviews(existing_files, review_coverage_months)
        
        if all_reviews_analysis["meets_coverage_requirement"]:
            if all_reviews_analysis["recent_scrape_exists"]:
                return {
                    "should_skip": True, 
                    "reason": f"recent_sufficient_coverage ({all_reviews_analysis['latest_reviews_months']:.1f} months, {all_reviews_analysis['total_reviews']} reviews)"
                }
            else:
                return {"should_skip": False, "reason": "coverage_sufficient_but_old_scrape"}
        else:
            return {"should_skip": False, "reason": f"insufficient_coverage ({all_reviews_analysis['latest_reviews_months']:.1f} months)"}
    
    async def _analyze_all_existing_reviews(self, filepaths: List[str], review_coverage_months: int) -> Dict[str, Any]:
        """分析所有现有评论文件"""
        all_reviews = []
        most_recent_scrape_date = None
        file_scrape_dates = []
        
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
                                       max_pages_info: Optional[Dict[str, Any]] = None) -> None:
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
                "configuration": {
                    "max_pages_per_asin": MAX_PAGES_PER_ASIN,
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
                "max_pages_requested": reviews_data.get("max_pages_requested", MAX_PAGES_PER_ASIN),
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