"""Review insights service for dashboard."""

import logging
from typing import List, Dict, Any, Set

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class ReviewInsightsService(BaseDashboardService):
    """Service for review insights data.
    
    Updated to use new table structure:
    - review_analysis_aspects
    - review_analysis_aspect_categories  
    - review_analysis_aspect_occurrences
    
    Provides enhanced sentiment analysis and category definitions.
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get review insights data with ASIN filtering from new table structure.
        
        Returns data in the exact same format as frontend getReviewInsightsData()
        to ensure compatibility with existing UI components, but with enhanced
        accuracy from sentiment analysis.
        """
        try:
            # Get comprehensive data from new table structure
            comprehensive_data = self._get_comprehensive_review_data()
            
            if not comprehensive_data:
                logger.warning(f"No review insights data found for project {self.project_id}")
                return {
                    'painPoints': [],
                    'customerLikes': [],
                    'underservedUseCases': []
                }
            
            logger.info(f"🔍 Review insights query returned {len(comprehensive_data)} aspect records for project {self.project_id}")
            
            # Process data with sentiment analysis
            return self._process_review_data_with_sentiment(comprehensive_data)
            
        except Exception as e:
            logger.error(f"Error getting review insights data for project {self.project_id}: {e}")
            raise

    def _get_comprehensive_review_data(self) -> List[Dict[str, Any]]:
        """Get comprehensive review data from new table structure with JOINs."""
        try:
            # Build the query with proper JOINs
            # Note: Supabase client doesn't support complex JOINs directly,
            # so we'll use individual queries and combine them
            
            # First, get aspects filtered by project
            aspects_query = self.supabase.from_('review_analysis_aspects').select('''
                aspect_pk,
                product_id,
                aspect_type,
                detail_text,
                parent_group_name,
                category_pk
            ''').eq('project_id', self.project_id)
            
            # Apply ASIN filtering
            if not self.project_asins:
                logger.warning(f"No ASINs found for project {self.project_id}")
                return []
            
            aspects_query = aspects_query.in_('product_id', self.project_asins)
            aspects_result = aspects_query.execute()
            
            if not aspects_result.data:
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
                ''').in_('category_pk', category_pks)
                
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
                        occurrences_data[aspect_pk] = {
                            'total_count': 0,
                            'positive_count': 0,
                            'negative_count': 0,
                            'neutral_count': 0,
                            'review_ids': set()
                        }
                    
                    occurrences_data[aspect_pk]['total_count'] += 1
                    occurrences_data[aspect_pk]['review_ids'].add(occurrence['review_id'])
                    
                    if occurrence['sentiment'] == '+':
                        occurrences_data[aspect_pk]['positive_count'] += 1
                    elif occurrence['sentiment'] == '-':
                        occurrences_data[aspect_pk]['negative_count'] += 1
                    else:
                        occurrences_data[aspect_pk]['neutral_count'] += 1
            
            # Combine all data
            combined_data = []
            for aspect in aspects_result.data:
                aspect_pk = aspect['aspect_pk']
                category_pk = aspect['category_pk']
                
                # Get category info
                category_info = categories_data.get(category_pk, {})
                
                # Get occurrence info
                occurrence_info = occurrences_data.get(aspect_pk, {
                    'total_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'review_ids': set()
                })
                
                # Handle missing category_pk by using fallback naming
                if category_pk and category_pk in categories_data:
                    category_name = categories_data[category_pk]['name']
                    category_definition = categories_data[category_pk]['definition']
                else:
                    # Fallback: use parent_group_name or detail_text as category name
                    category_name = aspect['parent_group_name'] or aspect['detail_text'] or 'Unknown'
                    category_definition = f"Aspect type: {aspect['aspect_type']}"
                
                combined_data.append({
                    'aspect_pk': aspect_pk,
                    'product_id': aspect['product_id'],
                    'aspect_type': aspect['aspect_type'],
                    'detail_text': aspect['detail_text'],
                    'parent_group_name': aspect['parent_group_name'],
                    'category_name': category_name,
                    'category_definition': category_definition,
                    'total_count': occurrence_info['total_count'],
                    'positive_count': occurrence_info['positive_count'],
                    'negative_count': occurrence_info['negative_count'],
                    'neutral_count': occurrence_info['neutral_count'],
                    'review_count': len(occurrence_info['review_ids'])
                })
            
            logger.info(f"📊 Combined data: {len(combined_data)} aspects with sentiment analysis")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive review data: {e}")
            return []

    def _process_review_data_with_sentiment(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process review data with enhanced sentiment analysis."""
        
        # Map aspect types to display names
        def get_category_type(aspect_type: str) -> str:
            type_map = {
                'phy': 'Physical',
                'perf': 'Performance', 
                'use': 'Usability'
            }
            return type_map.get(aspect_type, 'Physical')
        
        # Group data by category for aggregation
        category_aggregates = {}
        
        for item in data:
            # Skip items with no occurrences
            if item['total_count'] == 0:
                continue
                
            category_key = f"{item['category_name']}_{item['aspect_type']}"
            
            if category_key not in category_aggregates:
                category_aggregates[category_key] = {
                    'category_name': item['category_name'],
                    'category_definition': item['category_definition'],
                    'aspect_type': item['aspect_type'],
                    'total_mentions': 0,
                    'positive_mentions': 0,
                    'negative_mentions': 0,
                    'neutral_mentions': 0,
                    'products': set(),
                    'details': set(),
                    'parent_groups': set()
                }
            
            agg = category_aggregates[category_key]
            agg['total_mentions'] += item['total_count']
            agg['positive_mentions'] += item['positive_count']
            agg['negative_mentions'] += item['negative_count']
            agg['neutral_mentions'] += item['neutral_count']
            agg['products'].add(item['product_id'])
            agg['details'].add(item['detail_text'])
            agg['parent_groups'].add(item['parent_group_name'])
        
        # Generate pain points (categories with high negative sentiment)
        pain_points = []
        for key, agg in category_aggregates.items():
            if agg['negative_mentions'] > 0:  # Only include categories with negative feedback
                negative_rate = (agg['negative_mentions'] / agg['total_mentions']) * 100
                severity = min(100, max(10, negative_rate))  # Severity based on negative percentage
                
                pain_points.append({
                    'aspect': agg['category_name'],
                    'category': ', '.join(list(agg['details'])[:3]),  # Sample details
                    'severity': severity,
                    'frequency': agg['negative_mentions'],
                    'impactedProducts': len(agg['products']),
                    'type': get_category_type(agg['aspect_type']),
                    # Enhanced fields for frontend optimization
                    'categoryDefinition': agg['category_definition'],
                    'totalMentions': agg['total_mentions'],
                    'negativeRate': negative_rate
                })
        
        # Sort by severity and take top 15
        pain_points.sort(key=lambda x: x['severity'], reverse=True)
        pain_points = pain_points[:15]
        
        # Generate customer likes (categories with high positive sentiment)
        customer_likes = []
        for key, agg in category_aggregates.items():
            if agg['positive_mentions'] > 0:  # Only include categories with positive feedback
                positive_rate = (agg['positive_mentions'] / agg['total_mentions']) * 100
                
                if positive_rate >= 70:
                    satisfaction_level = 'High'
                elif positive_rate >= 40:
                    satisfaction_level = 'Medium'
                else:
                    satisfaction_level = 'Low'
                
                customer_likes.append({
                    'feature': agg['category_name'],
                    'category': ', '.join(list(agg['details'])[:3]),  # Sample details
                    'frequency': agg['positive_mentions'],
                    'satisfactionLevel': satisfaction_level,
                    # Enhanced fields for frontend optimization
                    'categoryDefinition': agg['category_definition'],
                    'totalMentions': agg['total_mentions'],
                    'positiveRate': positive_rate
                })
        
        # Sort by frequency and take top 10
        customer_likes.sort(key=lambda x: x['frequency'], reverse=True)
        customer_likes = customer_likes[:10]
        
        # Generate underserved use cases (categories with low overall mentions but presence across products)
        underserved_use_cases = []
        for key, agg in category_aggregates.items():
            # Focus on use case type categories with low mention count but multi-product presence
            # 放宽筛选条件：mentions < 10 且 products >= 2
            if (agg['aspect_type'] == 'use' and 
                agg['total_mentions'] < 10 and 
                len(agg['products']) >= 2):
                
                gap_level = max(30, 100 - (agg['total_mentions'] * 10))  # Inverse relationship with mentions, increased multiplier
                
                underserved_use_cases.append({
                    'useCase': agg['category_name'],
                    'productAttribute': ', '.join(list(agg['parent_groups'])),
                    'gapLevel': gap_level,
                    'mentionCount': agg['total_mentions'],
                    # Enhanced fields for frontend optimization
                    'categoryDefinition': agg['category_definition'],
                    'productCount': len(agg['products'])
                })
        
        # Sort by gap level and take top 8
        underserved_use_cases.sort(key=lambda x: x['gapLevel'], reverse=True)
        underserved_use_cases = underserved_use_cases[:8]
        
        logger.info(f"📈 Processed results: {len(pain_points)} pain points, {len(customer_likes)} likes, {len(underserved_use_cases)} underserved use cases")
        
        return {
            'painPoints': pain_points,
            'customerLikes': customer_likes,
            'underservedUseCases': underserved_use_cases
        } 