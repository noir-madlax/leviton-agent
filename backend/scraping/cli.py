import argparse
import uuid
import asyncio
from scraping.orchestrator import ScrapingOrchestrator

# Centralized constants for default values
DEFAULT_MAX_PRODUCTS = 100
DEFAULT_MAX_REVIEWS = 30
DEFAULT_START_PAGE = 1
DEFAULT_END_PAGE = None
DEFAULT_OUTPUT_DIR = "backend/scraping/data/scraped"
DEFAULT_LOG_LEVEL = "INFO"


def parse_args():
    parser = argparse.ArgumentParser(
        description="CLI for scraping Amazon products and their reviews. Either --category-url or one of --product-urls/--asins is required."
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--category-url",
        type=str,
        help="Amazon category page URL to scrape products from."
    )
    group.add_argument(
        "--product-urls",
        nargs='+',
        type=str,
        help="List of Amazon product URLs to scrape."
    )
    group.add_argument(
        "--asins",
        nargs='+',
        type=str,
        help="List of Amazon product ASINs to scrape."
    )

    parser.add_argument(
        "--category-id",
        type=str,
        default=None,
        help="Optional category ID (if available)."
    )
    parser.add_argument(
        "--max-products",
        type=int,
        default=DEFAULT_MAX_PRODUCTS,
        help=f"Maximum number of products to scrape (category mode). Default: {DEFAULT_MAX_PRODUCTS}"
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=DEFAULT_MAX_REVIEWS,
        help=f"Maximum number of reviews per product. Default: {DEFAULT_MAX_REVIEWS}"
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=DEFAULT_START_PAGE,
        help=f"Start page for product listing (category mode). Default: {DEFAULT_START_PAGE}"
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=DEFAULT_END_PAGE,
        help="End page for product listing (category mode). Default: None (no limit)"
    )
    parser.add_argument(
        "--review-start-date",
        type=str,
        default=None,
        help="Only scrape reviews after this date (YYYY-MM-DD)."
    )
    parser.add_argument(
        "--review-end-date",
        type=str,
        default=None,
        help="Only scrape reviews before this date (YYYY-MM-DD)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to store raw scraped data. Default: {DEFAULT_OUTPUT_DIR}"
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        default=None,
        help="Unique batch ID for this run. Default: auto-generated."
    )
    parser.add_argument(
        "--import-to-db",
        action="store_true",
        help="If set, import cleaned data into the database after scraping."
    )
    parser.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        help="Use asyncio for concurrent scraping. Default: True."
    )
    parser.add_argument(
        "--no-async",
        dest="use_async",
        action="store_false",
        help="Disable asyncio for scraping."
    )
    parser.set_defaults(use_async=True)
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry failed scraping tasks. Default: True."
    )
    parser.add_argument(
        "--no-retry-failed",
        dest="retry_failed",
        action="store_false",
        help="Do not retry failed scraping tasks."
    )
    parser.set_defaults(retry_failed=True)
    parser.add_argument(
        "--log-level",
        type=str,
        default=DEFAULT_LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help=f"Logging level. Default: {DEFAULT_LOG_LEVEL}"
    )
    parser.add_argument(
        "--force-reviews",
        action="store_true",
        help="Force review scraping, ignoring existing review files."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    import logging
    logging.basicConfig(level=getattr(logging, args.log_level), format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    batch_id = args.batch_id or str(uuid.uuid4())

    orchestrator = ScrapingOrchestrator()

    if args.category_url:
        # Category mode
        orchestrator_kwargs = {
            "category_url": args.category_url,
            "category_id": args.category_id,
            "max_products": args.max_products,
            "max_reviews": args.max_reviews,
            "start_page": args.start_page,
            "end_page": args.end_page,
            "review_start_date": args.review_start_date,
            "review_end_date": args.review_end_date,
            "output_dir": args.output_dir,
            "batch_id": batch_id,
            "import_to_db": args.import_to_db,
            "use_async": args.use_async,
            "retry_failed": args.retry_failed,
            "log_level": args.log_level,
        }
        # Use asyncio for orchestrator methods
        result = asyncio.run(orchestrator.process_url(
            args.category_url, 
            max_products=args.max_products, 
            scrape_reviews=True,
            review_coverage_months=6,  # Use normal coverage requirement
            max_reviews=args.max_reviews
        ))
        # Print completion message for test detection
        status = result.get("overall_status", "")
        if status:
            print(status)
        else:
            print(result)
    else:
        # Product-list mode (product-urls or asins)
        orchestrator_kwargs = {
            "product_urls": args.product_urls,
            "asins": args.asins,
            "max_reviews": args.max_reviews,
            "review_start_date": args.review_start_date,
            "review_end_date": args.review_end_date,
            "import_to_db": args.import_to_db,
            "use_async": args.use_async,
            "retry_failed": args.retry_failed,
            "log_level": args.log_level,
        }
        result = asyncio.run(orchestrator.process_products_list(**orchestrator_kwargs))
        # Print completion message for test detection
        if isinstance(result, dict) and "results" in result:
            print("results")
        else:
            print(result)

if __name__ == "__main__":
    main() 