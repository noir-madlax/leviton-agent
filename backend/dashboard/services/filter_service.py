from typing import Optional, List, Dict, Any
from supabase import Client
from core.models.filters import ProjectFilters, FilterOptions
import logging

logger = logging.getLogger(__name__)

class FilterService:
    """筛选器服务"""
    
    def __init__(self, supabase_client: Client, project_asins: List[str]):
        self.supabase = supabase_client
        self.project_asins = project_asins
    
    def apply_filters(self, query, filters: ProjectFilters):
        """应用筛选器到查询"""
        # 首先应用项目ASIN过滤（安全边界）
        query = self._apply_asin_filter(query)
        
        # 应用其他筛选器
        if filters.categories:
            query = query.in_('category', filters.categories)
            logger.info(f"Applied category filter: {filters.categories}")
        
        if filters.brands:  # 改：packaging_types -> brands
            query = query.in_('brand', filters.brands)  # 改：packaging_type -> brand
            logger.info(f"Applied brands filter: {filters.brands}")
        
        if filters.segments:
            query = query.in_('segment', filters.segments)
            logger.info(f"Applied segments filter: {filters.segments}")

        # 应用is_bestseller筛选
        if filters.is_bestseller is not None:
            if filters.is_bestseller == "true":
                query = query.eq('is_bestseller', True)
                logger.info(f"Applied is_bestseller filter: true")
            elif filters.is_bestseller == "false":
                query = query.eq('is_bestseller', False)
                logger.info(f"Applied is_bestseller filter: false")
            elif filters.is_bestseller == "null":
                query = query.is_('is_bestseller', None)
                logger.info(f"Applied is_bestseller filter: null")

        # 应用extend_fields筛选
        for field_name, field_value in filters.extend_fields.items():
            if field_value is not None:
                query = query.eq(field_name, field_value)
                logger.info(f"Applied extend_field filter: {field_name} = {field_value}")

        return query
    
    def _apply_asin_filter(self, query):
        """应用ASIN过滤"""
        if not self.project_asins:
            raise ValueError("Cannot apply ASIN filter: project has no ASINs")
        return query.in_('platform_id', self.project_asins)
    
    def get_available_options(self, filters: Optional[ProjectFilters] = None) -> FilterOptions:
        """获取可用的筛选选项"""
        query = self.supabase.table('amazon_products').select('*')
        query = self._apply_asin_filter(query)
        
        # 如果有预筛选器，先应用
        if filters and not filters.is_empty():
            query = self.apply_filters(query, filters)
        
        try:
            data = query.execute().data
            
            # 从数据中提取唯一值
            categories = list(set(item['category'] for item in data if item.get('category')))
            brands = list(set(item['brand'] for item in data if item.get('brand')))  # 改：packaging_type -> brand
            segments = list(set(item['segment'] for item in data if item.get('segment')))

            # 获取is_bestseller的选项
            is_bestseller_values = set()
            for item in data:
                bestseller_value = item.get('is_bestseller')
                if bestseller_value is True:
                    is_bestseller_values.add("true")
                elif bestseller_value is False:
                    is_bestseller_values.add("false")
                elif bestseller_value is None:
                    is_bestseller_values.add("null")
            is_bestseller_options = list(is_bestseller_values)

            # 获取extend_fields的选项
            extend_fields = {}
            for item in data:
                for key, value in item.items():
                    if key.startswith('extend_') and value is not None:
                        if key not in extend_fields:
                            extend_fields[key] = set()
                        extend_fields[key].add(str(value))

            # 转换为列表
            extend_fields = {k: list(v) for k, v in extend_fields.items()}

            return FilterOptions(
                categories=categories,
                brands=brands,  # 改：packaging_types -> brands
                segments=segments,
                is_bestseller_options=is_bestseller_options,
                extend_fields=extend_fields
            )
            
        except Exception as e:
            logger.error(f"Failed to get available options: {e}")
            return FilterOptions(
                categories=[],
                brands=[],  # 改：packaging_types -> brands
                segments=[],
                is_bestseller_options=[],
                extend_fields={}
            )
    
    def get_project_segments(self, project_id: str) -> List[str]:
        """获取项目的所有segments"""
        try:
            query = self.supabase.table('product_segment_assignment').select('segment_name').eq('project_id', project_id)
            data = query.execute().data
            
            segments = list(set(item['segment_name'] for item in data if item.get('segment_name')))
            return segments
            
        except Exception as e:
            logger.error(f"Failed to get project segments: {e}")
            return [] 