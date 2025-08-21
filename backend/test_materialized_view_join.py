#!/usr/bin/env python3
"""
Script to manually test the materialized view JOIN conditions for a specific ASIN.
"""

import logging
from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_materialized_view_join_for_asin(asin: str):
    """Test the materialized view JOIN conditions for a specific ASIN."""
    client = get_supabase_client()
    
    logger.info(f"🔍 Testing materialized view JOIN conditions for {asin}")
    logger.info("=" * 60)
    
    # Step 1: Get categories with stage = 'final' and name != 'OUT_OF_SCOPE'
    logger.info("Step 1: Getting final categories...")
    categories = client.table('review_analysis_aspect_categories').select(
        'category_pk,name,stage'
    ).eq('stage', 'final').neq('name', 'OUT_OF_SCOPE').execute()
    
    category_pks = [cat['category_pk'] for cat in categories.data]
    logger.info(f"Found {len(category_pks)} final categories")
    
    # Step 2: Get aspects for this ASIN that belong to final categories
    logger.info("Step 2: Getting aspects for final categories...")
    aspects = client.table('review_analysis_aspects').select(
        'aspect_pk,category_pk,product_id'
    ).eq('product_id', asin).in_('category_pk', category_pks).execute()
    
    aspect_pks = [aspect['aspect_pk'] for aspect in aspects.data]
    logger.info(f"Found {len(aspect_pks)} aspects for {asin}")
    
    if not aspect_pks:
        logger.error(f"No aspects found for {asin}")
        return
    
    # Step 3: Get occurrences for these aspects
    logger.info("Step 3: Getting aspect occurrences...")
    occurrences = client.table('review_analysis_aspect_occurrences').select(
        'aspect_pk,review_id,sentiment'
    ).in_('aspect_pk', aspect_pks).execute()
    
    logger.info(f"Found {len(occurrences.data)} occurrences")
    
    if not occurrences.data:
        logger.error(f"No occurrences found for {asin}")
        return
    
    # Step 4: Get unique review_ids from occurrences
    occurrence_review_ids = list(set([occ['review_id'] for occ in occurrences.data]))
    logger.info(f"Unique review_ids in occurrences: {occurrence_review_ids[:10]}")
    
    # Step 5: Check if these review_ids exist in product_reviews with non-null review_text
    logger.info("Step 5: Checking product_reviews...")
    reviews = client.table('product_reviews').select(
        'review_id,review_text'
    ).eq('product_id', asin).in_('review_id', occurrence_review_ids[:10]).execute()
    
    logger.info(f"Found {len(reviews.data)} matching reviews in product_reviews")
    
    # Step 6: Check if ASIN exists in product_wide_table
    logger.info("Step 6: Checking product_wide_table...")
    product_wide = client.table('product_wide_table').select(
        'platform_id'
    ).eq('platform_id', asin).execute()
    
    logger.info(f"Found {len(product_wide.data)} records in product_wide_table")
    
    # Step 7: Manual JOIN test
    logger.info("Step 7: Manual JOIN test...")
    
    # Get a sample occurrence
    sample_occurrence = occurrences.data[0]
    sample_aspect_pk = sample_occurrence['aspect_pk']
    sample_review_id = sample_occurrence['review_id']
    
    logger.info(f"Sample occurrence: aspect_pk={sample_aspect_pk}, review_id={sample_review_id}")
    
    # Check if this specific occurrence can be joined
    aspect = client.table('review_analysis_aspects').select(
        'aspect_pk,category_pk,product_id'
    ).eq('aspect_pk', sample_aspect_pk).execute()
    
    if aspect.data:
        aspect_data = aspect.data[0]
        category_pk = aspect_data['category_pk']
        product_id = aspect_data['product_id']
        
        logger.info(f"Aspect data: category_pk={category_pk}, product_id={product_id}")
        
        # Check category
        category = client.table('review_analysis_aspect_categories').select(
            'category_pk,name,stage'
        ).eq('category_pk', category_pk).execute()
        
        if category.data:
            category_data = category.data[0]
            logger.info(f"Category data: name={category_data['name']}, stage={category_data['stage']}")
        
        # Check review
        review = client.table('product_reviews').select(
            'review_id,review_text'
        ).eq('product_id', product_id).eq('review_id', sample_review_id).execute()
        
        if review.data:
            review_data = review.data[0]
            logger.info(f"Review data: review_id={review_data['review_id']}, text_length={len(review_data.get('review_text', ''))}")
        else:
            logger.error(f"❌ Review not found: product_id={product_id}, review_id={sample_review_id}")
        
        # Check product_wide_table
        product_wide = client.table('product_wide_table').select(
            'platform_id'
        ).eq('platform_id', product_id).execute()
        
        if product_wide.data:
            logger.info(f"✅ Product found in product_wide_table: {product_wide.data[0]['platform_id']}")
        else:
            logger.error(f"❌ Product not found in product_wide_table: {product_id}")
    
    logger.info("=" * 60)
    logger.info("Manual JOIN test completed")

def main():
    """Main function."""
    # Test with one of the missing ASINs
    test_asins = ['B085D8M2MR', 'B0BVKZLT3B', 'B0BVKYKKRK', 'B0BSHKS26L']
    
    for asin in test_asins:
        test_materialized_view_join_for_asin(asin)
        print("\n")

if __name__ == "__main__":
    main() 