"""Data transformation utilities for standardizing API responses.

This module provides utilities to transform data between different naming conventions
and ensure consistency across the dashboard API.
"""

from typing import Dict, List, Any, Union
import re


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def transform_dict_keys(data: Any, transform_func) -> Any:
    """Recursively transform dictionary keys using the provided function."""
    if isinstance(data, dict):
        return {transform_func(k): transform_dict_keys(v, transform_func) for k, v in data.items()}
    elif isinstance(data, list):
        return [transform_dict_keys(item, transform_func) for item in data]
    else:
        return data


def to_snake_case(data: Any) -> Any:
    """Convert all dictionary keys from camelCase to snake_case."""
    return transform_dict_keys(data, camel_to_snake)


def to_camel_case(data: Any) -> Any:
    """Convert all dictionary keys from snake_case to camelCase."""
    return transform_dict_keys(data, snake_to_camel)


class CompetitorAnalysisTransformer:
    """Transformer for competitor analysis data between service and API formats."""
    
    @staticmethod
    def service_to_api(service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform service data (camelCase) to API response format (snake_case)."""
        return {
            'target_products': service_data.get('targetProducts', []),
            'matrix_data': [
                {
                    'product': item.get('product', ''),
                    'category': item.get('category', ''),
                    'category_type': item.get('categoryType', 'Performance'),
                    'total_reviews': item.get('totalReviews', 0),
                    'positive_reviews': item.get('positiveCount', 0),
                    'negative_reviews': item.get('negativeCount', 0),
                    'satisfaction_rate': item.get('satisfactionRate', 0.0)
                }
                for item in service_data.get('matrixData', [])
            ],
            'product_total_reviews': service_data.get('productTotalReviews', {}),
            'use_case_data': {
                'target_products': service_data.get('useCaseData', {}).get('targetProducts', []),
                'matrix_data': [
                    {
                        'product': item.get('product', ''),
                        'use_case': item.get('useCase', ''),
                        'mentions': item.get('mentions', 0),
                        'satisfaction_rate': item.get('satisfactionRate', 0.0),
                        'gap_level': item.get('gapLevel', 0.0)
                    }
                    for item in service_data.get('useCaseData', {}).get('matrixData', [])
                ]
            },
            'review_content': service_data.get('reviewContent', {})
        }
    
    @staticmethod
    def api_to_frontend(api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API data (snake_case) to frontend format (camelCase)."""
        return {
            'targetProducts': api_data.get('target_products', []),
            'matrixData': [
                {
                    'product': item.get('product', ''),
                    'category': item.get('category', ''),
                    'categoryType': item.get('category_type', 'Performance'),
                    'mentions': item.get('total_reviews', 0),
                    'satisfactionRate': item.get('satisfaction_rate', 0.0),
                    'positiveCount': item.get('positive_reviews', 0),
                    'negativeCount': item.get('negative_reviews', 0),
                    'totalReviews': item.get('total_reviews', 0)
                }
                for item in api_data.get('matrix_data', [])
            ],
            'productTotalReviews': api_data.get('product_total_reviews', {}),
            'useCaseData': {
                'targetProducts': api_data.get('use_case_data', {}).get('target_products', []),
                'matrixData': [
                    {
                        'product': item.get('product', ''),
                        'useCase': item.get('use_case', ''),
                        'mentions': item.get('mentions', 0),
                        'satisfactionRate': item.get('satisfaction_rate', 0.0),
                        'gapLevel': item.get('gap_level', 0.0)
                    }
                    for item in api_data.get('use_case_data', {}).get('matrix_data', [])
                ]
            },
            'reviewContent': api_data.get('review_content', {})
        }


class ReviewInsightsTransformer:
    """Transformer for review insights data between service and API formats."""
    
    @staticmethod
    def service_to_api(service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform service data to API response format."""
        return {
            'pain_points': [
                {
                    'category_name': item.get('categoryName', ''),
                    'example_details': item.get('exampleDetails', ''),
                    'satisfaction_rate': item.get('satisfactionRate', 0.0),
                    'impacted_products': item.get('impactedProducts', 0),
                    'type': item.get('type', 'Performance'),
                    'total_reviews': item.get('totalReviews', 0),
                    'positive_reviews': item.get('positiveReviews', 0),
                    'negative_reviews': item.get('negativeReviews', 0),
                    'category_definition': item.get('categoryDefinition', ''),
                    'related_detail_texts': item.get('relatedDetailTexts', []),
                    'category_id': item.get('categoryId')
                }
                for item in service_data.get('painPoints', [])
            ],
            'customer_likes': [
                {
                    'category_name': item.get('categoryName', ''),
                    'example_details': item.get('exampleDetails', ''),
                    'satisfaction_level': item.get('satisfactionLevel', 'Medium'),
                    'total_reviews': item.get('totalReviews', 0),
                    'positive_reviews': item.get('positiveReviews', 0),
                    'negative_reviews': item.get('negativeReviews', 0),
                    'category_definition': item.get('categoryDefinition', ''),
                    'related_detail_texts': item.get('relatedDetailTexts', []),
                    'category_id': item.get('categoryId')
                }
                for item in service_data.get('customerLikes', [])
            ],
            'all_use_cases': [
                {
                    'use_case': item.get('useCase', ''),
                    'product_attribute': item.get('productAttribute', ''),
                    'satisfaction_rate': item.get('satisfactionRate', 0.0),
                    'product_count': item.get('productCount', 0),
                    'total_reviews': item.get('totalReviews', 0),
                    'positive_reviews': item.get('positiveReviews', 0),
                    'negative_reviews': item.get('negativeReviews', 0),
                    'category_definition': item.get('categoryDefinition', ''),
                    'related_detail_texts': item.get('relatedDetailTexts', []),
                    'category_id': item.get('categoryId')
                }
                for item in service_data.get('allUseCases', [])
            ],
            'underserved_use_cases': [
                {
                    'use_case': item.get('useCase', ''),
                    'product_attribute': item.get('productAttribute', ''),
                    'satisfaction_rate': item.get('satisfactionRate', 0.0),
                    'product_count': item.get('productCount', 0),
                    'total_reviews': item.get('totalReviews', 0),
                    'positive_reviews': item.get('positiveReviews', 0),
                    'negative_reviews': item.get('negativeReviews', 0),
                    'category_definition': item.get('categoryDefinition', ''),
                    'related_detail_texts': item.get('relatedDetailTexts', []),
                    'category_id': item.get('categoryId')
                }
                for item in service_data.get('underservedUseCases', [])
            ],
            'total_use_reviews': service_data.get('totalUseReviews', 0)
        }


class DataTransformerRegistry:
    """Registry for data transformers by endpoint type."""
    
    _transformers = {
        'competitor_analysis': CompetitorAnalysisTransformer,
        'review_insights': ReviewInsightsTransformer
    }
    
    @classmethod
    def get_transformer(cls, endpoint_type: str):
        """Get transformer for the specified endpoint type."""
        return cls._transformers.get(endpoint_type)
    
    @classmethod
    def register_transformer(cls, endpoint_type: str, transformer_class):
        """Register a new transformer."""
        cls._transformers[endpoint_type] = transformer_class 