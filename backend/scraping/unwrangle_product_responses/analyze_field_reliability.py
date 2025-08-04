#!/usr/bin/env python3
"""
Analyze field reliability in conflict situations.
This script examines which fields tend to provide more accurate/reliable information
when conflicts occur between different source fields.
"""

import pandas as pd
import json
from collections import defaultdict, Counter
import re

def analyze_field_reliability():
    """Analyze which fields are more reliable in conflict situations."""
    
    # Read the V6 CSV file
    df = pd.read_csv('extracted_product_details_v6.csv')
    
    print("Analyzing Field Reliability in Conflicts")
    print("=" * 60)
    
    # Find all columns with conflicts
    conflict_columns = []
    for col in df.columns:
        if not col.endswith('_origin') and col not in ['asin', 'name', 'brand', 'price', 'rating', 'total_ratings', 'file_source']:
            conflict_rows = df[df[col].astype(str).str.contains('⚠️CONFLICT⚠️', na=False)]
            if not conflict_rows.empty:
                conflict_columns.append(col)
    
    print(f"Found {len(conflict_columns)} columns with conflicts")
    print()
    
    # Analyze each conflict column
    field_reliability_stats = defaultdict(lambda: {'count': 0, 'examples': []})
    
    for col in conflict_columns:
        print(f"🔍 Analyzing column: {col}")
        
        conflict_rows = df[df[col].astype(str).str.contains('⚠️CONFLICT⚠️', na=False)]
        origin_col = f"{col}_origin"
        
        if origin_col not in df.columns:
            print(f"   No origin data found for {col}")
            continue
        
        print(f"   Found {len(conflict_rows)} conflicts")
        
        for idx, row in conflict_rows.iterrows():
            asin = row['asin']
            value = row[col]
            origin_str = row[origin_col]
            
            if pd.isna(origin_str):
                continue
                
            try:
                origin_dict = eval(origin_str)
                
                # Count which fields are involved in this conflict
                for field, field_value in origin_dict.items():
                    field_reliability_stats[field]['count'] += 1
                    field_reliability_stats[field]['examples'].append({
                        'column': col,
                        'asin': asin,
                        'value': field_value,
                        'conflict_value': value
                    })
                
                print(f"   ASIN {asin}: {len(origin_dict)} fields in conflict")
                for field, field_value in origin_dict.items():
                    print(f"     - {field}: '{field_value}'")
                
            except Exception as e:
                print(f"   Error parsing origin for ASIN {asin}: {e}")
        
        print()
    
    # Analyze field reliability patterns
    print("📊 Field Reliability Analysis")
    print("=" * 60)
    
    # Sort fields by conflict frequency
    sorted_fields = sorted(field_reliability_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for field, stats in sorted_fields:
        print(f"\n🔍 {field.upper()}")
        print(f"   Involved in {stats['count']} conflicts")
        
        # Analyze the types of conflicts this field is involved in
        conflict_types = Counter()
        value_patterns = []
        
        for example in stats['examples']:
            conflict_types[example['column']] += 1
            value_patterns.append(example['value'])
        
        print(f"   Most common conflict columns:")
        for col, count in conflict_types.most_common(3):
            print(f"     - {col}: {count} conflicts")
        
        # Analyze value patterns
        print(f"   Sample values: {value_patterns[:5]}")
    
    # Analyze specific conflict patterns
    print("\n🎯 Specific Conflict Pattern Analysis")
    print("=" * 60)
    
    # Look for patterns where certain fields consistently disagree
    field_pairs = defaultdict(int)
    
    for col in conflict_columns:
        origin_col = f"{col}_origin"
        if origin_col not in df.columns:
            continue
            
        conflict_rows = df[df[col].astype(str).str.contains('⚠️CONFLICT⚠️', na=False)]
        
        for idx, row in conflict_rows.iterrows():
            origin_str = row[origin_col]
            if pd.isna(origin_str):
                continue
                
            try:
                origin_dict = eval(origin_str)
                fields = list(origin_dict.keys())
                
                # Record field pairs that conflict
                for i in range(len(fields)):
                    for j in range(i+1, len(fields)):
                        pair = tuple(sorted([fields[i], fields[j]]))
                        field_pairs[pair] += 1
                        
            except:
                continue
    
    print("Most common field conflict pairs:")
    for (field1, field2), count in sorted(field_pairs.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {field1} ↔ {field2}: {count} conflicts")
    
    # Analyze value quality by field
    print("\n📈 Value Quality Analysis by Field")
    print("=" * 60)
    
    field_quality = {}
    
    for field, stats in field_reliability_stats.items():
        values = [ex['value'] for ex in stats['examples']]
        
        # Analyze value characteristics
        quality_metrics = {
            'total_values': len(values),
            'unique_values': len(set(values)),
            'avg_length': sum(len(str(v)) for v in values) / len(values) if values else 0,
            'has_numbers': sum(1 for v in values if re.search(r'\d', str(v))),
            'has_units': sum(1 for v in values if re.search(r'(AWG|V|A|°C|ft|oz|g|kg)', str(v), re.IGNORECASE)),
            'is_detailed': sum(1 for v in values if len(str(v)) > 10),
        }
        
        field_quality[field] = quality_metrics
        
        print(f"\n🔍 {field.upper()}")
        print(f"   Total values: {quality_metrics['total_values']}")
        print(f"   Unique values: {quality_metrics['unique_values']}")
        print(f"   Average length: {quality_metrics['avg_length']:.1f} chars")
        print(f"   Contains numbers: {quality_metrics['has_numbers']} ({quality_metrics['has_numbers']/quality_metrics['total_values']*100:.1f}%)")
        print(f"   Contains units: {quality_metrics['has_units']} ({quality_metrics['has_units']/quality_metrics['total_values']*100:.1f}%)")
        print(f"   Detailed descriptions: {quality_metrics['is_detailed']} ({quality_metrics['is_detailed']/quality_metrics['total_values']*100:.1f}%)")
    
    # Provide recommendations
    print("\n💡 Field Reliability Recommendations")
    print("=" * 60)
    
    # Based on the analysis, provide recommendations
    recommendations = {
        'details_table': 'HIGH - Structured data, consistent format',
        'overview': 'MEDIUM - Good for basic specs, may have formatting issues',
        'technical_details': 'HIGH - Technical specifications, usually accurate',
        'features': 'MEDIUM - May contain marketing language, less structured',
        'from_the_manufacturer': 'MEDIUM-HIGH - Official info but may be marketing-focused',
        'variant_info': 'MEDIUM - Product variants, may be incomplete',
        'variants': 'LOW-MEDIUM - Limited data, may be incomplete'
    }
    
    for field, reliability in recommendations.items():
        if field in field_reliability_stats:
            conflict_count = field_reliability_stats[field]['count']
            print(f"   {field.upper()}: {reliability} ({conflict_count} conflicts)")
        else:
            print(f"   {field.upper()}: {reliability} (no conflicts found)")
    
    # Save detailed analysis
    analysis_report = {
        'field_reliability_stats': dict(field_reliability_stats),
        'field_quality_metrics': field_quality,
        'field_pairs_conflicts': {f"{field1}__{field2}": count for (field1, field2), count in field_pairs.items()},
        'recommendations': recommendations
    }
    
    with open('field_reliability_analysis.json', 'w') as f:
        json.dump(analysis_report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed analysis saved to: field_reliability_analysis.json")

if __name__ == "__main__":
    analyze_field_reliability() 