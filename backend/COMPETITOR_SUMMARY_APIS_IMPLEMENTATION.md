# Competitor Analysis APIs Implementation

## Overview

A comprehensive competitor analysis API suite has been implemented with a clean service-based architecture to provide quick access to competitor product information, review metrics, and matrix view data.

## APIs Implemented

### 1. Competitor Summary API

**Endpoint:** `POST /competitor-analysis/summary`

**Request:**
```json
{
    "project_id": "project-uuid",
    "selected_asins": ["ASIN1", "ASIN2", "ASIN3"]
}
```

**Response:**
```json
{
    "products": [
        {
            "asin": "B00NG0ELL0",
            "product_title": "Leviton Decora Slide Dimmer Switch for Dimmable LED...",
            "rating": 4.6,
            "brand": "Leviton",
            "product_url": "https://amazon.com/...",
            "list_price": 29.99,
            "unique_reviews_count": 48,
            "additional_metrics": {
                "positive_aspects": 158,
                "negative_aspects": 87,
                "neutral_aspects": 0,
                "unique_categories": 71,
                "total_aspects": 245
            }
        }
    ],
    "total_products": 1,
    "selected_asins": ["B00NG0ELL0", "ASIN2", "ASIN3"]
}
```

### 2. Competitor Matrix View API

**Endpoint:** `POST /competitor-analysis/matrix-view`

**Request:**
```json
{
    "project_id": "project-uuid",
    "selected_asins": ["ASIN1", "ASIN2", "ASIN3"],
    "aspect_type": "phy_perf",
    "filter": {
        "top_n": 10
    }
}
```

**Response:**
```json
{
    "aspect_categories": [
        {
            "category_id": 7365,
            "category_name": "Physical Installation",
            "definition": "Installation process and physical setup aspects"
        }
    ],
    "product_aspect_data": [
        {
            "asin": "B00NG0ELL0",
            "aspect_data": [
                {
                    "category_id": 7365,
                    "total_mentions": 16,
                    "positive_mentions": 16,
                    "negative_mentions": 0,
                    "unique_reviews": 13
                }
            ]
        }
    ],
    "selected_asins": ["ASIN1", "ASIN2", "ASIN3"],
    "aspect_type": "phy_perf",
    "total_categories": 10
}
```

## Architecture

### Service Layer (`dashboard/services/competitor_summary_service.py`)

The `CompetitorSummaryService` class handles all data retrieval and processing logic:

#### Summary Methods:
- **`get_competitor_summary()`**: Main method that orchestrates data retrieval
- **`_get_product_summary_data()`**: Retrieves product data from `product_wide_table`
- **`_get_unique_review_counts()`**: Calculates unique review counts from `matrix_review_data`
- **`_get_additional_metrics()`**: Calculates sentiment distribution and category metrics

#### Matrix View Methods:
- **`get_matrix_view_data()`**: Main method for matrix view data retrieval
- **`_get_top_aspect_categories()`**: Gets top aspect categories by total mentions
- **`_get_category_info()`**: Retrieves category information and definitions
- **`_get_product_aspect_data()`**: Gets detailed product-category statistics

### API Layer (`dashboard/api.py`)

The API endpoints are clean and focused:
- Use the service for all data processing
- Handle request/response model conversion
- Provide error handling and logging

## Data Sources

### Product Information (`product_wide_table`)
- `platform_id` (ASIN)
- `title` (Product title)
- `rating` (Product rating)
- `brand` (Product brand)
- `product_url` (Product URL)
- `list_price_usd` (List price in USD)
- `price_usd` (Current price)
- `reviews_count` (Total reviews count)
- `category` (Product category)

### Review Data (`review_aspect_data_view` - materialized view)
- `product_id` (ASIN)
- `review_id` (Unique review identifier)
- `sentiment` (+, -, or neutral)
- `category_name` (Review aspect category)
- `category_pk` (Category primary key)
- `aspect_type` (phy, perf, or use)

### Category Information (`review_analysis_aspect_categories`)
- `category_pk` (Category primary key)
- `name` (Category name)
- `definition` (Category definition)
- `stage` (final)

## Implementation Details

### Models (`dashboard/models.py`)

#### Summary Models:
1. **CompetitorSummaryRequest**
   - `project_id`: str - Required project ID for filtering
   - `selected_asins`: List[str] - Required list of ASINs to analyze

2. **CompetitorSummaryProduct**
   - `asin`: str - Product ASIN
   - `product_title`: str - Product title
   - `rating`: Optional[float] - Product rating
   - `brand`: Optional[str] - Product brand
   - `product_url`: Optional[str] - Product URL
   - `list_price`: Optional[float] - List price in USD
   - `unique_reviews_count`: int - Number of unique reviews
   - `additional_metrics`: Optional[Dict[str, Any]] - Additional metrics including sentiment distribution

3. **CompetitorSummaryResponse**
   - `products`: List[CompetitorSummaryProduct] - List of competitor products
   - `total_products`: int - Total number of products returned
   - `selected_asins`: List[str] - List of ASINs that were requested

#### Matrix View Models:
4. **CompetitorMatrixViewFilter**
   - `top_n`: int - Number of top aspect categories to include

5. **CompetitorMatrixViewRequest**
   - `project_id`: str - Required project ID for filtering
   - `selected_asins`: List[str] - List of ASINs to analyze
   - `aspect_type`: Literal["phy_perf", "use"] - Aspect type filter
   - `filter`: CompetitorMatrixViewFilter - Filter configuration

