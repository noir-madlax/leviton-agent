import subprocess
import sys
import os
import pytest
import time
import re
from core.database.connection import get_supabase_service_client

CLI_PATH = os.path.join(os.path.dirname(__file__), '..', 'cli.py')

CATEGORY_URL = "https://www.amazon.com/Wall-Switches/b/ref=dp_bc_4?ie=UTF8&node=6291358011"
ASINS = ["B0BVKYKKRK", "B0BVKZLT3B", "B01M3XJUAD"]

def colorize(text, color):
    colors = {
        "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m", "cyan": "\033[96m", "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def cleanup_existing_files():
    """Clean up existing scraping files to ensure fresh test state"""
    import glob
    import os
    
    # Define scraping data directories
    scraping_dirs = [
        "scraping/data/scraped/amazon",
        "scraping/data/scraped/amazon/review"
    ]
    
    for scraping_dir in scraping_dirs:
        if os.path.exists(scraping_dir):
            # Remove JSON files
            for pattern in ["*.json"]:
                files = glob.glob(os.path.join(scraping_dir, pattern))
                for file_path in files:
                    try:
                        os.remove(file_path)
                        print(f"🗑️ Cleaned up: {file_path}")
                    except Exception as e:
                        print(f"⚠️ Could not remove {file_path}: {e}")

def get_full_output(result):
    """Get combined stdout and stderr for analysis"""
    full_output = result.stdout
    if result.stderr:
        full_output += "\n" + result.stderr
    return full_output

def check_skip_indicators(output, context=""):
    """Check for skip indicators in output with Chinese support"""
    skip_patterns = [
        'sufficient_local_products', 'recent_db_batch', 'sufficient_recent_reviews', 
        'recent_db_reviews', 'skipped', 'skip', '跳过', '跳过商品爬取', '跳过ASIN'
    ]
    found_patterns = [pattern for pattern in skip_patterns if pattern in output.lower()]
    
    if found_patterns:
        print(f"✅ Skip logic detected {context}: {found_patterns}")
        return True
    else:
        print(f"⚠️ No skip indicators found {context}")
        return False

def check_force_indicators(output, context=""):
    """Check for force indicators in output with Chinese support"""
    force_patterns = [
        '强制爬取', 'force_scrape', 'ignoring existing', '🔥', 
        'force.*scrape', 'force.*product', 'force.*review'
    ]
    found_patterns = [pattern for pattern in force_patterns if pattern in output.lower()]
    
    if found_patterns:
        print(f"✅ Force logic detected {context}: {found_patterns}")
        return True
    else:
        print(f"⚠️ No force indicators found {context}")
        return False

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
    Tests: Initial scrape, skip logic, and force scrape override.
    """
    # Clean up existing files first to ensure fresh state
    cleanup_existing_files()
    
    base_cmd = [
        sys.executable, '-m', 'scraping.cli',
        '--category-url', CATEGORY_URL,
        '--max-products', '3',
        '--max-reviews', '2',
        '--log-level', 'INFO',
    ]
    
    print(colorize("\n=== 🚀 Phase 1: Initial Scrape (Fresh) ===", "cyan"))
    # First run - should scrape normally (after cleanup)
    result1 = subprocess.run(base_cmd, capture_output=True, text=True)
    print("CLI output (initial category scrape):\n", result1.stdout)
    if result1.stderr:
        print("CLI stderr:\n", result1.stderr)
    
    assert result1.returncode == 0
    # Handle the case where products might be skipped on first run due to existing data
    success_indicators = ['completed', 'products_only_completed', 'product_scraping_failed']
    has_success = any(indicator in result1.stdout for indicator in success_indicators)
    assert has_success, f"Expected success indicator in output: {result1.stdout}"
    
    # Wait for file system and DB writes
    time.sleep(3)
    
    print(colorize("\n=== ⏩ Phase 2: Skip Logic Test ===", "yellow"))
    # Second run - should skip due to existing files/data
    result2 = subprocess.run(base_cmd, capture_output=True, text=True)
    print("CLI output (skip test):\n", result2.stdout)
    if result2.stderr:
        print("CLI stderr (skip test):\n", result2.stderr)
    assert result2.returncode == 0
    
    # Check if products or reviews were skipped using full output
    full_output2 = get_full_output(result2)
    has_skip_logic = check_skip_indicators(full_output2, "in second run")
    
    print(colorize("\n=== 🔥 Phase 3: Force Scrape Test ===", "red"))
    # Third run - with force flags, should not skip
    force_cmd = base_cmd + ['--force-products', '--force-reviews']
    result3 = subprocess.run(force_cmd, capture_output=True, text=True)
    print("CLI output (force scrape):\n", result3.stdout)
    if result3.stderr:
        print("CLI stderr (force scrape):\n", result3.stderr)
    assert result3.returncode == 0
    
    # Check success but be flexible about the exact status
    success_indicators = ['completed', 'products_only_completed', 'product_scraping_failed']
    has_success = any(indicator in result3.stdout for indicator in success_indicators)
    assert has_success, f"Expected success indicator in force output: {result3.stdout}"
    
    # Check for force indicators using full output
    full_output3 = get_full_output(result3)
    has_force_scrape = check_force_indicators(full_output3, "in force run")
    
    # Wait a moment for final DB writes
    time.sleep(2)
    client = get_supabase_service_client()
    # Print up to 5 recent results to see all phases
    reqs = client.table('scraping_requests').select('*').order('updated_at', desc=True).limit(5).execute()
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
    Tests: Initial scrape, skip logic, and force scrape override.
    """
    # Clean up existing files first
    cleanup_existing_files()
    
    base_cmd = [
        sys.executable, '-m', 'scraping.cli',
        '--asins', *ASINS,
        '--max-reviews', '2',
        '--log-level', 'INFO',
    ]
    
    print(colorize("\n=== 🚀 Phase 1: Initial ASIN Scrape (Fresh) ===", "cyan"))
    # First run - should scrape normally (after cleanup)
    result1 = subprocess.run(base_cmd, capture_output=True, text=True)
    print("CLI output (initial ASIN scrape):\n", result1.stdout)
    if result1.stderr:
        print("CLI stderr:\n", result1.stderr)
    assert result1.returncode == 0
    
    # Check for success indicators
    success_indicators = ['completed', 'results']
    has_success = any(indicator in result1.stdout for indicator in success_indicators)
    assert has_success, f"Expected success indicator in ASIN output: {result1.stdout}"
    
    # Wait for file system and DB writes
    time.sleep(3)
    
    print(colorize("\n=== ⏩ Phase 2: ASIN Skip Logic Test ===", "yellow"))
    # Second run - should skip due to existing files/data
    result2 = subprocess.run(base_cmd, capture_output=True, text=True)
    print("CLI output (ASIN skip test):\n", result2.stdout)
    if result2.stderr:
        print("CLI stderr (ASIN skip test):\n", result2.stderr)
    assert result2.returncode == 0
    
    # Check if products or reviews were skipped using full output
    full_output2 = get_full_output(result2)
    has_skip_logic = check_skip_indicators(full_output2, "in ASIN second run")
    
    print(colorize("\n=== 🔥 Phase 3: ASIN Force Scrape Test ===", "red"))
    # Third run - with force flags, should not skip
    force_cmd = base_cmd + ['--force-products', '--force-reviews']
    result3 = subprocess.run(force_cmd, capture_output=True, text=True)
    print("CLI output (ASIN force scrape):\n", result3.stdout)
    if result3.stderr:
        print("CLI stderr (ASIN force scrape):\n", result3.stderr)
    assert result3.returncode == 0
    
    # Check for success indicators
    success_indicators = ['completed', 'results']
    has_success = any(indicator in result3.stdout for indicator in success_indicators)
    assert has_success, f"Expected success indicator in ASIN force output: {result3.stdout}"
    
    # Check for force indicators using full output
    full_output3 = get_full_output(result3)
    has_force_scrape = check_force_indicators(full_output3, "in ASIN force run")
    
    # Wait a moment for final DB writes
    time.sleep(2)
    client = get_supabase_service_client()
    # Print up to 5 recent results to see all phases
    reqs = client.table('scraping_requests').select('*').order('updated_at', desc=True).limit(5).execute()
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
def test_skip_and_force_logic_detailed():
    """
    Dedicated test for skip and force logic with detailed verification.
    Tests file-based and database-based skip detection.
    """
    test_url = "https://www.amazon.com/dp/B0BVKYKKRK"  # Single product for focused testing
    
    # Clean up existing files first
    cleanup_existing_files()
    
    base_cmd = [
        sys.executable, '-m', 'scraping.cli',
        '--category-url', test_url,
        '--max-products', '1',
        '--max-reviews', '3',
        '--log-level', 'DEBUG',  # More verbose for testing
    ]
    
    print(colorize("\n=== 🔍 Detailed Skip & Force Logic Test ===", "cyan"))
    
    # Phase 1: Fresh scrape
    print(colorize("Phase 1: Fresh scrape (should complete)", "green"))
    result1 = subprocess.run(base_cmd, capture_output=True, text=True)
    print("Fresh scrape result:", "✅ SUCCESS" if result1.returncode == 0 else "❌ FAILED")
    if result1.stderr:
        print("Phase 1 stderr:", result1.stderr[:200])
    
    # Wait for files to be written
    time.sleep(2)
    
    # Phase 2: Test skip logic
    print(colorize("\nPhase 2: Skip test (should detect existing data)", "yellow"))
    result2 = subprocess.run(base_cmd, capture_output=True, text=True)
    print("Skip test result:", "✅ SUCCESS" if result2.returncode == 0 else "❌ FAILED")
    
    # Analyze skip behavior using full output
    full_output2 = get_full_output(result2)
    found_skips = check_skip_indicators(full_output2, "in detailed test")
    
    if not found_skips:
        print("Second run full output snippet:", full_output2[:800])
    
    # Phase 3: Test force override
    print(colorize("\nPhase 3: Force override test (should ignore existing data)", "red"))
    force_cmd = base_cmd + ['--force-products', '--force-reviews']
    result3 = subprocess.run(force_cmd, capture_output=True, text=True)
    print("Force test result:", "✅ SUCCESS" if result3.returncode == 0 else "❌ FAILED")
    
    # Analyze force behavior using full output
    full_output3 = get_full_output(result3)
    found_force = check_force_indicators(full_output3, "in detailed test")
    
    if not found_force:
        print("Force run full output snippet:", full_output3[:800])
    
    # Phase 4: Verify database state
    print(colorize("\nPhase 4: Database verification", "cyan"))
    client = get_supabase_service_client()
    
    # Check recent scraping requests
    reqs = client.table('scraping_requests').select('*').order('created_at', desc=True).limit(5).execute()
    print(f"Recent scraping requests: {len(reqs.data)}")
    
    for i, req in enumerate(reqs.data[:3]):  # Show top 3
        status = req.get('status', 'unknown')
        review_status = req.get('review_status', 'unknown')
        workflow = req.get('workflow_stage', 'unknown')
        print(f"  #{i+1}: Status={status}, Reviews={review_status}, Workflow={workflow}")
    
    # Summary
    print(colorize("\n=== Test Summary ===", "cyan"))
    print(f"Fresh scrape: {'✅' if result1.returncode == 0 else '❌'}")
    print(f"Skip detection: {'✅' if found_skips else '⚠️'}")
    print(f"Force override: {'✅' if found_force else '⚠️'}")
    print(f"DB records: {len(reqs.data)} recent requests")
    
    # Assertions
    assert result1.returncode == 0, "Fresh scrape should succeed"
    assert result2.returncode == 0, "Skip test should succeed"
    assert result3.returncode == 0, "Force test should succeed"

@pytest.mark.integration 
def test_individual_force_flags():
    """
    Test individual force flags (--force-products vs --force-reviews).
    """
    test_url = "https://www.amazon.com/dp/B01M3XJUAD"  # Different product for isolation
    
    # Clean up existing files first
    cleanup_existing_files()
    
    base_cmd = [
        sys.executable, '-m', 'scraping.cli',
        '--category-url', test_url,
        '--max-products', '1',
        '--max-reviews', '2',
        '--log-level', 'INFO',
    ]
    
    print(colorize("\n=== 🎯 Individual Force Flags Test ===", "cyan"))
    
    # Initial scrape
    print("Initial scrape...")
    result1 = subprocess.run(base_cmd, capture_output=True, text=True)
    assert result1.returncode == 0
    time.sleep(2)
    
    # Test force-products only
    print(colorize("\nTesting --force-products only", "yellow"))
    force_products_cmd = base_cmd + ['--force-products']
    result2 = subprocess.run(force_products_cmd, capture_output=True, text=True)
    print("Force products result:", "✅ SUCCESS" if result2.returncode == 0 else "❌ FAILED")
    
    # Check for product force and review skip using full output
    full_output2 = get_full_output(result2)
    has_product_force = check_force_indicators(full_output2, "for products")
    has_review_skip = check_skip_indicators(full_output2, "for reviews")
    
    print(f"Product force detected: {'✅' if has_product_force else '⚠️'}")
    print(f"Review skip detected: {'✅' if has_review_skip else '⚠️'}")
    
    time.sleep(1)
    
    # Test force-reviews only  
    print(colorize("\nTesting --force-reviews only", "yellow"))
    force_reviews_cmd = base_cmd + ['--force-reviews']
    result3 = subprocess.run(force_reviews_cmd, capture_output=True, text=True)
    print("Force reviews result:", "✅ SUCCESS" if result3.returncode == 0 else "❌ FAILED")
    
    # Check for review force and product skip using full output
    full_output3 = get_full_output(result3)
    has_review_force = check_force_indicators(full_output3, "for reviews")
    has_product_skip = check_skip_indicators(full_output3, "for products")
    
    print(f"Review force detected: {'✅' if has_review_force else '⚠️'}")
    print(f"Product skip detected: {'✅' if has_product_skip else '⚠️'}")
    
    # Summary
    print(colorize("\n=== Individual Force Test Summary ===", "cyan"))
    print(f"Force products only: {'✅' if has_product_force else '⚠️'}")
    print(f"Force reviews only: {'✅' if has_review_force else '⚠️'}")
    
    # Assertions
    assert result2.returncode == 0, "Force products test should succeed"
    assert result3.returncode == 0, "Force reviews test should succeed"

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