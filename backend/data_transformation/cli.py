"""Command line interface for data transformation."""

import argparse
import logging
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data_transformation.services.transformation_service import DataTransformationService
from data_transformation.models import TransformationConfig

def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def run_transformation(args):
    """Run data transformation with given arguments."""
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Create configuration
    config = TransformationConfig(
        batch_size=args.batch_size,
        skip_existing=args.skip_existing,
        validate_calculations=args.validate_calculations,
        dry_run=args.dry_run,
        log_level=args.log_level
    )
    
    logger.info(f"Starting data transformation with config:")
    logger.info(f"  Limit: {args.limit}")
    logger.info(f"  Batch size: {config.batch_size}")
    logger.info(f"  Skip existing: {config.skip_existing}")
    logger.info(f"  Validate calculations: {config.validate_calculations}")
    logger.info(f"  Dry run: {config.dry_run}")
    
    # Execute transformation
    service = DataTransformationService(config)
    result = service.transform_batch(args.limit)
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 TRANSFORMATION RESULTS")
    print("=" * 60)
    print(f"✅ Success: {result.success}")
    print(f"📝 Processed: {result.processed_count}")
    print(f"⏭️  Skipped: {result.skipped_count}")  
    print(f"❌ Errors: {result.error_count}")
    print(f"⏱️  Duration: {result.duration_seconds:.2f}s")
    
    if result.summary:
        print(f"\n📈 SUMMARY:")
        for key, value in result.summary.items():
            print(f"  {key}: {value}")
    
    if result.errors and not args.quiet:
        print(f"\n⚠️  ERRORS ({len(result.errors)}):")
        for i, error in enumerate(result.errors[:10], 1):  # Show first 10 errors
            print(f"  {i}. {error}")
        if len(result.errors) > 10:
            print(f"  ... and {len(result.errors) - 10} more errors")

def get_stats(args):
    """Get transformation statistics."""
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    service = DataTransformationService()
    stats = service.get_transformation_stats()
    
    print("\n" + "=" * 60)
    print("📊 TRANSFORMATION STATISTICS")
    print("=" * 60)
    
    if 'error' in stats:
        print(f"❌ Error: {stats['error']}")
        return
    
    print(f"📦 Source records: {stats.get('source_records', 0)}")
    print(f"✅ Transformed records: {stats.get('transformed_records', 0)}")
    print(f"📈 Coverage: {stats.get('coverage_percent', 0)}%")
    print(f"📋 Remaining records: {stats.get('remaining_records', 0)}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Data Transformation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transform 100 records in dry-run mode
  python cli.py transform --limit 100 --dry-run
  
  # Transform all data with custom batch size
  python cli.py transform --batch-size 50 --no-skip-existing
  
  # Get transformation statistics
  python cli.py stats
  
  # Run in debug mode
  python cli.py transform --limit 10 --log-level DEBUG
        """
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Transform command
    transform_parser = subparsers.add_parser('transform', help='Run data transformation')
    transform_parser.add_argument('--limit', type=int, help='Limit number of records to process')
    transform_parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    transform_parser.add_argument('--no-skip-existing', action='store_false', dest='skip_existing', 
                                help='Don\'t skip existing records')
    transform_parser.add_argument('--no-validate', action='store_false', dest='validate_calculations',
                                help='Skip calculation validation')
    transform_parser.add_argument('--dry-run', action='store_true', help='Test mode - don\'t write to database')
    transform_parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                                default='INFO', help='Logging level')
    transform_parser.add_argument('--quiet', action='store_true', help='Suppress error details')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Get transformation statistics')
    stats_parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                            default='INFO', help='Logging level')
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == 'transform':
        run_transformation(args)
    elif args.command == 'stats':
        get_stats(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 