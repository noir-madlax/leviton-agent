"""Shared constants and configuration for review analysis."""

class ReviewAnalysisConfig:
    """Shared configuration for review analysis."""
    
    # Database table names
    REVIEW_ASPECT_DATA_VIEW = 'review_aspect_data_view'
    ASPECT_CATEGORIES_TABLE = 'review_analysis_aspect_categories'
    
    # Default values
    DEFAULT_LIMIT = 100
    DEFAULT_OFFSET = 0
    DEFAULT_SORT_BY = 'review_id'
    DEFAULT_SORT_ORDER = 'desc'
    
    # Aspect types
    ASPECT_TYPES = ['phy', 'perf', 'use']
    ASPECT_TYPE_MAP = {
        'phy_perf': ['phy', 'perf'],  # phy_perf maps to both phy and perf
        'use': ['use']
    }
    
    # Sort options
    SORT_OPTIONS = ['review_id', 'date', 'rating', 'sentiment']
    SORT_ORDERS = ['asc', 'desc']
    
    # Category sorting options
    CATEGORY_SORT_OPTIONS = ['mentions', 'positive_mentions', 'negative_mentions', 'positive_ratio']
    
    # Default category limits
    DEFAULT_TOP_CATEGORIES = 10
    MAX_CATEGORIES = 50 