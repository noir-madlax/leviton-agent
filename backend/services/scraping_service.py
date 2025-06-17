"""
Scraping Service Module

This module handles all scraping operations for Amazon products and reviews.
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os
import json

from scraping.url_parser import parse_amazon_url
from scraping.scrape_best_sellers import (
    scrape_products_from_amazon,
    create_directories,
)
from scraping.amazon_api import get_product_details_rainforest, get_bestsellers_rainforest
from app.services.data_import_service import DataImportService

logger = logging.getLogger(__name__)


class ScrapingService:
    """Service class for handling scraping operations"""
    
    def __init__(self):
        self.amazon_dir, self.home_depot_dir = create_directories()
        self.data_import_service = DataImportService()
    
    async def process_url(self, url: str, max_products: int = 100, max_reviews: int = 50) -> Dict[str, Any]:
        """
        Process Amazon URL, dynamically discover category info, and execute scraping.
        """
        if not url:
            raise ValueError("URL parameter cannot be empty")
        
        task_id = str(uuid.uuid4())
        logger.info(f"Starting scraping task {task_id}: URL={url}, max_products={max_products}")
        
        # 1. Parse URL to get initial parameters
        scraping_params = parse_amazon_url(url, max_products, max_reviews)
        logger.info(f"URL parsed successfully: {scraping_params}")
        
        try:
            # 2. Dynamically discover the definitive category_id and search_term
            logger.info("Discovering category information via API...")
            category_info = await self._discover_category_info(scraping_params)
            logger.info(f"Category discovered: {category_info}")
            
            # 3. Scrape products using the discovered category info
            product_count, scraped_products, filepath = scrape_products_from_amazon(
                category_id=category_info["category_id"],
                search_term=category_info["search_term"],
                target_count=max_products,
                save_dir=self.amazon_dir,
                url_type=scraping_params.get("url_type"),
                original_url=url
            )

            # 4. If the original URL was a product, ensure its ASIN is in the list.
            if scraping_params.get("url_type") == "product":
                original_asin = scraping_params.get("asin")
                if original_asin:
                    is_present = any(
                        product.get("asin", "").lower() == original_asin.lower()
                        for product in scraped_products
                    )
                    if not is_present:
                        logger.info(
                            f"Original ASIN {original_asin} not in bestsellers. Fetching it directly."
                        )
                        original_product_details = await asyncio.to_thread(
                            get_product_details_rainforest, original_asin
                        )
                        if (
                            original_product_details
                            and "product" in original_product_details
                        ):
                            scraped_products.insert(0, original_product_details["product"])
                            product_count += 1
                            
                            # Read the existing file to preserve its structure
                            try:
                                with open(filepath, "r", encoding="utf-8") as f:
                                    existing_data = json.load(f)
                                
                                # Check if it's a structured file with metadata or just a product array
                                if isinstance(existing_data, dict):
                                    # Structured file - update the products while preserving metadata
                                    if "search_results" in existing_data:
                                        existing_data["search_results"] = scraped_products
                                        existing_data["scraping_summary"]["total_products"] = len(scraped_products)
                                    elif "category_results" in existing_data:
                                        existing_data["category_results"] = scraped_products
                                        existing_data["scraping_summary"]["total_products"] = len(scraped_products)
                                    else:
                                        # Fallback - just replace with products array
                                        existing_data = scraped_products
                                else:
                                    # Simple array file - replace with updated array
                                    existing_data = scraped_products
                                
                                # Write back the updated data
                                with open(filepath, "w", encoding="utf-8") as f:
                                    json.dump(existing_data, f, indent=4, ensure_ascii=False)
                                    
                            except (json.JSONDecodeError, FileNotFoundError) as e:
                                logger.warning(f"Could not read existing file structure, falling back to simple array: {e}")
                                # Fallback to original behavior
                                with open(filepath, "w") as f:
                                    json.dump(scraped_products, f, indent=4)
                            
                            logger.info(f"Added original ASIN {original_asin} to the list: {filepath}")

            logger.info(
                f"Scraping task {task_id} completed. Products scraped: {product_count}"
            )
            
            # 新增：导入数据到数据库
            logger.info("开始导入数据到数据库...")
            import_result = await self.data_import_service.import_scraping_result(
                filepath, 
                {
                    "task_id": task_id,
                    "original_url": url,
                    "max_products": max_products,
                    "max_reviews": max_reviews
                }
            )
            
            # 从数据库获取实际的评论爬取数量
            try:
                from app.repositories.scraping_request_repository import ScrapingRequestRepository
                from app.database.connection import get_supabase_client
                
                # 获取数据库中的最新状态
                supabase_client = get_supabase_client()
                request_repo = ScrapingRequestRepository(supabase_client)
                request_data = await request_repo.get_request_by_id(import_result.get("request_id"))
                
                reviews_scraped = 0
                if request_data:
                    reviews_scraped = request_data.get("reviews_scraped", 0)
                    logger.info(f"从数据库获取评论数量: {reviews_scraped}")
                else:
                    logger.warning("无法从数据库获取请求数据")
                    
            except Exception as e:
                logger.error(f"获取评论数量时出错: {e}")
                reviews_scraped = 0
            
            return {
                "task_id": task_id,
                "status": "completed",
                "message": f"Product data scraping finished. Found {product_count} products.",
                "results": {
                    "products_scraped": product_count,
                    "reviews_scraped": reviews_scraped,  # 从数据库获取实际数量
                    "data_saved_to": self.amazon_dir,
                    "discovered_category_id": category_info["category_id"],
                    "used_search_term": category_info["search_term"],
                    "discovery_method": category_info["method"]
                },
                "database_import": import_result  # 新增：数据库导入结果
            }
            
        except Exception as e:
            logger.error(f"Scraping task {task_id} failed: {e}", exc_info=True)
            raise

    async def _discover_category_info(self, params: Dict) -> Dict:
        """
        Dynamically discovers the category_id and search_term using the correct
        Rainforest API endpoint based on the URL type.
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

            # API response received successfully

            if not product_details or "product" not in product_details:
                raise ValueError(f"Failed to retrieve product details for ASIN {asin}.")

            product_data = product_details["product"]
            categories = product_data.get("categories")
            if not categories:
                raise ValueError(f"No 'categories' field found for ASIN {asin}.")

            # Find the first valid category with an ID from the list
            category_id = None
            search_term = None
            for category in reversed(categories):
                if isinstance(category, dict) and category.get("category_id"):
                    category_id = category["category_id"]
                    search_term = category.get("name")
                    break
            
            if not category_id:
                raise ValueError(
                    f"Could not extract category_id from categories for ASIN {asin}."
                )

            logger.info(
                f"Discovered category_id: {category_id} and search_term: {search_term}"
            )

            return {
                "category_id": category_id,
                "search_term": search_term,
                "method": "Direct from Product API 'categories' field",
            }

        elif url_type in ["category", "search", "bestsellers"]:
            category_id = params.get("category_id")
            search_term = params.get("search_term") or params.get("keywords")
            
            if not category_id and not search_term:
                raise ValueError(f"Could not extract category_id or search_term for URL type '{url_type}' from parameters.")

            # If we only have a search term, we still need a category_id to scrape efficiently.
            # We can use a default or a broader category. For now, we require a category_id.
            if not category_id:
                raise ValueError(f"URL type '{url_type}' requires a category_id, which could not be found in the URL.")

            logger.info(
                f"Discovered category_id: {category_id} and search_term: {search_term} directly from URL"
            )
            return {
                "category_id": category_id,
                "search_term": search_term,
                "method": "Directly from URL parameters",
            }

        # TODO: Implement logic for other URL types like 'category' and 'search'
        else:
            raise NotImplementedError(
                f"URL type '{url_type}' is not yet supported for category discovery."
            )

    def _get_asin_from_url(self, url: str) -> str | None:
        """Extracts the ASIN from an Amazon product URL."""
        try:
            # Split the URL by 'dp/' and take the second part, then split by '/' to isolate the ASIN
            return url.split('dp/')[1].split('/')[0]
        except IndexError:
            return None

    def _discover_category_info_from_url(self, url: str) -> tuple[str, str, str]:
        """
        For a given product URL, discover the category ID, category name, and original ASIN.
        """
        logger.info(f"Discovering category info for product URL: {url}")
        product_details_response = get_product_details_rainforest(url)

        # API response received successfully

        if not product_details_response or 'product' not in product_details_response:
            raise ValueError("Invalid response from product details API")

        product_data = product_details_response['product']
        original_asin = product_data.get('asin')
        if not original_asin:
            original_asin = self._get_asin_from_url(url)
            logger.info(f"ASIN not in response, extracted from URL: {original_asin}")

        categories = product_data.get('categories')
        if not categories:
            raise ValueError("No categories found in product details")

        # The most specific category is the last one in the list.
        category_obj = categories[-1]
        
        logger.info(f"Found category object: {category_obj}")

        if isinstance(category_obj, dict) and 'id' in category_obj:
            category_id = category_obj['id']
            category_name = category_obj.get('name', 'N/A')
            return category_id, category_name, original_asin
        else:
            raise ValueError(f"Could not extract category_id from category object: {category_obj}")

    def scrape_bestsellers(self, url: str) -> list[dict]:
        """
        Scrapes bestsellers from a given URL.
        It can handle both product URLs and category/bestseller URLs.
        """
        logger.info(f"Starting bestsellers scrape for URL: {url}")

        # Default to the passed URL being a category URL
        bestsellers_url = url
        category_id = None
        category_name = "N/A"
        original_asin = None

        # Check if it's a product URL to discover the category first
        if "/dp/" in url or "/gp/product/" in url:
            try:
                category_id, category_name, original_asin = self._discover_category_info_from_url(url)
                logger.info(f"Discovered category '{category_name}' ({category_id}) for original ASIN {original_asin}")
            except ValueError as e:
                logger.error(f"Could not discover category for URL {url}: {e}")
                return [] # Return empty list if category discovery fails
        
        # If we have a category_id, we can get bestsellers for that category
        if category_id:
            logger.info(f"Fetching bestsellers for category ID: {category_id}")
            bestsellers_response = get_bestsellers_rainforest(category_id=category_id)
        else:
            # Fallback for non-product URLs (assuming they are best seller URLs)
            logger.info(f"Fetching bestsellers directly from URL: {bestsellers_url}")
            bestsellers_response = get_bestsellers_rainforest(url=bestsellers_url)

        if not bestsellers_response or 'bestsellers' not in bestsellers_response:
            logger.warning("No bestsellers found in the response.")
            return []

        scraped_products = bestsellers_response['bestsellers']
        logger.info(f"Successfully scraped {len(scraped_products)} products from category '{category_name}'.")

        # Ensure the original product is in the list if it was a product URL scrape
        if original_asin:
            is_original_asin_in_list = any(p['asin'] == original_asin for p in scraped_products)
            if not is_original_asin_in_list:
                logger.info(f"Original ASIN {original_asin} not found in bestsellers list. Adding it.")
                # We need product details to add it to the list
                product_details_response = get_product_details_rainforest(url)
                if product_details_response and 'product' in product_details_response:
                    original_product_data = product_details_response['product']
                    # We need to match the structure of the bestsellers list items
                    scraped_products.append({
                        'rank': 0, # Or some other indicator that it's the original
                        'asin': original_product_data.get('asin'),
                        'title': original_product_data.get('title'),
                        'link': original_product_data.get('link'),
                        'image': original_product_data.get('main_image', {}).get('link')
                    })
        
        return scraped_products


# Global service instance
scraping_service = ScrapingService() 