#!/usr/bin/env python3
"""
Create comprehensive sales comparison plots
- Include all 4 products
- Exclude first month from calculations
- Show units accuracy vs average units sold per month
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Set style
plt.style.use('default')
sns.set_palette("husl")

# Consistent color mapping for products
PRODUCT_COLORS = {
    '6674-P0W': '#1f77b4',  # Blue
    'DSL06-1LZ': '#ff7f0e',  # Orange
    'RNL06-10Z': '#2ca02c',  # Green
    'TSL06-1LW': '#d62728'   # Red
}

def load_and_prepare_data():
    """Load and prepare the comparison data"""
    # Load the detailed comparison data
    df = pd.read_csv('sales_comparison_detailed.csv')
    
    # Convert time_period to datetime for easier manipulation
    df['time_period'] = pd.to_datetime(df['time_period'])
    
    # Include all data (including first month)
    df_filtered = df.copy()
    
    return df, df_filtered

def create_comprehensive_plots(df, df_filtered):
    """Create all the required plots"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Sales Data Comparison Analysis (All Data)', fontsize=16, fontweight='bold')
    
    # 1. Units Accuracy by SKU (Top-Left)
    create_sku_accuracy_plot(df_filtered, axes[0, 0])
    
    # 2. Units Accuracy Over Time (Top-Right)
    create_time_accuracy_plot(df_filtered, axes[0, 1])
    
    # 3. POS vs Scraped Units (Bottom-Left)
    create_scatter_plot(df_filtered, axes[1, 0])
    
    # 4. Units Accuracy vs Average Units Sold (Bottom-Right)
    create_accuracy_vs_volume_plot(df_filtered, axes[1, 1])
    
    plt.tight_layout()
    plt.savefig('sales_comparison_analysis_fixed.png', dpi=300, bbox_inches='tight')
    print("Plot saved as 'sales_comparison_analysis_fixed.png'")

