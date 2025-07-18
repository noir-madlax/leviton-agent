from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ProjectFilters:
    """项目筛选器模型"""
    categories: List[str]
    brands: List[str]
    segments: List[str]
    extend_fields: Dict[str, Any]
    asins: List[str]

    def is_empty(self) -> bool:
        """检查筛选器是否为空"""
        return (
            not self.categories and
            not self.brands and
            not self.segments and
            not self.extend_fields and
            not self.asins
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'categories': self.categories,
            'brands': self.brands,
            'segments': self.segments,
            'extend_fields': self.extend_fields,
            'asins': self.asins
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectFilters':
        """从字典创建筛选器实例"""
        return cls(
            categories=data.get('categories', []),
            brands=data.get('brands', []),
            segments=data.get('segments', []),
            extend_fields=data.get('extend_fields', {}),
            asins=data.get('asins', [])
        )

    @classmethod
    def empty(cls) -> 'ProjectFilters':
        """创建空的筛选器"""
        return cls(
            categories=[],
            brands=[],
            segments=[],
            extend_fields={},
            asins=[]
        )


@dataclass
class EnhancedProjectFilters(ProjectFilters):
    """增强的项目筛选器，支持图表点击的精确筛选"""

    # 排除条件
    exclude_asins: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedProjectFilters':
        """从字典创建增强筛选器实例"""
        base_filters = super().from_dict(data)
        return cls(
            categories=base_filters.categories,
            brands=base_filters.brands,
            segments=base_filters.segments,
            extend_fields=base_filters.extend_fields,
            asins=base_filters.asins,
            exclude_asins=data.get('exclude_asins', [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            'exclude_asins': self.exclude_asins
        })
        return base_dict

    @classmethod
    def empty(cls) -> 'EnhancedProjectFilters':
        """创建空的增强筛选器"""
        return cls(
            categories=[],
            brands=[],
            segments=[],
            extend_fields={},
            asins=[],
            exclude_asins=[]
        )

@dataclass
class FilterOptions:
    """筛选器选项模型"""
    categories: List[str]
    brands: List[str]
    segments: List[str]
    extend_fields: Dict[str, List[str]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'categories': self.categories,
            'brands': self.brands,
            'segments': self.segments,
            'extend_fields': self.extend_fields
        } 