"""Shared data service for review analysis database operations."""

import logging
from typing import List, Dict, Any, Optional
from supabase import Client

from .constants import ReviewAnalysisConfig
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReviewDataService:
    """Shared service for review data operations."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def get_reviews_by_category(
        self, 
        project_id: str, 
        category_id: int, 
        asins: List[str],
        sort_by: str = "review_id",
        sort_order: str = "desc",
        aspect_types: Optional[List[str]] = None,
        sentiment_filter: Optional[str] = None,
        rating_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get deduplicated reviews for a category with sorting and aspect aggregation.
        
        Args:
            project_id: Project ID for filtering
            category_id: Category ID to filter by
            asins: List of ASINs to filter by
            sort_by: Sort field
            sort_order: Sort direction
            
        Returns:
            Dictionary containing deduplicated reviews with aspect aggregation
        """
        try:
            # Build the base query - use the same query as get_category_statistics
            query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                'review_id, review_title, review_text, rating, verified, review_date, '
                'sentiment, sentiment_label, aspect_description, category_name, '
                'category_definition, aspect_type, parent_group_name, detail_text, '
                'product_id, title, brand, product_url'
            ).eq('project_id', project_id).eq('category_pk', category_id).in_('product_id', asins)
            
            # Apply aspect type filter if provided
            if aspect_types:
                # Expand mapped aspect types
                expanded_aspect_types = []
                for aspect_type in aspect_types:
                    if aspect_type in ReviewAnalysisConfig.ASPECT_TYPE_MAP:
                        expanded_aspect_types.extend(ReviewAnalysisConfig.ASPECT_TYPE_MAP[aspect_type])
                    else:
                        expanded_aspect_types.append(aspect_type)
                
                # Remove duplicates
                expanded_aspect_types = list(set(expanded_aspect_types))
                query = query.in_('aspect_type', expanded_aspect_types)
            
            # Apply sorting
            if sort_by == 'date':
                query = query.order('review_date', desc=(sort_order == 'desc'))
            elif sort_by == 'rating':
                query = query.order('rating', desc=(sort_order == 'desc'))
            elif sort_by == 'sentiment':
                query = query.order('sentiment', desc=(sort_order == 'desc'))
            else:
                # Default sort by review_id
                query = query.order('review_id', desc=(sort_order == 'desc'))
            
            # Get all data (no pagination at this level since we need to deduplicate)
            result = query.execute()     
            if not result.data:
                logger.info(f"No reviews found for project {project_id}, category {category_id}")
                return {
                    'reviews': [],
                    'total_count': 0,
                    'category_info': None
                }
            
            logger.info(f"Retrieved {len(result.data)} review records from database")
            
            # Group by review to analyze sentiment patterns
            review_sentiments = defaultdict(set)
            review_data = defaultdict(list)
            
            for record in result.data:
                review_key = (record.get('product_id', 'unknown'), record['review_id'])
                sentiment = record['sentiment']
                review_sentiments[review_key].add(sentiment)
                review_data[review_key].append(record)
            
            # Apply the same business logic as tooltip:
            # - Include all reviews with any sentiment (positive, negative, or neutral)
            # - This matches the tooltip's business logic: total_reviews = unique reviews
            valid_review_keys = set()
            
            for review_key, sentiments in review_sentiments.items():
                # Include review if it has any sentiment (positive, negative, or neutral)
                if sentiments:  # Any sentiment means the review is valid
                    valid_review_keys.add(review_key)
            # Create deduplicated reviews only for valid reviews
            deduplicated_reviews = []
            for review_key in valid_review_keys:
                review_occurrences = review_data[review_key]
                base_review = review_occurrences[0]
                aspects = []
                for occurrence in review_occurrences:
                    aspect_description = self._format_aspect_description(
                        occurrence.get('parent_group_name', ''),
                        occurrence.get('detail_text', '')
                    )
                    aspect = {
                        'aspect_description': aspect_description,
                        'sentiment': occurrence['sentiment'],
                        'aspect_type': occurrence['aspect_type']
                    }
                    aspects.append(aspect)
                deduplicated_review = {
                    'review_id': base_review['review_id'],
                    'review_title': base_review.get('review_title'),
                    'review_text': base_review['review_text'],
                    'rating': self._transform_rating(base_review.get('rating')),
                    'verified': base_review.get('verified'),
                    'review_date': base_review.get('review_date'),
                    'product_id': base_review.get('product_id'),
                    'title': base_review.get('title'),
                    'brand': base_review.get('brand'),
                    'product_url': base_review.get('product_url'),
                    'aspects': aspects,
                    'category_name': base_review.get('category_name'),
                    'category_definition': base_review.get('category_definition'),
                    'aspect_type': base_review.get('aspect_type')
                }
                deduplicated_reviews.append(deduplicated_review)
            
            # Apply sentiment and rating filters
            filtered_reviews = []
            for review in deduplicated_reviews:
                # Apply sentiment filter
                if sentiment_filter:
                    # Check if any aspect has the required sentiment
                    review_sentiments = {aspect['sentiment'] for aspect in review['aspects']}
                    if sentiment_filter == 'positive' and 'positive' not in review_sentiments:
                        continue
                    elif sentiment_filter == 'negative' and 'negative' not in review_sentiments:
                        continue
                
                # Apply rating filter
                if rating_filter and review.get('rating'):
                    rating = review['rating']
                    if rating_filter == 'high' and rating < 4:
                        continue
                    elif rating_filter == 'mid' and rating != 3:
                        continue
                    elif rating_filter == 'low' and rating > 2:
                        continue
                
                filtered_reviews.append(review)
            
            # Use filtered reviews instead of all deduplicated reviews
            deduplicated_reviews = filtered_reviews
            
            # Get category info
            category_info = await self.get_category_info(project_id, category_id)
            
            return {
                'reviews': deduplicated_reviews,
                'total_count': len(deduplicated_reviews),
                'category_info': category_info
            }
            
        except Exception as e:
            logger.error(f"Error getting reviews by category: {e}", exc_info=True)
            return {
                'reviews': [],
                'total_count': 0,
                'category_info': None
            }

    def _deduplicate_and_aggregate_reviews(self, reviews_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate reviews and aggregate aspects for each review.
        
        Args:
            reviews_data: Raw review data from database
            
        Returns:
            List of deduplicated reviews with aggregated aspects
        """
        from collections import defaultdict
        
        # First group by product_id
        product_groups = defaultdict(list)
        for review in reviews_data:
            product_id = review.get('product_id', 'unknown')
            product_groups[product_id].append(review)
        
        deduplicated_reviews = []
        
        # Process each product group
        for product_id, product_reviews in product_groups.items():
            # Within each product, group by review_id to deduplicate
            review_groups = defaultdict(list)
            for review in product_reviews:
                review_id = review['review_id']
                review_groups[review_id].append(review)
            
            # Process each unique review within this product
            for review_id, review_occurrences in review_groups.items():
                # Use the first occurrence for basic review info
                base_review = review_occurrences[0]
                
                # Aggregate aspects from all occurrences
                aspects = []
                for occurrence in review_occurrences:
                    # Format aspect description based on parent_group_name and detail_text
                    parent_group = occurrence.get('parent_group_name', '')
                    detail_text = occurrence.get('detail_text', '')
                    
                    aspect_description = self._format_aspect_description(parent_group, detail_text)
                    
                    aspect = {
                        'aspect_description': aspect_description,
                        'sentiment': occurrence['sentiment'],
                        'aspect_type': occurrence['aspect_type']
                    }
                    aspects.append(aspect)
                
                # Transform rating from string to integer if needed
                rating = self._transform_rating(base_review.get('rating'))
                
                # Create deduplicated review with aggregated aspects
                deduplicated_review = {
                    'review_id': review_id,
                    'review_title': base_review.get('review_title'),
                    'review_text': base_review['review_text'],
                    'rating': rating,
                    'verified': base_review.get('verified'),
                    'review_date': base_review.get('review_date'),
                    'aspects': aspects,  # All aspects mentioned in this review
                    'category_name': base_review['category_name'],
                    'category_definition': base_review.get('category_definition'),
                    'aspect_type': base_review['aspect_type']
                }
                
                # Add product information if available
                if 'product_id' in base_review:
                    deduplicated_review['product_id'] = base_review['product_id']
                    deduplicated_review['title'] = base_review.get('title')
                    deduplicated_review['brand'] = base_review.get('brand')
                    deduplicated_review['product_url'] = base_review.get('product_url')
                
                deduplicated_reviews.append(deduplicated_review)
        
        logger.info(f"Deduplicated {len(reviews_data)} review occurrences into {len(deduplicated_reviews)} unique reviews across {len(product_groups)} products")
        return deduplicated_reviews

    def _format_aspect_description(self, parent_group: str, detail_text: str) -> str:
        """Format aspect description from parent_group_name and detail_text.
        
        Args:
            parent_group: Parent group name
            detail_text: Detail text
            
        Returns:
            Formatted aspect description
        """
        if detail_text and detail_text.strip():
            return f"{parent_group}: {detail_text.strip()}"
        return parent_group

    def _transform_rating(self, rating) -> int:
        """Transform rating to integer.
        
        Args:
            rating: Rating value (could be string or int)
            
        Returns:
            Integer rating
        """
        if rating is None:
            return 0
        
        # Handle "X.X out of 5 stars" format
        if isinstance(rating, str) and 'out of' in rating:
            try:
                rating_value = float(rating.split(' out of')[0])
                return int(round(rating_value))
            except (ValueError, IndexError):
                return 0
        
        # Handle simple numeric conversion
        try:
            if isinstance(rating, str):
                return int(round(float(rating)))
            return int(rating)
        except (ValueError, TypeError):
            return 0



    async def get_category_info(self, project_id: str, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category information for the specified category ID.
        
        Args:
            project_id: Project ID for filtering
            category_id: Category ID to get info for
            
        Returns:
            Category information dict or None if not found
        """
        try:
            result = self.supabase.table('review_analysis_aspect_categories').select(
                'category_pk, name, definition, aspect_type, stage'
            ).eq('category_pk', category_id).eq('project_id', project_id).execute()
            
            if result.data:
                category_data = result.data[0]
                return {
                    'category_pk': category_data['category_pk'],
                    'name': category_data['name'],
                    'definition': category_data['definition'],
                    'aspect_type': category_data['aspect_type'],
                    'stage': category_data['stage']
                }
            
            logger.warning(f"Category {category_id} not found for project {project_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting category info: {e}", exc_info=True)
            return None
    
    async def get_category_statistics(
        self, 
        project_id: str, 
        asins: List[str],
        aspect_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get category statistics with mentions, sentiments, etc.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            aspect_types: Optional list of aspect types to filter by
            
        Returns:
            List of category statistics dictionaries
        """
        try:
            # First, get all unique categories for this project and aspect types
            category_query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                'category_pk, category_name, category_definition, aspect_type'
            ).eq('project_id', project_id).in_('product_id', asins)
            
            # Apply aspect type filter if provided
            if aspect_types:
                # Expand mapped aspect types
                expanded_aspect_types = []
                for aspect_type in aspect_types:
                    if aspect_type in ReviewAnalysisConfig.ASPECT_TYPE_MAP:
                        expanded_aspect_types.extend(ReviewAnalysisConfig.ASPECT_TYPE_MAP[aspect_type])
                    else:
                        expanded_aspect_types.append(aspect_type)
                
                # Remove duplicates
                expanded_aspect_types = list(set(expanded_aspect_types))
                category_query = category_query.in_('aspect_type', expanded_aspect_types)
            
            # Get unique categories
            category_result = category_query.execute()
            
            if not category_result.data:
                logger.info(f"No categories found for project {project_id}")
                return []
            
            # Get unique categories (remove duplicates)
            unique_categories = {}
            for item in category_result.data:
                category_pk = item['category_pk']
                if category_pk not in unique_categories:
                    unique_categories[category_pk] = {
                        'category_pk': category_pk,
                        'category_name': item['category_name'],
                        'definition': item['category_definition'],
                        'aspect_type': item['aspect_type']
                    }
            
            logger.info(f"Found {len(unique_categories)} unique categories")
            
            # Process each category individually (same logic as get_reviews_by_category)
            categories = []
            for category_pk, category_info in unique_categories.items():
                # Build the same query as get_reviews_by_category for this specific category
                query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                    'category_pk, category_name, category_definition, aspect_type, sentiment, review_id, product_id'
                ).eq('project_id', project_id).eq('category_pk', category_pk).in_('product_id', asins)
                
                # Apply aspect type filter if provided
                if aspect_types:
                    # Expand mapped aspect types
                    expanded_aspect_types = []
                    for aspect_type in aspect_types:
                        if aspect_type in ReviewAnalysisConfig.ASPECT_TYPE_MAP:
                            expanded_aspect_types.extend(ReviewAnalysisConfig.ASPECT_TYPE_MAP[aspect_type])
                        else:
                            expanded_aspect_types.append(aspect_type)
                    
                    # Remove duplicates
                    expanded_aspect_types = list(set(expanded_aspect_types))
                    query = query.in_('aspect_type', expanded_aspect_types)
                
                result = query.execute()
                
                if not result.data:
                    continue
                
                # Group by review to analyze sentiment patterns
                review_sentiments = defaultdict(set)
                total_mentions = 0
                positive_mentions = 0
                negative_mentions = 0
                neutral_mentions = 0
                
                for record in result.data:
                    review_key = (record.get('product_id', 'unknown'), record['review_id'])
                    sentiment = record['sentiment']
                    review_sentiments[review_key].add(sentiment)
                    
                    # Count mentions
                    total_mentions += 1
                    if sentiment == '+':
                        positive_mentions += 1
                    elif sentiment == '-':
                        negative_mentions += 1
                    else:
                        neutral_mentions += 1
                
                # Apply the same business logic as get_reviews_by_category
                valid_review_keys = set()
                positive_reviews = set()
                negative_reviews = set()
                neutral_reviews = set()
                
                for review_key, sentiments in review_sentiments.items():
                    # Include review if it has any sentiment (positive, negative, or neutral)
                    if sentiments:  # Any sentiment means the review is valid
                        valid_review_keys.add(review_key)
                        
                        # Add to sentiment-specific sets
                        if '+' in sentiments:
                            positive_reviews.add(review_key)
                        if '-' in sentiments:
                            negative_reviews.add(review_key)
                        if not ('+' in sentiments or '-' in sentiments):
                            neutral_reviews.add(review_key)
                
                # Calculate final counts with business logic:
                # - If a review has both positive and negative sentiment, count it only as negative
                # - Total reviews = unique reviews (no double counting)
                positive_only_reviews = positive_reviews - negative_reviews
                negative_reviews_final = negative_reviews  # Includes mixed sentiment reviews
                neutral_only_reviews = neutral_reviews - (positive_reviews | negative_reviews)
                
                positive_count = len(positive_only_reviews)
                negative_count = len(negative_reviews_final)
                neutral_count = len(neutral_only_reviews)
                total_count = len(valid_review_keys)  # Total unique reviews
                
                # Calculate positive ratio based on unique reviews
                total_sentiment_reviews = positive_count + negative_count
                if total_sentiment_reviews > 0:
                    positive_ratio = positive_count / total_sentiment_reviews
                else:
                    positive_ratio = 0.0
                
                # Create category data
                cat_data = {
                    'category_pk': category_pk,
                    'category_id': category_pk,
                    'category_name': category_info['category_name'],
                    'definition': category_info['definition'],
                    'aspect_type': category_info['aspect_type'],
                    'total_mentions': total_mentions,
                    'positive_mentions': positive_mentions,
                    'negative_mentions': negative_mentions,
                    'neutral_mentions': neutral_mentions,
                    'total_reviews': total_count,
                    'positive_reviews': positive_count,
                    'negative_reviews': negative_count,
                    'neutral_reviews': neutral_count,
                    'positive_ratio': positive_ratio
                }
                
                categories.append(cat_data)
            
            logger.info(f"Retrieved statistics for {len(categories)} categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting category statistics: {e}", exc_info=True)
            return []
    
    async def get_aspect_categories_with_metrics(
        self,
        project_id: str,
        asins: List[str],
        aspect_types: List[str],
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get aspect categories with filtering and sorting options.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            aspect_types: List of aspect types to filter by
            options: Options for sorting and filtering
            
        Returns:
            List of aspect categories with metrics
        """
        try:
            # Get category statistics
            categories = await self.get_category_statistics(project_id, asins, aspect_types)
            
            if not categories:
                return []
            
            # Apply filters
            categories = self._apply_category_filters(categories, options)
            
            # Apply sorting
            categories = self._apply_category_sorting(categories, options)
            
            # Apply limit
            max_categories = options.get('max_categories', ReviewAnalysisConfig.DEFAULT_TOP_CATEGORIES)
            categories = categories[:max_categories]
            
            logger.info(f"Retrieved {len(categories)} aspect categories after filtering and sorting")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting aspect categories with metrics: {e}", exc_info=True)
            return []
    
    def _apply_category_filters(self, categories: List[Dict[str, Any]], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply category filters based on options.
        
        Args:
            categories: List of category data
            options: Filter options
            
        Returns:
            Filtered list of categories
        """
        filtered_categories = categories
        
        # Filter by minimum mentions
        min_mentions = options.get('min_mentions')
        if min_mentions is not None:
            filtered_categories = [cat for cat in filtered_categories if cat['total_mentions'] >= min_mentions]
        
        # Filter by minimum reviews
        min_reviews = options.get('min_reviews')
        if min_reviews is not None:
            filtered_categories = [cat for cat in filtered_categories if cat['total_reviews'] >= min_reviews]
        
        # Filter by minimum positive mentions
        min_positive = options.get('min_positive_mentions')
        if min_positive is not None:
            filtered_categories = [cat for cat in filtered_categories if cat['positive_mentions'] >= min_positive]
        
        # Filter by minimum negative mentions
        min_negative = options.get('min_negative_mentions')
        if min_negative is not None:
            filtered_categories = [cat for cat in filtered_categories if cat['negative_mentions'] >= min_negative]
        
        return filtered_categories
    
    def _apply_category_sorting(self, categories: List[Dict[str, Any]], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply category sorting based on options.
        
        Args:
            categories: List of category data
            options: Sort options
            
        Returns:
            Sorted list of categories
        """
        sort_by = options.get('sort_by', 'total_mentions')
        sort_direction = options.get('sort_direction', 'desc')
        
        reverse = sort_direction == 'desc'
        
        if sort_by == 'mentions' or sort_by == 'total_mentions':
            categories.sort(key=lambda x: x['total_mentions'], reverse=reverse)
        elif sort_by == 'reviews' or sort_by == 'total_reviews':
            categories.sort(key=lambda x: x['total_reviews'], reverse=reverse)
        elif sort_by == 'positive_mentions':
            categories.sort(key=lambda x: x['positive_mentions'], reverse=reverse)
        elif sort_by == 'negative_mentions':
            categories.sort(key=lambda x: x['negative_mentions'], reverse=reverse)
        elif sort_by == 'positive_ratio':
            categories.sort(key=lambda x: x['positive_ratio'], reverse=reverse)
        
        return categories 