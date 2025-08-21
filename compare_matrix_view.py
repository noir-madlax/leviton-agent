#!/usr/bin/env python3
"""
Script to compare matrix view API responses with different options.

This script compares the response from the competitor analysis matrix view API
with empty options vs. specific sorting and filtering options.
"""

import requests
import json
import sys
from typing import Dict, Any, List
from datetime import datetime


# API Configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/dashboard/charts/competitor-analysis/matrix-view"

# Request data
PROJECT_ID = "d2c02b80-4c82-44cc-8093-56708a7883f7"
SELECTED_ASINS = [
    "B00NG0ELL0",
    "B0BVKZLT3B",
    "B0BVKYKKRK",
    "B0BSHKS26L",
    "B085D8M2MR",
    "B01EZV35QU"
]

# Request payloads
REQUEST_1 = {
    "project_id": PROJECT_ID,
    "selected_asins": SELECTED_ASINS,
    "aspect_type": "phy_perf",
    "options": {}
}

REQUEST_2 = {
    "project_id": PROJECT_ID,
    "selected_asins": SELECTED_ASINS,
    "aspect_type": "phy_perf",
    "options": {
        "sort_by": "mentions",
        "sort_direction": "desc",
        "max_categories": 10
    }
}


def make_api_request(payload: Dict[str, Any], request_name: str) -> Dict[str, Any]:
    """Make API request and return response."""
    try:
        print(f"\n{'='*60}")
        print(f"Making {request_name}...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"{'='*60}")
        
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            headers={
                'accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {}


def compare_aspect_categories(categories_1: List[Dict], categories_2: List[Dict]) -> None:
    """Compare aspect categories between two responses."""
    print(f"\n{'='*60}")
    print("ASPECT CATEGORIES COMPARISON")
    print(f"{'='*60}")
    
    print(f"\nRequest 1 (empty options): {len(categories_1)} categories")
    print(f"Request 2 (with options): {len(categories_2)} categories")
    
    # Compare category names and order
    names_1 = [cat['category_name'] for cat in categories_1]
    names_2 = [cat['category_name'] for cat in categories_2]
    
    print(f"\nCategory names in Request 1: {names_1}")
    print(f"Category names in Request 2: {names_2}")
    
    # Check if order is different
    if names_1 != names_2:
        print("\n⚠️  Category order is different!")
        
        # Find categories that are in different positions
        for i, (name_1, name_2) in enumerate(zip(names_1, names_2)):
            if name_1 != name_2:
                print(f"  Position {i}: '{name_1}' vs '{name_2}'")
        
        # Check if any categories are missing
        missing_in_2 = set(names_1) - set(names_2)
        missing_in_1 = set(names_2) - set(names_1)
        
        if missing_in_2:
            print(f"\nCategories missing in Request 2: {list(missing_in_2)}")
        if missing_in_1:
            print(f"Categories missing in Request 1: {list(missing_in_1)}")
    else:
        print("\n✅ Category order is the same")
    
    # Compare metrics for each category
    print(f"\n{'='*60}")
    print("DETAILED METRICS COMPARISON")
    print(f"{'='*60}")
    
    # Create lookup for categories by name
    cat_lookup_1 = {cat['category_name']: cat for cat in categories_1}
    cat_lookup_2 = {cat['category_name']: cat for cat in categories_2}
    
    all_categories = set(cat_lookup_1.keys()) | set(cat_lookup_2.keys())
    
    for cat_name in sorted(all_categories):
        cat_1 = cat_lookup_1.get(cat_name)
        cat_2 = cat_lookup_2.get(cat_name)
        
        print(f"\nCategory: {cat_name}")
        print("-" * 40)
        
        if cat_1 and cat_2:
            # Compare metrics
            metrics_diff = False
            for metric in ['mentions', 'reviews']:
                val_1 = cat_1.get(metric, 0)
                val_2 = cat_2.get(metric, 0)
                if val_1 != val_2:
                    print(f"  {metric}: {val_1} vs {val_2} (diff: {val_2 - val_1})")
                    metrics_diff = True
                else:
                    print(f"  {metric}: {val_1} (same)")
            
            # Compare sentiment counts
            sent_1 = cat_1.get('sentiment_counts', {})
            sent_2 = cat_2.get('sentiment_counts', {})
            for sentiment in ['positive', 'negative', 'neutral']:
                val_1 = sent_1.get(sentiment, 0)
                val_2 = sent_2.get(sentiment, 0)
                if val_1 != val_2:
                    print(f"  {sentiment}: {val_1} vs {val_2} (diff: {val_2 - val_1})")
                    metrics_diff = True
                else:
                    print(f"  {sentiment}: {val_1} (same)")
            
            if not metrics_diff:
                print("  ✅ All metrics are identical")
                
        elif cat_1:
            print(f"  ❌ Only in Request 1: mentions={cat_1.get('mentions')}, reviews={cat_1.get('reviews')}")
        elif cat_2:
            print(f"  ❌ Only in Request 2: mentions={cat_2.get('mentions')}, reviews={cat_2.get('reviews')}")


def compare_product_aspect_data(data_1: List[Dict], data_2: List[Dict]) -> None:
    """Compare product aspect data between two responses."""
    print(f"\n{'='*60}")
    print("PRODUCT ASPECT DATA COMPARISON")
    print(f"{'='*60}")
    
    print(f"\nRequest 1 (empty options): {len(data_1)} products")
    print(f"Request 2 (with options): {len(data_2)} products")
    
    # Create lookup by ASIN
    data_lookup_1 = {item['asin']: item for item in data_1}
    data_lookup_2 = {item['asin']: item for item in data_2}
    
    all_asins = set(data_lookup_1.keys()) | set(data_lookup_2.keys())
    
    for asin in sorted(all_asins):
        product_1 = data_lookup_1.get(asin)
        product_2 = data_lookup_2.get(asin)
        
        print(f"\nProduct: {asin}")
        print("-" * 30)
        
        if product_1 and product_2:
            aspect_data_1 = product_1.get('aspect_data', [])
            aspect_data_2 = product_2.get('aspect_data', [])
            
            print(f"  Aspect data count: {len(aspect_data_1)} vs {len(aspect_data_2)}")
            
            # Compare aspect data
            aspect_lookup_1 = {item['category_pk']: item for item in aspect_data_1}
            aspect_lookup_2 = {item['category_pk']: item for item in aspect_data_2}
            
            all_categories = set(aspect_lookup_1.keys()) | set(aspect_lookup_2.keys())
            
            for category_pk in sorted(all_categories):
                aspect_1 = aspect_lookup_1.get(category_pk)
                aspect_2 = aspect_lookup_2.get(category_pk)
                
                if aspect_1 and aspect_2:
                    # Compare metrics
                    mentions_1 = aspect_1.get('mentions', 0)
                    mentions_2 = aspect_2.get('mentions', 0)
                    reviews_1 = aspect_1.get('reviews', 0)
                    reviews_2 = aspect_2.get('reviews', 0)
                    
                    if mentions_1 != mentions_2 or reviews_1 != reviews_2:
                        print(f"    Category {category_pk}: mentions {mentions_1} vs {mentions_2}, reviews {reviews_1} vs {reviews_2}")
                    else:
                        print(f"    Category {category_pk}: ✅ identical")
                        
                elif aspect_1:
                    print(f"    Category {category_pk}: ❌ Only in Request 1")
                elif aspect_2:
                    print(f"    Category {category_pk}: ❌ Only in Request 2")
                    
        elif product_1:
            print(f"  ❌ Only in Request 1")
        elif product_2:
            print(f"  ❌ Only in Request 2")


def save_responses(response_1: Dict[str, Any], response_2: Dict[str, Any]) -> None:
    """Save responses to files for further analysis."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename_1 = f"matrix_view_response_1_{timestamp}.json"
    filename_2 = f"matrix_view_response_2_{timestamp}.json"
    
    with open(filename_1, 'w') as f:
        json.dump(response_1, f, indent=2)
    
    with open(filename_2, 'w') as f:
        json.dump(response_2, f, indent=2)
    
    print(f"\n{'='*60}")
    print("RESPONSES SAVED")
    print(f"{'='*60}")
    print(f"Request 1 response: {filename_1}")
    print(f"Request 2 response: {filename_2}")


def main():
    """Main function to run the comparison."""
    print("Matrix View API Comparison Script")
    print("=" * 60)
    print(f"Comparing responses for project: {PROJECT_ID}")
    print(f"ASINs: {', '.join(SELECTED_ASINS)}")
    
    # Make API requests
    response_1 = make_api_request(REQUEST_1, "Request 1 (empty options)")
    response_2 = make_api_request(REQUEST_2, "Request 2 (with sorting options)")
    
    if not response_1 or not response_2:
        print("\n❌ Failed to get responses from API")
        sys.exit(1)
    
    # Save responses
    save_responses(response_1, response_2)
    
    # Compare responses
    print(f"\n{'='*60}")
    print("RESPONSE SUMMARY")
    print(f"{'='*60}")
    
    # Basic response comparison
    total_categories_1 = response_1.get('total_categories', 0)
    total_categories_2 = response_2.get('total_categories', 0)
    total_products_1 = len(response_1.get('product_aspect_data', []))
    total_products_2 = len(response_2.get('product_aspect_data', []))
    
    print(f"Total categories: {total_categories_1} vs {total_categories_2}")
    print(f"Total products: {total_products_1} vs {total_products_2}")
    
    # Detailed comparisons
    compare_aspect_categories(
        response_1.get('aspect_categories', []),
        response_2.get('aspect_categories', [])
    )
    
    compare_product_aspect_data(
        response_1.get('product_aspect_data', []),
        response_2.get('product_aspect_data', [])
    )
    
    print(f"\n{'='*60}")
    print("COMPARISON COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main() 