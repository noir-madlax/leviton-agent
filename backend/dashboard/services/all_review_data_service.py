"""All Review Data Service for Dashboard module.

This service handles all review data retrieval with project ASIN filtering.
Migrated from frontend logic to ensure consistent project-based filtering.
"""

import logging
from typing import Dict, List, Any, Literal
import re
from datetime import datetime

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class AllReviewDataService(BaseDashboardService):
    """Service for all review data with project ASIN filtering.
    
    Provides comprehensive review data by joining:
    - product_review_analysis (main analysis data)
    - product_reviews (rating, verified, date)
    - product_wide_table (brand information)
    
    This replaces the frontend getAllReviewData() method with proper
    project ASIN filtering and real data instead of random values.
    """

    def get_data(self) -> Dict[str, Any]:
        """Get all review data filtered by project ASINs.
        
        Returns:
            Dict containing review data grouped by standardized_aspect
        """
        try:
            # Get comprehensive review data with joins
            review_data = self._get_comprehensive_review_data()
            
            # Process and group data by aspect
            grouped_data = self._process_and_group_data(review_data)
            
            # Calculate statistics
            total_aspects = len(grouped_data)
            total_reviews = sum(len(reviews) for reviews in grouped_data.values())
            
            logger.info(f"Retrieved {total_reviews} reviews across {total_aspects} aspects for project {self.project_id}")
            
            return {
                'data': grouped_data,
                'total_aspects': total_aspects,
                'total_reviews': total_reviews
            }
            
        except Exception as e:
            logger.error(f"Error in AllReviewDataService for project {self.project_id}: {e}")
            return {
                'data': {},
                'total_aspects': 0,
                'total_reviews': 0
            }

    def _get_comprehensive_review_data(self) -> List[Dict[str, Any]]:
        """Get comprehensive review data using individual queries."""
        
        # Use fallback method directly for better compatibility
        return self._get_review_data_fallback()

    def _get_review_data_fallback(self) -> List[Dict[str, Any]]:
        """Fallback method using individual queries."""
        
        # Get analysis data
        analysis_query = self.supabase.from_('product_review_analysis').select(
            'product_id, review_content, standardized_aspect, aspect_category, review_id'
        ).in_('product_id', self.project_asins).neq('standardized_aspect', 'OUT_OF_SCOPE').limit(2000)
        
        analysis_result = analysis_query.execute()
        
        if not analysis_result.data:
            return []
        
        # Get ratings data
        review_ids = [item['review_id'] for item in analysis_result.data]
        rating_query = self.supabase.from_('product_reviews').select(
            'review_id, rating, verified, review_date'
        ).in_('review_id', review_ids)
        
        rating_result = rating_query.execute()
        rating_map = {item['review_id']: item for item in rating_result.data} if rating_result.data else {}
        
        # Get brand data
        product_ids = list(set([item['product_id'] for item in analysis_result.data]))
        brand_query = self._get_base_product_table().select('platform_id, brand').in_('platform_id', product_ids)
        brand_query = self._apply_base_filters(brand_query)
        
        brand_result = brand_query.execute()
        brand_map = {item['platform_id']: item['brand'] for item in brand_result.data} if brand_result.data else {}
        
        # Combine data
        combined_data = []
        for item in analysis_result.data:
            review_id = item['review_id']
            product_id = item['product_id']
            
            rating_info = rating_map.get(review_id, {})
            brand = brand_map.get(product_id, 'Unknown')
            
            combined_data.append({
                'product_id': product_id,
                'review_content': item['review_content'],
                'standardized_aspect': item['standardized_aspect'],
                'aspect_category': item['aspect_category'],
                'review_id': review_id,
                'rating': rating_info.get('rating'),
                'verified': rating_info.get('verified', False),
                'review_date': rating_info.get('review_date'),
                'brand': brand
            })
        
        logger.info(f"Retrieved {len(combined_data)} records using fallback method")
        return combined_data

    def _process_and_group_data(self, review_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Process review data and group by standardized_aspect."""
        
        grouped_data = {}
        
        for item in review_data:
            aspect = item['standardized_aspect']
            
            if aspect not in grouped_data:
                grouped_data[aspect] = []
            
            # Parse rating and determine sentiment
            rating_str = item.get('rating', '3.0')
            rating = self._parse_rating(rating_str)
            sentiment = self._get_sentiment(rating)
            
            # Parse date
            date = self._parse_date(item.get('review_date'))
            
            review_item = {
                'id': f"{item['review_id']}_{len(grouped_data[aspect])}",
                'productId': item['product_id'],
                'text': item['review_content'] or '',
                'sentiment': sentiment,
                'category': item['aspect_category'] or 'unknown',
                'aspect': aspect,
                'rating': max(1, min(5, rating)),  # Ensure rating is 1-5
                'verified': bool(item.get('verified', False)),
                'date': date,
                'brand': item.get('brand', 'Unknown')
            }
            
            grouped_data[aspect].append(review_item)
        
        return grouped_data

    def _parse_rating(self, rating_str: str) -> int:
        """Parse rating string to integer."""
        if not rating_str:
            return 3
        
        try:
            # Handle formats like "5.0 out of 5 stars" or "4.5"
            rating_match = re.search(r'(\d+\.?\d*)', str(rating_str))
            if rating_match:
                rating_float = float(rating_match.group(1))
                return max(1, min(5, round(rating_float)))
            return 3
        except (ValueError, AttributeError):
            return 3

    def _get_sentiment(self, rating: int) -> Literal['positive', 'negative', 'neutral']:
        """Determine sentiment from rating."""
        if rating >= 4:
            return 'positive'
        elif rating <= 2:
            return 'negative'
        else:
            return 'neutral'

    def _parse_date(self, date_str: str) -> str:
        """Parse date string to ISO format."""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Handle format like "Reviewed in the United States on May 19, 2025"
            date_match = re.search(r'on\s+(\w+\s+\d+,\s+\d+)', date_str)
            if date_match:
                date_part = date_match.group(1)
                parsed_date = datetime.strptime(date_part, '%B %d, %Y')
                return parsed_date.strftime('%Y-%m-%d')
            
            # Try other common formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Fallback to current date
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception:
            return datetime.now().strftime('%Y-%m-%d') 