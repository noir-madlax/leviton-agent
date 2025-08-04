# Sales History Monthly Aggregation

This directory contains scripts for aggregating daily sales history data to monthly data.

## Files

- `aggregate_sales_to_monthly.py` - Main script to aggregate daily sales data to monthly data
- `leviton_sales_history_script.py` - Original script that generates daily sales data

## Usage

### Generate Monthly Aggregated Data

```bash
cd backend/scraping
python aggregate_sales_to_monthly.py
```

This script will:
1. Read all CSV files from `sales_history_output/`
2. Aggregate daily data to monthly data:
   - Sum the `estimated_units_sold` for each month
   - Calculate the average `last_known_price` for each month
3. Create `monthly_sales_history_output/` with the exact same folder structure
4. Save aggregated monthly data with the same file names

## Directory Structure

The script maintains the exact same folder structure:

```
sales_history_output/
├── leviton_dimmer/
│   ├── leviton_B0076HPM8A_sales_20250720_184540.csv
│   └── ...
└── leviton_light_switches/
    ├── leviton_B00004YUO0_sales_20250720_184933.csv
    └── ...

monthly_sales_history_output/
├── leviton_dimmer/
│   ├── leviton_B0076HPM8A_sales_20250720_184540.csv (monthly data)
│   └── ...
└── leviton_light_switches/
    ├── leviton_B00004YUO0_sales_20250720_184933.csv (monthly data)
    └── ...
```

## Data Format

### Input (Daily Data)
```csv
date,estimated_units_sold,last_known_price
2024-07-19,21,13.99
2024-07-20,28,13.99
2024-07-21,40,13.99
...
```

### Output (Monthly Data)
```csv
date,estimated_units_sold,last_known_price
2024-07-01,273,13.99
2024-08-01,581,13.21
2024-09-01,817,7.53
...
```

## Aggregation Logic

- **Units Sold**: Sum of all daily units sold in the month
- **Price**: Average of all daily prices in the month (rounded to 2 decimal places)
- **Date**: First day of the month (YYYY-MM-01 format)

## Error Handling

The script includes comprehensive error handling:
- Skips incomplete or invalid data rows
- Logs warnings for data issues
- Continues processing even if individual files fail
- Provides summary of successful vs failed operations

## Logging

The script provides detailed logging including:
- Processing progress for each file
- Number of monthly records generated per file
- Summary statistics at completion
- Error messages for troubleshooting 