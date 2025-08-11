"""Price Distribution Analysis services for dashboard."""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from dashboard.services.base_service import BaseDashboardService
from core.models.filters import ProjectFilters
from dashboard.charts.filters.asin_filter_service import get_filtered_asins
from dashboard.charts.base_service import ChartsBaseService
from .models import (
    PriceDistributionRequest, PriceDistributionResponse, PriceDistributionMetadata,
    PriceVsRevenueRequest, PriceVsRevenueResponse,
    BrandPriceDistributionRequest, BrandPriceDistributionResponse,
    PriceDistributionOverviewRequest, PriceDistributionOverviewResponse, PriceDistributionOverviewData,
    CategoryPriceData, CategoryBrandDistribution, BrandPriceData, PriceStatistics,
    TopProductsData, ProductDetail
)

logger = logging.getLogger(__name__)

# ==================== 共享基础服务类 ====================

class BasePricingService:
    """价格分析服务基类 - 包含共享的数据获取和处理方法"""
    
    def __init__(self, supabase_client):
        """初始化服务
        
        Args:
            supabase_client: Supabase客户端实例
        """
        self.supabase = supabase_client
    
    def _get_product_pricing_data(self, asins: List[str]) -> List[Dict[str, Any]]:
        """获取产品价格和分类数据
        
        Args:
            asins: ASIN列表
            
        Returns:
            List of product data with pricing and category information
        """
        try:
            all_products_data = []
            page = 0
            page_size = 1000

            while True:
                range_from = page * page_size
                range_to = range_from + page_size - 1
                
                # 构建基础查询
                query = (self.supabase.table('product_wide_table')
                        .select('platform_id, title, brand, price_usd, unit_price_calculated, category, past_year_revenue, past_year_volume, product_url')
                        .in_('platform_id', asins)
                        .eq('source', 'amazon')
                        .not_.is_('price_usd', 'null')
                        .not_.is_('unit_price_calculated', 'null')
                        .range(range_from, range_to))

                response = query.execute()
                
                if not response.data:
                    break
                
                all_products_data.extend(response.data)
                
                # 检查是否还有更多数据
                if len(response.data) < page_size:
                    break
                
                page += 1

            logger.info(f"📊 Retrieved {len(all_products_data)} product records with pricing data")
            return all_products_data
            
        except Exception as e:
            logger.error(f"Error fetching product pricing data: {e}", exc_info=True)
            return []

    def _calculate_price_statistics(self, prices: List[float]) -> PriceStatistics:
        """计算价格统计信息"""
        if not prices:
            return PriceStatistics(min=0, q1=0, median=0, mean=0, q3=0, max=0)
        
        prices_array = np.array(prices)
        return PriceStatistics(
            min=float(np.min(prices_array)),
            q1=float(np.percentile(prices_array, 25)),
            median=float(np.median(prices_array)),
            mean=float(np.mean(prices_array)),
            q3=float(np.percentile(prices_array, 75)),
            max=float(np.max(prices_array))
        )
    
    def _generate_metadata(self, filtered_asins_count: int, categories_processed: List[str]) -> PriceDistributionMetadata:
        """生成分析元数据"""
        return PriceDistributionMetadata(
            filtered_asins_count=filtered_asins_count,
            calculation_timestamp=datetime.now().isoformat(),
            timeframe_used="year",
            data_source="product_wide_table",
            categories_processed=categories_processed
        )

# ==================== 价格分布服务 (按产品类型) ====================

