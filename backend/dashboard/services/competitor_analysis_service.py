"""Competitor Analysis Service for Dashboard module.

This service handles competitor analysis data retrieval with project ASIN filtering.
Migrated from frontend logic to ensure consistent project-based filtering.
"""

import logging
from typing import Dict, List, Any, Literal, Optional
import re

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class CompetitorAnalysisService(BaseDashboardService):
    """Service for competitor analysis data with focused 6-product comparison.
    
    Updated to use new table structure:
    - review_analysis_aspects
    - review_analysis_aspect_categories
    - review_analysis_aspect_occurrences
    
    Provides competitor analysis data for 6 core products:
    - Leviton D26HD, Leviton D215S, Lutron Caseta Diva
    - TP Link Switch, Leviton DSL06, Lutron Diva
    
    This replaces the frontend getCompetitorAnalysisData() method with proper
    focused product comparison and enhanced sentiment analysis.
    """

    # Default core products for competitor analysis when no specific ASINs are provided
    DEFAULT_COMPETITOR_ASINS = [
        'B00NG0ELL0',  # Leviton DSL06 - Mid-tier brand representative
        'B0BVKZLT3B',  # Leviton D215S - Mid-tier brand representative
        'B0BVKYKKRK',  # Leviton D26HD - Mid-tier brand representative
        'B0BSHKS26L',  # Lutron Caseta Diva - Mid-tier brand representative
        'B085D8M2MR',  # Lutron Diva - Mid-tier brand representative
        "B01EZV35QU",  # TP Link Switch
    
    ]

    # ASIN to display name mapping (consistent with frontend)
    ASIN_TO_DISPLAY_NAME = {
        'B08PKMT2DV': 'Philips Hue Smart',
        'B0771BC2YH': 'CLOUDY BAY Dimmer',
        'B004DZONXI': 'Lutron Credenza',
        'B07SXDFH38': 'Feit Electric Smart',
        'B073H9Y7SH': 'Leviton Trimatron',
        'B00NG0ELL0': 'Leviton DSL06',
        'B0BVKZLT3B': 'Leviton D215S',
        'B0BVKYKKRK': 'Leviton D26HD',
        'B0BSHKS26L': 'Lutron Caseta Diva',
        'B01EZV35QU': 'TP Link Switch',
        'B085D8M2MR': 'Lutron Diva',
        'B0BTMWZH3K': 'Kasa HomeKit'
    }

    def __init__(self, project_id: str, selected_asins: Optional[List[str]] = None):
        """Initialize CompetitorAnalysisService with optional custom ASINs.
        
        Args:
            project_id: The project ID for filtering
            selected_asins: Optional list of ASINs to analyze. If None, uses default core ASINs.
        """
        super().__init__(project_id)
        self.selected_asins = selected_asins or self.DEFAULT_COMPETITOR_ASINS

    def _capitalize_words(self, text: str) -> str:
        """Capitalize the first letter of each word in the text."""
        if not text:
            return text
        return ' '.join(word.capitalize() for word in str(text).split())

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
        """Get product information for selected competitor products."""
        query = self._get_base_product_table().select('platform_id, title, reviews_count')
        query = self._apply_base_filters(query)
        # Use selected ASINs for comparison
        query = query.in_('platform_id', self.selected_asins)
        # Apply category filtering if set
        query = self._apply_category_filter(query)
        result = query.execute()
        
        if result.data:
            logger.info(f"Retrieved {len(result.data)} selected competitor products")
            return result.data
        else:
            logger.warning("No product information found for selected competitor ASINs")
            return []

    def _get_analysis_data(self) -> List[Dict[str, Any]]:
        """Get review analysis data from new table structure filtered by selected competitor ASINs."""
        
        try:
            # Apply category filtering to selected ASINs if category filters are set
            filtered_asins = self.selected_asins
            if self.category_filters:
                # Get ASINs that match both selected ASINs and category filter
                product_filter_query = self._get_base_product_table().select('platform_id')
                product_filter_query = self._apply_base_filters(product_filter_query)
                product_filter_query = product_filter_query.in_('platform_id', self.selected_asins)
                product_filter_query = self._apply_category_filter(product_filter_query)
                product_filter_result = product_filter_query.execute()
                
                if product_filter_result.data:
                    filtered_asins = [item['platform_id'] for item in product_filter_result.data]
                    logger.info(f"🔍 Category filters applied to competitor analysis: {len(filtered_asins)} products after filtering")
                else:
                    logger.warning(f"No competitor products found matching category filters: {self.category_filters}")
                    return []
            
            # Get aspects filtered by project and filtered competitor ASINs
            aspects_query = self.supabase.from_('review_analysis_aspects').select('''
                aspect_pk,
                product_id,
                aspect_type,
                detail_text,
                parent_group_name,
                category_pk
            ''').eq('project_id', self.project_id).in_('product_id', filtered_asins)
            
            aspects_result = aspects_query.execute()
            
            if not aspects_result.data:
                logger.warning("No aspects data found for selected competitor ASINs")
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
                
                # Group occurrences by aspect_pk
                for occurrence in all_occurrences:
                    aspect_pk = occurrence['aspect_pk']
                    if aspect_pk not in occurrences_data:
                        occurrences_data[aspect_pk] = []
                    
                    occurrences_data[aspect_pk].append({
                        'sentiment': occurrence['sentiment'],
                        'review_id': occurrence['review_id']
                    })
            
            # Combine data to match old format
            combined_data = []
            for aspect in aspects_result.data:
                aspect_pk = aspect['aspect_pk']
                category_pk = aspect['category_pk']
                
                # Skip aspects without proper category classification
                if not category_pk or category_pk not in categories_data:
                    continue  # Only use properly categorized aspects
                
                # Get category info
                category_info = categories_data[category_pk]
                category_name = self._capitalize_words(category_info['name'])
                aspect_type = category_info['aspect_type']
                
                # Map aspect_type to old format
                if aspect_type == 'use':
                    aspect_category = 'use_case'
                elif aspect_type == 'phy':
                    aspect_category = 'physical'
                elif aspect_type == 'perf':
                    aspect_category = 'performance'
                else:
                    aspect_category = 'unknown'
                
                # Add records for each occurrence
                aspect_occurrences = occurrences_data.get(aspect_pk, [])
                for occurrence in aspect_occurrences:
                    combined_data.append({
                        'product_id': aspect['product_id'],
                        'aspect_category': aspect_category,
                        'standardized_aspect': category_name,  # Use category name for proper aggregation
                        'category_name': category_name,  # Add category name for proper use case aggregation
                        'review_id': occurrence['review_id'],
                        'sentiment': occurrence['sentiment']  # Direct sentiment from new table
                    })
            
            logger.info(f"Retrieved {len(combined_data)} analysis records for core competitors from new table structure")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error getting analysis data from new table structure: {e}")
            return []

    def _get_rating_data(self) -> List[Dict[str, Any]]:
        """Get rating data for sentiment analysis."""
        # Apply category filtering to selected ASINs if category filters are set
        filtered_asins = self.selected_asins
        if self.category_filters:
            # Get ASINs that match both selected ASINs and category filter
            product_filter_query = self._get_base_product_table().select('platform_id')
            product_filter_query = self._apply_base_filters(product_filter_query)
            product_filter_query = product_filter_query.in_('platform_id', self.selected_asins)
            product_filter_query = self._apply_category_filter(product_filter_query)
            product_filter_result = product_filter_query.execute()
            
            if product_filter_result.data:
                filtered_asins = [item['platform_id'] for item in product_filter_result.data]
            else:
                return []  # No products match category filter
        
        query = self.supabase.from_('product_reviews').select(
            'product_id, review_id, rating'
        ).in_('product_id', filtered_asins).neq('rating', None)
        
        result = query.execute()
        
        if result.data:
            logger.info(f"Retrieved {len(result.data)} rating records for selected competitors")
            return result.data
        else:
            logger.warning("No rating data found for core competitor ASINs")
            return []

    def _process_competitor_data(self, product_info: List[Dict], analysis_data: List[Dict], rating_data: List[Dict]) -> Dict[str, Any]:
        """Process competitor analysis data."""
        
        # Build product mapping using predefined display names
        asin_to_product = {}
        
        for product in product_info:
            asin = product['platform_id']
            # Use predefined display name for consistency with frontend
            display_name = self.ASIN_TO_DISPLAY_NAME.get(asin, asin)
            asin_to_product[asin] = display_name
        
        # Calculate actual project review counts from analysis_data (not Amazon totals)
        product_total_reviews = {}
        product_review_ids = {}
        
        # Initialize counters for all products using ASIN as key
        for asin in asin_to_product.keys():
            product_review_ids[asin] = set()
        
        # Count unique review_ids for each product from actual analysis data
        for item in analysis_data:
            product_asin = item['product_id']
            review_id = item.get('review_id')
            
            if product_asin and review_id:
                product_review_ids[product_asin].add(review_id)
        
        # Convert sets to counts using ASIN as key
        for product_asin, review_id_set in product_review_ids.items():
            product_total_reviews[product_asin] = len(review_id_set)

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

        target_products = list(asin_to_product.keys())

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

            # Get sentiment - use direct sentiment from new table if available
            if 'sentiment' in item:
                # Convert new table sentiment format to old format
                raw_sentiment = item['sentiment']
                if raw_sentiment == '+':
                    sentiment = 'positive'
                elif raw_sentiment == '-':
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
            else:
                # Fallback to rating-based sentiment
                rating_key = f"{product_asin}_{item['review_id']}"
                rating = self._parse_rating(rating_map.get(rating_key, '3.0'))
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

            # Process use_case categories - FIXED: use category_name instead of detail_text
            else:
                # Use category name for proper "Main Use Cases" aggregation
                use_case = item.get('category_name', item['standardized_aspect'])
                
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
            
            for product_asin, product_name in asin_to_product.items():
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
                        'product': product_asin,
                        'category': display_category,
                        'categoryType': category_data['categoryType'],
                        'mentions': product_data['total'],
                        'satisfactionRate': round(satisfaction_rate, 1),
                        'positiveCount': positive_count,
                        'negativeCount': negative_count,
                        'totalReviews': product_data['total']
                    })
                else:
                    # No data for this product-category combination
                    matrix_data.append({
                        'product': product_asin,
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
            for product_asin, product_name in asin_to_product.items():
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
                        'product': product_asin,
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

    # ============================================================================
    # NEW METHODS FOR MATERIALIZED VIEW INTEGRATION
    # ============================================================================

    def get_data_with_materialized_view(self, include_review_content: bool = True) -> Dict[str, Any]:
        """Get competitor analysis data using the materialized view for enhanced performance.
        
        Args:
            include_review_content: Whether to include full review content for cell clicks
            
        Returns:
            Dict containing competitor analysis data with enhanced review content
        """
        try:
            # Get product information for target products
            product_info = self._get_product_info()
            
            # Get analysis data from materialized view
            analysis_data = self._get_analysis_data_from_view(include_review_content)
            
            # Get rating data for sentiment analysis
            rating_data = self._get_rating_data()
            
            # Process data and generate matrices with review content
            return self._process_competitor_data_with_reviews(
                product_info, analysis_data, rating_data, include_review_content
            )
            
        except Exception as e:
            logger.error(f"Error in CompetitorAnalysisService with materialized view for project {self.project_id}: {e}")
            return {
                'targetProducts': [],
                'matrixData': [],
                'productTotalReviews': {},
                'useCaseData': {
                    'targetProducts': [],
                    'matrixData': []
                },
                'reviewContent': {} if include_review_content else None
            }

    def _get_analysis_data_from_view(self, include_review_content: bool = True) -> List[Dict[str, Any]]:
        """Get analysis data from the materialized view for enhanced performance.
        
        Args:
            include_review_content: Whether to include full review content
            
        Returns:
            List of analysis data records with review content if requested
        """
        try:
            # Build the query based on whether we need review content
            if include_review_content:
                query = """
                    SELECT 
                        mrd.category_pk,
                        mrd.category_name,
                        mrd.category_definition,
                        mrd.aspect_type,
                        mrd.aspect_pk,
                        mrd.product_id,
                        mrd.detail_text,
                        mrd.parent_group_name,
                        mrd.sentiment,
                        mrd.review_id,
                        mrd.review_text,
                        mrd.review_rating,
                        mrd.review_verified,
                        mrd.review_date,
                        mrd.review_brand,
                        mrd.occurrence_count
                    FROM matrix_review_data mrd
                    WHERE mrd.product_id = ANY($1)
                    ORDER BY mrd.category_name, mrd.product_id, mrd.occurrence_count DESC
                """
            else:
                query = """
                    SELECT 
                        mrd.category_pk,
                        mrd.category_name,
                        mrd.category_definition,
                        mrd.aspect_type,
                        mrd.aspect_pk,
                        mrd.product_id,
                        mrd.detail_text,
                        mrd.parent_group_name,
                        mrd.sentiment,
                        mrd.occurrence_count
                    FROM matrix_review_data mrd
                    WHERE mrd.product_id = ANY($1)
                    ORDER BY mrd.category_name, mrd.product_id, mrd.occurrence_count DESC
                """
            
            # Use direct query instead of RPC for materialized view
            result = self.supabase.from_('matrix_review_data').select('*').in_('product_id', self.selected_asins).execute()
            
            if result.data is None:
                logger.error(f"Error querying materialized view: No data returned")
                return []
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting analysis data from materialized view: {e}")
            return []

    def _process_competitor_data_with_reviews(
        self, 
        product_info: List[Dict], 
        analysis_data: List[Dict], 
        rating_data: List[Dict],
        include_review_content: bool = True
    ) -> Dict[str, Any]:
        """Process competitor data with enhanced review content support.
        
        Args:
            product_info: Product information
            analysis_data: Analysis data from materialized view
            rating_data: Rating data for sentiment analysis
            include_review_content: Whether to include review content
            
        Returns:
            Processed competitor data with review content
        """
        try:
            # Create ASIN to product name mapping
            asin_to_product = {}
            for product in product_info:
                asin_to_product[product['platform_id']] = self._get_display_name(product['title'])
            
            # Also create mapping for the selected ASINs that might not be in product_info
            for asin in self.selected_asins:
                if asin not in asin_to_product:
                    asin_to_product[asin] = self.ASIN_TO_DISPLAY_NAME.get(asin, asin)
            
            # Create rating map
            rating_map = {}
            for rating in rating_data:
                # Use product_id to match the materialized view field name
                rating_map[rating['product_id']] = self._parse_rating(rating['rating'])
            
            # Aggregate analysis data with review content
            category_stats, use_case_stats, review_content = self._aggregate_analysis_data_with_reviews(
                analysis_data, asin_to_product, rating_map, include_review_content
            )
            
            # Build matrix data
            matrix_data = self._build_matrix_data(category_stats, asin_to_product)
            
            # Build use case data
            use_case_matrix_data = self._build_use_case_data(use_case_stats, asin_to_product)
            
            # Get total reviews per product
            product_total_reviews = {}
            for product in product_info:
                product_total_reviews[product['platform_id']] = product.get('reviews_count', 0)
            
            return {
                'targetProducts': self.selected_asins,
                'matrixData': matrix_data,
                'productTotalReviews': product_total_reviews,
                'useCaseData': {
                    'targetProducts': self.selected_asins,
                    'matrixData': use_case_matrix_data
                },
                'reviewContent': review_content if include_review_content else None
            }
            
        except Exception as e:
            logger.error(f"Error processing competitor data with reviews: {e}")
            return {
                'targetProducts': [],
                'matrixData': [],
                'productTotalReviews': {},
                'useCaseData': {
                    'targetProducts': [],
                    'matrixData': []
                },
                'reviewContent': {} if include_review_content else None
            }

    def _aggregate_analysis_data_with_reviews(
        self, 
        analysis_data: List[Dict], 
        asin_to_product: Dict, 
        rating_map: Dict,
        include_review_content: bool = True
    ) -> tuple:
        """Aggregate analysis data with review content support.
        
        Args:
            analysis_data: Analysis data from materialized view
            asin_to_product: ASIN to product name mapping
            rating_map: Rating mapping
            include_review_content: Whether to include review content
            
        Returns:
            Tuple of (category_stats, use_case_stats, review_content)
        """
        category_stats = {}
        use_case_stats = {}
        review_content = {} if include_review_content else {}
        
        for record in analysis_data:
            product_asin = record['product_id']
            category_name = record['category_name']
            aspect_type = record['aspect_type']
            sentiment_raw = record['sentiment']
            occurrence_count = record.get('occurrence_count', 1)
            
            # Map sentiment values from materialized view to expected format
            if sentiment_raw == '+':
                sentiment = 'positive'
            elif sentiment_raw == '-':
                sentiment = 'negative'
            else:
                sentiment = 'neutral'  # Default fallback
            
            # Skip if product not in our target list
            if product_asin not in asin_to_product:
                continue
            
            product_name = asin_to_product[product_asin]
            
            # Initialize category stats
            if category_name not in category_stats:
                # Map aspect_type to expected categoryType values
                if aspect_type == 'perf':
                    category_type = 'Performance'
                elif aspect_type == 'phys':
                    category_type = 'Physical'
                else:
                    category_type = 'Performance'  # Default fallback
                
                category_stats[category_name] = {
                    'totalMentions': 0,
                    'productData': {},
                    'categoryType': category_type
                }
            
            # Initialize product data in category
            if product_name not in category_stats[category_name]['productData']:
                category_stats[category_name]['productData'][product_name] = {
                    'total': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0
                }
            
            # Update category stats
            category_stats[category_name]['totalMentions'] += occurrence_count
            category_stats[category_name]['productData'][product_name]['total'] += occurrence_count
            
            # Update sentiment counts
            if sentiment == 'positive':
                category_stats[category_name]['productData'][product_name]['positive'] += occurrence_count
            elif sentiment == 'negative':
                category_stats[category_name]['productData'][product_name]['negative'] += occurrence_count
            else:
                category_stats[category_name]['productData'][product_name]['neutral'] += occurrence_count
            
            # Handle use cases (aspect_type == 'use')
            if aspect_type == 'use':
                if category_name not in use_case_stats:
                    use_case_stats[category_name] = {
                        'totalMentions': 0,
                        'productData': {}
                    }
                
                if product_name not in use_case_stats[category_name]['productData']:
                    use_case_stats[category_name]['productData'][product_name] = {
                        'total': 0,
                        'positive': 0,
                        'negative': 0,
                        'neutral': 0
                    }
                
                use_case_stats[category_name]['totalMentions'] += occurrence_count
                use_case_stats[category_name]['productData'][product_name]['total'] += occurrence_count
                
                if sentiment == 'positive':
                    use_case_stats[category_name]['productData'][product_name]['positive'] += occurrence_count
                elif sentiment == 'negative':
                    use_case_stats[category_name]['productData'][product_name]['negative'] += occurrence_count
                else:
                    use_case_stats[category_name]['productData'][product_name]['neutral'] += occurrence_count
            
            # Store review content if requested
            if include_review_content and 'review_id' in record:
                review_id = record['review_id']
                if review_id:
                    # Create review content key
                    review_key = f"{product_asin}_{category_name}"
                    
                    if review_key not in review_content:
                        review_content[review_key] = []
                    
                    # Add review if not already present
                    review_exists = any(r['id'] == review_id for r in review_content[review_key])
                    if not review_exists:
                        review_content[review_key].append({
                            'id': review_id,
                            'productId': product_asin,
                            'text': record.get('review_text', ''),
                            'sentiment': sentiment,
                            'category': category_name,
                            'aspect': record.get('detail_text', ''),
                            'rating': record.get('rating', 0),
                            'verified': record.get('verified', False),
                            'date': record.get('review_date', ''),
                            'brand': record.get('brand', '')
                        })
        
        return category_stats, use_case_stats, review_content

    def get_reviews_for_cell(
        self, 
        product_asin: str, 
        category_name: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get reviews for a specific matrix cell (product-category combination).
        
        Args:
            product_asin: The product ASIN
            category_name: The category name
            limit: Maximum number of reviews to return
            offset: Offset for pagination
            
        Returns:
            List of review objects for the cell
        """
        try:
            # Use direct query instead of RPC for materialized view
            result = self.supabase.from_('matrix_review_data').select('''
                review_id,
                review_text,
                rating,
                verified,
                review_date,
                brand,
                sentiment,
                detail_text
            ''').eq('product_id', product_asin).eq('category_name', category_name).order('review_date', desc=True).range(offset, offset + limit - 1).execute()
            
            if result.data is None:
                logger.error(f"Error getting reviews for cell: No data returned")
                return []
            
            reviews = []
            for record in result.data:
                reviews.append({
                    'id': record['review_id'],
                    'productId': product_asin,
                    'text': record['review_text'],
                    'sentiment': record['sentiment'],
                    'category': category_name,
                    'aspect': record['detail_text'],
                    'rating': record['rating'],
                    'verified': record['verified'],
                    'date': record['review_date'],
                    'brand': record['brand']
                })
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error getting reviews for cell {product_asin}-{category_name}: {e}")
            return [] 