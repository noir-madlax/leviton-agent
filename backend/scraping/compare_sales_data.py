#!/usr/bin/env python3
"""
Sales Data Comparison Script

This script compares Amazon POS data with scraped sales data to calculate accuracy metrics
for units, revenue, and average price per ASIN across the same time periods.
"""

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import logging

# Constants
POS_DATA_FILE = "backend/scraping/monthly_sales_history_output/Amazon POS by Month Requested LC Product 07-21-25.csv"
SALES_HISTORY_DIR = "backend/scraping/sales_history_output/leviton_dimmer"

# ASIN to SKU mapping based on product titles
ASIN_TO_SKU_MAPPING = {
    'B00NG0ELL0': 'DSL06-1LZ',  # Decora Slide Dimmer
    'B01M7RTUIO': 'TSL06-1LW',  # Toggle Slide Dimmer
    'B073H9Y7SH': 'RNL06-10Z',  # Trimatron Rotary Dimmer
    'B0076HPM8A': '6674-P0W',   # SureSlide Dimmer
    'B00CF4IPGK': '6672-1LW',   # SureSlide Dimmer (different model)
    'B0CB22CTTV': 'MLWSB-1RW'   # Wi-Fi Bridge (not a dimmer, exclude from comparison)
}

# Time period mapping (Amazon POS format to standard date format)
# These represent monthly periods, so we map to the start of each month
TIME_PERIOD_MAPPING = {
    'Jul-24': '2024-07-01',  # Start of July 2024
    'Aug-24': '2024-08-01',  # Start of August 2024
    'Sep-24': '2024-09-01',  # Start of September 2024
    'Oct-24': '2024-10-01',  # Start of October 2024
    '24-Nov': '2024-11-01',  # Start of November 2024
    '24-Dec': '2024-12-01',  # Start of December 2024
    '25-Jan': '2025-01-01',  # Start of January 2025
    '25-Feb': '2025-02-01',  # Start of February 2025
    '25-Mar': '2025-03-01',  # Start of March 2025
    '25-Apr': '2025-04-01',  # Start of April 2025
    '25-May': '2025-05-01',  # Start of May 2025
    '25-Jun': '2025-06-01'   # Start of June 2025
}

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sales_comparison.log'),
            logging.StreamHandler()
        ]
    )

def clean_currency_value(value: str) -> float:
    """Clean currency string and convert to float"""
    if pd.isna(value) or value == '':
        return 0.0
    
    # Remove currency symbols, commas, and spaces
    cleaned = re.sub(r'[$,]', '', str(value).strip())
    try:
        return float(cleaned)
    except ValueError:
        logging.warning(f"Could not convert currency value: {value}")
        return 0.0

def clean_units_value(value: str) -> int:
    """Clean units string and convert to integer"""
    if pd.isna(value) or value == '':
        return 0
    
    # Remove commas and spaces
    cleaned = re.sub(r'[,]', '', str(value).strip())
    try:
        return int(cleaned)
    except ValueError:
        logging.warning(f"Could not convert units value: {value}")
        return 0

