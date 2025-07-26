# Review Analysis Tests

This directory contains comprehensive tests for the Review Analysis module.

## Test Files

### `test_models.py`
- **Purpose**: Unit tests for Pydantic models
- **Tests**: Request/response model validation
- **Run**: `python test_models.py`

### `test_review_analysis_apis.py`
- **Purpose**: Integration tests for service methods
- **Tests**: 
  - Top categories API with different sorting options
  - Reviews by category API with pagination
  - Direct service method testing
- **Run**: `python test_review_analysis_apis.py`

### `test_review_analysis_http.py`
- **Purpose**: HTTP API endpoint testing
- **Tests**: 
  - Direct HTTP requests to API endpoints
  - End-to-end API testing
- **Run**: `python test_review_analysis_http.py`
- **Note**: Requires running FastAPI server on localhost:8000

## Running Tests

### From the tests directory:
```bash
cd backend/dashboard/charts/reviewAnalysis/tests

# Run model tests
python test_models.py

# Run service integration tests
python test_review_analysis_apis.py

# Run HTTP API tests (requires server running)
python test_review_analysis_http.py
```

### From the backend directory:
```bash
cd backend

# Run all tests
python -m pytest dashboard/charts/reviewAnalysis/tests/

# Run specific test file
python dashboard/charts/reviewAnalysis/tests/test_models.py
```

## Test Data

- **Project ID**: `d2c02b80-4c82-44cc-8093-56708a7883f7`
- **Test Categories**: Core Device Functionality, Physical Installation Process, etc.
- **Test Reviews**: Real review data from the database

## Expected Results

### Top Categories API
- ✅ Aspect type filtering (phy_perf, use)
- ✅ Sorting options (mentions, positive_mentions, negative_mentions, positive_ratio)
- ✅ Category statistics with sentiment analysis
- ✅ Summary statistics across all categories

### Reviews by Category API
- ✅ Review deduplication
- ✅ Aspect aggregation per review
- ✅ Product information included
- ✅ Pagination support
- ✅ Multiple sorting options

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