# Review Analysis Chart Module

This module provides comprehensive review analysis functionality for the dashboard, including top aspect categories analysis and review retrieval with product information.

## Overview

The review analysis module consists of:
- **Service Layer**: `ReviewAnalysisChartService` - Handles data retrieval and processing
- **Models**: Request/response models with validation following API documentation standards
- **API Endpoints**: Centralized in `backend/dashboard/charts/api.py`

## Key Features

### 1. Top Categories Analysis
- Project-wide aspect category analysis
- Comprehensive statistics (mentions, sentiments, review counts)
- Flexible filtering by aspect type (phy_perf, use)
- Advanced sorting options (mentions, positive_mentions, negative_mentions, positive_ratio)

### 2. Reviews by Category with Product Information ⭐ **NEW**
- Retrieves reviews for specific aspect categories across all filtered products
- **Includes product information** (product_id, title, brand, URL) since reviews come from different products
- **Deduplicates reviews** to avoid duplicates from multiple aspect mentions
- **Aggregates aspects** per review to show all mentioned aspects with sentiments
- **Pagination support** following API documentation standards
- **Sorting options** by date, rating, sentiment, or review ID

## API Endpoints

### 1. Top Categories API

**Endpoint:** `POST /api/v1/dashboard/charts/review-analysis/top-categories`

**Purpose:** Get top aspect categories with comprehensive statistics for all filtered products under a project.

**Request:**
```json
{
    "project_id": "project-uuid",
    "filters": {
        "categories": ["Light Switches"],
        "brands": ["Leviton", "Lutron"],
        "segments": ["Smart"],
        "extend_fields": {"smart_capability": "Smart"}
    },
    "additional_conditions": {
        "aspect_type": "phy_perf",
        "sort_by": "positive_mentions",
        "sort_direction": "desc",
        "max_categories": 10,
        "min_mentions": 5,
        "min_positive_mentions": 2
    }
}
```

**Response:**
```json
{
    "status": "success",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "categories": [
            {
                "category_id": 12499,
                "category_name": "Physical Installation Process",
                "definition": "Ease and compatibility of physical mounting and electrical installation processes",
                "aspect_type": "phy",
                "total_mentions": 45,
                "positive_mentions": 32,
                "negative_mentions": 10,
                "neutral_mentions": 3,
                "unique_reviews": 38,
                "positive_ratio": 0.711
            }
        ],
        "total_categories": 1,
        "summary_stats": {
            "total_categories": 1,
            "total_mentions": 45,
            "total_reviews": 38,
            "total_positive_mentions": 32,
            "total_negative_mentions": 10,
            "overall_positive_ratio": 0.711
        }
    }
}
```

### 2. Reviews by Category API

**Endpoint:** `POST /api/v1/dashboard/charts/review-analysis/reviews-by-category`

**Purpose:** Get reviews for a specific category with product information and deduplication.

**Request:**
```json
{
    "project_id": "project-uuid",
    "filters": {
        "categories": ["Light Switches"],
        "brands": ["Leviton", "Lutron"]
    },
    "category_id": 12499,
    "limit": 10,
    "offset": 0,
    "sort_by": "date",
    "sort_order": "desc"
}
```

**Response:**
```json
{
    "status": "success",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "reviews": [
            {
                "review_id": "R123456789",
                "review_title": "Great dimmer switch",
                "review_text": "This dimmer switch works perfectly...",
                "rating": 5,
                "verified": true,
                "review_date": "2024-01-10",
                "aspects": [
                    {
                        "aspect_description": "Physical Installation Process: Easy to install",
                        "sentiment": "+",
                        "aspect_type": "phy"
                    },
                    {
                        "aspect_description": "Performance: Smooth dimming",
                        "sentiment": "+",
                        "aspect_type": "perf"
                    }
                ],
                "product_id": "B00NG0ELL0",
                "product_title": "Leviton Decora Slide Dimmer Switch",
                "product_brand": "Leviton",
                "product_url": "https://www.amazon.com/Leviton-DSL06-1LZ..."
            }
        ],
        "total_reviews": 25,
        "project_id": "project-uuid",
        "category_id": 12499,
        "category_info": {
            "category_id": 12499,
            "category_name": "Physical Installation Process",
            "definition": "Ease and compatibility of physical mounting...",
            "aspect_type": "phy"
        },
        "pagination": {
            "limit": 10,
            "offset": 0,
            "has_more": true
        }
    }
}
```