class PriceDistributionService(BasePricingService):
    """价格分布分析服务 - 专门用于按产品类型的价格分布图表"""
    
    def get_price_distribution_data(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        """获取价格分布数据
        
        Args:
            request: 价格分布请求
            
        Returns:
            PriceDistributionResponse: 价格分布数据
        """
        try:
            logger.info(f"💰 Starting Price Distribution analysis for project {request.project_id}")
            
            # Step 1: 获取过滤后的ASIN列表
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: 获取产品价格和分类数据
            products_data = self._get_product_pricing_data(filtered_asins)
            if not products_data:
                return self._get_empty_response(request)
            
            # Step 3: 按分类分组并计算价格分布
            category_price_data = self._calculate_category_price_distributions(products_data)
            
            # Step 4: 生成分类名称和颜色
            segment_names = [cat.category for cat in category_price_data]
            segment_colors = self._generate_colors(len(segment_names))
            
            # Step 5: 生成元数据
            metadata = self._generate_metadata(len(filtered_asins), segment_names)
            
            return PriceDistributionResponse(
                priceDistribution=category_price_data,
                segmentNames=segment_names,
                segmentColors=segment_colors,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in PriceDistributionService: {e}", exc_info=True)
            return self._get_empty_response(request)

    def _calculate_category_price_distributions(self, products_data: List[Dict[str, Any]]) -> List[CategoryPriceData]:
        """按分类计算价格分布"""
        category_groups = defaultdict(list)
        
        # 按分类分组产品
        for product in products_data:
            category = product.get('category', 'Unknown')
            if category:
                category_groups[category].append(product)
        
        category_price_data = []
        for category, products in category_groups.items():
            sku_prices = [float(p['price_usd']) for p in products if p.get('price_usd')]
            unit_prices = [float(p['unit_price_calculated']) for p in products if p.get('unit_price_calculated')]
            
            # 计算统计信息
            stats = {
                'sku': self._calculate_price_statistics(sku_prices),
                'unit': self._calculate_price_statistics(unit_prices)
            }
            
            category_data = CategoryPriceData(
                category=category,
                skuPrices=sku_prices,
                unitPrices=unit_prices,
                productCount=len(products),
                stats=stats
            )
            category_price_data.append(category_data)
        
        return category_price_data

    def _get_empty_response(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        """返回空响应"""
        return PriceDistributionResponse(
            priceDistribution=[],
            segmentNames=[],
            segmentColors=[],
            metadata=self._generate_metadata(0, [])
        )

    def _generate_colors(self, count: int) -> List[str]:
        """生成颜色列表"""
        base_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFA07A', '#98D8C8']
        return (base_colors * ((count // len(base_colors)) + 1))[:count]

# ==================== 价格收入散点图服务 ====================

class PriceVsRevenueService(BasePricingService, ChartsBaseService):
    """价格收入散点图分析服务"""
    
    def get_price_vs_revenue_data(self, request: PriceVsRevenueRequest) -> PriceVsRevenueResponse:
        """获取价格收入散点图数据
        
        Args:
            request: 价格收入请求
            
        Returns:
            PriceVsRevenueResponse: 散点图数据
        """
        try:
            logger.info(f"📈 Starting Price vs Revenue analysis for project {request.project_id}")
            
            # Step 1: 获取过滤后的ASIN列表
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: 获取产品数据（包含收入信息，改为基于月度明细聚合）
            products_data = self._get_product_pricing_data_with_aggregates(filtered_asins, request.timeframe)
            if not products_data:
                return self._get_empty_response(request)
            
            # Step 3: 生成Top产品数据（用于散点图）
            top_products_data = self._generate_top_products_data(products_data)
            
            # Step 4: 生成分类名称和颜色
            segment_names = list(top_products_data.segments.keys())
            segment_colors = self._generate_colors(len(segment_names))
            
            # Step 5: 生成元数据
            metadata = self._generate_metadata(len(filtered_asins), segment_names)
            
            return PriceVsRevenueResponse(
                topProducts=top_products_data,
                segmentNames=segment_names,
                segmentColors=segment_colors,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in PriceVsRevenueService: {e}", exc_info=True)
            return self._get_empty_response(request)

    def _get_product_pricing_data_with_aggregates(self, asins: List[str], timeframe=None) -> List[Dict[str, Any]]:
        """获取产品价格、分类数据，并基于月度明细聚合得到收入与销量。
        
        返回的字段与现有下游一致：
        - platform_id, title, brand, price_usd, unit_price_calculated, category, product_url
        - past_year_revenue: 聚合的 total_revenue
        - past_year_volume: 聚合的 total_units_sold
        """
        try:
            # 1) 聚合月度销售（每个 ASIN 一行）
            aggregates = self.query_monthly_sales_aggregate_with_timeframe(asins, timeframe)
            if not aggregates:
                return []

            # 2) 取 wide 表的基础信息
            wide_query = (
                self.supabase
                .table('product_wide_table')
                .select('platform_id, title, brand, price_usd, unit_price_calculated, category, product_url')
                .in_('platform_id', [a.platform_id for a in aggregates])
                .eq('source', 'amazon')
            )
            wide_result = wide_query.execute()
            if not wide_result.data:
                return []

            # 3) 合并
            agg_map = {a.platform_id: a for a in aggregates}
            products: List[Dict[str, Any]] = []
            for row in wide_result.data:
                asin = row.get('platform_id')
                agg = agg_map.get(asin)
                if not agg:
                    continue
                price_usd_val = row.get('price_usd')
                unit_price_val = row.get('unit_price_calculated')
                products.append({
                    'platform_id': asin,
                    'title': row.get('title'),
                    'brand': row.get('brand'),
                    'price_usd': float(price_usd_val) if price_usd_val is not None else 0.0,
                    'unit_price_calculated': float(unit_price_val) if unit_price_val is not None else 0.0,
                    'category': row.get('category'),
                    'product_url': row.get('product_url'),
                    'past_year_revenue': float(getattr(agg, 'total_revenue', 0.0) or 0.0),
                    'past_year_volume': int(getattr(agg, 'total_units_sold', 0) or 0),
                })

            logger.info(f"📊 Retrieved {len(products)} products with aggregated revenue/volume from monthly sales")
            return products
        except Exception as e:
            logger.error(f"Error fetching product data with monthly aggregates: {e}")
            return []

    def _generate_top_products_data(self, products_data: List[Dict[str, Any]], limit_per_category: int = 20) -> TopProductsData:
        """生成Top产品数据"""
        category_groups = defaultdict(list)
        
        # 按分类分组并过滤有收入数据的产品
        for product in products_data:
            category = product.get('category', 'Unknown')
            revenue = product.get('past_year_revenue')
            
            if category and revenue and float(revenue) > 0:
                category_groups[category].append(product)
        
        # 为每个分类选取Top产品
        segments = {}
        dimmer_switches = []
        light_switches = []
        
        for category, products in category_groups.items():
            # 按收入排序，取Top产品
            sorted_products = sorted(products, key=lambda x: float(x.get('past_year_revenue', 0)), reverse=True)
            top_products = sorted_products[:limit_per_category]
            
            # 转换为ProductDetail对象
            product_details = []
            for product in top_products:
                detail = ProductDetail(
                    id=product['platform_id'],
                    name=product.get('title', 'Unknown'),
                    brand=product.get('brand', 'Unknown'),
                    price=float(product.get('price_usd', 0)),
                    unitPrice=float(product.get('unit_price_calculated', 0)),
                    revenue=float(product.get('past_year_revenue', 0)),
                    volume=float(product.get('past_year_volume', 0)),
                    url=product.get('product_url', '')
                )
                product_details.append(detail)
            
            segments[category] = product_details
            
            # 兼容性字段
            if 'dimmer' in category.lower():
                dimmer_switches.extend(product_details)
            elif 'switch' in category.lower():
                light_switches.extend(product_details)
        
        return TopProductsData(
            segments=segments,
            dimmerSwitches=dimmer_switches,
            lightSwitches=light_switches
        )

    def _get_empty_response(self, request: PriceVsRevenueRequest) -> PriceVsRevenueResponse:
        """返回空响应"""
        return PriceVsRevenueResponse(
            topProducts=TopProductsData(segments={}, dimmerSwitches=[], lightSwitches=[]),
            segmentNames=[],
            segmentColors=[],
            metadata=self._generate_metadata(0, [])
        )

    def _generate_colors(self, count: int) -> List[str]:
        """生成颜色列表"""
        base_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFA07A', '#98D8C8']
        return (base_colors * ((count // len(base_colors)) + 1))[:count]

# ==================== 品牌价格分布服务 ====================

class BrandPriceDistributionService(BasePricingService):
    """品牌价格分布分析服务"""
    
    def get_brand_price_distribution_data(self, request: BrandPriceDistributionRequest) -> BrandPriceDistributionResponse:
        """获取品牌价格分布数据
        
        Args:
            request: 品牌价格分布请求
            
        Returns:
            BrandPriceDistributionResponse: 品牌价格分布数据
        """
        try:
            logger.info(f"🏷️ Starting Brand Price Distribution analysis for project {request.project_id}")
            
            # Step 1: 获取过滤后的ASIN列表
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: 获取产品价格和分类数据
            products_data = self._get_product_pricing_data(filtered_asins)
            if not products_data:
                return self._get_empty_response(request)
            
            # Step 3: 计算品牌价格分布
            brand_price_distributions = self._calculate_brand_price_distributions(products_data)
            
            # Step 4: 生成分类名称和颜色
            segment_names = [cat.category for cat in brand_price_distributions]
            segment_colors = self._generate_colors(len(segment_names))
            
            # Step 5: 生成元数据
            metadata = self._generate_metadata(len(filtered_asins), segment_names)
            
            return BrandPriceDistributionResponse(
                brandPriceDistribution=brand_price_distributions,
                segmentNames=segment_names,
                segmentColors=segment_colors,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in BrandPriceDistributionService: {e}", exc_info=True)
            return self._get_empty_response(request)

    def _calculate_brand_price_distributions(self, products_data: List[Dict[str, Any]]) -> List[CategoryBrandDistribution]:
        """计算品牌价格分布"""
        category_groups = defaultdict(lambda: defaultdict(list))
        
        # 按分类和品牌分组产品
        for product in products_data:
            category = product.get('category', 'Unknown')
            brand = product.get('brand', 'Unknown')
            if category and brand:
                category_groups[category][brand].append(product)
        
        brand_distributions = []
        for category, brand_groups in category_groups.items():
            brands_data = []
            
            for brand, products in brand_groups.items():
                sku_prices = [float(p['price_usd']) for p in products if p.get('price_usd')]
                unit_prices = [float(p['unit_price_calculated']) for p in products if p.get('unit_price_calculated')]
                
                brand_data = BrandPriceData(
                    name=brand,
                    skuPrices=sku_prices,
                    unitPrices=unit_prices
                )
                brands_data.append(brand_data)
            
            category_brand_dist = CategoryBrandDistribution(
                category=category,
                brands=brands_data
            )
            brand_distributions.append(category_brand_dist)
        
        return brand_distributions

    def _get_empty_response(self, request: BrandPriceDistributionRequest) -> BrandPriceDistributionResponse:
        """返回空响应"""
        return BrandPriceDistributionResponse(
            brandPriceDistribution=[],
            segmentNames=[],
            segmentColors=[],
            metadata=self._generate_metadata(0, [])
        )

    def _generate_colors(self, count: int) -> List[str]:
        """生成颜色列表"""
        base_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFA07A', '#98D8C8']
        return (base_colors * ((count // len(base_colors)) + 1))[:count]

# ==================== 价格分布概览服务 ====================

class PriceDistributionOverviewService(BasePricingService):
    """价格分布概览服务 - 生成统计表格数据，不使用过滤器"""
    
    def get_overview_data(self, request: PriceDistributionOverviewRequest) -> PriceDistributionOverviewResponse:
        """获取价格分布概览数据
        
        Args:
            request: 价格分布概览请求
            
        Returns:
            PriceDistributionOverviewResponse: 概览表格数据
        """
        try:
            logger.info(f"📊 Starting Price Distribution Overview analysis for project {request.project_id}")
            
            # Step 1: 获取项目的所有ASIN（不应用过滤器）
            # 创建一个不带过滤器的请求来获取所有产品
            from ..base_models import FiltersModel
            base_request = type('BaseRequest', (), {
                'project_id': request.project_id,
                'filters': FiltersModel(),  # 空过滤器
                'timeframe': request.timeframe
            })()
            
            all_asins = get_filtered_asins(self.supabase, base_request)
            
            if not all_asins:
                logger.warning(f"No ASINs found for project {request.project_id}")
                return self._get_empty_response(request)
            
            logger.info(f"📊 Found {len(all_asins)} total ASINs for project")
            
            # Step 2: 获取产品价格和分类数据
            products_data = self._get_product_pricing_data(all_asins)
            if not products_data:
                return self._get_empty_response(request)
            
            # Step 3: 按分类分组并计算概览统计
            overview_data = self._calculate_overview_statistics(products_data)
            
            # Step 4: 生成元数据
            segment_names = [item.segment for item in overview_data]
            metadata = self._generate_metadata(len(all_asins), segment_names)
            
            return PriceDistributionOverviewResponse(
                overview_data=overview_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in PriceDistributionOverviewService: {e}", exc_info=True)
            return self._get_empty_response(request)

    def _calculate_overview_statistics(self, products_data: List[Dict[str, Any]]) -> List[PriceDistributionOverviewData]:
        """计算概览统计数据"""
        category_groups = defaultdict(list)
        
        # 按分类分组产品
        for product in products_data:
            category = product.get('category', 'Unknown')
            if category:
                category_groups[category].append(product)
        
        overview_data = []
        for category, products in category_groups.items():
            # 使用unit_price_calculated作为主要价格
            unit_prices = [float(p['unit_price_calculated']) for p in products if p.get('unit_price_calculated')]
            
            if unit_prices:
                # 计算统计信息
                unit_prices_array = np.array(unit_prices)
                
                overview_item = PriceDistributionOverviewData(
                    segment=category,
                    products=len(products),
                    min_price=float(np.min(unit_prices_array)),
                    median_price=float(np.median(unit_prices_array)),
                    max_price=float(np.max(unit_prices_array)),
                    average_price=float(np.mean(unit_prices_array))
                )
                overview_data.append(overview_item)
        
        # 按产品数量降序排序
        overview_data.sort(key=lambda x: x.products, reverse=True)
        
        return overview_data

    def _get_empty_response(self, request: PriceDistributionOverviewRequest) -> PriceDistributionOverviewResponse:
        """返回空响应"""
        return PriceDistributionOverviewResponse(
            overview_data=[],
            metadata=self._generate_metadata(0, [])
        )