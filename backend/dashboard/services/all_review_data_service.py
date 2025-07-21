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
    """Service for all review data with project filtering.
    
    Updated to use new table structure:
    - review_analysis_aspects (main analysis data)
    - review_analysis_aspect_categories (category information)
    - review_analysis_aspect_occurrences (sentiment data)
    - product_reviews (rating, verified, date)
    - product_wide_table (brand information)
    
    This replaces the frontend getAllReviewData() method with proper
    project filtering and enhanced sentiment analysis.
    """

    def _capitalize_words(self, text: str) -> str:
        """Capitalize the first letter of each word in the text."""
        if not text:
            return text
        return ' '.join(word.capitalize() for word in str(text).split())

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
        
        # Get review data from new table structure
        return self._get_review_data()

    def _get_review_data(self) -> List[Dict[str, Any]]:
        """Get review data from new table structure (review_analysis_aspects, etc.)."""
        
        try:
            # Get aspects filtered by project
            aspects_query = self.supabase.from_('review_analysis_aspects').select('''
                aspect_pk,
                product_id,
                aspect_type,
                detail_text,
                parent_group_name,
                category_pk
            ''').eq('project_id', self.project_id)
            
            logger.info(f"Executing aspects query for project_id: {self.project_id}")
            
            # Apply ASIN filtering
            if not self.project_asins:
                logger.warning(f"No ASINs found for project {self.project_id}")
                return []
            
            logger.info(f"Project ASINs count: {len(self.project_asins)}, first 10: {self.project_asins[:10]}")
            
            aspects_query = aspects_query.in_('product_id', self.project_asins)
            
            try:
                aspects_result = aspects_query.execute()
                logger.info(f"Found {len(aspects_result.data) if aspects_result.data else 0} aspects for project {self.project_id}")
                
                if not aspects_result.data:
                    logger.warning(f"No aspects data returned for project {self.project_id}")
                    return []
            except Exception as e:
                logger.error(f"Error executing aspects query: {e}")
                return []
            
            # Get category information
            category_pks = list(set([item['category_pk'] for item in aspects_result.data if item['category_pk']]))
            categories_data = {}
            
            if category_pks:
                categories_query = self.supabase.from_('review_analysis_aspect_categories').select('''
                    category_pk,
                    name,
                    definition,
                    aspect_type
                ''').in_('category_pk', category_pks).eq('stage', 'final')
                
                categories_result = categories_query.execute()
                if categories_result.data:
                    categories_data = {item['category_pk']: item for item in categories_result.data}
            
            # Get occurrence data with sentiment
            aspect_pks = [item['aspect_pk'] for item in aspects_result.data]
            occurrences_data = {}
            
            if aspect_pks:
                # Split into batches to avoid query length limits
                batch_size = 100
                all_occurrences = []
                
                for i in range(0, len(aspect_pks), batch_size):
                    batch_pks = aspect_pks[i:i + batch_size]
                    occurrences_query = self.supabase.from_('review_analysis_aspect_occurrences').select('''
                        aspect_pk,
                        sentiment,
                        review_id
                    ''').in_('aspect_pk', batch_pks)
                    
                    occurrences_result = occurrences_query.execute()
                    if occurrences_result.data:
                        all_occurrences.extend(occurrences_result.data)
                
                # Group occurrences by review_id for detailed review data
                for occurrence in all_occurrences:
                    review_id = occurrence['review_id']
                    aspect_pk = occurrence['aspect_pk']
                    
                    if review_id not in occurrences_data:
                        occurrences_data[review_id] = []
                    
                    occurrences_data[review_id].append({
                        'aspect_pk': aspect_pk,
                        'sentiment': occurrence['sentiment']
                    })
            
            # Get ratings data
            review_ids = list(occurrences_data.keys())
            rating_map = {}
            
            logger.info(f"Total review_ids to process: {len(review_ids)}")
            
            if review_ids:
                # Split into batches for rating queries
                batch_size = 100
                for i in range(0, len(review_ids), batch_size):
                    batch_ids = review_ids[i:i + batch_size]
                    # Convert text review_ids to integers for product_reviews table query
                    try:
                        int_batch_ids = []
                        for rid in batch_ids:
                            try:
                                int_batch_ids.append(int(rid))
                            except (ValueError, TypeError):
                                # Log the problematic ID and skip it
                                logger.warning(f"Skipping non-integer review_id: {rid}")
                                continue
                        if int_batch_ids:
                            logger.info(f"Processing batch with {len(int_batch_ids)} review_ids")
                            
                            rating_query = self.supabase.from_('product_reviews').select(
                                'review_id,product_id,review_text,rating,verified,review_date'
                            ).in_('review_id', int_batch_ids)
                            
                            # Apply ASIN filtering to ensure we only get reviews for our project products
                            rating_query = rating_query.in_('product_id', self.project_asins)
                            
                            rating_result = rating_query.execute()
                            if rating_result.data:
                                logger.info(f"Found {len(rating_result.data)} matching rating records")
                                for item in rating_result.data:
                                    # Use review_id as the key for simpler, more robust lookup
                                    rating_map[str(item['review_id'])] = item
                            else:
                                logger.warning(f"No rating data found for batch_ids: {int_batch_ids}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error converting review_ids to integers: {e}")
                        continue
            
            logger.info(f"Final rating_map size: {len(rating_map)}")
            sample_keys = list(rating_map.keys())[:5]
            logger.info(f"Sample rating_map keys: {sample_keys}")
            
            # Get brand data
            product_ids = list(set([item['product_id'] for item in aspects_result.data]))
            brand_query = self._get_base_product_table().select('platform_id, brand').in_('platform_id', product_ids)
            brand_query = self._apply_base_filters(brand_query)
            
            brand_result = brand_query.execute()
            brand_map = {item['platform_id']: item['brand'] for item in brand_result.data} if brand_result.data else {}
            
            # Combine data
            combined_data = []
            for aspect in aspects_result.data:
                aspect_pk = aspect['aspect_pk']
                category_pk = aspect['category_pk']
                
                # Get category info
                if category_pk and category_pk in categories_data:
                    category_name = categories_data[category_pk]['name']
                else:
                    # Fallback: use parent_group_name or detail_text as category name
                    category_name = aspect['parent_group_name'] or aspect['detail_text'] or 'Unknown'
                
                # Find occurrences for this aspect
                aspect_occurrences = []
                for review_id, occurrences in occurrences_data.items():
                    for occ in occurrences:
                        if occ['aspect_pk'] == aspect_pk:
                            aspect_occurrences.append({
                                'review_id': review_id,
                                'sentiment': occ['sentiment']
                            })
                
                # Create review records for each occurrence
                for occurrence in aspect_occurrences:
                    review_id = occurrence['review_id']
                    sentiment = occurrence['sentiment']
                    
                    # Get rating and review text using only review_id for lookup
                    rating_info = rating_map.get(review_id, {})
                    brand = brand_map.get(aspect['product_id'], 'Unknown')
                    review_text = rating_info.get('review_text', '')
                    
                    # Debug logging
                    if not review_text:
                        logger.warning(f"Empty review_text for review_id: {review_id}, product_id: {aspect['product_id']}, rating_info: {rating_info}")
                        # Log available keys for debugging
                        if len(rating_map) < 20: # Avoid logging huge maps
                            logger.warning(f"Available rating_map keys: {list(rating_map.keys())}")
                    
                    # Convert sentiment from new format to old format
                    if sentiment == '+':
                        sentiment_label = 'positive'
                    elif sentiment == '-':
                        sentiment_label = 'negative'
                    else:
                        sentiment_label = 'neutral'
                    
                    combined_data.append({
                        'product_id': aspect['product_id'],
                        'review_content': review_text,
                        'standardized_aspect': self._capitalize_words(aspect['detail_text']),
                        'aspect_category': self._capitalize_words(category_name),
                        'review_id': review_id,
                        'rating': rating_info.get('rating'),
                        'verified': rating_info.get('verified', False),
                        'review_date': rating_info.get('review_date'),
                        'brand': brand,
                        'sentiment': sentiment_label  # Direct sentiment from new table
                    })
            
            logger.info(f"Retrieved {len(combined_data)} records from new table structure")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error getting review data from new table structure: {e}")
            return []

    def _process_and_group_data(self, review_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Process review data and group by aspect_category."""
        
        grouped_data = {}
        
        for item in review_data:
            category = item['aspect_category'] or 'unknown'
            
            if category not in grouped_data:
                grouped_data[category] = []
            
            # Parse rating (fallback to rating-based sentiment if not available)
            rating_str = item.get('rating', '3.0')
            rating = self._parse_rating(rating_str)
            
            # Use direct sentiment from new table structure if available
            sentiment = item.get('sentiment')
            if not sentiment:
                sentiment = self._get_sentiment(rating)
            
            # Parse date
            date = self._parse_date(item.get('review_date'))
            
            review_item = {
                'id': f"{item['review_id']}_{len(grouped_data[category])}",
                'productId': item['product_id'],
                'text': item['review_content'] or '',
                'sentiment': sentiment,
                'category': category,
                'aspect': self._capitalize_words(item['standardized_aspect']),
                'rating': max(1, min(5, rating)),  # Ensure rating is 1-5
                'verified': bool(item.get('verified', False)),
                'date': date,
                'brand': item.get('brand', 'Unknown')
            }
            
            grouped_data[category].append(review_item)
        
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