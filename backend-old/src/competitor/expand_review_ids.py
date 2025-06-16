#!/usr/bin/env python3
"""
Review ID Expansion Script

Convert review IDs in consolidated_review_results.json back to actual review text.
This script takes the hierarchical review analysis and expands all the review ID 
references to include the actual review content for better readability and analysis.

Input: consolidated_review_results.json with review ID references
Output: expanded_review_results.json with actual review text included
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
    """
    Load the original review file for a given ASIN
    
    Args:
        asin: Product ASIN
    
    Returns:
        Dictionary containing review data or empty dict if not found
    """
    # Look for review file with the expected naming pattern
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
    """
    Create a mapping from review ID (position index) to review data.
    This replicates the exact logic from process_reviews.py to ensure correct mapping.
    
    Args:
        reviews: List of review dictionaries from the original file
    
    Returns:
        Dictionary mapping review ID to review data
    """
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

def expand_review_ids_in_section(section_data: Any, review_mapping: Dict[int, Dict[str, Any]]) -> Any:
    """
    Recursively expand review IDs to include actual review text
    
    Args:
        section_data: Section of the hierarchy (could be dict, list, or primitive)
        review_mapping: Mapping from review ID to review data
    
    Returns:
        Expanded section with review text included
    """
    if isinstance(section_data, dict):
        expanded_dict = {}
        for key, value in section_data.items():
            if key in ['+', '-'] and isinstance(value, list):
                # This is a sentiment section with review IDs
                expanded_reviews = []
                for review_id in value:
                    if isinstance(review_id, int) and review_id in review_mapping:
                        review_data = review_mapping[review_id]
                        expanded_reviews.append({
                            'review_id': review_id,
                            'review_text': review_data['text'],
                            'review_title': review_data['title'],
                            'rating': review_data['rating'],
                            'date': review_data['date'],
                            'verified': review_data['verified'],
                            'userName': review_data['userName'],
                            'numberOfHelpful': review_data['numberOfHelpful']
                        })
                    else:
                        # Keep original if review not found
                        expanded_reviews.append({'review_id': review_id, 'review_text': '[Review not found]'})
                expanded_dict[key] = expanded_reviews
            else:
                # Recursively process other parts
                expanded_dict[key] = expand_review_ids_in_section(value, review_mapping)
        return expanded_dict
    
    elif isinstance(section_data, list):
        return [expand_review_ids_in_section(item, review_mapping) for item in section_data]
    
    else:
        # Primitive value, return as-is
        return section_data

def expand_performance_section(perf_data: Dict[str, Any], review_mapping: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Expand performance section which has nested reason structures
    
    Args:
        perf_data: Performance section from review hierarchy
        review_mapping: Mapping from review ID to review data
    
    Returns:
        Expanded performance section
    """
    expanded_perf = {}
    
    for perf_category, details in perf_data.items():
        expanded_details = {}
        
        for perf_id_detail, sentiments in details.items():
            expanded_sentiments = {}
            
            for sentiment, reasons in sentiments.items():
                expanded_reasons = {}
                
                for reason, review_ids in reasons.items():
                    # Expand the review IDs for this reason
                    expanded_review_ids = []
                    for review_id in review_ids:
                        if isinstance(review_id, int) and review_id in review_mapping:
                            review_data = review_mapping[review_id]
                            expanded_review_ids.append({
                                'review_id': review_id,
                                'review_text': review_data['text'],
                                'review_title': review_data['title'],
                                'rating': review_data['rating'],
                                'date': review_data['date'],
                                'verified': review_data['verified'],
                                'userName': review_data['userName'],
                                'numberOfHelpful': review_data['numberOfHelpful']
                            })
                        else:
                            expanded_review_ids.append({'review_id': review_id, 'review_text': '[Review not found]'})
                    
                    expanded_reasons[reason] = expanded_review_ids
                
                expanded_sentiments[sentiment] = expanded_reasons
            
            expanded_details[perf_id_detail] = expanded_sentiments
        
        expanded_perf[perf_category] = expanded_details
    
    return expanded_perf

