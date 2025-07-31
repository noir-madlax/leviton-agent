"""Market Analysis service for TAM and Market Share calculations."""

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from collections import defaultdict

from dashboard.charts.filters.asin_filter_service import get_filtered_asins
from dashboard.charts.base_models import BaseRequestModel
from .models import (
    TAMMarketShareRequest,
    TAMMarketShareResponse,
    TAMData,
    CategoryMarketShare,
    BrandShareData,
    TAMMarketShareMetadata
)

logger = logging.getLogger(__name__)


class TAMMarketShareService:
    """Service for Total Addressable Market and Market Share analysis."""

    def __init__(self, supabase_client):
        """Initialize the service with Supabase client."""
        self.supabase = supabase_client
    
    def get_tam_market_share_data(self, request: TAMMarketShareRequest) -> TAMMarketShareResponse:
        """Get TAM and Market Share data with filtering.
        
        Args:
            request: TAM Market Share request with project_id, filters, and timeframe
            
        Returns:
            TAMMarketShareResponse: Complete TAM and market share analysis
        """
        try:
            logger.info(f"🏢 Starting TAM Market Share analysis for project {request.project_id}")
            
            # Step 1: Use public get_filtered_asins method
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            if not filtered_asins:
                logger.warning(f"No ASINs found after filtering for project {request.project_id}")
                return self._get_empty_response()
            
            logger.info(f"📊 Found {len(filtered_asins)} ASINs after filtering")
            
            # Step 2: Get product data from wide table with timeframe support
            product_data = self._get_product_data_from_wide_table(filtered_asins, request.timeframe)
            
            if not product_data:
                logger.warning(f"No product data found for filtered ASINs")
                return self._get_empty_response()
            
            # Step 3: Process data and calculate market shares
            tam_data, category_market_shares = self._calculate_market_shares(product_data)
            
            # Step 4: Generate metadata
            metadata = self._generate_metadata(
                filtered_asins_count=len(filtered_asins),
                product_data=product_data
            )
            
            logger.info(f"✅ TAM Market Share analysis completed successfully")
            
            return TAMMarketShareResponse(
                tam_data=tam_data,
                market_share_by_category=category_market_shares,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Error in TAM Market Share analysis: {e}", exc_info=True)
            return self._get_empty_response()

    def _get_product_data_from_wide_table(self, asins: List[str], timeframe=None) -> List[Dict[str, Any]]:
        """Get product data from product_wide_table.
        
        Args:
            asins: List of ASINs to query
            timeframe: Optional TimeframeModel to determine which fields to query
            
        Returns:
            List of product data dictionaries
        """
        try:
            # Determine which revenue and volume fields to query based on timeframe
            revenue_field = "past_year_revenue"  # default
            volume_field = "past_year_volume"    # default
            
            if timeframe and timeframe.period:
                if timeframe.period == "month":
                    revenue_field = "past_month_revenue"
                    volume_field = "past_month_volume"  
                elif timeframe.period == "6months":
                    revenue_field = "past_6_month_revenue"
                    volume_field = "past_6_month_volume"  
                else:  # year (default)
                    revenue_field = "past_year_revenue"
                    volume_field = "past_year_volume"
            
            # Build select fields
            select_fields = f'platform_id, brand, category, {revenue_field}'
            if volume_field:
                select_fields += f', {volume_field}'
            
            logger.info(f"📊 Querying fields: {select_fields}")
            
            # Query product_wide_table for required fields
            query = self.supabase.table('product_wide_table').select(select_fields).in_('platform_id', asins)
            
            result = query.execute()
            
            if not result.data:
                logger.warning("No data found in product_wide_table")
                return []
            
            # Filter out products with missing essential data and normalize field names
            valid_products = []
            for product in result.data:
                if (product.get('brand') and 
                    product.get('category') and 
                    product.get(revenue_field) is not None):
                    
                    # Normalize field names for consistent processing
                    normalized_product = {
                        'platform_id': product.get('platform_id'),
                        'brand': product.get('brand'),
                        'category': product.get('category'),
                        'revenue': product.get(revenue_field, 0),
                        'volume': product.get(volume_field, 0) if volume_field else 0
                    }
                    valid_products.append(normalized_product)
            
            logger.info(f"📈 Retrieved {len(valid_products)} valid products from wide table using {revenue_field}")
            return valid_products
            
        except Exception as e:
            logger.error(f"Error querying product_wide_table: {e}")
            return []
    
    def _calculate_market_shares(self, product_data: List[Dict[str, Any]]) -> tuple[TAMData, List[CategoryMarketShare]]:
        """Calculate TAM and market shares by category.
        
        Args:
            product_data: List of product data from wide table
            
        Returns:
            Tuple of (TAMData, List[CategoryMarketShare])
        """
        # Group data by category and brand
        category_brand_data = defaultdict(lambda: defaultdict(lambda: {
            'revenue': 0.0,
            'volume': 0,
            'product_count': 0
        }))
        
        total_revenue = 0.0
        total_volume = 0
        total_products = 0
        
        for product in product_data:
            category = product.get('category', 'Unknown')
            brand = product.get('brand', 'Unknown')
            revenue = float(product.get('revenue', 0) or 0)
            volume = int(product.get('volume', 0) or 0)
            
            # Aggregate by category and brand
            category_brand_data[category][brand]['revenue'] += revenue
            category_brand_data[category][brand]['volume'] += volume
            category_brand_data[category][brand]['product_count'] += 1
            
            # Aggregate totals
            total_revenue += revenue
            total_volume += volume
            total_products += 1
        
        # Create TAM data
        tam_data = TAMData(
            total_market_revenue=total_revenue,
            total_market_volume=total_volume,
            total_products=total_products,
            currency="USD"
        )
        
        # Create category market shares
        category_market_shares = []
        
        for category, brand_data in category_brand_data.items():
            # Calculate category totals
            category_revenue = sum(data['revenue'] for data in brand_data.values())
            category_volume = sum(data['volume'] for data in brand_data.values())
            category_products = sum(data['product_count'] for data in brand_data.values())
            
            # Create brand shares for this category
            brand_shares = []
            for rank, (brand, data) in enumerate(
                sorted(brand_data.items(), key=lambda x: x[1]['revenue'], reverse=True), 1
            ):
                market_share_pct = (data['revenue'] / category_revenue * 100) if category_revenue > 0 else 0
                
                brand_shares.append(BrandShareData(
                    brand=brand,
                    revenue=data['revenue'],
                    volume=data['volume'],
                    product_count=data['product_count'],
                    market_share_percentage=round(market_share_pct, 2),
                    rank=rank
                ))
            
            category_market_shares.append(CategoryMarketShare(
                category=category,
                total_revenue=category_revenue,
                total_volume=category_volume,
                total_products=category_products,
                brand_shares=brand_shares
            ))
        
        # Sort categories by revenue (descending)
        category_market_shares.sort(key=lambda x: x.total_revenue, reverse=True)
        
        return tam_data, category_market_shares
    
    def _generate_metadata(self, filtered_asins_count: int, product_data: List[Dict[str, Any]]) -> TAMMarketShareMetadata:
        """Generate metadata for the analysis.
        
        Args:
            filtered_asins_count: Number of ASINs after filtering
            product_data: Product data used in analysis
            
        Returns:
            TAMMarketShareMetadata
        """
        categories = set(p.get('category') for p in product_data if p.get('category'))
        brands = set(p.get('brand') for p in product_data if p.get('brand'))
        
        return TAMMarketShareMetadata(
            filtered_asins_count=filtered_asins_count,
            total_categories=len(categories),
            total_brands=len(brands),
            calculation_timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _get_empty_response(self) -> TAMMarketShareResponse:
        """Return empty response when no data is available."""
        return TAMMarketShareResponse(
            tam_data=TAMData(
                total_market_revenue=0.0,
                total_market_volume=0,
                total_products=0,
                currency="USD"
            ),
            market_share_by_category=[],
            metadata=TAMMarketShareMetadata(
                filtered_asins_count=0,
                total_categories=0,
                total_brands=0,
                calculation_timestamp=datetime.now(timezone.utc).isoformat()
            )
        )
