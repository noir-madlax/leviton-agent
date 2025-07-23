"""Sales trend API models and data structures."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import date

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