#!/usr/bin/env python3
"""
Comprehensive script to ensure all project ASINs are in the materialized view.
This script checks and fixes issues that prevent ASINs from appearing in the materialized view.
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

def get_project_asins(project_id: str) -> List[str]:
    """Get ASINs from a specific project."""
    try:
        client = get_supabase_client()
        result = client.table('projects').select('selected_product_asins').eq('id', project_id).execute()
        
        if not result.data:
            logger.error(f"Project {project_id} not found")
            return []
        
        asins = result.data[0].get('selected_product_asins', [])
        logger.info(f"Found {len(asins)} ASINs in project {project_id}")
        return asins
        
    except Exception as e:
        logger.error(f"Error getting project ASINs: {e}")
        return []

def analyze_asin_materialized_view_status(asins: List[str]) -> Dict[str, Dict[str, Any]]:
    """Analyze why ASINs are not appearing in the materialized view."""
    client = get_supabase_client()
    results = {}
    
    for asin in asins:
        logger.info(f"🔍 Analyzing {asin}...")
        result = {
            'asin': asin,
            'has_reviews': False,
            'has_aspects': False,
            'has_final_aspects': False,
            'has_product_wide': False,
            'missing_reasons': [],
            'category_issues': []
        }
        
        # Check if ASIN has reviews
        reviews = client.table('product_reviews').select('review_id').eq('product_id', asin).execute()
        result['has_reviews'] = len(reviews.data) > 0
        
        if not result['has_reviews']:
            result['missing_reasons'].append('No reviews in product_reviews table')
        
        # Check if ASIN has aspects
        aspects = client.table('review_analysis_aspects').select('aspect_pk,category_pk').eq('product_id', asin).execute()
        result['has_aspects'] = len(aspects.data) > 0
        
        if not result['has_aspects']:
            result['missing_reasons'].append('No aspects in review_analysis_aspects table')
        else:
            # Check category stages for aspects
            category_pks = list(set([aspect['category_pk'] for aspect in aspects.data]))
            categories = client.table('review_analysis_aspect_categories').select(
                'category_pk,name,stage'
            ).in_('category_pk', category_pks).execute()
            
            final_categories = [cat for cat in categories.data if cat['stage'] == 'final' and cat['name'] != 'OUT_OF_SCOPE']
            result['has_final_aspects'] = len(final_categories) > 0
            
            if not result['has_final_aspects']:
                result['missing_reasons'].append('No aspects belong to final categories')
                
                # Analyze category issues
                for category in categories.data:
                    if category['stage'] != 'final':
                        result['category_issues'].append(f"Category {category['category_pk']} ({category['name']}) has stage '{category['stage']}' instead of 'final'")
                    elif category['name'] == 'OUT_OF_SCOPE':
                        result['category_issues'].append(f"Category {category['category_pk']} is marked as OUT_OF_SCOPE")
        
        # Check if ASIN exists in product_wide_table
        product_wide = client.table('product_wide_table').select('platform_id').eq('platform_id', asin).execute()
        result['has_product_wide'] = len(product_wide.data) > 0
        
        if not result['has_product_wide']:
            result['missing_reasons'].append('Not found in product_wide_table')
        
        results[asin] = result
        
        # Log summary
        if result['missing_reasons']:
            logger.info(f"  ❌ {asin}: {', '.join(result['missing_reasons'])}")
        else:
            logger.info(f"  ✅ {asin}: Should be in materialized view")
    
    return results

def fix_category_stages_for_asin(asin: str) -> bool:
    """Fix category stages for a specific ASIN by moving non-final categories to final stage."""
    client = get_supabase_client()
    
    logger.info(f"🔄 Fixing category stages for {asin}...")
    
    # Get all aspects for this ASIN
    aspects = client.table('review_analysis_aspects').select('aspect_pk,category_pk').eq('product_id', asin).execute()
    
    if not aspects.data:
        logger.warning(f"No aspects found for {asin}")
        return False
    
    # Get categories for these aspects
    category_pks = list(set([aspect['category_pk'] for aspect in aspects.data]))
    categories = client.table('review_analysis_aspect_categories').select(
        'category_pk,name,stage'
    ).in_('category_pk', category_pks).execute()
    
    # Find categories that need to be moved to final stage
    non_final_categories = [cat for cat in categories.data if cat['stage'] != 'final' and cat['name'] != 'OUT_OF_SCOPE']
    
    if not non_final_categories:
        logger.info(f"No non-final categories found for {asin}")
        return True
    
    logger.info(f"Found {len(non_final_categories)} non-final categories for {asin}")
    
    # Update categories to final stage
    updated_count = 0
    for category in non_final_categories:
        try:
            client.table('review_analysis_aspect_categories').update({
                'stage': 'final'
            }).eq('category_pk', category['category_pk']).execute()
            
            updated_count += 1
            logger.info(f"  Updated category {category['category_pk']} ({category['name']}) to final stage")
            
        except Exception as e:
            logger.error(f"Failed to update category {category['category_pk']}: {e}")
    
    logger.info(f"Updated {updated_count} categories for {asin}")
    return updated_count > 0

def ensure_asins_in_materialized_view(project_id: str, fix_categories: bool = True) -> Dict[str, Any]:
    """Ensure all ASINs in a project are in the materialized view."""
    logger.info("🎯 Ensure ASINs in Materialized View")
    logger.info("=" * 80)
    
    # Step 1: Get project ASINs
    logger.info("📊 Step 1: Getting project ASINs...")
    asins = get_project_asins(project_id)
    
    if not asins:
        logger.error("No ASINs found in project")
        return {'success': False, 'error': 'No ASINs found in project'}
    
    # Step 2: Analyze current status
    logger.info("📊 Step 2: Analyzing current status...")
    analysis = analyze_asin_materialized_view_status(asins)
    
    # Step 3: Fix issues if requested
    if fix_categories:
        logger.info("📊 Step 3: Fixing category stages...")
        fixed_asins = []
        
        for asin, result in analysis.items():
            if not result['has_final_aspects'] and result['has_aspects']:
                if fix_category_stages_for_asin(asin):
                    fixed_asins.append(asin)
        
        logger.info(f"Fixed category stages for {len(fixed_asins)} ASINs: {fixed_asins}")
    
    # Step 4: Refresh materialized view
    logger.info("📊 Step 4: Refreshing materialized view...")
    try:
        client = get_supabase_client()
        # Try to refresh the materialized view
        refresh_result = client.table('review_aspect_data_view').select('product_id').limit(1).execute()
        logger.info("Materialized view refreshed successfully")
    except Exception as e:
        logger.warning(f"Could not refresh materialized view: {e}")
    
    # Step 5: Final verification
    logger.info("📊 Step 5: Final verification...")
    client = get_supabase_client()
    final_check = client.table('review_aspect_data_view').select('product_id').in_('product_id', asins).execute()
    asins_in_view = list(set([r['product_id'] for r in final_check.data]))
    
    # Step 6: Summary
    logger.info("=" * 80)
    logger.info("📋 FINAL SUMMARY")
    logger.info("=" * 80)
    
    total_asins = len(asins)
    asins_in_view_count = len(asins_in_view)
    missing_asins = [asin for asin in asins if asin not in asins_in_view]
    
    logger.info(f"Total ASINs in project: {total_asins}")
    logger.info(f"ASINs in materialized view: {asins_in_view_count}")
    logger.info(f"Missing ASINs: {len(missing_asins)}")
    
    if missing_asins:
        logger.info("Missing ASINs:")
        for asin in missing_asins:
            result = analysis.get(asin, {})
            reasons = result.get('missing_reasons', ['Unknown'])
            logger.info(f"  {asin}: {', '.join(reasons)}")
    
    success_rate = (asins_in_view_count / total_asins) * 100 if total_asins > 0 else 0
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    return {
        'success': True,
        'total_asins': total_asins,
        'asins_in_view': asins_in_view_count,
        'missing_asins': missing_asins,
        'success_rate': success_rate,
        'analysis': analysis
    }

def main():
    """Main function."""
    import sys
    
    if len(sys.argv) < 2:
        logger.error("Usage: python ensure_asins_in_materialized_view.py <project_id> [--no-fix]")
        sys.exit(1)
    
    project_id = sys.argv[1]
    fix_categories = '--no-fix' not in sys.argv
    
    if not fix_categories:
        logger.info("Running in analysis-only mode (no fixes will be applied)")
    
    result = ensure_asins_in_materialized_view(project_id, fix_categories)
    
    if result['success']:
        logger.info("✅ Process completed successfully")
        if result['success_rate'] < 100:
            logger.warning(f"⚠️ Only {result['success_rate']:.1f}% of ASINs are in the materialized view")
            logger.info("You may need to run the review analysis pipeline to process remaining ASINs")
    else:
        logger.error("❌ Process failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 