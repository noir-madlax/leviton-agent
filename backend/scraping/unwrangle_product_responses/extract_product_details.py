#!/usr/bin/env python3
"""
Comprehensive script to extract and flatten product details from JSON files.
Features:
- NLTK stemming for key merging
- Conflict detection and resolution
- Regex extraction from features and additional fields
- Origin tracking for all data sources
"""

import json
import os
import re
import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any, Tuple
import nltk
from nltk.stem import PorterStemmer
import logging
from datetime import datetime

# Constants
TARGET_FIELDS = ['overview', 'details_table', 'technical_details', 'features']
ADDITIONAL_FIELDS = ['variant_info', 'from_the_manufacturer', 'variants']
CONFLICT_MARKER = "⚠️CONFLICT⚠️"
REGEX_EXTRACTED_MARKER = "🔍REGEX🔍"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction_log.txt'),
        logging.StreamHandler()
    ]
)

class ProductDetailsExtractor:
    def __init__(self):
        """Initialize the extractor with NLTK stemmer and regex patterns."""
        # Download NLTK data if not available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        self.stemmer = PorterStemmer()
        
        # Regex patterns for extracting specifications
        self.regex_patterns = {
            'voltage': r'\b(\d+(?:\.\d+)?)\s*(?:V|Volts?|volts?)\b',
            'current': r'\b(\d+(?:\.\d+)?)\s*(?:A|Amps?|amps?)\b',
            'temperature': r'\b(-?\d+(?:\.\d+)?)\s*(?:°C|°F|Celsius|Fahrenheit)\b',
            'length': r'\b(\d+(?:\.\d+)?)\s*(?:ft|feet|m|meters?|cm|centimeters?)\b',
            'gauge': r'\b(\d+(?:\.\d+)?)\s*(?:AWG|awg|gauge)\b',
            'strands': r'\b(\d+)\s*(?:strands?|strand)\b',
            'conductor': r'\b(\d+)\s*(?:conductor|conductors?)\b',
            'wire_count': r'\b(\d+)\s*(?:wire|wires?)\b',
            'package_weight': r'\b(\d+(?:\.\d+)?)\s*(?:oz|ounces?|g|grams?|kg|kilograms?)\b',
            'dimensions': r'\b(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:inches?|cm|mm)\b',
            'material': r'\b(Copper|Aluminum|Steel|PVC|Silicone|Tinned\s+Copper|Galvanized)\b',
            'color': r'\b(Black|Red|Yellow|White|Green|Blue|Brown|Orange|Purple|Gray|Silver|Gold)\b',
            'certification': r'\b(UL|CSA|CE|RoHS|VW-1|FT1|Flame\s+Retardant)\b',
            'temperature_range': r'\b(-?\d+(?:\.\d+)?)\s*(?:°C|°F)\s*to\s*(-?\d+(?:\.\d+)?)\s*(?:°C|°F)\b',
            'voltage_rating': r'\b(\d+(?:\.\d+)?)\s*(?:V|Volts?)\s*(?:rated?|rating)\b',
            'max_voltage': r'\b(\d+(?:\.\d+)?)\s*(?:V|Volts?)\s*(?:max|maximum)\b',
            'max_current': r'\b(\d+(?:\.\d+)?)\s*(?:A|Amps?)\s*(?:max|maximum)\b',
            'variant_gauge_conductor': r'(\d+)\s*AWG-(\d+)C',
            'variant_size': r'(\d+(?:\.\d+)?)\s*(?:FT|ft|M|m)',
        }
        
        # Field priority for conflict resolution
        self.field_priority = {
            'details_table': 1,
            'overview': 2,
            'technical_details': 3,
            'variant_info': 4,
            'from_the_manufacturer': 5,
            'features': 6
        }
        
        self.schema = set()
        self.extraction_stats = {
            'files_processed': 0,
            'conflicts_found': 0,
            'regex_extractions': 0,
            'stem_merges': 0
        }

    def get_stemmed_key(self, key: str) -> str:
        """Get stemmed version of a key for merging similar keys."""
        # Clean and stem the key
        clean_key = re.sub(r'[^\w\s]', '', key.lower())
        words = clean_key.split()
        stemmed_words = [self.stemmer.stem(word) for word in words]
        return '_'.join(stemmed_words)

    def extract_field_data(self, product_data: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
        """Extract data from all target fields."""
        result = {}
        
        # Extract from main fields
        for field in TARGET_FIELDS:
            field_data = product_data.get('detail', {}).get(field, [])
            if isinstance(field_data, list):
                result[field] = field_data
            else:
                result[field] = []
        
        # Extract from additional fields
        detail = product_data.get('detail', {})
        
        # Extract variant_info from reviews
        variant_info = []
        for review in detail.get('top_reviews', []):
            if isinstance(review, dict) and 'variant_info' in review:
                variant_info.extend(review.get('variant_info', []))
        result['variant_info'] = variant_info
        
        # Extract from_the_manufacturer text
        manufacturer_text = []
        manufacturer_data = detail.get('from_the_manufacturer', {})
        if isinstance(manufacturer_data, dict) and 'text_content' in manufacturer_data:
            manufacturer_text = manufacturer_data.get('text_content', [])
        result['from_the_manufacturer'] = manufacturer_text
        
        # Extract variants
        variants = []
        variants_data = detail.get('variants', {})
        if isinstance(variants_data, dict):
            for variant_type, variant_list in variants_data.items():
                if isinstance(variant_list, list):
                    for variant in variant_list:
                        if isinstance(variant, dict) and 'name' in variant:
                            variants.append({'name': variant['name'], 'type': variant_type})
        result['variants'] = variants
        
        return result

    def extract_regex_data(self, text_list: List[str], field_name: str) -> Dict[str, Any]:
        """Extract data using regex patterns from text."""
        extracted_data = {}
        origin_info = {}
        
        for text in text_list:
            if not isinstance(text, str):
                continue
                
            for pattern_name, pattern in self.regex_patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if pattern_name not in extracted_data:
                        extracted_data[pattern_name] = []
                        origin_info[pattern_name] = []
                    
                    extracted_data[pattern_name].extend(matches)
                    origin_info[pattern_name].append({
                        'field': field_name,
                        'text': text[:100] + '...' if len(text) > 100 else text,
                        'matches': matches
                    })
        
        return extracted_data, origin_info

    def merge_stemmed_keys(self, all_keys: Set[str]) -> Dict[str, List[str]]:
        """Group keys by their stemmed versions."""
        stemmed_groups = defaultdict(list)
        
        for key in all_keys:
            stemmed_key = self.get_stemmed_key(key)
            stemmed_groups[stemmed_key].append(key)
        
        return dict(stemmed_groups)

    def resolve_conflicts(self, values_by_field: Dict[str, Any]) -> Tuple[Any, Dict[str, Any], bool]:
        """Resolve conflicts when the same key has different values across fields."""
        if len(values_by_field) <= 1:
            return list(values_by_field.values())[0], values_by_field, False
        
        # Check if all values are the same
        unique_values = set(str(v) for v in values_by_field.values())
        if len(unique_values) == 1:
            return list(values_by_field.values())[0], values_by_field, False
        
        # There's a conflict - use priority to select primary value
        sorted_fields = sorted(values_by_field.items(), 
                             key=lambda x: self.field_priority.get(x[0], 999))
        
        primary_value = sorted_fields[0][1]
        origin_info = dict(values_by_field)
        
        return primary_value, origin_info, True

    def process_single_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single product details file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                product_data = json.load(f)
        except Exception as e:
            logging.error(f"Error loading {file_path}: {e}")
            return {}
        
        if not product_data or 'detail' not in product_data:
            return {}
        
        # Extract basic product info
        detail = product_data['detail']
        result = {
            'asin': detail.get('asin', ''),
            'name': detail.get('name', ''),
            'brand': detail.get('brand', ''),
            'price': detail.get('price', ''),
            'rating': detail.get('rating', ''),
            'total_ratings': detail.get('total_ratings', ''),
            'file_source': os.path.basename(file_path)
        }
        
        # Extract field data
        field_data = self.extract_field_data(product_data)
        
        # Collect all keys and their values
        key_values = defaultdict(dict)
        
        # Process structured fields (overview, details_table, technical_details)
        for field in ['overview', 'details_table', 'technical_details']:
            for item in field_data.get(field, []):
                if isinstance(item, dict) and 'name' in item and 'value' in item:
                    key = item['name'].strip()
                    value = item['value'].strip()
                    key_values[key][field] = value
        
        # Process variant_info
        for variant_info in field_data.get('variant_info', []):
            if isinstance(variant_info, str):
                # Extract gauge and conductor info from variant strings
                gauge_match = re.search(r'(\d+)\s*AWG', variant_info, re.IGNORECASE)
                conductor_match = re.search(r'(\d+)C', variant_info, re.IGNORECASE)
                
                if gauge_match:
                    key_values['Gauge']['variant_info'] = gauge_match.group(1)
                if conductor_match:
                    key_values['Conductor_Count']['variant_info'] = conductor_match.group(1)
        
        # Process manufacturer text with regex
        manufacturer_text = field_data.get('from_the_manufacturer', [])
        if manufacturer_text:
            regex_data, regex_origin = self.extract_regex_data(manufacturer_text, 'from_the_manufacturer')
            for pattern_name, matches in regex_data.items():
                if matches:
                    key_values[pattern_name]['from_the_manufacturer'] = matches[0]
                    if pattern_name not in result:
                        result[f'{pattern_name}_origin'] = regex_origin[pattern_name]
        
        # Process features with regex
        features = field_data.get('features', [])
        if features:
            regex_data, regex_origin = self.extract_regex_data(features, 'features')
            for pattern_name, matches in regex_data.items():
                if matches:
                    if pattern_name not in key_values:
                        key_values[pattern_name] = {}
                    key_values[pattern_name]['features'] = matches[0]
                    if pattern_name not in result:
                        result[f'{pattern_name}_origin'] = regex_origin[pattern_name]
        
        # Process variants
        for variant in field_data.get('variants', []):
            if isinstance(variant, dict) and 'name' in variant:
                variant_name = variant['name']
                # Extract specifications from variant names
                gauge_match = re.search(r'(\d+)\s*AWG', variant_name, re.IGNORECASE)
                if gauge_match:
                    key_values['Gauge']['variants'] = gauge_match.group(1)
        
        # Resolve conflicts and add to result
        for key, values_by_field in list(key_values.items()):
            primary_value, origin_info, has_conflict = self.resolve_conflicts(values_by_field)
            
            # Add primary value
            result[key] = primary_value
            
            # Add origin information
            result[f'{key}_origin'] = origin_info
            
            # Mark conflicts
            if has_conflict:
                result[key] = f"{CONFLICT_MARKER} {primary_value}"
                self.extraction_stats['conflicts_found'] += 1
        
        return result

    def discover_schema(self, directory: str, sample_size: int = 10) -> Set[str]:
        """Discover the complete schema from sample files."""
        json_files = [f for f in os.listdir(directory) if f.endswith('_product_details.json')]
        sample_files = json_files[:sample_size]
        
        all_keys = set()
        
        for filename in sample_files:
            file_path = os.path.join(directory, filename)
            result = self.process_single_file(file_path)
            
            for key in result.keys():
                if not key.endswith('_origin') and key not in ['asin', 'name', 'brand', 'price', 'rating', 'total_ratings', 'file_source']:
                    all_keys.add(key)
        
        return all_keys

    def extract_all_files(self, directory: str) -> pd.DataFrame:
        """Extract data from all product detail files."""
        json_files = [f for f in os.listdir(directory) if f.endswith('_product_details.json')]
        
        logging.info(f"Processing {len(json_files)} files...")
        
        all_results = []
        
        for i, filename in enumerate(json_files):
            if i % 10 == 0:
                logging.info(f"Processing file {i+1}/{len(json_files)}: {filename}")
            
            file_path = os.path.join(directory, filename)
            result = self.process_single_file(file_path)
            
            if result:
                all_results.append(result)
                self.extraction_stats['files_processed'] += 1
        
        # Create DataFrame
        df = pd.DataFrame(all_results)
        
        # Reorder columns to put origins after their corresponding columns
        column_order = ['asin', 'name', 'brand', 'price', 'rating', 'total_ratings', 'file_source']
        
        # Add data columns first, then their origins
        data_columns = [col for col in df.columns if not col.endswith('_origin') and col not in column_order]
        origin_columns = [col for col in df.columns if col.endswith('_origin')]
        
        # Sort data columns alphabetically
        data_columns.sort()
        
        # Group origins with their data columns
        final_order = column_order.copy()
        for data_col in data_columns:
            final_order.append(data_col)
            origin_col = f"{data_col}_origin"
            if origin_col in df.columns:
                final_order.append(origin_col)
        
        # Reorder DataFrame
        df = df.reindex(columns=final_order)
        
        return df

    def generate_reports(self, df: pd.DataFrame, output_dir: str = '.'):
        """Generate comprehensive reports."""
        
        # Save main CSV
        csv_path = os.path.join(output_dir, 'extracted_product_details.csv')
        df.to_csv(csv_path, index=False)
        logging.info(f"Main CSV saved to: {csv_path}")
        
        # Generate conflict report
        conflict_report = {
            'total_conflicts': self.extraction_stats['conflicts_found'],
            'conflict_details': []
        }
        
        for col in df.columns:
            if not col.endswith('_origin') and col not in ['asin', 'name', 'brand', 'price', 'rating', 'total_ratings', 'file_source']:
                conflict_rows = df[df[col].astype(str).str.contains(CONFLICT_MARKER, na=False)]
                if not conflict_rows.empty:
                    conflict_report['conflict_details'].append({
                        'column': col,
                        'conflict_count': len(conflict_rows),
                        'conflict_asins': conflict_rows['asin'].tolist()
                    })
        
        # Save conflict report
        conflict_path = os.path.join(output_dir, 'conflict_report.json')
        with open(conflict_path, 'w') as f:
            json.dump(conflict_report, f, indent=2)
        logging.info(f"Conflict report saved to: {conflict_path}")
        
        # Generate extraction statistics
        stats_report = {
            'extraction_timestamp': datetime.now().isoformat(),
            'files_processed': self.extraction_stats['files_processed'],
            'total_columns': len(df.columns),
            'data_columns': len([col for col in df.columns if not col.endswith('_origin')]),
            'origin_columns': len([col for col in df.columns if col.endswith('_origin')]),
            'total_rows': len(df),
            'conflicts_found': self.extraction_stats['conflicts_found'],
            'regex_extractions': self.extraction_stats['regex_extractions'],
            'stem_merges': self.extraction_stats['stem_merges']
        }
        
        # Save statistics
        stats_path = os.path.join(output_dir, 'extraction_statistics.json')
        with open(stats_path, 'w') as f:
            json.dump(stats_report, f, indent=2)
        logging.info(f"Extraction statistics saved to: {stats_path}")
        
        # Generate schema mapping
        schema_mapping = {
            'regex_patterns': self.regex_patterns,
            'field_priority': self.field_priority,
            'target_fields': TARGET_FIELDS,
            'additional_fields': ADDITIONAL_FIELDS
        }
        
        schema_path = os.path.join(output_dir, 'schema_mapping.json')
        with open(schema_path, 'w') as f:
            json.dump(schema_mapping, f, indent=2)
        logging.info(f"Schema mapping saved to: {schema_path}")

def main():
    """Main function to run the extraction process."""
    current_dir = os.getcwd()
    
    logging.info("Starting product details extraction...")
    
    # Initialize extractor
    extractor = ProductDetailsExtractor()
    
    # Discover schema first
    logging.info("Discovering schema from sample files...")
    schema = extractor.discover_schema(current_dir, sample_size=20)
    logging.info(f"Discovered {len(schema)} unique columns in schema")
    
    # Extract all files
    logging.info("Extracting data from all files...")
    df = extractor.extract_all_files(current_dir)
    
    # Generate reports
    logging.info("Generating reports...")
    extractor.generate_reports(df)
    
    logging.info("Extraction completed successfully!")
    logging.info(f"Processed {extractor.extraction_stats['files_processed']} files")
    logging.info(f"Found {extractor.extraction_stats['conflicts_found']} conflicts")
    logging.info(f"Generated {len(df.columns)} columns")

if __name__ == "__main__":
    main() 