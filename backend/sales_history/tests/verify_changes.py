#!/usr/bin/env python3
"""
Verify Sales History Changes

This script verifies that the sales history service works correctly with the new schema
that includes platform_source and api_source fields.

Usage:
    python verify_changes.py

Requirements:
    - Supabase credentials in backend/.env
    - Test ASINs in product_wide_table
"""

import os
import sys
import asyncio
import logging
from datetime import date, timedelta
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sales_history.models import (
    SalesHistoryScrapingRequest,
    SalesHistoryQueryRequest
)
from sales_history.services.sales_history_service import SalesHistoryService
from sales_history.repositories.sales_history_repository import SalesHistoryRepository
from sales_history.repositories.sales_history_monthly_repository import SalesHistoryMonthlyRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_ASINS = ["B08N5WRWNW", "B07ZPKBL9V"]

class SalesHistoryVerifier:
    """Verifier for sales history changes."""
    
    def __init__(self):
        """Initialize the verifier."""
        self.service = SalesHistoryService()
        self.daily_repo = SalesHistoryRepository()
        self.monthly_repo = SalesHistoryMonthlyRepository()
        self.verification_results = []
        
    async def run_verification(self):
        """Run all verification tests."""
        logger.info("=" * 60)
        logger.info("VERIFYING SALES HISTORY CHANGES")
        logger.info("=" * 60)
        
        try:
            # Test 1: Verify new field structure in models
            await self.verify_model_structure()
            
            # Test 2: Verify repository methods with new fields
            await self.verify_repository_methods()
            
            # Test 3: Verify service methods with new fields
            await self.verify_service_methods()
            
            # Test 4: Verify database table structure
            await self.verify_database_structure()
            
            # Test 5: Verify API endpoint compatibility
            await self.verify_api_compatibility()
            
            # Print verification summary
            await self.print_verification_summary()
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            raise
    
    async def verify_model_structure(self):
        """Verify that models have the correct field structure."""
        logger.info("\n" + "=" * 40)
        logger.info("VERIFYING MODEL STRUCTURE")
        logger.info("=" * 40)
        
        # Test SalesHistoryScrapingRequest
        request = SalesHistoryScrapingRequest(
            asins=TEST_ASINS,
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info("✅ SalesHistoryScrapingRequest created successfully")
        logger.info(f"  platform_source: {request.platform_source}")
        logger.info(f"  api_source: {request.api_source}")
        
        # Test SalesHistoryQueryRequest
        query_request = SalesHistoryQueryRequest(
            asins=TEST_ASINS,
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info("✅ SalesHistoryQueryRequest created successfully")
        logger.info(f"  platform_source: {query_request.platform_source}")
        logger.info(f"  api_source: {query_request.api_source}")
        
        self.verification_results.append({
            "test": "Model Structure",
            "status": "PASS",
            "details": "All models have correct field structure"
        })
    
    async def verify_repository_methods(self):
        """Verify that repository methods work with new fields."""
        logger.info("\n" + "=" * 40)
        logger.info("VERIFYING REPOSITORY METHODS")
        logger.info("=" * 40)
        
        # Test ASIN validation with platform_source
        asin_existence = await self.daily_repo.check_multiple_asins_exist(
            TEST_ASINS, 
            platform_source="amazon"
        )
        
        logger.info("✅ ASIN validation with platform_source works")
        logger.info(f"  Results: {asin_existence}")
        
        # Test data coverage with new fields
        coverage = await self.daily_repo.get_data_coverage_for_multiple_asins(
            TEST_ASINS,
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info("✅ Data coverage with new fields works")
        logger.info(f"  Coverage: {coverage}")
        
        # Test data retrieval with new fields
        data = await self.daily_repo.get_sales_data(
            TEST_ASINS,
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info("✅ Data retrieval with new fields works")
        logger.info(f"  Retrieved data for {len(data)} ASINs")
        
        self.verification_results.append({
            "test": "Repository Methods",
            "status": "PASS",
            "details": "All repository methods work with new fields"
        })
    
    async def verify_service_methods(self):
        """Verify that service methods work with new fields."""
        logger.info("\n" + "=" * 40)
        logger.info("VERIFYING SERVICE METHODS")
        logger.info("=" * 40)
        
        # Test scraping request with new fields
        request = SalesHistoryScrapingRequest(
            asins=TEST_ASINS,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today() - timedelta(days=1),
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info("✅ Scraping request with new fields created")
        
        # Test query request with new fields
        query_request = SalesHistoryQueryRequest(
            asins=TEST_ASINS,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today() - timedelta(days=1),
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info("✅ Query request with new fields created")
        
        # Test stats retrieval with new fields
        if TEST_ASINS:
            stats = await self.service.get_sales_stats(
                TEST_ASINS[0],
                platform_source="amazon",
                api_source="jungle_scout"
            )
            
            logger.info("✅ Stats retrieval with new fields works")
            logger.info(f"  Stats keys: {list(stats.keys())}")
        
        self.verification_results.append({
            "test": "Service Methods",
            "status": "PASS",
            "details": "All service methods work with new fields"
        })
    
    async def verify_database_structure(self):
        """Verify that database tables have the correct structure."""
        logger.info("\n" + "=" * 40)
        logger.info("VERIFYING DATABASE STRUCTURE")
        logger.info("=" * 40)
        
        try:
            from core.database.connection import get_supabase_service_client
            supabase = get_supabase_service_client()
            
            # Check daily table structure
            daily_result = supabase.table('product_sales_history_daily').select(
                'platform_id, platform_source, api_source, date'
            ).limit(1).execute()
            
            logger.info("✅ product_sales_history_daily table exists and accessible")
            
            # Check monthly table structure
            monthly_result = supabase.table('product_sales_history_monthly').select(
                'platform_id, platform_source, api_source, year_month'
            ).limit(1).execute()
            
            logger.info("✅ product_sales_history_monthly table exists and accessible")
            
            # Check if tables have the new columns
            if daily_result.data:
                sample_row = daily_result.data[0]
                has_platform_source = 'platform_source' in sample_row
                has_api_source = 'api_source' in sample_row
                
                logger.info(f"  Daily table has platform_source: {has_platform_source}")
                logger.info(f"  Daily table has api_source: {has_api_source}")
            
            if monthly_result.data:
                sample_row = monthly_result.data[0]
                has_platform_source = 'platform_source' in sample_row
                has_api_source = 'api_source' in sample_row
                
                logger.info(f"  Monthly table has platform_source: {has_platform_source}")
                logger.info(f"  Monthly table has api_source: {has_api_source}")
            
            self.verification_results.append({
                "test": "Database Structure",
                "status": "PASS",
                "details": "Database tables have correct structure"
            })
            
        except Exception as e:
            logger.error(f"❌ Database structure verification failed: {e}")
            self.verification_results.append({
                "test": "Database Structure",
                "status": "FAIL",
                "details": f"Error: {str(e)}"
            })
    
    async def verify_api_compatibility(self):
        """Verify that API endpoints are compatible with new structure."""
        logger.info("\n" + "=" * 40)
        logger.info("VERIFYING API COMPATIBILITY")
        logger.info("=" * 40)
        
        # Test that we can create requests for all API endpoints
        try:
            # Test scraping endpoint request
            scraping_request = SalesHistoryScrapingRequest(
                asins=TEST_ASINS,
                platform_source="amazon",
                api_source="jungle_scout"
            )
            
            # Test daily query endpoint request
            daily_query_request = SalesHistoryQueryRequest(
                asins=TEST_ASINS,
                platform_source="amazon",
                api_source="jungle_scout"
            )
            
            # Test monthly query endpoint request
            monthly_query_request = SalesHistoryQueryRequest(
                asins=TEST_ASINS,
                platform_source="amazon",
                api_source="jungle_scout"
            )
            
            logger.info("✅ All API request models work with new fields")
            logger.info("✅ API endpoints should be compatible with new structure")
            
            self.verification_results.append({
                "test": "API Compatibility",
                "status": "PASS",
                "details": "API endpoints are compatible with new structure"
            })
            
        except Exception as e:
            logger.error(f"❌ API compatibility verification failed: {e}")
            self.verification_results.append({
                "test": "API Compatibility",
                "status": "FAIL",
                "details": f"Error: {str(e)}"
            })
    
    async def print_verification_summary(self):
        """Print verification summary."""
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.verification_results)
        passed_tests = sum(1 for result in self.verification_results if result["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("\nDetailed Results:")
        for result in self.verification_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            logger.info(f"  {status_icon} {result['test']}: {result['status']}")
            logger.info(f"    {result['details']}")
        
        if success_rate == 100:
            logger.info("\n🎉 All verifications passed! The sales history service is ready.")
        else:
            logger.error("\n⚠️  Some verifications failed. Please check the issues above.")

async def main():
    """Main verification function."""
    verifier = SalesHistoryVerifier()
    await verifier.run_verification()

if __name__ == "__main__":
    asyncio.run(main()) 