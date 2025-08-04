#!/usr/bin/env python3
"""
Leviton Sales History Script

This script queries ASINs from Supabase amazon_products table for Leviton brand products
in the dimmer switches category (category_l5_id = 507840), samples 10 products,
fetches their sales history from Jungle Scout API for the last 2 years,
and saves the results as individual CSV files.

Usage:
    python leviton_sales_history_script.py

Requirements:
    - JUNGLE_SCOUT_API_KEY in backend/.env
    - Supabase credentials in backend/.env
"""

import os
import sys
import csv
import random
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the backend directory to the path to import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import required modules
from core.database.connection import get_supabase_service_client
from common.jungle_scout_api import get_sales_history, JungleScoutAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
# CATEGORY_L5_ID = 507840  # Dimmer Switches category
CATEGORY_L5_ID = 6291359011  # Light Switches category
BRAND_NAME = "Leviton"
SAMPLE_SIZE = 10
MARKETPLACE = "us"
# OUTPUT_DIR = Path(__file__).parent / "sales_history_output" / "leviton_dimmer"
OUTPUT_DIR = Path(__file__).parent / "sales_history_output" / "leviton_light_switches"

# Date range for last 2 years
END_DATE = date.today() - timedelta(days=1)  # Yesterday
START_DATE = END_DATE - timedelta(days=365)  # 1 year ago

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

def query_leviton_asins() -> List[str]:
    """
    Query ASINs from amazon_products table for Leviton brand products
    in the dimmer switches category (category_l5_id = 507840)
    
    Returns:
        List[str]: List of ASINs (platform_ids)
    """
    try:
        logger.info("Querying Supabase for Leviton ASINs...")
        
        supabase = get_supabase_service_client()
        
        # Query amazon_products table for Leviton products in dimmer switches category
        result = supabase.table('amazon_products').select(
            'platform_id, title, brand, category_l5_id'
        ).eq('category_l5_id', CATEGORY_L5_ID).eq('brand', BRAND_NAME).execute()
        
        if not result.data:
            logger.warning(f"No products found for category_l5_id={CATEGORY_L5_ID} and brand={BRAND_NAME}")
            return []
        
        asins = [row['platform_id'] for row in result.data if row.get('platform_id')]
        logger.info(f"Found {len(asins)} Leviton products in dimmer switches category")
        
        # Log some sample products for verification
        sample_products = result.data[:3]
        for product in sample_products:
            logger.info(f"Sample product: {product['platform_id']} - {product['title'][:50]}...")
        
        return asins
        
    except Exception as e:
        logger.error(f"Error querying Supabase: {e}")
        raise

def sample_asins(asins: List[str], sample_size: int = SAMPLE_SIZE) -> List[str]:
    """
    Randomly sample ASINs from the list
    
    Args:
        asins: List of ASINs
        sample_size: Number of ASINs to sample
        
    Returns:
        List[str]: Sampled ASINs
    """
    if len(asins) <= sample_size:
        logger.info(f"Using all {len(asins)} ASINs (less than sample size {sample_size})")
        return asins
    
    sampled_asins = random.sample(asins, sample_size)
    logger.info(f"Sampled {len(sampled_asins)} ASINs from {len(asins)} total")
    return sampled_asins

def fetch_sales_history_for_asin(asin: str) -> Optional[Dict[str, Any]]:
    """
    Fetch sales history for a single ASIN from Jungle Scout API
    
    Args:
        asin: Product ASIN
        
    Returns:
        Optional[Dict[str, Any]]: Sales history data or None if error
    """
    try:
        logger.info(f"Fetching sales history for ASIN: {asin}")
        
        result = get_sales_history(
            asin=asin,
            marketplace=MARKETPLACE,
            start_date=START_DATE.strftime("%Y-%m-%d"),
            end_date=END_DATE.strftime("%Y-%m-%d")
        )
        
        logger.info(f"Successfully fetched sales history for ASIN: {asin}")
        return result
        
    except JungleScoutAPIError as e:
        logger.error(f"Jungle Scout API error for ASIN {asin}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for ASIN {asin}: {e}")
        return None

