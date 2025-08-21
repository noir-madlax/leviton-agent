#!/usr/bin/env python3
"""
CLI tool for running targeted review analysis for specific ASINs.

This tool runs extraction + refinement stages for specific ASINs using existing taxonomy
from previous runs, without re-running categorization and consolidation.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database.connection import get_supabase_client
from review_analysis.services.db_review_analysis import DatabaseReviewAnalysisService
from review_analysis.models import ReviewAnalysisRequest

# Sample ASINs for testing
SAMPLE_ASINS = [
    "B0BVKYKKRK",  # Leviton D26HD
    "B0BVKZLT3B",  # Leviton D215S
    "B0BSHKS26L",  # Lutron Caseta Diva
    "B01EZV35QU",  # TP Link Switch
    "B00NG0ELL0",  # Leviton DSL06
    "B085D8M2MR",  # Lutron Diva
]


def setup_logging(verbose: bool = False, log_llm: bool = False) -> None:
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Set specific loggers
    logging.getLogger('review_analysis').setLevel(log_level)
    logging.getLogger('core.llm_taxonomy_pipeline').setLevel(log_level)
    
    if log_llm:
        # Enable LLM interaction logging
        logging.getLogger('core.utils.llm_utils').setLevel(logging.DEBUG)
        logging.getLogger('core.llm_taxonomy_pipeline.pipeline_stage').setLevel(logging.DEBUG)
    
    # Reduce noise from other modules - set to ERROR to completely eliminate debug output
    logging.getLogger('httpx').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('httpcore').setLevel(logging.ERROR)
    logging.getLogger('anthropic').setLevel(logging.ERROR)
    logging.getLogger('hpack').setLevel(logging.ERROR)
    logging.getLogger('anthropic._base_client').setLevel(logging.ERROR)


async def run_targeted_analysis(
    project_id: str,
    asins: List[str],
    product_category: str,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False,
    summary_stats: bool = False
) -> None:
    """Run targeted review analysis for specific ASINs."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 Starting targeted review analysis")
    logger.info(f"   Project ID: {project_id}")
    logger.info(f"   ASINs: {asins}")
    logger.info(f"   Product Category: {product_category}")
    logger.info(f"   Dry Run: {dry_run}")
    logger.info(f"   Verbose: {verbose}")
    
    try:
        # Initialize service
        service = DatabaseReviewAnalysisService()
        
        # Create request
        request = ReviewAnalysisRequest(
            project_id=project_id,
            product_ids=asins,
            product_category=product_category
        )
        
        # Run targeted analysis
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No database changes will be made")
            await service.run_targeted_analysis_dry_run(request)
        else:
            if force:
                logger.info("💾 PRODUCTION MODE - Force re-analysis (may create duplicates)")
            else:
                logger.info("💾 PRODUCTION MODE - Results will be saved to database (skipping existing aspects)")
            analysis_id = await service.run_targeted_analysis(request, force=force)
            logger.info(f"✅ Analysis completed with ID: {analysis_id}")
        
        # Print summary stats if requested
        if summary_stats:
            await print_summary_stats(project_id, asins, product_category, dry_run)
            
    except Exception as e:
        logger.error(f"❌ Error during targeted analysis: {e}")
        if verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


