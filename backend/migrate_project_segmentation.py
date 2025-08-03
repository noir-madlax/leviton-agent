#!/usr/bin/env python3
"""
Script to migrate product segmentation data from hashed project IDs to a single run.

This script consolidates all segmentation data from multiple hashed project runs
into a single run with the actual project_id, making it easier to manage and query.

Usage:
    python migrate_project_segmentation.py <project_id> [--dry-run]
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from projects.analysis.analyze_project_segmentation import ProjectSegmentationAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_project(project_id: str, dry_run: bool = False) -> bool:
    """
    Migrate project segmentation data.
    
    Args:
        project_id: The project ID to migrate
        dry_run: If True, only analyze without making changes
        
    Returns:
        True if successful, False otherwise
    """
    try:
        analyzer = ProjectSegmentationAnalyzer()
        
        if dry_run:
            logger.info(f"DRY RUN: Analyzing project {project_id} without making changes")
            
            # Find hashed project IDs and assignments
            hashed_project_ids, project_asins = await analyzer.find_project_segmentation_data(project_id)
            
            if not hashed_project_ids:
                logger.warning(f"No hashed project IDs found for project {project_id}")
                return False
            
            logger.info(f"Found {len(hashed_project_ids)} hashed project IDs: {hashed_project_ids}")
            
            # Get assignments to see what would be migrated
            all_assignments = await analyzer.get_segmentation_assignments(hashed_project_ids)
            total_products = len(all_assignments)
            
            logger.info(f"Would migrate {total_products} product assignments")
            logger.info(f"Would create a new run with project_id: {project_id}")
            logger.info("DRY RUN completed - no changes made")
            return True
        else:
            logger.info(f"Starting migration for project {project_id}")
            new_run_id = await analyzer.migrate_project_segmentation_data(project_id)
            
            if new_run_id:
                logger.info(f"Migration completed successfully!")
                logger.info(f"New run_id: {new_run_id}")
                logger.info(f"All segmentation data now uses project_id: {project_id}")
                return True
            else:
                logger.error("Migration failed!")
                return False
                
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate product segmentation data from hashed project IDs to a single run',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze what would be migrated (dry run)
  python migrate_project_segmentation.py d2c02b80-4c82-44cc-8093-56708a7883f7 --dry-run
  
  # Perform the actual migration
  python migrate_project_segmentation.py d2c02b80-4c82-44cc-8093-56708a7883f7
        """
    )
    parser.add_argument('project_id', help='Project ID to migrate')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Analyze what would be migrated without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = await migrate_project(args.project_id, args.dry_run)
    
    if success:
        logger.info("Operation completed successfully!")
        sys.exit(0)
    else:
        logger.error("Operation failed!")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main()) 