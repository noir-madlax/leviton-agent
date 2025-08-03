# Unwrangle Amazon Product Data API Test Script

This script tests the new Unwrangle Amazon Product Data API by reading ASINs from an Excel file, sampling a subset, and saving the API responses to JSON files.

## Files Created

- `test_unwrangle_product_api.py` - Main test script
- `unwrangle_product_responses/` - Output directory for API responses
- `README_unwrangle_test.md` - This documentation

## Prerequisites

1. **Environment Variables**: Set the `UNWRANGLE_API_KEY` environment variable
   ```bash
   export UNWRANGLE_API_KEY="your_api_key_here"
   ```

2. **Dependencies**: Install required packages
   ```bash
   pip install openpyxl pandas requests
   ```

## Usage

### Basic Usage
```bash
cd backend/scraping
python test_unwrangle_product_api.py
```

### Configuration

The script can be customized by modifying these constants at the top of the file:

```python
EXCEL_FILE_PATH = "/Users/maoc/MIT Dropbox/Chengfeng Mao/JMP/UX168 data and code/data/raw/电线电缆_495310_asin_review明细.xlsx"
OUTPUT_DIR = "unwrangle_product_responses"
SAMPLE_SIZE = 50
DELAY_BETWEEN_REQUESTS = 1  # seconds
```

## What the Script Does

1. **Reads Excel File**: Reads ASINs from the specified Excel file
2. **Validates ASINs**: Filters for valid 10-character alphanumeric ASINs
3. **Samples ASINs**: Randomly selects 50 ASINs (or all if less than 50)
4. **Calls API**: Makes requests to Unwrangle Product Data API for each ASIN
5. **Saves Responses**: Saves individual JSON files for each successful response
6. **Creates Summary**: Generates a summary JSON file with statistics

## Output Structure

```
unwrangle_product_responses/
├── api_test_summary.json          # Summary of all requests
├── B07CWPTHYH_product_details.json # Individual product response
├── B0C7MLQB5L_product_details.json # Individual product response
└── ... (one file per ASIN)
```

## API Response Format

Each successful API response includes:
- Product name, brand, URL, ASIN
- Current and original prices
- Availability status
- Rating and review count
- Product images
- Features and specifications
- Sample reviews
- Remaining API credits

## Error Handling

The script handles various error scenarios:
- Missing API key
- Invalid ASIN formats
- API request failures
- File I/O errors

All errors are logged and included in the summary file.

## Rate Limiting

The script includes a 1-second delay between API requests to avoid rate limiting. This can be adjusted via the `DELAY_BETWEEN_REQUESTS` constant.

## Credits Usage

- US Amazon: 1 credit per request
- Other countries: 2.5 credits per request
- 50 requests = 50-125 credits depending on country

## Example Output

```json
{
  "total_asins_processed": 50,
  "successful_requests": 45,
  "failed_requests": 5,
  "processed_asins": ["B07CWPTHYH", "B0C7MLQB5L", ...],
  "results": [...]
}
```

## Troubleshooting

1. **Missing API Key**: Ensure `UNWRANGLE_API_KEY` is set in environment
2. **Excel File Not Found**: Check the `EXCEL_FILE_PATH` constant
3. **Invalid ASINs**: The script will skip invalid ASIN formats
4. **API Errors**: Check the summary file for specific error messages 