async def print_summary_stats(project_id: str, asins: List[str], product_category: str, dry_run: bool = False) -> None:
    """Print summary statistics for the analyzed ASINs."""
    logger = logging.getLogger(__name__)
    
    logger.info("📊 Generating Summary Statistics...")
    logger.info("=" * 80)
    
    try:
        supabase = get_supabase_client()
        
        # Get project info
        project_result = supabase.table('projects').select('project_name').eq('id', project_id).single().execute()
        project_name = project_result.data.get('project_name', 'Unknown Project') if project_result.data else 'Unknown Project'
        
        logger.info(f"📋 Project: {project_name} ({project_id})")
        logger.info(f"🏷️  Category: {product_category}")
        logger.info(f"🔍 Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
        logger.info("")
        
        # Get existing taxonomy with detailed info
        categories_result = supabase.table('review_analysis_aspect_categories').select(
            'category_pk, name, definition, aspect_type, stage'
        ).eq('project_id', project_id).eq('stage', 'final').neq('name', 'OUT_OF_SCOPE').execute()
        
        categories_by_type = {}
        if categories_result.data:
            for category in categories_result.data:
                aspect_type = category.get('aspect_type', 'unknown')
                if aspect_type not in categories_by_type:
                    categories_by_type[aspect_type] = []
                categories_by_type[aspect_type].append(category)
        
        logger.info("📚 Existing Taxonomy Summary:")
        for aspect_type, categories in categories_by_type.items():
            logger.info(f"   • {aspect_type.upper()}: {len(categories)} categories")
            # Show a few example categories
            for i, cat in enumerate(categories[:3], 1):
                logger.info(f"     {i}. {cat['name']}")
            if len(categories) > 3:
                logger.info(f"     ... and {len(categories) - 3} more")
        logger.info("")
        
        # Process each ASIN
        total_reviews = 0
        total_aspects = 0
        asin_stats = []
        
        for asin in asins:
            # Get product info
            product_result = supabase.table('product_wide_table').select(
                'title, brand, price_usd, monthly_sales_volume, reviews_count'
            ).eq('platform_id', asin).single().execute()
            
            product_info = product_result.data if product_result.data else {}
            product_title = product_info.get('title', f'Product {asin}')
            product_brand = product_info.get('brand', 'Unknown')
            product_price = product_info.get('price_usd', 0)
            product_sales = product_info.get('monthly_sales_volume', 0)
            
            # Get review count
            reviews_result = supabase.table('product_reviews').select(
                'review_id', count='exact'
            ).eq('product_id', asin).execute()
            
            review_count = reviews_result.count or 0
            total_reviews += review_count
            
            # Get extracted aspects count and details (if not dry run)
            aspect_count = 0
            aspects_by_type = {}
            if not dry_run:
                aspects_result = supabase.table('review_analysis_aspects').select(
                    'aspect_pk, aspect_type, detail_text, parent_group_name, category_pk'
                ).eq('project_id', project_id).eq('product_id', asin).execute()
                
                if aspects_result.data:
                    aspect_count = len(aspects_result.data)
                    total_aspects += aspect_count
                    
                    # Group aspects by type
                    for aspect in aspects_result.data:
                        aspect_type = aspect['aspect_type']
                        if aspect_type not in aspects_by_type:
                            aspects_by_type[aspect_type] = []
                        aspects_by_type[aspect_type].append(aspect)
            
            asin_stats.append({
                'asin': asin,
                'title': product_title,
                'brand': product_brand,
                'price': product_price,
                'sales': product_sales,
                'reviews': review_count,
                'aspects': aspect_count,
                'aspects_by_type': aspects_by_type
            })
        
        # Print ASIN details
        logger.info("📦 Product Analysis Summary:")
        logger.info("-" * 80)
        
        for stat in asin_stats:
            logger.info(f"🔸 ASIN: {stat['asin']}")
            logger.info(f"   📝 Title: {stat['title'][:60]}{'...' if len(stat['title']) > 60 else ''}")
            logger.info(f"   🏷️  Brand: {stat['brand']}")
            logger.info(f"   💰 Price: ${stat['price']:.2f}" if stat['price'] else "   💰 Price: N/A")
            logger.info(f"   📈 Monthly Sales: {stat['sales']:,}" if stat['sales'] else "   📈 Monthly Sales: N/A")
            logger.info(f"   📖 Reviews: {stat['reviews']:,}")
            if not dry_run:
                logger.info(f"   🎯 Extracted Aspects: {stat['aspects']:,}")
                
                # Show aspect breakdown by type
                if stat['aspects_by_type']:
                    for aspect_type, aspects in stat['aspects_by_type'].items():
                        logger.info(f"      • {aspect_type.upper()}: {len(aspects)} aspects")
                        
                        # Show a few examples per type
                        examples = aspects[:2]  # Show first 2 examples
                        for i, example in enumerate(examples, 1):
                            if aspect_type == 'use':
                                example_text = example['detail_text']
                            else:
                                parent = example.get('parent_group_name', '')
                                detail = example['detail_text']
                                example_text = f"{parent}: {detail}" if parent else detail
                            logger.info(f"        {i}. {example_text}")
                        if len(aspects) > 2:
                            logger.info(f"        ... and {len(aspects) - 2} more")
            logger.info("")
        
        # Print overall summary
        logger.info("📊 Overall Summary:")
        logger.info("-" * 40)
        logger.info(f"   🎯 Total ASINs: {len(asins)}")
        logger.info(f"   📖 Total Reviews: {total_reviews:,}")
        if not dry_run:
            logger.info(f"   🎯 Total Aspects Extracted: {total_aspects:,}")
            if total_reviews > 0:
                avg_aspects_per_review = total_aspects / total_reviews
                logger.info(f"   📊 Avg Aspects per Review: {avg_aspects_per_review:.2f}")
        
        # Print taxonomy coverage
        if categories_by_type:
            logger.info("")
            logger.info("📚 Taxonomy Coverage:")
            logger.info("-" * 40)
            for aspect_type, categories in categories_by_type.items():
                logger.info(f"   • {aspect_type.upper()}: {len(categories)} categories")
        
        logger.info("=" * 80)
        logger.info("✅ Summary Statistics Complete")
        
    except Exception as e:
        logger.error(f"❌ Error generating summary stats: {e}")
        logger.exception("Full traceback:")


async def test_with_sample_data(verbose: bool = False, summary_stats: bool = False) -> None:
    """Test the CLI with sample data."""
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Running test with sample data")
    
    # Sample project ID (you may need to update this)
    test_project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    
    # Sample ASINs from the provided product list
    test_asins = SAMPLE_ASINS
    
    # Sample product category
    test_category = "Light Switches"
    
    logger.info(f"   Test Project ID: {test_project_id}")
    logger.info(f"   Test ASINs: {test_asins}")
    logger.info(f"   Test Category: {test_category}")
    
    # First, verify the project exists and has existing taxonomy
    try:
        supabase = get_supabase_client()
        
        # Check if project exists
        project_result = supabase.table('projects').select('id, project_name').eq('id', test_project_id).single().execute()
        if not project_result.data:
            logger.error(f"❌ Test project {test_project_id} not found")
            logger.info("💡 Please update the test_project_id in the CLI with a valid project ID")
            return
        
        logger.info(f"✅ Found test project: {project_result.data['project_name']}")
        
        # Check if existing taxonomy exists
        taxonomy_result = supabase.table('review_analysis_aspect_categories').select(
            'category_pk, name, aspect_type, stage'
        ).eq('project_id', test_project_id).eq('stage', 'final').execute()
        
        if not taxonomy_result.data:
            logger.error(f"❌ No existing taxonomy found for project {test_project_id}")
            logger.info("💡 Please run a full review analysis first to create taxonomy")
            return
        
        logger.info(f"✅ Found {len(taxonomy_result.data)} existing categories")
        
        # Check if test ASINs have reviews
        for asin in test_asins:
            reviews_result = supabase.table('product_reviews').select(
                'review_id', count='exact'
            ).eq('product_id', asin).execute()
            
            review_count = reviews_result.count or 0
            logger.info(f"   ASIN {asin}: {review_count} reviews")
            
            if review_count == 0:
                logger.warning(f"⚠️  No reviews found for ASIN {asin}")
        
        # Run the test
        await run_targeted_analysis(
            project_id=test_project_id,
            asins=test_asins,
            product_category=test_category,
            dry_run=True,  # Always dry run for tests
            verbose=verbose,
            summary_stats=summary_stats
        )
        
    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
        if verbose:
            logger.exception("Full traceback:")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run targeted review analysis for specific ASINs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run targeted analysis for specific ASINs
  python -m review_analysis.cli run-targeted \\
    --project-id "d2c02b80-4c82-44cc-8093-56708a7883f7" \\
    --asins "B00MXCRAX8,B00CF4IPGK" \\
    --category "Light Switches"

  # Dry run mode (no database changes)
  python -m review_analysis.cli run-targeted \\
    --project-id "d2c02b80-4c82-44cc-8093-56708a7883f7" \\
    --asins "B00MXCRAX8" \\
    --category "Light Switches" \\
    --dry-run \\
    --verbose

  # Force re-analysis (may create duplicates)
  python -m review_analysis.cli run-targeted \\
    --project-id "d2c02b80-4c82-44cc-8093-56708a7883f7" \\
    --asins "B00MXCRAX8" \\
    --category "Light Switches" \\
    --force \\
    --verbose

  # Test with sample data
  python -m review_analysis.cli test \\
    --verbose

  # Show summary statistics for existing data (no LLM processing)
  python -m review_analysis.cli summary-stats \\
    --project-id "d2c02b80-4c82-44cc-8093-56708a7883f7" \\
    --asins "B00MXCRAX8,B00CF4IPGK" \\
    --category "Light Switches"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # run-targeted command
    run_parser = subparsers.add_parser('run-targeted', help='Run targeted review analysis')
    run_parser.add_argument('--project-id', required=True, help='Project ID')
    run_parser.add_argument('--asins', required=True, help='Comma-separated list of ASINs')
    run_parser.add_argument('--category', required=True, help='Product category')
    run_parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no database changes)')
    run_parser.add_argument('--force', action='store_true', help='Force re-analysis even if aspects already exist (may create duplicates)')
    run_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    run_parser.add_argument('--log-llm', action='store_true', help='Log LLM interactions')
    run_parser.add_argument('--summary-stats', action='store_true', help='Print summary stats after completion')
    
    # test command
    test_parser = subparsers.add_parser('test', help='Test with sample data')
    test_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    test_parser.add_argument('--log-llm', action='store_true', help='Log LLM interactions')
    test_parser.add_argument('--summary-stats', action='store_true', help='Print summary stats after completion')
    
    # summary-stats command
    stats_parser = subparsers.add_parser('summary-stats', help='Show summary statistics for existing data (no LLM processing)')
    stats_parser.add_argument('--project-id', required=True, help='Project ID')
    stats_parser.add_argument('--asins', required=True, help='Comma-separated list of ASINs')
    stats_parser.add_argument('--category', required=True, help='Product category')
    stats_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    log_llm = getattr(args, 'log_llm', False)  # Default to False if not available
    setup_logging(verbose=args.verbose, log_llm=log_llm)
    
    # Run command
    if args.command == 'run-targeted':
        asins = [asin.strip() for asin in args.asins.split(',')]
        asyncio.run(run_targeted_analysis(
            project_id=args.project_id,
            asins=asins,
            product_category=args.category,
            dry_run=args.dry_run,
            force=args.force,
            verbose=args.verbose,
            summary_stats=args.summary_stats
        ))
    elif args.command == 'test':
        asyncio.run(test_with_sample_data(verbose=args.verbose, summary_stats=args.summary_stats))
    elif args.command == 'summary-stats':
        asins = [asin.strip() for asin in args.asins.split(',')]
        asyncio.run(print_summary_stats(
            project_id=args.project_id,
            asins=asins,
            product_category=args.category,
            dry_run=False  # Always show existing data
        ))


if __name__ == '__main__':
    main() 