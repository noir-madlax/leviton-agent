#!/usr/bin/env python3
"""
Category Feedback Analyzer

Analyze categorized review aspects to generate comprehensive feedback analysis
including category-based pain points, strengths, and use case satisfaction data.

This script reads from the actual generated data files:
- consolidated_aspect_categorization.json (categorized aspects)
- expanded_review_results.json (detailed review analysis)
- aspect_category_definitions.json (category definitions)
"""

import json
import pandas as pd
from typing import Dict, List, Any, Set, Tuple
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# === CONSTANTS ===
# Minimum number of reviews required for statistical significance
MIN_REVIEWS_FOR_STATS = 5

# Product type mapping keywords for classification
PRODUCT_TYPE_KEYWORDS = {
    'dimmer': ['dimmer', 'dimming', 'dimmable', 'brightness control', 'light level'],
    'light': ['switch', 'light switch', 'toggle', 'on/off', 'rocker switch']
}

CURRENT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = CURRENT_DIR / "data/result/process_review/20250609_05"
OUTPUT_PATH = CURRENT_DIR.parent / "frontend/lib/categoryFeedback.ts"
# Data file names
CONSOLIDATED_ASPECT_FILE = "consolidated_aspect_categorization.json"
EXPANDED_REVIEW_FILE = "expanded_review_results.json"
CATEGORY_DEFINITIONS_FILE = "aspect_category_definitions.json"
PRODUCT_MAPPING_FILE = "product_type_mapping.json"

