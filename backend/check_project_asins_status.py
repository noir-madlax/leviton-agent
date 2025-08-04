#!/usr/bin/env python3
"""
Simple script to check the status of project ASINs in the materialized view.
"""

import logging
from typing import List, Dict, Any

from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_asins(project_id: str) -> List[str]:
    """Get ASINs from a specific project."""
    try:
        client = get_supabase_client()
        result = client.table('projects').select('selected_product_asins').eq('id', project_id).execute()
        
        if not result.data:
            logger.error(f"Project {project_id} not found")
            return []
        
        asins = result.data[0].get('selected_product_asins', [])
        logger.info(f"Found {len(asins)} ASINs in project {project_id}: {asins}")
        return asins
        
    except Exception as e:
        logger.error(f"Error getting project ASINs: {e}")
        return []

def check_asins_in_materialized_view(asins: List[str]) -> Dict[str, bool]:
    """Check which ASINs are in the materialized view."""
    try:
        client = get_supabase_client()
        result = client.table('review_aspect_data_view').select('product_id').in_('product_id', asins).execute()
        
        asins_in_view = set([r['product_id'] for r in result.data])
        status = {asin: asin in asins_in_view for asin in asins}
        
        logger.info(f"ASINs in materialized view: {list(asins_in_view)}")
        logger.info(f"ASINs missing from view: {[asin for asin in asins if not status[asin]]}")
        
        return status
        
    except Exception as e:
        logger.error(f"Error checking materialized view: {e}")
        return {asin: False for asin in asins}

def check_asins_have_review_analysis(asins: List[str]) -> Dict[str, bool]:
    """Check which ASINs have been processed through review analysis pipeline."""
    try:
        client = get_supabase_client()
        result = client.table('review_analysis_aspects').select('product_id').in_('product_id', asins).execute()
        
        asins_with_analysis = set([r['product_id'] for r in result.data])
        status = {asin: asin in asins_with_analysis for asin in asins}
        
        logger.info(f"ASINs with review analysis: {list(asins_with_analysis)}")
        logger.info(f"ASINs missing review analysis: {[asin for asin in asins if not status[asin]]}")
        
        return status
        
    except Exception as e:
        logger.error(f"Error checking review analysis: {e}")
        return {asin: False for asin in asins}

def check_asins_have_reviews(asins: List[str]) -> Dict[str, bool]:
    """Check which ASINs have reviews in the product_reviews table."""
    try:
        client = get_supabase_client()
        result = client.table('product_reviews').select('product_id').in_('product_id', asins).execute()
        
        asins_with_reviews = set([r['product_id'] for r in result.data])
        status = {asin: asin in asins_with_reviews for asin in asins}
        
        logger.info(f"ASINs with reviews: {list(asins_with_reviews)}")
        logger.info(f"ASINs missing reviews: {[asin for asin in asins if not status[asin]]}")
        
        return status
        
    except Exception as e:
        logger.error(f"Error checking reviews: {e}")
        return {asin: False for asin in asins}

def check_project_asins_status(project_id: str) -> Dict[str, Any]:
    """Check the status of all ASINs in a project."""
    logger.info(f"🎯 Checking status of ASINs in project {project_id}")
    logger.info("=" * 80)
    
    # Step 1: Get project ASINs
    asins = get_project_asins(project_id)
    if not asins:
        return {"status": "error", "message": "No ASINs found in project"}
    
    # Step 2: Check all statuses
    logger.info("📊 Checking statuses...")
    asins_in_view = check_asins_in_materialized_view(asins)
    asins_with_analysis = check_asins_have_review_analysis(asins)
    asins_with_reviews = check_asins_have_reviews(asins)
    
    # Step 3: Analyze results
    missing_from_view = [asin for asin in asins if not asins_in_view[asin]]
    missing_analysis = [asin for asin in asins if not asins_with_analysis[asin]]
    missing_reviews = [asin for asin in asins if not asins_with_reviews[asin]]
    
    logger.info("=" * 80)
    logger.info("📋 SUMMARY")
    logger.info("=" * 80)
    
    for asin in asins:
        logger.info(f"📦 {asin}:")
        logger.info(f"   Reviews: {'✅' if asins_with_reviews[asin] else '❌'}")
        logger.info(f"   Analysis: {'✅' if asins_with_analysis[asin] else '❌'}")
        logger.info(f"   In View: {'✅' if asins_in_view[asin] else '❌'}")
        logger.info("")
    
    logger.info(f"📊 Overall Status:")
    logger.info(f"   Total ASINs: {len(asins)}")
    logger.info(f"   With reviews: {len([a for a in asins if asins_with_reviews[a]])}")
    logger.info(f"   With analysis: {len([a for a in asins if asins_with_analysis[a]])}")
    logger.info(f"   In materialized view: {len([a for a in asins if asins_in_view[a]])}")
    
    if missing_reviews:
        logger.warning(f"⚠️  ASINs missing reviews: {missing_reviews}")
        logger.warning("   → Run review scraping first")
    
    if missing_analysis and not missing_reviews:
        logger.warning(f"⚠️  ASINs missing analysis: {missing_analysis}")
        logger.warning("   → Run review analysis pipeline")
    
    if missing_from_view and not missing_analysis:
        logger.warning(f"⚠️  ASINs missing from view: {missing_from_view}")
        logger.warning("   → Refresh materialized view")
    
    if not missing_from_view:
        logger.info("✅ All ASINs are in the materialized view!")
    
    return {
        "status": "success",
        "total_asins": len(asins),
        "asins_with_reviews": len([a for a in asins if asins_with_reviews[a]]),
        "asins_with_analysis": len([a for a in asins if asins_with_analysis[a]]),
        "asins_in_view": len([a for a in asins if asins_in_view[a]]),
        "missing_reviews": missing_reviews,
        "missing_analysis": missing_analysis,
        "missing_from_view": missing_from_view
    }

def main():
    """Main CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check the status of project ASINs in the materialized view",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('project_id', help='Project ID to check')
    
    args = parser.parse_args()
    
    result = check_project_asins_status(args.project_id)
    
    logger.info("=" * 80)
    logger.info(f"Final result: {result}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main() 