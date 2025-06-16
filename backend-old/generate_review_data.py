#!/usr/bin/env python3
"""
Script to generate review data from consolidated_aspect_categorization.json and scraped reviews
Creates mappings between review categories and actual review texts for frontend clicking functionality
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Set
import glob
import re
import random
from datetime import datetime

# Configuration
CURRENT_DIR = Path(__file__).parent
BACKEND_DATA_DIR = CURRENT_DIR / "data/result/process_review/20250609_05"
SCRAPED_REVIEWS_DIR = CURRENT_DIR / "data/scraped/amazon/review"
PRODUCT_CSV_PATH = CURRENT_DIR / "data/result/product_segment/combined_products_cleaned/combined_products_with_final_categories.csv"
CONSOLIDATED_FILE = "consolidated_aspect_categorization.json"
OUTPUT_FILE = CURRENT_DIR.parent / "frontend/lib/reviewData.ts"

def load_consolidated_categorization() -> Dict:
    """Load consolidated aspect categorization data"""
    consolidated_path = BACKEND_DATA_DIR / CONSOLIDATED_FILE
    
    if not consolidated_path.exists():
        raise FileNotFoundError(f"Consolidated categorization file not found: {consolidated_path}")
    
    with open(consolidated_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_actual_chart_categories() -> Set[str]:
    """
    Extract all actual category names from consolidated_aspect_categorization.json
    These are the category names that will be used in the charts.
    """
    consolidated_path = BACKEND_DATA_DIR / CONSOLIDATED_FILE
    
    if not consolidated_path.exists():
        raise FileNotFoundError(f"Consolidated data file not found: {consolidated_path}")
    
    with open(consolidated_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    categories = set()
    
    # Extract all category names from the actual data structure
    for product_id, product_data in data.get('results', {}).items():
        aspect_categorization = product_data.get('aspect_categorization', {})
        
        # Process phy, perf, and use sections
        for section_type in ['phy', 'perf', 'use']:
            if section_type not in aspect_categorization:
                continue
                
            section_data = aspect_categorization[section_type]
            
            if section_type == 'use':
                # Use section: direct mapping use_case -> category_name
                for use_case, category_name in section_data.items():
                    if category_name != "OUT_OF_SCOPE":
                        categories.add(category_name)
            else:
                # Phy and perf sections: nested structure
                for aspect_group_name, aspect_mappings in section_data.items():
                    if isinstance(aspect_mappings, dict):
                        for aspect_key, category_name in aspect_mappings.items():
                            if category_name != "OUT_OF_SCOPE":
                                categories.add(category_name)
    
    print(f"Found {len(categories)} unique categories in the data:")
    for i, category in enumerate(sorted(categories), 1):
        print(f"  {i:2d}. {category}")
    
    return categories

def create_category_to_review_mapping(actual_categories: Set[str]) -> Dict[str, str]:
    """
    Create direct mapping - use actual category names as both keys and values
    No artificial mapping needed since we want to use the actual names
    """
    # Direct mapping - category names map to themselves
    category_mapping = {category: category for category in actual_categories}
    
    print(f"\nUsing direct category mapping (no transformation needed):")
    for category in sorted(actual_categories):
        print(f"  {category} -> {category}")
    
    return category_mapping

def load_expanded_review_results() -> Dict:
    """Load expanded review results with detailed review analysis"""
    expanded_path = BACKEND_DATA_DIR / "expanded_review_results.json"
    
    if not expanded_path.exists():
        raise FileNotFoundError(f"Expanded review results file not found: {expanded_path}")
    
    with open(expanded_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_reviews_by_category(consolidated_data: Dict, expanded_reviews: Dict, category_mapping: Dict[str, str], product_info: Dict[str, Dict[str, str]]) -> Dict[str, List[Dict]]:
    """
    Extract reviews by category from consolidated and expanded data
    
    Args:
        consolidated_data: Consolidated aspect categorization data
        expanded_reviews: Expanded review results with detailed analysis
        category_mapping: Direct mapping (category names map to themselves)
    
    Returns:
        Dictionary mapping category names to lists of review data
    """
    reviews_by_category = {}
    
    # Initialize all categories (they map to themselves)
    for category in category_mapping.keys():
        reviews_by_category[category] = []
    
    print(f"Processing {len(consolidated_data.get('results', {}))} products...")
    
    # Process each product
    for product_id, product_data in consolidated_data.get('results', {}).items():
        if product_id not in expanded_reviews.get('results', {}):
            continue
            
        expanded_product = expanded_reviews['results'][product_id]
        aspect_categorization = product_data.get('aspect_categorization', {})
        review_analysis = expanded_product.get('review_analysis', {})
        
        # Get product info from CSV
        product_data_csv = product_info.get(product_id, {})
        product_title = product_data_csv.get('title', expanded_product.get('product_title', 'Unknown Product'))
        brand = product_data_csv.get('brand', 'Unknown')
        
        # Process phy, perf, and use sections
        for section_type in ['phy', 'perf', 'use']:
            if section_type not in aspect_categorization or section_type not in review_analysis:
                continue
                
            section_categorization = aspect_categorization[section_type]
            section_reviews = review_analysis[section_type]
            
            if section_type == 'use':
                # Use section: direct mapping use_case -> category_name
                for use_case, category_name in section_categorization.items():
                    if category_name == "OUT_OF_SCOPE" or category_name not in reviews_by_category:
                        continue
                        
                    # Get review data for this use case
                    if use_case in section_reviews:
                        use_case_reviews = section_reviews[use_case]
                        reviews_by_category[category_name].extend(
                            extract_sentiment_reviews(use_case_reviews, product_id, product_title, brand, category_name)
                        )
            else:
                # Phy and perf sections: nested structure
                for aspect_group_name, aspect_mappings in section_categorization.items():
                    if not isinstance(aspect_mappings, dict):
                        continue
                        
                    for aspect_key, category_name in aspect_mappings.items():
                        if category_name == "OUT_OF_SCOPE" or category_name not in reviews_by_category:
                            continue
                            
                        # Get review data for this aspect
                        if aspect_group_name in section_reviews and aspect_key in section_reviews[aspect_group_name]:
                            aspect_reviews = section_reviews[aspect_group_name][aspect_key]
                            reviews_by_category[category_name].extend(
                                extract_sentiment_reviews(aspect_reviews, product_id, product_title, brand, category_name)
                            )
    
    # Print statistics
    print(f"\n📊 Review Categories Statistics:")
    total_reviews = 0
    for category, reviews in sorted(reviews_by_category.items()):
        count = len(reviews)
        total_reviews += count
        print(f"  {category}: {count} reviews")
    
    print(f"\nTotal reviews extracted: {total_reviews}")
    
    return reviews_by_category

def extract_sentiment_reviews(sentiment_data: Dict, product_id: str, product_title: str, brand: str, category: str) -> List[Dict]:
    """Extract reviews from sentiment data structure"""
    reviews = []
    review_counter = 0
    
    for sentiment in ['+', '-']:
        if sentiment not in sentiment_data:
            continue
            
        sentiment_reviews = sentiment_data[sentiment]
        sentiment_label = 'positive' if sentiment == '+' else 'negative'
        
        # Handle different data structures
        review_list = []
        if isinstance(sentiment_reviews, list):
            review_list = sentiment_reviews
        elif isinstance(sentiment_reviews, dict):
            # Flatten nested structure
            for key, value in sentiment_reviews.items():
                if isinstance(value, list):
                    review_list.extend(value)
        
        # Process each review
        for review_item in review_list:
            if not isinstance(review_item, dict):
                continue
                
            review_counter += 1
            review_id = f"{product_id}_{category}_{review_counter}"
            
            # Extract review data
            review_text = review_item.get('review_text', '')
            if len(review_text) > 500:
                review_text = review_text[:500] + "..."
                
            rating_str = review_item.get('rating', '3.0 out of 5 stars')
            rating = extract_rating_value(rating_str)
            
            review_date = review_item.get('date', '')
            verified = review_item.get('verified', False)
            
            reviews.append({
                'id': review_id,
                'text': review_text,
                'rating': rating,
                'sentiment': sentiment_label,
                'verified': verified,
                'date': review_date,
                'productId': product_id,
                'category': category,
                'brand': brand
            })
    
    return reviews

def extract_rating_value(rating_str: str) -> float:
    """Extract numeric rating from rating string"""
    try:
        if isinstance(rating_str, str) and "out of 5 stars" in rating_str:
            return float(rating_str.split()[0])
        elif isinstance(rating_str, (int, float)):
            return float(rating_str)
        return 3.0
    except (ValueError, IndexError):
        return 3.0

def generate_typescript_file(review_data: Dict[str, List[Dict]]):
    """Generate TypeScript file with review data"""
    
    # Calculate statistics
    total_reviews = sum(len(reviews) for reviews in review_data.values())
    categories_with_data = len([cat for cat, reviews in review_data.items() if reviews])
    
    print(f"\n📊 Review Data Statistics:")
    print(f"Total categories: {len(review_data)}")
    print(f"Categories with reviews: {categories_with_data}")
    print(f"Total reviews: {total_reviews}")
    
    print(f"\nReviews per category:")
    for category, reviews in sorted(review_data.items()):
        print(f"  {category}: {len(reviews)} reviews")
    
    # Track used variable names to avoid duplicates
    used_names = set()
    category_to_var_name = {}
    
    # Pre-process all categories to assign unique variable names
    for category in review_data.keys():
        base_name = sanitize_category_name(category)
        var_name = base_name
        counter = 1
        
        # If name is already used, add numeric suffix
        while var_name in used_names:
            var_name = f"{base_name}{counter}"
            counter += 1
        
        used_names.add(var_name)
        category_to_var_name[category] = var_name
    
    # Generate TypeScript content
    ts_content = f'''// Review Data - Generated from consolidated aspect categorization
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Total reviews: {total_reviews} across {categories_with_data} categories

export interface Review {{
  id: string;
  text: string;
  rating: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  verified: boolean;
  date: string;
  productId: string;
  category: string;
  brand: string;
}}

export interface ReviewData {{
  reviews: Review[];
  totalCount: number;
  categories: string[];
  lastUpdated: string;
}}

// Review data by category
'''
    
    # Add individual category exports
    for category, reviews in review_data.items():
        var_name = category_to_var_name[category]
        ts_content += f"\nexport const {var_name}Reviews: Review[] = {json.dumps(reviews, indent=2)};\n"
    
    # Add combined export
    ts_content += f'''
// All review data
export const allReviewData: Record<string, Review[]> = {{
'''
    
    for category, reviews in review_data.items():
        var_name = category_to_var_name[category]
        ts_content += f'  "{category}": {var_name}Reviews,\n'
    
    ts_content += f'''}};

// Utility functions
export function getReviewsByCategory(category: string): Review[] {{
  return allReviewData[category] || [];
}}

export function getAllCategories(): string[] {{
  return Object.keys(allReviewData);
}}

export function getTotalReviewCount(): number {{
  return {total_reviews};
}}

export function getReviewData(): ReviewData {{
  const allReviews = Object.values(allReviewData).flat();
  return {{
    reviews: allReviews,
    totalCount: allReviews.length,
    categories: Object.keys(allReviewData),
    lastUpdated: "{datetime.now().isoformat()}"
  }};
}}

// Get reviews with specific sentiment
export function getReviewsBySentiment(category: string, sentiment: 'positive' | 'negative' | 'neutral'): Review[] {{
  const categoryReviews = getReviewsByCategory(category);
  return categoryReviews.filter(review => review.sentiment === sentiment);
}}

// Search reviews by text
export function searchReviews(query: string, category?: string): Review[] {{
  const reviewsToSearch = category ? getReviewsByCategory(category) : Object.values(allReviewData).flat();
  const lowerQuery = query.toLowerCase();
  return reviewsToSearch.filter(review => 
    review.text.toLowerCase().includes(lowerQuery)
  );
}}
'''
    
    # Write the file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    
    print(f"✅ TypeScript file generated: {OUTPUT_FILE}")
    
    # Report any duplicate names that were resolved
    duplicates_found = [(cat, var) for cat, var in category_to_var_name.items() if var != sanitize_category_name(cat)]
    if duplicates_found:
        print(f"\n⚠️  Resolved {len(duplicates_found)} duplicate variable names:")
        for category, var_name in duplicates_found:
            print(f"  '{category}' -> {var_name}Reviews")

def load_product_info() -> Dict[str, Dict[str, str]]:
    """Load product information including brands from CSV file"""
    try:
        df = pd.read_csv(PRODUCT_CSV_PATH)
        product_info = {}
        
        for _, row in df.iterrows():
            product_id = row.get('platform_id', '')
            brand = row.get('brand', 'Unknown')
            title = row.get('title', 'Unknown Product')
            
            if product_id:
                product_info[product_id] = {
                    'brand': brand,
                    'title': title
                }
        
        print(f"Loaded product info for {len(product_info)} products from CSV")
        return product_info
        
    except Exception as e:
        print(f"Warning: Could not load product CSV: {e}")
        return {}

def sanitize_category_name(category_name: str) -> str:
    """
    Sanitize category name to be a valid TypeScript variable name
    - Remove spaces and special characters
    - Convert to camelCase
    - Ensure it starts with a letter
    """
    import re
    
    # Replace spaces and hyphens with nothing, keep alphanumeric
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', category_name)
    
    # Convert to camelCase by capitalizing first letter of each word
    words = re.findall(r'[A-Z][a-z]*|[a-z]+|[0-9]+', category_name)
    if not words:
        return "UnknownCategory"
    
    # First word lowercase, rest capitalized
    camel_case = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    # Ensure it starts with a letter
    if not camel_case[0].isalpha():
        camel_case = 'category' + camel_case.capitalize()
    
    return camel_case

def main():
    print("Generating review data from consolidated categorization...")
    
    # Load product information from CSV
    product_info = load_product_info()
    
    # Load the consolidated categorization data
    consolidated_data = load_consolidated_categorization()
    
    # Get actual chart categories from the data
    chart_categories = get_actual_chart_categories()
    
    # Create mapping from chart categories to review categories
    category_mapping = create_category_to_review_mapping(chart_categories)
    
    # Load expanded review results
    expanded_reviews = load_expanded_review_results()
    
    # Extract reviews by category
    reviews_by_category = extract_reviews_by_category(consolidated_data, expanded_reviews, category_mapping, product_info)
    
    # Generate TypeScript file
    generate_typescript_file(reviews_by_category)
    
    print(f"\n✅ Review data generated successfully!")
    print(f"✅ Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main() 