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
        parent_group_stripped = parent_group.strip() if parent_group else ''
        detail_text_stripped = detail_text.strip() if detail_text else ''
        if parent_group_stripped and detail_text_stripped:
            if parent_group_stripped == detail_text_stripped:
                return detail_text_stripped
            return f"{parent_group_stripped}: {detail_text_stripped}"
        elif detail_text_stripped:
            return detail_text_stripped
        return parent_group_stripped

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
        aspect_types: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get category statistics with mentions, sentiments, etc.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            aspect_types: Optional list of aspect types to filter by
            options: Options for filtering and sorting
            
        Returns:
            List of category statistics dictionaries
        """
        try:
            # Build the base query - get all data in one go
            query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                'category_pk, category_name, category_definition, aspect_type, sentiment, review_id, product_id'
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
                query = query.in_('aspect_type', expanded_aspect_types)
            
            # Get all data in one query (much more efficient than individual category queries)
            result = query.execute()
            
            if not result.data:
                logger.info(f"No categories found for project {project_id}")
                return []
            
            logger.info(f"Retrieved {len(result.data)} review records for aggregation")
            
            # Group by category and apply business logic
            category_stats = defaultdict(lambda: {
                'mentions': defaultdict(int),
                'reviews': set(),
                'review_sentiments': defaultdict(set)
            })
            
            # Process all records
            for record in result.data:
                category_pk = record['category_pk']
                review_key = (record.get('product_id', 'unknown'), record['review_id'])
                sentiment = record['sentiment']
                
                # Count mentions
                category_stats[category_pk]['mentions']['total'] += 1
                category_stats[category_pk]['mentions'][sentiment] += 1
                
                # Track reviews and their sentiments
                category_stats[category_pk]['reviews'].add(review_key)
                category_stats[category_pk]['review_sentiments'][review_key].add(sentiment)
            
            # Apply business logic and create category data
            categories = []
            for category_pk, stats in category_stats.items():
                # Get category info from first record
                first_record = next(r for r in result.data if r['category_pk'] == category_pk)
                
                # Apply business logic for review sentiment classification
                positive_only_reviews = set()
                negative_reviews = set()
                neutral_only_reviews = set()
                
                for review_key, sentiments in stats['review_sentiments'].items():
                    if '+' in sentiments and '-' not in sentiments:
                        positive_only_reviews.add(review_key)
                    elif '-' in sentiments:
                        negative_reviews.add(review_key)
                    elif not ('+' in sentiments or '-' in sentiments):
                        neutral_only_reviews.add(review_key)
                
                # Calculate metrics
                total_mentions = stats['mentions']['total']
                positive_mentions = stats['mentions'].get('+', 0)
                negative_mentions = stats['mentions'].get('-', 0)
                neutral_mentions = total_mentions - positive_mentions - negative_mentions
                total_reviews = len(stats['reviews'])
                positive_reviews = len(positive_only_reviews)
                negative_reviews = len(negative_reviews)
                neutral_reviews = len(neutral_only_reviews)
                
                # Calculate positive ratio
                total_sentiment_reviews = positive_reviews + negative_reviews
                positive_ratio = positive_reviews / total_sentiment_reviews if total_sentiment_reviews > 0 else 0.0
                
                cat_data = {
                    'category_pk': category_pk,
                    'category_id': category_pk,
                    'category_name': first_record['category_name'],
                    'definition': first_record['category_definition'],
                    'aspect_type': first_record['aspect_type'],
                    'total_mentions': total_mentions,
                    'positive_mentions': positive_mentions,
                    'negative_mentions': negative_mentions,
                    'neutral_mentions': neutral_mentions,
                    'total_reviews': total_reviews,
                    'positive_reviews': positive_reviews,
                    'negative_reviews': negative_reviews,
                    'neutral_reviews': neutral_reviews,
                    'positive_ratio': round(positive_ratio, 4)
                }
                categories.append(cat_data)
            
            # Apply filters and sorting inline
            if options:
                # Apply filters
                filtered_categories = categories
                
                min_mentions = options.get('min_mentions')
                if min_mentions is not None:
                    filtered_categories = [cat for cat in filtered_categories if cat['total_mentions'] >= min_mentions]
                
                min_reviews = options.get('min_reviews')
                if min_reviews is not None:
                    filtered_categories = [cat for cat in filtered_categories if cat['total_reviews'] >= min_reviews]
                
                min_positive = options.get('min_positive_mentions')
                if min_positive is not None:
                    filtered_categories = [cat for cat in filtered_categories if cat['positive_mentions'] >= min_positive]
                
                min_negative = options.get('min_negative_mentions')
                if min_negative is not None:
                    filtered_categories = [cat for cat in filtered_categories if cat['negative_mentions'] >= min_negative]
                
                # Apply sorting
                sort_by = options.get('sort_by', 'total_mentions')
                sort_direction = options.get('sort_direction', 'desc')
                reverse = sort_direction == 'desc'
                
                if sort_by == 'mentions' or sort_by == 'total_mentions':
                    filtered_categories.sort(key=lambda x: x['total_mentions'], reverse=reverse)
                elif sort_by == 'reviews' or sort_by == 'total_reviews':
                    filtered_categories.sort(key=lambda x: x['total_reviews'], reverse=reverse)
                elif sort_by == 'positive_mentions':
                    filtered_categories.sort(key=lambda x: x['positive_mentions'], reverse=reverse)
                elif sort_by == 'negative_mentions':
                    filtered_categories.sort(key=lambda x: x['negative_mentions'], reverse=reverse)
                elif sort_by == 'positive_ratio':
                    filtered_categories.sort(key=lambda x: x['positive_ratio'], reverse=reverse)
                
                categories = filtered_categories
            
            # Apply limit
            max_categories = options.get('max_categories', ReviewAnalysisConfig.DEFAULT_TOP_CATEGORIES) if options else ReviewAnalysisConfig.DEFAULT_TOP_CATEGORIES
            categories = categories[:max_categories]
            
            logger.info(f"Retrieved statistics for {len(categories)} categories using optimized approach")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting category statistics (optimized): {e}", exc_info=True)
            return []

    async def get_cause_analysis(
        self,
        project_id: str,
        asins: List[str],
        top_category_ids: List[int],
        sentiment_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get cause analysis for top categories.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            top_category_ids: List of category IDs to analyze causes for
            sentiment_filter: Optional sentiment filter ('+', '-', or None for both)
            limit: Maximum number of cause categories to return (top N across all categories)
            
        Returns:
            List of top N cause categories with aggregated unique review counts across all top aspect categories
        """
        try:
            if not top_category_ids:
                return []
            
            # Build the query to get cause data with review_id for deduplication
            query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                'category_pk, causes, sentiment, review_id, product_id'
            ).eq('project_id', project_id).in_('product_id', asins).in_('category_pk', top_category_ids).not_.is_('causes', 'null')
            
            # Add sentiment filter if provided
            if sentiment_filter:
                query = query.eq('sentiment', sentiment_filter)
            
            # Execute the query
            result = query.execute()
            
            if not result.data:
                logger.info(f"No cause data found for top categories")
                return []
            
            # Process cause data - aggregate unique reviews across all top aspect categories
            cause_stats = defaultdict(lambda: defaultdict(lambda: {'reviews': set(), 'positive_reviews': set(), 'negative_reviews': set()}))  # cause_pk -> {aspect_description -> review_sets}
            cause_names = {}  # cause_pk -> category_name
            
            for record in result.data:
                causes = record.get('causes', [])
                sentiment = record['sentiment']
                review_key = (record.get('product_id', 'unknown'), record['review_id'])
                
                if not causes:
                    continue
                
                # Process each cause in the causes array
                for cause in causes:
                    if isinstance(cause, dict):
                        cause_category_pk = cause.get('category_pk')
                        cause_category_name = cause.get('category_name', 'Unknown')
                        cause_detail_text = cause.get('detail_text', '')
                        cause_parent_group = cause.get('parent_group_name', '')
                        
                        if not cause_category_pk:
                            continue
                        
                        # Format aspect description
                        aspect_description = self._format_aspect_description(cause_parent_group, cause_detail_text)
                        
                        # Store category name for this cause
                        cause_names[cause_category_pk] = cause_category_name
                        
                        # Track unique reviews by cause_pk and aspect_description
                        review_sets = cause_stats[cause_category_pk][aspect_description]
                        review_sets['reviews'].add(review_key)
                        
                        if sentiment == '+':
                            review_sets['positive_reviews'].add(review_key)
                        elif sentiment == '-':
                            review_sets['negative_reviews'].add(review_key)
            
            # Convert to final format and apply ranking
            cause_analysis = []
            for cause_pk, aspect_counts in cause_stats.items():
                # Create list of aspect descriptions with unique review counts for this cause
                aspect_list = []
                total_positive_reviews = set()
                total_negative_reviews = set()
                
                for aspect_desc, review_sets in aspect_counts.items():
                    # Calculate unique review counts for this aspect
                    total_reviews = len(review_sets['reviews'])
                    positive_reviews = len(review_sets['positive_reviews'])
                    negative_reviews = len(review_sets['negative_reviews'])
                    
                    # Apply business logic: if review has both positive and negative sentiment, count only in negative
                    # This is already handled by the set operations above
                    
                    aspect_list.append({
                        'aspect_description': aspect_desc,
                        'total_reviews': total_reviews,
                        'positive_reviews': positive_reviews,
                        'negative_reviews': negative_reviews
                    })
                    
                    # Aggregate for total cause statistics
                    total_positive_reviews.update(review_sets['positive_reviews'])
                    total_negative_reviews.update(review_sets['negative_reviews'])
                
                # Calculate total unique reviews for this cause across all aspects
                total_reviews = sum(len(review_sets['reviews']) for review_sets in aspect_counts.values())
                total_positive_count = len(total_positive_reviews)
                total_negative_count = len(total_negative_reviews)
                
                cause_info = {
                    'category_pk': cause_pk,
                    'category_name': cause_names.get(cause_pk, 'Unknown'),
                    'aspects': aspect_list,
                    'total_reviews': total_reviews,
                    'total_positive_reviews': total_positive_count,
                    'total_negative_reviews': total_negative_count
                }
                cause_analysis.append(cause_info)
            
            # Sort by total reviews (descending) and take top N
            cause_analysis.sort(key=lambda x: x['total_reviews'], reverse=True)
            cause_analysis = cause_analysis[:limit]
            
            # Add rank
            for rank, cause in enumerate(cause_analysis, 1):
                cause['rank'] = rank
            
            logger.info(f"Retrieved top {len(cause_analysis)} cause categories aggregated across all top aspect categories")
            return cause_analysis
            
        except Exception as e:
            logger.error(f"Error getting cause analysis: {e}", exc_info=True)
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
            options: Options for sorting and filtering, including return_top_cause_categories
            
        Returns:
            List of aspect categories with metrics and optional cause analysis
        """
        try:
            # Get category statistics using optimized method (already includes filtering, sorting, and limit)
            categories = await self.get_category_statistics(project_id, asins, aspect_types, options)
            
            if not categories:
                return []
            
            # Check if cause analysis is requested
            cause_options = options.get('return_top_cause_categories')
            if cause_options:
                # Extract top category IDs for cause analysis
                top_category_ids = [cat['category_pk'] for cat in categories]
                
                # Get cause analysis parameters
                sentiment_filter = cause_options.get('sentiment')  # Optional: '+', '-', or None for both
                limit = cause_options.get('limit', 10)
                
                # Get cause analysis for top categories only
                cause_analysis = await self.get_cause_analysis(
                    project_id=project_id,
                    asins=asins,
                    top_category_ids=top_category_ids,
                    sentiment_filter=sentiment_filter,
                    limit=limit
                )
                
                # Add cause analysis to the response (now a single list for all categories)
                # We'll add it to the first category as a shared result, or create a separate field
                if categories:
                    categories[0]['top_cause_categories'] = cause_analysis
                else:
                    # If no categories, create a dummy entry with cause analysis
                    categories.append({'top_cause_categories': cause_analysis})
            
            logger.info(f"Retrieved {len(categories)} aspect categories with metrics")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting aspect categories with metrics: {e}", exc_info=True)
            return []

    async def get_cause_matrix_view_data(
        self,
        project_id: str,
        asins: List[str],
        top_aspect_category_ids: List[int],
        top_cause_category_ids: List[int],
        sentiment_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cause analysis matrix view data.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            top_aspect_category_ids: List of top aspect category IDs (columns)
            top_cause_category_ids: List of top cause category IDs (rows)
            sentiment_filter: Optional sentiment filter ('+', '-', or None for both)
            
        Returns:
            Dict containing matrix view data with aspect categories as columns and cause categories as rows
        """
        try:
            if not top_aspect_category_ids or not top_cause_category_ids:
                logger.warning("No aspect categories or cause categories provided for matrix view")
                return {
                    'aspect_categories': [],
                    'cause_categories': [],
                    'matrix_data': [],
                    'total_aspect_categories': 0,
                    'total_cause_categories': 0
                }
            
            # Build the query to get cause data with review_id for deduplication
            query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                'category_pk, causes, sentiment, review_id, product_id'
            ).eq('project_id', project_id).in_('product_id', asins).in_('category_pk', top_aspect_category_ids).not_.is_('causes', 'null')
            
            # Add sentiment filter if provided
            if sentiment_filter:
                query = query.eq('sentiment', sentiment_filter)
            
            # Execute the query
            result = query.execute()
            
            if not result.data:
                logger.info(f"No cause data found for matrix view")
                return {
                    'aspect_categories': [],
                    'cause_categories': [],
                    'matrix_data': [],
                    'total_aspect_categories': 0,
                    'total_cause_categories': 0
                }
            
            # Get category information for both aspect and cause categories
            all_category_ids = top_aspect_category_ids + top_cause_category_ids
            category_info = await self.get_category_info_batch(project_id, all_category_ids)
            
            # Process cause data to build matrix
            matrix_data = defaultdict(lambda: defaultdict(lambda: {
                'positive_reviews': set(),
                'negative_reviews': set(),
                'total_reviews': set()
            }))
            
            for record in result.data:
                aspect_category_pk = record['category_pk']  # This is the aspect category (column)
                causes = record.get('causes', [])
                sentiment = record['sentiment']
                review_key = (record.get('product_id', 'unknown'), record['review_id'])
                
                if not causes:
                    continue
                
                # Process each cause in the causes array
                for cause in causes:
                    if isinstance(cause, dict):
                        cause_category_pk = cause.get('category_pk')
                        
                        if not cause_category_pk or cause_category_pk not in top_cause_category_ids:
                            continue
                        
                        # Track unique reviews for this aspect-cause combination
                        cell_data = matrix_data[aspect_category_pk][cause_category_pk]
                        cell_data['total_reviews'].add(review_key)
                        
                        if sentiment == '+':
                            cell_data['positive_reviews'].add(review_key)
                        elif sentiment == '-':
                            cell_data['negative_reviews'].add(review_key)
            
            # Build aspect categories (columns)
            aspect_categories = []
            for category_pk in top_aspect_category_ids:
                cat_info = category_info.get(category_pk, {})
                aspect_categories.append({
                    'category_pk': category_pk,
                    'category_name': cat_info.get('name', 'Unknown Category'),
                    'definition': cat_info.get('definition', '')
                })
            
            # Build cause categories (rows)
            cause_categories = []
            for category_pk in top_cause_category_ids:
                cat_info = category_info.get(category_pk, {})
                cause_categories.append({
                    'category_id': category_pk,
                    'category_name': cat_info.get('name', 'Unknown Category'),
                    'definition': cat_info.get('definition', '')
                })
            
            # Build matrix data in competitor-style format
            # Each cause category is a "product" with aspect data for each aspect category
            cause_aspect_data = []
            for cause_category_pk in top_cause_category_ids:
                cause_data = {
                    'cause_category_id': cause_category_pk,
                    'cause_category_name': category_info.get(cause_category_pk, {}).get('name', 'Unknown Category'),
                    'aspect_data': []
                }
                
                for aspect_category_pk in top_aspect_category_ids:
                    cell_data = matrix_data[aspect_category_pk][cause_category_pk]
                    
                    # Calculate unique review counts
                    total_reviews = len(cell_data['total_reviews'])
                    positive_reviews = len(cell_data['positive_reviews'])
                    negative_reviews = len(cell_data['negative_reviews'])
                    
                    cause_data['aspect_data'].append({
                        'category_pk': aspect_category_pk,
                        'category_name': category_info.get(aspect_category_pk, {}).get('name', 'Unknown Category'),
                        'total_reviews': total_reviews,
                        'positive_reviews': positive_reviews,
                        'negative_reviews': negative_reviews
                    })
                
                cause_aspect_data.append(cause_data)
            
            result = {
                'aspect_categories': aspect_categories,
                'cause_aspect_data': cause_aspect_data,
                'total_aspect_categories': len(aspect_categories),
                'total_cause_categories': len(cause_aspect_data)
            }
            
            logger.info(f"Cause matrix view returned data for {len(aspect_categories)} aspect categories and {len(cause_categories)} cause categories")
            return result
            
        except Exception as e:
            logger.error(f"Error getting cause matrix view data: {e}", exc_info=True)
            return {
                'aspect_categories': [],
                'cause_categories': [],
                'matrix_data': [],
                'total_aspect_categories': 0,
                'total_cause_categories': 0
            }

    async def get_category_info_batch(self, project_id: str, category_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Get category information for multiple categories.
        
        Args:
            project_id: Project ID for filtering
            category_ids: List of category IDs to get info for
            
        Returns:
            Dictionary mapping category_id to category information
        """
        try:
            result = self.supabase.table('review_analysis_aspect_categories').select(
                'category_pk, name, definition, aspect_type, stage'
            ).eq('project_id', project_id).in_('category_pk', category_ids).execute()
            
            category_info = {}
            for record in result.data:
                category_info[record['category_pk']] = {
                    'name': record['name'],
                    'definition': record['definition'],
                    'aspect_type': record['aspect_type'],
                    'stage': record['stage']
                }
            
            logger.info(f"Retrieved category info for {len(category_info)} categories")
            return category_info
            
        except Exception as e:
            logger.error(f"Error getting category info batch: {e}", exc_info=True)
            return {}
    
 