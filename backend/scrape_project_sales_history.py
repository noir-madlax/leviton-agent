#!/usr/bin/env python3
"""
Scrape Sales History for Project

This script scrapes sales history for all ASINs in a specific project over the past year.

Usage:
    python3 scrape_project_sales_history.py <project_id>

Example:
    python3 scrape_project_sales_history.py d2c02b80-4c82-44cc-8093-56708a7883f7
"""

import sys
import asyncio
import logging
from datetime import date, timedelta
from pathlib import Path

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
        asins = project.get('selected_product_asins', [])
        
        logger.info(f"Project Name: {project_name}")
        logger.info(f"Total ASINs: {len(asins)}")
        logger.info(f"ASINs: {asins[:5]}{'...' if len(asins) > 5 else ''}")
        
        if not asins:
            logger.error("No ASINs found in project")
            return
        
        # Calculate date range (past year)
        end_date = date.today() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=365)  # One year ago
        
        logger.info(f"Date Range: {start_date} to {end_date}")
        logger.info(f"Total Days: {(end_date - start_date).days + 1}")
        
        # Initialize service
        service = SalesHistoryService()
        
        # Create scraping request
        request = SalesHistoryScrapingRequest(
            asins=asins,
            start_date=start_date,
            end_date=end_date,
            platform_source="amazon",
            api_source="jungle_scout"
        )
        
        logger.info("Starting sales history scraping...")
        logger.info(f"Request: {request.model_dump()}")
        
        # Execute scraping
        response = await service.scrape_sales_history(request)
        
        # Log results
        logger.info("\n" + "=" * 80)
        logger.info("SCRAPING RESULTS")
        logger.info("=" * 80)
        
        logger.info(f"Success: {response.success}")
        logger.info(f"Message: {response.message}")
        
        if response.scraping_summary:
            summary = response.scraping_summary
            logger.info(f"\nScraping Summary:")
            logger.info(f"  Total Requested: {summary.total_requested}")
            logger.info(f"  Successfully Scraped: {summary.scraped}")
            logger.info(f"  Skipped: {summary.skipped}")
            logger.info(f"  Failed: {summary.failed}")
            logger.info(f"  Invalid ASINs: {len(summary.invalid_asins)}")
            logger.info(f"  Scraping Errors: {len(summary.scraping_errors)}")
            
            if summary.invalid_asins:
                logger.warning(f"  Invalid ASINs: {summary.invalid_asins}")
            
            if summary.scraping_errors:
                logger.error("  Scraping Errors:")
                for asin, error in summary.scraping_errors.items():
                    logger.error(f"    {asin}: {error}")
        
        # Show detailed results for each ASIN
        if response.results:
            logger.info(f"\nDetailed Results:")
            for asin, result in response.results.items():
                status = "✅ SUCCESS" if result.success else "❌ FAILED"
                if result.skipped:
                    status = "⏭️  SKIPPED"
                
                logger.info(f"  {asin}: {status}")
                if result.success and result.data:
                    logger.info(f"    Records: {len(result.data)}")
                    if result.data:
                        first_record = result.data[0]
                        last_record = result.data[-1]
                        logger.info(f"    Date Range: {first_record.sales_date} to {last_record.sales_date}")
                        total_units = sum(record.estimated_units_sold for record in result.data)
                        avg_price = sum(record.last_known_price for record in result.data) / len(result.data)
                        logger.info(f"    Total Units: {total_units}")
                        logger.info(f"    Avg Price: ${avg_price:.2f}")
                elif result.error_message:
                    logger.error(f"    Error: {result.error_message}")
                elif result.skip_reason:
                    logger.warning(f"    Skipped: {result.skip_reason}")
        
        logger.info("\n" + "=" * 80)
        logger.info("SCRAPING COMPLETED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error scraping project sales history: {e}")
        raise

async def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python3 scrape_project_sales_history.py <project_id>")
        print("Example: python3 scrape_project_sales_history.py d2c02b80-4c82-44cc-8093-56708a7883f7")
        sys.exit(1)
    
    project_id = sys.argv[1]
    await scrape_project_sales_history(project_id)

if __name__ == "__main__":
    asyncio.run(main()) 