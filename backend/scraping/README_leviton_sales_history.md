# Leviton Sales History Script

This script fetches sales history data for Leviton brand products in the dimmer switches category using the Jungle Scout API.

## Overview

The script performs the following steps:

1. **Queries Supabase**: Fetches ASINs from the `amazon_products` table for Leviton brand products in category_l5_id 507840 (Dimmer Switches)
2. **Samples Products**: Randomly selects 10 products from the available ASINs
3. **Fetches Sales Data**: Uses Jungle Scout API to get sales history for the last 2 years
4. **Saves Results**: Creates individual CSV files for each product with date, estimated units sold, and last known price

## Prerequisites

### Environment Variables

Ensure the following environment variables are set in `backend/.env`:

```bash
# Jungle Scout API
JUNGLE_SCOUT_API_KEY=KEY_NAME:API_KEY

# Supabase (if not already configured)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### Jungle Scout API Key Format

The `JUNGLE_SCOUT_API_KEY` should be in the format `KEY_NAME:API_KEY` as provided by Jungle Scout.

## Usage

### Basic Usage

```bash
cd backend/scraping
python leviton_sales_history_script.py
```

### Output

The script creates a `sales_history_output` directory containing CSV files:

```
sales_history_output/
├── leviton_B08N5WRWNW_sales_20250115_143022.csv
├── leviton_B07ZPKBL9V_sales_20250115_143045.csv
└── ...
```

Each CSV file contains:
- `date`: Date of the sales record
- `estimated_units_sold`: Estimated number of units sold
- `last_known_price`: Last known price for the product

## Configuration

You can modify the following constants in the script:

```python
CATEGORY_L5_ID = 507840  # Dimmer Switches category
BRAND_NAME = "Leviton"   # Brand to search for
SAMPLE_SIZE = 10         # Number of products to sample
MARKETPLACE = "us"       # Marketplace (us, uk, de, etc.)
```

## Date Range

The script fetches data for the last 2 years:
- **End Date**: Yesterday
- **Start Date**: 730 days before end date

## Error Handling

The script includes comprehensive error handling:

- **API Errors**: Logs Jungle Scout API errors and continues with next ASIN
- **Database Errors**: Logs Supabase connection issues
- **File Errors**: Logs CSV writing errors
- **Summary Report**: Provides completion statistics

## Logging

The script provides detailed logging:

```
2025-01-15 14:30:22 - INFO - Starting Leviton Sales History Script
2025-01-15 14:30:22 - INFO - Category L5 ID: 507840 (Dimmer Switches)
2025-01-15 14:30:22 - INFO - Brand: Leviton
2025-01-15 14:30:22 - INFO - Sample size: 10
2025-01-15 14:30:22 - INFO - Date range: 2023-01-15 to 2025-01-14
2025-01-15 14:30:23 - INFO - Querying Supabase for Leviton ASINs...
2025-01-15 14:30:24 - INFO - Found 25 Leviton products in dimmer switches category
2025-01-15 14:30:24 - INFO - Sampled 10 ASINs from 25 total
2025-01-15 14:30:24 - INFO - Processing ASIN 1/10: B08N5WRWNW
2025-01-15 14:30:25 - INFO - Fetching sales history for ASIN: B08N5WRWNW
2025-01-15 14:30:26 - INFO - Successfully fetched sales history for ASIN: B08N5WRWNW
2025-01-15 14:30:26 - INFO - Extracted 730 sales records
2025-01-15 14:30:26 - INFO - Saved sales data to: sales_history_output/leviton_B08N5WRWNW_sales_20250115_143026.csv
...
```

## Troubleshooting

### Common Issues

1. **No ASINs Found**
   - Verify that `amazon_products` table contains data for category_l5_id 507840
   - Check that brand name "Leviton" matches exactly (case-sensitive)

2. **Jungle Scout API Errors**
   - Verify API key format: `KEY_NAME:API_KEY`
   - Check API key permissions and marketplace access
   - Ensure the API key supports the US marketplace

3. **Database Connection Issues**
   - Verify Supabase credentials in `.env`
   - Check network connectivity to Supabase

4. **No Sales Data**
   - Some products may not have sales data available
   - Check Jungle Scout API documentation for data availability

### Debug Mode

To enable debug logging, modify the logging level:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## API Response Structure

The script expects Jungle Scout API responses in this format:

```json
{
  "data": [
    {
      "date": "2024-01-15",
      "estimated_units_sold": 150,
      "last_known_price": 29.99
    }
  ]
}
```

If the API response structure differs, you may need to modify the `extract_sales_data()` function.

## Dependencies

The script requires the following Python packages:
- `requests` (for API calls)
- `supabase` (for database access)
- `python-dotenv` (for environment variables)

These should already be installed in your environment.

## Related Files

- `common/jungle_scout_api.py`: Jungle Scout API client
- `core/database/connection.py`: Supabase database connection
- `jungle_scout_cli.py`: Command-line interface for Jungle Scout API 