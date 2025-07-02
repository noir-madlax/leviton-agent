"""Categories module services."""

import logging
from typing import List, Optional
from pathlib import Path
import sys

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database.connection import get_supabase_service_client
sys.path.append(str(Path(__file__).parent.parent / "scraping" / "amazon-cat"))
from category_repository import CategoryRepository
from api_client import RainforestCategoryAPI
from models import CategoryInfo, CategoryFetchStatus
from .models import CategoryNode

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
            # Get the category and its path
            result = self.supabase_client.table('amazon_categories')\
                .select('*')\
                .eq('category_id', category_id)\
                .single()\
                .execute()
            
            if not result.data:
                return []
            
            category = result.data
            path = [{'category_id': category['category_id'], 'name': category['name'], 'level': category['level']}]
            
            # Traverse up the hierarchy
            current_parent_id = category.get('parent_category_id')
            while current_parent_id:
                parent_result = self.supabase_client.table('amazon_categories')\
                    .select('*')\
                    .eq('category_id', current_parent_id)\
                    .single()\
                    .execute()
                
                if parent_result.data:
                    parent = parent_result.data
                    path.insert(0, {'category_id': parent['category_id'], 'name': parent['name'], 'level': parent['level']})
                    current_parent_id = parent.get('parent_category_id')
                else:
                    break
            
            return path
            
        except Exception as e:
            logger.error(f"Error getting category path for {category_id}: {e}")
            return [] 