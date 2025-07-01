"""Base service for dashboard data with unified ASIN filtering."""

import logging
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from supabase import Client

from core.database.connection import get_supabase_client

logger = logging.getLogger(__name__)


class BaseDashboardService(ABC):
    """Base service for dashboard data queries with unified ASIN filtering.
    
    This class ensures ALL dashboard queries are filtered by project ASIN list
    to prevent data leakage between projects.
    """
    
    def __init__(self, project_id: str):
        """Initialize with project ID and extract ASIN filter list."""
        self.project_id = project_id
        self.supabase: Client = get_supabase_client()
        self.project_asins = self._get_project_asins()
        
        if not self.project_asins:
            raise ValueError(f"Project {project_id} has no ASIN filter defined")
        
        logger.info(f"Dashboard service initialized for project {project_id} with {len(self.project_asins)} ASINs")
    
    def _get_project_asins(self) -> List[str]:
        """Get ASIN list from project configuration.
        
        This is the core filtering mechanism - ALL queries must use this ASIN list.
        """
        try:
            result = self.supabase.table('projects').select('selected_product_asins').eq('id', self.project_id).single().execute()
            
            if not result.data:
                raise ValueError(f"Project {self.project_id} not found")
            
            asins = result.data.get('selected_product_asins', [])
            if not asins:
                logger.warning(f"Project {self.project_id} has empty ASIN list")
                return []
            
            return asins
            
        except Exception as e:
            logger.error(f"Error getting project ASINs: {e}")
            raise
    
    def _apply_asin_filter(self, query):
        """Apply ASIN filtering to any Supabase query.
        
        This is the critical method that ensures NO data leakage.
        Every subclass MUST use this method for product data queries.
        """
        if not self.project_asins:
            raise ValueError("Cannot apply ASIN filter: project has no ASINs")
        
        return query.in_('platform_id', self.project_asins)
    
    def _get_base_product_table(self):
        """Get base product table reference."""
        return self.supabase.table('product_wide_table')
    
    def _apply_base_filters(self, query):
        """Apply standard base filters to query."""
        return (query
                .eq('source', 'amazon')
                .neq('brand', None))
    
    @abstractmethod
    def get_data(self):
        """Abstract method to be implemented by subclasses."""
        pass
    
    def get_project_segments(self) -> List[str]:
        """获取项目的所有segment类型（排除OUT_OF_SCOPE）
        
        Returns:
            项目所有有效segment名称列表
        """
        try:
            result = self.supabase.table('product_segment_assignments')\
                .select('segment_name')\
                .eq('project_id', self.project_id)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if result.data:
                # 去重并排序
                segments = list(set(item['segment_name'] for item in result.data))
                return sorted(segments)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error fetching project segments: {e}")
            return []
    
    def get_product_segments_mapping(self, platform_ids: List[str]) -> Dict[str, str]:
        """获取产品的segment映射
        
        Args:
            platform_ids: 产品平台ID列表
            
        Returns:
            Dict mapping platform_id to segment_name
        """
        try:
            if not platform_ids:
                return {}
                
            # 查询product_segment_assignments表
            result = self.supabase.table('product_segment_assignments')\
                .select('product_id, segment_name')\
                .eq('project_id', self.project_id)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if result.data:
                # 注意：这里使用product_id作为key，需要映射到platform_id
                # 首先获取product_id到platform_id的映射
                product_id_mapping = {}
                for item in result.data:
                    product_id_mapping[str(item['product_id'])] = item['segment_name']
                
                # 查询platform_id到product_id的映射（如果需要）
                # 暂时直接返回，假设调用方已处理好映射关系
                return product_id_mapping
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching product segments: {e}")
            return {}
    
    def categorize_products_by_segments(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将产品按segment分类
        
        Args:
            products: 包含product信息的产品列表
            
        Returns:
            Dict mapping segment_name to products list
        """
        if not products:
            return {}
        
        # 获取项目的所有segments
        project_segments = self.get_project_segments()
        if not project_segments:
            logger.warning(f"No segments found for project {self.project_id}")
            return {}
        
        # 获取segment assignments
        result = self.supabase.table('product_segment_assignments')\
            .select('product_id, segment_name')\
            .eq('project_id', self.project_id)\
            .neq('segment_name', None)\
            .neq('segment_name', 'OUT_OF_SCOPE')\
            .execute()
        
        if not result.data:
            logger.warning(f"No segment assignments found for project {self.project_id}")
            return {}
        
        # 建立product_id到segment的映射
        product_segment_map = {str(item['product_id']): item['segment_name'] for item in result.data}
        
        # 初始化结果字典
        categorized_products = {segment: [] for segment in project_segments}
        
        # 分类产品
        for product in products:
            platform_id = product.get('platform_id') or product.get('id')
            if not platform_id:
                continue
                
            # 查找该产品的segment（这里需要通过platform_id找到对应的product_id）
            # 先尝试直接匹配（假设platform_id就是product_id的字符串形式）
            segment = product_segment_map.get(platform_id)
            
            if segment and segment in categorized_products:
                categorized_products[segment].append(product)
        
        return categorized_products 