"""Base service for dashboard data with unified ASIN filtering."""

import logging
from typing import List, Optional
from abc import ABC, abstractmethod

from core.database.connection import get_supabase_client

logger = logging.getLogger(__name__)


class BaseDashboardService(ABC):
    """Base service for dashboard data queries with unified ASIN filtering.
    
    This class ensures ALL dashboard queries are filtered by project ASIN list
    to prevent data leakage between projects.
    """
    
    def __init__(self, project_id: str):
        """Initialize with project ID and extract ASIN filter list."""
        self.project_id = project_id
        self.supabase = get_supabase_client()
        self.project_asins = self._get_project_asins()
        
        if not self.project_asins:
            raise ValueError(f"Project {project_id} has no ASIN filter defined")
        
        logger.info(f"Dashboard service initialized for project {project_id} with {len(self.project_asins)} ASINs")
    
    def _get_project_asins(self) -> List[str]:
        """Get ASIN list from project configuration.
        
        This is the core filtering mechanism - ALL queries must use this ASIN list.
        """
        try:
            result = self.supabase.table('projects').select('selected_product_asins').eq('id', self.project_id).single().execute()
            
            if not result.data:
                raise ValueError(f"Project {self.project_id} not found")
            
            asins = result.data.get('selected_product_asins', [])
            if not asins:
                logger.warning(f"Project {self.project_id} has empty ASIN list")
                return []
            
            return asins
            
        except Exception as e:
            logger.error(f"Error getting project ASINs: {e}")
            raise
    
    def _apply_asin_filter(self, query):
        """Apply ASIN filtering to any Supabase query.
        
        This is the critical method that ensures NO data leakage.
        Every subclass MUST use this method for product data queries.
        """
        if not self.project_asins:
            raise ValueError("Cannot apply ASIN filter: project has no ASINs")
        
        return query.in_('platform_id', self.project_asins)
    
    def _get_base_product_table(self):
        """Get base product table reference."""
        return self.supabase.table('product_wide_table')
    
    def _apply_base_filters(self, query):
        """Apply standard base filters to query."""
        return (query
                .eq('source', 'amazon')
                .neq('product_segment', 'OUT_OF_SCOPE')
                .neq('product_segment', None)
                .neq('brand', None))
    
    @abstractmethod
    def get_data(self):
        """Abstract method to be implemented by subclasses."""
        pass 