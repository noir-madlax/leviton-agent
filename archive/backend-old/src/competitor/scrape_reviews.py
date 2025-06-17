import json
import os
import asyncio
import aiofiles
import pandas as pd
from datetime import datetime, timedelta
from apify_client import ApifyClient

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "scraped")
AMAZON_REVIEW_DIR = os.path.join(OUTPUT_DIR, "amazon", "review")

# Ensure directory exists
os.makedirs(AMAZON_REVIEW_DIR, exist_ok=True)

# Apify API Configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
AXESSO_ACTOR_ID = "ZebkvH3nVOrafqr5T"

# Amazon Review Scraper Configuration (constant across all requests)
MAX_PAGES_PER_ASIN = 5  # Maximum pages to scrape per ASIN in single API call
DEFAULT_REVIEWS_PER_PAGE = 10  # Default number of reviews per page when currentPage is missing

AMAZON_REVIEW_CONFIG = {
    "domainCode": "com",           # Amazon.com (US marketplace)
    "sortBy": "recent",            # Sort by most recent reviews
    "maxPages": MAX_PAGES_PER_ASIN,  # Maximum pages per request
    "filterByStar": None,          # No star filter (all ratings)
    "filterByKeyword": None,       # No keyword filter
    "reviewerType": "verified_reviews",  # Only verified purchase reviews
    "formatType": "current_format",      # Use current Amazon review format
    "mediaType": "all_contents"          # Include all content types
}

# Configuration constants
RATE_LIMIT_DELAY = 0.1  # seconds - 100ms delay between individual requests
MAX_CONCURRENT_REQUESTS = 32  # Maximum concurrent API requests
SCRAPE_RECENCY_DAYS = 30  # Days to consider a scrape "recent"
DAYS_PER_MONTH = 30  # Approximation for months to days conversion
DEFAULT_COVERAGE_MONTHS = 6  # Default months of review coverage required

# Review date filtering constants
MIN_REVIEW_YEAR = 2010  # Earliest acceptable review year
MAX_REVIEW_YEAR = datetime.now().year  # Latest acceptable review year (current year)

async def get_existing_review_files(asin):
    """
    Get all existing review files for a given ASIN.
    
    Args:
        asin (str): Amazon ASIN
    
    Returns:
        list: List of existing file paths for this ASIN
    """
    existing_files = []
    for filename in os.listdir(AMAZON_REVIEW_DIR):
        if filename.startswith(f"{asin}_") and filename.endswith("_reviews.json"):
            existing_files.append(os.path.join(AMAZON_REVIEW_DIR, filename))
    return existing_files

