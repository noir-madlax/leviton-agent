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
            
            # Apply the same business logic as get_category_statistics:
            # - Include all reviews that mention this category
            # - This matches the tooltip's business logic: total_reviews = unique reviews
            valid_review_keys = set()
            
            for review_key, sentiments in review_sentiments.items():
                # Include review if it has any sentiment (positive, negative, or neutral)
                # This matches the business logic in get_category_statistics
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
            
            # Store the total count before filtering (to match bar chart logic)
            total_reviews_before_filtering = len(deduplicated_reviews)
            
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
            
            # Get category info
            category_info = await self.get_category_info(project_id, category_id)
            
            return {
                'reviews': filtered_reviews,
                'total_count': total_reviews_before_filtering,  # Use total count before filtering to match bar chart
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
    
    def get_categories(
        self, 
        project_id: str, 
        asins: List[str],
        aspect_types: List[str],
        sort_by: str = 'total_reviews',
        sort_direction: str = 'desc',
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get categories with efficient SQL aggregation, sorting, and limiting.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            aspect_types: List of aspect types to filter by
            sort_by: Field to sort by (total_reviews, positive_reviews, negative_reviews, etc.)
            sort_direction: Sort direction (asc, desc)
            limit: Maximum number of categories to return
            
        Returns:
            List of category statistics dictionaries
        """
        try:
            # Expand mapped aspect types
            expanded_aspect_types = []
            for aspect_type in aspect_types:
                if aspect_type in ReviewAnalysisConfig.ASPECT_TYPE_MAP:
                    expanded_aspect_types.extend(ReviewAnalysisConfig.ASPECT_TYPE_MAP[aspect_type])
                else:
                    expanded_aspect_types.append(aspect_type)
            
            # Remove duplicates
            expanded_aspect_types = list(set(expanded_aspect_types))
            
            # Build efficient SQL query with aggregation
            # Use simple string formatting for now (project_id is validated, asins and aspect_types are controlled)
            asins_str = "', '".join(asins)
            aspect_types_str = "', '".join(expanded_aspect_types)
            
            query = f"SELECT category_pk, category_name, category_definition, aspect_type, COUNT(DISTINCT (product_id, review_id)) as total_reviews, COUNT(DISTINCT CASE WHEN sentiment = '+' THEN (product_id, review_id) END) as positive_reviews, COUNT(DISTINCT CASE WHEN sentiment = '-' THEN (product_id, review_id) END) as negative_reviews, COUNT(*) as total_mentions, COUNT(CASE WHEN sentiment = '+' THEN 1 END) as positive_mentions, COUNT(CASE WHEN sentiment = '-' THEN 1 END) as negative_mentions FROM {ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW} WHERE project_id = '{project_id}' AND product_id IN ('{asins_str}') AND aspect_type IN ('{aspect_types_str}') GROUP BY category_pk, category_name, category_definition, aspect_type ORDER BY {sort_by} {sort_direction} LIMIT {limit}"
            
            # Execute query using the safe query RPC function
            result = self.supabase.rpc('execute_safe_query', {
                'query_text': query
            }).execute()
            
            if not result.data:
                logger.info(f"No categories found for project {project_id}")
                return []
            
            # Process results - RPC returns JSONB format
            categories = []
            for row in result.data:
                # Extract the result from JSONB format
                record = row.get('result', {})
                if not record:
                    continue
                total_reviews = record['total_reviews'] or 0
                positive_reviews = record['positive_reviews'] or 0
                negative_reviews = record['negative_reviews'] or 0
                total_mentions = record['total_mentions'] or 0
                positive_mentions = record['positive_mentions'] or 0
                negative_mentions = record['negative_mentions'] or 0
                
                # Calculate ratios
                positive_ratio = (positive_reviews / total_reviews) if total_reviews > 0 else 0.0
                
                category_data = {
                    'category_pk': record['category_pk'],
                    'category_id': record['category_pk'],
                    'category_name': record['category_name'],
                    'definition': record['category_definition'],
                    'aspect_type': record['aspect_type'],
                    'total_reviews': total_reviews,
                    'positive_reviews': positive_reviews,
                    'negative_reviews': negative_reviews,
                    'positive_ratio': positive_ratio,
                    'total_mentions': total_mentions,
                    'positive_mentions': positive_mentions,
                    'negative_mentions': negative_mentions
                }
                categories.append(category_data)
            
            logger.info(f"Retrieved {len(categories)} categories using efficient SQL query")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories efficiently: {e}", exc_info=True)
            return []

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
            # First, get all category IDs for this project and aspect types
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
            
            # Get unique category IDs
            unique_categories = {}
            for record in category_result.data:
                category_pk = record['category_pk']
                if category_pk not in unique_categories:
                    unique_categories[category_pk] = {
                        'category_name': record['category_name'],
                        'category_definition': record['category_definition'],
                        'aspect_type': record['aspect_type']
                    }
            
            logger.info(f"Found {len(unique_categories)} unique categories")
            
            # Query each category individually to avoid hitting the limit
            all_records = []
            for category_pk in unique_categories.keys():
                category_data_query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                    'category_pk, category_name, category_definition, aspect_type, sentiment, review_id, product_id'
                ).eq('project_id', project_id).eq('category_pk', category_pk).in_('product_id', asins)
                
                if aspect_types:
                    category_data_query = category_data_query.in_('aspect_type', expanded_aspect_types)
                
                category_data_result = category_data_query.execute()
                if category_data_result.data:
                    all_records.extend(category_data_result.data)
            
            logger.info(f"Retrieved {len(all_records)} total review records for aggregation")
            
            # Group by category and apply business logic
            category_stats = defaultdict(lambda: {
                'mentions': defaultdict(int),
                'reviews': set(),
                'review_sentiments': defaultdict(set)
            })
            
            # Process all records
            for record in all_records:
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
                # Get category info from unique_categories
                category_info = unique_categories[category_pk]
                
                # Apply business logic for review sentiment classification
                positive_only_reviews = set()
                negative_reviews = set()
                
                for review_key, sentiments in stats['review_sentiments'].items():
                    if '+' in sentiments and '-' not in sentiments:
                        positive_only_reviews.add(review_key)
                    elif '-' in sentiments:
                        negative_reviews.add(review_key)
                
                # Calculate metrics
                total_mentions = stats['mentions']['total']
                positive_mentions = stats['mentions'].get('+', 0)
                negative_mentions = stats['mentions'].get('-', 0)
                total_reviews = len(stats['reviews'])
                positive_reviews = len(positive_only_reviews)
                negative_reviews = len(negative_reviews)
                
                # Calculate positive ratio
                total_sentiment_reviews = positive_reviews + negative_reviews
                positive_ratio = positive_reviews / total_sentiment_reviews if total_sentiment_reviews > 0 else 0.0
                
                cat_data = {
                    'category_pk': category_pk,
                    'category_id': category_pk,
                    'category_name': category_info['category_name'],
                    'definition': category_info['category_definition'],
                    'aspect_type': category_info['aspect_type'],
                    'total_mentions': total_mentions,
                    'positive_mentions': positive_mentions,
                    'negative_mentions': negative_mentions,
                    'total_reviews': total_reviews,
                    'positive_reviews': positive_reviews,
                    'negative_reviews': negative_reviews,
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
                sort_by = options.get('sort_by', 'total_reviews')
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
                elif sort_by == 'positive_reviews':
                    filtered_categories.sort(key=lambda x: x['positive_reviews'], reverse=reverse)
                elif sort_by == 'negative_reviews':
                    filtered_categories.sort(key=lambda x: x['negative_reviews'], reverse=reverse)
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
    ) -> Dict[str, Any]:
        """Get aspect categories with embedded cause analysis.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            aspect_types: List of aspect types to filter by
            options: Options for sorting and filtering, including return_top_cause_categories
            
        Returns:
            Dict containing categories with embedded cause data and aggregated cause summary
        """
        try:
            # Extract sorting and limiting options (handle both camelCase and snake_case)
            sort_by = options.get('sort_by') or options.get('sortBy', 'total_reviews')
            sort_direction = options.get('sort_direction') or options.get('sortDirection', 'desc')
            max_categories = options.get('max_categories') or options.get('maxCategories', ReviewAnalysisConfig.DEFAULT_TOP_CATEGORIES)
            
            # Get categories using efficient SQL query
            categories = self.get_categories(
                project_id=project_id,
                asins=asins,
                aspect_types=aspect_types,
                sort_by=sort_by,
                sort_direction=sort_direction,
                limit=max_categories
            )
            
            if not categories:
                return {'categories': [], 'aggregated_cause_summary': []}
            
            # Check if cause analysis is requested
            cause_options = options.get('return_top_cause_categories')
            if cause_options:
                # Extract top category IDs for cause analysis
                top_category_ids = [cat['category_pk'] for cat in categories]
                
                # Get enhanced cause analysis with embedded structure
                embedded_cause_data, aggregated_summary = await self._get_enhanced_cause_analysis(
                    project_id=project_id,
                    asins=asins,
                    top_aspect_category_ids=top_category_ids,
                    cause_options=cause_options
                )
                
                # Embed cause data into each category
                for category in categories:
                    category_pk = category['category_pk']
                    category['cause_data'] = embedded_cause_data.get(category_pk, [])
                
                result = {
                    'categories': categories,
                    'aggregated_cause_summary': aggregated_summary
                }
            else:
                result = {'categories': categories, 'aggregated_cause_summary': []}
            
            logger.info(f"Retrieved {len(categories)} aspect categories with embedded cause analysis")
            return result
            
        except Exception as e:
            logger.error(f"Error getting aspect categories with metrics: {e}", exc_info=True)
            return {'categories': [], 'aggregated_cause_summary': []}

    async def _get_enhanced_cause_analysis(
        self,
        project_id: str,
        asins: List[str],
        top_aspect_category_ids: List[int],
        cause_options: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get enhanced cause analysis with embedded structure.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            top_aspect_category_ids: List of aspect category IDs to analyze
            cause_options: Options for cause analysis including limits and filters
            
        Returns:
            Tuple of (embedded_cause_data_per_aspect, aggregated_cause_summary)
        """
        try:
            if not top_aspect_category_ids:
                return {}, []
            
            # Get cause analysis parameters
            sentiment_filter = cause_options.get('sentiment')  # Optional: '+', '-', or None for all sentiments
            limit = cause_options.get('limit', 10)  # Single limit for both aggregated and per-aspect causes
            
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
                logger.info(f"No cause data found for enhanced analysis")
                return {}, []
            
            # Get category information for all causes found
            all_cause_pks = set()
            for record in result.data:
                causes = record.get('causes', [])
                for cause in causes:
                    if isinstance(cause, dict):
                        cause_pk = cause.get('category_pk')
                        if cause_pk:
                            all_cause_pks.add(cause_pk)
            
            category_info = await self.get_category_info_batch(project_id, list(all_cause_pks))
            
            # Dual data structures for optimization
            aspect_cause_matrix = defaultdict(lambda: defaultdict(lambda: {
                'reviews': set(),
                'positive_reviews': set(),
                'negative_reviews': set(),
                'aspects': set()  # Set of (aspect_description, sentiment) tuples
            }))
            
            global_cause_stats = defaultdict(lambda: {
                'reviews': set(),
                'positive_reviews': set(),
                'negative_reviews': set(),
                'aspects': set()  # Set of (aspect_description, sentiment) tuples
            })
            
            # Single processing loop for both structures
            for record in result.data:
                aspect_pk = record['category_pk']
                causes = record.get('causes', [])
                sentiment = record['sentiment']
                review_key = (record.get('product_id', 'unknown'), record['review_id'])
                
                if not causes:
                    continue
                
                # Process each cause in the causes array
                for cause in causes:
                    if isinstance(cause, dict):
                        cause_category_pk = cause.get('category_pk')
                        cause_detail_text = cause.get('detail_text', '')
                        cause_parent_group = cause.get('parent_group_name', '')
                        
                        if not cause_category_pk:
                            continue
                        
                        # Format aspect description
                        aspect_description = self._format_aspect_description(cause_parent_group, cause_detail_text)
                        
                        # Update aspect-specific cause data
                        aspect_cause_matrix[aspect_pk][cause_category_pk]['reviews'].add(review_key)
                        aspect_cause_matrix[aspect_pk][cause_category_pk]['aspects'].add((aspect_description, sentiment))
                        
                        if sentiment == '+':
                            aspect_cause_matrix[aspect_pk][cause_category_pk]['positive_reviews'].add(review_key)
                        elif sentiment == '-':
                            aspect_cause_matrix[aspect_pk][cause_category_pk]['negative_reviews'].add(review_key)
                        
                        # Update global cause aggregation
                        global_cause_stats[cause_category_pk]['reviews'].add(review_key)
                        global_cause_stats[cause_category_pk]['aspects'].add((aspect_description, sentiment))
                        
                        if sentiment == '+':
                            global_cause_stats[cause_category_pk]['positive_reviews'].add(review_key)
                        elif sentiment == '-':
                            global_cause_stats[cause_category_pk]['negative_reviews'].add(review_key)
            
            # Format embedded cause data per aspect
            embedded_cause_data = {}
            for aspect_pk, causes in aspect_cause_matrix.items():
                aspect_causes = []
                for cause_pk, cause_data in causes.items():
                    # Calculate review counts
                    total_reviews = len(cause_data['reviews'])
                    positive_reviews = len(cause_data['positive_reviews'])
                    negative_reviews = len(cause_data['negative_reviews'])
                    
                    # Format aspects as simplified objects
                    aspects = [
                        {
                            'aspect_description': desc,
                            'sentiment': sentiment
                        }
                        for desc, sentiment in cause_data['aspects']
                    ]
                    
                    aspect_causes.append({
                        'cause_category_pk': cause_pk,
                        'cause_category_name': category_info.get(cause_pk, {}).get('name', 'Unknown'),
                        'total_reviews': total_reviews,
                        'positive_reviews': positive_reviews,
                        'negative_reviews': negative_reviews,
                        'aspects': aspects
                    })
                
                # Sort by total reviews and apply limit
                aspect_causes.sort(key=lambda x: x['total_reviews'], reverse=True)
                embedded_cause_data[aspect_pk] = aspect_causes[:limit]
            
            # Format aggregated cause summary
            aggregated_summary = []
            for cause_pk, cause_data in global_cause_stats.items():
                # Calculate review counts
                total_reviews = len(cause_data['reviews'])
                total_positive_reviews = len(cause_data['positive_reviews'])
                total_negative_reviews = len(cause_data['negative_reviews'])
                
                # Format aspects as simplified objects
                aspects = [
                    {
                        'aspect_description': desc,
                        'sentiment': sentiment
                    }
                    for desc, sentiment in cause_data['aspects']
                ]
                
                aggregated_summary.append({
                    'cause_category_pk': cause_pk,
                    'cause_category_name': category_info.get(cause_pk, {}).get('name', 'Unknown'),
                    'total_reviews': total_reviews,
                    'total_positive_reviews': total_positive_reviews,
                    'total_negative_reviews': total_negative_reviews,
                    'aspects': aspects
                })
            
            # Sort by total reviews and apply limit
            aggregated_summary.sort(key=lambda x: x['total_reviews'], reverse=True)
            aggregated_summary = aggregated_summary[:limit]
            
            # Add rank to aggregated summary
            for rank, cause in enumerate(aggregated_summary, 1):
                cause['rank'] = rank
            
            logger.info(f"Enhanced cause analysis: {len(embedded_cause_data)} aspects with embedded causes, {len(aggregated_summary)} aggregated causes")
            return embedded_cause_data, aggregated_summary
            
        except Exception as e:
            logger.error(f"Error in enhanced cause analysis: {e}", exc_info=True)
            return {}, []



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
    
 