# Competitor Analysis Tests

This directory contains comprehensive tests for the Competitor Analysis module.

## Test Files

### `test_api.py`
- **Purpose**: Integration tests for service methods and API endpoints
- **Tests**:
  - Competitor summary API with product analysis
  - Matrix view API with different aspect types and sorting options
  - Review retrieval API with pagination and sorting
  - Direct HTTP API endpoint testing
- **Run**: `python test_api.py`

## Running Tests

### From the tests directory:
```bash
cd backend/dashboard/charts/competitorAnalysis/tests

# Run all tests
python test_api.py
```

### From the backend directory:
```bash
cd backend

# Run all tests
python -m pytest dashboard/charts/competitorAnalysis/tests/

# Run specific test file
python dashboard/charts/competitorAnalysis/tests/test_api.py
```

## Test Data

- **Project ID**: `d2c02b80-4c82-44cc-8093-56708a7883f7`
- **Test ASINs**: 
  - `B00NG0ELL0` (Leviton DSL06)
  - `B0BVKZLT3B` (Leviton D215S)
  - `B0BVKYKKRK` (Leviton D26HD)
  - `B0BSHKS26L` (Lutron Caseta Diva)
  - `B085D8M2MR` (Lutron Diva)
  - `B01EZV35QU` (TP Link Switch)
- **Test Categories**: Physical Installation Process, Core Device Functionality, Smart Home System Integration, etc.

## Expected Results

### Competitor Summary API
- ✅ Product information and metrics
- ✅ Review counts and sentiment distribution
- ✅ Brand and pricing data
- ✅ Category counts per product

### Matrix View API
- ✅ Aspect type filtering (phy_perf, use)
- ✅ Sorting options (mentions, reviews, sentiment)
- ✅ Category information with definitions
- ✅ Product aspect data with metrics

### Review Retrieval API
- ✅ Review deduplication (using shared reviewCore logic)
- ✅ Aspect aggregation per review
- ✅ Pagination support
- ✅ Multiple sorting options (date, rating, review_id)
- ✅ Category information included

## Key Features Tested

### 1. Shared ReviewCore Integration
- **Deduplication Logic**: Tests the updated product-based deduplication
- **Aspect Aggregation**: Verifies aspects are properly aggregated per review
- **Product Information**: Ensures product details are included where needed

### 2. Competitor Analysis Specific Features
- **Product Comparison**: Tests comparison across multiple ASINs
- **Matrix View**: Tests flexible sorting and filtering options
- **Review Retrieval**: Tests product-specific review retrieval

### 3. Data Processing
- **Rating Transformation**: Tests conversion from string to numeric ratings
- **Sentiment Analysis**: Tests positive/negative/neutral sentiment counting
- **Category Metrics**: Tests mentions, reviews, and sentiment ratios

## Test Coverage

### Service Layer Testing
- ✅ Direct service method calls
- ✅ Error handling and edge cases
- ✅ Data transformation and formatting
- ✅ Database query results processing

### API Endpoint Testing
- ✅ HTTP request/response validation
- ✅ Request model validation
- ✅ Response model formatting
- ✅ Error response handling

### Integration Testing
- ✅ Database connectivity
- ✅ Real data processing
- ✅ End-to-end functionality
- ✅ Performance with actual data volumes

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the correct directory:
- For service tests: Run from `backend/` directory
- For HTTP tests: Make sure the FastAPI server is running

### Database Connection
Tests require a valid database connection to the Supabase instance with the test project data.

### Test Project
The tests use project ID `d2c02b80-4c82-44cc-8093-56708a7883f7` which should have:
- Review data in `review_aspect_data_view`
- Category data in `review_analysis_aspect_categories`
- Product data in `product_wide_table`

## Performance Notes

- **Test Duration**: ~30-60 seconds for full test suite
- **Data Volume**: Tests with real data from 6 products and multiple categories
- **Memory Usage**: Moderate - processes actual review and aspect data
- **Network**: Requires database connection for real queries

## Future Enhancements

- **Mock Testing**: Add unit tests with mocked database responses
- **Performance Testing**: Add benchmarks for large datasets
- **Edge Case Testing**: Add tests for empty results, invalid IDs, etc.
- **Load Testing**: Test with larger product sets and review volumes 