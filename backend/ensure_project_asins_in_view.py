#!/usr/bin/env python3
"""
Script to ensure all ASINs in project.selected_product_asins are processed through 
the review analysis pipeline and included in the materialized view.
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

# Add project root to Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.database.connection import get_supabase_client
from review_analysis.cli import run_review_analysis_pipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def get_project_asins(project_id: str) -> List[str]:
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

async def check_asins_in_materialized_view(asins: List[str]) -> Dict[str, bool]:
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

async def check_asins_have_review_analysis(asins: List[str]) -> Dict[str, bool]:
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

async def run_review_analysis_for_asins(asins: List[str]) -> bool:
    """Run the review analysis pipeline for specific ASINs."""
    try:
        logger.info(f"Running review analysis pipeline for {len(asins)} ASINs...")
        
        # Run the review analysis pipeline
        # Note: This assumes the pipeline can handle specific ASINs
        # You may need to modify the pipeline to accept ASIN parameters
        success = await run_review_analysis_pipeline(asins)
        
        if success:
            logger.info("✅ Review analysis pipeline completed successfully")
        else:
            logger.error("❌ Review analysis pipeline failed")
            
        return success
        
    except Exception as e:
        logger.error(f"Error running review analysis pipeline: {e}")
        return False

async def refresh_materialized_view() -> bool:
    """Refresh the materialized view to include new data."""
    try:
        logger.info("🔄 Refreshing materialized view...")
        
        # Import and run the refresh script
        from refresh_matrix_view import main as refresh_main
        await refresh_main()
        
        logger.info("✅ Materialized view refreshed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error refreshing materialized view: {e}")
        return False

async def ensure_project_asins_in_view(project_id: str, force_analysis: bool = False) -> Dict[str, Any]:
    """Main function to ensure all project ASINs are in the materialized view."""
    logger.info(f"🎯 Ensuring all ASINs in project {project_id} are in materialized view")
    logger.info("=" * 80)
    
    # Step 1: Get project ASINs
    asins = await get_project_asins(project_id)
    if not asins:
        return {"status": "error", "message": "No ASINs found in project"}
    
    # Step 2: Check current status
    logger.info("📊 Checking current status...")
    asins_in_view = await check_asins_in_materialized_view(asins)
    asins_with_analysis = await check_asins_have_review_analysis(asins)
    
    # Step 3: Identify missing ASINs
    missing_from_view = [asin for asin in asins if not asins_in_view[asin]]
    missing_analysis = [asin for asin in asins if not asins_with_analysis[asin]]
    
    logger.info(f"Missing from materialized view: {missing_from_view}")
    logger.info(f"Missing review analysis: {missing_analysis}")
    
    if not missing_from_view and not force_analysis:
        logger.info("✅ All ASINs are already in the materialized view!")
        return {
            "status": "success", 
            "message": "All ASINs already in view",
            "asins_in_view": len([a for a in asins if asins_in_view[a]]),
            "total_asins": len(asins)
        }
    
    # Step 4: Run review analysis for missing ASINs
    if missing_analysis or force_analysis:
        logger.info(f"🔄 Running review analysis for {len(missing_analysis)} missing ASINs...")
        analysis_success = await run_review_analysis_for_asins(missing_analysis)
        
        if not analysis_success:
            return {"status": "error", "message": "Review analysis pipeline failed"}
    
    # Step 5: Refresh materialized view
    logger.info("🔄 Refreshing materialized view...")
    refresh_success = await refresh_materialized_view()
    
    if not refresh_success:
        return {"status": "error", "message": "Failed to refresh materialized view"}
    
    # Step 6: Verify final status
    logger.info("📊 Verifying final status...")
    final_asins_in_view = await check_asins_in_materialized_view(asins)
    final_missing = [asin for asin in asins if not final_asins_in_view[asin]]
    
    if final_missing:
        logger.warning(f"⚠️  Still missing from view: {final_missing}")
        return {
            "status": "partial_success",
            "message": f"Some ASINs still missing: {final_missing}",
            "asins_in_view": len([a for a in asins if final_asins_in_view[a]]),
            "total_asins": len(asins),
            "missing_asins": final_missing
        }
    else:
        logger.info("✅ All ASINs are now in the materialized view!")
        return {
            "status": "success",
            "message": "All ASINs now in view",
            "asins_in_view": len(asins),
            "total_asins": len(asins)
        }

async def main():
    """Main CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ensure all project ASINs are in the materialized view",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('project_id', help='Project ID to check')
    parser.add_argument('--force', action='store_true', 
                       help='Force re-run review analysis even if ASINs exist')
    
    args = parser.parse_args()
    
    result = await ensure_project_asins_in_view(args.project_id, args.force)
    
    logger.info("=" * 80)
    logger.info(f"Final result: {result}")
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 