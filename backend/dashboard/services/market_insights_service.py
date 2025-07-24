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
                past_year_volume,
                past_year_revenue
            ''')
            
            # Apply base filters and combined filtering (ASIN + category)
            query = self._apply_base_filters(query)
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            if not result.data:
                logger.warning(f"No product data found for project {self.project_id}")
                return self._get_empty_response()
            
            logger.info(f"🔍 Found {len(result.data)} products for project {self.project_id}")
            
            # 第三步：获取segment assignments
            segment_assignments = self._get_segment_assignments()
            
            logger.info(f"📊 Segment assignments loaded: {len(segment_assignments)} products mapped")
            
            # 第四步：按segment和category聚合数据
            segment_data = self._aggregate_by_segment_category(result.data, segment_assignments, project_segments)
            
            # 第五步：格式化为API期望的格式
            return self._format_market_response(segment_data, project_segments)
            
        except Exception as e:
            logger.error(f"Error in MarketInsightsService.get_data(): {e}", exc_info=True)
            return self._get_empty_response()
    
    def _get_segment_assignments(self) -> Dict[str, str]:
        """获取项目的segment分配（platform_id到segment_name的映射）
        
        首先尝试使用原项目ID，如果找不到数据，再尝试哈希ID方案。
        
        Returns:
            Dict mapping platform_id to segment_name
        """
        try:
            # 方案1: 直接使用原项目ID（新格式）
            direct_assignments = self._get_segment_assignments_direct()
            if direct_assignments:
                logger.info(f"Found segment assignments using direct project ID: {len(direct_assignments)} mappings")
                return direct_assignments
            
            # 方案2: 使用哈希ID方案（旧格式）
            hashed_assignments = self._get_segment_assignments_shared()
            if hashed_assignments:
                logger.info(f"Found segment assignments using hashed project IDs: {len(hashed_assignments)} mappings")
                return hashed_assignments
            
            logger.warning(f"No segment assignments found for project {self.project_id}")
            return {}
            
        except Exception as e:
            logger.error(f"Error getting segment assignments: {e}")
            return {}
    
    def _get_segment_assignments_direct(self) -> Dict[str, str]:
        """使用原项目ID直接查找segment分配（新格式）
        
        Returns:
            Dict mapping platform_id to segment_name
        """
        try:
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
            
            # 查询segment assignments（使用原项目ID和wide_table_id）
            wide_table_ids = list(platform_to_wide_id.values())
            assignments_result = self.supabase.table('product_segment_assignments')\
                .select('product_id, segment_name')\
                .eq('project_id', self.project_id)\
                .in_('product_id', wide_table_ids)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if not assignments_result.data:
                logger.info(f"No segment assignments found using direct project ID: {self.project_id}")
                return {}
            
            # 建立wide_table_id到segment的映射
            wide_id_to_segment = {item['product_id']: item['segment_name'] for item in assignments_result.data}
            
            # 转换为platform_id到segment的映射
            platform_to_segment = {}
            for platform_id, wide_id in platform_to_wide_id.items():
                if wide_id in wide_id_to_segment:
                    platform_to_segment[platform_id] = wide_id_to_segment[wide_id]
            
            logger.info(f"📋 Direct segment assignments: {len(platform_to_segment)} products mapped")
            return platform_to_segment
            
        except Exception as e:
            logger.error(f"Error getting direct segment assignments: {e}")
            return {}
    
    def _aggregate_by_segment_category(self, products: List[Dict[str, Any]], 
                                     segment_assignments: Dict[str, str], 
                                     project_segments: List[str]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """按segment和category聚合数据"""
        
        # 初始化数据结构：segment -> category -> {revenue, volume, product_count}
        segment_data = {}
        for segment in project_segments:
            segment_data[segment] = {}
        
        for product in products:
            platform_id = product.get('platform_id')
            category = product.get('category', 'Unknown Category')
            
            # 获取product的segment
            segment = segment_assignments.get(platform_id)
            
            if not segment or segment not in project_segments:
                continue  # 跳过不在项目segments中的产品
            
            # 初始化category数据
            if category not in segment_data[segment]:
                segment_data[segment][category] = {
                    'revenue': 0,
                    'volume': 0,
                    'product_count': 0
                }
            
            # 聚合数据
            segment_data[segment][category]['revenue'] += product.get('past_year_revenue', 0) or 0
            segment_data[segment][category]['volume'] += product.get('past_year_volume', 0) or 0
            segment_data[segment][category]['product_count'] += 1
        
        return segment_data
    
    def _format_market_response(self, segment_data: Dict[str, Dict[str, Dict[str, Any]]], 
                        project_segments: List[str]) -> Dict[str, Any]:
        """格式化响应数据，返回真实的segment数据而不是强制的两分法
        
        新版本：返回真实的segment结构，支持动态数量的segments
        """
        # 为每个segment创建汇总数据
        segment_summaries = {}
        
        for segment_name, categories in segment_data.items():
            if not categories:
                continue
                
            # 计算该segment的汇总数据
            total_revenue = sum(item.get('revenue', 0) for item in categories.values())
            total_volume = sum(item.get('volume', 0) for item in categories.values()) 
            total_products = sum(item.get('product_count', 0) for item in categories.values())
            
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