"""Price Distribution Analysis service for dashboard."""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from dashboard.services.base_service import BaseDashboardService
from core.models.filters import ProjectFilters
from dashboard.charts.filters.asin_filter_service import get_filtered_asins
from .models import (
    PriceDistributionRequest, PriceDistributionResponse, PriceDistributionMetadata,
    CategoryPriceData, CategoryBrandDistribution, BrandPriceData, PriceStatistics
)

logger = logging.getLogger(__name__)

class PriceDistributionService:
    """价格分布分析服务
    
    提供按分类的价格分布分析，包含统计计算和品牌价格分布
    数据来源：product_wide_table
    """
    
    def __init__(self, supabase_client):
        """初始化服务
        
        Args:
            supabase_client: Supabase客户端实例
        """
        self.supabase = supabase_client
    
    def get_price_distribution_data(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        """获取价格分布数据
        
        Args:
            request: 价格分布请求
            
        Returns:
            PriceDistributionResponse: 完整的价格分布数据
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
            
            # Step 4: 计算品牌价格分布
            brand_price_distributions = self._calculate_brand_price_distributions(products_data)
            
            # Step 5: 格式化响应数据
            return self._format_response(category_price_data, brand_price_distributions, request)
            
        except Exception as e:
            logger.error(f"Error in PriceDistributionService.get_price_distribution_data(): {e}", exc_info=True)
            return self._get_empty_response(request)
    
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
                        .select('platform_id, title, brand, price_usd, unit_price_calculated, category')
                        .in_('platform_id', asins)
                        .eq('source', 'amazon')
                        .not_.is_('price_usd', 'null')
                        .not_.is_('category', 'null')
                        .not_.is_('brand', 'null'))
                
                # 使用 .range() 进行分页
                query = query.range(range_from, range_to)
                result = query.execute()

                if not result.data:
                    break

                all_products_data.extend(result.data)

                if len(result.data) < page_size:
                    break
                
                page += 1

            logger.info(f"Product pricing data: {len(all_products_data)} records found with valid price and category")
            return all_products_data
            
        except Exception as e:
            logger.error(f"Error getting product pricing data: {e}")
            return []
    
    def _calculate_category_price_distributions(self, products_data: List[Dict[str, Any]]) -> List[CategoryPriceData]:
        """计算各分类的价格分布
        
        Args:
            products_data: 产品数据列表
            
        Returns:
            List of CategoryPriceData
        """
        # 按分类分组
        category_groups = defaultdict(list)
        for product in products_data:
            category = product.get('category')
            if category:
                category_groups[category].append(product)
        
        category_price_data = []
        
        for category, products in category_groups.items():
            # 提取价格数据
            sku_prices = []
            unit_prices = []
            
            for product in products:
                sku_price = product.get('price_usd')
                unit_price = product.get('unit_price_calculated')
                
                if sku_price and sku_price > 0:
                    sku_prices.append(float(sku_price))
                    
                if unit_price and unit_price > 0:
                    unit_prices.append(float(unit_price))
                elif sku_price and sku_price > 0:
                    # 如果没有单位价格，使用SKU价格作为备用
                    unit_prices.append(float(sku_price))
            
            if not sku_prices and not unit_prices:
                continue
            
            # 计算统计信息
            sku_stats = self._calculate_price_statistics(sku_prices) if sku_prices else None
            unit_stats = self._calculate_price_statistics(unit_prices) if unit_prices else None
            
            # 创建分类价格数据
            category_data = CategoryPriceData(
                category=category,
                skuPrices=sku_prices,
                unitPrices=unit_prices,
                productCount=len(products),
                stats={
                    "sku": sku_stats if sku_stats else PriceStatistics(min=0, q1=0, median=0, mean=0, q3=0, max=0),
                    "unit": unit_stats if unit_stats else PriceStatistics(min=0, q1=0, median=0, mean=0, q3=0, max=0)
                }
            )
            
            category_price_data.append(category_data)
        
        logger.info(f"Calculated price distributions for {len(category_price_data)} categories")
        return category_price_data
    
    def _calculate_brand_price_distributions(self, products_data: List[Dict[str, Any]]) -> List[CategoryBrandDistribution]:
        """计算各分类的品牌价格分布
        
        Args:
            products_data: 产品数据列表
            
        Returns:
            List of CategoryBrandDistribution
        """
        # 按分类和品牌分组
        category_brand_groups = defaultdict(lambda: defaultdict(list))
        
        for product in products_data:
            category = product.get('category')
            brand = product.get('brand')
            if category and brand:
                category_brand_groups[category][brand].append(product)
        
        brand_distributions = []
        
        for category, brand_groups in category_brand_groups.items():
            brands_data = []
            
            for brand, products in brand_groups.items():
                # 提取品牌的价格数据
                sku_prices = []
                unit_prices = []
                
                for product in products:
                    sku_price = product.get('price_usd')
                    unit_price = product.get('unit_price_calculated')
                    
                    if sku_price and sku_price > 0:
                        sku_prices.append(float(sku_price))
                        
                    if unit_price and unit_price > 0:
                        unit_prices.append(float(unit_price))
                    elif sku_price and sku_price > 0:
                        unit_prices.append(float(sku_price))
                
                if sku_prices or unit_prices:
                    brand_data = BrandPriceData(
                        name=brand,
                        skuPrices=sku_prices,
                        unitPrices=unit_prices
                    )
                    brands_data.append(brand_data)
            
            if brands_data:
                category_distribution = CategoryBrandDistribution(
                    category=category,
                    brands=brands_data
                )
                brand_distributions.append(category_distribution)
        
        logger.info(f"Calculated brand distributions for {len(brand_distributions)} categories")
        return brand_distributions
    
    def _calculate_price_statistics(self, prices: List[float]) -> PriceStatistics:
        """计算价格统计信息
        
        Args:
            prices: 价格列表
            
        Returns:
            PriceStatistics: 价格统计数据
        """
        if not prices:
            return PriceStatistics(min=0, q1=0, median=0, mean=0, q3=0, max=0)
        
        prices_array = np.array(prices)
        
        return PriceStatistics(
            min=float(np.min(prices_array)),
            q1=float(np.percentile(prices_array, 25)),
            median=float(np.percentile(prices_array, 50)),
            mean=float(np.mean(prices_array)),
            q3=float(np.percentile(prices_array, 75)),
            max=float(np.max(prices_array))
        )
    
    def _format_response(self, category_price_data: List[CategoryPriceData], 
                        brand_distributions: List[CategoryBrandDistribution],
                        request: PriceDistributionRequest) -> PriceDistributionResponse:
        """格式化响应数据
        
        Args:
            category_price_data: 分类价格数据
            brand_distributions: 品牌价格分布
            request: 原始请求
            
        Returns:
            PriceDistributionResponse: 格式化的响应数据
        """
        # 生成分类名称和颜色（兼容性）
        segment_names = [data.category for data in category_price_data]
        segment_colors = self._generate_category_colors(len(segment_names))
        
        # 构建元数据
        metadata = PriceDistributionMetadata(
            filtered_asins_count=sum(data.productCount for data in category_price_data),
            calculation_timestamp=datetime.now().isoformat(),
            timeframe_used=request.timeframe.period if request.timeframe else "year",
            categories_processed=segment_names
        )
        
        # 构建最终响应
        response = PriceDistributionResponse(
            priceDistribution=category_price_data,
            brandPriceDistribution=brand_distributions,
            segmentNames=segment_names,
            segmentColors=segment_colors,
            metadata=metadata
        )
        
        logger.info(f"Response formatted: {len(category_price_data)} categories, {len(brand_distributions)} brand distributions")
        return response
    
    def _generate_category_colors(self, count: int) -> List[str]:
        """生成分类颜色
        
        Args:
            count: 分类数量
            
        Returns:
            List[str]: 颜色列表
        """
        default_colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
            "#FECA57", "#FF9FF3", "#54A0FF", "#5F27CD",
            "#00D2D3", "#FF9F43", "#EE5A24", "#0ABDE3"
        ]
        
        # 如果需要更多颜色，重复使用
        colors = []
        for i in range(count):
            colors.append(default_colors[i % len(default_colors)])
        
        return colors
    
    def _get_empty_response(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        """返回空响应数据"""
        metadata = PriceDistributionMetadata(
            filtered_asins_count=0,
            calculation_timestamp=datetime.now().isoformat(),
            timeframe_used=request.timeframe.period if request.timeframe else "year",
            categories_processed=[]
        )
        
        return PriceDistributionResponse(
            priceDistribution=[],
            brandPriceDistribution=[],
            segmentNames=[],
            segmentColors=[],
            metadata=metadata
        )
