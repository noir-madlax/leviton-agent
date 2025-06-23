"""Product analysis service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class ProductAnalysisService(BaseDashboardService):
    """Service for product analysis data.
    
    Replaces frontend getProductAnalysisData() method with server-side
    implementation that applies project ASIN filtering.
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get product analysis data with ASIN filtering.
        
        Returns data in the exact same format as frontend getProductAnalysisData()
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
                estimated_revenue,
                category,
                product_url
            ''')
            
            # Apply base filters
            query = self._apply_base_filters(query)
            
            # 🔑 CRITICAL: Apply ASIN filtering to prevent data leakage
            query = self._apply_asin_filter(query)
            
            # Order by revenue descending (matches frontend)
            query = query.order('estimated_revenue', desc=True)
            
            # Execute query
            result = query.execute()
            
            logger.info(f"🔍 Product analysis query returned {len(result.data) if result.data else 0} products for project {self.project_id}")
            
            if not result.data:
                logger.warning(f"No product data found for project {self.project_id}")
                return {
                    'priceVsRevenue': [
                        {'category': 'Dimmer Switches', 'products': []},
                        {'category': 'Light Switches', 'products': []}
                    ],
                    'topProducts': [
                        {'category': 'Dimmer Switches', 'products': []},
                        {'category': 'Light Switches', 'products': []}
                    ]
                }
            
            # 转换数据格式 - replicate frontend mapping exactly
            products = []
            for item in result.data:
                # Skip items without revenue (matches frontend logic)
                revenue = item.get('estimated_revenue')
                if revenue is None:
                    continue
                    
                product = {
                    'id': item.get('platform_id'),
                    'name': item.get('title'),
                    'brand': item.get('brand'),
                    'price': item.get('price_usd'),
                    'unitPrice': item.get('unit_price_calculated') or item.get('price_usd'),
                    'revenue': revenue or 0,
                    'volume': item.get('monthly_sales_volume') or 0,
                    'url': item.get('product_url') or ''
                }
                products.append(product)
            
            logger.info(f"📊 Processed {len(products)} products with revenue data")
            
            # 按类别分组 - replicate frontend logic exactly
            dimmer_products = []
            switch_products = []
            
            for product in products:
                # Find original item to get category
                original_item = None
                for item in result.data:
                    if item.get('platform_id') == product['id']:
                        original_item = item
                        break
                
                if original_item:
                    category = original_item.get('category')
                    if category == 'Dimmer Switches':
                        dimmer_products.append(product)
                    else:
                        # Check product name for dimmer (matches frontend fallback logic)
                        if 'dimmer' in product['name'].lower():
                            dimmer_products.append(product)
                        else:
                            switch_products.append(product)
                else:
                    # Fallback to name check
                    if 'dimmer' in product['name'].lower():
                        dimmer_products.append(product)
                    else:
                        switch_products.append(product)
            
            logger.info(f"📈 Categorized products: {len(dimmer_products)} dimmers, {len(switch_products)} switches")
            
            # Prepare response data (matches frontend format exactly)
            response_data = {
                'priceVsRevenue': [
                    {'category': 'Dimmer Switches', 'products': dimmer_products},
                    {'category': 'Light Switches', 'products': switch_products}
                ],
                'topProducts': [
                    {'category': 'Dimmer Switches', 'products': dimmer_products[:20]},  # Top 20
                    {'category': 'Light Switches', 'products': switch_products[:20]}   # Top 20
                ]
            }
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error in product analysis for project {self.project_id}: {e}")
            raise 