6. **AspectCategoryInfo**
   - `category_id`: int - Category ID
   - `category_name`: str - Category name
   - `definition`: str - Category definition

7. **ProductAspectData**
   - `asin`: str - Product ASIN
   - `aspect_data`: List[Dict[str, Any]] - List of aspect data for this product, where each aspect contains:
     - `category_id`: int - Category ID
     - `total_mentions`: int - Total mentions of this category
     - `positive_mentions`: int - Positive mentions
     - `negative_mentions`: int - Negative mentions
     - `unique_reviews`: int - Unique number of reviews mentioning this category

8. **CompetitorMatrixViewResponse**
   - `aspect_categories`: List[AspectCategoryInfo] - List of aspect categories sorted by total mentions
   - `product_aspect_data`: List[ProductAspectData] - Aspect data for each product, grouped by ASIN with nested aspect_data arrays
   - `selected_asins`: List[str] - List of ASINs that were requested
   - `aspect_type`: str - Aspect type that was filtered
   - `total_categories`: int - Total number of categories returned

### Service Methods

#### Summary Methods:
1. **`get_competitor_summary(project_id, selected_asins)`**
   - Orchestrates all data retrieval operations
   - Filters data by project_id
   - Combines product data, review counts, and additional metrics
   - Returns comprehensive competitor summary

2. **`_get_product_summary_data(selected_asins)`**
   - Queries `product_wide_table` for product information
   - Returns dict mapping ASIN to product data

3. **`_get_unique_review_counts(project_id, selected_asins)`**
   - Queries `review_aspect_data_view` for review data filtered by project_id
   - Calculates unique review counts per product using `review_id` deduplication

4. **`_get_additional_metrics(project_id, selected_asins)`**
   - Analyzes sentiment distribution and category counts filtered by project_id
   - Returns metrics including positive/negative/neutral aspects and unique categories

#### Matrix View Methods:
5. **`get_matrix_view_data(project_id, selected_asins, aspect_type, top_n)`**
   - Orchestrates matrix view data retrieval
   - Filters data by project_id
   - Maps aspect_type to database values (phy_perf → ["phy", "perf"], use → ["use"])
   - Returns comprehensive matrix view data

6. **`_get_top_aspect_categories(project_id, selected_asins, aspect_types, top_n)`**
   - Queries `matrix_review_data` for category statistics filtered by project_id
   - Calculates total mentions per category
   - Returns top N categories sorted by total mentions

7. **`_get_category_info(category_pks)`**
   - Queries `review_analysis_aspect_categories` for category details
   - Returns category names and definitions

8. **`_get_product_aspect_data(project_id, selected_asins, category_pks)`**
   - Gets detailed product-category statistics filtered by project_id
   - Calculates mentions, sentiment distribution, and unique review counts
   - Returns comprehensive product aspect data

## Key Features

1. **Clean Architecture**: Separation of concerns with service layer handling all business logic
2. **Efficient Data Retrieval**: Direct Supabase queries to multiple tables
3. **Unique Review Counting**: Properly counts unique reviews per product using `review_id` deduplication
4. **Comprehensive Metrics**: Includes sentiment distribution and category analysis
5. **Aspect Type Filtering**: Supports "phy_perf" (physical/performance) and "use" (usability) filtering
6. **Top N Filtering**: Configurable number of top aspect categories to include
7. **Error Handling**: Comprehensive error handling with fallback values
8. **Logging**: Detailed logging for debugging and monitoring
9. **Type Safety**: Full Pydantic model validation for request/response

## Usage Examples

### Summary API
```bash
curl -X POST "http://localhost:8000/competitor-analysis/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "project-uuid",
    "selected_asins": ["B00NG0ELL0", "B0BVKZLT3B", "B01EZV35QU"]
  }'
```

### Matrix View API
```bash
curl -X POST "http://localhost:8000/competitor-analysis/matrix-view" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "project-uuid",
    "selected_asins": ["B00NG0ELL0", "B0BVKZLT3B", "B01EZV35QU"],
    "aspect_type": "phy_perf",
    "filter": {
      "top_n": 10
    }
  }'
```

## Test Results

The APIs have been tested with real data and show:
- ✅ Service layer working correctly
- ✅ Product data retrieval working correctly
- ✅ Unique review counting working correctly  
- ✅ Additional metrics calculation working correctly
- ✅ Matrix view data retrieval working correctly
- ✅ Aspect type filtering working correctly
- ✅ Top N filtering working correctly
- ✅ Proper error handling and logging

Sample test results for 3 ASINs:
- **Summary API**: 3 products with comprehensive metrics
- **Matrix View API (phy_perf)**: 5 categories with mentions ranging from 24-31
- **Matrix View API (use)**: 3 categories with mentions ranging from 11-15

## Benefits of Implementation

1. **Maintainability**: Business logic is centralized in the service layer
2. **Testability**: Service can be easily unit tested independently
3. **Reusability**: Service can be used by other parts of the application
4. **Clean API**: API endpoints are focused on request/response handling
5. **Separation of Concerns**: Clear separation between data access, business logic, and API handling
6. **Flexibility**: Support for different aspect types and configurable filtering
7. **Comprehensive Data**: Rich data structures with detailed metrics and statistics

## Integration

These APIs integrate seamlessly with the existing dashboard infrastructure:
- Uses existing database connection patterns
- Follows established error handling conventions
- Compatible with existing logging and monitoring
- Maintains consistent API response patterns 