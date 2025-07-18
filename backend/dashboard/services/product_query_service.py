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
        """构建产品查询，分两步获取数据"""
        # 第一步：获取该项目的所有产品segment分配（包括segment_name为空的情况）
        try:
            segment_assignments = self.supabase.table('product_segment_assignments').select(
                'product_id, segment_name'
            ).eq('project_id', self.project_id).execute()

            # 创建产品ID到segment的映射，处理空值
            # 注意：product_segment_assignments.product_id 关联 product_wide_table.id
            self._segment_map = {}
            project_product_ids = set()

            for assignment in segment_assignments.data or []:
                product_id = assignment.get('product_id')  # 这是 wide 表的 id
                segment_name = assignment.get('segment_name')  # 可能为空
                if product_id:
                    project_product_ids.add(product_id)
                    self._segment_map[product_id] = segment_name  # 保留空值

            logger.info(f"Found {len(project_product_ids)} products in project {self.project_id}")

            if not project_product_ids:
                # 如果项目没有任何产品分配，返回空查询
                logger.warning(f"No products found for project {self.project_id}")
                return self.supabase.table('product_wide_table').select('*').eq('id', -1)

            # 第二步：查询这些产品的详细信息
            # 使用 id 字段进行关联，而不是 platform_id
            query = self.supabase.table('product_wide_table').select(
                'id, platform_id, title, brand, category, '
                'price_usd, unit_price_calculated, estimated_revenue, '
                'monthly_sales_volume, rating, reviews_count, product_url, pack_count'
            ).in_('id', list(project_product_ids))

        except Exception as e:
            logger.error(f"Failed to get segment assignments: {e}")
            # 如果获取segment分配失败，使用原有逻辑
            self._segment_map = {}
            query = self.supabase.table('product_wide_table').select(
                'id, platform_id, title, brand, category, '
                'price_usd, unit_price_calculated, estimated_revenue, '
                'monthly_sales_volume, rating, reviews_count, product_url, pack_count'
            )

        # 应用项目ASIN过滤（安全边界）
        query = self._apply_asin_filter(query)

        # 调试：打印筛选器状态
        logger.info(f"Project filters in _build_product_query: {self.project_filters.to_dict()}")

        # 应用基础项目级筛选器
        query = self._apply_project_filters(query)

        return query

    def _apply_project_filters(self, query):
        """应用项目级筛选器，适配新的segment表结构"""
        if not self.project_filters:
            return query

        filters = self.project_filters

        # 类别筛选
        if filters.categories:
            query = query.in_('category', filters.categories)
            logger.info(f"Applied category filter: {filters.categories}")

        # 品牌筛选
        if filters.brands:
            query = query.in_('brand', filters.brands)
            logger.info(f"Applied brand filter: {filters.brands}")

        # 段筛选 - 使用内存中的segment映射进行筛选
        if filters.segments and hasattr(self, '_segment_map'):
            # 找到匹配指定segment的产品ID，处理空值情况
            filtered_product_ids = []

            for product_id, segment_name in self._segment_map.items():
                # 检查segment_name是否匹配（包括空值处理）
                if segment_name and segment_name in filters.segments:
                    filtered_product_ids.append(product_id)
                elif not segment_name and None in filters.segments:
                    # 如果筛选条件包含None，也包含segment_name为空的产品
                    filtered_product_ids.append(product_id)

            if filtered_product_ids:
                query = query.in_('id', filtered_product_ids)
                logger.info(f"Applied segments filter: {filters.segments}, found {len(filtered_product_ids)} matching products")
            else:
                # 如果没有匹配的产品，返回空结果
                # 使用一个不存在的整数ID，而不是字符串
                query = query.eq('id', -1)
                logger.info(f"Applied segments filter: {filters.segments}, no matching products found")

        # 扩展字段筛选
        if filters.extend_fields:
            for field_name, field_value in filters.extend_fields.items():
                if field_value is not None:
                    query = query.eq(field_name, field_value)
            logger.info(f"Applied extend_fields filter: {filters.extend_fields}")

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
            return query.order('estimated_revenue', desc=True)
        
        sort_field_map = {
            'price': 'price_usd',
            'revenue': 'estimated_revenue',
            'volume': 'monthly_sales_volume',
            'rating': 'rating',
            'reviews_count': 'reviews_count'
        }
        
        field = sort_field_map.get(options.sort_by, 'estimated_revenue')
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
        """处理产品数据，保持与前端期望格式一致"""
        products = []

        for item in raw_data:
            # 安全的数值转换函数
            def safe_float(value, default=0.0):
                if value is None:
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default

            def safe_int(value, default=0):
                if value is None:
                    return default
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            # 从内存中的segment映射获取 segment_name（可能为空）
            # 注意：segment映射使用的是 wide 表的 id，而不是 platform_id
            wide_table_id = item.get('id', '')
            platform_id = item.get('platform_id', '')
            segment_name = None
            if hasattr(self, '_segment_map') and wide_table_id in self._segment_map:
                segment_name = self._segment_map[wide_table_id]  # 可能为None或空字符串

            product = {
                'id': platform_id,  # API返回使用 platform_id 作为产品ID
                'name': item.get('title', ''),
                'brand': item.get('brand', ''),
                'category': item.get('category'),
                'segment': segment_name,  # 使用内存映射的 segment_name
                'price': safe_float(item.get('price_usd')),
                'unitPrice': safe_float(item.get('unit_price_calculated')) or safe_float(item.get('price_usd')),
                'revenue': safe_float(item.get('estimated_revenue')),
                'volume': safe_int(item.get('monthly_sales_volume')),
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
        revenues = safe_float_list(data, 'estimated_revenue')
        volumes = safe_int_list(data, 'monthly_sales_volume')

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
        revenues = safe_float_list(data, 'estimated_revenue')
        volumes = safe_int_list(data, 'monthly_sales_volume')

        # 分类统计
        categories = {}
        brands = {}
        segments = {}

        for item in data:
            category = item.get('category')
            if category:
                categories[category] = categories.get(category, 0) + 1

            brand = item.get('brand')
            if brand:
                brands[brand] = brands.get(brand, 0) + 1

            # 从内存映射中获取 segment_name（处理空值）
            # 注意：segment映射使用的是 wide 表的 id，而不是 platform_id
            wide_table_id = item.get('id', '')
            if hasattr(self, '_segment_map') and wide_table_id in self._segment_map:
                segment = self._segment_map[wide_table_id]
                if segment:  # 只统计非空的segment
                    segments[segment] = segments.get(segment, 0) + 1
                else:
                    # 可选：统计没有segment的产品
                    segments['Unassigned'] = segments.get('Unassigned', 0) + 1

        return {
            'total_count': total_count,
            'price_stats': {
                'sku_price': {
                    'min': min(prices) if prices else 0,
                    'max': max(prices) if prices else 0,
                    'avg': sum(prices) / len(prices) if prices else 0,
                    'count': len(prices)
                },
                'unit_price': {
                    'min': min(unit_prices) if unit_prices else 0,
                    'max': max(unit_prices) if unit_prices else 0,
                    'avg': sum(unit_prices) / len(unit_prices) if unit_prices else 0,
                    'count': len(unit_prices)
                }
            },
            'sales_stats': {
                'revenue': {
                    'min': min(revenues) if revenues else 0,
                    'max': max(revenues) if revenues else 0,
                    'total': sum(revenues) if revenues else 0,
                    'avg': sum(revenues) / len(revenues) if revenues else 0
                },
                'volume': {
                    'min': min(volumes) if volumes else 0,
                    'max': max(volumes) if volumes else 0,
                    'total': sum(volumes) if volumes else 0,
                    'avg': sum(volumes) / len(volumes) if volumes else 0
                }
            },
            'distribution': {
                'categories': dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)),
                'brands': dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)),
                'segments': dict(sorted(segments.items(), key=lambda x: x[1], reverse=True))
            }
        }
