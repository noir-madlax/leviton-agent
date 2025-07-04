from typing import Dict, List, Any, Optional
from .base_service import BaseDashboardService
import logging

logger = logging.getLogger(__name__)

class ProjectOverviewService(BaseDashboardService):
    """Service for handling project overview data and statistics"""
    
    def __init__(self, project_id: str):
        super().__init__(project_id)
    
    def get_data(self) -> Dict[str, Any]:
        """Implementation of abstract method - returns project overview data"""
        return self.get_project_overview()
        
    def get_project_overview(self) -> Dict[str, Any]:
        """Get comprehensive project overview data"""
        try:
            # Get project basic info
            project_info = self._get_project_info()
            
            # Get statistics based on actual project scope
            stats = self._get_project_statistics()
            
            # Get distribution data
            distributions = self._get_project_distributions()
            
            # Get available categories for filtering
            available_categories = self._get_available_categories()
            
            return {
                'project_name': project_info['project_name'],
                'created_at': project_info['created_at'],
                'stats': stats,
                'distributions': distributions,
                'available_categories': available_categories
            }
            
        except Exception as e:
            logger.error(f"Error getting project overview: {e}")
            raise
    
    def _get_project_info(self) -> Dict[str, Any]:
        """Get basic project information"""
        response = self.supabase.table('projects').select(
            'project_name, created_at, selected_product_asins, selected_categories'
        ).eq('id', self.project_id).execute()
        
        if not response.data:
            raise ValueError(f"Project {self.project_id} not found")
            
        return response.data[0]
    
    def _get_project_statistics(self) -> Dict[str, Any]:
        """Get actual project statistics based on selected ASINs"""
        # Get filtered ASINs
        filtered_asins = self.project_asins
        
        if not filtered_asins:
            return {
                'total_products': 0,
                'total_brands': 0,
                'total_reviews': 0,
                'segment_count': 0
            }
        
        # Get product statistics
        product_stats = self.supabase.table('product_wide_table').select(
            'platform_id, brand, reviews_count'
        ).in_('platform_id', filtered_asins).neq('category', None).neq('brand', None).execute()
        
        products = product_stats.data
        
        # Get actual review count from product_reviews table
        actual_reviews = self.supabase.table('product_reviews').select(
            'review_id', count='exact'
        ).in_('product_id', filtered_asins).execute()
        
        # Get segment assignments count
        # First get the product_wide_table IDs for our ASINs
        wide_table_result = self.supabase.table('product_wide_table').select(
            'id'
        ).in_('platform_id', filtered_asins).execute()
        
        if wide_table_result.data:
            wide_table_ids = [item['id'] for item in wide_table_result.data]
            segment_assignments = self.supabase.table('product_segment_assignments').select(
                'product_id', count='exact'
            ).eq('project_id', self.project_id).in_('product_id', wide_table_ids).execute()
        else:
            segment_assignments = type('MockResult', (), {'count': 0})()
        
        # Calculate unique brands
        unique_brands = set(p['brand'] for p in products if p['brand'])
        
        return {
            'total_products': len(products),
            'total_brands': len(unique_brands),
            'total_reviews': actual_reviews.count,  # Fixed: use actual count
            'segment_count': segment_assignments.count
        }
    
    def _get_project_distributions(self) -> Dict[str, Any]:
        """Get distribution data for sources and categories"""
        filtered_asins = self.project_asins
        
        if not filtered_asins:
            return {'sources': [], 'categories': []}
        
        # Get product data for distributions
        response = self.supabase.table('product_wide_table').select(
            'platform_id, category, source'
        ).in_('platform_id', filtered_asins).neq('category', None).execute()
        
        products = response.data
        
        # Calculate source distribution
        source_counts = {}
        for product in products:
            source = product.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        total_products = len(products)
        sources = [
            {
                'name': source,
                'count': count,
                'percentage': round((count / total_products) * 100, 1) if total_products > 0 else 0
            }
            for source, count in source_counts.items()
        ]
        
        # Calculate category distribution
        category_counts = {}
        for product in products:
            category = product.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        categories = [
            {
                'name': category,
                'count': count,
                'percentage': round((count / total_products) * 100, 1) if total_products > 0 else 0
            }
            for category, count in category_counts.items()
        ]
        
        # Sort by count descending
        sources.sort(key=lambda x: x['count'], reverse=True)
        categories.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'sources': sources,
            'categories': categories
        }
    
    def _get_available_categories(self) -> List[str]:
        """Get available categories for filtering"""
        filtered_asins = self.project_asins
        
        if not filtered_asins:
            return []
        
        response = self.supabase.table('product_wide_table').select(
            'category'
        ).in_('platform_id', filtered_asins).neq('category', None).execute()
        
        # Get unique categories
        categories = set(p['category'] for p in response.data if p['category'])
        
        return sorted(list(categories))
    
    def get_available_asins_with_info(self) -> List[Dict[str, Any]]:
        """Get available ASINs with product info for competitor selection"""
        filtered_asins = self.project_asins
        
        if not filtered_asins:
            return []
        
        response = self.supabase.table('product_wide_table').select(
            'platform_id, title, brand, price_usd, reviews_count, category'
        ).in_('platform_id', filtered_asins).neq('category', None).neq('brand', None).execute()
        
        # Sort by reviews count descending for better selection
        products = response.data
        products.sort(key=lambda x: x.get('reviews_count', 0), reverse=True)
        
        return products 