"""Brand analysis service for dashboard."""

import logging
from typing import List, Dict, Any
from collections import defaultdict

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class BrandAnalysisService(BaseDashboardService):
    """Service for brand analysis data.
    
    通用化版本：动态处理项目的所有segment类型，支持任意数量的segments。
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get brand analysis data with dynamic segment support."""
        try:
            # 获取项目segments
            project_segments = self.get_project_segments()
            
            if not project_segments:
                logger.warning(f"No segments found for project {self.project_id}")
                return self._get_empty_response()
            
            logger.info(f"📊 Processing {len(project_segments)} segments: {project_segments}")
            
            # 查询品牌数据
            query = self._get_base_product_table().select('''
                platform_id,
                brand,
                category,
                estimated_revenue,
                monthly_sales_volume
            ''')
            
            # Apply filters
            query = self._apply_base_filters(query)
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            if not result.data:
                logger.warning(f"No brand data found for project {self.project_id}")
                return self._get_empty_response()
            
            # 获取segment assignments
            segment_assignments = self._get_segment_assignments()
            
            # 按品牌和segment聚合数据
            brand_segment_data = self._aggregate_brand_data(result.data, segment_assignments, project_segments)
            
            # 格式化响应
            response = self._format_brand_response(brand_segment_data, project_segments)
            
            logger.info(f"📈 Brand analysis completed: {len(brand_segment_data)} brands processed")
            return response
            
        except Exception as e:
            logger.error(f"Error in brand analysis for project {self.project_id}: {e}")
            raise
    
    def _get_segment_assignments(self) -> Dict[str, str]:
        """获取segment分配（platform_id到segment_name的映射）"""
        try:
            if not self.project_asins:
                return {}
            
            # 查询ASINs在product_wide_table中的记录
            wide_table_result = self.supabase.table('product_wide_table')\
                .select('id, platform_id')\
                .in_('platform_id', self.project_asins)\
                .execute()
            
            if not wide_table_result.data:
                return {}
            
            # 建立映射
            platform_to_wide_id = {item['platform_id']: item['id'] for item in wide_table_result.data}
            
            # 查询segment assignments
            wide_table_ids = list(platform_to_wide_id.values())
            assignments_result = self.supabase.table('product_segment_assignments')\
                .select('product_id, segment_name')\
                .eq('project_id', self.project_id)\
                .in_('product_id', wide_table_ids)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if not assignments_result.data:
                return {}
            
            # 建立映射
            wide_id_to_segment = {item['product_id']: item['segment_name'] for item in assignments_result.data}
            
            # 转换为platform_id到segment的映射
            platform_to_segment = {}
            for platform_id, wide_id in platform_to_wide_id.items():
                if wide_id in wide_id_to_segment:
                    platform_to_segment[platform_id] = wide_id_to_segment[wide_id]
            
            return platform_to_segment
            
        except Exception as e:
            logger.error(f"Error getting segment assignments: {e}")
            return {}
    
    def _aggregate_brand_data(self, products: List[Dict[str, Any]], 
                            segment_assignments: Dict[str, str], 
                            project_segments: List[str]) -> Dict[str, Dict[str, Any]]:
        """按品牌和segment聚合数据"""
        
        brand_data = defaultdict(lambda: {segment: {'revenue': 0, 'volume': 0} for segment in project_segments})
        
        for product in products:
            brand = product.get('brand')
            platform_id = product.get('platform_id')
            
            if not brand or not platform_id:
                continue
            
            segment = segment_assignments.get(platform_id)
            
            if not segment or segment not in project_segments:
                continue
            
            # 聚合数据
            brand_data[brand][segment]['revenue'] += product.get('estimated_revenue', 0) or 0
            brand_data[brand][segment]['volume'] += product.get('monthly_sales_volume', 0) or 0
        
        return dict(brand_data)
    
    def _format_brand_response(self, brand_data: Dict[str, Dict[str, Any]], 
                             project_segments: List[str]) -> Dict[str, Any]:
        """格式化品牌分析响应数据
        
        新格式支持动态segments：
        {
            "brandCategoryRevenue": [
                {
                    "brand": "COSORI",
                    "segments": {
                        "Compact Single Basket Air Fryers": {"revenue": 1500000, "volume": 2000},
                        "Dual Basket Air Fryers": {"revenue": 500000, "volume": 500}
                    },
                    "dimmerRevenue": 1500000,  # 为了向后兼容，映射到最大的segment
                    "switchRevenue": 500000,   # 映射到第二大的segment
                    "dimmerVolume": 2000,
                    "switchVolume": 500
                }
            ],
            "segmentNames": ["Compact Single Basket Air Fryers", "Dual Basket Air Fryers", ...],
            "segmentColors": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
        }
        """
        
        # 定义颜色配色方案
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"]
        
        formatted_brands = []
        
        for brand, segments in brand_data.items():
            # 计算每个segment的总收入和销量
            segment_totals = []
            for segment in project_segments:
                segment_data = segments.get(segment, {'revenue': 0, 'volume': 0})
                segment_totals.append({
                    'segment': segment,
                    'revenue': segment_data['revenue'],
                    'volume': segment_data['volume']
                })
            
            # 按收入排序
            segment_totals.sort(key=lambda x: x['revenue'], reverse=True)
            
            # 为了向后兼容，将前两个segment映射到dimmer/switch字段
            dimmer_data = segment_totals[0] if len(segment_totals) > 0 else {'revenue': 0, 'volume': 0}
            switch_data = segment_totals[1] if len(segment_totals) > 1 else {'revenue': 0, 'volume': 0}
            
            brand_entry = {
                'brand': brand,
                'segments': {item['segment']: {'revenue': item['revenue'], 'volume': item['volume']} 
                           for item in segment_totals},
                'dimmerRevenue': dimmer_data['revenue'],
                'switchRevenue': switch_data['revenue'],
                'dimmerVolume': dimmer_data['volume'],
                'switchVolume': switch_data['volume']
            }
            
            formatted_brands.append(brand_entry)
        
        # 按总收入排序
        formatted_brands.sort(key=lambda x: x['dimmerRevenue'] + x['switchRevenue'], reverse=True)
        
        return {
            'brandCategoryRevenue': formatted_brands,
            'segmentNames': project_segments,
            'segmentColors': colors[:len(project_segments)]
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空的响应格式"""
        return {
            'brandCategoryRevenue': [],
            'segmentNames': [],
            'segmentColors': []
        } 