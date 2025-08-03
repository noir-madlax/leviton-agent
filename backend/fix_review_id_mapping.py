#!/usr/bin/env python3
"""
Script to fix review_id mapping between review_analysis_aspect_occurrences and product_reviews.
This addresses the issue where aspect occurrences have review_ids that don't match the product_reviews table.
"""

import logging
from typing import List, Dict, Any, Set
from collections import defaultdict

from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_asins_with_mismatched_review_ids() -> List[str]:
    """Get ASINs that have aspects but review_ids don't match between occurrences and product_reviews."""
    client = get_supabase_client()
    
    # Get ASINs with aspects
    aspects_result = client.table('review_analysis_aspects').select('product_id').execute()
    aspect_asins = list(set([r['product_id'] for r in aspects_result.data]))
    
    mismatched_asins = []
    
    for asin in aspect_asins[:10]:  # Check first 10 for efficiency
        logger.info(f"🔍 Checking {asin} for review_id mismatches...")
        
        # Get aspect_pks for this ASIN
        aspects = client.table('review_analysis_aspects').select('aspect_pk').eq('product_id', asin).limit(5).execute()
        aspect_pks = [aspect['aspect_pk'] for aspect in aspects.data]
        
        if not aspect_pks:
            continue
        
        # Get occurrences for these aspects
        occurrences = client.table('review_analysis_aspect_occurrences').select('review_id').in_('aspect_pk', aspect_pks).execute()
        occurrence_review_ids = set([occ['review_id'] for occ in occurrences.data])
        
        # Get product_reviews for this ASIN
        reviews = client.table('product_reviews').select('review_id').eq('product_id', asin).execute()
        product_review_ids = set([str(review['review_id']) for review in reviews.data])
        
        # Check for mismatch
        if occurrence_review_ids and product_review_ids:
            intersection = occurrence_review_ids.intersection(product_review_ids)
            if len(intersection) == 0:
                logger.info(f"  ❌ {asin}: No matching review_ids found")
                logger.info(f"    Occurrence review_ids: {list(occurrence_review_ids)[:5]}")
                logger.info(f"    Product review_ids: {list(product_review_ids)[:5]}")
                mismatched_asins.append(asin)
            else:
                logger.info(f"  ✅ {asin}: {len(intersection)} matching review_ids found")
    
    return mismatched_asins

def create_review_id_mapping(asin: str) -> Dict[str, str]:
    """Create a mapping from occurrence review_ids to product_reviews review_ids."""
    client = get_supabase_client()
    
    # Get all amazon_reviews for this ASIN
    amazon_reviews = client.table('amazon_reviews').select('review_id,review_title,review_text').eq('asin', asin).execute()
    
    # Get all product_reviews for this ASIN
    product_reviews = client.table('product_reviews').select('review_id,review_title,review_text').eq('product_id', asin).execute()
    
    # Create mapping based on review content similarity
    mapping = {}
    
    for amazon_review in amazon_reviews.data:
        amazon_review_id = amazon_review['review_id']
        amazon_title = amazon_review.get('review_title', '')
        amazon_text = amazon_review.get('review_text', '')
        amazon_content = f"{amazon_title} {amazon_text}".strip()
        
        # Find matching product_review based on content
        for product_review in product_reviews.data:
            product_review_id = str(product_review['review_id'])
            product_title = product_review.get('review_title', '')
            product_text = product_review.get('review_text', '')
            product_content = f"{product_title} {product_text}".strip()
            
            # Simple content matching (you could make this more sophisticated)
            if amazon_content == product_content:
                mapping[amazon_review_id] = product_review_id
                break
    
    logger.info(f"Created mapping for {asin}: {len(mapping)} matches out of {len(amazon_reviews.data)} amazon_reviews")
    return mapping

def update_occurrence_review_ids(asin: str, mapping: Dict[str, str]) -> int:
    """Update review_ids in review_analysis_aspect_occurrences for a specific ASIN."""
    client = get_supabase_client()
    
    # Get all aspects for this ASIN
    aspects = client.table('review_analysis_aspects').select('aspect_pk').eq('product_id', asin).execute()
    aspect_pks = [aspect['aspect_pk'] for aspect in aspects.data]
    
    if not aspect_pks:
        return 0
    
    # Get occurrences that need updating
    occurrences = client.table('review_analysis_aspect_occurrences').select('*').in_('aspect_pk', aspect_pks).execute()
    
    updated_count = 0
    
    for occurrence in occurrences.data:
        old_review_id = occurrence['review_id']
        
        # Find the amazon_review_id that corresponds to this occurrence
        # This is tricky because we need to reverse-engineer the mapping
        # For now, let's try to find a pattern or use a different approach
        
        # Let's check if the old_review_id is actually an amazon_review_id
        if old_review_id in mapping:
            new_review_id = mapping[old_review_id]
            
            # Update the occurrence
            try:
                client.table('review_analysis_aspect_occurrences').update({
                    'review_id': new_review_id
                }).eq('aspect_pk', occurrence['aspect_pk']).eq('review_id', old_review_id).execute()
                
                updated_count += 1
                logger.debug(f"Updated occurrence {occurrence['aspect_pk']}: {old_review_id} → {new_review_id}")
                
            except Exception as e:
                logger.error(f"Failed to update occurrence {occurrence['aspect_pk']}: {e}")
    
    return updated_count

