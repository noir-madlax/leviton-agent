"""Base service for dashboard data with unified ASIN filtering."""

import logging
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from supabase import Client

from core.database.connection import get_supabase_client
from core.models.filters import ProjectFilters
from dashboard.services.filter_service import FilterService
from dashboard.charts.base_models import BaseRequestModel

logger = logging.getLogger(__name__)

class FilterConfig:
    """Configuration class for dashboard filters."""
    def __init__(self):
        self.categories: Optional[List[str]] = None
        self.brands: Optional[List[str]] = None  # 改：packaging_types -> brands
        self.segments: Optional[List[str]] = None  # 新增: 产品段筛选
        self.extend_fields: Optional[Dict[str, Any]] = None  # 新增: 扩展字段筛选
    
    def has_filters(self) -> bool:
        """Check if any filters are set."""
        return bool(self.categories or self.brands or self.segments or self.extend_fields)  # 改：packaging_types -> brands

class BaseDashboardService(ABC):
    """Base service for dashboard data queries with unified ASIN filtering.
    
    This class ensures ALL dashboard queries are filtered by project ASIN list
    to prevent data leakage between projects.
    """
    
    def __init__(self, project_id: str):
        """Initialize with project ID and extract ASIN filter list."""
        self.project_id = project_id
        self.supabase: Client = get_supabase_client()
        self.filters = FilterConfig()  # 新增: 统一的筛选配置
        # 保持向后兼容性
        self.category_filters: Optional[List[str]] = None
        self.project_asins = self._get_project_asins()
        
        if not self.project_asins:
            raise ValueError(f"Project {project_id} has no ASIN filter defined")
        
        # 初始化FilterService
        self.filter_service = FilterService(self.supabase, self.project_asins)
        self.project_filters = ProjectFilters.empty()
        
        logger.info(f"Dashboard service initialized for project {project_id} with {len(self.project_asins)} ASINs")
    
    def _get_project_asins(self) -> List[str]:
        """Get ASIN list from project configuration.
        
        This is the core filtering mechanism - ALL queries must use this ASIN list.
        """
        try:
            result = self.supabase.table('projects').select('selected_product_asins').eq('id', self.project_id).single().execute()
            if result.data and result.data.get('selected_product_asins'):
                # 验证 ASIN 列表格式
                asins = result.data['selected_product_asins']
                if not isinstance(asins, list):
                    raise ValueError(f"Invalid ASIN format for project {self.project_id}")
                return asins
            else:
                logger.warning(f"No ASIN filter found for project {self.project_id}")
                return []
        except Exception as e:
            logger.error(f"Error fetching project ASINs: {e}")
            return []
    
    def _apply_asin_filter(self, query):
        """Apply ASIN filtering to any Supabase query.
        
        This is the critical method that ensures NO data leakage.
        Every subclass MUST use this method for product data queries.
        """
        if not self.project_asins:
            raise ValueError("Cannot apply ASIN filter: project has no ASINs")
        
        return query.in_('platform_id', self.project_asins)
    
    def set_category_filters(self, categories: List[str]):
        """Set category filters for additional filtering (deprecated - use set_filters instead)."""
        self.category_filters = categories
        self.filters.categories = categories
        # 同时更新新的筛选器
        self.project_filters.categories = categories
        logger.info(f"Category filters set: {categories}")
    
    def set_filters(self, categories: Optional[List[str]] = None, brands: Optional[List[str]] = None, segments: Optional[List[str]] = None, extend_fields: Optional[Dict[str, Any]] = None):
        """Set multiple filters for additional filtering."""
        if categories is not None:
            self.filters.categories = categories
            self.category_filters = categories  # 保持向后兼容性
            self.project_filters.categories = categories
        if brands is not None:  # 改：packaging_types -> brands
            self.filters.brands = brands
            self.project_filters.brands = brands
        if segments is not None:
            self.filters.segments = segments
            self.project_filters.segments = segments
        if extend_fields is not None:
            self.filters.extend_fields = extend_fields
            self.project_filters.extend_fields = extend_fields
        
        logger.info(f"Filters set - Categories: {categories}, Brands: {brands}, Segments: {segments}, Extend Fields: {extend_fields}")  # 改：Packaging -> Brands
    
    def set_project_filters(self, filters: ProjectFilters):
        """Set project filters using the new filter model."""
        self.project_filters = filters
        # 保持向后兼容性
        self.category_filters = filters.categories
        self.filters.categories = filters.categories
        self.filters.brands = filters.brands
        self.filters.segments = filters.segments
        self.filters.extend_fields = filters.extend_fields
        logger.info(f"Project filters set: {filters.to_dict()}")
    
    def _apply_category_filter(self, query):
        """Apply category filtering to any Supabase query if category filters are set."""
        if self.filters.categories:
            query = query.in_('category', self.filters.categories)
            logger.info(f"Applied category filter: {self.filters.categories}")
        return query
    
    def _apply_filters(self, query):
        """Apply all filters using the new filter service."""
        return self.filter_service.apply_filters(query, self.project_filters)
    
    def _apply_brand_filter(self, query):  # 改：_apply_packaging_filter -> _apply_brand_filter
        """Apply brand filtering to any Supabase query if brand filters are set."""
        if self.filters.brands:  # 改：packaging_types -> brands
            query = query.in_('brand', self.filters.brands)  # 改：packaging_type -> brand
            logger.info(f"Applied brand filter: {self.filters.brands}")
        return query

    def _apply_segments_filter(self, query):
        """Apply product segment filtering to any Supabase query if segment filters are set.
        
        此方法使用product_segment_assignments表来过滤产品，
        使用哈希项目ID方案查找正确的segment assignments。
        """
        if self.filters.segments:
            try:
                # Get the hashed project IDs that were used during segmentation
                hashed_project_ids = self._get_segmentation_hashed_project_ids()
                
                if not hashed_project_ids:
                    logger.warning(f"No segmentation hashes found for segment filter")
                    query = query.eq('id', -1)
                    return query
                
                # 第一步：从product_segment_assignments表获取符合segment条件的product_id
                segment_assignments_result = self.supabase.table('product_segment_assignments')\
                    .select('product_id')\
                    .in_('project_id', hashed_project_ids)\
                    .in_('segment_name', self.filters.segments)\
                    .execute()
                
                if not segment_assignments_result.data:
                    # 如果没有找到符合条件的产品，返回一个永远不匹配的条件
                    query = query.eq('id', -1)
                    logger.info(f"No products found for segment filter: {self.filters.segments}")
                else:
                    # 提取product_id列表
                    product_ids = [item['product_id'] for item in segment_assignments_result.data]
                    # 第二步：使用product_id列表过滤product_wide_table
                    query = query.in_('id', product_ids)
                    logger.info(f"Applied segment filter: {self.filters.segments}, found {len(product_ids)} products")
                    
            except Exception as e:
                logger.error(f"Error applying segment filter: {e}")
                # 出错时返回空结果
                query = query.eq('id', -1)
        
        return query

    def get_project_extend_fields(self) -> List[Dict[str, Any]]:
        """获取项目的扩展字段定义"""
        try:
            result = self.supabase.table('project_extend_fields')\
                .select('field_name, display_name, field_type, filter_options, sort_order')\
                .eq('project_id', self.project_id)\
                .eq('is_active', True)\
                .order('sort_order')\
                .execute()
            
            if result.data:
                logger.info(f"Found {len(result.data)} extend fields for project {self.project_id}")
                return result.data
            else:
                logger.info(f"No extend fields found for project {self.project_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching project extend fields: {e}")
            return []

    def _apply_extend_fields_filter(self, query):
        """Apply extend fields filtering to any Supabase query if extend field filters are set."""
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
            
            # 应用extend_fields过滤
            # 收集所有符合条件的ASINs，每个字段过滤后求交集
            valid_asins_sets = []
            
            for field_name, field_value in active_filters.items():
                field_valid_asins = set()
                
                # 处理数组值：需要为每个值分别查询并合并结果（OR逻辑）
                if isinstance(field_value, list):
                    logger.info(f"Processing array filter for {field_name}: {field_value}")
                    
                    for value in field_value:
                        # 处理布尔值：JavaScript的boolean需要转换为JSON中存储的字符串格式
                        if isinstance(value, bool):
                            value = str(value).lower()  # true/false
                        elif value == 'true':
                            value = 'true'
                        elif value == 'false':
                            value = 'false'
                        
                        # 为每个值查询匹配的ASINs
                        value_query = self.supabase.table('project_extend_data')\
                            .select('asins')\
                            .eq('project_id', self.project_id)\
                            .eq(f'extend->>{field_name}', value)
                        
                        value_result = value_query.execute()
                        if value_result.data:
                            value_asins = {row['asins'] for row in value_result.data}
                            field_valid_asins.update(value_asins)
                            logger.info(f"Found {len(value_asins)} ASINs for {field_name}={value}")
                
                else:
                    # 处理单个值
                    logger.info(f"Processing single value filter for {field_name}: {field_value}")
                    
                    # 处理布尔值：JavaScript的boolean需要转换为JSON中存储的字符串格式
                    if isinstance(field_value, bool):
                        field_value = str(field_value).lower()  # true/false
                    elif field_value == 'true':
                        field_value = 'true'
                    elif field_value == 'false':
                        field_value = 'false'
                    
                    # 查询匹配的ASINs
                    single_query = self.supabase.table('project_extend_data')\
                        .select('asins')\
                        .eq('project_id', self.project_id)\
                        .eq(f'extend->>{field_name}', field_value)
                    
                    single_result = single_query.execute()
                    if single_result.data:
                        field_valid_asins = {row['asins'] for row in single_result.data}
                        logger.info(f"Found {len(field_valid_asins)} ASINs for {field_name}={field_value}")
                
                # 只有当字段有匹配结果时才加入交集计算
                if field_valid_asins:
                    valid_asins_sets.append(field_valid_asins)
                else:
                    # 如果任何字段没有匹配，整个筛选应该返回空结果
                    logger.info(f"No ASINs found for {field_name}, returning empty result")
                    valid_asins_sets = []
                    break
            
            # 计算所有字段的交集（AND逻辑）
            if valid_asins_sets:
                # 从第一个集合开始，与后续集合求交集
                final_valid_asins = valid_asins_sets[0]
                for asin_set in valid_asins_sets[1:]:
                    final_valid_asins = final_valid_asins.intersection(asin_set)
                
                valid_asins = list(final_valid_asins)
                logger.info(f"Final intersection result: {len(valid_asins)} ASINs match all extend field filters")
            else:
                valid_asins = []
            
            # 应用最终的ASIN筛选结果
            if valid_asins:
                query = query.in_('platform_id', valid_asins)
                logger.info(f"Applied extend fields filter: {active_filters}, found {len(valid_asins)} matching ASINs")
            else:
                # 如果没有符合条件的产品，返回空结果
                query = query.eq('id', -1)
                logger.info(f"No products found for extend fields filter: {active_filters}")
                
        except Exception as e:
            logger.error(f"Error applying extend fields filter: {e}")
            # 出错时返回空结果
            query = query.eq('id', -1)
        
        return query
    
    def _apply_combined_filters(self, query):
        """Apply ASIN, category, brand, segments, and extend fields filters to a query."""
        query = self._apply_asin_filter(query)
        query = self._apply_category_filter(query)
        query = self._apply_brand_filter(query)  # 改：_apply_packaging_filter -> _apply_brand_filter
        query = self._apply_segments_filter(query)
        query = self._apply_extend_fields_filter(query)  # 新增：应用扩展字段筛选
        return query

    def execute_filtered_query(self, request: BaseRequestModel) -> List[str]:
        """使用链式过滤器执行查询，返回过滤后的ASIN列表

        Args:
            request: 基础请求模型，包含project_id和filters

        Returns:
            List[str]: 过滤后的ASIN列表

        Raises:
            ValueError: 当project_id为空时
            Exception: 当SQL执行失败时
        """
        try:
            from dashboard.charts.filters import build_filtered_sql

            # 验证project_id
            if not request.project_id:
                raise ValueError("project_id is required")

            # 构建SQL查询
            sql = build_filtered_sql(request.project_id, request.filters)

            logger.info(f"Executing filtered query for project {request.project_id}")
            logger.debug(f"SQL: {sql}")

            # 执行查询
            result = self.supabase.rpc('execute_safe_query', {
                'query_text': sql
            }).execute()

            if result.data is None:
                logger.warning("Query returned None data")
                return []

            # 调试：打印返回的数据结构
            if result.data:
                logger.info(f"Query returned {len(result.data)} rows")
                logger.info(f"First row keys: {list(result.data[0].keys()) if result.data else 'No data'}")
                logger.info(f"First row sample: {result.data[0] if result.data else 'No data'}")
            else:
                logger.info("Query returned empty result")
                return []

            # 提取ASIN列表 - 处理Supabase RPC返回的数据结构
            asins = []
            for row in result.data:
                # Supabase execute_safe_query 返回的数据结构是 {"result": {...}}
                if 'result' in row and isinstance(row['result'], dict):
                    result_data = row['result']
                    if 'platform_id' in result_data:
                        asins.append(result_data['platform_id'])
                    else:
                        logger.error(f"platform_id field not found in result data. Available fields: {list(result_data.keys())}")
                        raise KeyError(f"platform_id field not found in result data. Available fields: {list(result_data.keys())}")
                else:
                    # 如果不是预期的结构，打印调试信息
                    logger.error(f"Unexpected row structure. Row: {row}")
                    raise KeyError(f"Unexpected row structure. Expected 'result' field but got: {list(row.keys())}")

            logger.info(f"Query executed successfully, returned {len(asins)} ASINs")
            return asins

        except Exception as e:
            logger.error(f"Error executing filtered query: {e}")
            raise Exception(f"Failed to execute filtered query: {str(e)}")
    
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
    
    def _get_segmentation_hashed_project_ids(self) -> List[str]:
        """获取用于细分的哈希项目ID列表
        
        During segmentation, products are grouped by categories_flat and each group
        gets a hashed project_id = SHA1(actual_project_id + categories_flat).
        This method replicates that logic to find the hashed IDs.
        
        Returns:
            List of hashed project IDs used during segmentation
        """
        try:
            if not self.project_asins:
                return []
            
            # Get category groupings for project's ASINs (same as segmentation logic)
            result = self.supabase.table('product_wide_table').select(
                'platform_id, categories_flat'
            ).in_('platform_id', self.project_asins).execute()
            
            if not result.data:
                return []
            
            # Group by categories_flat (same as segmentation)
            category_groups = {}
            for row in result.data:
                categories_flat = row.get('categories_flat')
                if not categories_flat or not categories_flat.strip():
                    continue
                    
                full_category_path = categories_flat.strip()
                if full_category_path not in category_groups:
                    category_groups[full_category_path] = []
                category_groups[full_category_path].append(row['platform_id'])
            
            # Generate the same hashes that were used during segmentation
            import hashlib
            hashed_project_ids = []
            for full_category_path in category_groups.keys():
                run_group_id_str = f"{self.project_id}_{full_category_path}"
                run_group_id = hashlib.sha1(run_group_id_str.encode()).hexdigest()
                hashed_project_ids.append(run_group_id)
            
            logger.info(f"Found {len(hashed_project_ids)} segmentation group hashes for project {self.project_id}")
            return hashed_project_ids
                
        except Exception as e:
            logger.error(f"Error generating segmentation hashed project IDs: {e}")
            return []
    
    def get_project_segments(self) -> List[str]:
        """获取项目的所有segment类型（排除OUT_OF_SCOPE）
        
        首先尝试使用原项目ID，如果找不到数据，再尝试哈希ID方案。
        
        Returns:
            项目所有有效segment名称列表
        """
        try:
            # 方案1: 直接使用原项目ID（新格式）
            direct_result = self.supabase.table('product_segment_assignments')\
                .select('segment_name')\
                .eq('project_id', self.project_id)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if direct_result.data:
                segments = list(set(item['segment_name'] for item in direct_result.data))
                logger.info(f"Found {len(segments)} segments using direct project ID {self.project_id}: {segments}")
                return sorted(segments)
            
            # 方案2: 使用哈希ID方案（旧格式）
            hashed_project_ids = self._get_segmentation_hashed_project_ids()
            
            if not hashed_project_ids:
                logger.warning(f"No segmentation hashes found for project {self.project_id}")
                return []
            
            # Look up segments using the hashed project IDs
            hashed_result = self.supabase.table('product_segment_assignments')\
                .select('segment_name')\
                .in_('project_id', hashed_project_ids)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if hashed_result.data:
                segments = list(set(item['segment_name'] for item in hashed_result.data))
                logger.info(f"Found {len(segments)} segments using hashed project IDs: {segments}")
                return sorted(segments)
            else:
                logger.warning(f"No segment assignments found for hashed project IDs: {hashed_project_ids}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching project segments: {e}")
            return []
    
    def _get_segment_assignments_shared(self) -> Dict[str, str]:
        """获取项目的segment分配（platform_id到segment_name的映射）
        
        首先尝试使用哈希项目ID方案，如果找不到数据，再尝试原项目ID。
        
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
            wide_table_ids = list(platform_to_wide_id.values())
            
            # 方案1: 使用哈希ID方案（旧格式）
            hashed_project_ids = self._get_segmentation_hashed_project_ids()
            assignments_result = None
            
            if hashed_project_ids:
                # 查询segment assignments（使用hashed_project_ids）
                assignments_result = self.supabase.table('product_segment_assignments')\
                    .select('product_id, segment_name')\
                    .in_('project_id', hashed_project_ids)\
                    .in_('product_id', wide_table_ids)\
                    .neq('segment_name', None)\
                    .neq('segment_name', 'OUT_OF_SCOPE')\
                    .execute()
                
                if assignments_result.data:
                    logger.info(f"Found segment assignments using hashed project IDs: {len(assignments_result.data)} mappings")
                else:
                    logger.info(f"No segment assignments found using hashed project IDs")
                    assignments_result = None
            
            # 方案2: 使用原项目ID（新格式）作为fallback
            if not assignments_result or not assignments_result.data:
                assignments_result = self.supabase.table('product_segment_assignments')\
                    .select('product_id, segment_name')\
                    .eq('project_id', self.project_id)\
                    .in_('product_id', wide_table_ids)\
                    .neq('segment_name', None)\
                    .neq('segment_name', 'OUT_OF_SCOPE')\
                    .execute()
                
                if assignments_result.data:
                    logger.info(f"Found segment assignments using direct project ID: {len(assignments_result.data)} mappings")
                else:
                    logger.warning(f"No segment assignments found for either hashed or direct project ID")
                    return {}
            
            # 建立wide_table_id到segment的映射
            wide_id_to_segment = {item['product_id']: item['segment_name'] for item in assignments_result.data}
            
            # 转换为platform_id到segment的映射
            platform_to_segment = {}
            for platform_id, wide_id in platform_to_wide_id.items():
                if wide_id in wide_id_to_segment:
                    platform_to_segment[platform_id] = wide_id_to_segment[wide_id]
            
            logger.info(f"Successfully mapped {len(platform_to_segment)} products to segments")
            return platform_to_segment
                
        except Exception as e:
            logger.error(f"Error getting segment assignments: {e}")
            return {}
    
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