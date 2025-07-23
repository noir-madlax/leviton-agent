#!/usr/bin/env python3
"""
Sales History API Tests

This script tests all sales history API endpoints and prints database results
for manual inspection. It includes setup, execution, and cleanup phases.

Usage:
    python test_sales_history_api.py

Requirements:
    - JUNGLE_SCOUT_API_KEY in backend/.env
    - Supabase credentials in backend/.env
    - Test ASINs in product_wide_table
"""

import os
import sys
import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sales_history.services.sales_history_service import SalesHistoryService
from sales_history.models import (
    SalesHistoryScrapingRequest,
    SalesHistoryQueryRequest
)
from sales_history.repositories.sales_history_repository import SalesHistoryRepository
from sales_history.repositories.sales_history_monthly_repository import SalesHistoryMonthlyRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_ASINS = [
    "B08N5WRWNW",  # Example ASIN 1
    "B07ZPKBL9V",  # Example ASIN 2
    "B08SJ3Z8XD",  # Example ASIN 3
    "INVALID_ASIN" # Invalid ASIN for testing
]

class SalesHistoryAPITester:
    """Test runner for sales history API endpoints."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.service = SalesHistoryService()
        self.daily_repo = SalesHistoryRepository()
        self.monthly_repo = SalesHistoryMonthlyRepository()
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all tests and print results."""
        logger.info("=" * 60)
        logger.info("STARTING SALES HISTORY API TESTS")
        logger.info("=" * 60)
        
        try:
            # Test 1: Validate ASINs exist in product database
            await self.test_asin_validation()
            
            # Test 2: Scrape sales history
            await self.test_scrape_sales_history()
            
            # Test 3: Get daily sales history
            await self.test_get_daily_sales_history()
            
            # Test 4: Monthly aggregation
            await self.test_monthly_aggregation()
            
            # Test 5: Get monthly sales history
            await self.test_get_monthly_sales_history()
            
            # Test 6: Get sales statistics
            await self.test_get_sales_stats()
            
            # Test 7: Test date filtering
            await self.test_date_filtering()
            
            # Test 8: Test error handling
            await self.test_error_handling()
            
            # Print final summary
            await self.print_test_summary()
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            raise
    
    async def test_asin_validation(self):
        """Test ASIN validation against product database."""
        logger.info("\n" + "=" * 40)
        logger.info("TEST 1: ASIN VALIDATION")
        logger.info("=" * 40)
        
        # Check which ASINs exist in product database
        asin_existence = await self.daily_repo.check_multiple_asins_exist(
            TEST_ASINS, 
            platform_source="amazon"
        )
        
        logger.info("ASIN Validation Results:")
        for asin, exists in asin_existence.items():
            status = "✅ EXISTS" if exists else "❌ NOT FOUND"
            logger.info(f"  {asin}: {status}")
        
        # Filter valid ASINs for subsequent tests
        self.valid_asins = [asin for asin, exists in asin_existence.items() if exists]
        logger.info(f"\nValid ASINs for testing: {self.valid_asins}")
        
        if not self.valid_asins:
            logger.warning("No valid ASINs found! Tests may fail.")
        
        self.test_results.append({
            "test": "ASIN Validation",
            "status": "PASS" if self.valid_asins else "FAIL",
            "valid_asins": self.valid_asins,
            "invalid_asins": [asin for asin, exists in asin_existence.items() if not exists]
        })
    
    async def test_scrape_sales_history(self):
        """Test sales history scraping."""
        logger.info("\n" + "=" * 40)
        logger.info("TEST 2: SALES HISTORY SCRAPING")
        logger.info("=" * 40)
        
        if not self.valid_asins:
            logger.warning("Skipping scraping test - no valid ASINs")
            return
        
        # Create scraping request
        request = SalesHistoryScrapingRequest(
            asins=self.valid_asins,
            start_date=date.today() - timedelta(days=30),  # Last 30 days
            end_date=date.today() - timedelta(days=1),     # Yesterday
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info(f"Scraping request: {request.model_dump()}")
        
        # Execute scraping
        response = await self.service.scrape_sales_history(request)
        
        # Print results
        logger.info(f"Scraping response success: {response.success}")
        logger.info(f"Scraping message: {response.message}")
        logger.info(f"Scraping summary: {response.scraping_summary.model_dump()}")
        
        if response.warnings:
            logger.info("Warnings:")
            for warning in response.warnings:
                logger.info(f"  - {warning}")
        
        # Print scraped data
        logger.info("\nScraped Data:")
        for asin, data in response.data.items():
            logger.info(f"  {asin}: {len(data)} records")
            if data:
                # Show first few records
                for i, record in enumerate(data[:3]):
                    logger.info(f"    {i+1}. {record.sales_date}: {record.estimated_units_sold} units @ ${record.last_known_price}")
                if len(data) > 3:
                    logger.info(f"    ... and {len(data) - 3} more records")
        
        self.test_results.append({
            "test": "Sales History Scraping",
            "status": "PASS" if response.success else "FAIL",
            "scraped_asins": response.scraping_summary.scraped,
            "skipped_asins": response.scraping_summary.skipped,
            "failed_asins": response.scraping_summary.failed,
            "total_records": sum(len(data) for data in response.data.values())
        })
    
    async def test_get_daily_sales_history(self):
        """Test daily sales history retrieval."""
        logger.info("\n" + "=" * 40)
        logger.info("TEST 3: GET DAILY SALES HISTORY")
        logger.info("=" * 40)
        
        if not self.valid_asins:
            logger.warning("Skipping daily retrieval test - no valid ASINs")
            return
        
        # Create query request
        request = SalesHistoryQueryRequest(
            asins=self.valid_asins,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=1),
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info(f"Daily query request: {request.model_dump()}")
        
        # Execute query
        response = await self.service.get_daily_sales_history(request)
        
        # Print results
        logger.info(f"Daily query success: {response.success}")
        logger.info(f"Daily query message: {response.message}")
        logger.info(f"Query summary: {response.query_summary}")
        
        if response.warnings:
            logger.info("Warnings:")
            for warning in response.warnings:
                logger.info(f"  - {warning}")
        
        # Print retrieved data
        logger.info("\nRetrieved Daily Data:")
        for asin, data in response.data.items():
            logger.info(f"  {asin}: {len(data)} records")
            if data:
                # Show first few records
                for i, record in enumerate(data[:3]):
                    logger.info(f"    {i+1}. {record.sales_date}: {record.estimated_units_sold} units @ ${record.last_known_price}")
                if len(data) > 3:
                    logger.info(f"    ... and {len(data) - 3} more records")
        
        self.test_results.append({
            "test": "Get Daily Sales History",
            "status": "PASS" if response.success else "FAIL",
            "asins_with_data": response.query_summary.get("asins_with_data", 0),
            "asins_without_data": response.query_summary.get("asins_without_data", 0),
            "total_records": response.query_summary.get("total_records", 0)
        })
    
    async def test_monthly_aggregation(self):
        """Test monthly aggregation functionality."""
        logger.info("\n" + "=" * 40)
        logger.info("TEST 4: MONTHLY AGGREGATION")
        logger.info("=" * 40)
        
        if not self.valid_asins:
            logger.warning("Skipping monthly aggregation test - no valid ASINs")
            return
        
        # Test aggregation for first valid ASIN
        test_asin = self.valid_asins[0]
        
        logger.info(f"Testing monthly aggregation for ASIN: {test_asin}")
        
        # Aggregate daily data to monthly
        aggregated_count = await self.monthly_repo.aggregate_daily_to_monthly(
            test_asin, 
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info(f"Aggregated {aggregated_count} months for ASIN {test_asin}")
        
        # Get the aggregated monthly data
        monthly_data = await self.monthly_repo.get_monthly_data(
            [test_asin],
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        asin_monthly_data = monthly_data.get(test_asin, [])
        logger.info(f"Retrieved {len(asin_monthly_data)} monthly records")
        
        if asin_monthly_data:
            logger.info("Monthly Data:")
            for record in asin_monthly_data:
                logger.info(f"  {record.year_month_date}: {record.total_units_sold} units @ ${record.average_price} avg ({record.days_in_month} days)")
        
        self.test_results.append({
            "test": "Monthly Aggregation",
            "status": "PASS" if aggregated_count > 0 else "FAIL",
            "aggregated_months": aggregated_count,
            "retrieved_months": len(asin_monthly_data)
        })
    
    async def test_get_monthly_sales_history(self):
        """Test monthly sales history retrieval."""
        logger.info("\n" + "=" * 40)
        logger.info("TEST 5: GET MONTHLY SALES HISTORY")
        logger.info("=" * 40)
        
        if not self.valid_asins:
            logger.warning("Skipping monthly retrieval test - no valid ASINs")
            return
        
        # Create query request
        request = SalesHistoryQueryRequest(
            asins=self.valid_asins,
            start_date=date.today() - timedelta(days=90),  # Last 3 months
            end_date=date.today() - timedelta(days=1),
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info(f"Monthly query request: {request.model_dump()}")
        
        # Execute query
        response = await self.service.get_monthly_sales_history(request)
        
        # Print results
        logger.info(f"Monthly query success: {response.success}")
        logger.info(f"Monthly query message: {response.message}")
        logger.info(f"Query summary: {response.query_summary}")
        
        if response.warnings:
            logger.info("Warnings:")
            for warning in response.warnings:
                logger.info(f"  - {warning}")
        
        # Print retrieved data
        logger.info("\nRetrieved Monthly Data:")
        for asin, data in response.data.items():
            logger.info(f"  {asin}: {len(data)} months")
            if data:
                # Show all monthly records
                for record in data:
                    logger.info(f"    {record.year_month_date}: {record.total_units_sold} units @ ${record.average_price} avg ({record.days_in_month} days)")
        
        self.test_results.append({
            "test": "Get Monthly Sales History",
            "status": "PASS" if response.success else "FAIL",
            "asins_with_data": response.query_summary.get("asins_with_data", 0),
            "asins_without_data": response.query_summary.get("asins_without_data", 0),
            "total_months": response.query_summary.get("total_months", 0)
        })
    
    async def test_get_sales_stats(self):
        """Test sales statistics retrieval."""
        logger.info("\n" + "=" * 40)
        logger.info("TEST 6: GET SALES STATISTICS")
        logger.info("=" * 40)
        
        if not self.valid_asins:
            logger.warning("Skipping stats test - no valid ASINs")
            return
        
        # Test stats for first valid ASIN
        test_asin = self.valid_asins[0]
        
        logger.info(f"Getting stats for ASIN: {test_asin}")
        
        # Get stats
        stats = await self.service.get_sales_stats(
            test_asin,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=1),
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        # Print stats
        logger.info(f"Sales Statistics for {test_asin}:")
        logger.info(f"  Daily Stats:")
        daily_stats = stats["daily_stats"]
        logger.info(f"    Total Records: {daily_stats['total_records']}")
        logger.info(f"    Date Range: {daily_stats['min_date']} to {daily_stats['max_date']}")
        logger.info(f"    Total Units Sold: {daily_stats['total_units_sold']}")
        logger.info(f"    Average Price: ${daily_stats['average_price']:.2f}")
        logger.info(f"    Price Range: ${daily_stats['min_price']:.2f} - ${daily_stats['max_price']:.2f}")
        
        logger.info(f"  Monthly Stats:")
        monthly_stats = stats["monthly_stats"]
        logger.info(f"    Total Months: {monthly_stats['total_months']}")
        logger.info(f"    Month Range: {monthly_stats['min_month']} to {monthly_stats['max_month']}")
        logger.info(f"    Total Units Sold: {monthly_stats['total_units_sold']}")
        logger.info(f"    Average Price: ${monthly_stats['average_price']:.2f}")
        logger.info(f"    Price Range: ${monthly_stats['min_price']:.2f} - ${monthly_stats['max_price']:.2f}")
        logger.info(f"    Total Days: {monthly_stats['total_days']}")
        
        self.test_results.append({
            "test": "Get Sales Statistics",
            "status": "PASS",
            "daily_records": daily_stats['total_records'],
            "monthly_records": monthly_stats['total_months'],
            "total_units": daily_stats['total_units_sold']
        })
    
    async def test_date_filtering(self):
        """Test date filtering functionality."""
        logger.info("\n" + "=" * 40)
        logger.info("TEST 7: DATE FILTERING")
        logger.info("=" * 40)
        
        if not self.valid_asins:
            logger.warning("Skipping date filtering test - no valid ASINs")
            return
        
        # Test different date ranges
        test_ranges = [
            ("7 days", date.today() - timedelta(days=7), date.today() - timedelta(days=1)),
            ("14 days", date.today() - timedelta(days=14), date.today() - timedelta(days=1)),
            ("30 days", date.today() - timedelta(days=30), date.today() - timedelta(days=1))
        ]
        
        for range_name, start_date, end_date in test_ranges:
            logger.info(f"\nTesting {range_name} range: {start_date} to {end_date}")
            
            # Test daily data
            daily_data = await self.daily_repo.get_sales_data(
                self.valid_asins,
                start_date=start_date,
                end_date=end_date,
                platform_source="amazon",
                api_source="jungle_scout"
            )
            
            total_daily_records = sum(len(data) for data in daily_data.values())
            logger.info(f"  Daily records: {total_daily_records}")
            
            # Test monthly data
            monthly_data = await self.monthly_repo.get_monthly_data(
                self.valid_asins,
                start_date=start_date,
                end_date=end_date,
                platform_source="amazon",
                api_source="jungle_scout"
            )
            
            total_monthly_records = sum(len(data) for data in monthly_data.values())
            logger.info(f"  Monthly records: {total_monthly_records}")
        
        self.test_results.append({
            "test": "Date Filtering",
            "status": "PASS",
            "ranges_tested": len(test_ranges)
        })
    
    async def test_error_handling(self):
        """Test error handling with invalid inputs."""
        logger.info("\n" + "=" * 40)
        logger.info("TEST 8: ERROR HANDLING")
        logger.info("=" * 40)
        
        # Test with invalid ASINs
        invalid_asins = ["INVALID_ASIN_1", "INVALID_ASIN_2"]
        
        logger.info("Testing with invalid ASINs:")
        logger.info(f"  Invalid ASINs: {invalid_asins}")
        
        # Test ASIN validation
        asin_existence = await self.daily_repo.check_multiple_asins_exist(
            invalid_asins, 
            platform_source="amazon"
        )
        
        for asin, exists in asin_existence.items():
            status = "EXISTS" if exists else "NOT FOUND"
            logger.info(f"  {asin}: {status}")
        
        # Test scraping with invalid ASINs
        request = SalesHistoryScrapingRequest(
            asins=invalid_asins,
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        response = await self.service.scrape_sales_history(request)
        
        logger.info(f"Scraping response with invalid ASINs:")
        logger.info(f"  Success: {response.success}")
        logger.info(f"  Message: {response.message}")
        logger.info(f"  Invalid ASINs: {response.scraping_summary.invalid_asins}")
        
        self.test_results.append({
            "test": "Error Handling",
            "status": "PASS" if not response.success else "FAIL",
            "invalid_asins_tested": len(invalid_asins),
            "invalid_asins_found": len(response.scraping_summary.invalid_asins)
        })
    
    async def print_test_summary(self):
        """Print comprehensive test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("\nDetailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            logger.info(f"  {status_icon} {result['test']}: {result['status']}")
            
            # Print additional details for each test
            for key, value in result.items():
                if key not in ["test", "status"]:
                    if isinstance(value, list):
                        logger.info(f"    {key}: {', '.join(map(str, value))}")
                    else:
                        logger.info(f"    {key}: {value}")

async def main():
    """Main test execution function."""
    tester = SalesHistoryAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 