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
        """Get actual project statistics based on selected ASINs and category filters"""
        # Get filtered ASINs
        filtered_asins = self.project_asins
        
        if not filtered_asins:
            return {
                'total_products': 0,
                'total_brands': 0,
                'total_reviews': 0,
                'segment_count': 0
            }
        
        # Get product statistics with all filtering applied
        query = self.supabase.table('product_wide_table').select(
            'platform_id, brand, reviews_count'
        ).in_('platform_id', filtered_asins).neq('category', None).neq('brand', None)
        
        # Apply all filters including packaging and segments
        query = self._apply_combined_filters(query)
        
        product_stats = query.execute()
        
        products = product_stats.data
        
        # Get actual review count from product_reviews table
        # First get filtered product IDs based on all filters
        if self.filters.has_filters():
            # Get filtered product IDs based on all filters
            filtered_products_query = self.supabase.table('product_wide_table').select(
                'platform_id'
            ).in_('platform_id', filtered_asins)
            filtered_products_query = self._apply_combined_filters(filtered_products_query)
            filtered_products_response = filtered_products_query.execute()
            review_product_ids = [p['platform_id'] for p in filtered_products_response.data]
        else:
            review_product_ids = filtered_asins
        
        actual_reviews = self.supabase.table('product_reviews').select(
            'review_id', count='exact'
        ).in_('product_id', review_product_ids).execute()
        
        # Get segment count from product_wide_table (not assignments)
        # Use the actual product_segment field and exclude OUT_OF_SCOPE
        segments_query = self.supabase.table('product_wide_table').select(
            'product_segment'
        ).in_('platform_id', filtered_asins).neq('product_segment', None).neq('product_segment', 'OUT_OF_SCOPE')
        
        # Apply all filters including packaging and segments
        segments_query = self._apply_combined_filters(segments_query)
        
        segments_response = segments_query.execute()
        
        if segments_response.data:
            # Calculate unique segments (excluding OUT_OF_SCOPE)
            unique_segments = set(p['product_segment'] for p in segments_response.data if p['product_segment'] and p['product_segment'] != 'OUT_OF_SCOPE')
            segment_count = len(unique_segments)
        else:
            segment_count = 0
        
        # Calculate unique brands
        unique_brands = set(p['brand'] for p in products if p['brand'])
        
        return {
            'total_products': len(products),
            'total_brands': len(unique_brands),
            'total_reviews': actual_reviews.count,  # Fixed: use actual count
            'segment_count': segment_count
        }
    
    def _get_project_distributions(self) -> Dict[str, Any]:
        """Get distribution data for sources, categories, brands, and segments
        
        根据当前应用的所有filter（categories、brands、segments）
        动态计算数据分布统计。
        """
        filtered_asins = self.project_asins
        
        if not filtered_asins:
            return {'sources': [], 'categories': [], 'brands': [], 'segments': []}
        
        # Get product data for distributions with ALL filters applied
        query = self.supabase.table('product_wide_table').select(
            'platform_id, category, source, brand'
        ).in_('platform_id', filtered_asins).neq('category', None)
        
        # Apply ALL filters (categories, brands, segments) to get filtered distribution
        query = self._apply_combined_filters(query)
        
        response = query.execute()
        
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
        
        # Calculate category distribution (from filtered products)
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
        
        # Calculate brand distribution (from filtered products)
        brand_counts = {}
        for product in products:
            brand = product.get('brand', 'Unknown')
            if brand:  # Only count non-null brands
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
        
        brands = [
            {
                'name': brand,
                'count': count,
                'percentage': round((count / total_products) * 100, 1) if total_products > 0 else 0
            }
            for brand, count in brand_counts.items()
        ]
        
        # Calculate segments distribution from product_segment_assignments table
        # This also needs to respect the current filters
        segments = []
        try:
            # 获取filtered products对应的product IDs
            if products:
                filtered_platform_ids = [p['platform_id'] for p in products]
                
                product_ids_query = self.supabase.table('product_wide_table').select(
                    'id, platform_id'
                ).in_('platform_id', filtered_platform_ids).execute()
                
                if product_ids_query.data:
                    product_ids = [p['id'] for p in product_ids_query.data]
                    
                    segments_response = self.supabase.table('product_segment_assignments').select(
                        'segment_name'
                    ).eq('project_id', self.project_id)\
                    .in_('product_id', product_ids)\
                    .neq('segment_name', None)\
                    .neq('segment_name', 'OUT_OF_SCOPE')\
                    .execute()
                    
                    if segments_response.data:
                        segment_counts = {}
                        for assignment in segments_response.data:
                            segment_name = assignment.get('segment_name')
                            if segment_name:
                                segment_counts[segment_name] = segment_counts.get(segment_name, 0) + 1
                        
                        total_segments = sum(segment_counts.values())
                        segments = [
                            {
                                'name': segment_name,
                                'count': count,
                                'percentage': round((count / total_segments) * 100, 1) if total_segments > 0 else 0
                            }
                            for segment_name, count in segment_counts.items()
                        ]
                        segments.sort(key=lambda x: x['count'], reverse=True)
                        
        except Exception as e:
            logger.error(f"Error calculating segments distribution: {e}")
            segments = []
        
        # Sort by count descending
        sources.sort(key=lambda x: x['count'], reverse=True)
        categories.sort(key=lambda x: x['count'], reverse=True)
        brands.sort(key=lambda x: x['count'], reverse=True)
        
        # Calculate extend fields distribution
        extend_fields_distributions = {}
        try:
            # 获取项目的extend fields定义
            extend_fields_defs = self.get_project_extend_fields()
            
            if extend_fields_defs and products:
                # 获取filtered products对应的extend fields数据
                filtered_platform_ids = [p['platform_id'] for p in products]
                
                extend_data_query = self.supabase.table('project_extend_data').select(
                    'asins, extend'
                ).eq('project_id', self.project_id)\
                .in_('asins', filtered_platform_ids)\
                .execute()
                
                if extend_data_query.data:
                    # 为每个extend field计算分布
                    for field_def in extend_fields_defs:
                        field_name = field_def['field_name']
                        field_type = field_def['field_type']
                        
                        field_counts = {}
                        for data_row in extend_data_query.data:
                            extend_data = data_row.get('extend', {})
                            field_value = extend_data.get(field_name)
                            
                            if field_value is not None:
                                # 对于boolean类型，转换为更友好的显示格式
                                if field_type == 'boolean':
                                    if field_value == 'true' or field_value is True:
                                        display_value = field_def['filter_options'].get('true_label', 'Yes')
                                    else:
                                        display_value = field_def['filter_options'].get('false_label', 'No')
                                else:
                                    display_value = str(field_value)
                                
                                field_counts[display_value] = field_counts.get(display_value, 0) + 1
                        
                        # 计算百分比
                        total_field_count = sum(field_counts.values())
                        field_distribution = [
                            {
                                'name': value,
                                'count': count,
                                'percentage': round((count / total_field_count) * 100, 1) if total_field_count > 0 else 0
                            }
                            for value, count in field_counts.items()
                        ]
                        field_distribution.sort(key=lambda x: x['count'], reverse=True)
                        
                        extend_fields_distributions[field_name] = field_distribution
                        
        except Exception as e:
            logger.error(f"Error calculating extend fields distribution: {e}")
            extend_fields_distributions = {}
        
        return {
            'sources': sources,
            'categories': categories,
            'brands': brands,
            'segments': segments,
            'extend_fields': extend_fields_distributions
        }
    
    def _get_available_categories(self) -> Dict[str, Any]:
        """Get available categories with hierarchy for filtering"""
        filtered_asins = self.project_asins
        
        if not filtered_asins:
            return {
                "flat_categories": [],
                "hierarchical_categories": []
            }
        
        response = self.supabase.table('product_wide_table').select(
            'category, categories_flat'
        ).in_('platform_id', filtered_asins).neq('category', None).execute()
        
        # 解析层级关系
        category_hierarchy = {}
        category_counts = {}
        
        for product in response.data:
            leaf_category = product.get('category')
            categories_flat = product.get('categories_flat', '')
            
            if not leaf_category:
                continue
                
            # 计数
            category_counts[leaf_category] = category_counts.get(leaf_category, 0) + 1
            
            # 解析父类别（向上一层）
            parent_category = "其他类别"  # 默认分组
            
            if categories_flat and ' > ' in categories_flat:
                path_parts = [part.strip() for part in categories_flat.split(' > ')]
                if len(path_parts) >= 2:
                    parent_category = path_parts[-2]  # 倒数第二个是父类别
            
            # 构建层级结构
            if parent_category not in category_hierarchy:
                category_hierarchy[parent_category] = []
            
            if leaf_category not in category_hierarchy[parent_category]:
                category_hierarchy[parent_category].append(leaf_category)
        
        # 构建返回数据
        hierarchical_categories = []
        total_products = sum(category_counts.values())
        
        for parent, children in category_hierarchy.items():
            parent_count = sum(category_counts.get(child, 0) for child in children)
            
            hierarchical_categories.append({
                "parent_category": parent,
                "parent_count": parent_count,
                "children": [
                    {
                        "category": child,
                        "count": category_counts.get(child, 0),
                        "percentage": round((category_counts.get(child, 0) / total_products) * 100, 1) if total_products > 0 else 0
                    }
                    for child in sorted(children)
                ]
            })
        
        # 按父类别产品数量排序
        hierarchical_categories.sort(key=lambda x: x["parent_count"], reverse=True)
        
        return {
            "flat_categories": sorted(list(category_counts.keys())),
            "hierarchical_categories": hierarchical_categories,
            "total_products": total_products
        }
    
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