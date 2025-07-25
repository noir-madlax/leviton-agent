"""Customer satisfaction analysis API models and data structures."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..base_models import BaseRequestModel

# ==================== 请求模型 ====================

class CustomerSatisfactionRequest(BaseRequestModel):
    """客户满意度分析请求模型"""
    selected_asins: Optional[List[str]] = Field(default=None, description="选中的ASIN列表，如果为空则使用默认竞争对手产品")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "project_123",
                "filters": {
                    "categories": ["Smart Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "segments": ["Premium"],
                    "extend_fields": {"is_bestseller": True}
                },
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-06-30"
                },
                "selected_asins": ["B00NG0ELL0", "B0BVKZLT3B", "B0BVKYKKRK"]
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

class CustomerSatisfactionSummary(BaseModel):
    """客户满意度汇总统计"""
    total_products: int = Field(..., description="分析的产品总数")
    avg_satisfaction_score: float = Field(..., description="平均满意度分数")
    total_reviews_analyzed: int = Field(..., description="分析的评论总数")
    top_performer: Optional[str] = Field(None, description="表现最佳产品ASIN")
    analysis_method: str = Field(..., description="分析方法说明")
    last_updated: str = Field(..., description="数据最后更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_products": 6,
                "avg_satisfaction_score": 76.8,
                "total_reviews_analyzed": 8450,
                "top_performer": "B0BVKYKKRK",
                "analysis_method": "Based on latest 200 reviews per product",
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }

class CustomerSatisfactionResponse(BaseModel):
    """客户满意度分析API响应模型"""
    products: List[ProductSatisfactionData] = Field(..., description="产品满意度数据列表")
    summary: CustomerSatisfactionSummary = Field(..., description="汇总统计信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "products": [
                    {
                        "asin": "B00NG0ELL0",
                        "name": "Leviton DSL06-1LZ Decora Smart...",
                        "full_title": "Leviton DSL06-1LZ Decora Smart Wi-Fi 600W Incandescent/300W LED Dimmer",
                        "brand": "Leviton",
                        "total_reviews": 1250,
                        "average_rating": 4.3,
                        "satisfaction_score": 78.5,
                        "price_usd": 49.99,
                        "product_url": "https://amazon.com/dp/B00NG0ELL0"
                    }
                ],
                "summary": {
                    "total_products": 6,
                    "avg_satisfaction_score": 76.8,
                    "total_reviews_analyzed": 8450,
                    "top_performer": "B0BVKYKKRK",
                    "analysis_method": "Based on latest 200 reviews per product",
                    "last_updated": "2024-01-15T10:30:00Z"
                }
            }
        }
