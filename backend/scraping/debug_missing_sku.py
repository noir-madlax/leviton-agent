#!/usr/bin/env python3
"""
Debug script to investigate why 6674-P0W is missing from the comparison
"""

import pandas as pd
import os
import re
from typing import Dict

# Constants from the main script
POS_DATA_FILE = "backend/scraping/monthly_sales_history_output/Amazon POS by Month Requested LC Product 07-21-25.csv"
SALES_HISTORY_DIR = "backend/scraping/sales_history_output/leviton_dimmer"

# ASIN to SKU mapping
ASIN_TO_SKU_MAPPING = {
    'B00NG0ELL0': 'DSL06-1LZ',  # Decora Slide Dimmer
    'B01M7RTUIO': 'TSL06-1LW',  # Toggle Slide Dimmer
    'B073H9Y7SH': 'RNL06-10Z',  # Trimatron Rotary Dimmer
    'B0076HPM8A': '6674-P0W',   # SureSlide Dimmer
    'B00CF4IPGK': '6672-1LW',   # SureSlide Dimmer (different model)
    'B0CB22CTTV': 'MLWSB-1RW'   # Wi-Fi Bridge (not a dimmer, exclude from comparison)
}

def check_pos_data():
    """Check what SKUs are in the POS data"""
    print("=== POS DATA ANALYSIS ===")
    pos_df = pd.read_csv(POS_DATA_FILE)
    print(f"POS data shape: {pos_df.shape}")
    print(f"POS data columns: {list(pos_df.columns)}")
    
    # Get SKUs from POS data
    skus_in_pos = []
    for idx in range(1, len(pos_df)):  # Start from row 1 (first data row)
        row = pos_df.iloc[idx]
        sku = row.iloc[0]  # First column is SKU
        print(f"Row {idx}: SKU = '{sku}' (type: {type(sku)})")
        if pd.notna(sku) and sku != '' and sku != 'SKU':
            skus_in_pos.append(sku)
    
    print(f"SKUs in POS data: {skus_in_pos}")
    return skus_in_pos

def check_scraped_data():
    """Check what ASINs have scraped data"""
    print("\n=== SCRAPED DATA ANALYSIS ===")
    
    scraped_asins = []
    for filename in os.listdir(SALES_HISTORY_DIR):
        if filename.endswith('.csv') and filename.startswith('leviton_'):
            # Extract ASIN from filename
            asin_match = re.search(r'leviton_([A-Z0-9]+)_sales_', filename)
            if asin_match:
                asin = asin_match.group(1)
                scraped_asins.append(asin)
                print(f"Found scraped data for ASIN: {asin} -> SKU: {ASIN_TO_SKU_MAPPING.get(asin, 'NOT MAPPED')}")
    
    print(f"\nTotal ASINs with scraped data: {len(scraped_asins)}")
    print(f"Unique ASINs: {list(set(scraped_asins))}")
    return scraped_asins

def check_mapping():
    """Check the ASIN to SKU mapping"""
    print("\n=== MAPPING ANALYSIS ===")
    print("ASIN to SKU mapping:")
    for asin, sku in ASIN_TO_SKU_MAPPING.items():
        print(f"  {asin} -> {sku}")
    
    # Check which SKUs should be in the comparison
    expected_skus = []
    for asin, sku in ASIN_TO_SKU_MAPPING.items():
        if asin != 'B0CB22CTTV':  # Exclude Wi-Fi Bridge
            expected_skus.append(sku)
    
    print(f"\nExpected SKUs for comparison: {expected_skus}")

def main():
    """Main debug function"""
    print("DEBUGGING MISSING SKU ISSUE")
    print("=" * 50)
    
    # Check POS data
    pos_skus = check_pos_data()
    
    # Check scraped data
    scraped_asins = check_scraped_data()
    
    # Check mapping
    check_mapping()
    
    # Analyze the issue
    print("\n=== ISSUE ANALYSIS ===")
    
    # Check if 6674-P0W is in POS data
    if '6674-P0W' in pos_skus:
        print("✓ 6674-P0W is in POS data")
    else:
        print("✗ 6674-P0W is NOT in POS data")
    
    # Check if B0076HPM8A has scraped data
    if 'B0076HPM8A' in scraped_asins:
        print("✓ B0076HPM8A has scraped data")
    else:
        print("✗ B0076HPM8A does NOT have scraped data")
    
    # Check if B0076HPM8A is in the mapping
    if 'B0076HPM8A' in ASIN_TO_SKU_MAPPING:
        print("✓ B0076HPM8A is in ASIN mapping")
    else:
        print("✗ B0076HPM8A is NOT in ASIN mapping")
    
    # Check what should be in the final comparison
    print(f"\nExpected SKUs in comparison: {[sku for asin, sku in ASIN_TO_SKU_MAPPING.items() if asin != 'B0CB22CTTV']}")
    print(f"Actual SKUs in POS data: {pos_skus}")
    
    # Find missing SKUs
    expected_comparison_skus = [sku for asin, sku in ASIN_TO_SKU_MAPPING.items() if asin != 'B0CB22CTTV']
    missing_skus = [sku for sku in expected_comparison_skus if sku not in pos_skus]
    print(f"Missing SKUs from POS data: {missing_skus}")

if __name__ == "__main__":
    main() 