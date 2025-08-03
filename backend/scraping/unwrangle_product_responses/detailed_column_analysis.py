#!/usr/bin/env python3
"""
Detailed script to examine actual column values and determine if they should be merged.
"""

import pandas as pd
import re
import json

def examine_column_values(df, col1, col2, sample_size=5):
    """Examine values in two columns to see if they should be merged."""
    
    print(f"\n🔍 Comparing {col1} vs {col2}:")
    print("-" * 50)
    
    # Count non-null values
    count1 = df[col1].notna().sum()
    count2 = df[col2].notna().sum()
    
    print(f"Non-null values: {col1}={count1}, {col2}={count2}")
    
    # Check for overlapping data
    both_have_data = df[col1].notna() & df[col2].notna()
    overlap_count = both_have_data.sum()
    print(f"Rows with data in both columns: {overlap_count}")
    
    if overlap_count > 0:
        print("Sample rows with data in both columns:")
        overlap_rows = df[both_have_data][['asin', col1, col2]].head(sample_size)
        for _, row in overlap_rows.iterrows():
            print(f"  ASIN {row['asin']}: {col1}='{row[col1]}', {col2}='{row[col2]}'")
    
    # Show sample values from each column
    print(f"\nSample values from {col1}:")
    sample1 = df[col1].dropna().head(sample_size).tolist()
    for val in sample1:
        print(f"  '{val}'")
    
    print(f"\nSample values from {col2}:")
    sample2 = df[col2].dropna().head(sample_size).tolist()
    for val in sample2:
        print(f"  '{val}'")
    
    # Determine if they should be merged
    should_merge = False
    reason = ""
    
    if overlap_count > 0:
        should_merge = True
        reason = f"Overlapping data found in {overlap_count} rows"
    elif count1 > 0 and count2 > 0:
        # Check if they seem to represent the same concept
        if any(word in col1.lower() for word in ['rank', 'seller']) and any(word in col2.lower() for word in ['rank', 'seller']):
            should_merge = True
            reason = "Both appear to be seller rank information"
        elif any(word in col1.lower() for word in ['batteri', 'battery']) and any(word in col2.lower() for word in ['batteri', 'battery']):
            should_merge = True
            reason = "Both appear to be battery information"
        elif any(word in col1.lower() for word in ['connector']) and any(word in col2.lower() for word in ['connector']):
            should_merge = True
            reason = "Both appear to be connector information"
        elif any(word in col1.lower() for word in ['temperatur', 'temperature']) and any(word in col2.lower() for word in ['temperatur', 'temperature']):
            should_merge = True
            reason = "Both appear to be temperature information"
    
    print(f"\nRecommendation: {'MERGE' if should_merge else 'KEEP SEPARATE'}")
    if reason:
        print(f"Reason: {reason}")
    
    return should_merge, reason

def main():
    """Main analysis function."""
    
    # Read the CSV file
    df = pd.read_csv('extracted_product_details_v2.csv')
    
    print("Detailed Column Analysis for Potential Merges")
    print("=" * 60)
    
    # Define column pairs to examine
    column_pairs = [
        ('best_seller_rank', 'bestsellersrank'),
        ('batteri_includ', 'batteri_requir'),
        ('connector_type', 'connectortyp'),
        ('temperatur_rate', 'temperature'),
        ('voltage', 'voltage_rating'),
    ]
    
    merge_recommendations = []
    
    for col1, col2 in column_pairs:
        if col1 in df.columns and col2 in df.columns:
            should_merge, reason = examine_column_values(df, col1, col2)
            merge_recommendations.append({
                'column1': col1,
                'column2': col2,
                'should_merge': should_merge,
                'reason': reason
            })
        else:
            print(f"\n⚠️  Columns {col1} and/or {col2} not found in dataset")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY OF MERGE RECOMMENDATIONS")
    print("=" * 60)
    
    for rec in merge_recommendations:
        status = "✅ MERGE" if rec['should_merge'] else "❌ KEEP SEPARATE"
        print(f"{status}: {rec['column1']} + {rec['column2']}")
        if rec['reason']:
            print(f"   Reason: {rec['reason']}")
        print()
    
    # Save recommendations
    with open('merge_recommendations.json', 'w') as f:
        json.dump(merge_recommendations, f, indent=2)
    
    print("Merge recommendations saved to merge_recommendations.json")

if __name__ == "__main__":
    main() 