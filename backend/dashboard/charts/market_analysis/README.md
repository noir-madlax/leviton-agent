# Market Analysis API Implementation

## Overview

This module implements the Total Addressable Market (TAM) and Market Share analysis API for the Market Analysis dashboard section. It provides comprehensive market size calculations and brand market share analysis grouped by product categories.

## API Endpoint

**Endpoint:** `POST /api/v1/dashboard/charts/market-analysis/tam-market-share`

**Request:**
```json
{
    "project_id": "project-uuid",
    "filters": {
        "categories": ["Dimmer Switches", "Light Switches"],
        "brands": ["Leviton", "Lutron"],
        "segments": ["Premium", "Standard"],
        "extend_fields": {
            "smart_capability": "Smart"
        }
    }
}
```

**Response:**
```json
{
    "tam_data": {
        "total_market_revenue": 15000000.50,
        "total_market_volume": 25000,
        "total_products": 1250,
        "currency": "USD"
    },
    "market_share_by_category": [
        {
            "category": "Dimmer Switches",
            "total_revenue": 8000000.25,
            "total_volume": 12000,
            "total_products": 600,
            "brand_shares": [
                {
                    "brand": "Leviton",
                    "revenue": 3200000.10,
                    "volume": 4800,
                    "product_count": 240,
                    "market_share_percentage": 40.0,
                    "rank": 1
                },
                {
                    "brand": "Lutron",
                    "revenue": 2400000.08,
                    "volume": 3600,
                    "product_count": 180,
                    "market_share_percentage": 30.0,
                    "rank": 2
                }
            ]
        }
    ],
    "metadata": {
        "filtered_asins_count": 1250,
        "total_categories": 2,
        "total_brands": 15,
        "calculation_timestamp": "2024-01-15T10:30:00Z"
    }
}
```

## Architecture

### Service Layer (`service.py`)

The `TAMMarketShareService` class handles all data processing:

1. **`get_tam_market_share_data()`**: Main orchestration method
2. **`_get_product_data_from_wide_table()`**: Retrieves product data from `product_wide_table`
3. **`_calculate_market_shares()`**: Calculates TAM and market shares by category
4. **`_generate_metadata()`**: Generates analysis metadata

### Data Flow

1. **Filter Application**: Uses `get_filtered_asins()` from asin_filter_service to get filtered ASIN list
2. **Data Retrieval**: Queries `product_wide_table` for product information
3. **Aggregation**: Groups data by category and brand, calculates market shares
4. **Response Formatting**: Structures data for frontend consumption

### Data Sources

**Product Information (`product_wide_table`)**
- `platform_id` (ASIN)
- `brand` (Product brand)
- `category` (Product category)
- `past_year_revenue` (Annual revenue)
- `past_year_volume` (Annual volume)

## Key Features

1. **Unified Filtering**: Uses `get_filtered_asins()` from asin_filter_service for consistent data filtering
2. **Complete TAM Calculation**: Backend calculates total market size across all categories
3. **Category-Based Market Share**: Detailed brand analysis within each category
4. **Ranking System**: Brands ranked by revenue within each category
5. **Comprehensive Metadata**: Analysis statistics and timestamps
6. **Error Handling**: Graceful handling of missing data and edge cases

## Frontend Integration

This API is designed to replace the frontend calculations in the Market Analysis component:

- **Before**: Frontend aggregated data from `brandCategoryRevenue` 
- **After**: Backend provides pre-calculated TAM and market share data
- **Benefits**: Improved performance, consistent calculations, reduced frontend complexity

## Usage Example

```bash
curl -X POST "http://localhost:8000/api/v1/dashboard/charts/market-analysis/tam-market-share" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "filters": {
      "categories": ["Dimmer Switches"],
      "brands": ["Leviton", "Lutron"]
    }
  }'
```

## Implementation Benefits

1. **Performance**: Backend aggregation reduces frontend processing
2. **Consistency**: Unified filtering ensures data accuracy
3. **Maintainability**: Centralized business logic
4. **Scalability**: Efficient database queries handle large datasets
5. **Flexibility**: Supports all existing filter types
6. **Type Safety**: Full Pydantic model validation
