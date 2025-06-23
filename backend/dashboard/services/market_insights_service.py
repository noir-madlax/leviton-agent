"""Market insights service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class MarketInsightsService(BaseDashboardService):
    """Service for market insights data.
    
    Replaces frontend getMarketInsightsData() method with server-side
    implementation that applies project ASIN filtering.
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get market insights data with ASIN filtering.
        
        Returns data in the exact same format as frontend getMarketInsightsData()
        to ensure compatibility with existing UI components.
        """
        try:
            # Build query - replicate frontend logic exactly
            query = self._get_base_product_table().select('''
                product_segment,
                category,
                price_usd,
                monthly_sales_volume,
                estimated_revenue
            ''')
            
            # Apply base filters
            query = query.eq('source', 'amazon').neq('product_segment', 'OUT_OF_SCOPE')
            
            # 🔑 CRITICAL: Apply ASIN filtering to prevent data leakage
            query = self._apply_asin_filter(query)
            
            # Execute query
            result = query.execute()
            
            logger.info(f"🔍 Market insights query returned {len(result.data) if result.data else 0} products for project {self.project_id}")
            
            if not result.data:
                logger.warning(f"No market insights data found for project {self.project_id}")
                return {
                    'segmentRevenue': {
                        'dimmerSwitches': [],
                        'lightSwitches': []
                    }
                }
            
            # 按产品细分和类别聚合数据 - replicate frontend logic exactly
            segment_data = {}
            
            for item in result.data:
                # Filter in Python: Skip items without segment, category, or revenue data
                segment = item.get('product_segment')
                category = item.get('category')
                revenue = item.get('estimated_revenue')
                
                if not segment or not category or revenue is None:
                    continue
                
                if segment not in segment_data:
                    segment_data[segment] = {}
                
                if category not in segment_data[segment]:
                    segment_data[segment][category] = {
                        'segment': f"{segment} {category}",
                        'revenue': 0,
                        'volume': 0,
                        'products': 0
                    }
                
                # Aggregate data
                segment_data[segment][category]['revenue'] += item.get('estimated_revenue', 0) or 0
                segment_data[segment][category]['volume'] += item.get('monthly_sales_volume', 0) or 0
                segment_data[segment][category]['products'] += 1
            
            logger.info(f"📊 Processed {len(segment_data)} segments")
            
            # 分离 Dimmer 和 Light Switches 数据 - replicate frontend logic exactly
            dimmer_switches = []
            light_switches = []
            
            for category_data in segment_data.values():
                for item in category_data.values():
                    if 'Dimmer Switches' in item['segment']:
                        dimmer_switches.append(item)
                    elif 'Light Switches' in item['segment']:
                        light_switches.append(item)
            
            # 按收入排序 - replicate frontend logic exactly
            dimmer_switches.sort(key=lambda x: x['revenue'], reverse=True)
            light_switches.sort(key=lambda x: x['revenue'], reverse=True)
            
            logger.info(f"📈 Market insights completed: {len(dimmer_switches)} dimmer segments, {len(light_switches)} switch segments")
            
            return {
                'segmentRevenue': {
                    'dimmerSwitches': dimmer_switches,
                    'lightSwitches': light_switches
                }
            }
            
        except Exception as e:
            logger.error(f"Error in market insights for project {self.project_id}: {e}")
            raise 