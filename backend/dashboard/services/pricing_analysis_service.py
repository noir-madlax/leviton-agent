"""Pricing analysis service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class PricingAnalysisService(BaseDashboardService):
    """Service for pricing analysis data.
    
    Replaces frontend getPricingAnalysisData() method with server-side
    implementation that applies project ASIN filtering.
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get pricing analysis data with ASIN filtering.
        
        Returns data in the exact same format as frontend getPricingAnalysisData()
        to ensure compatibility with existing UI components.
        """
        try:
            # Build query - replicate frontend logic exactly
            query = self._get_base_product_table().select('''
                platform_id,
                title,
                brand,
                price_usd,
                unit_price_calculated,
                monthly_sales_volume,
                category,
                pack_count
            ''')
            
            # Apply base filters
            query = self._apply_base_filters(query)
            
            # 🔑 CRITICAL: Apply ASIN filtering to prevent data leakage
            query = self._apply_asin_filter(query)
            
            # Execute query
            result = query.execute()
            
            logger.info(f"🔍 Pricing analysis query returned {len(result.data) if result.data else 0} products for project {self.project_id}")
            
            if not result.data:
                logger.warning(f"No pricing data found for project {self.project_id}")
                return {
                    'priceDistribution': [],
                    'brandPriceDistribution': []
                }
            
            # 按类别分组数据 - replicate frontend logic exactly
            # Filter out items without price data (matches frontend logic)
            products_with_price = [item for item in result.data if item.get('price_usd') is not None]
            dimmer_products = [item for item in products_with_price if item.get('category') == 'Dimmer Switches']
            switch_products = [item for item in products_with_price if item.get('category') == 'Light Switches']
            
            logger.info(f"📊 Categorized pricing data: {len(dimmer_products)} dimmers, {len(switch_products)} switches")
            
            # 计算统计数据的辅助函数 - replicate frontend calculateStats exactly
            def calculate_stats(prices):
                if not prices or len(prices) == 0:
                    return {'min': 0, 'q1': 0, 'median': 0, 'mean': 0, 'q3': 0, 'max': 0}
                
                sorted_prices = sorted([p for p in prices if p is not None])
                if not sorted_prices:
                    return {'min': 0, 'q1': 0, 'median': 0, 'mean': 0, 'q3': 0, 'max': 0}
                
                min_val = sorted_prices[0]
                max_val = sorted_prices[-1]
                q1 = sorted_prices[len(sorted_prices) // 4]
                median = sorted_prices[len(sorted_prices) // 2]
                q3 = sorted_prices[(len(sorted_prices) * 3) // 4]
                mean = sum(sorted_prices) / len(sorted_prices)
                
                return {
                    'min': min_val,
                    'q1': q1,
                    'median': median,
                    'mean': mean,
                    'q3': q3,
                    'max': max_val
                }
            
            # 构建价格分布数据 - replicate frontend logic exactly
            dimmer_sku_prices = [item.get('price_usd') for item in dimmer_products if item.get('price_usd') is not None]
            dimmer_unit_prices = [item.get('unit_price_calculated') or item.get('price_usd') for item in dimmer_products if (item.get('unit_price_calculated') or item.get('price_usd')) is not None]
            switch_sku_prices = [item.get('price_usd') for item in switch_products if item.get('price_usd') is not None]
            switch_unit_prices = [item.get('unit_price_calculated') or item.get('price_usd') for item in switch_products if (item.get('unit_price_calculated') or item.get('price_usd')) is not None]
            
            price_distribution = [
                {
                    'category': 'Dimmer Switches',
                    'skuPrices': dimmer_sku_prices,
                    'unitPrices': dimmer_unit_prices,
                    'stats': {
                        'sku': calculate_stats(dimmer_sku_prices),
                        'unit': calculate_stats(dimmer_unit_prices)
                    }
                },
                {
                    'category': 'Light Switches',
                    'skuPrices': switch_sku_prices,
                    'unitPrices': switch_unit_prices,
                    'stats': {
                        'sku': calculate_stats(switch_sku_prices),
                        'unit': calculate_stats(switch_unit_prices)
                    }
                }
            ]
            
            # 构建品牌价格分布数据 - replicate frontend getBrandDistribution exactly
            def get_brand_distribution(products, category):
                brand_map = {}
                
                for product in products:
                    brand = product.get('brand')
                    if not brand:
                        continue
                        
                    if brand not in brand_map:
                        brand_map[brand] = {'skuPrices': [], 'unitPrices': []}
                    
                    if product.get('price_usd') is not None:
                        brand_map[brand]['skuPrices'].append(product.get('price_usd'))
                    
                    unit_price = product.get('unit_price_calculated') or product.get('price_usd')
                    if unit_price is not None:
                        brand_map[brand]['unitPrices'].append(unit_price)
                
                return {
                    'category': category,
                    'brands': [
                        {
                            'name': name,
                            'skuPrices': prices['skuPrices'],
                            'unitPrices': prices['unitPrices']
                        }
                        for name, prices in brand_map.items()
                    ]
                }
            
            brand_price_distribution = [
                get_brand_distribution(dimmer_products, 'Dimmer Switches'),
                get_brand_distribution(switch_products, 'Light Switches')
            ]
            
            logger.info(f"📈 Pricing analysis completed: {len(price_distribution)} categories, {sum(len(b['brands']) for b in brand_price_distribution)} brand distributions")
            
            return {
                'priceDistribution': price_distribution,
                'brandPriceDistribution': brand_price_distribution
            }
            
        except Exception as e:
            logger.error(f"Error in pricing analysis for project {self.project_id}: {e}")
            raise 