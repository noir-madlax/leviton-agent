"""Timeframe field mapping utilities for dashboard."""

from typing import Optional, Tuple
from dashboard.charts.base_models import TimeframeModel


class TimeframeFieldMapper:
    """工具类：根据时间维度映射数据库字段"""
    
    # 字段映射配置
    FIELD_MAPPING = {
        "month": {
            "revenue": "past_month_revenue",
            "volume": "past_month_volume"
        },
        "6months": {
            "revenue": "past_6_month_revenue", 
            "volume": "past_6_month_volume"
        },
        "year": {
            "revenue": "past_year_revenue",
            "volume": "past_year_volume"
        }
    }
    
    DEFAULT_PERIOD = "year"
    
    @classmethod
    def get_fields(cls, timeframe: Optional[TimeframeModel]) -> Tuple[str, str]:
        """获取对应的revenue和volume字段名
        
        Args:
            timeframe: 时间维度模型，如果为None则使用默认值
            
        Returns:
            Tuple[str, str]: (revenue_field, volume_field)
        """
        period = cls.DEFAULT_PERIOD
        if timeframe and timeframe.period:
            period = timeframe.period
            
        mapping = cls.FIELD_MAPPING.get(period, cls.FIELD_MAPPING[cls.DEFAULT_PERIOD])
        return mapping["revenue"], mapping["volume"]