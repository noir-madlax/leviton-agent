"""Sales history scraper service using Jungle Scout API."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal

from scraping.common.jungle_scout_api import get_sales_history, JungleScoutAPIError
from ..models import (
    SalesHistoryDataPoint, 
    ScrapingResult, 
    DateRange,
    SalesHistoryScrapingSummary
)
from ..repositories.sales_history_repository import SalesHistoryRepository
from ..repositories.sales_history_monthly_repository import SalesHistoryMonthlyRepository

logger = logging.getLogger(__name__)

class SalesHistoryScraperService:
    """Service for scraping sales history data using Jungle Scout API."""
    
    def __init__(self):
        """Initialize the scraper service."""
        self.daily_repo = SalesHistoryRepository()
        self.monthly_repo = SalesHistoryMonthlyRepository()
    
    async def should_scrape_asin(
        self, 
        asin: str, 
        start_date: Optional[date], 
        end_date: Optional[date]
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if an ASIN should be scraped based on smart logic.
        
        Returns:
            tuple[bool, Optional[str]]: (should_scrape, reason_if_skipped)
        """
        try:
            # 1. Check if ASIN exists in product_wide_table
            asin_exists = await self.daily_repo.check_asin_exists(asin)
            if not asin_exists:
                return False, f"ASIN {asin} not found in product database"
            
            # 2. If no date range specified, always scrape (get all available data)
            if start_date is None and end_date is None:
                return True, None
            
            # 3. Check existing coverage
            existing_coverage = await self.daily_repo.get_coverage_for_asin(asin)
            
            if existing_coverage is None:
                # No existing data, should scrape
                return True, None
            
            # 4. Check if we already have sufficient coverage
            if start_date and end_date:
                if existing_coverage.contains(start_date, end_date):
                    return False, f"Already have complete coverage for {asin} from {start_date} to {end_date}"
            elif start_date:
                if existing_coverage.start_date <= start_date and existing_coverage.end_date >= date.today() - timedelta(days=1):
                    return False, f"Already have coverage for {asin} from {start_date} onwards"
            elif end_date:
                if existing_coverage.end_date >= end_date:
                    return False, f"Already have coverage for {asin} up to {end_date}"
            
            # 5. Check for partial overlap - if we have some data, we might still need to scrape
            # For now, we'll scrape if there's any gap, but this could be optimized
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking if should scrape ASIN {asin}: {e}")
            return False, f"Error checking coverage: {str(e)}"
    
    async def scrape_sales_history(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        source: str = "jungle_scout"
    ) -> ScrapingResult:
        """
        Scrape sales history for a single ASIN.
        
        Args:
            asin: Product ASIN
            start_date: Start date for scraping (if None, scrapes all available)
            end_date: End date for scraping (if None, scrapes up to yesterday)
            source: Data source identifier
            
        Returns:
            ScrapingResult: Result of the scraping operation
        """
        try:
            logger.info(f"Starting sales history scraping for ASIN: {asin}")
            
            # Check if we should scrape this ASIN
            should_scrape, skip_reason = await self.should_scrape_asin(asin, start_date, end_date)
            
            if not should_scrape:
                logger.info(f"Skipping ASIN {asin}: {skip_reason}")
                return ScrapingResult(
                    asin=asin,
                    success=True,
                    data=[],
                    skipped=True,
                    skip_reason=skip_reason
                )
            
            # Set default dates if not provided
            if end_date is None:
                end_date = date.today() - timedelta(days=1)  # Yesterday
            
            if start_date is None:
                # If no start date, try to get data from 365 days ago
                start_date = end_date - timedelta(days=365)
            
            # Validate date constraints
            today = date.today()
            max_old_date = today - timedelta(days=365)
            
            if start_date < max_old_date:
                logger.warning(f"Start date {start_date} is too old, adjusting to {max_old_date}")
                start_date = max_old_date
            
            if end_date > today:
                logger.warning(f"End date {end_date} is in the future, adjusting to {today - timedelta(days=1)}")
                end_date = today - timedelta(days=1)
            
            # Fetch data from Jungle Scout API
            logger.info(f"Fetching sales history for ASIN {asin} from {start_date} to {end_date}")
            
            api_response = get_sales_history(
                asin=asin,
                marketplace="us",
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            # Extract and validate sales data
            sales_data = self._extract_sales_data_from_api_response(api_response)
            
            if not sales_data:
                logger.warning(f"No sales data found for ASIN {asin}")
                return ScrapingResult(
                    asin=asin,
                    success=True,
                    data=[],
                    error_message="No sales data available from API"
                )
            
            # Save to database
            inserted_count = await self.daily_repo.insert_sales_data(asin, source, sales_data)
            
            # Trigger monthly aggregation
            if inserted_count > 0:
                await self.monthly_repo.aggregate_daily_to_monthly(asin, source)
            
            logger.info(f"Successfully scraped {len(sales_data)} records for ASIN {asin}")
            
            return ScrapingResult(
                asin=asin,
                success=True,
                data=sales_data
            )
            
        except JungleScoutAPIError as e:
            logger.error(f"Jungle Scout API error for ASIN {asin}: {e}")
            return ScrapingResult(
                asin=asin,
                success=False,
                data=[],
                error_message=f"Jungle Scout API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error scraping ASIN {asin}: {e}")
            return ScrapingResult(
                asin=asin,
                success=False,
                data=[],
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _extract_sales_data_from_api_response(self, api_response: Dict[str, Any]) -> List[SalesHistoryDataPoint]:
        """
        Extract sales data from Jungle Scout API response.
        
        Args:
            api_response: Raw API response from Jungle Scout
            
        Returns:
            List[SalesHistoryDataPoint]: List of sales data points
        """
        sales_records = []
        
        try:
            # Extract data from the API response
            # The structure is: data[0]['attributes']['data']
            data = api_response.get('data', [])
            
            if isinstance(data, list) and len(data) > 0:
                # Get the first (and usually only) result
                first_result = data[0]
                attributes = first_result.get('attributes', {})
                sales_data = attributes.get('data', [])
                
                if isinstance(sales_data, list):
                    for record in sales_data:
                        # Extract the required fields
                        record_date = record.get('date')
                        units_sold = record.get('estimated_units_sold')
                        price = record.get('last_known_price')
                        
                        # Validate data
                        if all(v is not None for v in [record_date, units_sold, price]):
                            try:
                                sales_records.append(SalesHistoryDataPoint(
                                    sales_date=date.fromisoformat(record_date),
                                    estimated_units_sold=int(units_sold),
                                    last_known_price=Decimal(str(price))
                                ))
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Invalid data in API response: {record}, error: {e}")
                                continue
            
            logger.info(f"Extracted {len(sales_records)} valid sales records from API response")
            
        except Exception as e:
            logger.error(f"Error extracting sales data from API response: {e}")
            logger.error(f"API response structure: {api_response}")
        
        return sales_records
    
    async def scrape_multiple_asins(
        self, 
        asins: List[str], 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> Dict[str, ScrapingResult]:
        """
        Scrape sales history for multiple ASINs with smart logic.
        
        Args:
            asins: List of ASINs to scrape
            start_date: Optional start date for scraping
            end_date: Optional end date for scraping
            platform_source: Platform source (amazon, walmart, etc.)
            api_source: Data source API (jungle_scout, etc.)
            
        Returns:
            Dict[str, ScrapingResult]: Results for each ASIN
        """
        try:
            logger.info(f"Starting scraping for {len(asins)} ASINs")
            
            # Check existing data coverage for all ASINs
            coverage = await self.daily_repo.get_data_coverage_for_multiple_asins(
                asins, start_date, end_date, platform_source, api_source
            )
            
            # Determine what needs to be scraped
            scraping_results = {}
            
            for asin in asins:
                existing_coverage = coverage.get(asin)
                
                if existing_coverage and self._has_complete_coverage(existing_coverage, start_date, end_date):
                    # Skip if we have complete coverage
                    scraping_results[asin] = ScrapingResult(
                        asin=asin,
                        success=True,
                        data=[],
                        skipped=True,
                        skip_reason="Complete data coverage already exists"
                    )
                    logger.info(f"Skipping ASIN {asin}: complete coverage exists")
                else:
                    # Scrape this ASIN
                    result = await self._scrape_single_asin(asin, start_date, end_date, platform_source, api_source)
                    scraping_results[asin] = result
            
            return scraping_results
            
        except Exception as e:
            logger.error(f"Error in scrape_multiple_asins: {e}")
            # Return failed results for all ASINs
            return {
                asin: ScrapingResult(
                    asin=asin,
                    success=False,
                    data=[],
                    error_message=str(e)
                ) for asin in asins
            }
    
    async def _scrape_single_asin(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: str = "amazon",
        api_source: str = "jungle_scout"
    ) -> ScrapingResult:
        """Scrape sales history for a single ASIN."""
        try:
            logger.info(f"Scraping sales history for ASIN {asin}")
            
            # Get sales data from Jungle Scout API
            # Convert dates to strings if provided
            start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
            end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None
            
            sales_data = get_sales_history(
                asin=asin,
                marketplace="us",
                start_date=start_date_str,
                end_date=end_date_str
            )
            
            if not sales_data:
                return ScrapingResult(
                    asin=asin,
                    success=True,
                    data=[],
                    error_message="No sales data available from API"
                )
            
            # Convert to our data model
            data_points = []
            
            # Extract sales data from the nested API response structure
            if 'data' in sales_data and len(sales_data['data']) > 0:
                attributes = sales_data['data'][0].get('attributes', {})
                sales_records = attributes.get('data', [])
                
                for record in sales_records:
                    data_points.append(SalesHistoryDataPoint(
                        sales_date=record['date'],
                        estimated_units_sold=record['estimated_units_sold'],
                        last_known_price=Decimal(str(record['last_known_price']))
                    ))
            
            # Insert into database
            if data_points:
                inserted_count = await self.daily_repo.insert_sales_data(
                    asin, platform_source, api_source, data_points
                )
                logger.info(f"Inserted {inserted_count} records for ASIN {asin}")
                
                # Aggregate to monthly data
                await self.monthly_repo.aggregate_daily_to_monthly(
                    asin, platform_source, api_source
                )
            
            return ScrapingResult(
                asin=asin,
                success=True,
                data=data_points
            )
            
        except JungleScoutAPIError as e:
            logger.error(f"Jungle Scout API error for ASIN {asin}: {e}")
            return ScrapingResult(
                asin=asin,
                success=False,
                data=[],
                error_message=f"API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error scraping ASIN {asin}: {e}")
            return ScrapingResult(
                asin=asin,
                success=False,
                data=[],
                error_message=str(e)
            )
    
    def _has_complete_coverage(self, coverage: DateRange, start_date: Optional[date], end_date: Optional[date]) -> bool:
        """
        Check if existing coverage is sufficient for the requested date range.
        
        Args:
            coverage: Existing data coverage
            start_date: Requested start date
            end_date: Requested end date
            
        Returns:
            bool: True if coverage is complete
        """
        if not coverage:
            return False
            
        if start_date and end_date:
            return coverage.contains(start_date, end_date)
        elif start_date:
            return coverage.start_date <= start_date and coverage.end_date >= date.today() - timedelta(days=1)
        elif end_date:
            return coverage.end_date >= end_date
        else:
            # No date range specified, check if we have recent data
            return coverage.end_date >= date.today() - timedelta(days=7)
    
    def _create_scraping_summary(self, results: Dict[str, ScrapingResult]) -> SalesHistoryScrapingSummary:
        """Create a summary of scraping results."""
        total_requested = len(results)
        scraped = sum(1 for r in results.values() if r.success and not r.skipped)
        skipped = sum(1 for r in results.values() if r.skipped)
        failed = sum(1 for r in results.values() if not r.success and not r.skipped)
        
        invalid_asins = []
        scraping_errors = {}
        
        for asin, result in results.items():
            if result.skip_reason and "not found in product database" in result.skip_reason:
                invalid_asins.append(asin)
            elif result.error_message:
                scraping_errors[asin] = result.error_message
        
        return SalesHistoryScrapingSummary(
            total_requested=total_requested,
            scraped=scraped,
            skipped=skipped,
            failed=failed,
            invalid_asins=invalid_asins,
            scraping_errors=scraping_errors
        ) 