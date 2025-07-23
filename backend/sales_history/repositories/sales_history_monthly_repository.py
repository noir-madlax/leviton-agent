"""Repository for sales history monthly aggregated data operations."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from supabase import Client

from core.database.connection import get_supabase_service_client
from ..models import SalesHistoryMonthlyDataPoint

logger = logging.getLogger(__name__)

class SalesHistoryMonthlyRepository:
    """Repository for sales history monthly aggregated data operations."""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """Initialize repository with Supabase client."""
        self.supabase = supabase_client or get_supabase_service_client()
    
    async def aggregate_daily_to_monthly(
        self, 
        asin: str, 
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> int:
        """Aggregate daily sales data to monthly data for an ASIN."""
        try:
            # Get all daily data for the ASIN
            from ..repositories.sales_history_repository import SalesHistoryRepository
            daily_repo = SalesHistoryRepository()
            
            # Get all daily data
            daily_data = await daily_repo.get_sales_data(
                [asin], 
                platform_source=platform_source,
                api_source=api_source
            )
            asin_data = daily_data.get(asin, [])
            
            if not asin_data:
                logger.info(f"No daily data found for ASIN {asin}, skipping monthly aggregation")
                return 0
            
            # Group by month
            monthly_groups = {}
            for record in asin_data:
                # Get the first day of the month
                month_start = record.sales_date.replace(day=1)
                month_key = month_start.isoformat()
                
                if month_key not in monthly_groups:
                    monthly_groups[month_key] = {
                        'units': [],
                        'prices': [],
                        'dates': []
                    }
                
                monthly_groups[month_key]['units'].append(record.estimated_units_sold)
                monthly_groups[month_key]['prices'].append(float(record.last_known_price))
                monthly_groups[month_key]['dates'].append(record.sales_date)
            
            # Create monthly records
            monthly_records = []
            for month_key, data in monthly_groups.items():
                total_units = sum(data['units'])
                avg_price = sum(data['prices']) / len(data['prices'])
                days_count = len(data['dates'])
                
                monthly_records.append({
                    'platform_id': asin,
                    'platform_source': platform_source,
                    'api_source': api_source,
                    'year_month': month_key,
                    'total_units_sold': total_units,
                    'average_price': round(avg_price, 2),
                    'days_in_month': days_count
                })
            
            # Insert monthly records with conflict resolution
            if monthly_records:
                result = self.supabase.table('product_sales_history_monthly').upsert(
                    monthly_records,
                    on_conflict='platform_id,platform_source,year_month'
                ).execute()
                
                inserted_count = len(result.data) if result.data else 0
                logger.info(f"Aggregated {inserted_count} months for ASIN {asin}")
                return inserted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error aggregating daily to monthly for ASIN {asin}: {e}")
            raise
    
    async def get_monthly_data(
        self, 
        asins: List[str], 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> Dict[str, List[SalesHistoryMonthlyDataPoint]]:
        """Get monthly sales data for multiple ASINs with optional date filtering."""
        try:
            query = self.supabase.table('product_sales_history_monthly').select(
                'platform_id, year_month, total_units_sold, average_price, days_in_month'
            ).in_('platform_id', asins)
            
            # Apply date filters
            if start_date:
                query = query.gte('year_month', start_date.replace(day=1).isoformat())
            if end_date:
                query = query.lte('year_month', end_date.replace(day=1).isoformat())
            
            # Apply source filters
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            # Order by platform_id and year_month
            query = query.order('platform_id').order('year_month', desc=True)
            
            result = query.execute()
            
            # Group by ASIN
            data_by_asin = {}
            for row in result.data:
                asin = row['platform_id']
                if asin not in data_by_asin:
                    data_by_asin[asin] = []
                
                data_by_asin[asin].append(SalesHistoryMonthlyDataPoint(
                    year_month_date=date.fromisoformat(row['year_month']),
                    total_units_sold=row['total_units_sold'],
                    average_price=Decimal(str(row['average_price'])),
                    days_in_month=row['days_in_month']
                ))
            
            # Add empty lists for ASINs with no data
            for asin in asins:
                if asin not in data_by_asin:
                    data_by_asin[asin] = []
            
            return data_by_asin
            
        except Exception as e:
            logger.error(f"Error getting monthly sales data: {e}")
            raise
    
    async def get_monthly_stats_for_asin(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics for an ASIN's monthly sales data."""
        try:
            # Get all monthly data for the ASIN and calculate stats manually
            query = self.supabase.table('product_sales_history_monthly').select(
                'year_month, total_units_sold, average_price, days_in_month'
            ).eq('platform_id', asin)
            
            if start_date:
                query = query.gte('year_month', start_date.replace(day=1).isoformat())
            if end_date:
                query = query.lte('year_month', end_date.replace(day=1).isoformat())
            
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                months = []
                units_sold = []
                prices = []
                days = []
                
                for row in result.data:
                    months.append(date.fromisoformat(row['year_month']))
                    units_sold.append(row['total_units_sold'])
                    prices.append(float(row['average_price']))
                    days.append(row['days_in_month'])
                
                return {
                    'total_months': len(months),
                    'min_month': min(months),
                    'max_month': max(months),
                    'total_units_sold': sum(units_sold),
                    'average_price': sum(prices) / len(prices),
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'total_days': sum(days)
                }
            
            return {
                'total_months': 0,
                'min_month': None,
                'max_month': None,
                'total_units_sold': 0,
                'average_price': 0.0,
                'min_price': 0.0,
                'max_price': 0.0,
                'total_days': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly stats for ASIN {asin}: {e}")
            raise
    
    async def delete_monthly_data(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> int:
        """Delete monthly sales data for an ASIN within a date range."""
        try:
            query = self.supabase.table('product_sales_history_monthly').delete().eq('platform_id', asin)
            
            if start_date:
                query = query.gte('year_month', start_date.replace(day=1).isoformat())
            if end_date:
                query = query.lte('year_month', end_date.replace(day=1).isoformat())
            
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            result = query.execute()
            deleted_count = len(result.data) if result.data else 0
            
            logger.info(f"Deleted {deleted_count} monthly sales records for ASIN {asin}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting monthly sales data for ASIN {asin}: {e}")
            raise
    
    async def get_latest_monthly_date(
        self, 
        asin: str, 
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> Optional[date]:
        """Get the latest month with data for an ASIN."""
        try:
            result = self.supabase.table('product_sales_history_monthly').select(
                'year_month'
            ).eq('platform_id', asin).eq('platform_source', platform_source).eq('api_source', api_source).order(
                'year_month', desc=True
            ).limit(1).execute()
            
            if result.data and result.data[0]['year_month']:
                return date.fromisoformat(result.data[0]['year_month'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest monthly date for ASIN {asin}: {e}")
            return None
    
    async def get_monthly_coverage_for_multiple_asins(
        self, 
        asins: List[str], 
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> Dict[str, Optional[date]]:
        """Get the latest monthly date for multiple ASINs."""
        try:
            # Get all monthly data for the ASINs
            result = self.supabase.table('product_sales_history_monthly').select(
                'platform_id, year_month'
            ).in_('platform_id', asins).eq('platform_source', platform_source).eq('api_source', api_source).order('platform_id,year_month').execute()
            
            # Group by ASIN and find latest month
            coverage = {}
            asin_months = {}
            
            for row in result.data:
                asin = row['platform_id']
                if asin not in asin_months:
                    asin_months[asin] = []
                asin_months[asin].append(date.fromisoformat(row['year_month']))
            
            for asin in asins:
                if asin in asin_months and asin_months[asin]:
                    coverage[asin] = max(asin_months[asin])
                else:
                    coverage[asin] = None
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error getting monthly coverage for multiple ASINs: {e}")
            return {asin: None for asin in asins} 