def load_pos_data() -> pd.DataFrame:
    """Load and clean Amazon POS data"""
    logging.info("Loading Amazon POS data...")
    
    try:
        # Read the POS data - the first row contains time periods
        pos_df = pd.read_csv(POS_DATA_FILE)
        
        # Clean the data
        cleaned_data = []
        
        # Get the time periods from the first row
        time_periods = []
        for col in pos_df.columns[1:]:  # Skip the first empty column
            if 'Jul-24' in col or 'Aug-24' in col or 'Sep-24' in col or 'Oct-24' in col or '24-Nov' in col or '24-Dec' in col or '25-Jan' in col or '25-Feb' in col or '25-Mar' in col or '25-Apr' in col or '25-May' in col or '25-Jun' in col:
                # Extract the time period from column name
                time_period = col.split(',')[0].strip()
                time_periods.append(time_period)
        
        # Process each SKU row (starting from row 1)
        for idx in range(1, len(pos_df)):
            row = pos_df.iloc[idx]
            sku = row.iloc[0]  # First column is SKU
            
            if pd.isna(sku) or sku == '' or sku == 'SKU':
                continue
            
            # Process each time period
            for i, time_period in enumerate(time_periods):
                if time_period in TIME_PERIOD_MAPPING:
                    # Calculate column indices for dollars and units
                    dollars_col_idx = 1 + (i * 2)  # Dollars columns are at odd indices
                    units_col_idx = 2 + (i * 2)    # Units columns are at even indices
                    
                    if dollars_col_idx < len(row) and units_col_idx < len(row):
                        dollars = clean_currency_value(row.iloc[dollars_col_idx])
                        units = clean_units_value(row.iloc[units_col_idx])
                        
                        if dollars > 0 and units > 0:
                            cleaned_data.append({
                                'sku': sku,
                                'time_period': TIME_PERIOD_MAPPING[time_period],
                                'dollars': dollars,
                                'units': units,
                                'avg_price': dollars / units
                            })
        
        pos_clean_df = pd.DataFrame(cleaned_data)
        logging.info(f"Loaded {len(pos_clean_df)} POS data records")
        return pos_clean_df
        
    except Exception as e:
        logging.error(f"Error loading POS data: {e}")
        raise

def load_scraped_sales_data() -> Dict[str, pd.DataFrame]:
    """Load all scraped sales data files"""
    logging.info("Loading scraped sales data...")
    
    sales_data = {}
    
    for filename in os.listdir(SALES_HISTORY_DIR):
        if filename.endswith('.csv') and filename.startswith('leviton_'):
            # Extract ASIN from filename
            asin_match = re.search(r'leviton_([A-Z0-9]+)_sales_', filename)
            if asin_match:
                asin = asin_match.group(1)
                
                if asin in ASIN_TO_SKU_MAPPING:
                    filepath = os.path.join(SALES_HISTORY_DIR, filename)
                    try:
                        df = pd.read_csv(filepath)
                        df['date'] = pd.to_datetime(df['date'])
                        df['year_month'] = df['date'].dt.to_period('M').astype(str)
                        
                        # Calculate daily revenue
                        df['daily_revenue'] = df['estimated_units_sold'] * df['last_known_price']
                        
                        sales_data[asin] = df
                        logging.info(f"Loaded sales data for ASIN {asin}: {len(df)} records")
                        
                    except Exception as e:
                        logging.error(f"Error loading {filename}: {e}")
    
    return sales_data

