#!/usr/bin/env python3
"""
Debug script to investigate first month accuracy issues
"""

import pandas as pd
import os
import re
from datetime import datetime
from typing import Dict

# Constants
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

def analyze_first_month_data():
    """Analyze the first month data to understand the accuracy issue"""
    print("=== FIRST MONTH ACCURACY ANALYSIS ===")
    
    # Load scraped data for one ASIN to analyze
    asin = 'B0076HPM8A'  # 6674-P0W
    filename = f"leviton_{asin}_sales_20250720_184543.csv"
    filepath = os.path.join(SALES_HISTORY_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    # Load scraped data
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    print(f"Scraped data columns: {list(df.columns)}")
    print(f"Scraped data date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total days in scraped data: {len(df)}")
    
    # Calculate daily revenue if not present
    if 'daily_revenue' not in df.columns:
        df['daily_revenue'] = df['estimated_units_sold'] * df['last_known_price']
    
    # Analyze different date ranges for July 2024
    print("\n=== JULY 2024 DATE RANGE ANALYSIS ===")
    
    # Current logic: 2024-06-24 to 2024-07-24 (30 days)
    current_start = datetime(2024, 6, 24)
    current_end = datetime(2024, 7, 24)
    current_mask = (df['date'] > current_start) & (df['date'] <= current_end)
    current_data = df[current_mask]
    
    print(f"Current logic (2024-06-24 to 2024-07-24):")
    print(f"  Days in range: {len(current_data)}")
    print(f"  Total units: {current_data['estimated_units_sold'].sum():.0f}")
    print(f"  Total revenue: ${current_data['daily_revenue'].sum():.2f}")
    
    # Alternative 1: Full month of July (2024-07-01 to 2024-07-31)
    july_start = datetime(2024, 7, 1)
    july_end = datetime(2024, 7, 31)
    july_mask = (df['date'] >= july_start) & (df['date'] <= july_end)
    july_data = df[july_mask]
    
    print(f"\nFull July month (2024-07-01 to 2024-07-31):")
    print(f"  Days in range: {len(july_data)}")
    print(f"  Total units: {july_data['estimated_units_sold'].sum():.0f}")
    print(f"  Total revenue: ${july_data['daily_revenue'].sum():.2f}")
    
    # Alternative 2: Month-to-date (2024-07-01 to 2024-07-24)
    mtd_start = datetime(2024, 7, 1)
    mtd_end = datetime(2024, 7, 24)
    mtd_mask = (df['date'] >= mtd_start) & (df['date'] <= mtd_end)
    mtd_data = df[mtd_mask]
    
    print(f"\nMonth-to-date (2024-07-01 to 2024-07-24):")
    print(f"  Days in range: {len(mtd_data)}")
    print(f"  Total units: {mtd_data['estimated_units_sold'].sum():.0f}")
    print(f"  Total revenue: ${mtd_data['daily_revenue'].sum():.2f}")
    
    # Alternative 3: Previous 30 days from July 24 (2024-06-25 to 2024-07-24)
    prev30_start = datetime(2024, 6, 25)
    prev30_end = datetime(2024, 7, 24)
    prev30_mask = (df['date'] > prev30_start) & (df['date'] <= prev30_end)
    prev30_data = df[prev30_mask]
    
    print(f"\nPrevious 30 days (2024-06-25 to 2024-07-24):")
    print(f"  Days in range: {len(prev30_data)}")
    print(f"  Total units: {prev30_data['estimated_units_sold'].sum():.0f}")
    print(f"  Total revenue: ${prev30_data['daily_revenue'].sum():.2f}")
    
    # Compare with POS data
    pos_units = 7594  # From POS data for 6674-P0W in July
    pos_revenue = 127590  # From POS data for 6674-P0W in July
    
    print(f"\n=== COMPARISON WITH POS DATA ===")
    print(f"POS data for 6674-P0W in July:")
    print(f"  Units: {pos_units}")
    print(f"  Revenue: ${pos_revenue}")
    
    print(f"\nAccuracy comparison:")
    print(f"Current logic: {current_data['estimated_units_sold'].sum()/pos_units*100:.1f}% units, {current_data['daily_revenue'].sum()/pos_revenue*100:.1f}% revenue")
    print(f"Full July: {july_data['estimated_units_sold'].sum()/pos_units*100:.1f}% units, {july_data['daily_revenue'].sum()/pos_revenue*100:.1f}% revenue")
    print(f"Month-to-date: {mtd_data['estimated_units_sold'].sum()/pos_units*100:.1f}% units, {mtd_data['daily_revenue'].sum()/pos_revenue*100:.1f}% revenue")
    print(f"Previous 30 days: {prev30_data['estimated_units_sold'].sum()/pos_units*100:.1f}% units, {prev30_data['daily_revenue'].sum()/pos_revenue*100:.1f}% revenue")

def check_pos_data_interpretation():
    """Check how POS data should be interpreted"""
    print("\n=== POS DATA INTERPRETATION ===")
    
    pos_df = pd.read_csv(POS_DATA_FILE)
    print(f"POS data columns: {list(pos_df.columns)}")
    
    # The column headers suggest monthly periods
    print("\nColumn headers suggest these are monthly totals:")
    print("- Jul-24 = July 2024")
    print("- Aug-24 = August 2024")
    print("- etc.")
    
    print("\nThis suggests POS data represents:")
    print("- Monthly totals (entire month)")
    print("- NOT specific 30-day periods ending on the 24th")
    
    print("\nRECOMMENDATION:")
    print("The date aggregation logic should be changed to use full months")
    print("instead of 30-day periods ending on specific dates.")

def main():
    """Main analysis function"""
    analyze_first_month_data()
    check_pos_data_interpretation()

if __name__ == "__main__":
    main() 