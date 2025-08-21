"""链式过滤器系统 - 用于构建动态SQL查询条件"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..base_models import FiltersModel
import logging

logger = logging.getLogger(__name__)


class SQLQueryBuilder:
    """SQL查询构建器"""
    
    def __init__(self, base_table: str = "product_wide_table", alias: str = "pwt"):
        self.base_table = base_table
        self.alias = alias
        self.select_fields = ["pwt.platform_id"]
        self.from_clause = f"{base_table} {alias}"
        self.where_conditions = ["1 = 1"]
        self.params = {}
        self.param_counter = 0
    
    def add_select_field(self, field: str):
        """添加SELECT字段"""
        if field not in self.select_fields:
            self.select_fields.append(field)
        return self
    
    def add_where_condition(self, condition: str):
        """添加WHERE条件"""
        self.where_conditions.append(condition)
        return self
    
    def add_param(self, value: Any) -> str:
        """添加参数并返回SQL字面值"""
        if isinstance(value, str):
            # 转义单引号并用单引号包围
            escaped_value = value.replace("'", "''")
            return f"'{escaped_value}'"
        elif isinstance(value, list):
            # 处理数组类型
            if all(isinstance(item, str) for item in value):
                # 字符串数组
                escaped_items = []
                for item in value:
                    escaped_item = item.replace("'", "''")
                    escaped_items.append(f"'{escaped_item}'")
                return f"ARRAY[{', '.join(escaped_items)}]"
            else:
                # 其他类型数组
                return f"ARRAY[{', '.join(str(item) for item in value)}]"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif value is None:
            return 'NULL'
        else:
            # 其他类型转为字符串并转义
            escaped_value = str(value).replace("'", "''")
            return f"'{escaped_value}'"
    
    def build(self) -> str:
        """构建最终SQL"""
        sql_parts = [
            f"select {', '.join(self.select_fields)}",
            f"from {self.from_clause}",
            f"where {' and '.join(self.where_conditions)}"
        ]

        sql = "\n".join(sql_parts)
        return sql


class BaseFilter(ABC):
    """过滤器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.next_filter: Optional['BaseFilter'] = None
    
    def set_next(self, filter_instance: 'BaseFilter') -> 'BaseFilter':
        """设置下一个过滤器"""
        self.next_filter = filter_instance
        return filter_instance
    
    def handle(self, builder: SQLQueryBuilder, project_id: str, filters: Optional[FiltersModel]) -> SQLQueryBuilder:
        """处理过滤器逻辑"""
        # 应用当前过滤器
        builder = self.apply_filter(builder, project_id, filters)
        
        # 传递给下一个过滤器
        if self.next_filter:
            builder = self.next_filter.handle(builder, project_id, filters)
        
        return builder
    
    @abstractmethod
    def apply_filter(self, builder: SQLQueryBuilder, project_id: str, filters: Optional[FiltersModel]) -> SQLQueryBuilder:
        """应用具体的过滤逻辑"""
        pass


class ProjectIdFilter(BaseFilter):
    """项目ID过滤器 - 必传参数"""
    
    def __init__(self):
        super().__init__("project_id")
    
    def apply_filter(self, builder: SQLQueryBuilder, project_id: str, filters: Optional[FiltersModel]) -> SQLQueryBuilder:
        """应用项目ID过滤"""
        if not project_id:
            raise ValueError("project_id is required")
        
        logger.info(f"Applying project_id filter: {project_id}")
        
        # 添加项目ID过滤条件
        project_id_param = builder.add_param(project_id)
        condition = f"""(
    exists (
      select
        1
      from
        project_extend_data ped
      where
        ped.asins = {builder.alias}.platform_id
        and ped.project_id = {project_id_param}
    )
  )"""
        
        builder.add_where_condition(condition)
        return builder