def extract_sales_data(sales_history: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract sales data from Jungle Scout API response
    
    Args:
        sales_history: Raw API response
        
    Returns:
        List[Dict[str, Any]]: List of sales records with date, estimated_units_sold, last_known_price
    """
    sales_records = []
    
    try:
        # Extract data from the API response
        # The structure is: data[0]['attributes']['data']
        data = sales_history.get('data', [])
        
        if isinstance(data, list) and len(data) > 0:
            # Get the first (and usually only) result
            first_result = data[0]
            attributes = first_result.get('attributes', {})
            sales_data = attributes.get('data', [])
            
            if isinstance(sales_data, list):
                for record in sales_data:
                    # Extract the required fields
                    sales_record = {
                        'date': record.get('date'),
                        'estimated_units_sold': record.get('estimated_units_sold'),
                        'last_known_price': record.get('last_known_price')
                    }
                    
                    # Only include records with valid data
                    if all(sales_record.values()):
                        sales_records.append(sales_record)
        
        logger.info(f"Extracted {len(sales_records)} sales records")
        
    except Exception as e:
        logger.error(f"Error extracting sales data: {e}")
        logger.error(f"Response structure: {sales_history}")
    
    return sales_records

def save_sales_to_csv(asin: str, sales_records: List[Dict[str, Any]]):
    """
    Save sales records to a CSV file
    
    Args:
        asin: Product ASIN
        sales_records: List of sales records
    """
    if not sales_records:
        logger.warning(f"No sales records to save for ASIN: {asin}")
        return
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"leviton_{asin}_sales_{timestamp}.csv"
    filepath = OUTPUT_DIR / filename
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'estimated_units_sold', 'last_known_price']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in sales_records:
                writer.writerow(record)
        
        logger.info(f"Saved sales data to: {filepath}")
        
    except Exception as e:
        logger.error(f"Error saving CSV for ASIN {asin}: {e}")

def main():
    """Main execution function"""
    logger.info("Starting Leviton Sales History Script")
    logger.info(f"Category L5 ID: {CATEGORY_L5_ID} (Dimmer Switches)")
    logger.info(f"Brand: {BRAND_NAME}")
    logger.info(f"Sample size: {SAMPLE_SIZE}")
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    
    try:
        # Ensure output directory exists
        ensure_output_directory()
        
        # Query ASINs from Supabase
        all_asins = query_leviton_asins()
        
        if not all_asins:
            logger.error("No ASINs found. Exiting.")
            return
        
        # Sample ASINs
        sampled_asins = sample_asins(all_asins)
        logger.info(f"Sampled ASINs: {sampled_asins}")
        
        # Process each ASIN
        successful_count = 0
        failed_count = 0
        
        for i, asin in enumerate(sampled_asins, 1):
            logger.info(f"Processing ASIN {i}/{len(sampled_asins)}: {asin}")
            
            # Fetch sales history
            sales_history = fetch_sales_history_for_asin(asin)
            
            if sales_history:
                # Extract sales data
                sales_records = extract_sales_data(sales_history)
                
                if sales_records:
                    # Save to CSV
                    save_sales_to_csv(asin, sales_records)
                    successful_count += 1
                else:
                    logger.warning(f"No sales records extracted for ASIN: {asin}")
                    logger.warning(f"Sales history: {sales_history}")
                    failed_count += 1
            else:
                logger.warning(f"No sales history found for ASIN: {asin}")
                logger.warning(f"Sales history: {sales_history}")
                failed_count += 1
        
        # Summary
        logger.info("=" * 50)
        logger.info("SCRIPT COMPLETION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total ASINs processed: {len(sampled_asins)}")
        logger.info(f"Successful: {successful_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Output directory: {OUTPUT_DIR}")
        
        if successful_count > 0:
            logger.info("✅ Script completed successfully!")
        else:
            logger.error("❌ No sales data was successfully processed")
            
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main() 