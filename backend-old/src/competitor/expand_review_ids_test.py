#!/usr/bin/env python3
"""
Test version of Review ID Expansion Script

Test the expansion on just one ASIN to verify the mapping is correct.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import utility modules
from utils.config import get_process_review_config

# === CONFIGURATION ===
config = get_process_review_config()

# Data paths
REVIEW_DATA_DIR = config.get_data_path("scraped", "amazon", "review")
CONSOLIDATED_RESULTS_PATH = config.get_data_path("result", "process_review", "20250609_01", "consolidated_review_results.json")

def load_review_file(asin: str) -> Dict[str, Any]:
    """Load the original review file for a given ASIN"""
    review_files = list(REVIEW_DATA_DIR.glob(f"{asin}_*_reviews.json"))
    
    if not review_files:
        print(f"⚠️ No review file found for ASIN {asin}")
        return {}
    
    try:
        with open(review_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        reviews = data.get('reviews_data', {}).get('reviews', [])
        return {'reviews': reviews, 'product_context': data.get('product_context', {})}
        
    except Exception as e:
        print(f"❌ Error loading review file for {asin}: {e}")
        return {}

def create_review_mapping(reviews: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Create review mapping exactly like process_reviews.py"""
    review_mapping = {}
    
    # First, create valid_reviews list exactly like process_reviews.py does
    valid_reviews = []
    for i, review in enumerate(reviews):
        review_text = review.get('text', '').strip()
        if review_text and len(review_text) > 10:  # Same validation as in process_reviews.py
            valid_reviews.append({
                'id': i,  # Original position in raw reviews
                'text': review_text,
                'title': review.get('title', ''),
                'rating': review.get('rating', ''),
                'date': review.get('date', ''),
                'verified': review.get('verified', False),
                'userName': review.get('userName', ''),
                'numberOfHelpful': review.get('numberOfHelpful', 0)
            })
    
    # Now map review IDs (positions in valid_reviews) to review data
    for idx, review in enumerate(valid_reviews):
        review_mapping[idx] = review  # idx is the review ID used in analysis
    
    return review_mapping

def test_review_mapping(test_asin: str = "B08PKMT2DV"):
    """Test the review mapping for a specific ASIN"""
    print(f"Testing review mapping for {test_asin}...")
    
    # Load consolidated results
    try:
        with open(CONSOLIDATED_RESULTS_PATH, 'r', encoding='utf-8') as f:
            consolidated_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading consolidated results: {e}")
        return
    
    results = consolidated_data.get('results', {})
    if test_asin not in results:
        print(f"❌ {test_asin} not found in consolidated results")
        return
    
    product_data = results[test_asin]
    
    # Load original review file
    review_file_data = load_review_file(test_asin)
    if not review_file_data:
        print(f"❌ Could not load reviews for {test_asin}")
        return
    
    # Create review mapping
    review_mapping = create_review_mapping(review_file_data['reviews'])
    
    # Check counts
    expected_total = product_data.get('total_reviews', 0)
    print(f"Expected total reviews: {expected_total}")
    print(f"Mapped reviews: {len(review_mapping)}")
    print(f"Raw reviews in file: {len(review_file_data['reviews'])}")
    
    if len(review_mapping) != expected_total:
        print(f"❌ Count mismatch!")
        return
    else:
        print(f"✓ Review counts match")
    
    # Test some specific mappings from the analysis
    review_analysis = product_data.get('review_analysis', {})
    
    # Get some review IDs from the analysis to test
    test_ids = set()
    if 'phy' in review_analysis:
        for category in review_analysis['phy'].values():
            for detail in category.values():
                for sentiment in detail.values():
                    if isinstance(sentiment, list):
                        test_ids.update(sentiment)
    
    print(f"\nTesting some review ID mappings...")
    for review_id in sorted(list(test_ids)[:5]):  # Test first 5 IDs
        if review_id in review_mapping:
            review_data = review_mapping[review_id]
            print(f"Review ID {review_id}:")
            print(f"  Title: '{review_data['title'][:60]}...' " if len(review_data['title']) > 60 else f"  Title: '{review_data['title']}'")
            print(f"  Text preview: '{review_data['text'][:100]}...'")
            print(f"  Rating: {review_data['rating']}")
            print(f"  Original position in file: {review_data['id']}")
            print()
        else:
            print(f"❌ Review ID {review_id} not found in mapping!")
    
    print("✓ Test completed")

if __name__ == "__main__":
    test_review_mapping() 