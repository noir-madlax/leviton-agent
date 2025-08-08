"""Sales trend service for brand monthly sales analysis."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict

from dashboard.services.base_service import BaseDashboardService
from dashboard.models import MonthlySalesRecord
from dashboard.charts.base_service import ChartsBaseService
from core.models.filters import ProjectFilters
from dashboard.charts.filters.asin_filter_service import get_filtered_asins
from .models import (
    BrandSalesTrendRequest, BrandSalesTrendResponse, BrandSalesTrendMetadata, 
    CategorySalesTrendData, CategorySalesTrendSummary, OverallSummary
)

logger = logging.getLogger(__name__)

class SalesTrendService(BaseDashboardService):
    """销售趋势分析服务
    
    提供品牌月度销售趋势数据，支持revenue和volume双指标，
    数据来源：product_sales_history_monthly + product_wide_table
    """
    
    def __init__(self, project_id: str, filters: Optional[Dict[str, Any]] = None, date_range: Optional[Dict[str, str]] = None):
        """初始化服务
        
        Args:
            project_id: 项目ID 
            filters: 过滤条件（categories, brands, segments, extend_fields）
            date_range: 时间范围 {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
        """
        super().__init__(project_id)
        
        # 设置筛选器
        if filters:
            project_filters = ProjectFilters.from_dict(filters)
            self.set_project_filters(project_filters)
        
        # 设置时间范围
        self.date_range = date_range or {}
        
        logger.info(f"SalesTrendService initialized for project {project_id} with {len(self.project_asins)} ASINs")
    
    def get_data(self) -> Dict[str, Any]:
        """获取销售趋势数据
        
        Returns:
            Dict包含trend_data, brands, summary三个字段
        """
        try:
            # 1. 获取过滤后的ASIN列表
            filtered_asins = self._get_filtered_asins()
            if not filtered_asins:
                return self._get_empty_response()
            
            # 2. 获取ASIN到品牌的映射
            asin_brand_mapping = self._get_asin_brand_mapping(filtered_asins)
            if not asin_brand_mapping:
                return self._get_empty_response()
            
            # 3. 查询月度销售数据
            monthly_sales_data = self._query_monthly_sales(filtered_asins)
            if not monthly_sales_data:
                return self._get_empty_response()
            
            # 4. 按品牌和月份聚合数据
            brand_month_data = self._aggregate_by_brand_month(monthly_sales_data, asin_brand_mapping)
            
            # 5. 获取Top 10品牌（按总revenue排序）
            top_brands = self._get_top_brands(brand_month_data, limit=10)
            
            # 6. 格式化响应数据
            return self._format_response(brand_month_data, top_brands)
            
        except Exception as e:
            logger.error(f"Error in SalesTrendService.get_data(): {e}", exc_info=True)
            return self._get_empty_response()
    
    def _get_filtered_asins(self) -> List[str]:
        """获取应用所有过滤条件后的ASIN列表"""
        try:
            # 构建查询：获取platform_id字段
            query = self._get_base_product_table().select('platform_id')
            
            # 应用所有过滤条件（ASIN + category + brand + segments + extend_fields）
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            filtered_asins = [item['platform_id'] for item in result.data] if result.data else []
            logger.info(f"Filtered ASINs: {len(filtered_asins)} products match all filters")
            
            return filtered_asins
            
        except Exception as e:
            logger.error(f"Error getting filtered ASINs: {e}")
            return []
    
    def _get_asin_brand_mapping(self, asins: List[str]) -> Dict[str, str]:
        """获取ASIN到品牌的映射
        
        Args:
            asins: ASIN列表
            
        Returns:
            Dict[asin, brand] 映射
        """
        try:
            # 查询产品品牌信息
            query = self._get_base_product_table().select('platform_id, brand').in_('platform_id', asins)
            query = self._apply_base_filters(query)  # 基础过滤（source=amazon, brand!=null）
            
            result = query.execute()
            
            asin_brand_mapping = {}
            if result.data:
                for item in result.data:
                    asin = item['platform_id']
                    brand = item.get('brand')
                    if brand and brand.strip():
                        asin_brand_mapping[asin] = brand.strip()
            
            logger.info(f"ASIN-Brand mapping: {len(asin_brand_mapping)} products have valid brands")
            return asin_brand_mapping
            
        except Exception as e:
            logger.error(f"Error getting ASIN-brand mapping: {e}")
            return {}
    
    def _query_monthly_sales(self, asins: List[str]) -> List[Dict[str, Any]]:
        """查询月度销售数据
        
        Args:
            asins: ASIN列表
            
        Returns:
            List of monthly sales records
        """
        try:
            all_sales_data = []
            page = 0
            page_size = 1000  # Supabase's default limit

            while True:
                range_from = page * page_size
                range_to = range_from + page_size - 1
                
                # 构建基础查询
                query = self.supabase.table('product_sales_history_monthly').select(
                    'platform_id, year_month, total_units_sold, average_price'
                ).in_('platform_id', asins).eq('platform_source', 'amazon')
                
                # 应用时间范围过滤
                start_date = self.date_range.get('start_date')
                end_date = self.date_range.get('end_date') 
                
                if start_date:
                    # 转换为月份第一天格式
                    start_month = datetime.strptime(start_date, '%Y-%m-%d').replace(day=1).date()
                    query = query.gte('year_month', start_month.isoformat())
                
                if end_date:
                    # 转换为月份第一天格式
                    end_month = datetime.strptime(end_date, '%Y-%m-%d').replace(day=1).date()
                    query = query.lte('year_month', end_month.isoformat())
                
                # 按时间排序
                query = query.order('year_month', desc=False)
                
                # 使用 .range() 进行分页
                query = query.range(range_from, range_to)

                result = query.execute()

                if not result.data:
                    break

                all_sales_data.extend(result.data)

                if len(result.data) < page_size:
                    break
                
                page += 1

            logger.info(f"Monthly sales data: {len(all_sales_data)} records found after pagination")
            return all_sales_data
            
        except Exception as e:
            logger.error(f"Error querying monthly sales with pagination: {e}")
            return []
    
    def _aggregate_by_brand_month(self, sales_data: List[Dict[str, Any]], asin_brand_mapping: Dict[str, str]) -> Dict[str, Dict[str, Dict[str, float]]]:
        """按品牌和月份聚合销售数据
        
        Args:
            sales_data: 月度销售原始数据
            asin_brand_mapping: ASIN到品牌映射
            
        Returns:
            Dict[brand][month] = {"revenue": float, "volume": int}
        """
        # 初始化聚合数据结构
        brand_month_data = defaultdict(lambda: defaultdict(lambda: {"revenue": 0.0, "volume": 0}))
        
        for record in sales_data:
            asin = record['platform_id']
            brand = asin_brand_mapping.get(asin)
            
            if not brand:
                continue  # 跳过没有品牌信息的产品
            
            # 提取月份（转换为YYYY-MM格式）
            year_month_str = record['year_month']
            if isinstance(year_month_str, str):
                month = year_month_str[:7]  # "2024-01-01" -> "2024-01"
            else:
                month = year_month_str.strftime('%Y-%m')
            
            # 计算指标
            volume = record.get('total_units_sold', 0) or 0
            price = record.get('average_price', 0) or 0
            revenue = volume * price
            
            # 聚合到品牌+月份
            brand_month_data[brand][month]["revenue"] += revenue
            brand_month_data[brand][month]["volume"] += volume
        
        # 转换为普通dict并保留整数类型的volume
        result = {}
        for brand, months in brand_month_data.items():
            result[brand] = {}
            for month, metrics in months.items():
                result[brand][month] = {
                    "revenue": float(metrics["revenue"]),
                    "volume": int(metrics["volume"])
                }
        
        logger.info(f"Aggregated data: {len(result)} brands across {len(set().union(*[months.keys() for months in result.values()])) if result else 0} months")
        return result
    
    def _get_top_brands(self, brand_month_data: Dict[str, Dict[str, Dict[str, float]]], limit: int = 10) -> List[str]:
        """获取Top N品牌（按总revenue排序）
        
        Args:
            brand_month_data: 品牌月度聚合数据
            limit: 返回品牌数量限制
            
        Returns:
            List of top brand names
        """
        # 计算每个品牌的总revenue
        brand_totals = []
        for brand, months in brand_month_data.items():
            total_revenue = sum(metrics["revenue"] for metrics in months.values())
            brand_totals.append((brand, total_revenue))
        
        # 按总revenue降序排序，取前N个
        brand_totals.sort(key=lambda x: x[1], reverse=True)
        top_brands = [brand for brand, _ in brand_totals[:limit]]
        
        logger.info(f"Top {limit} brands by revenue: {top_brands}")
        return top_brands
    
    def _format_response(self, brand_month_data: Dict[str, Dict[str, Dict[str, float]]], top_brands: List[str]) -> Dict[str, Any]:
        """格式化响应数据为API期望的格式
        
        Args:
            brand_month_data: 品牌月度聚合数据
            top_brands: Top品牌列表
            
        Returns:
            格式化的响应数据
        """
        # 收集所有月份并排序
        all_months = set()
        for brand_data in brand_month_data.values():
            all_months.update(brand_data.keys())
        sorted_months = sorted(list(all_months))
        
        # 构建trend_data: 每个月份包含所有top品牌的数据
        trend_data = []
        for month in sorted_months:
            month_data = {"month": month}
            
            # 添加每个top品牌的数据
            for brand in top_brands:
                if brand in brand_month_data and month in brand_month_data[brand]:
                    month_data[brand] = brand_month_data[brand][month]
                else:
                    # 如果该品牌在该月没有数据，设为0
                    month_data[brand] = {"revenue": 0.0, "volume": 0}
            
            trend_data.append(month_data)
        
        # 计算汇总统计
        total_revenue = sum(
            sum(metrics["revenue"] for metrics in months.values())
            for months in brand_month_data.values()
        )
        total_volume = sum(
            sum(metrics["volume"] for metrics in months.values())
            for months in brand_month_data.values()
        )
        
        # 构建响应
        response = {
            "trend_data": trend_data,
            "brands": top_brands,
            "summary": {
                "total_brands": len(top_brands),
                "date_range": {
                    "start": sorted_months[0] if sorted_months else "",
                    "end": sorted_months[-1] if sorted_months else ""
                },
                "total_revenue": float(total_revenue),
                "total_volume": int(total_volume)
            }
        }
        
        logger.info(f"Response formatted: {len(trend_data)} months, {len(top_brands)} brands")
        return response
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空响应数据"""
        return {
            "trend_data": [],
            "brands": [],
            "summary": {
                "total_brands": 0,
                "date_range": {"start": "", "end": ""},
                "total_revenue": 0.0,
                "total_volume": 0
            }
        }


# ==================== 新版本Service（支持timeframe） ====================

class BrandSalesTrendService(ChartsBaseService):
    """品牌销售趋势分析服务 - 支持timeframe模式
    
    新版本服务，使用timeframe替代date_range，
    未来将支持基于timeframe的实际时间范围查询
    """
    
    def __init__(self, supabase_client):
        """初始化服务
        
        Args:
            supabase_client: Supabase客户端实例
        """
        super().__init__(supabase_client)
    
    def get_brand_sales_trend_data(self, request: BrandSalesTrendRequest) -> BrandSalesTrendResponse:
        """获取品牌销售趋势数据
        
        Args:
            request: 品牌销售趋势请求
            
        Returns:
            BrandSalesTrendResponse: 完整的趋势分析数据
        """
        try:
            logger.info(f"🏢 Starting Brand Sales Trend analysis for project {request.project_id}")
            
            # Step 1: 获取过滤后的ASIN列表
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: 获取ASIN到品牌和category的映射
            asin_mapping = self._get_asin_brand_category_mapping(filtered_asins)
            if not asin_mapping:
                return self._get_empty_response(request)
            
            # Step 3: 查询月度销售数据 (暂时使用固定时间范围，后续支持timeframe)
            monthly_sales_data = self.query_monthly_sales_with_timeframe(filtered_asins, request.timeframe)
            if not monthly_sales_data:
                return self._get_empty_response(request)
            
            # Step 4: 按category、品牌和月份聚合数据
            category_brand_month_data = self._aggregate_by_category_brand_month(monthly_sales_data, asin_mapping)
            
            # Step 5: 格式化响应数据
            return self._format_response(category_brand_month_data, request)
            
        except Exception as e:
            logger.error(f"Error in BrandSalesTrendService.get_brand_sales_trend_data(): {e}", exc_info=True)
            return self._get_empty_response(request)
    
    def _get_asin_brand_category_mapping(self, asins: List[str]) -> Dict[str, Dict[str, str]]:
        """获取ASIN到品牌和category的映射"""
        try:
            # 查询产品品牌和category信息
            query = (self.supabase.table('product_wide_table')
                    .select('platform_id, brand, category')
                    .in_('platform_id', asins)
                    .eq('source', 'amazon')
                    .not_.is_('brand', 'null')
                    .not_.is_('category', 'null'))
            
            result = query.execute()
            
            asin_mapping = {}
            if result.data:
                for item in result.data:
                    asin = item['platform_id']
                    brand = item.get('brand')
                    category = item.get('category')
                    if brand and brand.strip() and category and category.strip():
                        asin_mapping[asin] = {
                            'brand': brand.strip(),
                            'category': category.strip()
                        }
            
            logger.info(f"ASIN-Brand-Category mapping: {len(asin_mapping)} products have valid data")
            return asin_mapping
            
        except Exception as e:
            logger.error(f"Error getting ASIN-brand-category mapping: {e}")
            return {}
    
    
    def _aggregate_by_category_brand_month(self, sales_data: List["MonthlySalesRecord"], asin_mapping: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Dict[str, Dict[str, float]]]]:
        """按category、品牌和月份聚合销售数据
        
        Args:
            sales_data: 月度销售原始数据
            asin_mapping: ASIN到品牌和category的映射
            
        Returns:
            Dict[category][brand][month] = {"revenue": float, "volume": int}
        """
        # 初始化聚合数据结构
        category_brand_month_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"revenue": 0.0, "volume": 0})))
        
        for record in sales_data:
            asin = record.platform_id
            mapping = asin_mapping.get(asin)
            
            if not mapping:
                continue  # 跳过没有品牌或category信息的产品
            
            brand = mapping['brand']
            category = mapping['category']
            
            # 提取月份（转换为YYYY-MM格式）
            year_month_val = record.year_month
            if isinstance(year_month_val, str):
                month = year_month_val[:7]
            else:
                month = year_month_val.strftime('%Y-%m')
            
            # 计算指标
            volume = getattr(record, 'total_units_sold', 0) or 0
            price = getattr(record, 'average_price', 0) or 0
            revenue = volume * price
            
            # 聚合到category+品牌+月份
            category_brand_month_data[category][brand][month]["revenue"] += revenue
            category_brand_month_data[category][brand][month]["volume"] += volume
        
        # 转换为普通dict并保留整数类型的volume
        result = {}
        for category, brand_data in category_brand_month_data.items():
            result[category] = {}
            for brand, months in brand_data.items():
                result[category][brand] = {}
                for month, metrics in months.items():
                    result[category][brand][month] = {
                        "revenue": float(metrics["revenue"]),
                        "volume": int(metrics["volume"])
                    }
        
        logger.info(f"Aggregated data: {len(result)} categories, {sum(len(brands) for brands in result.values())} brands total")
        return result
    
    def _get_top_brands_by_category(self, category_brand_month_data: Dict[str, Dict[str, Dict[str, Dict[str, float]]]], metric_type: str, limit: int = 10) -> Dict[str, List[str]]:
        """获取每个category的Top N品牌（按指定指标排序）
        
        Args:
            category_brand_month_data: 按category分组的品牌月度聚合数据
            metric_type: 排序指标类型（revenue或volume）
            limit: 每个category返回的品牌数量限制
            
        Returns:
            Dict[category] = List[top_brand_names]
        """
        top_brands_by_category = {}
        
        for category, brand_month_data in category_brand_month_data.items():
            # 计算每个品牌的总指标值
            brand_totals = []
            for brand, months in brand_month_data.items():
                if metric_type == "revenue":
                    total_value = sum(metrics["revenue"] for metrics in months.values())
                else:  # volume
                    total_value = sum(metrics["volume"] for metrics in months.values())
                brand_totals.append((brand, total_value))
            
            # 按总指标值降序排序，取前N个
            brand_totals.sort(key=lambda x: x[1], reverse=True)
            top_brands = [brand for brand, _ in brand_totals[:limit]]
            
            top_brands_by_category[category] = top_brands
            logger.info(f"Top {limit} brands in {category} by {metric_type}: {top_brands}")
        
        return top_brands_by_category
    
    def _format_response(self, category_brand_month_data: Dict[str, Dict[str, Dict[str, Dict[str, float]]]], request: BrandSalesTrendRequest) -> BrandSalesTrendResponse:
        """格式化响应数据为多category API格式
        
        Args:
            category_brand_month_data: 按category分组的品牌月度聚合数据
            request: 原始请求对象
            
        Returns:
            格式化的多category响应数据
        """
        # 获取每个category的Top品牌
        top_brands_by_category = self._get_top_brands_by_category(category_brand_month_data, request.metric_type, request.limit)
        
        # 收集所有月份并排序
        all_months = set()
        for category_data in category_brand_month_data.values():
            for brand_data in category_data.values():
                all_months.update(brand_data.keys())
        sorted_months = sorted(list(all_months))
        
        # 构建categories_data
        categories_data = {}
        overall_revenue = 0.0
        overall_volume = 0
        all_brands_set = set()
        
        for category, brand_month_data in category_brand_month_data.items():
            top_brands = top_brands_by_category.get(category, [])
            
            # 构建该category的trend_data
            trend_data = []
            for month in sorted_months:
                month_data = {"month": month}
                
                # 添加每个top品牌的数据
                for brand in top_brands:
                    if brand in brand_month_data and month in brand_month_data[brand]:
                        month_data[brand] = brand_month_data[brand][month]
                    else:
                        # 如果该品牌在该月没有数据，设为0
                        month_data[brand] = {"revenue": 0.0, "volume": 0}
                
                trend_data.append(month_data)
            
            # 计算该category的汇总统计
            category_revenue = sum(
                sum(metrics["revenue"] for metrics in months.values())
                for months in brand_month_data.values()
            )
            category_volume = sum(
                sum(metrics["volume"] for metrics in months.values())
                for months in brand_month_data.values()
            )
            
            # 构建该category的数据
            categories_data[category] = CategorySalesTrendData(
                trend_data=trend_data,
                brands=top_brands,
                summary=CategorySalesTrendSummary(
                    total_brands=len(top_brands),
                    date_range={
                        "start": sorted_months[0] if sorted_months else "",
                        "end": sorted_months[-1] if sorted_months else ""
                    },
                    total_revenue=float(category_revenue),
                    total_volume=int(category_volume),
                    timeframe_period=request.timeframe.period if request.timeframe else "year"
                )
            )
            
            # 累加到全局统计
            overall_revenue += category_revenue
            overall_volume += category_volume
            all_brands_set.update(top_brands)
        
        # 构建overall_summary
        overall_summary = OverallSummary(
            total_categories=len(categories_data),
            all_brands=sorted(list(all_brands_set)),
            total_revenue=float(overall_revenue),
            total_volume=int(overall_volume),
            date_range={
                "start": sorted_months[0] if sorted_months else "",
                "end": sorted_months[-1] if sorted_months else ""
            },
            timeframe_period=request.timeframe.period if request.timeframe else "year"
        )
        
        # 构建metadata
        metadata = BrandSalesTrendMetadata(
            filtered_asins_count=sum(len(brand_data) for category_data in category_brand_month_data.values() for brand_data in category_data.values()),
            calculation_timestamp=datetime.now().isoformat(),
            timeframe_used=request.timeframe.period if request.timeframe else "year",
            categories_processed=list(categories_data.keys())
        )
        
        # 构建最终响应
        response = BrandSalesTrendResponse(
            categories_data=categories_data,
            overall_summary=overall_summary,
            metadata=metadata
        )
        
        logger.info(f"Response formatted: {len(categories_data)} categories, {len(all_brands_set)} unique brands, {len(sorted_months)} months")
        return response
    
    def _get_empty_response(self, request: BrandSalesTrendRequest) -> BrandSalesTrendResponse:
        """返回空响应数据"""
        return BrandSalesTrendResponse(
            categories_data={},
            overall_summary=OverallSummary(
                total_categories=0,
                all_brands=[],
                total_revenue=0.0,
                total_volume=0,
                date_range={"start": "", "end": ""},
                timeframe_period=request.timeframe.period if request.timeframe else "year"
            ),
            metadata=BrandSalesTrendMetadata(
                filtered_asins_count=0,
                calculation_timestamp=datetime.now().isoformat(),
                timeframe_used=request.timeframe.period if request.timeframe else "year",
                categories_processed=[]
            )
        ) 