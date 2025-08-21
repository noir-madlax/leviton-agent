"""Optimized base service with shared caching and reduced SQL queries.

This service provides optimized database access patterns to reduce duplicate
queries and improve performance across all dashboard services.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from functools import lru_cache
from core.database.connection import get_supabase_service_client
from dashboard.services.base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class OptimizedBaseService(BaseDashboardService):
    """Optimized base service with shared caching and query optimization."""
    
    def __init__(self, project_id: str):
        super().__init__(project_id)
        self._cache = {}
        self._project_asins_cache = None
        self._segment_assignments_cache = None
        self._review_aspect_data_cache = None
    
    def _get_cached_project_asins(self) -> Set[str]:
        """Get project ASINs with caching."""
        if self._project_asins_cache is None:
            self._project_asins_cache = set(self.project_asins)
        return self._project_asins_cache
    
    def _get_cached_segment_assignments(self) -> Dict[str, str]:
        """Get segment assignments with caching."""
        if self._segment_assignments_cache is None:
            client = get_supabase_service_client()
            result = client.table('product_segment_assignments').select(
                'product_asin, segment_name'
            ).eq('project_id', self.project_id).execute()
            
            self._segment_assignments_cache = {
                row['product_asin']: row['segment_name'] 
                for row in result.data
            }
        return self._segment_assignments_cache
    
    def _get_cached_review_aspect_data(self, include_review_content: bool = False) -> List[Dict[str, Any]]:
        """Get review aspect data with caching."""
        cache_key = f"review_aspect_data_{include_review_content}"
        
        if cache_key not in self._cache:
            client = get_supabase_service_client()
            
            # Build query based on whether review content is needed
            if include_review_content:
                query = """
                    SELECT 
                        raa.aspect_description,
                        raa.sentiment,
                        raa.aspect_type,
                        raac.category_name,
                        raac.definition as category_definition,
                        raac.category_type,
                        rao.product_asin,
                        rao.total_reviews,
                        rao.positive_reviews,
                        rao.negative_reviews,
                        rao.neutral_reviews,
                        r.review_text,
                        r.rating,
                        r.verified,
                        r.review_date,
                        p.brand
                    FROM review_analysis_aspects raa
                    JOIN review_analysis_aspect_categories raac ON raa.category_id = raac.category_id
                    JOIN review_analysis_aspect_occurrences rao ON raac.category_id = rao.category_id
                    JOIN reviews r ON raa.review_id = r.review_id
                    JOIN products p ON r.product_asin = p.platform_id
                    WHERE rao.product_asin = ANY($1)
                    ORDER BY rao.total_reviews DESC, raac.category_name
                """
            else:
                query = """
                    SELECT 
                        raac.category_name,
                        raac.definition as category_definition,
                        raac.category_type,
                        rao.product_asin,
                        rao.total_reviews,
                        rao.positive_reviews,
                        rao.negative_reviews,
                        rao.neutral_reviews
                    FROM review_analysis_aspect_categories raac
                    JOIN review_analysis_aspect_occurrences rao ON raac.category_id = rao.category_id
                    WHERE rao.product_asin = ANY($1)
                    ORDER BY rao.total_reviews DESC, raac.category_name
                """
            
            result = client.rpc('exec_sql', {'query': query, 'params': [list(self._get_cached_project_asins())]}).execute()
            self._cache[cache_key] = result.data or []
        
        return self._cache[cache_key]
    
    def _get_shared_product_info(self) -> Dict[str, Dict[str, Any]]:
        """Get shared product information with caching."""
        if 'product_info' not in self._cache:
            client = get_supabase_service_client()
            result = client.table('products').select(
                'platform_id, title, brand, price_usd, past_year_volume, past_year_revenue, category, product_segment'
            ).in_('platform_id', list(self._get_cached_project_asins())).execute()
            
            self._cache['product_info'] = {
                row['platform_id']: row for row in result.data
            }
        
        return self._cache['product_info']
    
    def _get_shared_sales_data(self) -> Dict[str, Dict[str, Any]]:
        """Get shared sales data with caching."""
        if 'sales_data' not in self._cache:
            client = get_supabase_service_client()
            result = client.table('sales_history_monthly').select(
                'product_asin, month, revenue, volume'
            ).in_('product_asin', list(self._get_cached_project_asins())).execute()
            
            # Group by product ASIN
            sales_by_product = {}
            for row in result.data:
                asin = row['product_asin']
                if asin not in sales_by_product:
                    sales_by_product[asin] = []
                sales_by_product[asin].append(row)
            
            self._cache['sales_data'] = sales_by_product
        
        return self._cache['sales_data']
    
    def _aggregate_review_data_by_category(self, review_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Aggregate review data by category with optimized processing."""
        category_stats = {}
        
        for row in review_data:
            category_name = row['category_name']
            product_asin = row['product_asin']
            
            if category_name not in category_stats:
                category_stats[category_name] = {
                    'categoryType': row['category_type'],
                    'totalMentions': 0,
                    'productData': {}
                }
            
            category_stats[category_name]['totalMentions'] += row['total_reviews']
            
            if product_asin not in category_stats[category_name]['productData']:
                category_stats[category_name]['productData'][product_asin] = {
                    'total': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0
                }
            
            product_data = category_stats[category_name]['productData'][product_asin]
            product_data['total'] += row['total_reviews']
            product_data['positive'] += row['positive_reviews']
            product_data['negative'] += row['negative_reviews']
            product_data['neutral'] += row['neutral_reviews']
        
        return category_stats
    
    def _aggregate_use_case_data(self, review_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Aggregate use case data with optimized processing."""
        use_case_stats = {}
        
        # Filter for use case data (aspect_type = 'use')
        use_case_data = [row for row in review_data if row.get('aspect_type') == 'use']
        
        for row in use_case_data:
            use_case = row['category_name']
            product_asin = row['product_asin']
            
            if use_case not in use_case_stats:
                use_case_stats[use_case] = {
                    'totalMentions': 0,
                    'productData': {}
                }
            
            use_case_stats[use_case]['totalMentions'] += row['total_reviews']
            
            if product_asin not in use_case_stats[use_case]['productData']:
                use_case_stats[use_case]['productData'][product_asin] = {
                    'total': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0
                }
            
            product_data = use_case_stats[use_case]['productData'][product_asin]
            product_data['total'] += row['total_reviews']
            product_data['positive'] += row['positive_reviews']
            product_data['negative'] += row['negative_reviews']
            product_data['neutral'] += row['neutral_reviews']
        
        return use_case_stats
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._project_asins_cache = None
        self._segment_assignments_cache = None
        self._review_aspect_data_cache = None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            'cache_keys': list(self._cache.keys()),
            'cache_size': len(self._cache),
            'project_asins_cached': self._project_asins_cache is not None,
            'segment_assignments_cached': self._segment_assignments_cache is not None,
            'review_aspect_data_cached': self._review_aspect_data_cache is not None
        } 