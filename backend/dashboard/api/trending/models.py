"""Sales trend API models and data structures."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import date, datetime

# ==================== 请求模型 ====================

class SalesTrendRequest(BaseModel):
    """销售趋势分析请求模型
    
    继承统一的API格式，支持：
    - 项目ID筛选
    - 标准过滤条件（categories, brands, segments, extend_fields）
    - 时间范围参数
    - 产品ASIN指定
    """
    project_id: str = Field(..., description="项目ID，用于ASIN过滤")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件JSON对象")
    
    # 业务特定参数
    date_range: Optional[Dict[str, str]] = Field(default=None, description="时间范围，格式：{'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}")
    asin: Optional[str] = Field(default=None, description="特定产品ASIN，如果未指定则返回项目汇总数据")
    metric_type: Optional[Literal["sales", "price", "revenue"]] = Field(default="sales", description="主要指标类型：销量/价格/收入")
    aggregation: Optional[Literal["daily", "weekly", "monthly"]] = Field(default="daily", description="数据聚合粒度")

    def get_date_range_filter(self) -> Dict[str, Optional[str]]:
        """获取时间范围筛选条件"""
        if not self.date_range:
            return {"start_date": None, "end_date": None}
        return {
            "start_date": self.date_range.get("start_date"),
            "end_date": self.date_range.get("end_date")
        }

# ==================== 响应模型 ====================

class SalesTrendDataPoint(BaseModel):
    """单个数据点模型"""
    date: str = Field(..., description="日期 (YYYY-MM-DD格式)")
    estimated_units_sold: int = Field(..., description="估计销售量")
    last_known_price: float = Field(..., description="最后已知价格(USD)")
    estimated_revenue: Optional[float] = Field(None, description="估计收入 (单价 × 销量)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-07-19",
                "estimated_units_sold": 53,
                "last_known_price": 3.5,
                "estimated_revenue": 185.5
            }
        }

class SalesTrendSummaryStats(BaseModel):
    """趋势汇总统计"""
    total_period_sales: int = Field(..., description="时间段内总销量")
    average_daily_sales: float = Field(..., description="日均销量")
    average_price: float = Field(..., description="平均价格")
    price_volatility: float = Field(..., description="价格波动率（标准差）")
    total_revenue: float = Field(..., description="总收入")
    growth_rate: Optional[float] = Field(None, description="销量增长率（对比期初期末）")
    
class SalesTrendResponse(BaseModel):
    """销售趋势API响应模型"""
    
    # 核心数据
    trend_data: List[SalesTrendDataPoint] = Field(..., description="趋势数据点列表")
    summary_stats: SalesTrendSummaryStats = Field(..., description="汇总统计信息")
    
    # 元数据
    project_id: str = Field(..., description="项目ID")
    asin: Optional[str] = Field(None, description="产品ASIN（如果是单产品查询）")
    date_range: Dict[str, str] = Field(..., description="实际查询的时间范围")
    metric_type: str = Field(..., description="主要指标类型")
    aggregation: str = Field(..., description="数据聚合粒度")
    
    # 筛选结果信息
    total_data_points: int = Field(..., description="返回的数据点数量")
    applied_filters: Dict[str, Any] = Field(default_factory=dict, description="实际应用的筛选条件")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trend_data": [
                    {
                        "date": "2024-07-19",
                        "estimated_units_sold": 53,
                        "last_known_price": 3.5,
                        "estimated_revenue": 185.5
                    },
                    {
                        "date": "2024-07-20", 
                        "estimated_units_sold": 45,
                        "last_known_price": 3.5,
                        "estimated_revenue": 157.5
                    }
                ],
                "summary_stats": {
                    "total_period_sales": 18234,
                    "average_daily_sales": 95.3,
                    "average_price": 3.52,
                    "price_volatility": 0.85,
                    "total_revenue": 64183.68,
                    "growth_rate": 15.2
                },
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "asin": "B08SJ3Z8XD",
                "date_range": {
                    "start_date": "2024-07-19",
                    "end_date": "2025-07-19"
                },
                "metric_type": "sales",
                "aggregation": "daily",
                "total_data_points": 365,
                "applied_filters": {}
            }
        } 