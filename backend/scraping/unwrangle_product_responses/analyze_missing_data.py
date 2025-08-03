#!/usr/bin/env python3
"""
Analyze missing data in important columns and identify extraction issues.
This script identifies which columns are most important and shouldn't be missing,
then selects ASINs with missing values to inspect their original JSON files.
"""

import pandas as pd
import json
import os
from collections import defaultdict, Counter
import re

def analyze_missing_data():
    """Analyze missing data patterns and identify important columns."""
    
    # Read the V7 CSV file
    df = pd.read_csv('extracted_product_details_v7.csv')
    
    print("Analyzing Missing Data in Important Columns")
    print("=" * 60)
    
    # Define important columns based on the field reliability analysis
    important_columns = {
        'HIGH_PRIORITY': [
            'materi',           # Material is critical for electrical products
            'no_of_wire',       # Wire gauge is essential
            'voltag',           # Voltage rating is critical for safety
            'conductor',        # Conductor count is important
            'size',             # Size/dimensions are important
            'brand',            # Brand identification
            'price',            # Pricing information
        ],
        'MEDIUM_PRIORITY': [
            'color',            # Color is useful but not critical
            'certification',    # Safety certifications
            'temperature',      # Temperature ratings
            'length',           # Cable length
            'package_weight',   # Package information
            'best_seller_rank', # Market information
        ],
        'LOW_PRIORITY': [
            'batteri_includ',   # Battery information
            'custom_review',    # Customer reviews
            'date_first_avail', # Availability dates
            'is_discontinu_by_manufactur', # Discontinuation info
        ]
    }
    
    # Analyze missing data for each priority level
    missing_analysis = {}
    
    for priority, columns in important_columns.items():
        print(f"\n🔍 {priority} COLUMNS")
        print("-" * 40)
        
        priority_missing = {}
        
        for col in columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                total_count = len(df)
                missing_percentage = (missing_count / total_count) * 100
                
                priority_missing[col] = {
                    'missing_count': missing_count,
                    'total_count': total_count,
                    'missing_percentage': missing_percentage
                }
                
                print(f"   {col}: {missing_count}/{total_count} missing ({missing_percentage:.1f}%)")
                
                # If high priority column has significant missing data, flag it
                if priority == 'HIGH_PRIORITY' and missing_percentage > 20:
                    print(f"     ⚠️  WARNING: High priority column with significant missing data!")
        
        missing_analysis[priority] = priority_missing
    
    # Find ASINs with missing high-priority data
    print(f"\n🎯 ASINs WITH MISSING HIGH-PRIORITY DATA")
    print("=" * 60)
    
    high_priority_cols = important_columns['HIGH_PRIORITY']
    asins_with_missing = defaultdict(list)
    
    for idx, row in df.iterrows():
        asin = row['asin']
        missing_cols = []
        
        for col in high_priority_cols:
            if col in df.columns and pd.isna(row[col]):
                missing_cols.append(col)
        
        if missing_cols:
            asins_with_missing[asin] = missing_cols
    
    # Sort ASINs by number of missing high-priority columns
    sorted_asins = sorted(asins_with_missing.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"Found {len(sorted_asins)} ASINs with missing high-priority data:")
    
    # Select top ASINs for detailed inspection
    inspection_candidates = []
    
    for asin, missing_cols in sorted_asins[:10]:  # Top 10
        print(f"\n📦 ASIN: {asin}")
        print(f"   Missing columns: {missing_cols}")
        print(f"   Missing count: {len(missing_cols)}")
        
        # Get the row data
        row = df[df['asin'] == asin].iloc[0]
        print(f"   Product name: {row.get('name', 'N/A')}")
        print(f"   Brand: {row.get('brand', 'N/A')}")
        
        inspection_candidates.append({
            'asin': asin,
            'missing_cols': missing_cols,
            'missing_count': len(missing_cols),
            'name': row.get('name', 'N/A'),
            'brand': row.get('brand', 'N/A')
        })
    
    # Select 3 ASINs for detailed JSON inspection
    selected_asins = inspection_candidates[:3]
    
    print(f"\n🔍 SELECTED ASINs FOR JSON INSPECTION")
    print("=" * 60)
    
    for candidate in selected_asins:
        asin = candidate['asin']
        missing_cols = candidate['missing_cols']
        
        print(f"\n📦 Inspecting ASIN: {asin}")
        print(f"   Product: {candidate['name']}")
        print(f"   Brand: {candidate['brand']}")
        print(f"   Missing columns: {missing_cols}")
        
        # Check if JSON file exists
        json_file = f"{asin}_product_details.json"
        if os.path.exists(json_file):
            print(f"   ✅ JSON file found: {json_file}")
            
            # Load and inspect the JSON
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                
                # Inspect the structure for missing data
                detail = product_data.get('detail', {})
                
                print(f"   📊 JSON Structure Analysis:")
                
                # Check each missing column's potential sources
                for missing_col in missing_cols:
                    print(f"\n     🔍 Looking for data related to: {missing_col}")
                    
                    # Check different fields that might contain this data
                    potential_sources = {
                        'overview': detail.get('overview', []),
                        'details_table': detail.get('details_table', []),
                        'technical_details': detail.get('technical_details', []),
                        'features': detail.get('features', []),
                        'from_the_manufacturer': detail.get('from_the_manufacturer', {}),
                        'variants': detail.get('variants', {}),
                    }
                    
                    found_data = False
                    
                    for source_name, source_data in potential_sources.items():
                        if source_data:
                            # Search for relevant data in this source
                            if isinstance(source_data, list):
                                for item in source_data:
                                    if isinstance(item, dict) and 'name' in item and 'value' in item:
                                        name = item['name'].lower()
                                        value = item['value']
                                        
                                        # Check if this item might be related to the missing column
                                        if any(keyword in name for keyword in get_keywords_for_column(missing_col)):
                                            print(f"       ✅ Found in {source_name}: '{item['name']}' = '{value}'")
                                            found_data = True
                            
                            elif isinstance(source_data, dict):
                                # Handle structured data like from_the_manufacturer
                                if 'text_content' in source_data:
                                    text_content = source_data['text_content']
                                    if isinstance(text_content, list):
                                        for text in text_content:
                                            if any(keyword in text.lower() for keyword in get_keywords_for_column(missing_col)):
                                                print(f"       ✅ Found in {source_name}: '{text[:100]}...'")
                                                found_data = True
                    
                    if not found_data:
                        print(f"       ❌ No relevant data found for {missing_col}")
                
            except Exception as e:
                print(f"   ❌ Error reading JSON file: {e}")
        else:
            print(f"   ❌ JSON file not found: {json_file}")
    
    # Generate summary report
    print(f"\n📊 MISSING DATA SUMMARY")
    print("=" * 60)
    
    total_asins = len(df)
    asins_with_high_priority_missing = len(asins_with_missing)
    
    print(f"Total ASINs: {total_asins}")
    print(f"ASINs with missing high-priority data: {asins_with_high_priority_missing}")
    print(f"Percentage with missing high-priority data: {(asins_with_high_priority_missing/total_asins)*100:.1f}%")
    
    # Most commonly missing columns
    all_missing_cols = []
    for missing_cols in asins_with_missing.values():
        all_missing_cols.extend(missing_cols)
    
    missing_col_counts = Counter(all_missing_cols)
    print(f"\nMost commonly missing high-priority columns:")
    for col, count in missing_col_counts.most_common():
        percentage = (count / total_asins) * 100
        print(f"   {col}: {count} ASINs ({percentage:.1f}%)")
    
    # Save analysis report
    analysis_report = {
        'important_columns': important_columns,
        'missing_analysis': missing_analysis,
        'asins_with_missing': dict(asins_with_missing),
        'inspection_candidates': inspection_candidates,
        'missing_col_counts': dict(missing_col_counts)
    }
    
    with open('missing_data_analysis.json', 'w') as f:
        json.dump(analysis_report, f, indent=2, default=str)
    
    print(f"\n📄 Analysis report saved to: missing_data_analysis.json")

