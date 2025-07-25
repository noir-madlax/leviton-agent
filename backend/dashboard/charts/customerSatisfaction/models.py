"""Customer satisfaction analysis API models and data structures."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..base_models import BaseRequestModel, BaseResponseModel

# ==================== 请求模型 ====================

class CustomerSatisfactionRequest(BaseRequestModel):
    """客户满意度分析请求模型"""

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "project_123",
                "filters": {
                    "categories": ["Light Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "segments": ["Premium"],
                    "extend_fields": {"smart_capability": "Smart"}
                },
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-06-30"
                }
            }
        }

# ==================== 响应模型 ====================

class ProductSatisfactionData(BaseModel):
    """单个产品满意度数据"""
    asin: str = Field(..., description="产品ASIN")
    name: str = Field(..., description="产品名称（截断版）")
    full_title: str = Field(..., description="产品完整标题")
    brand: str = Field(..., description="品牌")
    total_reviews: int = Field(..., description="分析的评论总数")
    average_rating: Optional[float] = Field(None, description="平均星级评分")
    satisfaction_score: float = Field(..., description="满意度分数（0-100）")
    price_usd: Optional[float] = Field(None, description="价格（美元）")
    product_url: Optional[str] = Field(None, description="产品链接")
    thumbnail_url: Optional[str] = Field(None, description="产品缩略图")
    
    class Config:
        json_schema_extra = {
            "example": {
                "asin": "B00NG0ELL0",
                "name": "Leviton DSL06-1LZ Decora Smart...",
                "full_title": "Leviton DSL06-1LZ Decora Smart Wi-Fi 600W Incandescent/300W LED Dimmer",
                "brand": "Leviton",
                "total_reviews": 1250,
                "average_rating": 4.3,
                "satisfaction_score": 78.5,
                "price_usd": 49.99,
                "product_url": "https://amazon.com/dp/B00NG0ELL0",
                "thumbnail_url": "https://images.amazon.com/..."
            }
        }

class CustomerSatisfactionResponse(BaseResponseModel[List[ProductSatisfactionData]]):
    """客户满意度分析API响应模型

    直接返回产品数组，便于前端按顺序渲染
    """

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": None,
                "timestamp": "2024-01-15T10:30:00Z",
                "data": [
                    {
                        "asin": "B00NG0ELL0",
                        "name": "Leviton DSL06-1LZ Decora Smart...",
                        "full_title": "Leviton DSL06-1LZ Decora Smart Wi-Fi 600W Incandescent/300W LED Dimmer",
                        "brand": "Leviton",
                        "total_reviews": 1250,
                        "average_rating": 4.3,
                        "satisfaction_score": 78.5,
                        "price_usd": 49.99,
                        "product_url": "https://amazon.com/dp/B00NG0ELL0",
                        "thumbnail_url": None
                    },
                    {
                        "asin": "B0BVKZLT3B",
                        "name": "Leviton D215S Smart Switch...",
                        "full_title": "Leviton D215S Smart Switch",
                        "brand": "Leviton",
                        "total_reviews": 890,
                        "average_rating": 4.1,
                        "satisfaction_score": 72.5,
                        "price_usd": 39.99,
                        "product_url": "https://amazon.com/dp/B0BVKZLT3B",
                        "thumbnail_url": None
                    }
                ]
            }
        }