## Key Differences from Competitor Analysis

### Review Analysis (This Module)
- **Scope**: All filtered products under project
- **Reviews**: From different products (product info required)
- **Focus**: Project-wide category analysis
- **Data**: Uses project filters
- **Product Info**: Included in reviews since they come from different products

### Competitor Analysis
- **Scope**: Specific selected ASINs
- **Reviews**: From same products (no product info needed)
- **Focus**: Product-to-product comparison
- **Data**: Uses selected_asins parameter

## Additional Conditions for Top Categories

### Aspect Type Filtering
- `"aspect_type": "phy_perf"` - Physical and performance aspects
- `"aspect_type": "use"` - Usability aspects

### Sorting Options
- `"sort_by": "mentions"` - Total mentions (default)
- `"sort_by": "positive_mentions"` - Positive mentions count
- `"sort_by": "negative_mentions"` - Negative mentions count
- `"sort_by": "positive_ratio"` - Ratio of positive to total mentions

### Filtering Options
- `"min_mentions": 5` - Minimum total mentions
- `"min_positive_mentions": 2` - Minimum positive mentions
- `"min_negative_mentions": 1` - Minimum negative mentions
- `"max_categories": 10` - Maximum categories to return

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

## Business Logic

### Review Deduplication and Aspect Aggregation
The service uses shared logic from `reviewCore` to:
1. **Deduplicate reviews** by grouping by `review_id`
2. **Aggregate aspects** from all occurrences of each review
3. **Format aspect descriptions** using parent group and detail text
4. **Transform ratings** from string to numeric format

### Category Statistics Calculation
For each category, the service calculates:
- **Total mentions**: Sum of all aspect occurrences
- **Positive mentions**: Count of positive sentiment occurrences
- **Negative mentions**: Count of negative sentiment occurrences
- **Neutral mentions**: Count of neutral sentiment occurrences
- **Unique reviews**: Count of distinct review IDs
- **Positive ratio**: Positive mentions / total mentions

## Error Handling

The service includes comprehensive error handling:
- **Validation Errors**: Invalid project_id, category_id, or filter parameters
- **Database Errors**: Connection issues or missing data
- **Pagination Errors**: Invalid limit/offset values
- **Graceful Degradation**: Returns empty results instead of failing

## Performance Considerations

- **Efficient Queries**: Uses indexed fields for filtering
- **Pagination**: Limits data transfer with offset/limit
- **Deduplication**: Performed in memory for better performance
- **Caching**: Leverages materialized view for fast access
- **Filtering**: Applies project filters to reduce data volume

## Usage Examples

### Frontend Integration
```typescript
// Get top categories
const response = await fetch('/api/v1/dashboard/charts/review-analysis/top-categories', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        project_id: 'project-uuid',
        filters: {
            categories: ['Light Switches'],
            brands: ['Leviton']
        },
        additional_conditions: {
            aspect_type: 'phy_perf',
            sort_by: 'positive_mentions',
            max_categories: 10
        }
    })
});

// Get reviews by category
const reviewsResponse = await fetch('/api/v1/dashboard/charts/review-analysis/reviews-by-category', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        project_id: 'project-uuid',
        category_id: 12499,
        limit: 20,
        offset: 0,
        sort_by: 'date',
        sort_order: 'desc'
    })
});
```

### Backend Integration
```python
from dashboard.charts.reviewAnalysis.service import ReviewAnalysisChartService

service = ReviewAnalysisChartService(project_id="project-uuid")
top_categories = await service.get_top_categories({
    'aspect_type': 'phy_perf',
    'sort_by': 'positive_mentions',
    'max_categories': 10
})

reviews = await service.get_reviews_by_category(
    category_id=12499,
    limit=10,
    offset=0
)
```

## Testing

Run the test script to verify functionality:
```bash
cd backend
python -m pytest dashboard/charts/reviewAnalysis/tests/
```

The test suite validates:
- Database connectivity
- Category and review retrieval
- Deduplication logic
- Pagination functionality
- Service integration
- API endpoint responses

## Future Enhancements

- **Advanced Filtering**: Filter by sentiment, rating, or date range
- **Aspect Highlighting**: Highlight specific aspects in review text
- **Export Functionality**: Export reviews to CSV/Excel
- **Real-time Updates**: WebSocket support for live data updates
- **Category Comparison**: Compare categories across different time periods 