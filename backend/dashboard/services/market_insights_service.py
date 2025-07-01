"""Market insights service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class MarketInsightsService(BaseDashboardService):
    """Service for market insights data.
    
    通用化版本：动态处理项目的所有segment类型，不再硬编码Dimmer/Switch分类。
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get market insights data with ASIN filtering.
        
        Returns data in dynamic segment format based on project's actual segments.
        """
        try:
            # 第一步：获取项目的所有segment类型
            project_segments = self.get_project_segments()
            
            if not project_segments:
                logger.warning(f"No segments found for project {self.project_id}")
                return self._get_empty_response()
            
            logger.info(f"📊 Found {len(project_segments)} segments for project {self.project_id}: {project_segments}")
            
            # 第二步：获取项目的产品数据（使用ASIN过滤）
            query = self._get_base_product_table().select('''
                platform_id,
                category,
                price_usd,
                monthly_sales_volume,
                estimated_revenue
            ''')
            
            # Apply base filters and ASIN filtering
            query = self._apply_base_filters(query)
            query = self._apply_asin_filter(query)
            
            result = query.execute()
            
            if not result.data:
                logger.warning(f"No product data found for project {self.project_id}")
                return self._get_empty_response()
            
            logger.info(f"🔍 Found {len(result.data)} products for project {self.project_id}")
            
            # 第三步：获取segment assignments
            segment_assignments = self._get_segment_assignments()
            
            if not segment_assignments:
                logger.warning(f"No segment assignments found for project {self.project_id}")
                return self._get_empty_response()
            
            # 第四步：将产品数据按segment分组和聚合
            segment_data = self._aggregate_data_by_segments(result.data, segment_assignments, project_segments)
            
            # 第五步：生成通用化的响应格式
            response = self._format_response(segment_data, project_segments)
            
            logger.info(f"📈 Market insights completed: {len(segment_data)} segments processed")
            return response
            
        except Exception as e:
            logger.error(f"Error in market insights for project {self.project_id}: {e}")
            raise
    
    def _get_segment_assignments(self) -> Dict[str, str]:
        """获取项目的segment分配（platform_id到segment_name的映射）
        
        Returns:
            Dict mapping platform_id to segment_name
        """
        try:
            # 先获取项目的ASINs
            if not self.project_asins:
                return {}
            
            # 查询这些ASINs在product_wide_table中的记录，获取wide_table_id
            wide_table_result = self.supabase.table('product_wide_table')\
                .select('id, platform_id')\
                .in_('platform_id', self.project_asins)\
                .execute()
            
            if not wide_table_result.data:
                logger.warning(f"No product_wide_table records found for project ASINs")
                return {}
            
            # 建立platform_id到wide_table_id的映射
            platform_to_wide_id = {item['platform_id']: item['id'] for item in wide_table_result.data}
            
            # 查询segment assignments（使用wide_table_id作为product_id）
            wide_table_ids = list(platform_to_wide_id.values())
            assignments_result = self.supabase.table('product_segment_assignments')\
                .select('product_id, segment_name')\
                .eq('project_id', self.project_id)\
                .in_('product_id', wide_table_ids)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if not assignments_result.data:
                logger.warning(f"No segment assignments found for project products")
                return {}
            
            # 建立wide_table_id到segment的映射
            wide_id_to_segment = {item['product_id']: item['segment_name'] for item in assignments_result.data}
            
            # 转换为platform_id到segment的映射
            platform_to_segment = {}
            for platform_id, wide_id in platform_to_wide_id.items():
                if wide_id in wide_id_to_segment:
                    platform_to_segment[platform_id] = wide_id_to_segment[wide_id]
            
            logger.info(f"📋 Segment assignments: {len(platform_to_segment)} products mapped")
            return platform_to_segment
            
        except Exception as e:
            logger.error(f"Error getting segment assignments: {e}")
            return {}
    
    def _aggregate_data_by_segments(self, products: List[Dict[str, Any]], 
                                  segment_assignments: Dict[str, str], 
                                  project_segments: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """按segment聚合产品数据"""
        
        # 初始化segment数据结构
        segment_data = {segment: {} for segment in project_segments}
        
        for product in products:
            platform_id = product.get('platform_id')
            segment = segment_assignments.get(platform_id)
            category = product.get('category', 'Unknown')
            
            if not segment or segment not in segment_data:
                continue
            
            # 为每个segment内的category创建聚合数据
            if category not in segment_data[segment]:
                segment_data[segment][category] = {
                    'segment': f"{segment} - {category}",
                    'revenue': 0,
                    'volume': 0,
                    'products': 0
                }
            
            # 聚合数据
            segment_data[segment][category]['revenue'] += product.get('estimated_revenue', 0) or 0
            segment_data[segment][category]['volume'] += product.get('monthly_sales_volume', 0) or 0
            segment_data[segment][category]['products'] += 1
        
        # 转换为列表格式并排序
        formatted_segment_data = {}
        for segment, categories in segment_data.items():
            segment_list = list(categories.values())
            segment_list.sort(key=lambda x: x['revenue'], reverse=True)
            formatted_segment_data[segment] = segment_list
        
        return formatted_segment_data
    
    def _format_response(self, segment_data: Dict[str, List[Dict[str, Any]]], 
                        project_segments: List[str]) -> Dict[str, Any]:
        """格式化响应数据，返回真实的segment数据而不是强制的两分法
        
        新版本：返回真实的segment结构，支持动态数量的segments
        """
        # 为每个segment创建汇总数据
        segment_summaries = {}
        
        for segment_name, segment_items in segment_data.items():
            if not segment_items:
                continue
                
            # 计算该segment的汇总数据
            total_revenue = sum(item.get('revenue', 0) for item in segment_items)
            total_volume = sum(item.get('volume', 0) for item in segment_items) 
            total_products = sum(item.get('products', 0) for item in segment_items)
            
            segment_summaries[segment_name] = {
                'segment': segment_name,
                'revenue': total_revenue,
                'volume': total_volume,
                'products': total_products
            }
        
        # 转换为列表并按收入排序
        segment_list = list(segment_summaries.values())
        segment_list.sort(key=lambda x: x['revenue'], reverse=True)
        
        # 新格式：返回真实的segments
        return {
            'segmentRevenue': {
                'segments': segment_list,
                'segmentNames': project_segments,
                # 为了兼容老的前端组件，也提供旧格式（但使用真实数据）
                'dimmerSwitches': segment_list[:2] if len(segment_list) >= 2 else segment_list,
                'lightSwitches': segment_list[2:] if len(segment_list) > 2 else []
            }
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空的响应格式"""
        return {
            'segmentRevenue': {
                'dimmerSwitches': [],
                'lightSwitches': []
            }
        } 