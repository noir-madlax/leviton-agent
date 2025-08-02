# Review Core Module

This module provides shared functionality for review analysis across different chart modules. It contains the core logic for review processing, deduplication, aspect aggregation, and database operations.

## Overview

The `reviewCore` module is designed to be shared between:
- **Competitor Analysis**: Review analysis for individual selected products
- **Review Analysis**: Review analysis for all filtered products under a project

## Key Features

### 1. Shared Review Processing
- **Review Deduplication**: Eliminates duplicate reviews from multiple aspect mentions
- **Aspect Aggregation**: Collects all aspects mentioned in each review with sentiments
- **Rating Transformation**: Converts string ratings to numeric format
- **Aspect Description Formatting**: Creates clean aspect descriptions

### 2. Shared Database Operations
- **Category Statistics**: Calculate mentions, sentiments, and review counts
- **Review Retrieval**: Get reviews with sorting and filtering
- **Category Information**: Retrieve category definitions and metadata

### 3. Shared Utilities
- **Sentiment Analysis**: Calculate sentiment distributions
- **Pagination**: Apply pagination with metadata
- **Data Transformation**: Format and transform review data

## Module Structure

```
reviewCore/
├── __init__.py              # Standard exports
├── models.py                # Shared base models
├── base_service.py          # Base service with shared logic
├── data_service.py          # Shared database operations
├── utils.py                 # Shared utilities
├── constants.py             # Shared configuration
└── README.md                # This documentation
```

## Shared Models

### ReviewAspectBase
Base model for review aspects with sentiment and type information.

### ReviewDetailBase
Base model for review details without product information (used by competitor analysis).

### CategoryInfoBase
Base model for category information with definitions.

### PaginationBase
Base model for pagination metadata.

## Shared Services

### ReviewAnalysisBaseService
Base service class that provides:
- Review deduplication and aspect aggregation
- Category information retrieval
- Review sorting logic
- Filtered ASIN retrieval

### ReviewDataService
Shared data service for database operations:
- `get_reviews_by_category()` - Retrieve reviews for a category
- `get_category_statistics()` - Optimized category statistics with SQL-level filtering/sorting
- `get_aspect_categories_with_metrics()` - Get categories with filtering/sorting and optional cause analysis
- `get_cause_analysis()` - Analyze cause categories for top categories

## Shared Utilities

### ReviewProcessingUtils
Static utility methods for:
- `calculate_sentiment_distribution()` - Calculate sentiment counts
- `aggregate_category_metrics()` - Aggregate metrics across categories
- `apply_pagination()` - Apply pagination with metadata
- `format_aspect_description()` - Format aspect descriptions
- `transform_rating()` - Transform rating formats

## Configuration

### ReviewAnalysisConfig
Shared configuration including:
- Database table names
- Default values for limits and sorting
- Aspect type mappings
- Sort options and category limits

## Usage Examples

### Inheriting from Base Service
```python
from reviewCore import ReviewAnalysisBaseService

class MyReviewService(ReviewAnalysisBaseService):
    def __init__(self, project_id: str):
        super().__init__(project_id)
    
    async def get_my_data(self):
        # Use shared methods
        filtered_asins = self._get_filtered_asins()
        reviews = await self.review_data_service.get_reviews_by_category(...)
        deduplicated = self._deduplicate_and_aggregate_reviews(reviews)
        return deduplicated
```

### Using Shared Utilities
```python
from reviewCore import ReviewProcessingUtils

# Calculate sentiment distribution
sentiment_dist = ReviewProcessingUtils.calculate_sentiment_distribution(reviews_data)

# Apply pagination
pagination_result = ReviewProcessingUtils.apply_pagination(data, limit=10, offset=0)
```

## Key Differences Between Modules

### Competitor Analysis
- **Scope**: Specific selected ASINs
- **Reviews**: From same products (no product info needed)
- **Focus**: Product-to-product comparison
- **Data**: Uses `selected_asins` parameter

### Review Analysis
- **Scope**: All filtered products under project
- **Reviews**: From different products (product info required)
- **Focus**: Project-wide category analysis
- **Data**: Uses project filters

## Data Sources

### Primary Tables
- `review_aspect_data_view` - Materialized view with review and aspect data
- `review_analysis_aspect_categories` - Category definitions and metadata
- `product_wide_table` - Product information and pricing

### Key Fields
- `project_id` - Project filtering
- `category_pk` - Aspect category identification
- `product_id` - Product ASIN
- `review_id` - Unique review identifier
- `sentiment` - Aspect sentiment (+/-/neutral)
- `aspect_description` - Detailed aspect text

## Error Handling

The module includes comprehensive error handling:
- **Database Errors**: Connection issues or missing data
- **Validation Errors**: Invalid parameters or data formats
- **Graceful Degradation**: Returns empty results instead of failing

## Performance Considerations

- **Efficient Queries**: Uses indexed fields for filtering
- **Pagination**: Limits data transfer with offset/limit
- **Deduplication**: Performed in memory for better performance
- **Optimized Methods**: New optimized methods reduce database queries from N+1 to 2 total
- **Cause Analysis**: Only analyzes causes for top N categories, not all categories

## New Features

### Cause Analysis
The `get_aspect_categories_with_metrics()` method now supports cause analysis through the `return_top_cause_categories` option:

```python
options = {
    'max_categories': 5,
    'sort_by': 'total_mentions',
    'return_top_cause_categories': {
        'sentiment': '+',  # Optional: '+', '-', or None for both
        'limit': 3
    }
}
```

### Performance Improvements
- **`get_category_statistics()`**: Single query approach instead of N+1 queries
- **Integrated filtering/sorting**: Applied during data processing, not as separate steps
- **Cause analysis**: Only processes top N categories for efficiency

## Future Enhancements

- **Advanced Filtering**: Filter by sentiment, rating, or date range
- **Aspect Highlighting**: Highlight specific aspects in review text
- **Export Functionality**: Export reviews to CSV/Excel
- **Real-time Updates**: WebSocket support for live data updates 