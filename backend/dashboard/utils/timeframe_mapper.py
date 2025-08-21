"""Timeframe field mapping utilities for dashboard."""

from typing import Optional, Tuple
from datetime import datetime, timedelta
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
    
    @classmethod
    def get_date_range(cls, timeframe: Optional[TimeframeModel]) -> Tuple[str, str]:
        """根据timeframe计算实际的开始和结束日期
        
        Args:
            timeframe: 时间维度模型
            
        Returns:
            Tuple[str, str]: (start_date, end_date) in YYYY-MM-DD format
        """
        end_date = datetime.now().date()
        
        period = cls.DEFAULT_PERIOD
        if timeframe and timeframe.period:
            period = timeframe.period
        
        if period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "6months":
            start_date = end_date - timedelta(days=180)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=365)  # 默认1年
        
        return start_date.isoformat(), end_date.isoformat()
    
    @classmethod
    def get_month_range(cls, timeframe: Optional[TimeframeModel]) -> Tuple[str, str]:
        """根据timeframe计算月份范围（用于月度销售数据查询）
        
        Args:
            timeframe: 时间维度模型
            
        Returns:
            Tuple[str, str]: (start_month, end_month) in YYYY-MM-01 format
        """
        start_date, end_date = cls.get_date_range(timeframe)
        
        # 转换为月份第一天格式
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(day=1)
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(day=1)
        
        return start_datetime.date().isoformat(), end_datetime.date().isoformat()