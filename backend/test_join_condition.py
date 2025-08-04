#!/usr/bin/env python3
"""
Test script to understand why the JOIN condition in the materialized view is failing.
"""

import logging
from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_join_condition(asin: str):
    """Test the JOIN condition manually to understand the issue."""
    client = get_supabase_client()
    
    logger.info(f"🔍 Testing JOIN condition for {asin}")
    logger.info("=" * 60)
    
    # Step 1: Get a sample occurrence
    logger.info("1. Getting a sample occurrence...")
    
    # Get aspects for this ASIN
    aspects_result = client.table('review_analysis_aspects').select('aspect_pk').eq('product_id', asin).limit(5).execute()
    if not aspects_result.data:
        logger.error(f"No aspects found for {asin}")
        return
    
    aspect_pks = [r['aspect_pk'] for r in aspects_result.data]
    
    # Get occurrences for these aspects
    occurrences_result = client.table('review_analysis_aspect_occurrences').select(
        'aspect_pk,review_id,sentiment'
    ).in_('aspect_pk', aspect_pks).limit(5).execute()
    
    if not occurrences_result.data:
        logger.error(f"No occurrences found for {asin}")
        return
    
    sample_occurrence = occurrences_result.data[0]
    logger.info(f"Sample occurrence: {sample_occurrence}")
    
    # Step 2: Test the JOIN condition manually
    logger.info("\n2. Testing JOIN condition manually...")
    
    review_id = sample_occurrence['review_id']
    aspect_pk = sample_occurrence['aspect_pk']
    
    logger.info(f"Testing JOIN with review_id = '{review_id}' (type: {type(review_id)})")
    
    # Test 1: Check if review_id exists in product_reviews as string
    pr_string_result = client.table('product_reviews').select('review_id,review_text').eq('review_id', str(review_id)).eq('product_id', asin).execute()
    logger.info(f"product_reviews with review_id = '{review_id}' (string): {len(pr_string_result.data)}")
    
    # Test 2: Check if review_id exists in product_reviews as integer
    try:
        review_id_int = int(review_id)
        pr_int_result = client.table('product_reviews').select('review_id,review_text').eq('review_id', review_id_int).eq('product_id', asin).execute()
        logger.info(f"product_reviews with review_id = {review_id_int} (integer): {len(pr_int_result.data)}")
    except (ValueError, TypeError):
        logger.info(f"Could not convert '{review_id}' to integer")
    
    # Test 3: Check what the actual review_id types are in product_reviews
    logger.info("\n3. Checking review_id types in product_reviews...")
    pr_sample_result = client.table('product_reviews').select('review_id').eq('product_id', asin).limit(5).execute()
    if pr_sample_result.data:
        logger.info("Sample review_ids from product_reviews:")
        for i, record in enumerate(pr_sample_result.data):
            review_id_val = record['review_id']
            logger.info(f"  {i+1}. value: {review_id_val}, type: {type(review_id_val)}")
    
    # Test 4: Check what the actual review_id types are in occurrences
    logger.info("\n4. Checking review_id types in occurrences...")
    logger.info("Sample review_ids from occurrences:")
    for i, record in enumerate(occurrences_result.data[:5]):
        review_id_val = record['review_id']
        logger.info(f"  {i+1}. value: {review_id_val}, type: {type(review_id_val)}")
    
    # Step 5: Test a manual JOIN query
    logger.info("\n5. Testing manual JOIN query...")
    
    # Try to replicate the materialized view JOIN manually
    try:
        # This should match the materialized view logic
        manual_query = f"""
        SELECT 
            rao.review_id as occurrence_review_id,
            pr.review_id as product_review_id,
            rao.review_id::text as occurrence_review_id_text,
            pr.review_id::text as product_review_id_text
        FROM review_analysis_aspect_occurrences rao
        JOIN review_analysis_aspects raa ON rao.aspect_pk = raa.aspect_pk
        JOIN product_reviews pr ON rao.review_id::text = pr.review_id::text AND raa.product_id = pr.product_id
        WHERE raa.product_id = '{asin}'
        LIMIT 5
        """
        
        # Since we can't run raw SQL easily, let's test the logic step by step
        logger.info("Testing JOIN logic step by step...")
        
        # Get the aspect_pk for our sample occurrence
        aspect_result = client.table('review_analysis_aspects').select('aspect_pk,product_id').eq('aspect_pk', aspect_pk).execute()
        if aspect_result.data:
            aspect_data = aspect_result.data[0]
            logger.info(f"Aspect data: {aspect_data}")
            
            # Check if the JOIN condition would work
            review_id_text = str(review_id)
            product_id = aspect_data['product_id']
            
            # Test the exact JOIN condition
            join_test = client.table('product_reviews').select('review_id').eq('review_id', review_id_text).eq('product_id', product_id).execute()
            logger.info(f"JOIN test result: {len(join_test.data)} matches")
            
            if join_test.data:
                logger.info(f"✅ JOIN condition works for review_id = '{review_id_text}'")
            else:
                logger.warning(f"❌ JOIN condition fails for review_id = '{review_id_text}'")
                
    except Exception as e:
        logger.error(f"Error testing manual JOIN: {e}")

if __name__ == "__main__":
    test_join_condition('B0BVKZLT3B') 