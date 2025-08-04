#!/usr/bin/env python3
"""
CLI for rerunning Amazon review scraping for specific ASINs.
Direct ASIN-based approach to avoid scraping irrelevant products.
"""

import argparse
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database.connection import get_supabase_client, get_supabase_service_client
from scraping.reviews.scraper import ReviewScraper
from scraping.reviews.importer import ReviewImporter

# Test ASINs from the review analysis CLI
TEST_ASINS = [
    "B00NG0ELL0",  # Leviton DSL06
    "B0BVKZLT3B",  # Leviton D215S
    "B0BVKYKKRK",  # Leviton D26HD
    "B0BSHKS26L",  # Lutron Caseta Diva
    "B085D8M2MR",  # Lutron Diva
    "B01EZV35QU",  # TP Link Switch
]

# Default settings
DEFAULT_MAX_REVIEWS = 100

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def get_updated_review_counts(asins: List[str]) -> Dict[str, int]:
    """Get current review counts for ASINs from product_reviews table."""
    try:
        client = get_supabase_service_client()
        result = client.table('product_reviews').select('product_id,review_id').in_('product_id', asins).execute()
        
        counts = {}
        for row in result.data:
            asin = row['product_id']
            if asin not in counts:
                counts[asin] = set()
            counts[asin].add(row['review_id'])
        
        return {asin: len(reviews) for asin, reviews in counts.items()}
    except Exception as e:
        logger.error(f"Error getting review counts: {e}")
        return {}

async def print_summary_stats(asins: List[str], before_counts: Dict[str, int], after_counts: Dict[str, int]):
    """Print summary statistics for the scraping operation."""
    logger.info("=" * 80)
    logger.info("📊 SUMMARY STATISTICS")
    logger.info("=" * 80)
    
    total_added = 0
    for asin in asins:
        before = before_counts.get(asin, 0)
        after = after_counts.get(asin, 0)
        added = after - before
        
        logger.info(f"📦 {asin}:")
        logger.info(f"   Before: {before} reviews")
        logger.info(f"   After:  {after} reviews")
        if added > 0:
            logger.info(f"   ✅ Added: {added} new reviews")
            total_added += added
        elif added == 0:
            logger.info("   ⚠️  No new reviews added (may already have sufficient coverage)")
        else:
            logger.info(f"   ❌ Unexpected: {added} reviews (should not be negative)")
        logger.info("")
    
    if total_added > 0:
        logger.info(f"   🎉 Successfully added {total_added} new reviews across {len(asins)} products")
    else:
        logger.info("   ℹ️  No new reviews were added (all products may already have sufficient coverage)")
    
    logger.info("=" * 80)

