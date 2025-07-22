"""Sales trend data service for dashboard."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import statistics

# 引入基础服务和过滤器
from backend.dashboard.services.base_service import BaseDashboardService
from backend.core.models.filters import ProjectFilters

logger = logging.getLogger(__name__)

class SalesTrendService(BaseDashboardService):
    """销售趋势数据服务类
    
    继承BaseDashboardService，自动获得：
    - 项目ASIN过滤
    - 标准过滤条件支持（categories, brands, segments, extend_fields）
    - Supabase客户端连接
    """
    
    def __init__(self, project_id: str):
        super().__init__(project_id)
        self.target_asin: Optional[str] = None
        self.date_range_filter = {"start_date": None, "end_date": None}
        self.metric_type = "sales"
        self.aggregation = "daily"
    
    def set_target_asin(self, asin: str):
        """设置特定的目标ASIN"""
        self.target_asin = asin
        logger.info(f"Target ASIN set to: {asin}")
    
    def set_date_range(self, start_date: Optional[str], end_date: Optional[str]):
        """设置时间范围"""
        self.date_range_filter = {
            "start_date": start_date,
            "end_date": end_date
        }
        logger.info(f"Date range set: {start_date} to {end_date}")
    
    def set_metric_type(self, metric_type: str):
        """设置主要指标类型"""
        self.metric_type = metric_type
        
    def set_aggregation(self, aggregation: str):
        """设置聚合粒度"""
        self.aggregation = aggregation

    def get_data(self) -> Dict[str, Any]:
        """实现BaseDashboardService的抽象方法
        
        返回格式化的销售趋势数据
        """
        try:
            # 获取原始趋势数据
            raw_trend_data = self._get_sales_trend_data()
            
            # 计算汇总统计
            summary_stats = self._calculate_summary_stats(raw_trend_data)
            
            # 应用日期范围筛选
            filtered_data = self._apply_date_filter(raw_trend_data)
            
            # 数据聚合处理
            aggregated_data = self._apply_aggregation(filtered_data)
            
            return {
                'trend_data': aggregated_data,
                'summary_stats': summary_stats,
                'total_data_points': len(aggregated_data),
                'date_range': self._get_actual_date_range(aggregated_data),
                'applied_filters': self._get_applied_filters()
            }
            
        except Exception as e:
            logger.error(f"Error getting sales trend data: {e}")
            raise
    
    def _get_sales_trend_data(self) -> List[Dict[str, Any]]:
        """获取原始销售趋势数据
        
        目前使用Mock数据，实际实现时应该查询sales_trend_data表
        """
        # TODO: 实际实现应该查询数据库
        # 这里使用Mock数据演示数据结构
        
        mock_data = [
            {"date": "2024-07-19", "estimated_units_sold": 53, "last_known_price": 3.5},
            {"date": "2024-07-20", "estimated_units_sold": 45, "last_known_price": 3.5},
            {"date": "2024-07-21", "estimated_units_sold": 66, "last_known_price": 3.5},
            {"date": "2024-07-22", "estimated_units_sold": 37, "last_known_price": 3.5},
            {"date": "2024-07-23", "estimated_units_sold": 46, "last_known_price": 3.5},
            # 更多数据...
        ]
        
        # 计算estimated_revenue
        for item in mock_data:
            item['estimated_revenue'] = item['estimated_units_sold'] * item['last_known_price']
        
        logger.info(f"Retrieved {len(mock_data)} mock trend data points")
        return mock_data
        
        # 实际数据库查询代码（注释掉的实现示例）：
        """
        query = self.supabase.table('sales_trend_data').select(
            'date, estimated_units_sold, last_known_price, asin'
        )
        
        # 应用ASIN过滤
        if self.target_asin:
            query = query.eq('asin', self.target_asin)
        else:
            # 使用项目ASIN列表筛选
            query = query.in_('asin', self.project_asins)
        
        # 应用其他筛选条件
        query = self._apply_combined_filters(query)
        
        # 按日期排序
        query = query.order('date', desc=False)
        
        result = query.execute()
        
        if not result.data:
            logger.warning(f"No sales trend data found for project {self.project_id}")
            return []
        
        # 计算estimated_revenue
        for item in result.data:
            item['estimated_revenue'] = item['estimated_units_sold'] * item['last_known_price']
        
        logger.info(f"Retrieved {len(result.data)} trend data points")
        return result.data
        """
    
    def _apply_date_filter(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用日期范围筛选"""
        if not self.date_range_filter["start_date"] and not self.date_range_filter["end_date"]:
            return data
        
        filtered_data = []
        for item in data:
            item_date = item['date']
            
            # 检查开始日期
            if self.date_range_filter["start_date"]:
                if item_date < self.date_range_filter["start_date"]:
                    continue
            
            # 检查结束日期
            if self.date_range_filter["end_date"]:
                if item_date > self.date_range_filter["end_date"]:
                    continue
            
            filtered_data.append(item)
        
        logger.info(f"Date filtering: {len(data)} -> {len(filtered_data)} data points")
        return filtered_data
    
    def _apply_aggregation(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用数据聚合（日、周、月）
        
        目前只实现daily，weekly和monthly聚合可在后续添加
        """
        if self.aggregation == "daily":
            return data
        
        # TODO: 实现weekly和monthly聚合
        logger.warning(f"Aggregation {self.aggregation} not implemented, using daily")
        return data
    
    def _calculate_summary_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算汇总统计信息"""
        if not data:
            return self._get_empty_summary_stats()
        
        # 提取数值
        sales_values = [item['estimated_units_sold'] for item in data]
        price_values = [item['last_known_price'] for item in data]
        revenue_values = [item['estimated_revenue'] for item in data]
        
        # 计算统计指标
        total_sales = sum(sales_values)
        average_daily_sales = statistics.mean(sales_values)
        average_price = statistics.mean(price_values)
        price_volatility = statistics.stdev(price_values) if len(price_values) > 1 else 0.0
        total_revenue = sum(revenue_values)
        
        # 计算增长率（期末vs期初）
        growth_rate = None
        if len(sales_values) >= 2:
            initial_sales = sales_values[0]
            final_sales = sales_values[-1]
            if initial_sales > 0:
                growth_rate = ((final_sales - initial_sales) / initial_sales) * 100
        
        return {
            'total_period_sales': total_sales,
            'average_daily_sales': round(average_daily_sales, 2),
            'average_price': round(average_price, 2),
            'price_volatility': round(price_volatility, 2),
            'total_revenue': round(total_revenue, 2),
            'growth_rate': round(growth_rate, 2) if growth_rate is not None else None
        }
    
    def _get_empty_summary_stats(self) -> Dict[str, Any]:
        """返回空的统计数据"""
        return {
            'total_period_sales': 0,
            'average_daily_sales': 0.0,
            'average_price': 0.0,
            'price_volatility': 0.0,
            'total_revenue': 0.0,
            'growth_rate': None
        }
    
    def _get_actual_date_range(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """获取实际的数据日期范围"""
        if not data:
            return {"start_date": "", "end_date": ""}
        
        dates = [item['date'] for item in data]
        return {
            "start_date": min(dates),
            "end_date": max(dates)
        }
    
    def _get_applied_filters(self) -> Dict[str, Any]:
        """获取实际应用的筛选条件"""
        filters = {}
        
        if self.target_asin:
            filters['asin'] = self.target_asin
        
        if self.date_range_filter["start_date"] or self.date_range_filter["end_date"]:
            filters['date_range'] = self.date_range_filter
        
        # 添加标准筛选条件
        if self.project_filters and not self.project_filters.is_empty():
            filters.update(self.project_filters.to_dict())
        
        return filters 