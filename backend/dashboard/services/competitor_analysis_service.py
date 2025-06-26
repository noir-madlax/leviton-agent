"""Competitor Analysis Service for Dashboard module.

This service handles competitor analysis data retrieval with project ASIN filtering.
Migrated from frontend logic to ensure consistent project-based filtering.
"""

import logging
from typing import Dict, List, Any, Literal
import re

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class CompetitorAnalysisService(BaseDashboardService):
    """Service for competitor analysis data with focused 6-product comparison.
    
    Provides competitor analysis data for 6 core products:
    - Leviton D26HD, Leviton D215S, Lutron Caseta Diva
    - TP Link Switch, Leviton DSL06, Lutron Diva
    
    This replaces the frontend getCompetitorAnalysisData() method with proper
    focused product comparison instead of all project ASINs.
    """

    # Core 6 products for competitor analysis
    CORE_COMPETITOR_ASINS = [
        'B08RRM8VH5',  # Leviton D26HD
        'B0BVKZLT3B',  # Leviton D215S  
        'B0BSHKS26L',  # Lutron Caseta Diva
        'B01EZV35QU',  # TP Link Switch
        'B00NG0ELL0',  # Leviton DSL06
        'B085D8M2MR'   # Lutron Diva
    ]

    # ASIN to display name mapping (consistent with frontend)
    ASIN_TO_DISPLAY_NAME = {
        'B08RRM8VH5': 'Leviton D26HD',
        'B0BVKZLT3B': 'Leviton D215S',
        'B0BSHKS26L': 'Lutron Caseta Diva', 
        'B01EZV35QU': 'TP Link Switch',
        'B00NG0ELL0': 'Leviton DSL06',
        'B085D8M2MR': 'Lutron Diva'
    }

    def get_data(self) -> Dict[str, Any]:
        """Get competitor analysis data filtered by project ASINs.
        
        Returns:
            Dict containing competitor analysis data matching frontend format
        """
        try:
            # Get product information for target products
            product_info = self._get_product_info()
            
            # Get review analysis data
            analysis_data = self._get_analysis_data()
            
            # Get rating data for sentiment analysis
            rating_data = self._get_rating_data()
            
            # Process data and generate matrices
            return self._process_competitor_data(product_info, analysis_data, rating_data)
            
        except Exception as e:
            logger.error(f"Error in CompetitorAnalysisService for project {self.project_id}: {e}")
            return {
                'targetProducts': [],
                'matrixData': [],
                'productTotalReviews': {},
                'useCaseData': {
                    'targetProducts': [],
                    'matrixData': []
                }
            }

    def _get_product_info(self) -> List[Dict[str, Any]]:
        """Get product information for core 6 competitor products."""
        query = self._get_base_product_table().select('platform_id, title, reviews_count')
        query = self._apply_base_filters(query)
        # Use core competitor ASINs instead of all project ASINs
        query = query.in_('platform_id', self.CORE_COMPETITOR_ASINS)
        result = query.execute()
        
        if result.data:
            logger.info(f"Retrieved {len(result.data)} core competitor products")
            return result.data
        else:
            logger.warning("No product information found for core competitor ASINs")
            return []

    def _get_analysis_data(self) -> List[Dict[str, Any]]:
        """Get review analysis data filtered by core competitor ASINs."""
        query = self.supabase.from_('product_review_analysis').select(
            'product_id, aspect_category, standardized_aspect, review_id'
        ).in_('product_id', self.CORE_COMPETITOR_ASINS).neq('standardized_aspect', 'OUT_OF_SCOPE')
        
        result = query.execute()
        
        if result.data:
            logger.info(f"Retrieved {len(result.data)} analysis records for core competitors")
            return result.data
        else:
            logger.warning("No analysis data found for core competitor ASINs")
            return []

    def _get_rating_data(self) -> List[Dict[str, Any]]:
        """Get rating data for sentiment analysis."""
        query = self.supabase.from_('product_reviews').select(
            'product_id, review_id, rating'
        ).in_('product_id', self.CORE_COMPETITOR_ASINS).neq('rating', None)
        
        result = query.execute()
        
        if result.data:
            logger.info(f"Retrieved {len(result.data)} rating records for core competitors")
            return result.data
        else:
            logger.warning("No rating data found for core competitor ASINs")
            return []

    def _process_competitor_data(self, product_info: List[Dict], analysis_data: List[Dict], rating_data: List[Dict]) -> Dict[str, Any]:
        """Process competitor analysis data."""
        
        # Build product mapping and total reviews using predefined display names
        asin_to_product = {}
        product_total_reviews = {}
        
        for product in product_info:
            asin = product['platform_id']
            # Use predefined display name for consistency with frontend
            display_name = self.ASIN_TO_DISPLAY_NAME.get(asin, asin)
            asin_to_product[asin] = display_name
            product_total_reviews[display_name] = product.get('reviews_count', 0)

        # Build rating mapping for sentiment analysis
        rating_map = {}
        for item in rating_data:
            key = f"{item['product_id']}_{item['review_id']}"
            rating_map[key] = item['rating']

        # Process analysis data
        category_stats, use_case_stats = self._aggregate_analysis_data(
            analysis_data, asin_to_product, rating_map
        )

        # Build matrices
        matrix_data = self._build_matrix_data(category_stats, asin_to_product)
        use_case_matrix_data = self._build_use_case_data(use_case_stats, asin_to_product)

        target_products = list(asin_to_product.values())

        return {
            'targetProducts': target_products,
            'matrixData': matrix_data,
            'productTotalReviews': product_total_reviews,
            'useCaseData': {
                'targetProducts': target_products,
                'matrixData': use_case_matrix_data
            }
        }

    def _get_display_name(self, title: str) -> str:
        """Extract display name from product title."""
        if not title:
            return "Unknown Product"
        
        # Extract brand and model from title
        # Common patterns: "Brand Model", "Brand - Model", etc.
        title = title.strip()
        
        # Take first few words up to common separators
        parts = re.split(r'[,\-\(\)\[\]]', title)
        if parts:
            first_part = parts[0].strip()
            # Limit to reasonable length
            words = first_part.split()[:3]  # First 3 words
            return ' '.join(words)
        
        return title[:30]  # Fallback: first 30 characters

    def _aggregate_analysis_data(self, analysis_data: List[Dict], asin_to_product: Dict, rating_map: Dict) -> tuple:
        """Aggregate analysis data by category and use case."""
        
        category_stats = {}
        use_case_stats = {}

        for item in analysis_data:
            product_asin = item['product_id']
            product_name = asin_to_product.get(product_asin)
            
            if not product_name:
                continue

            # Get sentiment from rating
            rating_key = f"{product_asin}_{item['review_id']}"
            rating_str = rating_map.get(rating_key, '3.0')
            rating = self._parse_rating(rating_str)
            sentiment = self._get_sentiment(rating)

            # Process non-use_case categories
            if item['aspect_category'] != 'use_case':
                aspect = item['standardized_aspect']
                
                if aspect not in category_stats:
                    category_stats[aspect] = {
                        'totalMentions': 0,
                        'productData': {}
                    }

                if product_name not in category_stats[aspect]['productData']:
                    category_stats[aspect]['productData'][product_name] = {
                        'positive': 0,
                        'negative': 0,
                        'neutral': 0,
                        'total': 0,
                        'categoryType': 'Physical' if item['aspect_category'] == 'physical' else 'Performance'
                    }

                category_stats[aspect]['totalMentions'] += 1
                category_stats[aspect]['productData'][product_name][sentiment] += 1
                category_stats[aspect]['productData'][product_name]['total'] += 1

            # Process use_case categories
            else:
                use_case = item['standardized_aspect']
                
                if use_case not in use_case_stats:
                    use_case_stats[use_case] = {
                        'totalMentions': 0,
                        'productData': {}
                    }

                if product_name not in use_case_stats[use_case]['productData']:
                    use_case_stats[use_case]['productData'][product_name] = {
                        'positive': 0,
                        'negative': 0,
                        'neutral': 0,
                        'total': 0
                    }

                use_case_stats[use_case]['totalMentions'] += 1
                use_case_stats[use_case]['productData'][product_name][sentiment] += 1
                use_case_stats[use_case]['productData'][product_name]['total'] += 1

        return category_stats, use_case_stats

    def _parse_rating(self, rating_str: str) -> float:
        """Parse rating string to numeric value."""
        if not rating_str:
            return 3.0
        
        # Extract numeric value from rating string
        match = re.match(r'^(\d+(?:\.\d+)?)', str(rating_str))
        return float(match.group(1)) if match else 3.0

    def _get_sentiment(self, rating: float) -> Literal['positive', 'negative', 'neutral']:
        """Determine sentiment from rating."""
        if rating >= 4:
            return 'positive'
        elif rating <= 2:
            return 'negative'
        else:
            return 'neutral'

    def _build_matrix_data(self, category_stats: Dict, asin_to_product: Dict) -> List[Dict[str, Any]]:
        """Build matrix data for categories."""
        
        # Get top 10 categories by mentions
        top_categories = sorted(
            category_stats.items(),
            key=lambda x: x[1]['totalMentions'],
            reverse=True
        )[:10]

        matrix_data = []
        
        for category, category_data in top_categories:
            display_category = self._get_friendly_category_name(category)
            
            for product_name in asin_to_product.values():
                product_data = category_data['productData'].get(product_name)
                
                if product_data:
                    positive_count = product_data['positive']
                    negative_count = product_data['negative']
                    total_sentiment_reviews = positive_count + negative_count
                    
                    # Calculate satisfaction rate
                    if total_sentiment_reviews > 0:
                        satisfaction_rate = (positive_count / total_sentiment_reviews) * 100
                    elif product_data['neutral'] > 0:
                        satisfaction_rate = 50.0  # neutral case
                    else:
                        satisfaction_rate = 0.0

                    matrix_data.append({
                        'product': product_name,
                        'category': display_category,
                        'categoryType': product_data['categoryType'],
                        'mentions': product_data['total'],
                        'satisfactionRate': round(satisfaction_rate, 1),
                        'positiveCount': positive_count,
                        'negativeCount': negative_count,
                        'totalReviews': product_data['total']
                    })
                else:
                    # No data for this product-category combination
                    matrix_data.append({
                        'product': product_name,
                        'category': display_category,
                        'categoryType': 'Performance',
                        'mentions': 0,
                        'satisfactionRate': 0.0,
                        'positiveCount': 0,
                        'negativeCount': 0,
                        'totalReviews': 0
                    })

        return matrix_data

    def _build_use_case_data(self, use_case_stats: Dict, asin_to_product: Dict) -> List[Dict[str, Any]]:
        """Build use case matrix data."""
        
        # Get top 10 use cases by mentions
        top_use_cases = sorted(
            use_case_stats.items(),
            key=lambda x: x[1]['totalMentions'],
            reverse=True
        )[:10]

        use_case_matrix_data = []
        
        for use_case, use_case_data in top_use_cases:
            for product_name in asin_to_product.values():
                product_data = use_case_data['productData'].get(product_name)
                
                if product_data:
                    positive_count = product_data['positive']
                    negative_count = product_data['negative']
                    total_sentiment_reviews = positive_count + negative_count
                    
                    # Calculate satisfaction rate
                    if total_sentiment_reviews > 0:
                        satisfaction_rate = (positive_count / total_sentiment_reviews) * 100
                    elif product_data['neutral'] > 0:
                        satisfaction_rate = 50.0
                    else:
                        satisfaction_rate = 0.0

                    # Gap level is inverse of satisfaction
                    gap_level = 100 - satisfaction_rate

                    use_case_matrix_data.append({
                        'product': product_name,
                        'useCase': use_case,
                        'mentions': product_data['total'],
                        'satisfactionRate': round(satisfaction_rate, 1),
                        'gapLevel': round(gap_level, 1)
                    })

        return use_case_matrix_data

    def _get_friendly_category_name(self, category: str) -> str:
        """Map technical category names to friendly display names."""
        category_mapping = {
            'Basic Functionality': 'Basic Functionality',
            'Installation Process': 'Installation Process',
            'Dimming Function': 'Dimming Performance',
            'Dimming Range and Precision': 'Dimming Control',
            'App Performance': 'App Control',
            'Network Connectivity': 'WiFi Connectivity',
            'Build Quality and Materials': 'Build Quality',
            'Physical Build Quality': 'Build Quality',
            'LED Lighting Integration': 'LED Compatibility',
            'Product Lifespan': 'Durability',
            'App Control Performance': 'Smart Controls',
            'Wiring Configuration and Connections': 'Wiring Setup',
            'Visual Appearance and Aesthetics': 'Design & Appearance',
            'Size and Fit': 'Size & Fit',
            'Construction Quality': 'Construction Quality'
        }
        
        return category_mapping.get(category, category) 