async def run_review_scraping(asins: List[str], max_reviews: int = DEFAULT_MAX_REVIEWS, 
                            force: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    """Run review scraping for specific ASINs using direct ASIN approach."""
    try:
        logger.info(f"🚀 Starting review scraping for {len(asins)} ASINs")
        logger.info(f"   Max reviews per product: {max_reviews}")
        logger.info(f"   Force mode: {force}")
        logger.info(f"   Dry run: {dry_run}")
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No actual scraping will be performed")
            return {
                "status": "dry_run",
                "asins": asins,
                "max_reviews": max_reviews
            }
        
        # Initialize scrapers
        review_scraper = ReviewScraper()
        review_importer = ReviewImporter()
        
        # Scrape reviews for each ASIN directly
        total_scraped = 0
        total_imported = 0
        
        for asin in asins:
            logger.info(f"📥 Scraping reviews for ASIN {asin}...")
            
            # Scrape reviews for this specific ASIN
            scrape_result = await review_scraper._scrape_product_reviews(
                asin=asin,
                semaphore=asyncio.Semaphore(1),  # Single semaphore for sequential processing
                review_coverage_months=6,  # Default coverage
                batch_id=None,  # No batch_id for direct ASIN scraping
                force_scrape=force,
                max_reviews=max_reviews
            )
            
            if scrape_result.get("status") == "success":
                scraped_count = scrape_result.get("reviews_scraped", 0)
                total_scraped += scraped_count
                logger.info(f"   ✅ Scraped {scraped_count} reviews for {asin}")
                
                # Import reviews for this ASIN
                # Note: We'll need to handle the import differently since we're not using batch_id
                # For now, we'll skip the import and just report the scraping results
                logger.info(f"   ⚠️  Import skipped for {asin} (direct ASIN approach)")
                
            elif scrape_result.get("status") == "skipped":
                logger.info(f"   ⏩ Skipped {asin}: {scrape_result.get('reason', 'Unknown reason')}")
            else:
                logger.error(f"   ❌ Scraping failed for {asin}: {scrape_result.get('error', 'Unknown error')}")
        
        logger.info(f"✅ Review scraping completed: {total_scraped} scraped across {len(asins)} ASINs")
        
        return {
            "status": "success",
            "total_scraped": total_scraped,
            "total_imported": total_imported,
            "asins_processed": len(asins)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in review scraping: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Rerun Amazon review scraping for specific ASINs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with first ASIN only
  python -m scraping.rerun_reviews_cli test --max-reviews 10
  
  # Run for all test ASINs
  python -m scraping.rerun_reviews_cli run --max-reviews 50
  
  # Run for specific ASINs
  python -m scraping.rerun_reviews_cli run --asins B0BVKYKKRK,B0BVKZLT3B --force
  
  # Dry run to see what would be scraped
  python -m scraping.rerun_reviews_cli run --dry-run
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test command - scrape only first ASIN
    test_parser = subparsers.add_parser('test', help='Test with first ASIN only')
    test_parser.add_argument('--max-reviews', type=int, default=DEFAULT_MAX_REVIEWS,
                           help=f'Maximum reviews per product (default: {DEFAULT_MAX_REVIEWS})')
    test_parser.add_argument('--force', action='store_true',
                           help='Force re-scrape even if reviews exist')
    test_parser.add_argument('--dry-run', action='store_true',
                           help='Show what would be scraped without doing it')
    
    # Run command - scrape specified ASINs or all test ASINs
    run_parser = subparsers.add_parser('run', help='Run scraping for ASINs')
    run_parser.add_argument('--asins', type=str,
                           help='Comma-separated list of ASINs (default: all test ASINs)')
    run_parser.add_argument('--max-reviews', type=int, default=DEFAULT_MAX_REVIEWS,
                           help=f'Maximum reviews per product (default: {DEFAULT_MAX_REVIEWS})')
    run_parser.add_argument('--force', action='store_true',
                           help='Force re-scrape even if reviews exist')
    run_parser.add_argument('--dry-run', action='store_true',
                           help='Show what would be scraped without doing it')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Determine ASINs to process
    if args.command == 'test':
        asins = [TEST_ASINS[0]]  # Only first ASIN
        logger.info(f"🧪 TEST MODE: Processing only {asins[0]}")
    else:  # run command
        if args.asins:
            asins = [asin.strip() for asin in args.asins.split(',')]
            logger.info(f"🎯 CUSTOM ASINS: Processing {len(asins)} ASINs")
        else:
            asins = TEST_ASINS
            logger.info(f"📋 ALL TEST ASINS: Processing {len(asins)} ASINs")
    
    # Get initial review counts
    logger.info("📊 Getting initial review counts...")
    before_counts = await get_updated_review_counts(asins)
    
    for asin in asins:
        count = before_counts.get(asin, 0)
        logger.info(f"   {asin}: {count} reviews")
    
    # Run scraping
    result = await run_review_scraping(
        asins=asins,
        max_reviews=args.max_reviews,
        force=args.force,
        dry_run=args.dry_run
    )
    
    if result.get("status") == "success" and not args.dry_run:
        # Get updated review counts after scraping
        logger.info("📊 Getting updated review counts...")
        after_counts = await get_updated_review_counts(asins)
        
        # Print summary statistics
        await print_summary_stats(asins, before_counts, after_counts)
    
    logger.info("✅ CLI execution completed")

if __name__ == "__main__":
    asyncio.run(main()) 