class BrandFilter(BaseFilter):
    """品牌过滤器"""
    
    def __init__(self):
        super().__init__("brand")
    
    def apply_filter(self, builder: SQLQueryBuilder, project_id: str, filters: Optional[FiltersModel]) -> SQLQueryBuilder:
        """应用品牌过滤"""
        if not filters or not filters.brands:
            logger.info("Skipping brand filter - no brands specified")
            return builder
        
        logger.info(f"Applying brand filter: {filters.brands}")
        
        # 添加品牌过滤条件
        brands_param = builder.add_param(filters.brands)
        condition = f"""(
    {builder.alias}.brand = any ({brands_param}::text[])
  )"""
        
        builder.add_where_condition(condition)
        return builder


class CategoryFilter(BaseFilter):
    """类别过滤器"""
    
    def __init__(self):
        super().__init__("category")
    
    def apply_filter(self, builder: SQLQueryBuilder, project_id: str, filters: Optional[FiltersModel]) -> SQLQueryBuilder:
        """应用类别过滤"""
        if not filters or not filters.categories:
            logger.info("Skipping category filter - no categories specified")
            return builder
        
        logger.info(f"Applying category filter: {filters.categories}")
        
        # 添加类别过滤条件
        categories_param = builder.add_param(filters.categories)
        condition = f"""(
    {builder.alias}.category = any ({categories_param}::text[])
  )"""
        
        builder.add_where_condition(condition)
        return builder


class ExtendFieldsFilter(BaseFilter):
    """扩展字段过滤器"""
    
    def __init__(self):
        super().__init__("extend_fields")
    
    def apply_filter(self, builder: SQLQueryBuilder, project_id: str, filters: Optional[FiltersModel]) -> SQLQueryBuilder:
        """应用扩展字段过滤"""
        if not filters or not filters.extend_fields:
            logger.info("Skipping extend_fields filter - no extend_fields specified")
            return builder
        
        logger.info(f"Applying extend_fields filter: {filters.extend_fields}")
        
        # 构建扩展字段过滤条件
        project_id_param = builder.add_param(project_id)
        extend_conditions = []
        
        for field_name, field_value in filters.extend_fields.items():
            if isinstance(field_value, list):
                # 如果是数组值，使用ANY操作符
                field_param = builder.add_param(field_value)
                extend_conditions.append(
                    f"ped.extend ->> '{field_name}' = any ({field_param}::text[])"
                )
            else:
                # 如果是单个值
                field_param = builder.add_param(str(field_value))
                extend_conditions.append(
                    f"ped.extend ->> '{field_name}' = {field_param}"
                )
        
        if extend_conditions:
            condition = f"""(
    exists (
      select
        1
      from
        project_extend_data ped
      where
        ped.asins = {builder.alias}.platform_id
        and ped.project_id = {project_id_param}
        and (
          {' and '.join(extend_conditions)}
        )
    )
  )"""
            
            builder.add_where_condition(condition)
        
        return builder


class FilterChain:
    """过滤器链管理器"""
    
    def __init__(self):
        self.chain = self._build_default_chain()
    
    def _build_default_chain(self) -> BaseFilter:
        """构建默认的过滤器链"""
        # 创建过滤器实例
        project_filter = ProjectIdFilter()
        brand_filter = BrandFilter()
        category_filter = CategoryFilter()
        extend_filter = ExtendFieldsFilter()
        
        # 构建链式关系
        project_filter.set_next(brand_filter).set_next(category_filter).set_next(extend_filter)
        
        return project_filter
    
    def build_sql(self, project_id: str, filters: Optional[FiltersModel] = None) -> str:
        """构建SQL查询"""
        logger.info(f"Building SQL for project_id: {project_id}, filters: {filters}")

        # 创建SQL构建器
        builder = SQLQueryBuilder()

        # 执行过滤器链
        builder = self.chain.handle(builder, project_id, filters)

        # 构建最终SQL
        sql = builder.build()

        logger.info(f"Generated SQL: {sql}")

        return sql


# 便捷函数
def build_filtered_sql(project_id: str, filters: Optional[FiltersModel] = None) -> str:
    """构建过滤后的SQL查询

    Args:
        project_id: 项目ID (必传)
        filters: 过滤条件 (可选)

    Returns:
        str: SQL字符串
    """
    chain = FilterChain()
    return chain.build_sql(project_id, filters)
