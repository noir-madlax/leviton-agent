#!/usr/bin/env python3
"""
Debug script to understand why conflicts are being marked incorrectly.
"""

import pandas as pd
import json

def debug_conflict_marking():
    """Debug the conflict marking logic."""
    
    # Read the CSV file
    df = pd.read_csv('extracted_product_details_v6.csv')
    
    print("Debugging conflict marking...")
    print("=" * 60)
    
    # Look at specific columns with conflicts
    conflict_columns = ['batteri_includ', 'conductor', 'materi', 'no_of_wire', 'numberofcablestrand']
    
    for col in conflict_columns:
        if col not in df.columns:
            continue
            
        print(f"\n🔍 Analyzing column: {col}")
        
        # Find rows with conflicts
        conflict_mask = df[col].astype(str).str.contains('⚠️CONFLICT⚠️', na=False)
        conflict_rows = df[conflict_mask]
        
        if conflict_rows.empty:
            print(f"   No conflicts found in {col}")
            continue
        
        print(f"   Found {len(conflict_rows)} conflicts")
        
        # Look at first few conflict rows
        for idx, row in conflict_rows.head(3).iterrows():
            asin = row['asin']
            value = row[col]
            origin_col = f"{col}_origin"
            origin = row[origin_col] if origin_col in df.columns else "NO_ORIGIN_COL"
            
            print(f"   ASIN {asin}:")
            print(f"     Value: '{value}'")
            print(f"     Origin: {origin}")
            
            # Check if origin is a valid dict
            if isinstance(origin, str) and origin.startswith('{'):
                try:
                    origin_dict = eval(origin)  # Be careful with eval in production
                    print(f"     Origin fields: {list(origin_dict.keys())}")
                    print(f"     Origin values: {origin_dict}")
                except:
                    print(f"     Could not parse origin as dict")
            else:
                print(f"     Origin type: {type(origin)}")

def check_merging_logic():
    """Check if the merging logic is working correctly."""
    
    print("\n" + "=" * 60)
    print("CHECKING MERGING LOGIC")
    print("=" * 60)
    
    # Read the original V4 file to compare
    try:
        df_v2 = pd.read_csv('extracted_product_details_v5.csv')
        print("Found V5 file for comparison")
        
        # Check if V2 has the same conflicts
        v2_conflicts = []
        for col in df_v2.columns:
            if not col.endswith('_origin'):
                conflict_rows = df_v2[df_v2[col].astype(str).str.contains('⚠️CONFLICT⚠️', na=False)]
                if not conflict_rows.empty:
                    v2_conflicts.append((col, len(conflict_rows)))
        
        print(f"V2 has conflicts in {len(v2_conflicts)} columns:")
        for col, count in v2_conflicts:
            print(f"   {col}: {count} conflicts")
            
    except FileNotFoundError:
        print("V5 file not found for comparison")

def analyze_origin_data():
    """Analyze the origin data structure."""
    
    print("\n" + "=" * 60)
    print("ANALYZING ORIGIN DATA STRUCTURE")
    print("=" * 60)
    
    df = pd.read_csv('extracted_product_details_v3.csv')
    
    # Look at origin columns
    origin_columns = [col for col in df.columns if col.endswith('_origin')]
    
    print(f"Found {len(origin_columns)} origin columns")
    
    # Check a few origin columns
    for col in origin_columns[:5]:
        base_col = col[:-7]  # Remove '_origin'
        print(f"\n📊 {col} (for {base_col}):")
        
        # Get non-null values
        non_null = df[col].dropna()
        print(f"   Non-null values: {len(non_null)}")
        
        if len(non_null) > 0:
            sample = non_null.iloc[0]
            print(f"   Sample value: {sample}")
            print(f"   Type: {type(sample)}")
            
            if isinstance(sample, str) and sample.startswith('{'):
                try:
                    parsed = eval(sample)
                    print(f"   Parsed as: {parsed}")
                    print(f"   Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                except:
                    print(f"   Could not parse as dict")

def main():
    """Main debug function."""
    
    debug_conflict_marking()
    check_merging_logic()
    analyze_origin_data()

if __name__ == "__main__":
    main() 