#!/usr/bin/env python3
"""
Clear Sales History Test Data

This script removes test data from the sales history tables.
Use this after running tests to clean up the database.

Usage:
    python clear_test_data.py [--asins ASIN1,ASIN2,ASIN3] [--all] [--dry-run]

Options:
    --asins: Comma-separated list of ASINs to clear (default: test ASINs)
    --all: Clear all sales history data (use with caution!)
    --dry-run: Show what would be deleted without actually deleting
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import List

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sales_history.repositories.sales_history_repository import SalesHistoryRepository
from sales_history.repositories.sales_history_monthly_repository import SalesHistoryMonthlyRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default test ASINs (same as in test file)
DEFAULT_TEST_ASINS = [
    "B08N5WRWNW",
    "B07ZPKBL9V", 
    "B08SJ3Z8XD",
    "INVALID_ASIN"
]

class SalesHistoryDataCleaner:
    """Cleaner for sales history test data."""
    
    def __init__(self):
        """Initialize the cleaner."""
        self.daily_repo = SalesHistoryRepository()
        self.monthly_repo = SalesHistoryMonthlyRepository()
        self.deletion_summary = {
            "daily_records_deleted": 0,
            "monthly_records_deleted": 0,
            "asins_processed": 0,
            "errors": []
        }
    
    async def clear_test_data(self, asins: List[str], dry_run: bool = False):
        """Clear test data for specified ASINs."""
        logger.info("=" * 60)
        logger.info("SALES HISTORY TEST DATA CLEANUP")
        logger.info("=" * 60)
        
        if dry_run:
            logger.info("DRY RUN MODE - No data will be deleted")
        
        logger.info(f"Processing {len(asins)} ASINs: {asins}")
        
        for asin in asins:
            try:
                await self.clear_asin_data(asin, dry_run)
                self.deletion_summary["asins_processed"] += 1
            except Exception as e:
                error_msg = f"Error clearing data for ASIN {asin}: {e}"
                logger.error(error_msg)
                self.deletion_summary["errors"].append(error_msg)
        
        await self.print_cleanup_summary()
    
    async def clear_asin_data(self, asin: str, dry_run: bool = False):
        """Clear data for a specific ASIN."""
        logger.info(f"\nProcessing ASIN: {asin}")
        
        # Clear daily data
        daily_deleted = await self.daily_repo.delete_sales_data(
            asin, 
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        if dry_run:
            logger.info(f"  Would delete {daily_deleted} daily records")
        else:
            logger.info(f"  Deleted {daily_deleted} daily records")
            self.deletion_summary["daily_records_deleted"] += daily_deleted
        
        # Clear monthly data
        monthly_deleted = await self.monthly_repo.delete_monthly_data(
            asin,
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        if dry_run:
            logger.info(f"  Would delete {monthly_deleted} monthly records")
        else:
            logger.info(f"  Deleted {monthly_deleted} monthly records")
            self.deletion_summary["monthly_records_deleted"] += monthly_deleted
    
    async def clear_all_data(self, dry_run: bool = False):
        """Clear all sales history data (use with caution!)."""
        logger.info("=" * 60)
        logger.info("CLEARING ALL SALES HISTORY DATA")
        logger.info("=" * 60)
        
        if dry_run:
            logger.info("DRY RUN MODE - No data will be deleted")
        else:
            logger.warning("WARNING: This will delete ALL sales history data!")
        
        try:
            # Get all ASINs from daily table
            from core.database.connection import get_supabase_service_client
            supabase = get_supabase_service_client()
            
            result = supabase.table('product_sales_history_daily').select(
                'platform_id'
            ).execute()
            
            if result.data:
                all_asins = list(set(row['platform_id'] for row in result.data))
                logger.info(f"Found {len(all_asins)} unique ASINs with data")
                
                for asin in all_asins:
                    await self.clear_asin_data(asin, dry_run)
                    self.deletion_summary["asins_processed"] += 1
            else:
                logger.info("No data found to clear")
                
        except Exception as e:
            error_msg = f"Error clearing all data: {e}"
            logger.error(error_msg)
            self.deletion_summary["errors"].append(error_msg)
        
        await self.print_cleanup_summary()
    
    async def show_data_summary(self):
        """Show summary of current data in the database."""
        logger.info("=" * 60)
        logger.info("SALES HISTORY DATA SUMMARY")
        logger.info("=" * 60)
        
        try:
            from core.database.connection import get_supabase_service_client
            supabase = get_supabase_service_client()
            
            # Get daily data summary
            daily_result = supabase.table('product_sales_history_daily').select(
                'platform_id, platform_source, api_source, date'
            ).execute()
            
            if daily_result.data:
                daily_summary = {}
                for row in daily_result.data:
                    asin = row['platform_id']
                    if asin not in daily_summary:
                        daily_summary[asin] = {
                            'platform_source': row['platform_source'],
                            'api_source': row['api_source'],
                            'dates': []
                        }
                    daily_summary[asin]['dates'].append(row['date'])
                
                logger.info(f"Daily Data Summary:")
                logger.info(f"  Total ASINs: {len(daily_summary)}")
                logger.info(f"  Total Records: {len(daily_result.data)}")
                
                for asin, data in daily_summary.items():
                    min_date = min(data['dates'])
                    max_date = max(data['dates'])
                    record_count = len(data['dates'])
                    logger.info(f"  {asin}: {record_count} records ({min_date} to {max_date}) - {data['platform_source']}/{data['api_source']}")
            else:
                logger.info("No daily data found")
            
            # Get monthly data summary
            monthly_result = supabase.table('product_sales_history_monthly').select(
                'platform_id, platform_source, api_source, year_month'
            ).execute()
            
            if monthly_result.data:
                monthly_summary = {}
                for row in monthly_result.data:
                    asin = row['platform_id']
                    if asin not in monthly_summary:
                        monthly_summary[asin] = {
                            'platform_source': row['platform_source'],
                            'api_source': row['api_source'],
                            'months': []
                        }
                    monthly_summary[asin]['months'].append(row['year_month'])
                
                logger.info(f"\nMonthly Data Summary:")
                logger.info(f"  Total ASINs: {len(monthly_summary)}")
                logger.info(f"  Total Records: {len(monthly_result.data)}")
                
                for asin, data in monthly_summary.items():
                    min_month = min(data['months'])
                    max_month = max(data['months'])
                    month_count = len(data['months'])
                    logger.info(f"  {asin}: {month_count} months ({min_month} to {max_month}) - {data['platform_source']}/{data['api_source']}")
            else:
                logger.info("No monthly data found")
                
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
    
    async def print_cleanup_summary(self):
        """Print summary of cleanup operations."""
        logger.info("\n" + "=" * 60)
        logger.info("CLEANUP SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"ASINs Processed: {self.deletion_summary['asins_processed']}")
        logger.info(f"Daily Records Deleted: {self.deletion_summary['daily_records_deleted']}")
        logger.info(f"Monthly Records Deleted: {self.deletion_summary['monthly_records_deleted']}")
        logger.info(f"Total Records Deleted: {self.deletion_summary['daily_records_deleted'] + self.deletion_summary['monthly_records_deleted']}")
        
        if self.deletion_summary['errors']:
            logger.error("Errors encountered:")
            for error in self.deletion_summary['errors']:
                logger.error(f"  - {error}")

async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Clear sales history test data")
    parser.add_argument("--asins", help="Comma-separated list of ASINs to clear")
    parser.add_argument("--all", action="store_true", help="Clear all sales history data")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    parser.add_argument("--summary", action="store_true", help="Show current data summary")
    
    args = parser.parse_args()
    
    cleaner = SalesHistoryDataCleaner()
    
    if args.summary:
        await cleaner.show_data_summary()
    elif args.all:
        await cleaner.clear_all_data(dry_run=args.dry_run)
    else:
        # Use provided ASINs or default test ASINs
        if args.asins:
            asins = [asin.strip() for asin in args.asins.split(",")]
        else:
            asins = DEFAULT_TEST_ASINS
        
        await cleaner.clear_test_data(asins, dry_run=args.dry_run)

if __name__ == "__main__":
    asyncio.run(main()) 