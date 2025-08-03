#!/usr/bin/env python3
"""
Script to analyze column values and identify which columns should be merged.
"""

import pandas as pd
import re
from collections import defaultdict
import json

def analyze_column_values(csv_file):
    """Analyze column values to identify potential merges."""
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Get all column names
    columns = df.columns.tolist()
    
    # Group columns by their stemmed names (without _origin suffix)
    column_groups = defaultdict(list)
    
    for col in columns:
        if col.endswith('_origin'):
            base_col = col[:-7]  # Remove '_origin'
        else:
            base_col = col
        
        # Clean the base column name
        clean_name = re.sub(r'[^\w\s]', '', base_col.lower())
        words = clean_name.split()
        stemmed_name = '_'.join(words)
        
        column_groups[stemmed_name].append(col)
    
    # Analyze each group
    merge_candidates = []
    
    for stemmed_name, cols in column_groups.items():
        if len(cols) > 1:
            # Get data columns (not origin columns)
            data_cols = [col for col in cols if not col.endswith('_origin')]
            origin_cols = [col for col in cols if col.endswith('_origin')]
            
            if len(data_cols) > 1:
                # Analyze the values in these columns
                column_analysis = {
                    'stemmed_name': stemmed_name,
                    'data_columns': data_cols,
                    'origin_columns': origin_cols,
                    'non_null_counts': {},
                    'sample_values': {},
                    'should_merge': False,
                    'reason': ''
                }
                
                for col in data_cols:
                    # Count non-null values
                    non_null_count = df[col].notna().sum()
                    column_analysis['non_null_counts'][col] = non_null_count
                    
                    # Get sample values
                    sample_values = df[col].dropna().head(3).tolist()
                    column_analysis['sample_values'][col] = sample_values
                
                # Determine if columns should be merged
                total_non_null = sum(column_analysis['non_null_counts'].values())
                if total_non_null > 0:
                    # Check if columns have overlapping data
                    overlapping = False
                    for i, col1 in enumerate(data_cols):
                        for col2 in data_cols[i+1:]:
                            # Check if both columns have data for same rows
                            both_have_data = df[col1].notna() & df[col2].notna()
                            if both_have_data.sum() > 0:
                                overlapping = True
                                break
                        if overlapping:
                            break
                    
                    if overlapping:
                        column_analysis['should_merge'] = True
                        column_analysis['reason'] = 'Overlapping data found'
                    elif total_non_null > len(df) * 0.1:  # If significant data exists
                        column_analysis['should_merge'] = True
                        column_analysis['reason'] = 'Significant data in multiple columns'
                
                merge_candidates.append(column_analysis)
    
    return merge_candidates

def analyze_similar_columns(csv_file):
    """Analyze columns with similar names that might be duplicates."""
    
    df = pd.read_csv(csv_file)
    columns = df.columns.tolist()
    
    # Look for columns with similar names
    similar_groups = []
    
    # Common patterns to look for
    patterns = [
        (r'batteri', 'battery'),
        (r'best.*rank', 'best_seller_rank'),
        (r'connector', 'connector'),
        (r'temperatur', 'temperature'),
        (r'voltage', 'voltage'),
        (r'gauge', 'gauge'),
        (r'material', 'material'),
        (r'color', 'color'),
        (r'length', 'length'),
        (r'weight', 'weight'),
        (r'dimension', 'dimension'),
        (r'manufacturer', 'manufacturer'),
        (r'model', 'model'),
        (r'part.*number', 'part_number'),
        (r'upc', 'upc'),
        (r'asin', 'asin'),
    ]
    
    for pattern, category in patterns:
        matching_cols = [col for col in columns if re.search(pattern, col.lower())]
        if len(matching_cols) > 1:
            similar_groups.append({
                'category': category,
                'pattern': pattern,
                'columns': matching_cols,
                'data_columns': [col for col in matching_cols if not col.endswith('_origin')],
                'origin_columns': [col for col in matching_cols if col.endswith('_origin')]
            })
    
    return similar_groups

def main():
    """Main analysis function."""
    
    csv_file = 'extracted_product_details_v2.csv'
    
    print("Analyzing column values for potential merges...")
    print("=" * 60)
    
    # Analyze column groups
    merge_candidates = analyze_column_values(csv_file)
    
    print(f"Found {len(merge_candidates)} potential merge candidates:")
    print()
    
    for candidate in merge_candidates:
        if candidate['should_merge']:
            print(f"🔍 {candidate['stemmed_name']}")
            print(f"   Data columns: {candidate['data_columns']}")
            print(f"   Non-null counts: {candidate['non_null_counts']}")
            print(f"   Reason: {candidate['reason']}")
            print(f"   Sample values:")
            for col, values in candidate['sample_values'].items():
                print(f"     {col}: {values}")
            print()
    
    # Analyze similar columns
    print("Analyzing similar column names...")
    print("=" * 60)
    
    similar_groups = analyze_similar_columns(csv_file)
    
    for group in similar_groups:
        if len(group['data_columns']) > 1:
            print(f"🔍 {group['category']} (pattern: {group['pattern']})")
            print(f"   Data columns: {group['data_columns']}")
            print(f"   Origin columns: {group['origin_columns']}")
            print()
    
    # Save analysis results
    analysis_results = {
        'merge_candidates': merge_candidates,
        'similar_groups': similar_groups
    }
    
    with open('column_analysis.json', 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print("Analysis results saved to column_analysis.json")

if __name__ == "__main__":
    main() 