def get_amazon_reviews_apify(asin):
    """
    Get Amazon product reviews using Axesso Amazon Review Scraper via Apify API.
    
    Args:
        asin (str): Amazon product ASIN
    
    Returns:
        dict: Processed reviews data with actual page information
    """
    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN environment variable is required")
    
    # Initialize the ApifyClient
    client = ApifyClient(APIFY_API_TOKEN)
    
    # Create the input configuration
    config = AMAZON_REVIEW_CONFIG.copy()
    config["asin"] = asin
    
    run_input = {"input": [config]}
    
    try:
        # Run the Actor and wait for it to finish
        print(f"   🔄 Starting Apify actor for ASIN {asin}, max_pages={MAX_PAGES_PER_ASIN}...")
        run = client.actor(AXESSO_ACTOR_ID).call(run_input=run_input)
        
        # Fetch results from the run's dataset
        all_items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            all_items.append(item)
        
        if not all_items:
            return {
                "reviews": [],
                "total_reviews": 0,
                "max_pages_requested": MAX_PAGES_PER_ASIN,
                "max_pages_reached": 0,
                "fetched_all_available_reviews": True,  # No reviews means we've seen all (zero) reviews
                "success": True
            }
        
        # Extract reviews and determine actual pages reached
        all_reviews = []
        max_current_page = 0
        has_current_page_info = False
        
        for item in all_items:
            # Each item should have currentPage and be a review
            if "currentPage" in item:
                current_page = item.get("currentPage", 1)
                max_current_page = max(max_current_page, current_page)
                has_current_page_info = True
            
            # The item itself is a review if it has review fields
            if "reviewId" in item or "text" in item:
                all_reviews.append(item)
        
        # Determine if we've reached all available pages
        if has_current_page_info:
            # If we have page info, check if we reached max pages OR got fewer reviews than expected
            fetched_all_available_reviews = (max_current_page >= MAX_PAGES_PER_ASIN or 
                                           len(all_reviews) < MAX_PAGES_PER_ASIN * DEFAULT_REVIEWS_PER_PAGE)
        else:
            # If no page info, estimate based on total reviews vs expected
            expected_reviews_for_max_pages = MAX_PAGES_PER_ASIN * DEFAULT_REVIEWS_PER_PAGE
            fetched_all_available_reviews = len(all_reviews) < expected_reviews_for_max_pages
            max_current_page = min(MAX_PAGES_PER_ASIN, max(1, len(all_reviews) // DEFAULT_REVIEWS_PER_PAGE))
        
        return {
            "reviews": all_reviews,
            "total_reviews": len(all_reviews),
            "max_pages_requested": MAX_PAGES_PER_ASIN,
            "max_pages_reached": max_current_page,
            "fetched_all_available_reviews": fetched_all_available_reviews,
            "success": True
        }
        
    except Exception as e:
        print(f"   ❌ Apify API error: {str(e)}")
        return {
            "reviews": [],
            "total_reviews": 0,
            "max_pages_requested": MAX_PAGES_PER_ASIN,
            "max_pages_reached": 0,
            "fetched_all_available_reviews": False,
            "success": False,
            "error": str(e)
        }

def parse_review_date(date_str):
    """
    Parse review date string to datetime object.
    Handles Axesso API format: "Reviewed in the United States on May 23, 2025"
    
    Args:
        date_str (str): Date string from review
    
    Returns:
        datetime or None: Parsed datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Extract date part from Axesso format: "Reviewed in [Country] on [Date]"
    if " on " in date_str:
        date_part = date_str.split(" on ")[-1].strip()
    else:
        date_part = date_str.strip()
    
    # Try various date formats
    date_formats = [
        "%B %d, %Y",      # "May 23, 2025"
        "%b %d, %Y",      # "May 23, 2025" (abbreviated month)
        "%m/%d/%Y",       # "05/23/2025"
        "%Y-%m-%d",       # "2025-05-23"
        "%d %B %Y",       # "23 May 2025"
        "%d %b %Y"        # "23 May 2025" (abbreviated month)
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_part, fmt)
        except ValueError:
            continue
    
    return None

def is_valid_review_date(review_date_str):
    """
    Validate if a review date is within acceptable bounds.
    
    Args:
        review_date_str (str): Review date string
    
    Returns:
        bool: True if date is valid and within bounds
    """
    parsed_date = parse_review_date(review_date_str)
    if not parsed_date:
        return False
    
    # Check year bounds
    review_year = parsed_date.year
    return MIN_REVIEW_YEAR <= review_year <= MAX_REVIEW_YEAR

async def analyze_all_existing_reviews(filepaths, review_coverage_months):
    """
    Analyze all existing review files to determine if we need to scrape again.
    
    Skip Conditions (ANY condition triggers skip):
    1. No recent scrape: Must have at least one file scraped within the last 30 days
    2. Earliest reviews already fetched in previous scrape
    3. All available reviews already fetched with current max pages setting
    4. Sufficient coverage: Combined reviews span at least the specified duration
    
    Args:
        filepaths (list): List of file paths to analyze
        review_coverage_months (int): Required months of review coverage to skip
    
    Returns:
        dict: Analysis result with skip recommendation
    """
    all_reviews = []
    scrape_dates = []
    earliest_reviews_fetched = False
    max_pages_already_reached = False
    
    for filepath in filepaths:
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
            
            # Extract metadata
            scrape_date_str = data.get("scrape_metadata", {}).get("scrape_date", "")
            reviews = data.get("reviews_data", {}).get("reviews", [])
            
            # Check if earliest reviews were fetched in this scrape
            scrape_metadata = data.get("scrape_metadata", {})
            if scrape_metadata.get("earliest_reviews_fetched", False):
                earliest_reviews_fetched = True
            
            # Check if we've already fetched all available reviews with current setting
            if (scrape_metadata.get("fetched_all_available_reviews", False) and 
                scrape_metadata.get("max_pages_requested", 0) == MAX_PAGES_PER_ASIN):
                max_pages_already_reached = True
            
            # Add scrape date
            if scrape_date_str:
                scrape_date = datetime.fromisoformat(scrape_date_str.replace('Z', '+00:00'))
                scrape_dates.append(scrape_date.replace(tzinfo=None))
            
            # Add all reviews
            all_reviews.extend(reviews)
            
        except Exception:
            continue  # Skip files that can't be parsed
    
    if not scrape_dates:
        return {
            "should_skip": False,
            "reason": "no_valid_scrapes",
            "details": "No valid scrape files found"
        }
    
    # Check if any scrape was within last month
    most_recent_scrape = max(scrape_dates)
    days_since_recent_scrape = (datetime.now() - most_recent_scrape).days
    
    if days_since_recent_scrape > SCRAPE_RECENCY_DAYS:
        return {
            "should_skip": False,
            "reason": "all_scrapes_too_old",
            "details": f"Most recent scrape was {days_since_recent_scrape} days ago (>{SCRAPE_RECENCY_DAYS} days)"
        }
    
    # If we've already fetched the earliest reviews, skip regardless of coverage
    if earliest_reviews_fetched:
        return {
            "should_skip": True,
            "reason": "earliest_reviews_already_fetched",
            "details": f"Earliest reviews already fetched in previous scrape, {len(all_reviews)} total reviews available"
        }
    
    # If we've already fetched all available reviews with current setting, skip
    if max_pages_already_reached:
        return {
            "should_skip": True,
            "reason": "all_available_reviews_already_fetched",
            "details": f"All available reviews already fetched with {MAX_PAGES_PER_ASIN} max pages in previous scrape, {len(all_reviews)} total reviews available"
        }
    
    # Analyze combined review date coverage
    review_dates = []
    for review in all_reviews:
        review_date = parse_review_date(review.get("date", ""))
        if review_date:
            review_dates.append(review_date)
    
    if not review_dates:
        return {
            "should_skip": False,
            "reason": "no_valid_review_dates",
            "details": "No parseable review dates found across all files"
        }
    
    # Check review coverage span
    review_dates.sort()
    oldest_review = review_dates[0]
    newest_review = review_dates[-1]
    coverage_days = (newest_review - oldest_review).days
    required_days = review_coverage_months * DAYS_PER_MONTH
    
    if coverage_days >= required_days:
        return {
            "should_skip": True,
            "reason": "sufficient_coverage",
            "details": f"Recent scrape {days_since_recent_scrape} days ago, {len(all_reviews)} total reviews spanning {coverage_days} days (≥{required_days} days required)"
        }
    else:
        return {
            "should_skip": False,
            "reason": "insufficient_coverage",
            "details": f"Reviews span only {coverage_days} days, need {required_days} days coverage"
        }

async def determine_skip_action(asin, review_coverage_months):
    """
    Determine if we should skip scraping for this ASIN based on all existing files.
    
    Skip Logic Documentation:
    1. Get all existing review files for this ASIN
    2. If no files exist → DON'T SKIP (scrape)
    3. If files exist → Analyze ALL files combined:
       a. At least one file must have been scraped within last SCRAPE_RECENCY_DAYS days
       b. Combined reviews must span ≥specified months of coverage
       c. Both conditions must be met to SKIP
    4. Always create new timestamped files to avoid overwriting
    
    Args:
        asin (str): Amazon ASIN
        review_coverage_months (int): Required months of review coverage to skip
    
    Returns:
        dict: Skip decision with reasoning
    """
    existing_files = await get_existing_review_files(asin)
    
    if not existing_files:
        return {
            "should_skip": False,
            "reason": "no_existing_files",
            "details": "No previous review files found for this ASIN"
        }
    
    # Analyze all files combined
    analysis = await analyze_all_existing_reviews(existing_files, review_coverage_months)
    
    analysis["total_existing_files"] = len(existing_files)
    analysis["analyzed_files"] = [os.path.basename(f) for f in existing_files]
    
    return analysis

async def generate_filename(asin):
    """
    Generate filename for saving reviews.
    
    Args:
        asin (str): Amazon ASIN
    
    Returns:
        str: Filename for saving reviews
    """
    date_str = datetime.now().strftime("%Y%m%d")
    base_filename = f"{asin}_{date_str}_reviews.json"
    filepath = os.path.join(AMAZON_REVIEW_DIR, base_filename)
    
    # If file already exists today, add timestamp to avoid overwriting
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{asin}_{date_str}_{timestamp}_reviews.json"
    else:
        filename = base_filename
    
    return filename

async def save_reviews_with_context(asin, reviews_data, filepath, earliest_reviews_fetched=False, max_pages_info=None):
    """
    Save reviews data with product context information.
    
    Args:
        asin (str): Amazon product ASIN
        reviews_data (dict): Reviews data from API
        filepath (str): File path to save to
        earliest_reviews_fetched (bool): Whether the earliest reviews were fetched
        max_pages_info (dict): Max pages information from API response
    """
    # Prepare data structure with context
    scrape_metadata = {
        "scrape_date": datetime.now().isoformat(),
        "source": "amazon_axesso_apify_api",
        "asin": asin,
        "scraper_version": "3.0",
        "earliest_reviews_fetched": earliest_reviews_fetched
    }
    
    # Add max pages information if provided
    if max_pages_info:
        scrape_metadata.update({
            "max_pages_requested": max_pages_info.get("max_pages_requested", MAX_PAGES_PER_ASIN),
            "max_pages_reached": max_pages_info.get("max_pages_reached", 0),
            "fetched_all_available_reviews": max_pages_info.get("fetched_all_available_reviews", False)
        })
    
    output_data = {
        "scrape_metadata": scrape_metadata,
        "reviews_data": reviews_data
    }
    
    async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(output_data, indent=2, ensure_ascii=False))

async def scrape_product_reviews(asin, semaphore, review_coverage_months):
    """
    Scrape reviews for a single product using Axesso Amazon Review Scraper via Apify API.
    
    Gets up to MAX_PAGES_PER_ASIN pages of reviews in a single API call.
    
    Args:
        asin (str): Amazon product ASIN
        semaphore: Asyncio semaphore for rate limiting
        review_coverage_months (int): Required months of review coverage to skip
    """
    async with semaphore:
        title = f"Product {asin}"  # Simple title since we don't have product info
        
        # Determine if we should skip based on existing data
        skip_analysis = await determine_skip_action(asin, review_coverage_months)
        
        if skip_analysis["should_skip"]:
            print(f"⏩ Skipping {asin} - {title[:50]}... ({skip_analysis['reason']})")
            print(f"   📋 {skip_analysis['details']}")
            return {
                "status": "skipped", 
                "asin": asin, 
                "reason": skip_analysis["reason"],
                "details": skip_analysis["details"]
            }
        
        # Generate new filename (will include timestamp if needed)
        filename = await generate_filename(asin)
        filepath = os.path.join(AMAZON_REVIEW_DIR, filename)
        
        try:
            print(f"🔍 Scraping reviews for {asin} - {title[:50]}...")
            print(f"   📄 Will save to: {filename}")
            
            # Calculate cutoff date for review coverage
            cutoff_date = datetime.now() - timedelta(days=review_coverage_months * DAYS_PER_MONTH)
            
            # Rate limiting
            await asyncio.sleep(RATE_LIMIT_DELAY)
            
            # Get reviews using Apify API (single call gets up to MAX_PAGES_PER_ASIN pages)
            reviews_data = get_amazon_reviews_apify(asin=asin)
            
            if not reviews_data or not reviews_data.get("success", False):
                error_msg = reviews_data.get("error", "Unknown error") if reviews_data else "No response"
                print(f"   ❌ API error: {error_msg}")
                return {"status": "error", "asin": asin, "error": error_msg}
            
            if "reviews" not in reviews_data:
                print(f"   ⚠️  No reviews data returned")
                return {"status": "error", "asin": asin, "error": "No reviews data in response"}
            
            all_page_reviews = reviews_data.get("reviews", [])
            if not all_page_reviews:
                print(f"   📄 No reviews found - product may have no reviews")
                return {"status": "success", "asin": asin, "review_count": 0, "earliest_reviews_fetched": True}
            
            # Filter reviews by date and validity
            all_reviews = []
            page_has_old_reviews = False
            
            for review in all_page_reviews:
                review_date_str = review.get("date", "")
                
                # Validate review date
                if is_valid_review_date(review_date_str):
                    review_date = parse_review_date(review_date_str)
                    if review_date and review_date < cutoff_date:
                        page_has_old_reviews = True
                all_reviews.append(review)
            
            # Get actual page information from API response
            max_pages_requested = reviews_data.get("max_pages_requested", MAX_PAGES_PER_ASIN)
            max_pages_reached = reviews_data.get("max_pages_reached", 0)
            fetched_all_available_reviews = reviews_data.get("fetched_all_available_reviews", False)
            
            # Determine if we got the earliest reviews
            earliest_reviews_fetched = fetched_all_available_reviews or page_has_old_reviews
            
            print(f"   ✅ Retrieved {len(all_reviews)} reviews from {max_pages_reached} pages (requested up to {max_pages_requested})")
            if page_has_old_reviews:
                print(f"   🎯 Found reviews older than {review_coverage_months} months")
            if fetched_all_available_reviews:
                print(f"   📄 Fetched all available reviews ({max_pages_reached} pages available)")
            
            # Prepare combined reviews data
            combined_reviews_data = {
                "reviews": all_reviews,
                "total_reviews": len(all_reviews),
                "pages_scraped": max_pages_reached,
                "earliest_reviews_fetched": earliest_reviews_fetched,
                "review_coverage_months": review_coverage_months
            }
            
            # Prepare max pages info for metadata
            max_pages_info = {
                "max_pages_requested": max_pages_requested,
                "max_pages_reached": max_pages_reached,
                "fetched_all_available_reviews": fetched_all_available_reviews
            }
            
            # Create minimal product info since we only have ASIN
            minimal_product_info = {
                "platform_id": asin,
                "title": title,
                "brand": "Unknown",
                "model_number": "Unknown",
                "price_usd": None,
                "rating": None,
                "reviews_count": None,
                "category": "Unknown",
                "product_segment": "Unknown",
                "product_url": f"https://www.amazon.com/dp/{asin}"
            }
            
            # Save reviews with context
            await save_reviews_with_context(
                asin,
                combined_reviews_data, 
                filepath, 
                earliest_reviews_fetched,
                max_pages_info
            )
            
            review_count = len(all_reviews)
            status_msg = "✅ Saved"
            if earliest_reviews_fetched:
                status_msg += " (earliest reviews fetched)"
                
            print(f"{status_msg} {review_count} reviews from {max_pages_reached} pages for {asin} - {title[:50]}...")
            
            return {
                "status": "success", 
                "asin": asin, 
                "review_count": review_count,
                "pages_scraped": max_pages_reached,
                "max_pages_requested": max_pages_requested,
                "fetched_all_available_reviews": fetched_all_available_reviews,
                "earliest_reviews_fetched": earliest_reviews_fetched,
                "filepath": filepath,
                "skip_analysis": skip_analysis
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error scraping {asin} - {title[:50]}...: {error_msg}")
            return {"status": "error", "asin": asin, "error": error_msg}

async def scrape_all_amazon_reviews(review_coverage_months=DEFAULT_COVERAGE_MONTHS):
    """
    Main function to scrape reviews for all non-out-of-scope Amazon products.
    
    Skip Logic (ALL conditions must be met to skip):
    1. At least one existing file scraped within SCRAPE_RECENCY_DAYS days
    2. Combined reviews from all files span ≥review_coverage_months of time coverage
    
    Args:
        review_coverage_months (int): Required months of review coverage to skip (default: DEFAULT_COVERAGE_MONTHS)
    """
    print("🚀 Starting Amazon reviews scraping...")
    print("\n📋 Skip Logic (ANY condition will trigger skip):")
    print(f"   • No recent scrape: Must have one file scraped within {SCRAPE_RECENCY_DAYS} days")
    print(f"   • Earliest reviews already fetched in previous scrape")
    print(f"   • All available reviews already fetched with current max pages ({MAX_PAGES_PER_ASIN}) setting")
    print(f"   • Sufficient coverage: Combined reviews span ≥{review_coverage_months} months")
    print("   • Always create timestamped files to avoid overwriting")
    print(f"\n📄 API Logic:")
    print(f"   • Single API call fetches up to {MAX_PAGES_PER_ASIN} pages of reviews per ASIN")
    print(f"   • Uses Axesso Amazon Review Scraper via Apify API")
    print(f"\n📅 Date filtering: Reviews from {MIN_REVIEW_YEAR} to {MAX_REVIEW_YEAR}\n")
    
    # Read the CSV file
    csv_path = os.path.join(DATA_DIR, "result", "product_segment", "combined_products_cleaned", "combined_products_with_final_categories.csv")
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    print(f"📊 Reading products from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Filter for Amazon products that are not out of scope
    amazon_products = df[
        (df['source'] == 'amazon') & 
        (df['product_segment'] != 'OUT_OF_SCOPE') &
        (df['platform_id'].notna())  # Ensure ASIN exists
    ].copy()
    
    # Extract ASINs from CSV products
    csv_asins = set(amazon_products['platform_id'].unique())
    
    # Additional ASINs to scrape (manually specified products)
    additional_asins = {
        'B0BVKYKKRK',  # Leviton D26HD
        'B0BVKZLT3B',  # Leviton D215S
        'B0BSHKS26L',  # Lutron Caseta Diva
        'B01EZV35QU',  # TP Link Switch
        'B00NG0ELL0',  # Leviton DSL06
        'B085D8M2MR'   # Lutron Diva
    }
    
    # Combine all unique ASINs
    all_asins = list(csv_asins.union(additional_asins))
    
    print(f"📦 Found {len(csv_asins)} ASINs from CSV + {len(additional_asins)} additional ASINs")
    print(f"📦 Total {len(all_asins)} unique ASINs to scrape")
    
    if len(all_asins) == 0:
        print("⚠️  No ASINs to scrape!")
        return
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    # Track results
    results = []
    
    # Create tasks for all ASINs - semaphore will control concurrency
    print(f"\n📦 Processing {len(all_asins)} ASINs with max {MAX_CONCURRENT_REQUESTS} concurrent requests")
    
    tasks = [
        scrape_product_reviews(asin, semaphore, review_coverage_months) 
        for asin in all_asins
    ]
    
    # Execute all tasks with semaphore-controlled concurrency
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Generate summary
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    skipped = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "skipped")
    errors = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error")
    exceptions = sum(1 for r in results if not isinstance(r, dict))
    
    print("\n📊 Scraping Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ⏩ Skipped: {skipped}")
    print(f"   ❌ Errors: {errors}")
    print(f"   🚫 Exceptions: {exceptions}")
    print(f"   📁 Files saved to: {AMAZON_REVIEW_DIR}")
    
    # Save summary report
    summary_data = {
        "scrape_session": {
            "timestamp": datetime.now().isoformat(),
            "total_asins": len(all_asins),
            "csv_asins": len(csv_asins),
            "additional_asins": len(additional_asins),
            "successful": successful,
            "skipped": skipped,
            "errors": errors,
            "exceptions": exceptions,
            "review_coverage_months": review_coverage_months,
            "configuration": {
                "rate_limit_delay": RATE_LIMIT_DELAY,
                "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
                "scrape_recency_days": SCRAPE_RECENCY_DAYS,
                "min_review_year": MIN_REVIEW_YEAR,
                "max_review_year": MAX_REVIEW_YEAR
            }
        },
        "results": [r for r in results if isinstance(r, dict)]
    }
    
    summary_file = os.path.join(AMAZON_REVIEW_DIR, f"scrape_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    async with aiofiles.open(summary_file, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(summary_data, indent=2, ensure_ascii=False))
    
    print(f"📄 Summary saved to: {summary_file}")

if __name__ == "__main__":
    # Run the async scraper
    asyncio.run(scrape_all_amazon_reviews())

