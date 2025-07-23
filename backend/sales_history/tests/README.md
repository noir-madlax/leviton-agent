# Sales History API Tests

This directory contains comprehensive tests for the sales history API endpoints, including test execution, database result inspection, and cleanup utilities.

## Files

- `test_sales_history_api.py` - Main test script for all API endpoints
- `verify_changes.py` - Verification script for new schema changes
- `clear_test_data.py` - Script to clean up test data from database
- `run_tests.sh` - Shell script to run tests and cleanup in sequence
- `README.md` - This documentation file

## Prerequisites

Before running tests, ensure you have:

1. **Environment Variables** set in `backend/.env`:
   ```bash
   JUNGLE_SCOUT_API_KEY=KEY_NAME:API_KEY
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   ```

2. **Database Tables** created using the SQL migration:
   ```bash
   # Run the SQL file to create tables
   psql -h your_host -U your_user -d your_db -f backend/sales_history/sql/001_create_sales_history_tables.sql
   ```

3. **Test ASINs** in the `product_wide_table`:
   - The test script uses these ASINs by default:
     - `B08N5WRWNW`
     - `B07ZPKBL9V`
     - `B08SJ3Z8XD`
   - You can modify the `TEST_ASINS` list in `test_sales_history_api.py`

## Schema Changes

The sales history service has been updated with the following schema changes:

### New Field Structure
- **`platform_source`**: Platform source (amazon, walmart, etc.) - defaults to "amazon"
- **`api_source`**: Data source API (jungle_scout, etc.) - defaults to "jungle_scout"
- **Table Names**: 
  - `sales_history_daily` → `product_sales_history_daily`
  - `sales_history_monthly` → `product_sales_history_monthly`

### Updated Constraints
- Unique constraints now include `platform_source`
- Foreign key constraints reference only `platform_id` (not composite keys)

## Running Tests

### Option 1: Verify Schema Changes First

```bash
cd backend/sales_history/tests

# Verify the new schema works correctly
python3 verify_changes.py
```

### Option 2: Using the Shell Script (Recommended)

```bash
cd backend/sales_history/tests

# Make the script executable
chmod +x run_tests.sh

# Run full test suite with cleanup
./run_tests.sh

# Run tests only (no cleanup)
./run_tests.sh --test-only

# Run cleanup only
./run_tests.sh --cleanup-only

# Show what would be cleaned up without deleting
./run_tests.sh --dry-run

# Show current data summary
./run_tests.sh --summary
```

### Option 3: Running Individual Scripts

```bash
cd backend/sales_history/tests

# Verify changes first
python3 verify_changes.py

# Run tests
python3 test_sales_history_api.py

# Clear test data
python3 clear_test_data.py

# Show data summary
python3 clear_test_data.py --summary

# Dry run cleanup
python3 clear_test_data.py --dry-run
```

## Test Coverage

The test suite covers the following areas:

### 1. Schema Verification (`verify_changes.py`)
- **Model Structure**: Verifies new field structure in Pydantic models
- **Repository Methods**: Tests repository methods with new fields
- **Service Methods**: Tests service methods with new fields
- **Database Structure**: Verifies table structure and column existence
- **API Compatibility**: Ensures API endpoints work with new structure

### 2. ASIN Validation
- Checks if test ASINs exist in `product_wide_table`
- Validates ASIN format and existence with platform source filtering
- Filters valid ASINs for subsequent tests

### 3. Sales History Scraping
- Tests the scraping endpoint with smart logic
- Validates date constraints (365-day limit)
- Tests coverage checking to avoid duplicate scraping
- Tests new field structure (platform_source, api_source)
- Prints scraped data for manual inspection

### 4. Daily Sales History Retrieval
- Tests GET `/daily` endpoint
- Validates date filtering functionality
- Tests source filtering with new field structure
- Prints retrieved data for manual inspection

### 5. Monthly Sales History Retrieval
- Tests GET `/monthly` endpoint
- Validates monthly aggregation logic
- Tests date range filtering
- Tests new field structure
- Prints aggregated data for manual inspection

### 6. Sales Statistics
- Tests GET `/stats/{asin}` endpoint
- Validates both daily and monthly statistics
- Tests date range filtering for stats
- Tests new field structure
- Prints comprehensive statistics

### 7. Date Filtering
- Tests various date range combinations
- Validates filtering logic
- Tests edge cases (7 days, 14 days, 30 days)
- Tests with new field structure

### 8. Error Handling
- Tests with invalid ASINs
- Tests with invalid date ranges
- Validates error response formats
- Tests graceful degradation

## Test Output

The test script provides detailed output including:

### Schema Verification Results
```
============================================================
VERIFYING SALES HISTORY CHANGES
============================================================

========================================
VERIFYING MODEL STRUCTURE
========================================
✅ SalesHistoryScrapingRequest created successfully
  platform_source: amazon
  api_source: jungle_scout
✅ SalesHistoryQueryRequest created successfully
  platform_source: amazon
  api_source: jungle_scout

========================================
VERIFYING REPOSITORY METHODS
========================================
✅ ASIN validation with platform_source works
  Results: {'B08N5WRWNW': True, 'B07ZPKBL9V': True}
✅ Data coverage with new fields works
✅ Data retrieval with new fields works
  Retrieved data for 2 ASINs
```

