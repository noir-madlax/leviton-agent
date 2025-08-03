#!/usr/bin/env python3
"""
Analysis script to understand the price accuracy vs correlation discrepancy
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load the comparison data
df = pd.read_csv('sales_comparison_detailed.csv')

print("=== PRICE ACCURACY vs CORRELATION ANALYSIS ===")
print()

# Calculate price accuracy (ratio of scraped to POS)
df['price_accuracy'] = df['avg_price_scraped'] / df['avg_price_pos']

print("1. PRICE ACCURACY (Ratio Analysis):")
print(f"   Mean Price Accuracy: {df['price_accuracy'].mean():.3f}")
print(f"   This means scraped prices are on average {df['price_accuracy'].mean()*100:.1f}% of POS prices")
print(f"   Very close to 100% = good accuracy")
print()

print("2. PRICE CORRELATION (Linear Relationship):")
print(f"   Price Correlation: {df['avg_price_pos'].corr(df['avg_price_scraped']):.3f}")
print(f"   This measures how well the prices move together linearly")
print()

print("3. WHY THE DISCREPANCY?")
print("   Let's look at some examples:")

# Show some examples
print("\n   Example 1 - High accuracy, good correlation:")
example1 = df[(df['price_accuracy'] > 0.99) & (df['price_accuracy'] < 1.01)].iloc[0]
print(f"   POS: ${example1['avg_price_pos']:.2f}, Scraped: ${example1['avg_price_scraped']:.2f}")
print(f"   Accuracy: {example1['price_accuracy']:.3f}")

print("\n   Example 2 - High accuracy, but different pattern:")
# Find an example where accuracy is good but price is very different
example2 = df[df['avg_price_pos'] > 40].iloc[0]  # High POS price
print(f"   POS: ${example2['avg_price_pos']:.2f}, Scraped: ${example2['avg_price_scraped']:.2f}")
print(f"   Accuracy: {example2['price_accuracy']:.3f}")

print("\n   Example 3 - Low POS price:")
example3 = df[df['avg_price_pos'] < 15].iloc[0]  # Low POS price
print(f"   POS: ${example3['avg_price_pos']:.2f}, Scraped: ${example3['avg_price_scraped']:.2f}")
print(f"   Accuracy: {example3['price_accuracy']:.3f}")

print("\n4. THE REAL ISSUE:")
print("   - Price accuracy measures: 'Are the scraped prices close to POS prices?'")
print("   - Price correlation measures: 'Do scraped prices follow the same pattern as POS prices?'")
print()
print("   The data shows:")
print("   - Individual price estimates are quite accurate (close to 100%)")
print("   - But the relationship between POS and scraped prices is not very linear")
print("   - This suggests the scraping method captures prices well but may not")
print("     follow the same temporal or product-specific patterns as POS data")

# Create a scatter plot to visualize
plt.figure(figsize=(10, 6))
plt.scatter(df['avg_price_pos'], df['avg_price_scraped'], alpha=0.6)
plt.plot([df['avg_price_pos'].min(), df['avg_price_pos'].max()], 
         [df['avg_price_pos'].min(), df['avg_price_pos'].max()], 'r--', label='Perfect correlation')
plt.xlabel('POS Average Price ($)')
plt.ylabel('Scraped Average Price ($)')
plt.title('POS vs Scraped Average Prices')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('price_correlation_analysis.png', dpi=300, bbox_inches='tight')
print("\n5. Visualization saved as 'price_correlation_analysis.png'")
print("   The scatter plot shows the relationship between POS and scraped prices")
print("   Red line = perfect correlation (y=x)")
print("   Points close to line = good correlation")
print("   Points scattered = poor correlation despite potentially good accuracy") 