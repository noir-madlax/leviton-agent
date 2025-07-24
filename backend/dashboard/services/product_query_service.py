"""产品查询服务"""

from typing import List, Optional, Dict, Any
import logging
from supabase import Client

from .base_service import BaseDashboardService
from ..models import DashboardQueryOptions
from core.models.filters import EnhancedProjectFilters

logger = logging.getLogger(__name__)

class ProductQueryService(BaseDashboardService):
    """专门用于产品查询的服务类"""

    def __init__(self, project_id: str):
        super().__init__(project_id)
        self.enhanced_filters: Optional[EnhancedProjectFilters] = None

    def get_data(self):
        """实现抽象方法 - 返回基础产品数据"""
        query = self._build_product_query()
        result = query.execute()
        return {
            'products': self._process_products(result.data or []),
            'total_count': len(result.data or [])
        }
    
    def set_project_filters(self, filters):
        """重写父类方法，支持增强筛选器"""
        if isinstance(filters, dict):
            # 如果是字典，尝试转换为增强筛选器
            self.enhanced_filters = EnhancedProjectFilters.from_dict(filters)
            # 同时设置基础筛选器（保持兼容性）
            super().set_project_filters(self.enhanced_filters)
        elif hasattr(filters, 'exclude_asins'):
            # 如果已经是EnhancedProjectFilters对象
            self.enhanced_filters = filters
            super().set_project_filters(filters)
        else:
            # 如果是普通ProjectFilters对象，转换为增强筛选器
            filter_dict = filters.to_dict() if hasattr(filters, 'to_dict') else {}
            self.enhanced_filters = EnhancedProjectFilters.from_dict(filter_dict)
            super().set_project_filters(filters)
    
    def query_products_enhanced(self, options: DashboardQueryOptions) -> Dict[str, Any]:
        """执行增强的产品查询"""
        # 构建基础查询
        query = self._build_product_query()
        
        # 应用增强筛选条件
        query = self._apply_enhanced_filters(query)
        
        # 应用排序
        query = self._apply_sorting(query, options)
        
        # 获取总数（用于分页）
        total_count = self._get_total_count(query)
        
        # 应用分页
        if options.limit:
            query = query.limit(options.limit)
        if options.offset:
            query = query.offset(options.offset)
        
        # 执行查询
        result = query.execute()
        
        # 处理结果
        products = self._process_products(result.data or [])
        
        # 计算统计信息
        stats = self._calculate_statistics(result.data or [])
        
        return {
            'products': products,
            'total_count': total_count,
            'applied_filters': self.enhanced_filters.to_dict() if self.enhanced_filters else {},
            'stats': stats
        }
    
    def get_quick_statistics(self) -> Dict[str, Any]:
        """获取快速统计信息"""
        # _build_product_query 会自动加载segment映射
        query = self._build_product_query()

        result = query.execute()

        return self._calculate_comprehensive_statistics(result.data or [])
    
    def _build_product_query(self):
        """构建产品查询，只在需要segment筛选时查询segment数据"""
        try:
            # 检查是否需要segment筛选
            need_segment_filter = (self.project_filters and 
                                  self.project_filters.segments and 
                                  len(self.project_filters.segments) > 0)
            
            if need_segment_filter:
                # 只有在需要segment筛选时才查询segment assignments
                logger.info(f"Segment filter required, querying segment assignments for project {self.project_id}")
                segment_assignments = self.supabase.table('product_segment_assignments').select(
                    'product_id, segment_name'
                ).eq('project_id', self.project_id).execute()

                # 创建产品ID到segment的映射
                self._segment_map = {}
                project_product_ids = set()

                for assignment in segment_assignments.data or []:
                    product_id = assignment.get('product_id')
                    segment_name = assignment.get('segment_name')
                    if product_id:
                        project_product_ids.add(product_id)
                        self._segment_map[product_id] = segment_name

                logger.info(f"Found {len(project_product_ids)} products in segment assignments")

                if not project_product_ids:
                    # 如果需要segment筛选但没有segment数据，返回空结果
                    logger.warning(f"No segment assignments found for project {self.project_id}")
                    return self.supabase.table('product_wide_table').select('*').eq('id', -1)

                # 基于segment assignments查询产品
                query = self.supabase.table('product_wide_table').select(
                    'id, platform_id, title, brand, category, '
                    'price_usd, unit_price_calculated, past_year_revenue, '
                    'past_year_volume, rating, reviews_count, product_url, pack_count'
                ).in_('id', list(project_product_ids))
            else:
                # 不需要segment筛选时，直接基于项目ASINs查询
                logger.info(f"No segment filter needed, querying directly by project ASINs for project {self.project_id}")
                self._segment_map = {}  # 设置为空，表示没有segment信息
                query = self.supabase.table('product_wide_table').select(
                    'id, platform_id, title, brand, category, '
                    'price_usd, unit_price_calculated, past_year_revenue, '
                    'past_year_volume, rating, reviews_count, product_url, pack_count'
                )

        except Exception as e:
            logger.error(f"Failed to get segment assignments: {e}")
            # 出错时回退到基础查询
            self._segment_map = {}
            query = self.supabase.table('product_wide_table').select(
                'id, platform_id, title, brand, category, '
                'price_usd, unit_price_calculated, past_year_revenue, '
                'past_year_volume, rating, reviews_count, product_url, pack_count'
            )

        # 应用项目ASIN过滤（安全边界）
        query = self._apply_asin_filter(query)

        # 调试：打印筛选器状态
        logger.info(f"Project filters in _build_product_query: {self.project_filters.to_dict()}")

        # 应用基础项目级筛选器
        query = self._apply_project_filters(query)

        return query
    
    def _apply_project_filters(self, query):
        """应用项目级筛选器"""
        if not self.project_filters:
            return query

        filters = self.project_filters

        # Category过滤
        if filters.categories:
            query = query.in_('category', filters.categories)

        # Brand过滤
        if filters.brands:
            query = query.in_('brand', filters.brands)

        # Segment过滤 - 需要使用内存映射
        if filters.segments and hasattr(self, '_segment_map') and self._segment_map:
            # 筛选出匹配segments的product IDs
            matching_product_ids = [
                product_id for product_id, segment_name in self._segment_map.items()
                if segment_name in filters.segments
            ]
            
            if matching_product_ids:
                query = query.in_('id', matching_product_ids)
            else:
                # 如果没有找到匹配的产品，返回空结果
                logger.warning(f"No products found for segments {filters.segments}")
                query = query.eq('id', -1)  # 这会返回空结果
        elif filters.segments and not (hasattr(self, '_segment_map') and self._segment_map):
            # 如果需要segment筛选但没有segment映射数据，说明配置有误，记录警告但不阻断查询
            logger.warning(f"Segment filter requested {filters.segments} but no segment mapping available, skipping segment filter")

        # 扩展字段筛选 (新) - 调用基类的方法
        if filters.extend_fields:
            query = self._apply_extend_fields_filter(query)

        return query

    def _apply_enhanced_filters(self, query):
        """应用增强筛选条件"""
        if not self.enhanced_filters:
            return query

        filters = self.enhanced_filters

        # 排除特定ASIN
        if hasattr(filters, 'exclude_asins') and filters.exclude_asins:
            query = query.not_.in_('platform_id', filters.exclude_asins)

        return query
    
    def _apply_sorting(self, query, options: DashboardQueryOptions):
        """应用排序"""
        if not options.sort_by:
            return query.order('past_year_revenue', desc=True)
        
        sort_field_map = {
            'price': 'price_usd',
            'revenue': 'past_year_revenue',
            'volume': 'past_year_volume',
            'rating': 'rating',
            'reviews_count': 'reviews_count'
        }
        
        field = sort_field_map.get(options.sort_by, 'past_year_revenue')
        ascending = options.sort_order == 'asc'
        
        return query.order(field, desc=not ascending)
    
    def _get_total_count(self, query) -> int:
        """获取总记录数"""
        try:
            # 创建一个只计数的查询
            count_query = query.select('platform_id', count='exact')
            result = count_query.execute()
            return result.count or 0
        except Exception as e:
            logger.warning(f"Failed to get total count: {e}")
            return 0

    def _process_products(self, raw_data: List[Dict]) -> List[Dict]:
        """处理产品数据并添加segment信息"""
        products = []

        for item in raw_data:
            # 安全地处理数值字段
            def safe_float(value):
                if value is None:
                    return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0

            def safe_int(value, default=0):
                if value is None:
                    return default
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            platform_id = item.get('platform_id', '')

            # 获取segment信息（如果可用）
            segment_name = None
            if hasattr(self, '_segment_map') and self._segment_map:
                product_id = item.get('id')
                segment_name = self._segment_map.get(product_id, 'Unknown Segment')

            product = {
                'id': platform_id,  # API返回使用 platform_id 作为产品ID
                'name': item.get('title', ''),
                'brand': item.get('brand', ''),
                'category': item.get('category'),
                'segment': segment_name,  # 使用内存映射的 segment_name
                'price': safe_float(item.get('price_usd')),
                'unitPrice': safe_float(item.get('unit_price_calculated')) or safe_float(item.get('price_usd')),
                'revenue': safe_float(item.get('past_year_revenue')),
                'volume': safe_int(item.get('past_year_volume')),
                'rating': safe_float(item.get('rating')) if item.get('rating') is not None else None,
                'reviews_count': safe_int(item.get('reviews_count')) if item.get('reviews_count') is not None else None,
                'url': item.get('product_url', ''),
                'packCount': safe_int(item.get('pack_count'), 1)
            }

            products.append(product)

        return products
    
    def _calculate_statistics(self, data: List[Dict]) -> Dict[str, Any]:
        """计算统计信息"""
        if not data:
            return {}

        # 安全的数值转换和过滤
        def safe_float_list(items, field):
            result = []
            for item in items:
                value = item.get(field)
                if value is not None:
                    try:
                        result.append(float(value))
                    except (ValueError, TypeError):
                        continue
            return result

        def safe_int_list(items, field):
            result = []
            for item in items:
                value = item.get(field)
                if value is not None:
                    try:
                        result.append(int(value))
                    except (ValueError, TypeError):
                        continue
            return result

        prices = safe_float_list(data, 'price_usd')
        revenues = safe_float_list(data, 'past_year_revenue')
        volumes = safe_int_list(data, 'past_year_volume')

        stats = {
            'total_products': len(data)
        }

        if prices:
            stats['price_range'] = {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices)
            }

        if revenues:
            stats['revenue_range'] = {
                'min': min(revenues),
                'max': max(revenues),
                'total': sum(revenues)
            }

        if volumes:
            stats['volume_range'] = {
                'min': min(volumes),
                'max': max(volumes),
                'total': sum(volumes)
            }

        return stats

    def _calculate_comprehensive_statistics(self, data: List[Dict]) -> Dict[str, Any]:
        """计算全面的统计信息"""
        if not data:
            return {'total_count': 0}

        # 基础统计
        total_count = len(data)

        # 安全的数值转换和过滤
        def safe_float_list(items, field):
            result = []
            for item in items:
                value = item.get(field)
                if value is not None:
                    try:
                        result.append(float(value))
                    except (ValueError, TypeError):
                        continue
            return result

        def safe_int_list(items, field):
            result = []
            for item in items:
                value = item.get(field)
                if value is not None:
                    try:
                        result.append(int(value))
                    except (ValueError, TypeError):
                        continue
            return result

        # 价格统计
        prices = safe_float_list(data, 'price_usd')
        unit_prices = safe_float_list(data, 'unit_price_calculated')

        # 销售统计
        revenues = safe_float_list(data, 'past_year_revenue')
        volumes = safe_int_list(data, 'past_year_volume')

        # 分类统计
        categories = {}
        brands = {}
        segments = {}
        
        for item in data:
            # 类别统计
            category = item.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
            
            # 品牌统计
            brand = item.get('brand', 'Unknown')
            brands[brand] = brands.get(brand, 0) + 1
            
            # 细分统计
            segment = item.get('product_segment', 'Unknown')
            segments[segment] = segments.get(segment, 0) + 1

        # 构建统计结果
        stats = {
            'total_count': total_count,
            'categories': dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)),
            'brands': dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)),
            'segments': dict(sorted(segments.items(), key=lambda x: x[1], reverse=True)),
        }

        # 价格统计
        if prices:
            stats['price'] = {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices),
                'total': sum(prices)
            }

        if unit_prices:
            stats['unit_price'] = {
                'min': min(unit_prices),
                'max': max(unit_prices),
                'avg': sum(unit_prices) / len(unit_prices)
            }

        # 收入统计
        if revenues:
            stats['revenue'] = {
                'min': min(revenues),
                'max': max(revenues),
                'total': sum(revenues),
                'avg': sum(revenues) / len(volumes) if volumes else 0
            }

        # 销量统计
        if volumes:
            stats['volume'] = {
                'min': min(volumes) if volumes else 0,
                'max': max(volumes) if volumes else 0,
                'total': sum(volumes) if volumes else 0,
                'avg': sum(volumes) / len(volumes) if volumes else 0
            }

        return stats
