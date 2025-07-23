# Sales History Service

A comprehensive service for scraping, storing, and retrieving sales history data from Jungle Scout API with smart logic to avoid duplicate data collection.

## Features

- **Smart Scraping Logic**: Avoids duplicate scraping by checking existing data coverage
- **Dual Data Storage**: Daily and monthly aggregated data tables
- **Comprehensive API**: Full CRUD operations with proper error handling
- **Date Constraints**: Enforces 365-day limit for historical data
- **Automatic Aggregation**: Monthly data automatically aggregated from daily data
- **Project Integration**: Works with existing product database structure
- **Multi-Platform Support**: Supports different platform sources (amazon, walmart, etc.)
- **Multi-API Support**: Supports different data source APIs (jungle_scout, etc.)

## Architecture

```
sales_history/
├── __init__.py                    # Module exports
├── models.py                      # Pydantic data models
├── api.py                         # FastAPI routes
├── sql/
│   └── 001_create_sales_history_tables.sql  # Database schema
├── repositories/
│   ├── __init__.py
│   ├── sales_history_repository.py           # Daily data operations
│   └── sales_history_monthly_repository.py   # Monthly data operations
├── services/
│   ├── __init__.py
│   ├── sales_history_service.py              # Main business logic
│   └── sales_history_scraper_service.py      # Jungle Scout API integration
└── README.md                      # This file
```

## Database Schema

### Daily Product Sales History Table (`product_sales_history_daily`)

```sql
CREATE TABLE product_sales_history_daily (
    id BIGSERIAL PRIMARY KEY,
    platform_id VARCHAR(20) NOT NULL,                    -- ASIN from product_wide_table
    platform_source VARCHAR(50) NOT NULL DEFAULT 'amazon', -- Platform source (amazon, walmart, etc.)
    api_source VARCHAR(50) NOT NULL DEFAULT 'jungle_scout', -- Data source API (jungle_scout, etc.)
    date DATE NOT NULL,                                  -- Sales date
    estimated_units_sold INTEGER NOT NULL CHECK (estimated_units_sold >= 0),
    last_known_price DECIMAL(10,2) NOT NULL CHECK (last_known_price >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_platform_date UNIQUE (platform_id, platform_source, date),
    CONSTRAINT fk_product_sales_history_platform_id FOREIGN KEY (platform_id) 
        REFERENCES product_wide_table(platform_id) ON DELETE CASCADE
);
```

### Monthly Aggregated Product Sales History Table (`product_sales_history_monthly`)

```sql
CREATE TABLE product_sales_history_monthly (
    id BIGSERIAL PRIMARY KEY,
    platform_id VARCHAR(20) NOT NULL,                    -- ASIN from product_wide_table
    platform_source VARCHAR(50) NOT NULL DEFAULT 'amazon', -- Platform source (amazon, walmart, etc.)
    api_source VARCHAR(50) NOT NULL DEFAULT 'jungle_scout', -- Data source API (jungle_scout, etc.)
    year_month DATE NOT NULL,                            -- First day of month (YYYY-MM-01)
    total_units_sold INTEGER NOT NULL CHECK (total_units_sold >= 0),
    average_price DECIMAL(10,2) NOT NULL CHECK (average_price >= 0),
    days_in_month INTEGER NOT NULL CHECK (days_in_month >= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_platform_month UNIQUE (platform_id, platform_source, year_month),
    CONSTRAINT fk_product_sales_history_monthly_platform_id FOREIGN KEY (platform_id) 
        REFERENCES product_wide_table(platform_id) ON DELETE CASCADE
);
```

## Data Contracts

### Scraping Request

```json
{
  "asins": ["B00NG0ELL0", "B01EZV35QU"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "platform_source": "amazon",
  "api_source": "jungle_scout"
}
```

### Scraping Response

```json
{
  "success": true,
  "message": "Scraping completed: 2 scraped, 0 skipped, 0 failed",
  "scraping_summary": {
    "total_requested": 2,
    "scraped": 2,
    "skipped": 0,
    "failed": 0,
    "invalid_asins": [],
    "scraping_errors": {}
  },
  "warnings": [],
  "data": {
    "B00NG0ELL0": [
      {
        "sales_date": "2024-01-01",
        "estimated_units_sold": 150,
        "last_known_price": 29.99
      }
    ]
  }
}
```

## API Endpoints

### Scrape Sales History

**POST** `/api/v1/sales-history/scrape`

Scrape sales history for multiple ASINs with smart logic to avoid duplicates.

**POST** `/api/v1/sales-history/scrape/project/{project_id}`

Scrape sales history for all products in a project based on `selected_product_asins`.

### Query Sales History

**GET** `/api/v1/sales-history/daily`

Get daily sales history data for multiple ASINs.

**GET** `/api/v1/sales-history/monthly`

Get monthly aggregated sales history data for multiple ASINs.

### Statistics and Management

**GET** `/api/v1/sales-history/stats/{asin}`

Get comprehensive statistics for an ASIN's sales data.

**DELETE** `/api/v1/sales-history/{asin}`

Delete sales data for an ASIN within a date range.

## Usage Examples

### Scrape Project Sales History

```bash
# Scrape all products in a project
curl -X POST "http://localhost:8000/api/v1/sales-history/scrape/project/your-project-id"

# Scrape with date range
curl -X POST "http://localhost:8000/api/v1/sales-history/scrape/project/your-project-id?start_date=2024-01-01&end_date=2024-12-31"

# Scrape with custom sources
curl -X POST "http://localhost:8000/api/v1/sales-history/scrape/project/your-project-id?platform_source=amazon&api_source=jungle_scout"
```

### Query Sales Data

```bash
# Get daily data
curl "http://localhost:8000/api/v1/sales-history/daily?asins=B00NG0ELL0,B01EZV35QU&start_date=2024-01-01&end_date=2024-12-31"

# Get monthly data
curl "http://localhost:8000/api/v1/sales-history/monthly?asins=B00NG0ELL0,B01EZV35QU&platform_source=amazon&api_source=jungle_scout"
```

## Key Features

### Smart Scraping Logic

- **Coverage Checking**: Before scraping, checks existing data coverage
- **Duplicate Prevention**: Skips ASINs with complete data coverage
- **Date Constraints**: Enforces 365-day limit for historical data
- **Flexible Date Ranges**: Supports various date range combinations

### Data Management

- **Automatic Aggregation**: Monthly data automatically aggregated from daily data
- **Conflict Resolution**: Uses upsert operations to handle duplicates
- **Cascade Deletion**: Automatically deletes related data when products are removed
- **Multi-Source Support**: Supports different platform sources and API sources

### Error Handling

- **Comprehensive Validation**: Validates ASINs, dates, and data integrity
- **Graceful Degradation**: Continues processing even if some ASINs fail
- **Detailed Error Reporting**: Provides specific error messages and warnings
- **HTTP Status Codes**: Returns appropriate status codes for different scenarios

## Integration

The service integrates with the existing product database structure:

- **Foreign Key Relationships**: Links to `product_wide_table` via `platform_id`
- **Project Integration**: Works with project `selected_product_asins`
- **Source Filtering**: Filters by platform source to match product data
- **Consistent Naming**: Uses consistent field names across the system 