def fix_review_id_mappings_for_asins(asins: List[str]) -> Dict[str, int]:
    """Fix review_id mappings for multiple ASINs."""
    results = {}
    
    for asin in asins:
        logger.info(f"🔄 Fixing review_id mappings for {asin}...")
        
        try:
            # Create mapping
            mapping = create_review_id_mapping(asin)
            
            if mapping:
                # Update occurrences
                updated_count = update_occurrence_review_ids(asin, mapping)
                results[asin] = updated_count
                logger.info(f"  ✅ Updated {updated_count} occurrences for {asin}")
            else:
                logger.warning(f"  ⚠️ No mapping found for {asin}")
                results[asin] = 0
                
        except Exception as e:
            logger.error(f"  ❌ Error fixing {asin}: {e}")
            results[asin] = -1
    
    return results

def verify_fix(asin: str) -> bool:
    """Verify that the fix worked for a specific ASIN."""
    client = get_supabase_client()
    
    # Get aspect_pks for this ASIN
    aspects = client.table('review_analysis_aspects').select('aspect_pk').eq('product_id', asin).limit(5).execute()
    aspect_pks = [aspect['aspect_pk'] for aspect in aspects.data]
    
    if not aspect_pks:
        return False
    
    # Get occurrences for these aspects
    occurrences = client.table('review_analysis_aspect_occurrences').select('review_id').in_('aspect_pk', aspect_pks).execute()
    occurrence_review_ids = set([occ['review_id'] for occ in occurrences.data])
    
    # Get product_reviews for this ASIN
    reviews = client.table('product_reviews').select('review_id').eq('product_id', asin).execute()
    product_review_ids = set([str(review['review_id']) for review in reviews.data])
    
    # Check for overlap
    intersection = occurrence_review_ids.intersection(product_review_ids)
    
    logger.info(f"Verification for {asin}:")
    logger.info(f"  Occurrence review_ids: {list(occurrence_review_ids)[:5]}")
    logger.info(f"  Product review_ids: {list(product_review_ids)[:5]}")
    logger.info(f"  Matching review_ids: {len(intersection)}")
    
    return len(intersection) > 0

def main():
    """Main function to fix review_id mappings."""
    logger.info("🎯 Fix Review ID Mappings")
    logger.info("=" * 80)
    
    # Step 1: Find ASINs with mismatched review_ids
    logger.info("📊 Step 1: Finding ASINs with mismatched review_ids...")
    mismatched_asins = get_asins_with_mismatched_review_ids()
    
    if not mismatched_asins:
        logger.info("✅ No ASINs with mismatched review_ids found.")
        return
    
    logger.info(f"Found {len(mismatched_asins)} ASINs with mismatched review_ids: {mismatched_asins}")
    
    # Step 2: Fix mappings for each ASIN
    logger.info("📊 Step 2: Fixing review_id mappings...")
    results = fix_review_id_mappings_for_asins(mismatched_asins)
    
    # Step 3: Verify fixes
    logger.info("📊 Step 3: Verifying fixes...")
    verification_results = {}
    
    for asin in mismatched_asins:
        if results.get(asin, 0) > 0:
            verification_results[asin] = verify_fix(asin)
        else:
            verification_results[asin] = False
    
    # Step 4: Summary
    logger.info("=" * 80)
    logger.info("📋 FIX SUMMARY")
    logger.info("=" * 80)
    
    success_count = 0
    for asin in mismatched_asins:
        updated_count = results.get(asin, 0)
        verified = verification_results.get(asin, False)
        
        logger.info(f"📦 {asin}:")
        logger.info(f"   Updated occurrences: {updated_count}")
        logger.info(f"   Verification: {'✅' if verified else '❌'}")
        
        if updated_count > 0 and verified:
            success_count += 1
        
        logger.info("")
    
    logger.info("=" * 80)
    logger.info(f"🎉 Fix completed!")
    logger.info(f"   Successfully fixed: {success_count}/{len(mismatched_asins)} ASINs")
    logger.info("=" * 80)
    
    if success_count > 0:
        logger.info("🔄 You should now refresh the materialized view to see the fixes.")
        logger.info("   Run: python refresh_matrix_view.py")

if __name__ == "__main__":
    main() 