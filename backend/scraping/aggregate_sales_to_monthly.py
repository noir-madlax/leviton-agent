#!/usr/bin/env python3
"""
Sales History Monthly Aggregation Script

This script aggregates daily sales history CSV files to monthly data.
It processes all CSV files in the sales_history_output directory structure
and creates aggregated monthly files in a new monthly_sales_history_output directory
with the exact same folder structure and file naming convention.

Usage:
    python aggregate_sales_to_monthly.py

The script will:
1. Read all CSV files from sales_history_output/
2. Aggregate daily data to monthly data (sum units, average price)
3. Create monthly_sales_history_output/ with same structure
4. Save aggregated monthly data with same file names
"""

import os
import sys
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_DIR = Path(__file__).parent / "sales_history_output"
OUTPUT_DIR = Path(__file__).parent / "monthly_sales_history_output"

# CSV field names
DATE_FIELD = 'date'
UNITS_FIELD = 'estimated_units_sold'
PRICE_FIELD = 'last_known_price'

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

def get_month_key(date_str: str) -> str:
    """
    Convert date string to month key (YYYY-MM format)
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        str: Month key in YYYY-MM format
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%Y-%m')
    except ValueError as e:
        logger.error(f"Invalid date format '{date_str}': {e}")
        return None

def aggregate_daily_to_monthly(csv_file_path: Path) -> List[Dict[str, Any]]:
    """
    Aggregate daily sales data to monthly data
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        List[Dict[str, Any]]: List of monthly aggregated records
    """
    monthly_data = defaultdict(lambda: {'total_units': 0, 'price_sum': 0, 'price_count': 0})
    
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                date_str = row.get(DATE_FIELD)
                units_str = row.get(UNITS_FIELD)
                price_str = row.get(PRICE_FIELD)
                
                if not all([date_str, units_str, price_str]):
                    logger.warning(f"Skipping incomplete row in {csv_file_path}: {row}")
                    continue
                
                try:
                    units = int(units_str)
                    price = float(price_str)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid numeric data in {csv_file_path}: units={units_str}, price={price_str}")
                    continue
                
                month_key = get_month_key(date_str)
                if month_key is None:
                    continue
                
                # Aggregate data
                monthly_data[month_key]['total_units'] += units
                monthly_data[month_key]['price_sum'] += price
                monthly_data[month_key]['price_count'] += 1
        
        # Convert to list of records
        monthly_records = []
        for month_key in sorted(monthly_data.keys()):
            data = monthly_data[month_key]
            avg_price = data['price_sum'] / data['price_count'] if data['price_count'] > 0 else 0
            
            monthly_records.append({
                'date': f"{month_key}-01",  # Use first day of month as representative date
                'estimated_units_sold': data['total_units'],
                'last_known_price': round(avg_price, 2)
            })
        
        logger.info(f"Aggregated {csv_file_path.name} to {len(monthly_records)} monthly records")
        return monthly_records
        
    except Exception as e:
        logger.error(f"Error processing {csv_file_path}: {e}")
        return []

def save_monthly_data(output_file_path: Path, monthly_records: List[Dict[str, Any]]):
    """
    Save monthly aggregated data to CSV file
    
    Args:
        output_file_path: Path to save the CSV file
        monthly_records: List of monthly aggregated records
    """
    try:
        # Ensure parent directory exists
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [DATE_FIELD, UNITS_FIELD, PRICE_FIELD]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in monthly_records:
                writer.writerow(record)
        
        logger.info(f"Saved monthly data to: {output_file_path}")
        
    except Exception as e:
        logger.error(f"Error saving monthly data to {output_file_path}: {e}")

def process_directory(input_dir: Path, output_dir: Path):
    """
    Process all CSV files in a directory and its subdirectories
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
    """
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    successful_count = 0
    failed_count = 0
    
    # Find all CSV files recursively
    csv_files = list(input_dir.rglob("*.csv"))
    logger.info(f"Found {len(csv_files)} CSV files to process")
    
    for csv_file in csv_files:
        try:
            # Calculate relative path from input directory
            relative_path = csv_file.relative_to(input_dir)
            
            # Create corresponding output path
            output_file = output_dir / relative_path
            
            logger.info(f"Processing: {relative_path}")
            
            # Aggregate daily data to monthly
            monthly_records = aggregate_daily_to_monthly(csv_file)
            
            if monthly_records:
                # Save monthly data
                save_monthly_data(output_file, monthly_records)
                successful_count += 1
            else:
                logger.warning(f"No monthly data generated for: {relative_path}")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
            failed_count += 1
    
    return successful_count, failed_count

def main():
    """Main execution function"""
    logger.info("Starting Sales History Monthly Aggregation Script")
    logger.info(f"Input directory: {INPUT_DIR}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    
    try:
        # Ensure output directory exists
        ensure_output_directory()
        
        # Process all directories
        successful_count, failed_count = process_directory(INPUT_DIR, OUTPUT_DIR)
        
        # Summary
        logger.info("=" * 60)
        logger.info("AGGREGATION COMPLETION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Successful: {successful_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Output directory: {OUTPUT_DIR}")
        
        if successful_count > 0:
            logger.info("✅ Monthly aggregation completed successfully!")
        else:
            logger.error("❌ No files were successfully processed")
            
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main() 