def create_sku_accuracy_plot(df, ax):
    """Create units accuracy by SKU bar chart"""
    # Calculate average accuracy by SKU (all data)
    sku_accuracy = df.groupby('sku')['units_accuracy'].mean().sort_values(ascending=False)
    
    # Use consistent colors for each SKU
    colors = [PRODUCT_COLORS[sku] for sku in sku_accuracy.index]
    bars = ax.bar(sku_accuracy.index, sku_accuracy.values, color=colors, alpha=0.7, edgecolor='black')
    
    # Add value labels on bars
    for bar, value in zip(bars, sku_accuracy.values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Perfect Accuracy')
    ax.set_title('Units Accuracy by SKU (All Data)', fontweight='bold')
    ax.set_ylabel('Accuracy Ratio')
    ax.set_ylim(0, 1.2)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    ax.tick_params(axis='x', rotation=45)

def create_time_accuracy_plot(df, ax):
    """Create units accuracy over time line chart"""
    # Calculate average accuracy by time period
    time_accuracy = df.groupby('time_period')['units_accuracy'].mean().reset_index()
    time_accuracy = time_accuracy.sort_values('time_period')
    
    # Create month labels
    time_accuracy['month_label'] = time_accuracy['time_period'].dt.strftime('%b %Y')
    
    ax.plot(range(len(time_accuracy)), time_accuracy['units_accuracy'], 
            marker='o', linewidth=2, markersize=6, color='#1f77b4')
    ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Perfect Accuracy')
    
    ax.set_title('Units Accuracy Over Time (All Data)', fontweight='bold')
    ax.set_ylabel('Accuracy Ratio')
    ax.set_xlabel('Time Period')
    ax.set_ylim(0, 1.2)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Set x-axis labels
    ax.set_xticks(range(len(time_accuracy)))
    ax.set_xticklabels(time_accuracy['month_label'], rotation=45)

def create_scatter_plot(df, ax):
    """Create POS vs Scraped Units scatter plot"""
    # Create scatter plot with different colors for each SKU
    skus = df['sku'].unique()
    
    for sku in skus:
        sku_data = df[df['sku'] == sku]
        ax.scatter(sku_data['units_pos'], sku_data['units_scraped'], 
                  c=PRODUCT_COLORS[sku], label=sku, alpha=0.6, s=50)
    
    # Add perfect match line
    max_units = max(df['units_pos'].max(), df['units_scraped'].max())
    ax.plot([0, max_units], [0, max_units], 'r--', alpha=0.7, label='Perfect Match')
    
    ax.set_title('POS vs Scraped Units (All Data)', fontweight='bold')
    ax.set_xlabel('POS Units')
    ax.set_ylabel('Scraped Units')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Make axes equal for better visualization
    ax.set_aspect('equal', adjustable='box')

def create_accuracy_vs_volume_plot(df, ax):
    """Create units accuracy vs average units sold per month"""
    # Calculate average units sold per month for each SKU
    sku_stats = df.groupby('sku').agg({
        'units_accuracy': 'mean',
        'units_pos': 'mean'
    }).reset_index()
    
    # Create scatter plot with consistent colors
    for _, row in sku_stats.iterrows():
        ax.scatter(row['units_pos'], row['units_accuracy'], 
                  c=PRODUCT_COLORS[row['sku']], s=200, alpha=0.7, edgecolor='black', linewidth=2)
        ax.annotate(row['sku'], (row['units_pos'], row['units_accuracy']), 
                   xytext=(5, 5), textcoords='offset points', fontweight='bold')
    
    # Add trend line
    z = np.polyfit(sku_stats['units_pos'], sku_stats['units_accuracy'], 1)
    p = np.poly1d(z)
    ax.plot(sku_stats['units_pos'], p(sku_stats['units_pos']), "r--", alpha=0.8, label='Trend Line')
    
    # Add perfect accuracy line
    ax.axhline(y=1.0, color='red', linestyle=':', alpha=0.7, label='Perfect Accuracy')
    
    ax.set_title('Units Accuracy vs Average Units Sold per Month', fontweight='bold')
    ax.set_xlabel('Average POS Units per Month')
    ax.set_ylabel('Average Units Accuracy')
    ax.legend()
    ax.grid(True, alpha=0.3)

def print_summary_statistics(df, df_filtered):
    """Print summary statistics"""
    print("=== SALES COMPARISON SUMMARY (All Data) ===")
    print()
    
    # Overall statistics
    print("OVERALL STATISTICS:")
    print(f"Total data points: {len(df_filtered)}")
    print(f"Average units accuracy: {df_filtered['units_accuracy'].mean():.3f} ({df_filtered['units_accuracy'].mean()*100:.1f}%)")
    print(f"Average revenue accuracy: {df_filtered['revenue_accuracy'].mean():.3f} ({df_filtered['revenue_accuracy'].mean()*100:.1f}%)")
    print(f"Average price accuracy: {df_filtered['price_accuracy'].mean():.3f} ({df_filtered['price_accuracy'].mean()*100:.1f}%)")
    print()
    
    # SKU-level statistics
    print("SKU-LEVEL STATISTICS:")
    sku_stats = df_filtered.groupby('sku').agg({
        'units_accuracy': 'mean',
        'revenue_accuracy': 'mean',
        'price_accuracy': 'mean',
        'units_pos': 'mean'
    }).round(3)
    
    for sku, row in sku_stats.iterrows():
        print(f"{sku}:")
        print(f"  Units Accuracy: {row['units_accuracy']:.3f} ({row['units_accuracy']*100:.1f}%)")
        print(f"  Revenue Accuracy: {row['revenue_accuracy']:.3f} ({row['revenue_accuracy']*100:.1f}%)")
        print(f"  Price Accuracy: {row['price_accuracy']:.3f} ({row['price_accuracy']*100:.1f}%)")
        print(f"  Avg Units per Month: {row['units_pos']:.0f}")
        print()
    
    # Correlation coefficients
    print("CORRELATION COEFFICIENTS:")
    print(f"Units Correlation: {df_filtered['units_pos'].corr(df_filtered['units_scraped']):.3f}")
    print(f"Revenue Correlation: {df_filtered['dollars_pos'].corr(df_filtered['daily_revenue_scraped']):.3f}")
    print(f"Price Correlation: {df_filtered['avg_price_pos'].corr(df_filtered['avg_price_scraped']):.3f}")

def main():
    """Main function"""
    print("Creating comprehensive sales comparison plots...")
    
    # Load and prepare data
    df, df_filtered = load_and_prepare_data()
    
    # Print summary statistics
    print_summary_statistics(df, df_filtered)
    
    # Create plots
    create_comprehensive_plots(df, df_filtered)
    
    print("\nPlot generation completed successfully!")

if __name__ == "__main__":
    main() 