"""Categories module data models."""

from typing import List, Optional
from pydantic import BaseModel


class CategoryNode(BaseModel):
    """Category node for frontend display."""
    category_id: str
    name: str
    level: int
    parent_id: Optional[str] = None
    has_children: bool = False
    children_count: int = 0


class CategoryChildrenResponse(BaseModel):
    """Response for category children API."""
    success: bool
    children: List[CategoryNode]
    parent_id: str
    message: Optional[str] = None
    total_count: int = 0


class CategoryTreeResponse(BaseModel):
    """Response for category tree structure."""
    success: bool
    categories: List[CategoryNode]
    message: Optional[str] = None 