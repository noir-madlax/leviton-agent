#!/usr/bin/env python3
"""
Script to analyze conflicts and determine if they're true conflicts or merging problems.
"""

import pandas as pd
import json
import re
from collections import defaultdict

def analyze_conflict_details(df, column_name):
    """Analyze conflicts in a specific column."""
    
    # Find rows with conflicts
    conflict_rows = df[df[column_name].astype(str).str.contains('⚠️CONFLICT⚠️', na=False)]
    
    if conflict_rows.empty:
        return None
    
    analysis = {
        'column': column_name,
        'total_conflicts': len(conflict_rows),
        'conflict_details': []
    }
    
    for idx, row in conflict_rows.iterrows():
        asin = row['asin']
        value = row[column_name]
        origin_col = f"{column_name}_origin"
        origin = row[origin_col] if origin_col in row else {}
        
        # Parse the conflict value
        if isinstance(value, str) and '⚠️CONFLICT⚠️' in value:
            # Extract the actual value after the conflict marker
            actual_value = value.replace('⚠️CONFLICT⚠️', '').strip()
        else:
            actual_value = value
        
        conflict_detail = {
            'asin': asin,
            'conflict_value': value,
            'actual_value': actual_value,
            'origin': origin,
            'origin_count': len(origin) if isinstance(origin, dict) else 0,
            'is_single_origin': len(origin) == 1 if isinstance(origin, dict) else False,
            'origin_fields': list(origin.keys()) if isinstance(origin, dict) else []
        }
        
        analysis['conflict_details'].append(conflict_detail)
    
    return analysis

def analyze_all_conflicts(df):
    """Analyze all conflicts in the dataset."""
    
    # Find all columns with conflicts
    conflict_columns = []
    for col in df.columns:
        if not col.endswith('_origin') and col not in ['asin', 'name', 'brand', 'price', 'rating', 'total_ratings', 'file_source']:
            conflict_rows = df[df[col].astype(str).str.contains('⚠️CONFLICT⚠️', na=False)]
            if not conflict_rows.empty:
                conflict_columns.append(col)
    
    print(f"Found {len(conflict_columns)} columns with conflicts:")
    print("=" * 60)
    
    all_analyses = []
    
    for col in conflict_columns:
        analysis = analyze_conflict_details(df, col)
        if analysis:
            all_analyses.append(analysis)
            
            print(f"\n🔍 Column: {col}")
            print(f"   Total conflicts: {analysis['total_conflicts']}")
            
            # Count single origin conflicts
            single_origin_count = sum(1 for detail in analysis['conflict_details'] if detail['is_single_origin'])
            print(f"   Single origin conflicts: {single_origin_count}")
            
            # Show sample conflicts
            print("   Sample conflicts:")
            for detail in analysis['conflict_details'][:3]:
                print(f"     ASIN {detail['asin']}: '{detail['conflict_value']}'")
                print(f"       Origin fields: {detail['origin_fields']}")
                print(f"       Origin count: {detail['origin_count']}")
    
    return all_analyses

def investigate_single_origin_conflicts(df, analyses):
    """Investigate why there are conflicts with single origins."""
    
    print("\n" + "=" * 60)
    print("INVESTIGATING SINGLE ORIGIN CONFLICTS")
    print("=" * 60)
    
    single_origin_conflicts = []
    
    for analysis in analyses:
        for detail in analysis['conflict_details']:
            if detail['is_single_origin']:
                single_origin_conflicts.append({
                    'column': analysis['column'],
                    'asin': detail['asin'],
                    'value': detail['conflict_value'],
                    'origin': detail['origin']
                })
    
    print(f"Found {len(single_origin_conflicts)} single origin conflicts")
    
    # Group by column to see patterns
    by_column = defaultdict(list)
    for conflict in single_origin_conflicts:
        by_column[conflict['column']].append(conflict)
    
    for column, conflicts in by_column.items():
        print(f"\n📊 Column '{column}' has {len(conflicts)} single origin conflicts:")
        
        for conflict in conflicts[:5]:  # Show first 5
            print(f"   ASIN {conflict['asin']}: '{conflict['value']}'")
            print(f"     Origin: {conflict['origin']}")
            
            # Check if this is a regex-extracted value
            if isinstance(conflict['origin'], dict):
                for field, value in conflict['origin'].items():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"     Field '{field}' has {len(value)} values")
                        if len(value) > 1:
                            print(f"     Multiple values in single field: {value}")

def check_merging_issues(df, analyses):
    """Check for potential merging issues."""
    
    print("\n" + "=" * 60)
    print("CHECKING FOR MERGING ISSUES")
    print("=" * 60)
    
    # Look for patterns that suggest merging problems
    merging_issues = []
    
    for analysis in analyses:
        column = analysis['column']
        
        # Check if conflicts have very similar values
        similar_value_conflicts = []
        for detail in analysis['conflict_details']:
            actual_value = detail['actual_value']
            if isinstance(actual_value, str):
                # Check for formatting differences
                clean_value = re.sub(r'[^\w\s]', '', actual_value.lower())
                similar_value_conflicts.append(clean_value)
        
        # If many conflicts have similar cleaned values, it might be a formatting issue
        if len(set(similar_value_conflicts)) < len(similar_value_conflicts) * 0.8:
            merging_issues.append({
                'column': column,
                'issue_type': 'formatting_differences',
                'description': 'Many conflicts have similar values with different formatting'
            })
        
        # Check for regex extraction conflicts
        regex_conflicts = []
        for detail in analysis['conflict_details']:
            if isinstance(detail['origin'], dict):
                for field, value in detail['origin'].items():
                    if isinstance(value, list) and len(value) > 1:
                        regex_conflicts.append({
                            'field': field,
                            'values': value
                        })
        
        if regex_conflicts:
            merging_issues.append({
                'column': column,
                'issue_type': 'regex_extraction',
                'description': f'Regex extracted multiple values from same field',
                'details': regex_conflicts
            })
    
    print(f"Found {len(merging_issues)} potential merging issues:")
    
    for issue in merging_issues:
        print(f"\n⚠️  {issue['column']}: {issue['issue_type']}")
        print(f"    {issue['description']}")
        if 'details' in issue:
            for detail in issue['details'][:3]:  # Show first 3
                print(f"    Field '{detail['field']}': {detail['values']}")

def main():
    """Main analysis function."""
    
    # Read the CSV file
    df = pd.read_csv('extracted_product_details_v3.csv')
    
    print("Analyzing conflicts in extracted data...")
    print("=" * 60)
    
    # Analyze all conflicts
    analyses = analyze_all_conflicts(df)
    
    # Investigate single origin conflicts
    investigate_single_origin_conflicts(df, analyses)
    
    # Check for merging issues
    check_merging_issues(df, analyses)
    
    # Save detailed analysis
    with open('conflict_analysis_detailed.json', 'w') as f:
        json.dump(analyses, f, indent=2, default=str)
    
    print(f"\nDetailed analysis saved to conflict_analysis_detailed.json")

if __name__ == "__main__":
    main() 