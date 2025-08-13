import json
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import logging

from ..common.amazon_api import (
    amazon_search, 
    get_bestsellers_rainforest, 
    get_products_from_category_rainforest,
    get_product_details_rainforest
)
from ..common.url_parser import parse_amazon_url

# Database imports for skip logic
from core.database.connection import get_supabase_service_client
from core.repositories.amazon_product_repository import AmazonProductRepository

logger = logging.getLogger(__name__)

# 获取scraping模块的data目录路径
SCRAPING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SCRAPING_DIR, "data")

class ProductScraper:
    """商品爬取器 - 负责Amazon商品数据的爬取"""
    
    def __init__(self):
        self.amazon_dir = os.path.join(DATA_DIR, "scraped", "amazon")
        self.home_depot_dir = os.path.join(DATA_DIR, "scraped", "home_depot")
        self._create_directories()
    
    def _create_directories(self):
        """创建必要的目录"""
        os.makedirs(self.amazon_dir, exist_ok=True)
        os.makedirs(self.home_depot_dir, exist_ok=True)
    
    async def scrape_from_url(self, url: str, max_products: int = 100, 
                             force_scrape: bool = False, 
                             force_import: bool = False, 
                             force_transformation: bool = False) -> Dict[str, Any]:
        """
        从URL爬取商品数据
        
        Args:
            url: Amazon URL
            max_products: 最大商品数量
            force_scrape: 是否强制爬取，忽略现有文件和数据库记录
            
        Returns:
            Dict[str, Any]: 爬取结果
        """
        logger.info(f"开始从URL爬取商品: {url}")
        
        try:
            # 1. 解析URL
            scraping_params = parse_amazon_url(url, max_products)
            logger.info(f"URL解析结果: {scraping_params}")
            
            # 2. 发现类别信息
            category_info = await self._discover_category_info(scraping_params)
            logger.info(f"类别发现结果: {category_info}")
            
            # 2.5. 检查是否需要跳过 (除非强制爬取)
            if not force_scrape:
                skip_action = await self._determine_product_skip_action(
                    category_info, max_products, scraping_params.get("url_type"), url
                )
                
                if skip_action["should_skip"]:
                    # 详细的跳过原因日志
                    skip_type = skip_action.get("skip_type", "unknown")
                    existing_count = skip_action.get("existing_products_count", 0)
                    
                    if skip_type == "local_file":
                        logger.info(f"🔄 智能跳过商品爬取 - 本地文件已存在: 发现 {existing_count} 个产品 (≥{max_products} 目标), 文件: {skip_action.get('existing_file_path', 'N/A')}")
                    elif skip_type == "database":
                        batch_id = skip_action.get("batch_id", "N/A")
                        logger.info(f"🔄 智能跳过商品爬取 - 数据库已有数据: 批次 {batch_id} 包含 {existing_count} 个产品 (≥{max_products} 目标), 时间: 24小时内")
                    else:
                        logger.info(f"🔄 智能跳过商品爬取: {skip_action['reason']}")
                    
                    logger.info(f"💡 节省API调用成本，如需强制重新爬取请使用 force_scrape=True")
                    
                    # Return skip result with additional info for potential force import/transformation
                    result = {
                        "status": "skipped",
                        "reason": skip_action["reason"],
                        "skip_type": skip_type,
                        "skip_details": {
                            "existing_products_count": existing_count,
                            "target_products": max_products,
                            "data_source": "Local File" if skip_type == "local_file" else "Database",
                            "file_path": skip_action.get("existing_file_path"),
                            "batch_id": skip_action.get("batch_id")
                        },
                        "products_scraped": existing_count,
                        "file_path": skip_action.get("existing_file_path"),
                        "existing_file_path": skip_action.get("existing_file_path"),  # Explicit field for force import
                        "category_info": category_info,
                        "products": skip_action.get("existing_products", []),
                        "batch_id": skip_action.get("batch_id"),  # For potential force transformation
                        "can_force_import": bool(skip_action.get("existing_file_path")),
                        "can_force_transformation": bool(skip_action.get("batch_id"))
                    }
                    
                    # If force_import or force_transformation is set, indicate success status for downstream processing
                    if force_import or force_transformation:
                        result["status"] = "success"
                        result["force_mode"] = True
                        logger.info(f"🔥 跳过爬取但启用强制模式: force_import={force_import}, force_transformation={force_transformation}")
                    
                    return result
            else:
                logger.info(f"🔥 强制爬取商品 (忽略现有文件和数据库记录)")
            
            # 3. 爬取商品
            product_count, scraped_products, filepath = await self._scrape_products(
                category_info=category_info,
                target_count=max_products,
                url_type=scraping_params.get("url_type"),
                original_url=url
            )
            
            # 4. 如果是产品页面，确保原产品在列表中
            if scraping_params.get("url_type") == "product":
                original_asin = scraping_params.get("asin")
                if original_asin:
                    product_count, scraped_products, filepath = await self._ensure_original_product(
                        original_asin, scraped_products, filepath
                    )
            
            return {
                "status": "success",
                "products_scraped": product_count,
                "file_path": filepath,
                "category_info": category_info,
                "products": scraped_products
            }
            
        except Exception as e:
            logger.error(f"从URL爬取商品失败: {e}")
            return {
                "status": "error",
                "message": str(e),
                "products_scraped": 0
            }

    async def scrape_by_asins(self, asins: List[str], concurrency: int = 8, max_retries: int = 3) -> Dict[str, Any]:
        """按 ASIN 列表抓取产品详情并保存为与导入器兼容的 JSON 文件。

        Returns:
            Dict[str, Any]: { status, file_path, products_scraped, products }
        """
        try:
            if not asins:
                return {"status": "error", "message": "ASIN list is empty", "products_scraped": 0}

            # 规范化并去重
            normalized = []
            seen = set()
            for a in asins:
                if not a:
                    continue
                token = str(a).strip().upper()
                if len(token) >= 8 and len(token) <= 12 and token not in seen:
                    seen.add(token)
                    normalized.append(token)

            if not normalized:
                return {"status": "error", "message": "No valid ASIN tokens found", "products_scraped": 0}

            # 并发抓详情
            sem = asyncio.Semaphore(max(1, concurrency))
            results: List[Dict[str, Any]] = []

            async def fetch_one(asin: str):
                retries = 0
                while retries <= max_retries:
                    try:
                        async with sem:
                            details = await asyncio.to_thread(get_product_details_rainforest, asin)
                        if details and "product" in details:
                            results.append(details["product"])
                            return
                        raise RuntimeError("empty response")
                    except Exception:
                        retries += 1
                        await asyncio.sleep(min(5, 1 + retries))

            await asyncio.gather(*(fetch_one(a) for a in normalized))

            # 落盘
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            import hashlib
            key = hashlib.sha1("_".join(normalized).encode()).hexdigest()[:12]
            filename = f"amazon_asins_{key}_{timestamp}.json"
            filepath = os.path.join(self.amazon_dir, filename)

            combined_data = {
                "scraping_summary": {
                    "type": "asin_list",
                    "total_products": len(results),
                    "requested_asins": len(normalized)
                },
                # Provide minimal metadata keys so category importer has a consistent structure
                "request_info": {},
                "request_parameters": {},
                "request_metadata": {},
                "category_information": {},
                # 与导入器兼容
                "category_results": results
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=4, ensure_ascii=False)

            return {
                "status": "success",
                "file_path": filepath,
                "products_scraped": len(results),
                "products": results
            }

        except Exception as e:
            logger.error(f"按ASIN列表爬取商品失败: {e}")
            return {"status": "error", "message": str(e), "products_scraped": 0}
    
    async def _discover_category_info(self, params: Dict) -> Dict:
        """
        动态发现类别信息
        
        Args:
            params: URL解析参数
            
        Returns:
            Dict: 类别信息
        """
        url_type = params.get("url_type")

        if url_type == "product":
            asin = params.get("asin")
            if not asin:
                raise ValueError("Could not extract ASIN from product URL.")

            logger.info(f"Fetching product details for ASIN: {asin}")
            product_details = await asyncio.to_thread(
                get_product_details_rainforest, asin
            )

            if not product_details or "product" not in product_details:
                raise ValueError(f"Failed to retrieve product details for ASIN {asin}.")

            product_data = product_details["product"]
            categories = product_data.get("categories")
            if not categories:
                raise ValueError(f"No 'categories' field found for ASIN {asin}.")

            # 取最后一个（最具体的）类别
            last_category = categories[-1] if categories else None
            if not last_category or "category_id" not in last_category:
                raise ValueError(f"No valid category found for ASIN {asin}.")

            category_id = last_category["category_id"]
            category_name = last_category.get("name", "Unknown Category")

            return {
                "category_id": category_id,
                "search_term": None,
                "method": f"discovered_from_product_{asin}",
                "category_name": category_name
            }

        elif url_type in ["search", "category", "bestsellers"]:
            # 直接使用解析出的参数
            return {
                "category_id": params.get("category_id"),
                "search_term": params.get("search_term"),
                "method": f"parsed_from_{url_type}_url",
                "category_name": "Unknown"
            }

        else:
            raise ValueError(f"Unsupported URL type: {url_type}")
    
    async def _scrape_products(self, category_info: Dict, target_count: int, 
                              url_type: str = None, original_url: str = None) -> Tuple[int, List[Dict], str]:
        """
        爬取商品数据
        
        Args:
            category_info: 类别信息
            target_count: 目标商品数量
            url_type: URL类型
            original_url: 原始URL
            
        Returns:
            Tuple[int, List[Dict], str]: (商品数量, 商品列表, 文件路径)
        """
        category_id = category_info["category_id"]
        search_term = category_info["search_term"]
        
        logger.info(f"开始爬取商品: category_id={category_id}, search_term={search_term}")
        
        if search_term:
            return await self._scrape_search_products(
                category_id, search_term, target_count, original_url
            )
        elif url_type in ['category', 'bestsellers', 'product']:
            return await self._scrape_category_products(
                category_id, target_count, url_type, original_url
            )
        else:
            raise ValueError("Neither search_term nor valid url_type provided")
    
    async def _scrape_search_products(self, category_id: str, search_term: str, 
                                    target_count: int, original_url: str = None) -> Tuple[int, List[Dict], str]:
        """爬取搜索结果商品"""
        logger.info(f"爬取搜索商品: '{search_term}' in category {category_id}")
        
        all_products = []
        page = 1
        first_page_metadata = {}
        
        while len(all_products) < target_count:
            try:
                logger.info(f"  获取搜索结果第 {page} 页...")
                
                result = await asyncio.to_thread(
                    amazon_search,
                    search_term=search_term,
                    amazon_domain="amazon.com",
                    category_id=category_id,
                    sort_by="featured",
                    page=page,
                    exclude_sponsored=True
                )
                
                # 保存第一页的元数据
                if page == 1:
                    first_page_metadata = {
                        "request_info": result.get("request_info", {}),
                        "request_parameters": result.get("request_parameters", {}),
                        "request_metadata": result.get("request_metadata", {}),
                        "search_information": result.get("search_information", {}),
                        "pagination": result.get("pagination", {})
                    }
                
                if 'search_results' in result and result['search_results']:
                    products = result['search_results']
                    all_products.extend(products)
                    logger.info(f"    找到 {len(products)} 个商品 (总计: {len(all_products)})")
                    
                    if len(products) < 10:
                        logger.info(f"    已到达 {search_term} 的搜索结果末尾")
                        break
                else:
                    logger.info(f"    第 {page} 页没有找到商品")
                    break
                
                page += 1
                time.sleep(1)  # 避免请求过于频繁
                
            except Exception as e:
                logger.error(f"    获取第 {page} 页时出错: {str(e)}")
                break
        
        logger.info(f"  搜索完成: 共爬取 {len(all_products)} 个商品")
        
        # 保存结果
        filepath = await self._save_search_results(
            search_term, category_id, all_products, first_page_metadata, page - 1, target_count
        )
        
        return len(all_products), all_products, filepath
    
    async def _scrape_category_products(self, category_id: str, target_count: int, 
                                       url_type: str, original_url: str = None) -> Tuple[int, List[Dict], str]:
        """爬取类别商品 - 使用混合API策略获取完整信息"""
        if url_type == "product":
            logger.info(f"从产品页面爬取同类别商品: category_id={category_id}, type={url_type}")
        else:
            logger.info(f"爬取类别商品: category_id={category_id}, type={url_type}")
        
        # Phase 1: 使用Category API获取产品ASIN列表
        all_basic_products = []
        page = 1
        first_page_metadata = {}
        amazon_domain = "amazon.com"
        
        logger.info(f"Phase 1: 获取产品ASIN列表...")
        
        while len(all_basic_products) < target_count:
            try:
                logger.info(f"  获取第 {page} 页...")
                
                if url_type == "product":
                    page_data = await asyncio.to_thread(
                        get_products_from_category_rainforest,
                        category_id=category_id,
                        page=page,
                        amazon_domain=amazon_domain
                    )
                else:
                    # For non-product URLs, use bestsellers API with URL
                    bestseller_url = f"https://www.amazon.com/Best-Sellers/zgbs/hi/{category_id}"
                    page_data = await asyncio.to_thread(
                        get_bestsellers_rainforest,
                        url=bestseller_url,
                        page=page
                    )
                
                # 保存第一页的元数据
                if page == 1:
                    first_page_metadata = {
                        "request_info": page_data.get("request_info", {}),
                        "request_parameters": page_data.get("request_parameters", {}),
                        "request_metadata": page_data.get("request_metadata", {}),
                        "search_information": page_data.get("search_information", {}),
                        "pagination": page_data.get("pagination", {})
                    }
                    
                    # Add appropriate category information based on URL type
                    if url_type == "product":
                        first_page_metadata["category_information"] = page_data.get("category_information", {})
                    else:
                        # For bestsellers, include the rich category hierarchy information
                        first_page_metadata["bestsellers_info"] = page_data.get("bestsellers_info", {})
                        # Also store current and parent category info at top level for consistency
                        bestsellers_info = page_data.get("bestsellers_info", {})
                        first_page_metadata["category_information"] = {
                            "title": bestsellers_info.get("title"),
                            "current_category": bestsellers_info.get("current_category"),
                            "parent_category": bestsellers_info.get("parent_category"),
                            "child_categories": bestsellers_info.get("child_categories", [])
                        }
                
                if not page_data:
                    logger.info(f"  第 {page} 页没有返回数据，停止")
                    break
                
                if url_type == "product":
                    if 'category_results' not in page_data:
                        logger.info(f"  第 {page} 页没有category_results数据，停止")
                        break
                    page_products = page_data.get('category_results', [])
                else:
                    if 'bestsellers' not in page_data:
                        logger.info(f"  第 {page} 页没有bestsellers数据，停止")
                        break
                    page_products = page_data.get('bestsellers', [])
                
                if not page_products:
                    logger.info(f"  第 {page} 页没有找到商品，停止")
                    break
                
                logger.info(f"  找到 {len(page_products)} 个商品")
                all_basic_products.extend(page_products)
                
                # 如果达到目标数量，截断结果
                if len(all_basic_products) >= target_count:
                    all_basic_products = all_basic_products[:target_count]
                    logger.info(f"  达到目标数量 {target_count}，停止")
                    break
                
                # For bestsellers, check if we should continue to next page
                if url_type != "product":
                    pagination = page_data.get('pagination', {})
                    current_page = pagination.get('current_page', 1)
                    total_pages = pagination.get('total_pages', 1)
                    
                    if current_page >= total_pages:
                        logger.info(f"  已到达最后一页 ({current_page}/{total_pages})，停止")
                        break
                
                page += 1
                time.sleep(1)  # 避免请求过于频繁
                
            except Exception as e:
                logger.error(f"  获取第 {page} 页时出错: {str(e)}")
                break
        
        logger.info(f"Phase 1 完成: 共获取 {len(all_basic_products)} 个基础产品信息")
        
        # Phase 2: 使用Product API获取每个产品的详细信息
        logger.info(f"Phase 2: 获取详细产品信息（包含品牌）...")
        enriched_products = []
        
        for i, basic_product in enumerate(all_basic_products):
            asin = basic_product.get('asin')
            if not asin:
                logger.warning(f"  产品 {i+1}/{len(all_basic_products)}: 缺少ASIN，跳过")
                continue
            
            try:
                logger.info(f"  获取产品详情 {i+1}/{len(all_basic_products)}: {asin}")
                
                # 获取详细产品信息，增加重试机制
                product_details = None
                max_retries = 3
                
                for retry_count in range(max_retries + 1):
                    try:
                        product_details = await asyncio.to_thread(
                            get_product_details_rainforest, asin, amazon_domain
                        )
                        if product_details:
                            break
                    except Exception as retry_error:
                        if retry_count < max_retries:
                            logger.warning(f"    重试 {retry_count + 1}/{max_retries}: {retry_error}")
                            await asyncio.sleep(2*(retry_count+1))  # 等待1秒后重试
                        else:
                            logger.error(f"    所有重试均失败: {retry_error}")
                            raise retry_error
                
                if product_details and 'product' in product_details:
                    detailed_product = product_details['product']
                    
                    # 合并基础信息和详细信息
                    # 详细信息优先，但保留一些基础信息中的有用字段
                    merged_product = {
                        **basic_product,  # 基础信息作为底层
                        **detailed_product,  # 详细信息覆盖
                        
                        # 确保关键字段不被覆盖（如果详细信息中没有）
                        'position': basic_product.get('position'),
                        'recent_sales': basic_product.get('recent_sales', detailed_product.get('recent_sales')),
                        
                        # 保留bestseller特有字段
                        'rank': basic_product.get('rank'),
                        'current_category': basic_product.get('current_category'),
                        'parent_category': basic_product.get('parent_category'),
                        
                        # 添加数据来源标记
                        '_data_enriched': True,
                        '_enrichment_timestamp': datetime.now().isoformat(),
                        '_category_api_data': basic_product,
                        '_data_source': 'bestsellers' if url_type != 'product' else 'category',
                    }
                    
                    enriched_products.append(merged_product)
                    
                    # 日志显示获取到的品牌信息
                    brand = detailed_product.get('brand', 'N/A')
                    logger.info(f"    ✅ 品牌: {brand}")
                    
                else:
                    error_msg = "API returned empty response" if product_details else "API call failed"
                    logger.warning(f"    ❌ 无法获取详细信息，使用基础信息 - {error_msg}")
                    # 即使没有详细信息，也保留基础信息
                    basic_product['_data_enriched'] = False
                    basic_product['_enrichment_error'] = error_msg
                    basic_product['_data_source'] = 'bestsellers' if url_type != 'product' else 'category'
                    enriched_products.append(basic_product)
                
                # 控制请求频率，避免API速率限制
                if i < len(all_basic_products) - 1:  # 不是最后一个
                    await asyncio.sleep(1.0)  # 增加到1秒间隔，减少API压力
                    
            except Exception as e:
                error_details = str(e)
                if "timeout" in error_details.lower():
                    logger.error(f"    ❌ API超时: {error_details}")
                elif "rate" in error_details.lower() or "limit" in error_details.lower():
                    logger.error(f"    ❌ API速率限制: {error_details}")
                else:
                    logger.error(f"    ❌ 获取产品详情失败: {error_details}")
                
                # 发生错误时仍保留基础信息
                basic_product['_data_enriched'] = False
                basic_product['_enrichment_error'] = error_details
                basic_product['_data_source'] = 'bestsellers' if url_type != 'product' else 'category'
                enriched_products.append(basic_product)
        
        logger.info(f"类别爬取完成: 共处理 {len(enriched_products)} 个商品")
        
        # 统计enrichment结果
        enriched_count = sum(1 for p in enriched_products if p.get('_data_enriched', False))
        brand_count = sum(1 for p in enriched_products if p.get('brand'))
        
        logger.info(f"数据充实统计: {enriched_count}/{len(enriched_products)} 获得详细信息, {brand_count} 个产品有品牌信息")
        
        # 保存结果
        filepath = await self._save_category_results(
            category_id, url_type, enriched_products, first_page_metadata, page - 1, target_count
        )
        
        return len(enriched_products), enriched_products, filepath
    
    async def _ensure_original_product(self, original_asin: str, scraped_products: List[Dict], 
                                     filepath: str) -> Tuple[int, List[Dict], str]:
        """确保原始产品在列表中"""
        # 检查原始ASIN是否在列表中
        is_present = any(
            product.get("asin", "").lower() == original_asin.lower()
            for product in scraped_products
        )
        
        if not is_present:
            logger.info(f"原始ASIN {original_asin} 不在最佳销量中，直接获取详情")
            
            original_product_details = await asyncio.to_thread(
                get_product_details_rainforest, original_asin
            )
            
            if original_product_details and "product" in original_product_details:
                scraped_products.insert(0, original_product_details["product"])
                
                # 更新文件
                await self._update_saved_file(filepath, scraped_products)
                
                logger.info(f"已添加原始ASIN {original_asin} 到列表: {filepath}")
        
        return len(scraped_products), scraped_products, filepath
    
    async def _determine_product_skip_action(self, category_info: Dict, max_products: int, 
                                           url_type: str, original_url: str) -> Dict[str, Any]:
        """
        确定是否应该跳过商品爬取，基于本地文件和数据库检查
        
        Args:
            category_info: 类别信息
            max_products: 目标商品数量
            url_type: URL类型
            original_url: 原始URL
            
        Returns:
            Dict[str, Any]: 跳过决策结果
        """
        try:
            # 1. 检查本地文件
            local_skip_action = await self._check_existing_product_files(
                category_info, max_products, url_type, original_url
            )
            
            if local_skip_action["should_skip"]:
                return local_skip_action
            
            # 2. 检查数据库
            db_skip_action = await self._check_existing_products_in_db(
                category_info, max_products, url_type, original_url
            )
            
            if db_skip_action["should_skip"]:
                return db_skip_action
            
            # 3. 不跳过
            return {"should_skip": False, "reason": "no_existing_data"}
            
        except Exception as e:
            logger.error(f"检查产品跳过条件时出错: {e}")
            return {"should_skip": False, "reason": f"error_checking_skip_conditions: {e}"}
    
    async def _check_existing_product_files(self, category_info: Dict, max_products: int,
                                          url_type: str, original_url: str) -> Dict[str, Any]:
        """检查本地产品文件"""
        try:
            category_id = category_info.get("category_id")
            search_term = category_info.get("search_term")
            
            # 构建可能的文件名模式
            patterns = []
            if search_term:
                search_term_clean = search_term.replace(" ", "_").lower()
                patterns.append(f"amazon_search_{search_term_clean}_cat_{category_id}_all_products_*.json")
            elif url_type in ['category', 'bestsellers', 'product']:
                patterns.append(f"amazon_{url_type}_cat_{category_id}_*.json")
            
            # 检查文件是否存在
            amazon_dir_path = Path(self.amazon_dir)
            for pattern in patterns:
                for file_path in amazon_dir_path.glob(pattern):
                    if file_path.is_file():
                        # 检查文件中的产品数量
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            existing_products = []
                            if 'search_results' in data:
                                existing_products = data['search_results']
                            elif 'category_results' in data:
                                existing_products = data['category_results']
                            
                            # Count unique products by ASIN/platform_id
                            unique_asins = set()
                            for product in existing_products:
                                asin = product.get('asin') or product.get('platform_id')
                                if asin:
                                    unique_asins.add(asin)
                            
                            unique_count = len(unique_asins)
                            if unique_count >= max_products:
                                logger.info(f"找到现有产品文件: {file_path.name}, {len(existing_products)} 个产品 ({unique_count} 个唯一)")
                                return {
                                    "should_skip": True,
                                    "skip_type": "local_file",
                                    "reason": f"sufficient_local_unique_products ({unique_count} unique >= {max_products})",
                                    "existing_products_count": unique_count,
                                    "existing_file_path": str(file_path),
                                    "existing_products": existing_products
                                }
                                
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"无法读取产品文件 {file_path}: {e}")
                            continue
            
            return {"should_skip": False, "reason": "no_sufficient_local_files"}
            
        except Exception as e:
            logger.error(f"检查本地产品文件时出错: {e}")
            return {"should_skip": False, "reason": f"error_checking_local_files: {e}"}
    
    async def _check_existing_products_in_db(self, category_info: Dict, max_products: int,
                                           url_type: str, original_url: str) -> Dict[str, Any]:
        """检查数据库中的现有产品"""
        try:
            # 获取数据库客户端
            supabase_client = get_supabase_service_client()
            product_repository = AmazonProductRepository(supabase_client)
            
            # 检查最近24小时内是否有足够的产品批次
            recent_check = await product_repository.check_recent_products_by_criteria(
                category_metadata=category_info,
                min_products=max_products,
                hours_threshold=24
            )
            
            if recent_check.get("has_recent_products"):
                logger.info(f"数据库中找到最近的符合条件的产品批次: {recent_check.get('reason')}")
                
                # Try to find corresponding file for force import support
                existing_file_path = await self._find_file_for_batch(
                    category_info, recent_check.get("batch_id"), url_type
                )
                
                return {
                    "should_skip": True,
                    "skip_type": "database",
                    "reason": f"recent_db_batch ({recent_check.get('reason')})",
                    "existing_products_count": recent_check.get("product_count", 0),
                    "batch_id": recent_check.get("batch_id"),
                    "existing_file_path": existing_file_path  # Add file path for force import
                }
            else:
                return {
                    "should_skip": False,
                    "reason": f"no_recent_db_products ({recent_check.get('reason')})"
                }
            
        except Exception as e:
            logger.error(f"检查数据库产品时出错: {e}")
            return {"should_skip": False, "reason": f"error_checking_database: {e}"}
    
    async def _find_file_for_batch(self, category_info: Dict, batch_id: int, url_type: str) -> Optional[str]:
        """Find existing file path for a given batch/category for force import support"""
        try:
            category_id = category_info.get("category_id")
            search_term = category_info.get("search_term")
            
            # Build possible file name patterns based on category info
            patterns = []
            if search_term:
                search_term_clean = search_term.replace(" ", "_").lower()
                patterns.extend([
                    f"amazon_search_{search_term_clean}_cat_{category_id}_*.json",
                    f"amazon_search_{search_term_clean}_*.json"
                ])
            
            # Add category/bestseller patterns
            if category_id:
                patterns.extend([
                    f"amazon_bestsellers_cat_{category_id}_*.json",
                    f"amazon_category_cat_{category_id}_*.json",
                    f"amazon_product_cat_{category_id}_*.json"
                ])
            
            # Search for matching files
            amazon_dir_path = Path(self.amazon_dir)
            for pattern in patterns:
                matching_files = list(amazon_dir_path.glob(pattern))
                if matching_files:
                    # Return the most recent file
                    most_recent = max(matching_files, key=lambda p: p.stat().st_mtime)
                    logger.info(f"为批次 {batch_id} 找到文件: {most_recent.name}")
                    return str(most_recent)
            
            logger.warning(f"未找到批次 {batch_id} 对应的文件")
            return None
            
        except Exception as e:
            logger.error(f"查找批次文件时出错: {e}")
            return None
    
    async def _save_search_results(self, search_term: str, category_id: str, products: List[Dict],
                                  metadata: Dict, pages_scraped: int, target_count: int) -> str:
        """保存搜索结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        search_term_clean = search_term.replace(" ", "_").lower()
        filename = f"amazon_search_{search_term_clean}_cat_{category_id}_all_products_{timestamp}.json"
        filepath = os.path.join(self.amazon_dir, filename)
        
        combined_data = {
            "request_info": metadata.get("request_info", {}),
            "request_parameters": metadata.get("request_parameters", {}),
            "request_metadata": metadata.get("request_metadata", {}),
            "search_information": metadata.get("search_information", {}),
            "pagination": metadata.get("pagination", {}),
            "scraping_summary": {
                "type": "search",
                "search_term": search_term,
                "category_id": category_id,
                "amazon_domain": "amazon.com",
                "total_pages_scraped": pages_scraped,
                "total_products": len(products),
                "max_products_requested": target_count,
                "sort_by": "featured",
                "exclude_sponsored": True
            },
            "search_results": products
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=4, ensure_ascii=False)
        
        return filepath
    
    async def _save_category_results(self, category_id: str, url_type: str, products: List[Dict],
                                   metadata: Dict, pages_scraped: int, target_count: int) -> str:
        """保存类别结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amazon_{url_type}_cat_{category_id}_{timestamp}.json"
        filepath = os.path.join(self.amazon_dir, filename)
        
        combined_data = {
            "request_info": metadata.get("request_info", {}),
            "request_parameters": metadata.get("request_parameters", {}),
            "request_metadata": metadata.get("request_metadata", {}),
            "search_information": metadata.get("search_information", {}),
            "category_information": metadata.get("category_information", {}),
            "pagination": metadata.get("pagination", {}),
            "scraping_summary": {
                "type": url_type,
                "category_id": category_id,
                "amazon_domain": "amazon.com",
                "total_pages_scraped": pages_scraped,
                "total_products": len(products),
                "max_products_requested": target_count
            },
            "category_results": products
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=4, ensure_ascii=False)
        
        return filepath
    
    async def _update_saved_file(self, filepath: str, products: List[Dict]):
        """更新已保存的文件"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            
            # 检查文件结构并更新
            if isinstance(existing_data, dict):
                if "search_results" in existing_data:
                    existing_data["search_results"] = products
                    existing_data["scraping_summary"]["total_products"] = len(products)
                elif "category_results" in existing_data:
                    existing_data["category_results"] = products
                    existing_data["scraping_summary"]["total_products"] = len(products)
                else:
                    existing_data = products
            else:
                existing_data = products
            
            # 重新写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"无法读取existing file structure, 使用简单数组: {e}")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=4, ensure_ascii=False) 