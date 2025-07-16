from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ProjectFilters:
    """项目筛选器模型"""
    categories: List[str]
    brands: List[str]
    segments: List[str]
    is_bestseller: Optional[str]  # 新增: 畅销书状态过滤 ("true", "false", None)
    extend_fields: Dict[str, Any]
    asins: List[str]
    
    def is_empty(self) -> bool:
        """检查筛选器是否为空"""
        return (
            not self.categories and
            not self.brands and
            not self.segments and
            not self.is_bestseller and
            not self.extend_fields and
            not self.asins
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'categories': self.categories,
            'brands': self.brands,
            'segments': self.segments,
            'is_bestseller': self.is_bestseller,
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
            is_bestseller=data.get('is_bestseller'),
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
            is_bestseller=None,
            extend_fields={},
            asins=[]
        )

@dataclass
class FilterOptions:
    """筛选器选项模型"""
    categories: List[str]
    brands: List[str]
    segments: List[str]
    is_bestseller_options: List[str]  # 新增: 畅销书状态选项 ["true", "false", "null"]
    extend_fields: Dict[str, List[str]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'categories': self.categories,
            'brands': self.brands,
            'segments': self.segments,
            'is_bestseller_options': self.is_bestseller_options,
            'extend_fields': self.extend_fields
        }