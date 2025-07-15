from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ProjectFilters:
    """项目筛选器模型"""
    categories: List[str]
    packaging_types: List[str]
    segments: List[str]
    extend_fields: Dict[str, Any]
    asins: List[str]
    
    def is_empty(self) -> bool:
        """检查筛选器是否为空"""
        return (
            not self.categories and 
            not self.packaging_types and 
            not self.segments and 
            not self.extend_fields and 
            not self.asins
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'categories': self.categories,
            'packaging_types': self.packaging_types,
            'segments': self.segments,
            'extend_fields': self.extend_fields,
            'asins': self.asins
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectFilters':
        """从字典创建筛选器实例"""
        return cls(
            categories=data.get('categories', []),
            packaging_types=data.get('packaging_types', []),
            segments=data.get('segments', []),
            extend_fields=data.get('extend_fields', {}),
            asins=data.get('asins', [])
        )
    
    @classmethod
    def empty(cls) -> 'ProjectFilters':
        """创建空的筛选器"""
        return cls(
            categories=[],
            packaging_types=[],
            segments=[],
            extend_fields={},
            asins=[]
        )

@dataclass
class FilterOptions:
    """筛选器选项模型"""
    categories: List[str]
    packaging_types: List[str]
    segments: List[str]
    extend_fields: Dict[str, List[str]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'categories': self.categories,
            'packaging_types': self.packaging_types,
            'segments': self.segments,
            'extend_fields': self.extend_fields
        } 