def aggregate_scraped_data_by_date_range(sales_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Aggregate scraped daily data to date range totals based on POS data dates"""
    logging.info("Aggregating scraped data by date ranges...")
    
    aggregated_data = []
    
    # Get all POS dates to determine aggregation periods
    pos_dates = list(TIME_PERIOD_MAPPING.values())
    pos_dates.sort()  # Sort chronologically
    
    for asin, df in sales_data.items():
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        for i, pos_date_str in enumerate(pos_dates):
            pos_date = datetime.strptime(pos_date_str, '%Y-%m-%d')
            
            # Determine the end date for aggregation (end of the month)
            if pos_date.month == 12:
                end_date = pos_date.replace(year=pos_date.year + 1, month=1, day=1) - pd.Timedelta(days=1)
            else:
                end_date = pos_date.replace(month=pos_date.month + 1, day=1) - pd.Timedelta(days=1)
            
            # Filter data for this date range (full calendar month)
            mask = (df['date'] >= pos_date) & (df['date'] <= end_date)
            period_data = df[mask]
            
            if len(period_data) > 0:
                # Aggregate the data for this period
                total_units = period_data['estimated_units_sold'].sum()
                total_revenue = period_data['daily_revenue'].sum()
                avg_price = total_revenue / total_units if total_units > 0 else 0
                
                aggregated_data.append({
                    'asin': asin,
                    'sku': ASIN_TO_SKU_MAPPING[asin],
                    'time_period': pos_date_str,
                    'units_scraped': total_units,
                    'daily_revenue_scraped': total_revenue,
                    'avg_price_scraped': avg_price,
                    'start_date': pos_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days_in_period': (end_date - pos_date).days
                })
    
    if aggregated_data:
        combined_df = pd.DataFrame(aggregated_data)
        logging.info(f"Aggregated data for {len(combined_df)} date range-SKU combinations")
        return combined_df
    else:
        return pd.DataFrame()

def compare_data(pos_data: pd.DataFrame, scraped_data: pd.DataFrame) -> pd.DataFrame:
    """Compare POS data with scraped data"""
    logging.info("Comparing POS data with scraped data...")
    
    # Merge data on SKU and time period
    comparison_df = pos_data.merge(
        scraped_data,
        left_on=['sku', 'time_period'],
        right_on=['sku', 'time_period'],
        how='inner',
        suffixes=('_pos', '_scraped')
    )
    
    # Rename columns for clarity
    comparison_df = comparison_df.rename(columns={
        'units': 'units_pos',
        'dollars': 'dollars_pos',
        'avg_price': 'avg_price_pos'
    })
    
    # Calculate accuracy metrics
    comparison_df['units_accuracy'] = np.where(
        comparison_df['units_pos'] > 0,
        comparison_df['units_scraped'] / comparison_df['units_pos'],
        0
    )
    
    comparison_df['revenue_accuracy'] = np.where(
        comparison_df['dollars_pos'] > 0,
        comparison_df['daily_revenue_scraped'] / comparison_df['dollars_pos'],
        0
    )
    
    comparison_df['price_accuracy'] = np.where(
        comparison_df['avg_price_pos'] > 0,
        comparison_df['avg_price_scraped'] / comparison_df['avg_price_pos'],
        0
    )
    
    # Calculate absolute differences
    comparison_df['units_diff'] = comparison_df['units_scraped'] - comparison_df['units_pos']
    comparison_df['revenue_diff'] = comparison_df['daily_revenue_scraped'] - comparison_df['dollars_pos']
    comparison_df['price_diff'] = comparison_df['avg_price_scraped'] - comparison_df['avg_price_pos']
    
    logging.info(f"Comparison completed for {len(comparison_df)} data points")
    return comparison_df

def calculate_summary_statistics(comparison_df: pd.DataFrame) -> Dict:
    """Calculate summary statistics for accuracy metrics"""
    logging.info("Calculating summary statistics...")
    
    summary = {}
    
    # Overall accuracy metrics
    summary['overall_units_accuracy'] = comparison_df['units_accuracy'].mean()
    summary['overall_revenue_accuracy'] = comparison_df['revenue_accuracy'].mean()
    summary['overall_price_accuracy'] = comparison_df['price_accuracy'].mean()
    
    # Accuracy by SKU
    sku_accuracy = comparison_df.groupby('sku').agg({
        'units_accuracy': 'mean',
        'revenue_accuracy': 'mean',
        'price_accuracy': 'mean'
    }).round(3)
    
    summary['sku_accuracy'] = sku_accuracy
    
    # Accuracy by time period with percentiles
    time_accuracy = comparison_df.groupby('time_period').agg({
        'units_accuracy': ['mean', lambda x: x.quantile(0.05), lambda x: x.quantile(0.25), 
                          lambda x: x.quantile(0.75), lambda x: x.quantile(0.95)],
        'revenue_accuracy': ['mean', lambda x: x.quantile(0.05), lambda x: x.quantile(0.25), 
                           lambda x: x.quantile(0.75), lambda x: x.quantile(0.95)],
        'price_accuracy': ['mean', lambda x: x.quantile(0.05), lambda x: x.quantile(0.25), 
                          lambda x: x.quantile(0.75), lambda x: x.quantile(0.95)]
    }).round(3)
    
    # Flatten column names
    time_accuracy.columns = [
        'units_accuracy_mean', 'units_accuracy_5pct', 'units_accuracy_25pct', 'units_accuracy_75pct', 'units_accuracy_95pct',
        'revenue_accuracy_mean', 'revenue_accuracy_5pct', 'revenue_accuracy_25pct', 'revenue_accuracy_75pct', 'revenue_accuracy_95pct',
        'price_accuracy_mean', 'price_accuracy_5pct', 'price_accuracy_25pct', 'price_accuracy_75pct', 'price_accuracy_95pct'
    ]
    
    summary['time_accuracy'] = time_accuracy
    
    # Correlation coefficients
    summary['units_correlation'] = comparison_df['units_pos'].corr(comparison_df['units_scraped'])
    summary['revenue_correlation'] = comparison_df['dollars_pos'].corr(comparison_df['daily_revenue_scraped'])
    summary['price_correlation'] = comparison_df['avg_price_pos'].corr(comparison_df['avg_price_scraped'])
    
    return summary

def generate_detailed_report(comparison_df: pd.DataFrame, summary: Dict) -> str:
    """Generate a detailed comparison report"""
    report = []
    report.append("=" * 80)
    report.append("SALES DATA COMPARISON REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Overall statistics
    report.append("OVERALL ACCURACY METRICS:")
    report.append("-" * 40)
    report.append(f"Units Accuracy: {summary['overall_units_accuracy']:.3f} ({summary['overall_units_accuracy']*100:.1f}%)")
    report.append(f"Revenue Accuracy: {summary['overall_revenue_accuracy']:.3f} ({summary['overall_revenue_accuracy']*100:.1f}%)")
    report.append(f"Price Accuracy: {summary['overall_price_accuracy']:.3f} ({summary['overall_price_accuracy']*100:.1f}%)")
    report.append("")
    
    # Correlation coefficients
    report.append("CORRELATION COEFFICIENTS:")
    report.append("-" * 40)
    report.append(f"Units Correlation: {summary['units_correlation']:.3f}")
    report.append(f"Revenue Correlation: {summary['revenue_correlation']:.3f}")
    report.append(f"Price Correlation: {summary['price_correlation']:.3f}")
    report.append("")
    
    # SKU-level accuracy
    report.append("ACCURACY BY SKU:")
    report.append("-" * 40)
    for sku, row in summary['sku_accuracy'].iterrows():
        report.append(f"{sku}:")
        report.append(f"  Units: {row['units_accuracy']:.3f} ({row['units_accuracy']*100:.1f}%)")
        report.append(f"  Revenue: {row['revenue_accuracy']:.3f} ({row['revenue_accuracy']*100:.1f}%)")
        report.append(f"  Price: {row['price_accuracy']:.3f} ({row['price_accuracy']*100:.1f}%)")
    report.append("")
    
    # Time period accuracy with percentiles
    report.append("ACCURACY BY TIME PERIOD (with percentiles):")
    report.append("-" * 60)
    
    for period, row in summary['time_accuracy'].iterrows():
        report.append(f"{period}:")
        report.append(f"  Units - Mean: {row['units_accuracy_mean']:.3f} ({row['units_accuracy_mean']*100:.1f}%)")
        report.append(f"          5%: {row['units_accuracy_5pct']:.3f}, 25%: {row['units_accuracy_25pct']:.3f}, 75%: {row['units_accuracy_75pct']:.3f}, 95%: {row['units_accuracy_95pct']:.3f}")
        report.append(f"  Revenue - Mean: {row['revenue_accuracy_mean']:.3f} ({row['revenue_accuracy_mean']*100:.1f}%)")
        report.append(f"             5%: {row['revenue_accuracy_5pct']:.3f}, 25%: {row['revenue_accuracy_25pct']:.3f}, 75%: {row['revenue_accuracy_75pct']:.3f}, 95%: {row['revenue_accuracy_95pct']:.3f}")
        report.append(f"  Price - Mean: {row['price_accuracy_mean']:.3f} ({row['price_accuracy_mean']*100:.1f}%)")
        report.append(f"          5%: {row['price_accuracy_5pct']:.3f}, 25%: {row['price_accuracy_25pct']:.3f}, 75%: {row['price_accuracy_75pct']:.3f}, 95%: {row['price_accuracy_95pct']:.3f}")
        report.append("")
    report.append("")
    
    # Detailed comparison table
    report.append("DETAILED COMPARISON TABLE:")
    report.append("-" * 80)
    report.append("SKU\tPeriod\tPOS Units\tScraped Units\tUnits Acc\tPOS Revenue\tScraped Revenue\tRevenue Acc")
    report.append("-" * 80)
    
    for _, row in comparison_df.iterrows():
        report.append(
            f"{row['sku']}\t{row['time_period']}\t"
            f"{row['units_pos']}\t{row['units_scraped']}\t{row['units_accuracy']:.3f}\t"
            f"${row['dollars_pos']:,.0f}\t${row['daily_revenue_scraped']:,.0f}\t{row['revenue_accuracy']:.3f}"
        )
    
    return "\n".join(report)

def save_results(comparison_df: pd.DataFrame, summary: Dict, report: str):
    """Save comparison results to files"""
    logging.info("Saving results...")
    
    # Save detailed comparison data
    comparison_df.to_csv('sales_comparison_detailed.csv', index=False)
    
    # Save summary statistics
    summary_df = pd.DataFrame({
        'metric': ['units_accuracy', 'revenue_accuracy', 'price_accuracy', 
                  'units_correlation', 'revenue_correlation', 'price_correlation'],
        'value': [summary['overall_units_accuracy'], summary['overall_revenue_accuracy'], 
                 summary['overall_price_accuracy'], summary['units_correlation'],
                 summary['revenue_correlation'], summary['price_correlation']]
    })
    summary_df.to_csv('sales_comparison_summary.csv', index=False)
    
    # Save SKU accuracy
    summary['sku_accuracy'].to_csv('sales_comparison_sku_accuracy.csv')
    
    # Save time period accuracy
    summary['time_accuracy'].to_csv('sales_comparison_time_accuracy.csv')
    
    # Save report
    with open('sales_comparison_report.txt', 'w') as f:
        f.write(report)
    
    logging.info("Results saved to files")

def main():
    """Main execution function"""
    setup_logging()
    
    try:
        logging.info("Starting sales data comparison...")
        
        # Load data
        pos_data = load_pos_data()
        scraped_data = load_scraped_sales_data()
        
        if not scraped_data:
            logging.error("No scraped data found")
            return
        
        # Aggregate scraped data
        aggregated_scraped = aggregate_scraped_data_by_date_range(scraped_data)
        
        if aggregated_scraped.empty:
            logging.error("No aggregated scraped data available")
            return
        
        # Compare data
        comparison_df = compare_data(pos_data, aggregated_scraped)
        
        if comparison_df.empty:
            logging.error("No matching data found for comparison")
            return
        
        # Calculate summary statistics
        summary = calculate_summary_statistics(comparison_df)
        
        # Generate report
        report = generate_detailed_report(comparison_df, summary)
        
        # Save results
        save_results(comparison_df, summary, report)
        
        # Print summary to console
        print("\n" + "=" * 60)
        print("SALES DATA COMPARISON SUMMARY")
        print("=" * 60)
        print(f"Overall Units Accuracy: {summary['overall_units_accuracy']:.3f} ({summary['overall_units_accuracy']*100:.1f}%)")
        print(f"Overall Revenue Accuracy: {summary['overall_revenue_accuracy']:.3f} ({summary['overall_revenue_accuracy']*100:.1f}%)")
        print(f"Overall Price Accuracy: {summary['overall_price_accuracy']:.3f} ({summary['overall_price_accuracy']*100:.1f}%)")
        print(f"Units Correlation: {summary['units_correlation']:.3f}")
        print(f"Revenue Correlation: {summary['revenue_correlation']:.3f}")
        print(f"Price Correlation: {summary['price_correlation']:.3f}")
        print(f"Total data points compared: {len(comparison_df)}")
        print("=" * 60)
        print("Detailed results saved to:")
        print("- sales_comparison_detailed.csv")
        print("- sales_comparison_summary.csv")
        print("- sales_comparison_sku_accuracy.csv")
        print("- sales_comparison_time_accuracy.csv")
        print("- sales_comparison_report.txt")
        
        logging.info("Sales data comparison completed successfully")
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main() 