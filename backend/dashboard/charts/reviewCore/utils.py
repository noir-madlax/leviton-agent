"""Shared utilities for review processing."""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReviewProcessingUtils:
    """Shared utilities for review processing."""
    
    @staticmethod
    def calculate_sentiment_distribution(reviews_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate sentiment distribution from review data.
        
        Args:
            reviews_data: List of review data dictionaries
            
        Returns:
            Dict with sentiment counts
        """
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for review in reviews_data:
            sentiment = review.get('sentiment', 'neutral')
            if sentiment == '+':
                sentiment_counts['positive'] += 1
            elif sentiment == '-':
                sentiment_counts['negative'] += 1
            else:
                sentiment_counts['neutral'] += 1
        
        return sentiment_counts
    
    @staticmethod
    def aggregate_category_metrics(categories_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metrics across categories.
        
        Args:
            categories_data: List of category data dictionaries
            
        Returns:
            Dict with aggregated metrics
        """
        total_mentions = sum(cat.get('mentions', 0) for cat in categories_data)
        total_reviews = sum(cat.get('reviews', 0) for cat in categories_data)
        total_positive = sum(cat.get('positive_mentions', 0) for cat in categories_data)
        total_negative = sum(cat.get('negative_mentions', 0) for cat in categories_data)
        
        return {
            'total_categories': len(categories_data),
            'total_mentions': total_mentions,
            'total_reviews': total_reviews,
            'total_positive_mentions': total_positive,
            'total_negative_mentions': total_negative,
            'overall_positive_ratio': total_positive / max(total_mentions, 1)
        }
    
    @staticmethod
    def apply_pagination(data: List[Dict[str, Any]], limit: int, offset: int) -> Dict[str, Any]:
        """Apply pagination to data with metadata.
        
        Args:
            data: List of data items
            limit: Number of items per page
            offset: Current offset
            
        Returns:
            Dict with paginated data and metadata
        """
        total_items = len(data)
        paginated_data = data[offset:offset + limit]
        
        return {
            'data': paginated_data,
            'total_items': total_items,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total_items
        }
    
    @staticmethod
    def format_aspect_description(parent_group: str, detail_text: str) -> str:
        """Format aspect description based on parent group and detail text.
        
        Args:
            parent_group: Parent group name
            detail_text: Detail text
            
        Returns:
            Formatted aspect description
        """
        if parent_group and detail_text and parent_group != detail_text:
            return f"{parent_group}: {detail_text}"
        else:
            return detail_text or parent_group
    
    @staticmethod
    def transform_rating(rating: Any) -> Optional[int]:
        """Transform rating from string to integer if needed.
        
        Args:
            rating: Rating value (string or int)
            
        Returns:
            Transformed rating as integer or None
        """
        if isinstance(rating, str) and 'out of' in rating:
            try:
                return int(float(rating.split(' out of')[0]))
            except (ValueError, IndexError):
                return None
        elif isinstance(rating, (int, float)):
            return int(rating)
        else:
            return None 