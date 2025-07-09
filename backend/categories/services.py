"""Categories module services."""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys
from collections import Counter
import asyncio

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database.connection import get_supabase_service_client
sys.path.append(str(Path(__file__).parent.parent / "scraping" / "amazon-cat"))
from category_repository import CategoryRepository
from api_client import RainforestCategoryAPI
from models import CategoryInfo, CategoryFetchStatus
from .models import CategoryNode

# Import scraping utilities
sys.path.append(str(Path(__file__).parent.parent / "scraping"))
from common.url_parser import parse_amazon_url
from common.amazon_api import get_product_details_rainforest, amazon_search

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for managing dynamic category loading."""
    
    def __init__(self):
        """Initialize the category service."""
        self.supabase_client = get_supabase_service_client()
        self.repository = CategoryRepository(self.supabase_client)
        
        # Initialize API client for on-demand fetching
        try:
            self.api_client = RainforestCategoryAPI(delay_seconds=1.0)
            logger.info("RainforestCategoryAPI initialized successfully")
        except ValueError as e:
            logger.warning(f"RainforestCategoryAPI initialization failed - API key required: {e}")
            self.api_client = None
        except Exception as e:
            logger.warning(f"Failed to initialize RainforestCategoryAPI: {e}")
            self.api_client = None
    
    async def get_root_categories(self) -> List[CategoryNode]:
        """Get root level categories (Level 1) - simple single query approach."""
        try:
            # Simple query: just get L1 categories, assume all have children
            result = self.supabase_client.table('amazon_categories')\
                .select('category_id, name, level, parent_category_id')\
                .eq('level', 1)\
                .order('name')\
                .execute()
            
            categories = []
            for row in result.data:
                category_node = CategoryNode(
                    category_id=row['category_id'],
                    name=row['name'],
                    level=row['level'],
                    parent_id=row.get('parent_category_id'),
                    has_children=True,  # Assume all L1 categories have children
                    children_count=0    # Don't pre-calculate count
                )
                categories.append(category_node)
            
            logger.info(f"Retrieved {len(categories)} root categories with single query")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting root categories: {e}")
            raise e  # Don't use fallback, just raise error as requested
    
    async def get_category_children(self, parent_category_id: str) -> List[CategoryNode]:
        """Get children for a specific category, fetch from API if not exists."""
        try:
            # First check if children exist in database
            result = self.supabase_client.table('amazon_categories')\
                .select('*')\
                .eq('parent_category_id', parent_category_id)\
                .order('name')\
                .execute()
            
            if result.data:
                # Children exist in database, return them
                logger.info(f"Found {len(result.data)} existing children for {parent_category_id}")
                return await self._convert_to_category_nodes(result.data)
            else:
                # No children in database, try to fetch from API
                logger.info(f"No children found in DB for {parent_category_id}, trying API fetch")
                return await self._fetch_children_from_api(parent_category_id)
                
        except Exception as e:
            logger.error(f"Error getting children for category {parent_category_id}: {e}")
            return []
    
    async def _convert_to_category_nodes(self, db_rows: List[dict]) -> List[CategoryNode]:
        """Convert database rows to CategoryNode objects - no N+1 queries."""
        categories = []
        for row in db_rows:
            # Don't check children individually to avoid N+1 queries
            # Assume categories below L6 might have children, L6 typically doesn't
            has_children = row['level'] < 6  # Assume categories below level 6 have children
            
            category_node = CategoryNode(
                category_id=row['category_id'],
                name=row['name'],
                level=row['level'],
                parent_id=row.get('parent_category_id'),
                has_children=has_children,
                children_count=0  # Don't pre-calculate count
            )
            categories.append(category_node)
        
        return categories
    
    async def _fetch_children_from_api(self, parent_category_id: str) -> List[CategoryNode]:
        """Simplified API fetch for category children."""
        if not self.api_client:
            logger.warning(f"API client not available for {parent_category_id} - please configure RAINFOREST_API_KEY")
            return []
        
        try:
            # Get parent category info to determine level
            parent_result = self.supabase_client.table('amazon_categories')\
                .select('*')\
                .eq('category_id', parent_category_id)\
                .single()\
                .execute()
            
            if not parent_result.data:
                logger.error(f"Parent category {parent_category_id} not found")
                return []
            
            parent_data = parent_result.data
            parent_level = parent_data['level']
            
            logger.info(f"Fetching children from API for {parent_data['name']} (level {parent_level})")
            
            # Call Amazon API
            api_response = self.api_client.get_category_children(
                parent_id=parent_category_id,
                domain="amazon.com"
            )
            
            if not api_response.success:
                logger.error(f"API call failed for {parent_category_id}: {api_response.error_message}")
                return []
            
            # Parse API response
            category_data_list = self.api_client.parse_categories_from_response(api_response)
            
            if not category_data_list:
                logger.info(f"No children found in API response for {parent_category_id}")
                return []
            
            # Convert to CategoryInfo objects
            children = []
            for cat_data in category_data_list:
                child_category = CategoryInfo(
                    category_id=cat_data["category_id"],
                    name=cat_data["name"],
                    level=parent_level + 1,
                    parent_id=parent_category_id,
                    link=cat_data.get("link"),
                    status=CategoryFetchStatus.COMPLETED
                )
                children.append(child_category)
            
            # Save to database
            if children:
                success_count, failed_count = await self.repository.save_categories_batch(children)
                logger.info(f"Saved {success_count} children for {parent_category_id}, {failed_count} failed")
            
            # Convert to CategoryNode objects for frontend
            category_nodes = []
            for child in children:
                category_node = CategoryNode(
                    category_id=child.category_id,
                    name=child.name,
                    level=child.level,
                    parent_id=child.parent_id,
                    has_children=child.level < 6,  # Assume categories below L6 have children
                    children_count=0
                )
                category_nodes.append(category_node)
            
            logger.info(f"Successfully fetched and saved {len(category_nodes)} children for {parent_category_id}")
            return category_nodes
            
        except Exception as e:
            logger.error(f"Error fetching children from API for {parent_category_id}: {e}")
            return []

    async def _fetch_single_category_from_api(self, category_id: str) -> Optional[dict]:
        """Fetch single category information from API and save to database."""
        try:
            logger.info(f"Fetching category {category_id} from Rainforest API using category endpoint")
            
            # Use category API to get category information
            from ..scraping.common.amazon_api import get_products_from_category_rainforest
            
            category_results = await asyncio.to_thread(
                get_products_from_category_rainforest,
                category_id=category_id,
                amazon_domain="amazon.com",
                page=1
            )
            
            if not category_results:
                logger.warning(f"No category results returned for category {category_id}")
                return None
            
            # Extract category information from the response
            category_name = f"Category {category_id}"
            full_path = category_name
            
            # Try to extract category name from the response
            if "category" in category_results:
                category_info = category_results["category"]
                if "name" in category_info and category_info["name"]:
                    category_name = category_info["name"]
                    full_path = category_name
                    logger.info(f"Extracted category name from API: {category_name}")
            
            # If we didn't get the name from category, try from search_information
            if category_name == f"Category {category_id}" and "search_information" in category_results:
                search_info = category_results["search_information"]
                if "title" in search_info and search_info["title"]:
                    category_name = search_info["title"]
                    full_path = category_name
            
            # Try to save to database
            try:
                self.supabase_client.table('amazon_categories')\
                    .insert({
                        'category_id': category_id,
                        'name': category_name,
                        'full_path': full_path,
                        'level': 1,
                        'parent_category_id': None
                    })\
                    .execute()
                
                logger.info(f"Successfully saved category {category_id} to database")
                        
            except Exception as save_error:
                logger.warning(f"Error saving category {category_id} to database: {save_error}")
            
            # Return the category info regardless of save status
            return {
                "category_id": category_id,
                "name": category_name,
                "full_path": full_path
            }
                
        except Exception as e:
            logger.error(f"Error fetching category {category_id} from API: {e}")
            # Return basic info as fallback
            return {
                "category_id": category_id,
                "name": f"Category {category_id}",
                "full_path": f"Category {category_id}"
            }

    async def get_descendant_categories(self, category_id: str) -> List[str]:
        """Get all descendant category names for product filtering."""
        try:
            # Get all categories that have this category in their path
            result = self.supabase_client.table('amazon_categories')\
                .select('name')\
                .like('full_path', f'%{category_id}%')\
                .execute()
            
            category_names = [row['name'] for row in result.data]
            
            # Also get the category itself
            self_result = self.supabase_client.table('amazon_categories')\
                .select('name')\
                .eq('category_id', category_id)\
                .single()\
                .execute()
            
            if self_result.data:
                category_names.append(self_result.data['name'])
            
            # Remove duplicates and return
            return list(set(category_names))
            
        except Exception as e:
            logger.error(f"Error getting descendant categories for {category_id}: {e}")
            return []

    async def get_category_path(self, category_id: str) -> List[dict]:
        """Get the full category path from root to the specified category."""
        try:
            # Get the category and its full path
            result = self.supabase_client.table('amazon_categories')\
                .select('name, full_path')\
                .eq('category_id', category_id)\
                .single()\
                .execute()
            
            if not result.data:
                return []
            
            # Parse the full path to create the path array
            full_path = result.data.get('full_path', '')
            if not full_path:
                return [{"name": result.data['name'], "category_id": category_id}]
            
            # Split the path and create the path array
            path_parts = full_path.split(' > ')
            path = [{"name": part.strip()} for part in path_parts if part.strip()]
            
            return path
            
        except Exception as e:
            logger.error(f"Error getting category path for {category_id}: {e}")
            return []

    async def get_category_info(self, category_id: str) -> Optional[dict]:
        """Get category information by category_id."""
        try:
            result = self.supabase_client.table('amazon_categories')\
                .select('category_id, name, full_path')\
                .eq('category_id', category_id)\
                .single()\
                .execute()
            
            if result.data:
                return {
                    "category_id": result.data['category_id'],
                    "name": result.data['name'],
                    "full_path": result.data.get('full_path')
                }
            else:
                logger.info(f"Category {category_id} not found in database, attempting to fetch from API")
                return await self._fetch_single_category_from_api(category_id)
                
        except Exception as e:
            logger.error(f"Error getting category info for {category_id}: {e}")
            # Try fetching from API as fallback
            logger.info(f"Attempting API fallback for category {category_id}")
            return await self._fetch_single_category_from_api(category_id)

    async def analyze_url_for_category(self, url: str) -> Dict[str, Any]:
        """
        Analyze Amazon URL and return category suggestions.
        Supports product URLs, search URLs, and category URLs.
        """
        try:
            # Parse URL to determine type
            parsed_info = parse_amazon_url(url)
            url_type = parsed_info.get("url_type")
            
            logger.info(f"Analyzing URL: {url}, detected type: {url_type}")
            logger.info(f"Parsed info: {parsed_info}")
            
            result = None
            if url_type == "product":
                result = await self._analyze_product_url(parsed_info)
            elif url_type == "search":
                result = await self._analyze_search_url(parsed_info)
            elif url_type == "category":
                result = await self._analyze_category_url(parsed_info)
            else:
                result = {
                    "success": False,
                    "url_type": "unknown",
                    "suggestions": [],
                    "confidence_level": "none",
                    "message": f"Unsupported URL type: {url_type}"
                }
            
            logger.info(f"URL analysis result: {result}")
            return result
                
        except Exception as e:
            logger.error(f"Error analyzing URL {url}: {e}")
            error_result = {
                "success": False,
                "url_type": "unknown",
                "suggestions": [],
                "confidence_level": "none",
                "message": f"Failed to analyze URL: {str(e)}"
            }
            logger.info(f"Returning error result: {error_result}")
            return error_result

    async def _analyze_product_url(self, parsed_info: Dict) -> Dict[str, Any]:
        """Analyze product URL to extract category information."""
        asin = parsed_info.get("asin")
        if not asin:
            raise ValueError("Could not extract ASIN from product URL. Please ensure the URL is a valid Amazon product URL (e.g., https://amazon.com/dp/B08N123456)")
        
        logger.info(f"Fetching product details for ASIN: {asin}")
        
        # Get product details from Rainforest API
        try:
            product_details = await asyncio.to_thread(
                get_product_details_rainforest, asin
            )
            logger.info(f"Rainforest API response received for ASIN {asin}: {bool(product_details)}")
        except Exception as e:
            logger.error(f"Error calling Rainforest API for ASIN {asin}: {e}")
            raise ValueError(f"Failed to fetch product details for ASIN {asin}. API error: {str(e)}")
        
        if not product_details:
            logger.error(f"Empty response from Rainforest API for ASIN {asin}")
            raise ValueError(f"Unable to fetch product details for ASIN {asin}. The product may not exist or be unavailable.")
        
        if "product" not in product_details:
            logger.error(f"Invalid product data structure for ASIN {asin}: {list(product_details.keys())}")
            raise ValueError(f"Invalid product data received for ASIN {asin}. Please check if the ASIN is correct.")
        
        product_data = product_details["product"]
        categories = product_data.get("categories", [])
        logger.info(f"Found {len(categories)} categories for ASIN {asin}")
        
        if not categories:
            raise ValueError(f"No category information found for product {asin}. This product may not have proper categorization.")
        
        # Extract the most specific category (last in the list)
        last_category = categories[-1] if categories else None
        if not last_category or "category_id" not in last_category:
            raise ValueError(f"Invalid category data for product {asin}. Unable to extract category ID.")
        
        category_id = last_category["category_id"]
        category_name = last_category.get("name", "Unknown Category")
        
        # Get category info from database if available
        db_category_info = await self.get_category_info(category_id)
        if db_category_info:
            category_name = db_category_info["name"]
            full_path = db_category_info.get("full_path", category_name)
        else:
            full_path = category_name
        
        suggestions = [{
            "category_id": category_id,
            "category_name": category_name,
            "confidence": 0.95,
            "reason": f"Automatically extracted from product details. This is the most specific category for this product. Full path: {full_path}"
        }]
        
        return {
            "success": True,
            "url_type": "product",
            "suggestions": suggestions,
            "confidence_level": "high",
            "message": f"Successfully extracted the highest relevance category from product {asin}. We analyzed this product and identified its most specific category classification."
        }

    async def _analyze_search_url(self, parsed_info: Dict) -> Dict[str, Any]:
        """Analyze search URL to suggest categories based on search results."""
        search_term = parsed_info.get("search_term")
        category_id = parsed_info.get("category_id")
        
        # If URL already contains category_id, use it directly
        if category_id:
            logger.info(f"Found category_id in search URL: {category_id}")
            db_category_info = await self.get_category_info(category_id)
            if db_category_info:
                logger.info(f"Successfully retrieved category info: {db_category_info}")
                suggestions = [{
                    "category_id": category_id,
                    "category_name": db_category_info["name"],
                    "confidence": 0.9,
                    "reason": f"Category ID automatically detected in your search URL. This is the category you were browsing. Full path: {db_category_info.get('full_path', db_category_info['name'])}"
                }]
                
                result = {
                    "success": True,
                    "url_type": "search",
                    "suggestions": suggestions,
                    "confidence_level": "high",
                    "message": f"Successfully extracted category from your search URL. We found that you were browsing in the '{db_category_info['name']}' category."
                }
                logger.info(f"Returning search URL analysis result: {result}")
                return result
            else:
                logger.warning(f"No category info found in database for category_id: {category_id}")
        
        # Search URLs without category_id are not supported
        raise ValueError("Search URLs are not supported. Please provide a valid Amazon category URL with a category ID (node parameter), or use a product URL instead. Example: https://amazon.com/s?node=12345678 or https://amazon.com/dp/B08N123456")

    async def _analyze_category_url(self, parsed_info: Dict) -> Dict[str, Any]:
        """Analyze category URL - direct category ID extraction."""
        category_id = parsed_info.get("category_id")
        if not category_id:
            raise ValueError("Could not extract category ID from URL")
        
        # Get category info from database
        db_category_info = await self.get_category_info(category_id)
        
        category_name = f"Category {category_id}"
        full_path = category_name
        
        if db_category_info:
            category_name = db_category_info["name"]
            full_path = db_category_info.get("full_path", category_name)
        
        suggestions = [{
            "category_id": category_id,
            "category_name": category_name,
            "confidence": 1.0,
            "reason": f"Direct category page URL detected. This is the exact category you provided. Full path: {full_path}"
        }]
        
        return {
            "success": True,
            "url_type": "category",
            "suggestions": suggestions,
            "confidence_level": "high",
            "message": f"Perfect match! We extracted the category '{category_name}' directly from your URL."
        } 