### Database Results
```
Scraped Data:
  B08N5WRWNW: 30 records
    1. 2024-07-19: 53 units @ $3.5
    2. 2024-07-20: 45 units @ $3.5
    3. 2024-07-21: 66 units @ $3.5
    ... and 27 more records
```

### Test Summary
```
============================================================
TEST EXECUTION SUMMARY
============================================================
Total Tests: 8
Passed: 8
Failed: 0
Success Rate: 100.0%

Detailed Results:
  ✅ ASIN Validation: PASS
    valid_asins: ['B08N5WRWNW', 'B07ZPKBL9V']
    invalid_asins: ['INVALID_ASIN']
  ✅ Sales History Scraping: PASS
    scraped_asins: 2
    skipped_asins: 0
    failed_asins: 0
    total_records: 60
```

## Cleanup Options

The cleanup script provides several options:

### Clear Test ASINs Only
```bash
python3 clear_test_data.py
```

### Clear Specific ASINs
```bash
python3 clear_test_data.py --asins B08N5WRWNW,B07ZPKBL9V
```

### Clear All Data (Use with Caution!)
```bash
python3 clear_test_data.py --all
```

### Dry Run (Preview)
```bash
python3 clear_test_data.py --dry-run
```

### Show Data Summary
```bash
python3 clear_test_data.py --summary
```

## Manual Database Inspection

After running tests, you can manually inspect the database:

### Check Daily Data
```sql
SELECT 
    platform_id,
    platform_source,
    api_source,
    COUNT(*) as record_count,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    SUM(estimated_units_sold) as total_units,
    AVG(last_known_price) as avg_price
FROM product_sales_history_daily
WHERE platform_id IN ('B08N5WRWNW', 'B07ZPKBL9V', 'B08SJ3Z8XD')
GROUP BY platform_id, platform_source, api_source
ORDER BY record_count DESC;
```

### Check Monthly Data
```sql
SELECT 
    platform_id,
    platform_source,
    api_source,
    COUNT(*) as month_count,
    MIN(year_month) as earliest_month,
    MAX(year_month) as latest_month,
    SUM(total_units_sold) as total_units,
    AVG(average_price) as avg_price
FROM product_sales_history_monthly
WHERE platform_id IN ('B08N5WRWNW', 'B07ZPKBL9V', 'B08SJ3Z8XD')
GROUP BY platform_id, platform_source, api_source
ORDER BY month_count DESC;
```

### Check Data Coverage
```sql
SELECT 
    platform_id,
    platform_source,
    api_source,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(*) as total_days,
    COUNT(DISTINCT DATE_TRUNC('month', date)) as total_months
FROM product_sales_history_daily
WHERE platform_id IN ('B08N5WRWNW', 'B07ZPKBL9V', 'B08SJ3Z8XD')
GROUP BY platform_id, platform_source, api_source;
```

## Troubleshooting

### Common Issues

1. **No valid ASINs found**
   - Ensure test ASINs exist in `product_wide_table`
   - Check ASIN format and case sensitivity
   - Verify database connection
   - Check that ASINs have `source = 'amazon'` in product_wide_table

2. **Jungle Scout API errors**
   - Verify `JUNGLE_SCOUT_API_KEY` is set correctly
   - Check API key format: `KEY_NAME:API_KEY`
   - Ensure API key has sufficient permissions

3. **Database connection errors**
   - Verify Supabase credentials in `.env`
   - Check network connectivity
   - Ensure database tables exist with new names

4. **Schema validation errors**
   - Run `verify_changes.py` first to check schema
   - Ensure tables have been created with new structure
   - Check that all columns exist (platform_source, api_source)

5. **Date constraint errors**
   - Tests use recent dates (last 30 days)
   - Ensure system date is correct
   - Check for timezone issues

### Debug Mode

To enable debug logging, modify the logging level in the test script:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Test Customization

To test with different ASINs, modify the `TEST_ASINS` list in `test_sales_history_api.py`:

```python
TEST_ASINS = [
    "YOUR_ASIN_1",
    "YOUR_ASIN_2", 
    "YOUR_ASIN_3",
    "INVALID_ASIN"
]
```

## Performance Notes

- Tests are designed to be lightweight and use recent data
- Scraping tests use 30-day date ranges to minimize API calls
- Cleanup operations are optimized for batch processing
- Database queries include proper indexing for performance
- New field structure improves query performance with better filtering

## Integration with CI/CD

The test scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Verify Schema Changes
  run: |
    cd backend/sales_history/tests
    python3 verify_changes.py
    
- name: Run Sales History Tests
  run: |
    cd backend/sales_history/tests
    python3 test_sales_history_api.py
    
- name: Cleanup Test Data
  run: |
    cd backend/sales_history/tests
    python3 clear_test_data.py
  if: always()  # Always run cleanup, even if tests fail
```

## Migration Notes

If you're upgrading from the old schema:

1. **Run verification first**: `python3 verify_changes.py`
2. **Check data compatibility**: Ensure existing data works with new structure
3. **Update any custom queries**: Use new table names and field structure
4. **Test thoroughly**: Run full test suite to ensure everything works
5. **Update documentation**: Update any custom documentation to reflect changes 