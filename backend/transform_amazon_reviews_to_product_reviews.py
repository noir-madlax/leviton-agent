#!/usr/bin/env python3
"""
Script to transform amazon_reviews to product_reviews for specific ASINs.
This will sync the data between the two tables.
"""

import logging
from typing import List, Dict, Any
from core.database.connection import get_supabase_client
from data_transformation.models import TransformationConfig
from data_transformation.services.review_transformation_service import ReviewTransformationService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_asins_in_tables(asins: List[str]) -> Dict[str, Dict[str, int]]:
    """Check ASINs in both amazon_reviews and product_reviews tables."""
    client = get_supabase_client()
    
    # Check amazon_reviews
    amazon_result = client.table('amazon_reviews').select('asin').in_('asin', asins).execute()
    amazon_counts = {}
    for row in amazon_result.data:
        asin = row['asin']
        amazon_counts[asin] = amazon_counts.get(asin, 0) + 1
    
    # Check product_reviews
    product_result = client.table('product_reviews').select('product_id').in_('product_id', asins).execute()
    product_counts = {}
    for row in product_result.data:
        asin = row['product_id']
        product_counts[asin] = product_counts.get(asin, 0) + 1
    
    return {
        'amazon_reviews': amazon_counts,
        'product_reviews': product_counts
    }

async def transform_reviews_for_asins(asins: List[str]) -> Dict[str, Any]:
    """Transform reviews from amazon_reviews to product_reviews for specific ASINs."""
    logger.info(f"🔄 Starting transformation for {len(asins)} ASINs: {asins}")
    
    # Create transformation config
    config = TransformationConfig(
        skip_existing=True,
        validate_calculations=False,
        dry_run=False,
        batch_size=100
    )
    
    # Create service
    service = ReviewTransformationService(config)
    
    # Run transformation
    result = service.transform_batch(limit=None)  # Process all available data
    
    logger.info("=" * 60)
    logger.info("📊 TRANSFORMATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"✅ Success: {result.success}")
    logger.info(f"📝 Processed: {result.processed_count}")
    logger.info(f"⏭️ Skipped: {result.skipped_count}")
    logger.info(f"❌ Errors: {result.error_count}")
    logger.info(f"⏱️ Duration: {result.duration_seconds:.2f} seconds")
    
    if result.summary:
        logger.info("📈 Summary:")
        for key, value in result.summary.items():
            logger.info(f"  {key}: {value}")
    
    return {
        "success": result.success,
        "processed_count": result.processed_count,
        "skipped_count": result.skipped_count,
        "error_count": result.error_count,
        "duration_seconds": result.duration_seconds,
        "summary": result.summary
    }

async def main():
    """Main function to transform reviews."""
    # ASINs that need transformation
    target_asins = [
        'B085D8M2MR',  # Lutron Diva
        'B0BVKYKKRK',  # Leviton D26HD
        'B0BSHKS26L',  # Lutron Caseta Diva
        'B00NG0ELL0',  # Leviton DSL06
        'B01EZV35QU',  # TP Link Switch
        'B0BVKZLT3B'   # Leviton D215S
    ]
    
    logger.info("🎯 Review Transformation for Project ASINs")
    logger.info("=" * 80)
    
    # Step 1: Check current status
    logger.info("📊 Checking current status...")
    status = check_asins_in_tables(target_asins)
    
    for asin in target_asins:
        amazon_count = status['amazon_reviews'].get(asin, 0)
        product_count = status['product_reviews'].get(asin, 0)
        logger.info(f"📦 {asin}:")
        logger.info(f"   amazon_reviews: {amazon_count} reviews")
        logger.info(f"   product_reviews: {product_count} reviews")
        if amazon_count > 0 and product_count == 0:
            logger.info(f"   ⚠️  Needs transformation!")
        elif amazon_count == 0:
            logger.info(f"   ❌ No reviews in amazon_reviews")
        else:
            logger.info(f"   ✅ Already synchronized")
        logger.info("")
    
    # Step 2: Run transformation
    logger.info("🔄 Running transformation...")
    result = await transform_reviews_for_asins(target_asins)
    
    # Step 3: Check final status
    logger.info("📊 Checking final status...")
    final_status = check_asins_in_tables(target_asins)
    
    logger.info("=" * 80)
    logger.info("📋 FINAL STATUS")
    logger.info("=" * 80)
    
    for asin in target_asins:
        amazon_count = final_status['amazon_reviews'].get(asin, 0)
        product_count = final_status['product_reviews'].get(asin, 0)
        logger.info(f"📦 {asin}:")
        logger.info(f"   amazon_reviews: {amazon_count} reviews")
        logger.info(f"   product_reviews: {product_count} reviews")
        if product_count > 0:
            logger.info(f"   ✅ Now in product_reviews!")
        else:
            logger.info(f"   ❌ Still missing from product_reviews")
        logger.info("")
    
    logger.info("=" * 80)
    logger.info(f"🎉 Transformation completed!")
    logger.info(f"   Processed: {result['processed_count']} reviews")
    logger.info(f"   Skipped: {result['skipped_count']} reviews")
    logger.info(f"   Errors: {result['error_count']} reviews")
    logger.info("=" * 80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 