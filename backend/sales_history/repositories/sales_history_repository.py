"""Repository for sales history daily data operations."""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from decimal import Decimal
from supabase import Client

from core.database.connection import get_supabase_service_client
from ..models import SalesHistoryDataPoint, DateRange

logger = logging.getLogger(__name__)

class SalesHistoryRepository:
    """Repository for sales history daily data operations."""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """Initialize repository with Supabase client."""
        self.supabase = supabase_client or get_supabase_service_client()
    
    async def check_asin_exists(self, asin: str, platform_source: str = "amazon") -> bool:
        """Check if ASIN exists in product_wide_table."""
        try:
            result = self.supabase.table('product_wide_table').select(
                'platform_id'
            ).eq('platform_id', asin).eq('source', platform_source).limit(1).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking if ASIN {asin} exists: {e}")
            return False
    
    async def check_multiple_asins_exist(self, asins: List[str], platform_source: str = "amazon") -> Dict[str, bool]:
        """Check which ASINs exist in product_wide_table."""
        try:
            result = self.supabase.table('product_wide_table').select(
                'platform_id'
            ).in_('platform_id', asins).eq('source', platform_source).execute()
            
            existing_asins = {row['platform_id'] for row in result.data}
            return {asin: asin in existing_asins for asin in asins}
            
        except Exception as e:
            logger.error(f"Error checking multiple ASINs: {e}")
            return {asin: False for asin in asins}
    
    async def get_data_coverage_for_asin(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> Optional[DateRange]:
        """Get the date range of existing data for an ASIN."""
        try:
            query = self.supabase.table('product_sales_history_daily').select(
                'date'
            ).eq('platform_id', asin).eq('platform_source', platform_source).eq('api_source', api_source)
            
            if start_date:
                query = query.gte('date', start_date.isoformat())
            if end_date:
                query = query.lte('date', end_date.isoformat())
            
            query = query.order('date')
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                dates = [date.fromisoformat(row['date']) for row in result.data]
                return DateRange(
                    start_date=min(dates),
                    end_date=max(dates)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting data coverage for ASIN {asin}: {e}")
            return None
    
    async def get_data_coverage_for_multiple_asins(
        self, 
        asins: List[str], 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> Dict[str, Optional[DateRange]]:
        """Get the date range of existing data for multiple ASINs."""
        try:
            query = self.supabase.table('product_sales_history_daily').select(
                'platform_id, date'
            ).in_('platform_id', asins).eq('platform_source', platform_source).eq('api_source', api_source)
            
            if start_date:
                query = query.gte('date', start_date.isoformat())
            if end_date:
                query = query.lte('date', end_date.isoformat())
            
            query = query.order('platform_id,date')
            result = query.execute()
            
            # Group by ASIN
            asin_dates = {}
            for row in result.data:
                asin = row['platform_id']
                if asin not in asin_dates:
                    asin_dates[asin] = []
                asin_dates[asin].append(date.fromisoformat(row['date']))
            
            # Create DateRange objects
            coverage = {}
            for asin in asins:
                if asin in asin_dates and asin_dates[asin]:
                    coverage[asin] = DateRange(
                        start_date=min(asin_dates[asin]),
                        end_date=max(asin_dates[asin])
                    )
                else:
                    coverage[asin] = None
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error getting data coverage for multiple ASINs: {e}")
            return {asin: None for asin in asins}
    
    async def insert_sales_data(
        self, 
        asin: str, 
        platform_source: str, 
        api_source: str,
        sales_data: List[SalesHistoryDataPoint]
    ) -> int:
        """Insert sales data for an ASIN."""
        if not sales_data:
            return 0
        
        try:
            # Convert to database format
            records = []
            for data_point in sales_data:
                # Calculate revenue
                revenue = float(data_point.last_known_price) * data_point.estimated_units_sold
                
                records.append({
                    'platform_id': asin,
                    'platform_source': platform_source,
                    'api_source': api_source,
                    'date': data_point.sales_date.isoformat(),
                    'estimated_units_sold': data_point.estimated_units_sold,
                    'last_known_price': float(data_point.last_known_price),
                    'revenue': revenue
                })
            
            # Insert with conflict resolution (ignore duplicates)
            result = self.supabase.table('product_sales_history_daily').upsert(
                records,
                on_conflict='platform_id,platform_source,date'
            ).execute()
            
            inserted_count = len(result.data) if result.data else 0
            logger.info(f"Inserted {inserted_count} sales records for ASIN {asin}")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error inserting sales data for ASIN {asin}: {e}")
            raise
    
    async def get_sales_data(
        self, 
        asins: List[str], 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> Dict[str, List[SalesHistoryDataPoint]]:
        """Get sales data for multiple ASINs with optional date filtering."""
        try:
            query = self.supabase.table('product_sales_history_daily').select(
                'platform_id, date, estimated_units_sold, last_known_price, revenue'
            ).in_('platform_id', asins)
            
            # Apply date filters
            if start_date:
                query = query.gte('date', start_date.isoformat())
            if end_date:
                query = query.lte('date', end_date.isoformat())
            
            # Apply source filters
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            # Order by platform_id and date
            query = query.order('platform_id').order('date', desc=True)
            
            result = query.execute()
            
            # Group by ASIN
            data_by_asin = {}
            for row in result.data:
                asin = row['platform_id']
                if asin not in data_by_asin:
                    data_by_asin[asin] = []
                
                data_by_asin[asin].append(SalesHistoryDataPoint(
                    sales_date=date.fromisoformat(row['date']),
                    estimated_units_sold=row['estimated_units_sold'],
                    last_known_price=Decimal(str(row['last_known_price'])),
                    revenue=Decimal(str(row['revenue']))
                ))
            
            # Add empty lists for ASINs with no data
            for asin in asins:
                if asin not in data_by_asin:
                    data_by_asin[asin] = []
            
            return data_by_asin
            
        except Exception as e:
            logger.error(f"Error getting sales data: {e}")
            raise
    
    async def delete_sales_data(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> int:
        """Delete sales data for an ASIN within a date range."""
        try:
            query = self.supabase.table('product_sales_history_daily').delete().eq('platform_id', asin)
            
            if start_date:
                query = query.gte('date', start_date.isoformat())
            if end_date:
                query = query.lte('date', end_date.isoformat())
            
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            result = query.execute()
            deleted_count = len(result.data) if result.data else 0
            
            logger.info(f"Deleted {deleted_count} sales records for ASIN {asin}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting sales data for ASIN {asin}: {e}")
            raise
    
    async def get_stats_for_asin(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics for an ASIN's sales data."""
        try:
            # Get all data for the ASIN and calculate stats manually
            query = self.supabase.table('product_sales_history_daily').select(
                'date, estimated_units_sold, last_known_price, revenue'
            ).eq('platform_id', asin)
            
            if start_date:
                query = query.gte('date', start_date.isoformat())
            if end_date:
                query = query.lte('date', end_date.isoformat())
            
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                dates = []
                units_sold = []
                prices = []
                revenues = []
                
                for row in result.data:
                    dates.append(date.fromisoformat(row['date']))
                    units_sold.append(row['estimated_units_sold'])
                    prices.append(float(row['last_known_price']))
                    revenues.append(float(row['revenue']))
                
                return {
                    'total_records': len(dates),
                    'min_date': min(dates),
                    'max_date': max(dates),
                    'total_units_sold': sum(units_sold),
                    'total_revenue': sum(revenues),
                    'average_price': sum(prices) / len(prices),
                    'min_price': min(prices),
                    'max_price': max(prices)
                }
            
            return {
                'total_records': 0,
                'min_date': None,
                'max_date': None,
                'total_units_sold': 0,
                'total_revenue': 0.0,
                'average_price': 0.0,
                'min_price': 0.0,
                'max_price': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for ASIN {asin}: {e}")
            raise 