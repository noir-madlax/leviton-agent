"""Sales trend API models and data structures."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import date, datetime
from ..base_models import BaseRequestModel

# ==================== 请求模型 ====================

class SalesTrendRequest(BaseModel):
    """销售趋势分析请求模型"""
    project_id: str = Field(..., description="项目ID，用于ASIN过滤")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件JSON对象")
    date_range: Optional[Dict[str, str]] = Field(default=None, description="时间范围，格式：{'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}")
    aggregation: Literal["monthly"] = Field(default="monthly", description="数据聚合粒度，目前只支持monthly")

    def get_date_range_filter(self) -> Dict[str, Optional[str]]:
        """获取时间范围筛选条件"""
        if not self.date_range:
            return {"start_date": None, "end_date": None}
        return {
            "start_date": self.date_range.get("start_date"),
            "end_date": self.date_range.get("end_date")
        }

# ==================== 响应模型 ====================

class BrandMetrics(BaseModel):
    """品牌指标模型"""
    revenue: float = Field(..., description="收入")
    volume: int = Field(..., description="销量")

class SalesTrendDataPoint(BaseModel):
    """单个月度数据点模型"""
    month: str = Field(..., description="月份 (YYYY-MM格式)")
    # 动态品牌字段将在运行时添加
    
    class Config:
        extra = "allow"  # 允许动态添加品牌字段
        json_schema_extra = {
            "example": {
                "month": "2024-01",
                "Leviton": {"revenue": 850000, "volume": 12000},
                "Lutron": {"revenue": 720000, "volume": 9000},
                "GE": {"revenue": 680000, "volume": 11000}
            }
        }

class SalesTrendSummary(BaseModel):
    """销售趋势汇总统计"""
    total_brands: int = Field(..., description="总品牌数（Top 10）")
    date_range: Dict[str, str] = Field(..., description="实际数据时间范围")
    total_revenue: float = Field(..., description="总收入")
    total_volume: int = Field(..., description="总销量")

class SalesTrendResponse(BaseModel):
    """销售趋势API响应模型"""
    trend_data: List[SalesTrendDataPoint] = Field(..., description="月度趋势数据列表")
    brands: List[str] = Field(..., description="Top 10品牌列表（按总revenue排序）")
    summary: SalesTrendSummary = Field(..., description="汇总统计信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trend_data": [
                    {
                        "month": "2024-01",
                        "Leviton": {"revenue": 850000, "volume": 12000},
                        "Lutron": {"revenue": 720000, "volume": 9000}
                    }
                ],
                "brands": ["Leviton", "Lutron", "GE"],
                "summary": {
                    "total_brands": 3,
                    "date_range": {"start": "2024-01", "end": "2024-06"},
                    "total_revenue": 15230000,
                    "total_volume": 89400
                }
            }
        }

# ==================== 新版本请求模型（支持timeframe） ====================

class BrandSalesTrendRequest(BaseRequestModel):
    """品牌销售趋势分析请求模型 - 新版本使用timeframe"""
    
    limit: int = Field(default=10, description="返回的Top品牌数量", ge=1, le=20)
    metric_type: Literal["revenue", "volume"] = Field(
        default="revenue", 
        description="主要指标类型: revenue(收入), volume(销量)"
    )
    aggregation: Literal["monthly"] = Field(
        default="monthly", 
        description="数据聚合粒度，目前只支持monthly"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "filters": {
                    "categories": ["Light Switches", "Dimmer Switches"],
                    "brands": [],
                    "segments": [],
                    "extend_fields": {"smart_capability": "Smart"}
                },
                "timeframe": {
                    "period": "year"
                },
                "limit": 10,
                "metric_type": "revenue",
                "aggregation": "monthly"
            }
        }

# ==================== 新版本响应模型 ====================

class BrandSalesTrendDataPoint(BaseModel):
    """单个月度数据点模型 - 新版本"""
    month: str = Field(..., description="月份 (YYYY-MM格式)")
    
    class Config:
        extra = "allow"  # 允许动态添加品牌字段
        json_schema_extra = {
            "example": {
                "month": "2024-01",
                "Leviton": {"revenue": 850000, "volume": 12000},
                "Lutron": {"revenue": 720000, "volume": 9000},
                "GE": {"revenue": 680000, "volume": 11000}
            }
        }

class CategorySalesTrendSummary(BaseModel):
    """单个category的销售趋势汇总统计"""
    total_brands: int = Field(..., description="该category的品牌数（Top N）")
    date_range: Dict[str, str] = Field(..., description="实际数据时间范围")
    total_revenue: float = Field(..., description="该category的总收入")
    total_volume: int = Field(..., description="该category的总销量")
    timeframe_period: str = Field(..., description="分析时间维度")

class CategorySalesTrendData(BaseModel):
    """单个category的完整销售趋势数据"""
    trend_data: List[BrandSalesTrendDataPoint] = Field(..., description="月度趋势数据列表")
    brands: List[str] = Field(..., description="该category的Top N品牌列表（按指标排序）")
    summary: CategorySalesTrendSummary = Field(..., description="该category的汇总统计信息")

class OverallSummary(BaseModel):
    """全局汇总统计信息"""
    total_categories: int = Field(..., description="处理的category总数")
    all_brands: List[str] = Field(..., description="所有category中出现的品牌列表（去重）")
    total_revenue: float = Field(..., description="所有category的总收入")
    total_volume: int = Field(..., description="所有category的总销量")
    date_range: Dict[str, str] = Field(..., description="数据时间范围")
    timeframe_period: str = Field(..., description="分析时间维度")

class BrandSalesTrendMetadata(BaseModel):
    """品牌销售趋势分析元数据"""
    filtered_asins_count: int = Field(..., description="过滤后的ASIN数量")
    calculation_timestamp: str = Field(..., description="计算时间戳")
    timeframe_used: str = Field(..., description="使用的时间维度")
    data_source: str = Field(default="product_sales_history_monthly", description="数据来源表")
    categories_processed: List[str] = Field(..., description="处理的category列表")

class BrandSalesTrendResponse(BaseModel):
    """品牌销售趋势API响应模型 - 多category版本"""
    categories_data: Dict[str, CategorySalesTrendData] = Field(..., description="按category分组的销售趋势数据")
    overall_summary: OverallSummary = Field(..., description="全局汇总统计信息")
    metadata: BrandSalesTrendMetadata = Field(..., description="分析元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "categories_data": {
                    "Light Switches": {
                        "trend_data": [
                            {
                                "month": "2024-01",
                                "Leviton": {"revenue": 850000, "volume": 12000},
                                "Lutron": {"revenue": 720000, "volume": 9000}
                            }
                        ],
                        "brands": ["Leviton", "Lutron", "GE"],
                        "summary": {
                            "total_brands": 3,
                            "date_range": {"start": "2024-01", "end": "2024-06"},
                            "total_revenue": 2270000,
                            "total_volume": 21000,
                            "timeframe_period": "year"
                        }
                    },
                    "Dimmer Switches": {
                        "trend_data": [
                            {
                                "month": "2024-01",
                                "TP-Link": {"revenue": 650000, "volume": 8000},
                                "Philips": {"revenue": 520000, "volume": 7000}
                            }
                        ],
                        "brands": ["TP-Link", "Philips", "LIFX"],
                        "summary": {
                            "total_brands": 3,
                            "date_range": {"start": "2024-01", "end": "2024-06"},
                            "total_revenue": 1820000,
                            "total_volume": 15000,
                            "timeframe_period": "year"
                        }
                    }
                },
                "overall_summary": {
                    "total_categories": 2,
                    "all_brands": ["Leviton", "Lutron", "GE", "TP-Link", "Philips", "LIFX"],
                    "total_revenue": 4090000,
                    "total_volume": 36000,
                    "date_range": {"start": "2024-01", "end": "2024-06"},
                    "timeframe_period": "year"
                },
                "metadata": {
                    "filtered_asins_count": 1250,
                    "calculation_timestamp": "2024-01-15T10:30:00Z",
                    "timeframe_used": "year",
                    "data_source": "product_sales_history_monthly",
                    "categories_processed": ["Light Switches", "Dimmer Switches"]
                }
            }
        } 