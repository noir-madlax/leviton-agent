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
    
    def get_data(self) -> Dict[str, Any]:
        """Get package preference data from project_extend_data table."""
        try:
            # 第一步：从project_extend_data表获取包装类型数据
            extend_data_query = self.supabase.table('project_extend_data')\
                .select('asins, extend')\
                .eq('project_id', self.project_id)
            
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
            
            # 第三步：获取产品收入数据
            product_revenue_query = self.supabase.table('product_wide_table')\
                .select('platform_id, estimated_revenue')\
                .in_('platform_id', valid_asins)\
                .not_.is_('estimated_revenue', 'null')
            
            product_result = product_revenue_query.execute()
            
            if not product_result.data:
                logger.warning(f"No product revenue data found for project {self.project_id}")
                return self._get_empty_response()
            
            # 第四步：建立ASIN到收入的映射
            asin_to_revenue = {}
            for product in product_result.data:
                asin = product['platform_id']
                revenue = product.get('estimated_revenue', 0)
                if revenue is not None:
                    asin_to_revenue[asin] = float(revenue)
                else:
                    asin_to_revenue[asin] = 0.0
            
            # 第五步：计算每个包装类型的总收入
            package_revenue_data = []
            for package_type, asins in package_type_data.items():
                total_revenue = sum(asin_to_revenue.get(asin, 0) for asin in asins)
                count = len(asins)
                
                if total_revenue > 0:  # 只包含有收入的包装类型
                    package_revenue_data.append({
                        'package_type': package_type,
                        'total_revenue': total_revenue,
                        'count': count
                    })
            
            logger.info(f"📈 Found {len(package_revenue_data)} package types with revenue data")
            
            # 格式化响应
            response = self._format_package_response(package_revenue_data)
            
            logger.info(f"📦 Package preference analysis completed")
            return response
            
        except Exception as e:
            logger.error(f"Error in package preference analysis for project {self.project_id}: {e}")
            raise
    
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