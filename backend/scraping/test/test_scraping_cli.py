import subprocess
import sys
import os
import pytest
import time
from core.database.connection import get_supabase_service_client

CLI_PATH = os.path.join(os.path.dirname(__file__), '..', 'cli.py')

CATEGORY_URL = "https://www.amazon.com/Wall-Switches/b/ref=dp_bc_4?ie=UTF8&node=6291358011"
ASINS = ["B0BVKYKKRK", "B0BVKZLT3B", "B01M3XJUAD"]

def colorize(text, color):
    colors = {
        "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m", "cyan": "\033[96m", "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def print_key_scraping_info_multi(latest_reqs, prods, reviews):
    print("\n=== 🗂️ Recent DB Scraping Results ===")
    for i, req in enumerate(latest_reqs):
        status = req.get('status')
        review_status = req.get('review_status')
        workflow = req.get('workflow_stage')
        color = "green" if status == "imported" and review_status == "completed" else "red" if "fail" in (status or "") or "fail" in (review_status or "") else "yellow"
        status_str = colorize(f"{status}/{review_status}", color)
        # Failure reason
        fail_reason = ""
        if color == "red":
            meta = req.get('review_metadata') or {}
            tmeta = req.get('transformation_metadata') or {}
            fail_reason = meta.get('import_error') or meta.get('scrape_error') or tmeta.get('summary', {}).get('message', '')
            if fail_reason:
                fail_reason = f" ❗{fail_reason[:60]}"
        print(f"\n#{i+1} 🆔{req.get('id')} 🏷️{req.get('request_type')} | 📊{status_str} | 🏁{workflow}{fail_reason}")
        print(f"   📦{req.get('products_scraped')} 📝{req.get('reviews_scraped')} | 🕒{req.get('created_at')[-8:]} ➡️ {req.get('updated_at')[-8:]}")
        # Product
        prod = prods[i] if i < len(prods) and prods[i] else None
        if prod:
            print(f"   📦 {prod.get('platform_id','')} | {prod.get('brand','')} | {prod.get('category','')} | 💲{prod.get('price_usd','')} | {prod.get('title','')[:30]}...")
        else:
            print("   📦 No product")
        # Review
        review = reviews[i] if i < len(reviews) and reviews[i] else None
        if review:
            text = review.get('review_text','')
            text_short = ' '.join(text.split()[:10]) + ('...' if len(text.split()) > 10 else '')
            print(f"   📝 {review.get('review_id','')} | {review.get('asin','')} | ⭐{review.get('rating','')} | {review.get('review_title','')[:20]} | {text_short}")
        else:
            print("   📝 No review")
    print("==============================\n")

@pytest.mark.integration
def test_scrape_products_by_category():
    """
    Test scraping a few products under a given category URL using the CLI.
    """
    cmd = [
        sys.executable, '-m', 'scraping.cli',
        '--category-url', CATEGORY_URL,
        '--max-products', '3',
        '--max-reviews', '2',
        '--log-level', 'INFO',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\nCLI output (category scrape):\n", result.stdout)
    assert result.returncode == 0
    assert 'completed' in result.stdout or 'products_only_completed' in result.stdout

    # Wait a moment for DB write
    time.sleep(2)
    client = get_supabase_service_client()
    # Print up to 3 recent results
    reqs = client.table('scraping_requests').select('*').order('updated_at', desc=True).limit(3).execute()
    batch_ids = [r['id'] for r in reqs.data]
    prods = []
    reviews = []
    for bid in batch_ids:
        prod = client.table('amazon_products').select('*').eq('batch_id', bid).limit(1).execute()
        prods.append(prod.data[0] if prod.data else None)
        review = client.table('amazon_reviews').select('*').eq('scrape_batch_id', bid).limit(1).execute()
        reviews.append(review.data[0] if review.data else None)
    print_key_scraping_info_multi(reqs.data, prods, reviews)

@pytest.mark.integration
def test_scrape_products_by_asins():
    """
    Test scraping products by a list of ASINs using the CLI.
    """
    cmd = [
        sys.executable, '-m', 'scraping.cli',
        '--asins', *ASINS,
        '--max-reviews', '2',
        '--log-level', 'INFO',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\nCLI output (ASIN scrape):\n", result.stdout)
    assert result.returncode == 0
    assert 'completed' in result.stdout or 'results' in result.stdout

    # Wait a moment for DB write
    time.sleep(2)
    client = get_supabase_service_client()
    # Print up to 3 recent results
    reqs = client.table('scraping_requests').select('*').order('updated_at', desc=True).limit(3).execute()
    batch_ids = [r['id'] for r in reqs.data]
    prods = []
    reviews = []
    for bid in batch_ids:
        prod = client.table('amazon_products').select('*').eq('batch_id', bid).limit(1).execute()
        prods.append(prod.data[0] if prod.data else None)
        review = client.table('amazon_reviews').select('*').eq('scrape_batch_id', bid).limit(1).execute()
        reviews.append(review.data[0] if review.data else None)
    print_key_scraping_info_multi(reqs.data, prods, reviews)

def test_analyze_all_existing_reviews_none_coverage(tmp_path):
    """
    Test that _analyze_all_existing_reviews does not fail when review_coverage_months is None.
    """
    import json
    import asyncio
    from backend.scraping.reviews.scraper import ReviewScraper
    from datetime import datetime

    # Create a fake review file with a valid review date
    review_data = {
        "scrape_context": {"scraped_at": datetime.now().isoformat()},
        "reviews": [
            {"date": "Reviewed in the United States on July 15, 2025"}
        ]
    }
    review_file = tmp_path / "test_review.json"
    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(review_data, f)

    scraper = ReviewScraper()
    # Should not raise error
    result = asyncio.run(scraper._analyze_all_existing_reviews([str(review_file)], None))
    assert isinstance(result, dict)
    assert "meets_coverage_requirement" in result 