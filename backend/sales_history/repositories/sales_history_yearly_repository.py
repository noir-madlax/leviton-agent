"""Repository for sales history yearly aggregated data operations."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from supabase import Client

from core.database.connection import get_supabase_service_client
from ..models import SalesHistoryYearlyDataPoint

logger = logging.getLogger(__name__)

class SalesHistoryYearlyRepository:
    """Repository for sales history yearly aggregated data operations."""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """Initialize repository with Supabase client."""
        self.supabase = supabase_client or get_supabase_service_client()
    
    async def aggregate_monthly_to_yearly(
        self, 
        asin: str, 
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> int:
        """Aggregate monthly sales data to yearly data for an ASIN (rolling year from latest date)."""
        try:
            # Get all monthly data for the ASIN
            from ..repositories.sales_history_monthly_repository import SalesHistoryMonthlyRepository
            monthly_repo = SalesHistoryMonthlyRepository()
            
            # Get all monthly data
            monthly_data = await monthly_repo.get_monthly_data(
                [asin], 
                platform_source=platform_source,
                api_source=api_source
            )
            asin_data = monthly_data.get(asin, [])
            
            if not asin_data:
                logger.info(f"No monthly data found for ASIN {asin}, skipping yearly aggregation")
                return 0
            
            # Find the latest date to determine the year end
            latest_date = max(record.year_month_date for record in asin_data)
            year_end_date = latest_date
            
            # Calculate year start date (one year back from the latest date)
            year_start_date = year_end_date.replace(year=year_end_date.year - 1)
            
            # Filter monthly data to only include the rolling year
            rolling_year_data = [
                record for record in asin_data 
                if record.year_month_date >= year_start_date and record.year_month_date <= year_end_date
            ]
            
            if not rolling_year_data:
                logger.info(f"No data in rolling year for ASIN {asin}, skipping yearly aggregation")
                return 0
            
            # Calculate yearly totals
            total_units = sum(record.total_units_sold for record in rolling_year_data)
            avg_price = sum(float(record.average_price) for record in rolling_year_data) / len(rolling_year_data)
            total_revenue = sum(float(record.total_revenue) for record in rolling_year_data)
            months_count = len(rolling_year_data)
            
            # Create yearly record
            yearly_record = {
                'platform_id': asin,
                'platform_source': platform_source,
                'api_source': api_source,
                'year_start_date': year_start_date.isoformat(),
                'year_end_date': year_end_date.isoformat(),
                'total_units_sold': total_units,
                'average_price': round(avg_price, 2),
                'total_revenue': round(total_revenue, 2),
                'months_in_year': months_count
            }
            
            # Insert yearly record with conflict resolution
            result = self.supabase.table('product_sales_history_yearly').upsert(
                yearly_record,
                on_conflict='platform_id,platform_source,year_start_date'
            ).execute()
            
            inserted_count = len(result.data) if result.data else 0
            logger.info(f"Aggregated yearly data for ASIN {asin} (year: {year_start_date} to {year_end_date})")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error aggregating monthly to yearly for ASIN {asin}: {e}")
            raise
    
    async def get_yearly_data(
        self, 
        asins: List[str], 
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> Dict[str, List[SalesHistoryYearlyDataPoint]]:
        """Get yearly sales data for multiple ASINs (rolling year from latest scraping date)."""
        try:
            query = self.supabase.table('product_sales_history_yearly').select(
                'platform_id, year_start_date, year_end_date, total_units_sold, average_price, total_revenue, months_in_year'
            ).in_('platform_id', asins)
            
            # Apply source filters
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            # Order by platform_id and year_start_date
            query = query.order('platform_id').order('year_start_date', desc=True)
            
            result = query.execute()
            
            # Group by ASIN
            data_by_asin = {}
            for row in result.data:
                asin = row['platform_id']
                if asin not in data_by_asin:
                    data_by_asin[asin] = []
                
                data_by_asin[asin].append(SalesHistoryYearlyDataPoint(
                    year_start_date=date.fromisoformat(row['year_start_date']),
                    year_end_date=date.fromisoformat(row['year_end_date']),
                    total_units_sold=row['total_units_sold'],
                    average_price=Decimal(str(row['average_price'])),
                    total_revenue=Decimal(str(row['total_revenue'])),
                    months_in_year=row['months_in_year']
                ))
            
            # Add empty lists for ASINs with no data
            for asin in asins:
                if asin not in data_by_asin:
                    data_by_asin[asin] = []
            
            return data_by_asin
            
        except Exception as e:
            logger.error(f"Error getting yearly sales data: {e}")
            raise
    
    async def get_yearly_stats_for_asin(
        self, 
        asin: str, 
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics for an ASIN's yearly sales data."""
        try:
            # Get all yearly data for the ASIN
            query = self.supabase.table('product_sales_history_yearly').select(
                'year_start_date, year_end_date, total_units_sold, average_price, total_revenue, months_in_year'
            ).eq('platform_id', asin)
            
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                years = []
                units_sold = []
                prices = []
                revenues = []
                months = []
                
                for row in result.data:
                    years.append({
                        'start_date': date.fromisoformat(row['year_start_date']),
                        'end_date': date.fromisoformat(row['year_end_date'])
                    })
                    units_sold.append(row['total_units_sold'])
                    prices.append(float(row['average_price']))
                    revenues.append(float(row['total_revenue']))
                    months.append(row['months_in_year'])
                
                return {
                    'total_years': len(years),
                    'latest_year': max(years, key=lambda x: x['end_date']),
                    'total_units_sold': sum(units_sold),
                    'total_revenue': sum(revenues),
                    'average_price': sum(prices) / len(prices),
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'total_months': sum(months)
                }
            
            return {
                'total_years': 0,
                'latest_year': None,
                'total_units_sold': 0,
                'total_revenue': 0.0,
                'average_price': 0.0,
                'min_price': 0.0,
                'max_price': 0.0,
                'total_months': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting yearly stats for ASIN {asin}: {e}")
            raise
    
    async def delete_yearly_data(
        self, 
        asin: str, 
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> int:
        """Delete yearly sales data for an ASIN."""
        try:
            query = self.supabase.table('product_sales_history_yearly').delete().eq('platform_id', asin)
            
            if platform_source:
                query = query.eq('platform_source', platform_source)
            if api_source:
                query = query.eq('api_source', api_source)
            
            result = query.execute()
            deleted_count = len(result.data) if result.data else 0
            
            logger.info(f"Deleted {deleted_count} yearly sales records for ASIN {asin}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting yearly sales data for ASIN {asin}: {e}")
            raise
    
    async def get_latest_yearly_date(
        self, 
        asin: str, 
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> Optional[date]:
        """Get the latest year end date with data for an ASIN."""
        try:
            result = self.supabase.table('product_sales_history_yearly').select(
                'year_end_date'
            ).eq('platform_id', asin).eq('platform_source', platform_source).eq('api_source', api_source).order(
                'year_end_date', desc=True
            ).limit(1).execute()
            
            if result.data and result.data[0]['year_end_date']:
                return date.fromisoformat(result.data[0]['year_end_date'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest yearly date for ASIN {asin}: {e}")
            return None
    
    async def get_yearly_coverage_for_multiple_asins(
        self, 
        asins: List[str], 
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> Dict[str, Optional[date]]:
        """Get the latest year end date with data for multiple ASINs."""
        try:
            result = self.supabase.table('product_sales_history_yearly').select(
                'platform_id, year_end_date'
            ).in_('platform_id', asins).eq('platform_source', platform_source).eq('api_source', api_source).order(
                'platform_id, year_end_date', desc=True
            ).execute()
            
            coverage = {}
            for row in result.data:
                asin = row['platform_id']
                if asin not in coverage:
                    coverage[asin] = date.fromisoformat(row['year_end_date'])
            
            # Add None for ASINs with no data
            for asin in asins:
                if asin not in coverage:
                    coverage[asin] = None
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error getting yearly coverage for multiple ASINs: {e}")
            return {asin: None for asin in asins} 