def get_keywords_for_column(column_name):
    """Get relevant keywords for searching a specific column."""
    keyword_mapping = {
        'materi': ['material', 'wire', 'copper', 'aluminum', 'steel', 'pvc', 'insulation'],
        'no_of_wire': ['gauge', 'awg', 'wire', 'strand', 'conductor'],
        'voltag': ['voltage', 'volt', 'v', 'rating', 'rated'],
        'conductor': ['conductor', 'strand', 'wire', 'cable'],
        'size': ['size', 'length', 'dimension', 'ft', 'meter', 'm', 'inch'],
        'brand': ['brand', 'manufacturer', 'make'],
        'price': ['price', 'cost', '$', 'dollar'],
        'color': ['color', 'colour', 'red', 'black', 'white', 'blue'],
        'certification': ['ul', 'csa', 'ce', 'rohs', 'certification', 'approved'],
        'temperature': ['temperature', 'temp', 'celsius', 'fahrenheit', '°c', '°f'],
        'length': ['length', 'long', 'ft', 'meter', 'm', 'inch'],
        'package_weight': ['weight', 'oz', 'gram', 'kg', 'pound', 'lb'],
        'best_seller_rank': ['rank', 'seller', 'best', 'top', '#'],
    }
    
    return keyword_mapping.get(column_name, [column_name])

if __name__ == "__main__":
    analyze_missing_data() 