"""
Agent 请求模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AgentFilters(BaseModel):
    """Agent 过滤器模型"""
    categories: List[str] = Field(default_factory=list, description="类别过滤器列表")
    brands: List[str] = Field(default_factory=list, description="品牌过滤器列表")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围过滤器")
    price_range: Optional[Dict[str, float]] = Field(None, description="价格范围过滤器")


class AgentStreamRequest(BaseModel):
    """Agent 流式请求模型"""
    query: str = Field(..., min_length=1, description="要处理的查询内容")
    project_id: Optional[str] = Field(None, alias="projectId", description="项目ID")
    user_id: Optional[str] = Field(None, alias="userId", description="用户ID")
    session_id: Optional[str] = Field(None, alias="sessionId", description="会话ID")
    filters: AgentFilters = Field(default_factory=AgentFilters, description="过滤器配置")
    
    class Config:
        # 允许使用字段别名
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "query": "What are the top selling product segments?",
                "projectId": "123e4567-e89b-12d3-a456-426614174000",
                "filters": {
                    "categories": ["Light Switches", "Dimmer Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    },
                    "price_range": {
                        "min": 10.0,
                        "max": 100.0
                    }
                }
            }
        }


class AgentQueryContext(BaseModel):
    """Agent 查询上下文模型"""
    original_query: str = Field(..., description="原始用户查询")
    project_id: Optional[str] = Field(None, description="项目ID")
    category_filters: List[str] = Field(default_factory=list, description="类别过滤器")
    brand_filters: List[str] = Field(default_factory=list, description="品牌过滤器")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="额外上下文信息")
    
    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        summary_parts = []
        
        if self.project_id:
            summary_parts.append(f"项目ID: {self.project_id}")
        
        if self.category_filters:
            categories_str = ", ".join(self.category_filters)
            summary_parts.append(f"需要过滤的类别: {categories_str}")
        
        if self.brand_filters:
            brands_str = ", ".join(self.brand_filters)
            summary_parts.append(f"需要过滤的品牌: {brands_str}")
        
        if summary_parts:
            return f"本次任务的上下文信息: {'; '.join(summary_parts)}"
        else:
            return "本次任务没有特定的过滤条件" 