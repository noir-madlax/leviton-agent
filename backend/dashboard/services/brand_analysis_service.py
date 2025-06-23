"""Brand analysis service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class BrandAnalysisService(BaseDashboardService):
    """Service for brand category revenue analysis.
    
    Replaces frontend getBrandCategoryRevenue() method with server-side
    implementation that applies project ASIN filtering.
    """
    
    def get_data(self) -> List[Dict[str, Any]]:
        """Get brand category revenue data with ASIN filtering.
        
        Returns data in the exact same format as frontend getBrandCategoryRevenue()
        to ensure compatibility with existing UI components.
        """
        try:
            # Build query - replicate frontend logic exactly
            # Correct Supabase query order: table -> select -> filters
            query = self._get_base_product_table().select('brand, category, monthly_sales_volume, estimated_revenue')
            
            # Apply base filters
            query = self._apply_base_filters(query)
            
            # 🔑 CRITICAL: Apply ASIN filtering to prevent data leakage
            query = self._apply_asin_filter(query)
            
            # Execute query (without revenue filter to avoid SQL errors)
            result = query.execute()
            
            logger.info(f"🔍 Raw query returned {len(result.data) if result.data else 0} products for project {self.project_id}")
            
            if not result.data:
                logger.warning(f"No data found for project {self.project_id}")
                return []
            
            # Debug: Log first few products
            for i, item in enumerate(result.data[:3]):
                logger.info(f"  Product {i+1}: brand={item.get('brand')}, category={item.get('category')}, revenue={item.get('estimated_revenue')}, volume={item.get('monthly_sales_volume')}")
            
            # Process data - replicate frontend aggregation logic
            # Apply revenue filter in Python code instead of SQL
            brand_data = {}
            products_with_revenue = 0
            products_without_revenue = 0
            
            for item in result.data:
                brand = item.get('brand')
                if not brand:
                    continue
                
                # Apply revenue filter here - only process items with revenue data
                revenue = item.get('estimated_revenue')
                logger.info(f"  🔍 Checking product: brand={brand}, revenue={revenue}, type={type(revenue)}")
                
                if revenue is None or revenue == 0:
                    products_without_revenue += 1
                    logger.info(f"  ❌ Skipping product with no revenue: brand={brand}, revenue={revenue}")
                    continue  # Skip items without revenue data (matches frontend logic)
                
                products_with_revenue += 1
                logger.info(f"  ✅ Processing product with revenue: brand={brand}, revenue={revenue}")
                
                if brand not in brand_data:
                    brand_data[brand] = {
                        'brand': brand,
                        'dimmerRevenue': 0,
                        'switchRevenue': 0,
                        'dimmerVolume': 0,
                        'switchVolume': 0
                    }
                
                volume = item.get('monthly_sales_volume', 0) or 0
                category = item.get('category', '')
                
                # Categorize by product type
                if category == 'Dimmer Switches':
                    brand_data[brand]['dimmerRevenue'] += revenue
                    brand_data[brand]['dimmerVolume'] += volume
                elif category == 'Light Switches':
                    brand_data[brand]['switchRevenue'] += revenue
                    brand_data[brand]['switchVolume'] += volume
            
            result_data = list(brand_data.values())
            
            logger.info(f"📊 Brand analysis summary for project {self.project_id}:")
            logger.info(f"  - Raw products: {len(result.data) if result.data else 0}")
            logger.info(f"  - Products with revenue: {products_with_revenue}")
            logger.info(f"  - Products without revenue: {products_without_revenue}")
            logger.info(f"  - Final brands: {len(result_data)}")
            
            if result_data:
                for brand in result_data:
                    logger.info(f"  📈 {brand['brand']}: Dimmer ${brand['dimmerRevenue']} | Switch ${brand['switchRevenue']}")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error in brand analysis for project {self.project_id}: {e}")
            raise 