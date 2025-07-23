#!/usr/bin/env python3
"""
Scrape Sales History for Project (Batch Processing)

This script scrapes sales history for all ASINs in a specific project over the past year,
processing them in batches to handle the 50 ASIN limit and date constraints.

Usage:
    python3 scrape_project_sales_history_batch.py <project_id>

Example:
    python3 scrape_project_sales_history_batch.py d2c02b80-4c82-44cc-8093-56708a7883f7
"""

import sys
import asyncio
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.database.connection import get_supabase_service_client
from sales_history.services.sales_history_service import SalesHistoryService
from sales_history.models import SalesHistoryScrapingRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BATCH_SIZE = 50  # Maximum ASINs per batch
MAX_DAYS_BACK = 365  # Maximum days to look back

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

async def scrape_batch(
    service: SalesHistoryService,
    asins: List[str],
    start_date: date,
    end_date: date,
    batch_num: int,
    total_batches: int
) -> Dict[str, Any]:
    """Scrape a batch of ASINs."""
    
    logger.info(f"Processing batch {batch_num}/{total_batches} with {len(asins)} ASINs")
    logger.info(f"ASINs: {asins[:3]}{'...' if len(asins) > 3 else ''}")
    
    try:
        # Create scraping request for this batch
        request = SalesHistoryScrapingRequest(
            asins=asins,
            start_date=start_date,
            end_date=end_date,
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        # Execute scraping
        response = await service.scrape_sales_history(request)
        
        return {
            'batch_num': batch_num,
            'asins': asins,
            'success': response.success,
            'message': response.message,
            'scraping_summary': response.scraping_summary,
            'results': response.data  # This is Dict[str, List[SalesHistoryDataPoint]]
        }
        
    except Exception as e:
        logger.error(f"Error processing batch {batch_num}: {e}")
        return {
            'batch_num': batch_num,
            'asins': asins,
            'success': False,
            'message': str(e),
            'scraping_summary': None,
            'results': {}
        }

async def scrape_project_sales_history(project_id: str):
    """Scrape sales history for all ASINs in a project over the past year."""
    
    logger.info("=" * 80)
    logger.info(f"SCRAPING SALES HISTORY FOR PROJECT: {project_id}")
    logger.info("=" * 80)
    
    try:
        # Get project details
        supabase = get_supabase_service_client()
        project_result = supabase.table('projects').select(
            'project_name, selected_product_asins'
        ).eq('id', project_id).execute()
        
        if not project_result.data:
            logger.error(f"Project {project_id} not found")
            return
        
        project = project_result.data[0]
        project_name = project.get('project_name', 'Unnamed Project')
        all_asins = project.get('selected_product_asins', [])
        
        logger.info(f"Project Name: {project_name}")
        logger.info(f"Total ASINs: {len(all_asins)}")
        logger.info(f"Sample ASINs: {all_asins[:5]}{'...' if len(all_asins) > 5 else ''}")
        
        if not all_asins:
            logger.error("No ASINs found in project")
            return
        
        # Calculate date range (respecting the 1-year constraint)
        end_date = date.today() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=MAX_DAYS_BACK)  # One year ago
        
        # Adjust start_date to respect the model validation (cannot be earlier than 1 year ago)
        today = date.today()
        min_allowed_date = today.replace(year=today.year - 1)
        if start_date < min_allowed_date:
            start_date = min_allowed_date
            logger.warning(f"Adjusted start_date to {start_date} due to model constraints")
        
        logger.info(f"Date Range: {start_date} to {end_date}")
        logger.info(f"Total Days: {(end_date - start_date).days + 1}")
        
        # Split ASINs into batches
        asin_batches = chunk_list(all_asins, BATCH_SIZE)
        total_batches = len(asin_batches)
        
        logger.info(f"Processing {len(all_asins)} ASINs in {total_batches} batches of {BATCH_SIZE}")
        
        # Initialize service
        service = SalesHistoryService()
        
        # Process batches
        batch_results = []
        total_scraped = 0
        total_skipped = 0
        total_failed = 0
        total_invalid = 0
        
        for i, asin_batch in enumerate(asin_batches, 1):
            batch_result = await scrape_batch(
                service, asin_batch, start_date, end_date, i, total_batches
            )
            batch_results.append(batch_result)
            
            # Update totals
            if batch_result['scraping_summary']:
                summary = batch_result['scraping_summary']
                total_scraped += summary.scraped
                total_skipped += summary.skipped
                total_failed += summary.failed
                total_invalid += len(summary.invalid_asins)
            
            # Add a small delay between batches to avoid overwhelming the API
            if i < total_batches:
                await asyncio.sleep(2)
        
        # Log final results
        logger.info("\n" + "=" * 80)
        logger.info("FINAL SCRAPING RESULTS")
        logger.info("=" * 80)
        
        logger.info(f"Total Batches Processed: {total_batches}")
        logger.info(f"Total ASINs Requested: {len(all_asins)}")
        logger.info(f"Successfully Scraped: {total_scraped}")
        logger.info(f"Skipped: {total_skipped}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Invalid ASINs: {total_invalid}")
        
        # Show batch-by-batch results
        logger.info(f"\nBatch-by-Batch Results:")
        for batch_result in batch_results:
            batch_num = batch_result['batch_num']
            success = "✅" if batch_result['success'] else "❌"
            asin_count = len(batch_result['asins'])
            
            if batch_result['scraping_summary']:
                summary = batch_result['scraping_summary']
                logger.info(f"  Batch {batch_num}: {success} {asin_count} ASINs - "
                          f"Scraped: {summary.scraped}, Skipped: {summary.skipped}, "
                          f"Failed: {summary.failed}")
            else:
                logger.info(f"  Batch {batch_num}: {success} {asin_count} ASINs - "
                          f"Error: {batch_result['message']}")
        
        # Show detailed results for successful batches
        logger.info(f"\nDetailed Results:")
        for batch_result in batch_results:
            if not batch_result['success'] or not batch_result['results']:
                continue
                
            batch_num = batch_result['batch_num']
            logger.info(f"\n  Batch {batch_num}:")
            
            # Results is a dictionary of ASIN -> List[SalesHistoryDataPoint]
            results_data = batch_result['results']
            if isinstance(results_data, dict):
                for asin, data_points in results_data.items():
                    if data_points:
                        logger.info(f"    {asin}: ✅ SUCCESS")
                        logger.info(f"      Records: {len(data_points)}")
                        if data_points:
                            first_record = data_points[0]
                            last_record = data_points[-1]
                            logger.info(f"      Date Range: {first_record.sales_date} to {last_record.sales_date}")
                            total_units = sum(record.estimated_units_sold for record in data_points)
                            avg_price = sum(record.last_known_price for record in data_points) / len(data_points)
                            logger.info(f"      Total Units: {total_units}")
                            logger.info(f"      Avg Price: ${avg_price:.2f}")
                    else:
                        logger.info(f"    {asin}: ⚠️  NO DATA")
            else:
                logger.warning(f"    Unexpected results data type: {type(results_data)}")
        
        logger.info("\n" + "=" * 80)
        logger.info("SCRAPING COMPLETED")
        logger.info("=" * 80)
        
        # Return summary
        return {
            'project_name': project_name,
            'total_asins': len(all_asins),
            'total_batches': total_batches,
            'total_scraped': total_scraped,
            'total_skipped': total_skipped,
            'total_failed': total_failed,
            'total_invalid': total_invalid,
            'date_range': {'start_date': start_date, 'end_date': end_date},
            'batch_results': batch_results
        }
        
    except Exception as e:
        logger.error(f"Error scraping project sales history: {e}")
        raise

async def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python3 scrape_project_sales_history_batch.py <project_id>")
        print("Example: python3 scrape_project_sales_history_batch.py d2c02b80-4c82-44cc-8093-56708a7883f7")
        sys.exit(1)
    
    project_id = sys.argv[1]
    result = await scrape_project_sales_history(project_id)
    
    # Print final summary
    if result:
        print(f"\n🎉 Final Summary:")
        print(f"   Project: {result['project_name']}")
        print(f"   Total ASINs: {result['total_asins']}")
        print(f"   Successfully Scraped: {result['total_scraped']}")
        print(f"   Skipped: {result['total_skipped']}")
        print(f"   Failed: {result['total_failed']}")
        print(f"   Date Range: {result['date_range']['start_date']} to {result['date_range']['end_date']}")
    else:
        print("❌ Scraping failed - no results returned")

if __name__ == "__main__":
    asyncio.run(main()) 