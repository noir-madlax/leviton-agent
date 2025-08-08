"""Base models for dashboard charts."""

from typing import Dict, Any, Optional, Generic, TypeVar, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# 泛型类型变量，用于BaseResponseModel
T = TypeVar('T')

class FiltersModel(BaseModel):
    """筛选条件模型"""
    categories: List[str] = Field(default_factory=list, description="产品类别筛选")
    brands: List[str] = Field(default_factory=list, description="品牌筛选")
    segments: List[str] = Field(default_factory=list, description="细分市场筛选")
    extend_fields: Dict[str, Any] = Field(default_factory=dict, description="扩展字段筛选，字段名和值不固定")

    class Config:
        json_schema_extra = {
            "example": {
                "categories": ["Light Switches"],
                "brands": [],
                "segments": [],
                "extend_fields": {"smart_capability": "Smart"}
            }
        }

class TimeframeModel(BaseModel):
    """时间维度模型 - 用于指定分析的时间范围"""
    period: Literal["month", "6months", "year"] = Field(
        default="year", 
        description="时间周期选择：month(过去1个月), 6months(过去6个月), year(过去1年)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "period": "year"
            }
        }

# 为了向后兼容，保留原有的DateRangeModel
class DateRangeModel(BaseModel):
    """时间范围模型（已废弃，请使用TimeframeModel）"""
    start_date: str = Field(..., description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式：YYYY-MM-DD")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-06-30"
            }
        }

class BaseRequestModel(BaseModel):
    """Dashboard charts 基础请求模型"""
    project_id: str = Field(..., description="项目ID，用于ASIN过滤")
    filters: Optional[FiltersModel] = Field(default=None, description="过滤条件对象")
    selected_asins: Optional[List[str]] = Field(default=None, description="指定要分析的ASIN列表，如果提供则优先使用此列表而不是filters")
    timeframe: Optional[TimeframeModel] = Field(default=None, description="时间维度对象，指定分析的时间范围")
    # 保留date_range以向后兼容，但推荐使用timeframe
    date_range: Optional[DateRangeModel] = Field(default=None, description="时间范围对象（已废弃，推荐使用timeframe）")

class BaseResponseModel(BaseModel, Generic[T]):
    """Dashboard charts 基础响应模型"""
    status: str = Field(default="success", description="响应状态：success/error")
    message: Optional[str] = Field(default=None, description="响应消息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="响应时间戳")
    data: T = Field(..., description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": None,
                "timestamp": "2024-01-15T10:30:00Z",
                "data": "具体的数据内容"
            }
        }
