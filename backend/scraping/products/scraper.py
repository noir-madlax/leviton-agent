import json
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import logging

from ..common.amazon_api import (
    amazon_search, 
    get_bestsellers_rainforest, 
    get_products_from_category_rainforest,
    get_product_details_rainforest
)
from ..common.url_parser import parse_amazon_url

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
    
    async def scrape_from_url(self, url: str, max_products: int = 100) -> Dict[str, Any]:
        """
        从URL爬取商品数据
        
        Args:
            url: Amazon URL
            max_products: 最大商品数量
            
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
        """爬取类别商品"""
        if url_type == "product":
            logger.info(f"从产品页面爬取同类别商品: category_id={category_id}, type={url_type}")
        else:
            logger.info(f"爬取类别商品: category_id={category_id}, type={url_type}")
        
        all_products = []
        page = 1
        first_page_metadata = {}
        amazon_domain = "amazon.com"
        
        while len(all_products) < target_count:
            try:
                logger.info(f"  获取第 {page} 页...")
                
                page_data = await asyncio.to_thread(
                    get_products_from_category_rainforest,
                    category_id=category_id,
                    page=page,
                    amazon_domain=amazon_domain
                )
                
                # 保存第一页的元数据
                if page == 1:
                    first_page_metadata = {
                        "request_info": page_data.get("request_info", {}),
                        "request_parameters": page_data.get("request_parameters", {}),
                        "request_metadata": page_data.get("request_metadata", {}),
                        "search_information": page_data.get("search_information", {}),
                        "category_information": page_data.get("category_information", {}),
                        "pagination": page_data.get("pagination", {})
                    }
                
                if not page_data or 'category_results' not in page_data:
                    logger.info(f"  第 {page} 页没有返回数据，停止")
                    break
                
                page_products = page_data.get('category_results', [])
                if not page_products:
                    logger.info(f"  第 {page} 页没有找到商品，停止")
                    break
                
                logger.info(f"  找到 {len(page_products)} 个商品")
                all_products.extend(page_products)
                
                # 如果达到目标数量，截断结果
                if len(all_products) >= target_count:
                    all_products = all_products[:target_count]
                    logger.info(f"  达到目标数量 {target_count}，停止")
                    break
                
                page += 1
                time.sleep(1)  # 避免请求过于频繁
                
            except Exception as e:
                logger.error(f"  获取第 {page} 页时出错: {str(e)}")
                break
        
        logger.info(f"类别爬取完成: 共爬取 {len(all_products)} 个商品")
        
        # 保存结果
        filepath = await self._save_category_results(
            category_id, url_type, all_products, first_page_metadata, page - 1, target_count
        )
        
        return len(all_products), all_products, filepath
    
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