# === DATA STRUCTURES ===
class CategoryFeedbackAnalyzer:
    """
    Analyzes categorized review aspects to generate feedback insights
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize analyzer with data directory
        
        Args:
            data_dir: Directory containing the processed data files
        """
        self.data_dir = Path(data_dir)
        
        # Data storage
        self.consolidated_data = {}
        self.expanded_reviews = {}
        self.category_definitions = {}
        self.product_mapping = {}
        
        # Analysis results
        self.category_stats_by_type = {'dimmer': {}, 'light': {}}
        self.use_case_stats_by_type = {'dimmer': {}, 'light': {}}
        self.summary_stats_by_type = {'dimmer': {}, 'light': {}}
        
    def load_product_mapping(self):
        """Load or generate product type mapping"""
        mapping_path = self.data_dir / PRODUCT_MAPPING_FILE
        
        if mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                self.product_mapping = json.load(f)
            print(f"Loaded product mapping for {len(self.product_mapping)} products")
        else:
            # Generate mapping based on product titles and categories
            print("Generating product type mapping from consolidated data...")
            self.product_mapping = self._generate_product_mapping()
            
            # Save generated mapping
            with open(mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.product_mapping, f, indent=2, ensure_ascii=False)
            print(f"Generated and saved product mapping for {len(self.product_mapping)} products")
    
    def _generate_product_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Generate product type mapping based on product titles and categories
        """
        mapping = {}
        
        # Try to load from CSV first
        try:
            csv_path = self.data_dir.parent.parent / "product_segment" / "combined_products_cleaned" / "combined_products_with_final_categories.csv"
            if csv_path.exists():
                products_df = pd.read_csv(csv_path)
                if 'product_segment' in products_df.columns:
                    for _, row in products_df.iterrows():
                        asin = row['platform_id']
                        title = row.get('title', '')
                        segment = row.get('product_segment', 'light')
                        
                        # Map product segment to our types
                        product_type = 'dimmer' if 'dimmer' in segment.lower() else 'light'
                        
                        mapping[asin] = {
                            'type': product_type,
                            'title': title,
                            'segment': segment
                        }
                    return mapping
        except Exception as e:
            print(f"Could not load from CSV: {e}")
        
        # Fallback: classify based on expanded review data
        if self.expanded_reviews:
            for product_id, product_data in self.expanded_reviews.get('results', {}).items():
                title = product_data.get('product_title', '').lower()
                category = product_data.get('product_category', '').lower()
                
                # Classify based on keywords
                product_type = 'light'  # default
                text_to_check = f"{title} {category}"
                
                for type_name, keywords in PRODUCT_TYPE_KEYWORDS.items():
                    if any(keyword in text_to_check for keyword in keywords):
                        product_type = type_name
                        break
                
                mapping[product_id] = {
                    'type': product_type,
                    'title': product_data.get('product_title', ''),
                    'segment': product_data.get('product_category', '')
                }
        
        return mapping
    
    def load_data(self):
        """Load all required data files"""
        print("Loading data files...")
        
        # Load consolidated aspect categorization
        consolidated_path = self.data_dir / CONSOLIDATED_ASPECT_FILE
        if consolidated_path.exists():
            with open(consolidated_path, 'r', encoding='utf-8') as f:
                self.consolidated_data = json.load(f)
            print(f"Loaded consolidated data for {len(self.consolidated_data.get('results', {}))} products")
        else:
            raise FileNotFoundError(f"Consolidated data not found at {consolidated_path}")
        
        # Load expanded review results
        expanded_path = self.data_dir / EXPANDED_REVIEW_FILE
        if expanded_path.exists():
            with open(expanded_path, 'r', encoding='utf-8') as f:
                self.expanded_reviews = json.load(f)
            print(f"Loaded expanded reviews for {len(self.expanded_reviews.get('results', {}))} products")
        else:
            print("Warning: Expanded review results not found, will use limited data")
        
        # Load category definitions
        definitions_path = self.data_dir / CATEGORY_DEFINITIONS_FILE
        if definitions_path.exists():
            with open(definitions_path, 'r', encoding='utf-8') as f:
                self.category_definitions = json.load(f)
            print("Loaded category definitions")
        else:
            print("Warning: Category definitions not found")
        
        # Load product mapping
        self.load_product_mapping()
    
    def extract_rating_score(self, rating_str: str) -> float:
        """Extract numeric rating from rating string"""
        if not rating_str:
            return 3.0
        
        try:
            # Extract first number from rating string
            import re
            numbers = re.findall(r'\d+\.?\d*', str(rating_str))
            if numbers:
                return float(numbers[0])
        except:
            pass
        
        return 3.0  # Default neutral rating
    
    def analyze_categories(self):
        """Analyze category feedback by product type using actual data"""
        print("Analyzing category feedback by product type...")
        
        for product_id, product_data in self.consolidated_data.get('results', {}).items():
            if product_id not in self.product_mapping:
                continue
            
            product_type = self.product_mapping[product_id]['type']
            aspect_categorization = product_data.get('aspect_categorization', {})
            
            # Get corresponding expanded review data
            expanded_product = self.expanded_reviews.get('results', {}).get(product_id, {})
            review_analysis = expanded_product.get('review_analysis', {})
            
            # Process physical and performance categories
            for section_type in ['phy', 'perf']:
                if section_type not in aspect_categorization:
                    continue
                
                section_data = aspect_categorization[section_type]
                review_section = review_analysis.get(section_type, {})
                
                # Process each aspect group in this section
                for aspect_group_name, aspect_mappings in section_data.items():
                    if not isinstance(aspect_mappings, dict):
                        continue
                    
                    # Get corresponding review data for this aspect group
                    group_reviews = review_section.get(aspect_group_name, {})
                    
                    # Process each aspect mapping
                    for aspect_key, final_category in aspect_mappings.items():
                        if final_category == "OUT_OF_SCOPE":
                            continue
                        
                        # Initialize category stats
                        if final_category not in self.category_stats_by_type[product_type]:
                            self.category_stats_by_type[product_type][final_category] = {
                                'category': final_category,
                                'categoryType': 'Physical' if section_type == 'phy' else 'Performance',
                                'mentions': 0,
                                'positiveCount': 0,
                                'negativeCount': 0,
                                'totalReviews': 0,
                                'satisfactionRate': 0.0,
                                'negativeRate': 0.0,
                                'averageRating': 0.0,
                                'topNegativeAspects': [],
                                'topPositiveAspects': [],
                                'topNegativeReasons': [],
                                'topPositiveReasons': [],
                                'rating_sum': 0,
                                'rating_count': 0
                            }
                        
                        category_stats = self.category_stats_by_type[product_type][final_category]
                        
                        # Get sentiment data for this aspect
                        aspect_reviews = group_reviews.get(aspect_key, {})
                        
                        # Process positive and negative sentiments
                        for sentiment in ['+', '-']:
                            if sentiment not in aspect_reviews:
                                continue
                            
                            sentiment_data = aspect_reviews[sentiment]
                            if isinstance(sentiment_data, list):
                                # Simple list of review IDs
                                review_ids = sentiment_data
                                reasons = []
                            elif isinstance(sentiment_data, dict):
                                # Dict with reasons mapping to review IDs
                                review_ids = []
                                reasons = []
                                for reason_code, reason_reviews in sentiment_data.items():
                                    if isinstance(reason_reviews, list):
                                        review_ids.extend(reason_reviews)
                                        # Resolve reason codes to descriptions for performance sections
                                        if section_type == 'perf':
                                            resolved_reasons = self.resolve_reason_codes(reason_code, review_analysis, sentiment)
                                            if resolved_reasons:  # Only add non-empty reasons
                                                for resolved_reason in resolved_reasons:
                                                    reasons.extend([resolved_reason] * len(reason_reviews))
                                        else:
                                            # For physical aspects, use reason as-is (skip '?' codes)
                                            if reason_code != '?':
                                                reasons.extend([reason_code] * len(reason_reviews))
                            else:
                                continue
                            
                            # Count mentions and sentiment
                            mention_count = len(review_ids)
                            category_stats['mentions'] += mention_count
                            category_stats['totalReviews'] += mention_count
                            
                            # Extract clean aspect description
                            clean_aspect = aspect_key.split('@', 1)[-1] if '@' in aspect_key else aspect_key
                            
                            if sentiment == '+':
                                category_stats['positiveCount'] += mention_count
                                # Add to positive aspects and reasons
                                category_stats['topPositiveAspects'].append(clean_aspect)
                                category_stats['topPositiveReasons'].extend(reasons)
                            else:
                                category_stats['negativeCount'] += mention_count
                                # Add to negative aspects and reasons
                                category_stats['topNegativeAspects'].append(clean_aspect)
                                category_stats['topNegativeReasons'].extend(reasons)
                            
                            # Add rating data if available (using default rating since raw review data is not in processed files)
                            for review_id in review_ids:
                                # Use default rating since we don't have access to raw review ratings in processed data
                                if isinstance(review_id, (int, str)):
                                    try:
                                        # Convert to int if it's a string representation
                                        review_id_int = int(review_id) if isinstance(review_id, str) else review_id
                                        # Use default neutral rating since raw review data is not available
                                        default_rating = 3.0
                                        category_stats['rating_sum'] += default_rating
                                        category_stats['rating_count'] += 1
                                    except (ValueError, TypeError):
                                        # Skip invalid review IDs
                                        continue
        
        # Calculate final statistics
        self._calculate_category_statistics()
    
    def _calculate_category_statistics(self):
        """Calculate final statistics for categories"""
        for product_type in ['dimmer', 'light']:
            for category_name, stats in self.category_stats_by_type[product_type].items():
                total_reviews = stats['totalReviews']
                if total_reviews > 0:
                    stats['satisfactionRate'] = round((stats['positiveCount'] / total_reviews) * 100, 1)
                    stats['negativeRate'] = round((stats['negativeCount'] / total_reviews) * 100, 1)
                
                if stats['rating_count'] > 0:
                    stats['averageRating'] = round(stats['rating_sum'] / stats['rating_count'], 1)
                else:
                    stats['averageRating'] = 3.0
                
                # Count occurrences and format top aspects and reasons with counts
                from collections import Counter
                
                # Process aspects
                positive_counter = Counter(stats['topPositiveAspects'])
                top_positive_with_counts = positive_counter.most_common(5)
                stats['topPositiveAspects'] = [
                    f"{aspect} ({count}x)" if count > 1 else aspect 
                    for aspect, count in top_positive_with_counts
                ]
                
                negative_counter = Counter(stats['topNegativeAspects'])
                top_negative_with_counts = negative_counter.most_common(5)
                stats['topNegativeAspects'] = [
                    f"{aspect} ({count}x)" if count > 1 else aspect 
                    for aspect, count in top_negative_with_counts
                ]
                
                # Process reasons
                positive_reasons_counter = Counter(stats['topPositiveReasons'])
                top_positive_reasons_with_counts = positive_reasons_counter.most_common(5)
                stats['topPositiveReasons'] = [
                    f"{reason} ({count}x)" if count > 1 else reason 
                    for reason, count in top_positive_reasons_with_counts
                ]
                
                negative_reasons_counter = Counter(stats['topNegativeReasons'])
                top_negative_reasons_with_counts = negative_reasons_counter.most_common(5)
                stats['topNegativeReasons'] = [
                    f"{reason} ({count}x)" if count > 1 else reason 
                    for reason, count in top_negative_reasons_with_counts
                ]
                
                # Clean up temporary fields
                del stats['rating_sum']
                del stats['rating_count']
    
    def calculate_summary_stats(self):
        """Calculate summary statistics by product type"""
        for product_type in ['dimmer', 'light']:
            categories = self.category_stats_by_type[product_type]
            
            if not categories:
                continue
            
            # Filter categories with sufficient data
            valid_categories = [cat for cat in categories.values() 
                             if cat['totalReviews'] >= MIN_REVIEWS_FOR_STATS]
            
            physical_count = sum(1 for cat in valid_categories if cat['categoryType'] == 'Physical')
            performance_count = sum(1 for cat in valid_categories if cat['categoryType'] == 'Performance')
            
            avg_satisfaction = 0
            if valid_categories:
                total_weighted_satisfaction = sum(cat['satisfactionRate'] * cat['totalReviews'] 
                                                for cat in valid_categories)
                total_reviews = sum(cat['totalReviews'] for cat in valid_categories)
                if total_reviews > 0:
                    avg_satisfaction = round(total_weighted_satisfaction / total_reviews, 1)
            
            self.summary_stats_by_type[product_type] = {
                'totalCategories': len(valid_categories),
                'physicalCategories': physical_count,
                'performanceCategories': performance_count,
                'avgSatisfactionRate': avg_satisfaction,
                'processingDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'productType': 'Dimmer Switches' if product_type == 'dimmer' else 'Light Switches'
            }
    
    def get_top_negative_categories(self, product_type: str, limit: int = 10) -> List[Dict]:
        """Get top negative categories by absolute negative count"""
        stats = self.category_stats_by_type[product_type]
        sorted_categories = sorted(
            [cat for cat in stats.values() if cat['totalReviews'] >= MIN_REVIEWS_FOR_STATS],
            key=lambda x: -x['negativeCount']
        )
        return sorted_categories[:limit]
    
    def get_top_positive_categories(self, product_type: str, limit: int = 10) -> List[Dict]:
        """Get top positive categories by absolute positive count"""
        stats = self.category_stats_by_type[product_type]
        sorted_categories = sorted(
            [cat for cat in stats.values() if cat['totalReviews'] >= MIN_REVIEWS_FOR_STATS],
            key=lambda x: -x['positiveCount']
        )
        return sorted_categories[:limit]

    def resolve_reason_codes(self, reason_codes: str, review_analysis: Dict[str, Any], sentiment_context: str = None) -> List[str]:
        """
        Resolve reason codes (like 'a,c,x,y') to actual aspect descriptions
        
        Args:
            reason_codes: Comma-separated reason codes (e.g., 'a,c,x,y')
            review_analysis: Full review analysis data for this product
            sentiment_context: '+' or '-' to ensure we only get descriptions from same sentiment
        
        Returns:
            List of human-readable reason descriptions
        """
        if reason_codes == '?':
            return []  # Skip unknown reason codes
        
        # Split multiple reason codes and filter out '?'
        codes = [code.strip() for code in reason_codes.split(',') if code.strip() != '?']
        if not codes:
            return []  # Return empty list if only '?' codes
        
        resolved_reasons = []
        
        # Look through physical and performance sections for aspect descriptions
        for section_name in ['phy', 'perf']:
            if section_name not in review_analysis:
                continue
            
            section_data = review_analysis[section_name]
            for category, aspects in section_data.items():
                if not isinstance(aspects, dict):
                    continue
                
                for aspect_key, aspect_sentiments in aspects.items():
                    # Extract the reason code from the aspect key (e.g., "A@description" -> "A")
                    if '@' in aspect_key:
                        aspect_code = aspect_key.split('@')[0]
                        aspect_description = aspect_key.split('@', 1)[1]
                        
                        # Check if this aspect code is in our reason codes
                        if aspect_code.lower() in [code.lower() for code in codes]:
                            # If sentiment_context is provided, only include if the aspect has that sentiment
                            if sentiment_context:
                                if isinstance(aspect_sentiments, dict) and sentiment_context in aspect_sentiments:
                                    resolved_reasons.append(aspect_description)
                            else:
                                # No sentiment context provided, include all matches
                                resolved_reasons.append(aspect_description)
        
        # If we couldn't resolve any codes, return empty list
        if not resolved_reasons:
            return []
        
        # Return all individual reasons (we'll count and show top ones later)
        return resolved_reasons

    def analyze_use_cases(self):
        """Analyze use case satisfaction data from actual 'use' sections"""
        print("Analyzing use case satisfaction data...")
        debug_count = 0
        
        # Initialize use case data by product type
        use_case_data_by_type = {
            'dimmer': defaultdict(lambda: {
                'total_mentions': 0,
                'positive_reviews': [],
                'negative_reviews': [],
                'satisfaction_reasons': [],
                'gap_reasons': [],
                'related_categories': set()
            }),
            'light': defaultdict(lambda: {
                'total_mentions': 0,
                'positive_reviews': [],
                'negative_reviews': [],
                'satisfaction_reasons': [],
                'gap_reasons': [],
                'related_categories': set()
            })
        }
        
        # Process each product
        for product_id, product_data in self.consolidated_data.get('results', {}).items():
            if product_id not in self.product_mapping:
                continue
            
            product_type = self.product_mapping[product_id]['type']
            aspect_categorization = product_data.get('aspect_categorization', {})
            
            # Get corresponding expanded review data
            expanded_product = self.expanded_reviews.get('results', {}).get(product_id, {})
            review_analysis = expanded_product.get('review_analysis', {})
            
            # Process 'use' section if available
            if 'use' not in review_analysis:
                continue
            
            use_reviews = review_analysis['use']
            use_categorization = aspect_categorization.get('use', {})
            
            # Process each use case directly from the review data
            for use_case, use_case_reviews in use_reviews.items():
                # Get the final category name from categorization, or use the original name
                final_category = use_categorization.get(use_case, use_case)
                if final_category == "OUT_OF_SCOPE":
                    continue
                
                # Format the display name properly
                display_name = final_category.replace('_', ' ').title()
                
                use_case_data = use_case_data_by_type[product_type][display_name]
                
                # Debug logging for first few products
                debug_count += 1
                if debug_count <= 3:
                    print(f"   Debug {debug_count}: Processing {use_case} -> {display_name} for {product_type}")
                    print(f"      Sentiments available: {list(use_case_reviews.keys())}")
                
                # Process positive and negative sentiments
                for sentiment in ['+', '-']:
                    if sentiment not in use_case_reviews:
                        continue
                    
                    sentiment_data = use_case_reviews[sentiment]
                    if not isinstance(sentiment_data, dict):
                        continue
                    
                    # Process each reason and its review objects
                    for reason, review_objects in sentiment_data.items():
                        if not isinstance(review_objects, list):
                            continue
                        
                        # Count each review object once for total mentions
                        mention_count = len(review_objects)
                        use_case_data['total_mentions'] += mention_count
                        
                        # Resolve reason codes to actual descriptions with sentiment context
                        clean_reasons = self.resolve_reason_codes(reason, review_analysis, sentiment)
                        if not clean_reasons:  # Skip empty reasons but still count the reviews
                            continue
                        
                        # Create review data entries from the actual review objects
                        for review_obj in review_objects:
                            # Skip invalid review objects
                            if not isinstance(review_obj, dict):
                                continue
                            
                            # Extract rating from the review object
                            rating_str = review_obj.get('rating', '3.0')
                            rating = self.extract_rating_score(rating_str)
                            
                            # Add ONE entry per review (not per clean_reason) for counting purposes
                            review_data = {
                                'rating': rating,
                                'sentiment': sentiment,
                                'reason': clean_reasons[0] if clean_reasons else reason,  # Use first clean reason or original
                                'use_case': use_case,
                                'product_id': product_id,
                                'review_id': review_obj.get('review_id', 0),
                                'review_text': review_obj.get('review_text', '')[:100] + '...'  # Truncated for storage
                            }
                            
                            if sentiment == '+':
                                use_case_data['positive_reviews'].append(review_data)
                            else:
                                use_case_data['negative_reviews'].append(review_data)
                            
                            # Add all clean reasons to the reasons lists for analysis
                            for clean_reason in clean_reasons:
                                if sentiment == '+':
                                    use_case_data['satisfaction_reasons'].append(clean_reason)
                                else:
                                    use_case_data['gap_reasons'].append(clean_reason)
                        
        
        # Calculate use case statistics
        print("Calculating use case statistics...")
        for product_type in ['dimmer', 'light']:
            self.use_case_stats_by_type[product_type] = {}
            use_case_data = use_case_data_by_type[product_type]
            
            for use_case, data in use_case_data.items():
                total_mentions = data['total_mentions']
                if total_mentions < MIN_REVIEWS_FOR_STATS:
                    continue
                
                positive_count = len(data['positive_reviews'])
                negative_count = len(data['negative_reviews'])
                
                # Calculate satisfaction rate
                satisfaction_rate = (positive_count / total_mentions) * 100 if total_mentions > 0 else 0
                
                # Get top satisfaction and gap reasons
                satisfaction_reasons_count = defaultdict(int)
                for reason in data['satisfaction_reasons']:
                    satisfaction_reasons_count[reason] += 1
                
                top_satisfaction_reasons = sorted(
                    satisfaction_reasons_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                gap_reasons_count = defaultdict(int)
                for reason in data['gap_reasons']:
                    gap_reasons_count[reason] += 1
                
                top_gap_reasons = sorted(
                    gap_reasons_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                # Format use case display name
                use_case_display = use_case.replace('_', ' ').title()
                
                self.use_case_stats_by_type[product_type][use_case] = {
                    'useCase': use_case_display,
                    'totalMentions': total_mentions,
                    'positiveCount': positive_count,
                    'negativeCount': negative_count,
                    'satisfactionRate': round(satisfaction_rate, 1),
                    'categoryType': 'Physical',  # Most use cases relate to physical characteristics
                    'topSatisfactionReasons': [
                        f"{reason} ({count}x)" if count > 1 else reason 
                        for reason, count in top_satisfaction_reasons
                    ],
                    'topGapReasons': [
                        f"{reason} ({count}x)" if count > 1 else reason 
                        for reason, count in top_gap_reasons
                    ],
                    'relatedCategories': list(data['related_categories'])[:5]
                }
    
    def get_top_use_cases(self, product_type: str, limit: int = 10) -> List[Dict]:
        """Get top use cases sorted by total mentions"""
        stats = self.use_case_stats_by_type[product_type]
        sorted_use_cases = sorted(
            stats.values(),
            key=lambda x: -x['totalMentions']
        )
        return sorted_use_cases[:limit]

    def generate_typescript_file(self, output_path: str):
        """Generate TypeScript data file with actual analyzed data"""
        print(f"Generating TypeScript file: {output_path}")
        
        # Get data for both product types
        top_negative_dimmer = self.get_top_negative_categories('dimmer', 10)
        top_negative_light = self.get_top_negative_categories('light', 10)
        
        top_positive_dimmer = self.get_top_positive_categories('dimmer', 10)
        top_positive_light = self.get_top_positive_categories('light', 10)
        
        top_use_cases_dimmer = self.get_top_use_cases('dimmer', 10)
        top_use_cases_light = self.get_top_use_cases('light', 10)
        
        # Get all categories data
        all_categories_dimmer = list(self.category_stats_by_type['dimmer'].values())
        all_categories_light = list(self.category_stats_by_type['light'].values())
        
        # Sort by negative rate
        all_categories_dimmer.sort(key=lambda x: -x['negativeRate'])
        all_categories_light.sort(key=lambda x: -x['negativeRate'])
        
        # Generate TypeScript content
        ts_content = f'''// Category Feedback Analysis Data - Generated from actual review analysis
// Data source: {self.data_dir}
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Products analyzed: Dimmer={len([p for p in self.product_mapping.values() if p['type'] == 'dimmer'])}, Light={len([p for p in self.product_mapping.values() if p['type'] == 'light'])}

export interface CategoryFeedback {{
  category: string;
  categoryType: 'Physical' | 'Performance';
  mentions: number;
  satisfactionRate: number;
  negativeRate: number;
  positiveCount: number;
  negativeCount: number;
  totalReviews: number;
  averageRating: number;
  topNegativeAspects: string[];
  topPositiveAspects: string[];
  topNegativeReasons: string[];
  topPositiveReasons: string[];
}}

export interface UseCaseFeedback {{
  useCase: string;
  totalMentions: number;
  positiveCount: number;
  negativeCount: number;
  satisfactionRate: number;
  categoryType: 'Physical' | 'Performance';
  topSatisfactionReasons: string[];
  topGapReasons: string[];
  relatedCategories: string[];
}}

export interface CategoryFeedbackData {{
  summary: {{
    totalCategories: number;
    physicalCategories: number;
    performanceCategories: number;
    avgSatisfactionRate: number;
    processingDate: string;
    productType: string;
  }};
  topNegativeCategories: CategoryFeedback[];
  topPositiveCategories: CategoryFeedback[];
  topUseCases: UseCaseFeedback[];
  allCategories: CategoryFeedback[];
}}

export type ProductType = 'dimmer' | 'light';

// Dimmer Switches Data
export const dimmerSwitchesSummary = {json.dumps(self.summary_stats_by_type['dimmer'], indent=2, ensure_ascii=False)};
export const topNegativeDimmerCategories: CategoryFeedback[] = {json.dumps(top_negative_dimmer, indent=2, ensure_ascii=False)};
export const topPositiveDimmerCategories: CategoryFeedback[] = {json.dumps(top_positive_dimmer, indent=2, ensure_ascii=False)};
export const topUseCasesDimmer: UseCaseFeedback[] = {json.dumps(top_use_cases_dimmer, indent=2, ensure_ascii=False)};
export const allDimmerCategories: CategoryFeedback[] = {json.dumps(all_categories_dimmer, indent=2, ensure_ascii=False)};

// Light Switches Data  
export const lightSwitchesSummary = {json.dumps(self.summary_stats_by_type['light'], indent=2, ensure_ascii=False)};
export const topNegativeLightCategories: CategoryFeedback[] = {json.dumps(top_negative_light, indent=2, ensure_ascii=False)};
export const topPositiveLightCategories: CategoryFeedback[] = {json.dumps(top_positive_light, indent=2, ensure_ascii=False)};
export const topUseCasesLight: UseCaseFeedback[] = {json.dumps(top_use_cases_light, indent=2, ensure_ascii=False)};
export const allLightCategories: CategoryFeedback[] = {json.dumps(all_categories_light, indent=2, ensure_ascii=False)};

// Utility Functions
export function getCategoryFeedback(productType: ProductType = 'dimmer'): CategoryFeedbackData {{
  if (productType === 'dimmer') {{
    return {{
      summary: dimmerSwitchesSummary,
      topNegativeCategories: topNegativeDimmerCategories,
      topPositiveCategories: topPositiveDimmerCategories,
      topUseCases: topUseCasesDimmer,
      allCategories: allDimmerCategories
    }};
  }} else {{
    return {{
      summary: lightSwitchesSummary,
      topNegativeCategories: topNegativeLightCategories,
      topPositiveCategories: topPositiveLightCategories,
      topUseCases: topUseCasesLight,
      allCategories: allLightCategories
    }};
  }}
}}

export function getTopNegativeCategories(productType: ProductType = 'dimmer', limit: number = 10): CategoryFeedback[] {{
  const data = getCategoryFeedback(productType);
  return data.topNegativeCategories.slice(0, limit);
}}

export function getTopPositiveCategories(productType: ProductType = 'dimmer', limit: number = 10): CategoryFeedback[] {{
  const data = getCategoryFeedback(productType);
  return data.topPositiveCategories.slice(0, limit);
}}

export function getTopUseCases(productType: ProductType = 'dimmer', limit: number = 10): UseCaseFeedback[] {{
  const data = getCategoryFeedback(productType);
  return data.topUseCases.slice(0, limit);
}}

export function getCategoriesByType(categoryType: 'Physical' | 'Performance', productType: ProductType = 'dimmer'): CategoryFeedback[] {{
  const data = getCategoryFeedback(productType);
  return data.allCategories.filter(cat => cat.categoryType === categoryType);
}}

export function getAvailableProductTypes(): {{ value: ProductType; label: string }}[] {{
  return [
    {{ value: 'dimmer', label: 'Dimmer Switches' }},
    {{ value: 'light', label: 'Light Switches' }}
  ];
}}
'''
        
        # Write file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ts_content)
        
        print(f"✓ Generated TypeScript file: {output_path}")
    
    def print_analysis_summary(self):
        """Print analysis results summary"""
        print("\n" + "="*80)
        print("Category Feedback Analysis Summary - Generated from Actual Data")
        print("="*80)
        
        for product_type in ['dimmer', 'light']:
            product_name = 'Dimmer Switches' if product_type == 'dimmer' else 'Light Switches'
            summary = self.summary_stats_by_type[product_type]
            
            print(f"\n📊 {product_name}:")
            print(f"Total Categories: {summary['totalCategories']}")
            print(f"Physical Categories: {summary['physicalCategories']}")
            print(f"Performance Categories: {summary['performanceCategories']}")
            print(f"Average Satisfaction Rate: {summary['avgSatisfactionRate']}%")
            
            print(f"\nTop 5 Negative Categories (by negative count):")
            top_negative = self.get_top_negative_categories(product_type, 5)
            for i, cat in enumerate(top_negative, 1):
                print(f"{i:2d}. {cat['category']:<35} | Negative: {cat['negativeCount']:3d} | Rate: {cat['negativeRate']:5.1f}% | Total: {cat['totalReviews']:3d}")
            
            print(f"\nTop 5 Positive Categories (by positive count):")
            top_positive = self.get_top_positive_categories(product_type, 5)
            for i, cat in enumerate(top_positive, 1):
                print(f"{i:2d}. {cat['category']:<35} | Positive: {cat['positiveCount']:3d} | Rate: {cat['satisfactionRate']:5.1f}% | Total: {cat['totalReviews']:3d}")
            
            print(f"\nTop 5 Use Cases (by mention count):")
            top_use_cases = self.get_top_use_cases(product_type, 5)
            for i, uc in enumerate(top_use_cases, 1):
                print(f"{i:2d}. {uc['useCase']:<35} | Mentions: {uc['totalMentions']:3d} | Satisfaction: {uc['satisfactionRate']:5.1f}%")
            
            print("-" * 80)
    
    def run(self, output_path: str):
        """Run the complete analysis pipeline"""
        try:
            self.load_data()
            self.analyze_categories()
            self.analyze_use_cases()
            self.calculate_summary_stats()
            self.generate_typescript_file(output_path)
            self.print_analysis_summary()
            
            print(f"\n✅ Analysis complete! TypeScript data generated at: {output_path}")
            
        except Exception as e:
            print(f"\n❌ Analysis failed: {str(e)}")
            raise


def main():
    """Main execution function"""
    # Set up paths
    
    print("Category Feedback Analyzer - Reading from Actual Generated Data")
    print("="*70)
    print(f"Data directory: {DATA_DIR}")
    print(f"Output file: {OUTPUT_PATH}")
    print()
    
    # Run analysis
    analyzer = CategoryFeedbackAnalyzer(str(DATA_DIR))
    analyzer.run(str(OUTPUT_PATH))


if __name__ == "__main__":
    main() 