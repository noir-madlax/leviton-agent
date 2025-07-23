"""Main sales history service for orchestrating scraping and data retrieval."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from ..models import (
    SalesHistoryScrapingRequest,
    SalesHistoryQueryRequest,
    SalesHistoryScrapingResponse,
    SalesHistoryQueryResponse,
    SalesHistoryMonthlyQueryResponse,
    SalesHistoryYearlyQueryResponse,
    SalesHistoryScrapingSummary,
    ScrapingResult
)
from ..repositories.sales_history_repository import SalesHistoryRepository
from ..repositories.sales_history_monthly_repository import SalesHistoryMonthlyRepository
from ..repositories.sales_history_yearly_repository import SalesHistoryYearlyRepository
from .sales_history_scraper_service import SalesHistoryScraperService

logger = logging.getLogger(__name__)

class SalesHistoryService:
    """Main service for sales history operations."""
    
    def __init__(self):
        """Initialize the sales history service."""
        self.daily_repo = SalesHistoryRepository()
        self.monthly_repo = SalesHistoryMonthlyRepository()
        self.yearly_repo = SalesHistoryYearlyRepository()
        self.scraper_service = SalesHistoryScraperService()
    
    async def scrape_sales_history(self, request: SalesHistoryScrapingRequest) -> SalesHistoryScrapingResponse:
        """
        Scrape sales history for multiple ASINs with smart logic.
        
        Args:
            request: Scraping request with ASINs and date range
            
        Returns:
            SalesHistoryScrapingResponse: Response with scraping results
        """
        try:
            logger.info(f"Starting sales history scraping for {len(request.asins)} ASINs")
            
            # Validate ASINs exist in product database
            asin_existence = await self.daily_repo.check_multiple_asins_exist(
                request.asins, 
                platform_source=request.platform_source
            )
            invalid_asins = [asin for asin, exists in asin_existence.items() if not exists]
            
            # Filter out invalid ASINs
            valid_asins = [asin for asin in request.asins if asin_existence[asin]]
            
            if not valid_asins:
                return SalesHistoryScrapingResponse(
                    success=False,
                    message="No valid ASINs found in product database",
                    scraping_summary=SalesHistoryScrapingSummary(
                        total_requested=len(request.asins),
                        scraped=0,
                        skipped=0,
                        failed=len(request.asins),
                        invalid_asins=invalid_asins,
                        scraping_errors={}
                    ),
                    warnings=[f"ASIN {asin} not found in product database" for asin in invalid_asins],
                    data={}
                )
            
            # Scrape data for valid ASINs
            scraping_results = await self.scraper_service.scrape_multiple_asins(
                valid_asins,
                request.start_date,
                request.end_date,
                request.platform_source,
                request.api_source
            )
            
            # Create response data
            response_data = {}
            warnings = []
            
            for asin, result in scraping_results.items():
                if result.success:
                    response_data[asin] = result.data
                else:
                    response_data[asin] = []
                    warnings.append(f"Failed to scrape {asin}: {result.error_message}")
            
            # Add empty data for invalid ASINs
            for asin in invalid_asins:
                response_data[asin] = []
            
            # Create scraping summary
            summary = self.scraper_service._create_scraping_summary(scraping_results)
            summary.invalid_asins = invalid_asins
            
            # Add warnings for invalid ASINs
            warnings.extend([f"ASIN {asin} not found in product database" for asin in invalid_asins])
            
            success = summary.scraped > 0 or summary.skipped > 0
            message = f"Scraping completed: {summary.scraped} scraped, {summary.skipped} skipped, {summary.failed} failed"
            
            return SalesHistoryScrapingResponse(
                success=success,
                message=message,
                scraping_summary=summary,
                warnings=warnings,
                data=response_data
            )
            
        except Exception as e:
            logger.error(f"Error in scrape_sales_history: {e}")
            return SalesHistoryScrapingResponse(
                success=False,
                message=f"Scraping failed: {str(e)}",
                scraping_summary=SalesHistoryScrapingSummary(
                    total_requested=len(request.asins),
                    scraped=0,
                    skipped=0,
                    failed=len(request.asins),
                    invalid_asins=[],
                    scraping_errors={}
                ),
                warnings=[f"Unexpected error: {str(e)}"],
                data={}
            )
    
    async def get_daily_sales_history(self, request: SalesHistoryQueryRequest) -> SalesHistoryQueryResponse:
        """
        Get daily sales history data for multiple ASINs.
        
        Args:
            request: Query request with ASINs and optional filters
            
        Returns:
            SalesHistoryQueryResponse: Response with daily sales data
        """
        try:
            logger.info(f"Getting daily sales history for {len(request.asins)} ASINs")
            
            # Get daily data from database
            data = await self.daily_repo.get_sales_data(
                request.asins,
                request.start_date,
                request.end_date,
                request.platform_source,
                request.api_source
            )
            
            # Generate warnings for ASINs with no data
            warnings = []
            total_records = 0
            
            for asin, records in data.items():
                if not records:
                    warnings.append(f"No daily sales data available for ASIN {asin}")
                else:
                    total_records += len(records)
            
            # Create query summary
            query_summary = {
                "total_asins": len(request.asins),
                "asins_with_data": sum(1 for records in data.values() if records),
                "asins_without_data": sum(1 for records in data.values() if not records),
                "total_records": total_records,
                "date_range": {
                    "start_date": request.start_date.isoformat() if request.start_date else None,
                    "end_date": request.end_date.isoformat() if request.end_date else None
                },
                "platform_source": request.platform_source,
                "api_source": request.api_source
            }
            
            success = total_records > 0
            message = f"Retrieved {total_records} daily records for {len(request.asins)} ASINs"
            
            return SalesHistoryQueryResponse(
                success=success,
                message=message,
                data=data,
                warnings=warnings,
                query_summary=query_summary
            )
            
        except Exception as e:
            logger.error(f"Error in get_daily_sales_history: {e}")
            return SalesHistoryQueryResponse(
                success=False,
                message=f"Query failed: {str(e)}",
                data={},
                warnings=[f"Unexpected error: {str(e)}"],
                query_summary={}
            )
    
    async def get_monthly_sales_history(self, request: SalesHistoryQueryRequest) -> SalesHistoryMonthlyQueryResponse:
        """
        Get monthly aggregated sales history data for multiple ASINs.
        
        Args:
            request: Query request with ASINs and optional filters
            
        Returns:
            SalesHistoryMonthlyQueryResponse: Response with monthly sales data
        """
        try:
            logger.info(f"Getting monthly sales history for {len(request.asins)} ASINs")
            
            # Get monthly data from database
            data = await self.monthly_repo.get_monthly_data(
                request.asins,
                request.start_date,
                request.end_date,
                request.platform_source,
                request.api_source
            )
            
            # Generate warnings for ASINs with no data
            warnings = []
            total_months = 0
            
            for asin, records in data.items():
                if not records:
                    warnings.append(f"No monthly sales data available for ASIN {asin}")
                else:
                    total_months += len(records)
            
            # Create query summary
            query_summary = {
                "total_asins": len(request.asins),
                "asins_with_data": sum(1 for records in data.values() if records),
                "asins_without_data": sum(1 for records in data.values() if not records),
                "total_months": total_months,
                "date_range": {
                    "start_date": request.start_date.isoformat() if request.start_date else None,
                    "end_date": request.end_date.isoformat() if request.end_date else None
                },
                "platform_source": request.platform_source,
                "api_source": request.api_source
            }
            
            success = total_months > 0
            message = f"Retrieved {total_months} monthly records for {len(request.asins)} ASINs"
            
            return SalesHistoryMonthlyQueryResponse(
                success=success,
                message=message,
                data=data,
                warnings=warnings,
                query_summary=query_summary
            )
            
        except Exception as e:
            logger.error(f"Error in get_monthly_sales_history: {e}")
            return SalesHistoryMonthlyQueryResponse(
                success=False,
                message=f"Query failed: {str(e)}",
                data={},
                warnings=[f"Unexpected error: {str(e)}"],
                query_summary={}
            )
    
    async def get_yearly_sales_history(self, request: SalesHistoryQueryRequest) -> SalesHistoryYearlyQueryResponse:
        """
        Get yearly sales history for multiple ASINs (rolling year from latest scraping date).
        
        Args:
            request: Query request with ASINs and filters
            
        Returns:
            SalesHistoryYearlyQueryResponse: Response with yearly sales data
        """
        try:
            logger.info(f"Getting yearly sales history for {len(request.asins)} ASINs")
            
            # Get yearly data
            data = await self.yearly_repo.get_yearly_data(
                request.asins,
                platform_source=request.platform_source,
                api_source=request.api_source
            )
            
            # Create query summary
            total_asins = len(request.asins)
            asins_with_data = sum(1 for asin_data in data.values() if asin_data)
            total_yearly_records = sum(len(asin_data) for asin_data in data.values())
            
            query_summary = {
                "total_asins_requested": total_asins,
                "asins_with_data": asins_with_data,
                "total_yearly_records": total_yearly_records,
                "platform_source": request.platform_source,
                "api_source": request.api_source
            }
            
            return SalesHistoryYearlyQueryResponse(
                success=True,
                message=f"Successfully retrieved yearly sales data for {asins_with_data}/{total_asins} ASINs",
                data=data,
                warnings=[],
                query_summary=query_summary
            )
            
        except Exception as e:
            logger.error(f"Error getting yearly sales history: {e}")
            return SalesHistoryYearlyQueryResponse(
                success=False,
                message=f"Query failed: {str(e)}",
                data={},
                warnings=[f"Unexpected error: {str(e)}"],
                query_summary={}
            )
    
    async def get_sales_stats(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for an ASIN's sales data.
        
        Args:
            asin: Product ASIN
            start_date: Optional start date filter
            end_date: Optional end date filter
            platform_source: Optional platform source filter
            api_source: Optional API source filter
            
        Returns:
            Dict[str, Any]: Sales statistics
        """
        try:
            # Get daily stats
            daily_stats = await self.daily_repo.get_stats_for_asin(
                asin, start_date, end_date, platform_source, api_source
            )
            
            # Get monthly stats
            monthly_stats = await self.monthly_repo.get_monthly_stats_for_asin(
                asin, start_date, end_date, platform_source, api_source
            )
            
            return {
                "asin": asin,
                "daily_stats": daily_stats,
                "monthly_stats": monthly_stats,
                "date_range": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "platform_source": platform_source,
                "api_source": api_source
            }
            
        except Exception as e:
            logger.error(f"Error getting sales stats for ASIN {asin}: {e}")
            raise
    
    async def delete_sales_data(
        self, 
        asin: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        platform_source: Optional[str] = None,
        api_source: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Delete sales data for an ASIN within a date range.
        
        Args:
            asin: Product ASIN
            start_date: Optional start date filter
            end_date: Optional end date filter
            platform_source: Optional platform source filter
            api_source: Optional API source filter
            
        Returns:
            Dict[str, int]: Number of records deleted from daily and monthly tables
        """
        try:
            # Delete from daily table
            daily_deleted = await self.daily_repo.delete_sales_data(
                asin, start_date, end_date, platform_source, api_source
            )
            
            # Delete from monthly table
            monthly_deleted = await self.monthly_repo.delete_monthly_data(
                asin, start_date, end_date, platform_source, api_source
            )
            
            total_deleted = daily_deleted + monthly_deleted
            
            logger.info(f"Deleted {total_deleted} total records for ASIN {asin} (daily: {daily_deleted}, monthly: {monthly_deleted})")
            
            return {
                "daily_records_deleted": daily_deleted,
                "monthly_records_deleted": monthly_deleted,
                "total_records_deleted": total_deleted
            }
            
        except Exception as e:
            logger.error(f"Error deleting sales data for ASIN {asin}: {e}")
            raise 