def expand_use_section(use_data: Dict[str, Any], review_mapping: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Expand use case section which has reason structures similar to performance
    
    Args:
        use_data: Use case section from review hierarchy
        review_mapping: Mapping from review ID to review data
    
    Returns:
        Expanded use case section
    """
    expanded_use = {}
    
    for use_case, sentiments in use_data.items():
        expanded_sentiments = {}
        
        for sentiment, reasons in sentiments.items():
            expanded_reasons = {}
            
            for reason, review_ids in reasons.items():
                # Expand the review IDs for this reason
                expanded_review_ids = []
                for review_id in review_ids:
                    if isinstance(review_id, int) and review_id in review_mapping:
                        review_data = review_mapping[review_id]
                        expanded_review_ids.append({
                            'review_id': review_id,
                            'review_text': review_data['text'],
                            'review_title': review_data['title'],
                            'rating': review_data['rating'],
                            'date': review_data['date'],
                            'verified': review_data['verified'],
                            'userName': review_data['userName'],
                            'numberOfHelpful': review_data['numberOfHelpful']
                        })
                    else:
                        expanded_review_ids.append({'review_id': review_id, 'review_text': '[Review not found]'})
                
                expanded_reasons[reason] = expanded_review_ids
            
            expanded_sentiments[sentiment] = expanded_reasons
        
        expanded_use[use_case] = expanded_sentiments
    
    return expanded_use

def expand_product_reviews(asin: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expand all review IDs for a single product
    
    Args:
        asin: Product ASIN
        product_data: Product data from consolidated results
    
    Returns:
        Expanded product data with review text included
    """
    print(f"Expanding reviews for {asin}...")
    
    # Load original review file
    review_file_data = load_review_file(asin)
    if not review_file_data:
        print(f"⚠️ Could not load reviews for {asin}, skipping expansion")
        return product_data
    
    # Create review mapping
    review_mapping = create_review_mapping(review_file_data['reviews'])
    
    # Validate against expected total_reviews
    expected_total = product_data.get('total_reviews', 0)
    if len(review_mapping) != expected_total:
        print(f"⚠️ Review count mismatch for {asin}: expected {expected_total}, got {len(review_mapping)}")
        print(f"   This may indicate the review file has changed since analysis was done")
    
    print(f"   Loaded {len(review_mapping)} reviews for {asin} (expected: {expected_total})")
    
    # Get the review analysis section
    review_analysis = product_data.get('review_analysis', {})
    if not review_analysis:
        print(f"⚠️ No review analysis found for {asin}")
        return product_data
    
    # Expand each section
    expanded_analysis = {}
    
    # Expand physical aspects (simple sentiment structure)
    if 'phy' in review_analysis:
        expanded_analysis['phy'] = expand_review_ids_in_section(review_analysis['phy'], review_mapping)
    
    # Expand performance aspects (nested reason structure)
    if 'perf' in review_analysis:
        expanded_analysis['perf'] = expand_performance_section(review_analysis['perf'], review_mapping)
    
    # Expand use case aspects (nested reason structure)
    if 'use' in review_analysis:
        expanded_analysis['use'] = expand_use_section(review_analysis['use'], review_mapping)
    
    # Create expanded product data
    expanded_product_data = product_data.copy()
    expanded_product_data['review_analysis'] = expanded_analysis
    expanded_product_data['review_statistics'] = {
        'total_reviews_in_file': len(review_file_data['reviews']),
        'valid_reviews_mapped': len(review_mapping),
        'reviews_referenced_in_analysis': len(set(
            id for section in expanded_analysis.values()
            for category in section.values()
            for detail in category.values() if isinstance(detail, dict)
            for sentiment in detail.values() if isinstance(sentiment, (list, dict))
            for item in (sentiment if isinstance(sentiment, list) else sentiment.values() if isinstance(sentiment, dict) else [])
            for entry in (item if isinstance(item, list) else [item])
            for id in ([entry.get('review_id')] if isinstance(entry, dict) and 'review_id' in entry else [])
            if isinstance(id, int)
        ))
    }
    
    print(f"✓ Expanded {asin}: {expanded_product_data['review_statistics']['reviews_referenced_in_analysis']} unique reviews referenced")
    return expanded_product_data

def main():
    """Main execution function"""
    print("Starting review ID expansion...")
    
    # Load consolidated results
    if not CONSOLIDATED_RESULTS_PATH.exists():
        print(f"❌ Consolidated results file not found at {CONSOLIDATED_RESULTS_PATH}")
        return
    
    try:
        with open(CONSOLIDATED_RESULTS_PATH, 'r', encoding='utf-8') as f:
            consolidated_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading consolidated results: {e}")
        return
    
    results = consolidated_data.get('results', {})
    if not results:
        print("❌ No results found in consolidated data")
        return
    
    print(f"Processing {len(results)} products...")
    
    # Expand reviews for each product
    expanded_results = {}
    success_count = 0
    
    for asin, product_data in results.items():
        try:
            expanded_product_data = expand_product_reviews(asin, product_data)
            expanded_results[asin] = expanded_product_data
            success_count += 1
        except Exception as e:
            print(f"❌ Error expanding {asin}: {e}")
            # Keep original data if expansion fails
            expanded_results[asin] = product_data
    
    # Create expanded consolidated data
    expanded_consolidated_data = {
        'processing_summary': consolidated_data.get('processing_summary', {}),
        'expansion_info': {
            'expansion_date': datetime.now().isoformat(),
            'products_expanded': success_count,
            'products_attempted': len(results),
            'expansion_script': 'expand_review_ids.py'
        },
        'results': expanded_results
    }
    
    # Save expanded results
    output_path = config.get_file_path("expanded_review_results.json")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(expanded_consolidated_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Review expansion complete!")
        print(f"✓ Successfully expanded {success_count}/{len(results)} products")
        print(f"✓ Expanded results saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error saving expanded results: {e}")

if __name__ == "__main__":
    main() 