# Competitor Analysis Chart Module

This module provides comprehensive competitor analysis functionality for the dashboard, including summary data and matrix view analysis with flexible sorting and filtering options.

## Overview

The competitor analysis module consists of:
- **Service Layer**: `CompetitorAnalysisChartService` - Handles data retrieval and processing
- **Models**: Request/response models with validation
- **API Endpoints**: Centralized in `backend/dashboard/charts/api.py`

## API Endpoints

### 1. Competitor Summary API

**Endpoint:** `POST /api/v1/dashboard/charts/competitor-analysis/summary`

**Purpose:** Get comprehensive competitor summary for selected ASINs including product information, review counts, and sentiment metrics.

**Request:**
```json
{
    "project_id": "project-uuid",
    "selected_asins": ["B00004YUO0", "B00NG0ELL0", "B0BVKZLT3B"]
}
```

**Response:**
```json
{
    "products": [
        {
            "asin": "B00004YUO0",
            "product_title": "Leviton 15 Amp, 120 Volt, Toggle Framed Single-Pole AC Quiet Switch...",
            "rating": 4.7,
            "brand": "Leviton",
            "product_url": "https://www.amazon.com/Leviton-1451-2WM-Single-Pole-Residential-Grounding/dp/B00004YUO0",
            "list_price": 6.98,
            "unique_reviews_count": 16,
            "additional_metrics": {
                "positive_aspects": 38,
                "negative_aspects": 11,
                "neutral_aspects": 0,
                "unique_categories": 17,
                "total_aspects": 49
            }
        }
    ],
    "total_products": 1,
    "selected_asins": ["B00004YUO0", "B00NG0ELL0", "B0BVKZLT3B"]
}
```

### 2. Competitor Matrix View API

**Endpoint:** `POST /api/v1/dashboard/charts/competitor-analysis/matrix-view`

**Purpose:** Get detailed matrix view data with flexible sorting, filtering, and limiting options.

**Request:**
```json
{
    "project_id": "project-uuid",
    "selected_asins": ["B00004YUO0", "B00NG0ELL0"],
    "aspect_type": "phy_perf",
    "options": {
        "sort_by": "mentions",
        "sort_direction": "desc",
        "max_categories": 10,
        "min_mentions": 5,
        "min_reviews": 3,
        "include_categories": ["Installation", "Quality"],
        "exclude_categories": ["Out of Scope"],
        "sentiment_filter": "positive_only"
    }
}
```

**Response:**
```json
{
    "aspect_categories": [
        {
            "category_id": 12455,
            "category_name": "Construction Materials and Build Quality",
            "definition": "Physical materials, build composition, structural integrity, and overall manufacturing quality of device components..."
        }
    ],
    "product_aspect_data": [
        {
            "asin": "B00004YUO0",
            "aspect_data": [
                {
                    "category_id": 12499,
                    "total_mentions": 6,
                    "positive_mentions": 6,
                    "negative_mentions": 0,
                    "unique_reviews": 6
                }
            ]
        }
    ],
    "selected_asins": ["B00004YUO0", "B00NG0ELL0"],
    "aspect_type": "phy_perf",
    "total_categories": 5
}
```

## Options Configuration

### Matrix View Options

The `CompetitorMatrixViewOptions` model provides flexible configuration:

#### Sorting Options
- **`sort_by`**: Field to sort by
  - `"mentions"` - Sort by total mentions (default)
  - `"reviews"` - Sort by unique reviews
  - `"sentiment"` - Sort by positive sentiment ratio
- **`sort_direction`**: Sort direction
  - `"asc"` - Ascending order
  - `"desc"` - Descending order (default)

#### Limiting Options
- **`max_categories`**: Maximum number of categories to return (1-50, default: 10)

#### Filtering Options
- **`min_mentions`**: Minimum total mentions to include
- **`min_reviews`**: Minimum unique reviews to include
- **`include_categories`**: Specific categories to include (array of category names)
- **`exclude_categories`**: Categories to exclude (array of category names)
- **`sentiment_filter`**: Filter by sentiment type
  - `"positive_only"` - Only categories with >50% positive sentiment
  - `"negative_only"` - Only categories with <50% positive sentiment
  - `"mixed_only"` - Only categories with 30-70% positive sentiment

## Usage Examples

### Basic Summary Request
```bash
curl -X POST "http://localhost:8000/api/v1/dashboard/charts/competitor-analysis/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "selected_asins": ["B00004YUO0", "B00NG0ELL0"]
  }'
```

### Matrix View with Default Options
```bash
curl -X POST "http://localhost:8000/api/v1/dashboard/charts/competitor-analysis/matrix-view" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "selected_asins": ["B00004YUO0"],
    "aspect_type": "phy_perf",
    "options": {}
  }'
```

### Matrix View with Custom Options
```bash
curl -X POST "http://localhost:8000/api/v1/dashboard/charts/competitor-analysis/matrix-view" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "selected_asins": ["B00004YUO0"],
    "aspect_type": "use",
    "options": {
        "sort_by": "sentiment",
        "sort_direction": "desc",
        "max_categories": 5,
        "min_mentions": 3,
        "sentiment_filter": "positive_only"
    }
  }'
```

## Data Sources

### Product Information (`product_wide_table`)
- Global product data including titles, ratings, brands, prices
- Not filtered by project_id (global data)

### Review Data (`review_aspect_data_view`)
- Project-specific review analysis data
- Filtered by project_id for data isolation
- Includes sentiment analysis and aspect categorization

## Error Handling

The API endpoints include comprehensive error handling:
- **Validation Errors**: Invalid request parameters return 422 status
- **Data Errors**: Missing or invalid data returns appropriate error messages
- **Server Errors**: Internal errors return 500 status with error details

## Performance Considerations

- Uses materialized views for efficient data retrieval
- Implements proper indexing on frequently queried fields
- Supports pagination through limiting options
- Caches category information to reduce database queries

## Dependencies

- `core.database.connection` - Database connectivity
- `review_analysis_aspect_categories` - Category definitions
- `product_wide_table` - Product information
- `review_aspect_data_view` - Review analysis data 