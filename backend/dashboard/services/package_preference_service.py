"""Package preference service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class PackagePreferenceService(BaseDashboardService):
    """Service for package preference data.
    
    获取项目扩展数据中的package_type字段进行分析。
    """
    
    def __init__(self, project_id: str):
        """Initialize with project ID and default metric type."""
        super().__init__(project_id)
        self.metric_type = "revenue"  # Default metric type
    
    def set_metric_type(self, metric_type: str):
        """Set the metric type for calculations."""
        if metric_type not in ["revenue", "count"]:
            raise ValueError(f"Invalid metric type: {metric_type}. Must be 'revenue' or 'count'")
        self.metric_type = metric_type
        logger.info(f"Metric type set to: {metric_type}")
    
    def _apply_brand_filter(self, query):
        """Apply brand filtering to any Supabase query if brand filters are set."""
        if self.filters.brands:
            query = query.in_('brand', self.filters.brands)
            logger.info(f"Applied brand filter: {self.filters.brands}")
        return query
    
    def _apply_segment_filter(self, query):
        """Apply segment filtering to any Supabase query if segment filters are set."""
        if self.filters.segments:
            query = query.in_('segment', self.filters.segments)
            logger.info(f"Applied segment filter: {self.filters.segments}")
        return query
    
    def _apply_extend_fields_filter_to_extend_data(self, query):
        """Apply extend fields filtering to project_extend_data table if extend fields filters are set."""
        if not self.filters.extend_fields:
            return query
        
        try:
            # 获取字段定义以识别默认值
            field_definitions = self.get_project_extend_fields()
            field_defaults = {}
            for field_def in field_definitions:
                field_name = field_def['field_name']
                filter_options = field_def.get('filter_options', {})
                default_value = filter_options.get('default') if filter_options else None
                field_defaults[field_name] = default_value
            
            # 过滤掉默认值，只保留需要过滤的字段
            active_filters = {}
            for field_name, field_value in self.filters.extend_fields.items():
                if field_value is not None:
                    default_value = field_defaults.get(field_name)
                    
                    # 检查是否为默认值
                    is_default = False
                    if default_value is not None:
                        # 处理不同类型的默认值比较
                        if isinstance(default_value, bool) and isinstance(field_value, bool):
                            is_default = (field_value == default_value)
                        elif isinstance(default_value, bool) and isinstance(field_value, str):
                            # 处理前端传递的字符串boolean值
                            is_default = (field_value.lower() == str(default_value).lower())
                        else:
                            is_default = (str(field_value) == str(default_value))
                    
                    # 只有非默认值才加入过滤条件
                    if not is_default:
                        active_filters[field_name] = field_value
            
            # 如果没有需要过滤的字段（都是默认值），直接返回原查询
            if not active_filters:
                logger.info(f"All extend fields are default values, skipping extend fields filter: {self.filters.extend_fields}")
                return query
            
            # 应用extend_fields过滤到project_extend_data表
            for field_name, field_value in active_filters.items():
                # 处理布尔值：JavaScript的boolean需要转换为JSON中存储的字符串格式
                if isinstance(field_value, bool):
                    field_value = str(field_value).lower()  # true/false
                elif field_value == 'true':
                    field_value = 'true'
                elif field_value == 'false':
                    field_value = 'false'
                
                # 使用正确的JSON文本提取语法 ->> 而不是 ->
                query = query.eq(f'extend->>{field_name}', field_value)
                logger.info(f"Applied extend field filter to project_extend_data: {field_name} = {field_value}")
                
        except Exception as e:
            logger.error(f"Error applying extend fields filter to project_extend_data: {e}")
            # 出错时返回空结果
            query = query.eq('id', -1)
        
        return query
    
    def get_data(self) -> Dict[str, Any]:
        """Get package preference data from project_extend_data table."""
        try:
            # 第一步：从project_extend_data表获取包装类型数据并应用extend fields过滤
            extend_data_query = self.supabase.table('project_extend_data')\
                .select('asins, extend')\
                .eq('project_id', self.project_id)
            
            # 应用extend fields过滤到project_extend_data表
            extend_data_query = self._apply_extend_fields_filter_to_extend_data(extend_data_query)
            
            extend_result = extend_data_query.execute()
            
            if not extend_result.data:
                logger.warning(f"No extend data found for project {self.project_id}")
                return self._get_empty_response()
            
            # 第二步：提取包装类型数据并聚合
            package_type_data = {}
            valid_asins = []
            
            for row in extend_result.data:
                asin = row.get('asins')
                extend = row.get('extend', {})
                package_type = extend.get('package_type')
                
                if package_type and asin:
                    # 将Multiple-X格式统一为Multiple
                    if package_type.startswith('Multiple-'):
                        package_type = 'Multiple'
                    
                    if package_type not in package_type_data:
                        package_type_data[package_type] = []
                    package_type_data[package_type].append(asin)
                    valid_asins.append(asin)
            
            if not valid_asins:
                logger.warning(f"No valid package type data found for project {self.project_id}")
                return self._get_empty_response()
            
            logger.info(f"📊 Found {len(valid_asins)} products with package type data")
            
            # 第三步：获取产品收入数据并应用筛选器
            product_revenue_query = self.supabase.table('product_wide_table')\
                .select('platform_id, estimated_revenue, category, brand')\
                .in_('platform_id', valid_asins)\
                .not_.is_('estimated_revenue', 'null')
            
            # 应用筛选器（但不包括extend fields过滤，因为已在第一步应用）
            product_revenue_query = self._apply_asin_filter(product_revenue_query)
            product_revenue_query = self._apply_category_filter(product_revenue_query)
            product_revenue_query = self._apply_brand_filter(product_revenue_query)
            # Note: segment filter is not applied as product_wide_table doesn't have segment column
            # Note: extend fields filter is not applied here as it was already applied in step 1
            
            product_result = product_revenue_query.execute()
            
            if not product_result.data:
                logger.warning(f"No product revenue data found for project {self.project_id} after applying filters")
                return self._get_empty_response()
            
            # 第四步：建立ASIN到收入和category的映射
            asin_to_data = {}
            for product in product_result.data:
                asin = product['platform_id']
                revenue = product.get('estimated_revenue', 0)
                category = product.get('category', 'Unknown')
                brand = product.get('brand', 'Unknown')
                
                if revenue is not None:
                    asin_to_data[asin] = {
                        'revenue': float(revenue),
                        'category': category,
                        'brand': brand
                    }
                else:
                    asin_to_data[asin] = {
                        'revenue': 0.0,
                        'category': category,
                        'brand': brand
                    }
            
            # 第五步：按category分组计算每个包装类型的收入
            category_package_data = {}
            for package_type, asins in package_type_data.items():
                for asin in asins:
                    if asin in asin_to_data:
                        product_data = asin_to_data[asin]
                        category = product_data['category']
                        
                        if category not in category_package_data:
                            category_package_data[category] = {}
                        
                        if package_type not in category_package_data[category]:
                            category_package_data[category][package_type] = {
                                'total_revenue': 0,
                                'count': 0,
                                'asins': []
                            }
                        
                        category_package_data[category][package_type]['total_revenue'] += product_data['revenue']
                        category_package_data[category][package_type]['count'] += 1
                        category_package_data[category][package_type]['asins'].append(asin)
            
            logger.info(f"📈 Found {len(category_package_data)} categories with package type data")
            
            # 格式化响应
            response = self._format_package_response_by_category(category_package_data)
            
            logger.info(f"📦 Package preference analysis completed")
            return response
            
        except Exception as e:
            logger.error(f"Error in package preference analysis for project {self.project_id}: {e}")
            raise
    
    def _format_package_response_by_category(self, category_package_data: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """格式化包装偏好响应数据为多category饼图格式"""
        
        if not category_package_data:
            return self._get_empty_response()
        
        # 生成按category分组的饼图数据
        segment_distributions = {}
        category_names = []
        
        # 总体饼图数据
        overall_package_data = {}
        
        for category, package_types in category_package_data.items():
            if not package_types:
                continue
            
            category_names.append(category)
            
            # 计算该category的总值
            if self.metric_type == "count":
                total_metric_value = sum(item['count'] for item in package_types.values())
            else:  # revenue
                total_metric_value = sum(item['total_revenue'] for item in package_types.values())
            
            # 生成该category的饼图数据
            category_pie_data = []
            for package_type, data in package_types.items():
                # 根据metric_type计算百分比
                if self.metric_type == "count":
                    percentage = (data['count'] / total_metric_value * 100) if total_metric_value > 0 else 0
                else:  # revenue
                    percentage = (data['total_revenue'] / total_metric_value * 100) if total_metric_value > 0 else 0
                
                category_pie_data.append({
                    'packSize': package_type,
                    'name': package_type,
                    'value': data['total_revenue'],
                    'salesRevenue': data['total_revenue'],
                    'count': data['count'],
                    'percentage': percentage
                })
                
                # 累计到总体数据
                if package_type not in overall_package_data:
                    overall_package_data[package_type] = {
                        'total_revenue': 0,
                        'count': 0
                    }
                overall_package_data[package_type]['total_revenue'] += data['total_revenue']
                overall_package_data[package_type]['count'] += data['count']
            
            # 按指标排序
            if self.metric_type == "count":
                category_pie_data.sort(key=lambda x: x['count'], reverse=True)
            else:  # revenue
                category_pie_data.sort(key=lambda x: x['value'], reverse=True)
            
            segment_distributions[category] = category_pie_data
        
        # 生成总体饼图数据
        if overall_package_data:
            if self.metric_type == "count":
                total_metric_value = sum(item['count'] for item in overall_package_data.values())
            else:  # revenue
                total_metric_value = sum(item['total_revenue'] for item in overall_package_data.values())
            
            overall_pie_data = []
            for package_type, data in overall_package_data.items():
                if self.metric_type == "count":
                    percentage = (data['count'] / total_metric_value * 100) if total_metric_value > 0 else 0
                else:  # revenue
                    percentage = (data['total_revenue'] / total_metric_value * 100) if total_metric_value > 0 else 0
                
                overall_pie_data.append({
                    'packSize': package_type,
                    'name': package_type,
                    'value': data['total_revenue'],
                    'salesRevenue': data['total_revenue'],
                    'count': data['count'],
                    'percentage': percentage
                })
            
            # 按指标排序
            if self.metric_type == "count":
                overall_pie_data.sort(key=lambda x: x['count'], reverse=True)
            else:  # revenue
                overall_pie_data.sort(key=lambda x: x['value'], reverse=True)
        else:
            overall_pie_data = []
        
        # 生成颜色
        segment_colors = ['#4ECDC4', '#FF6B6B', '#45B7D1', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA']
        
        return {
            'sameProductComparison': [],
            'packageDistribution': overall_pie_data,
            'segmentDistributions': segment_distributions,
            'segmentNames': category_names,
            'segmentColors': segment_colors[:len(category_names)],
            'dimmerSwitches': [],
            'lightSwitches': []
        }
    
    def _format_package_response(self, package_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化包装偏好响应数据为单一饼图格式"""
        
        if not package_data:
            return self._get_empty_response()
        
        # 根据metric_type决定排序和计算基准
        if self.metric_type == "count":
            package_data.sort(key=lambda x: x['count'], reverse=True)
            total_metric_value = sum(item['count'] for item in package_data)
        else:  # revenue
            package_data.sort(key=lambda x: x['total_revenue'], reverse=True)
            total_metric_value = sum(item['total_revenue'] for item in package_data)
        
        # 生成饼图数据
        pie_chart_data = []
        for item in package_data:
            # 根据metric_type计算百分比
            if self.metric_type == "count":
                percentage = (item['count'] / total_metric_value * 100) if total_metric_value > 0 else 0
            else:  # revenue
                percentage = (item['total_revenue'] / total_metric_value * 100) if total_metric_value > 0 else 0
            
            pie_chart_data.append({
                'packSize': item['package_type'],  # 保持原有字段名兼容性
                'name': item['package_type'],      # 新字段名
                'value': item['total_revenue'],    # 保持value字段为收入，前端会根据需要选择
                'salesRevenue': item['total_revenue'],  # 兼容性
                'count': item['count'],
                'percentage': percentage
            })
        
        # 为了向后兼容，保留原有的数据结构，但使用新的数据
        # 创建一个虚拟的segment叫做"All Products"
        segment_distributions = {
            'All Products': pie_chart_data
        }
        
        return {
            'sameProductComparison': [],  # 暂时不使用
            'packageDistribution': pie_chart_data,
            'segmentDistributions': segment_distributions,
            'segmentNames': ['All Products'],
            'segmentColors': ['#4ECDC4'],
            'dimmerSwitches': [],  # 旧格式兼容
            'lightSwitches': []    # 旧格式兼容
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空的响应格式"""
        return {
            'sameProductComparison': [],
            'packageDistribution': [],
            'segmentDistributions': {},
            'segmentNames': [],
            'segmentColors': [],
            'dimmerSwitches': [],
            'lightSwitches': []
        } 