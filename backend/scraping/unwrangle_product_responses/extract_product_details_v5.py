#!/usr/bin/env python3
"""
Fixed product details extraction with proper conflict detection during ASIN processing.
Key changes:
- Conflict detection happens during individual ASIN processing
- Column merging only handles schema unification
- Value normalization before conflict comparison
- Proper origin data preservation
"""

import json
import os
import re
import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any, Tuple
import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import logging
from datetime import datetime
from difflib import SequenceMatcher

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
        logging.FileHandler('extraction_log_v5.txt'),
        logging.StreamHandler()
    ]
)

class ValueNormalizer:
    """Normalize values for comparison to detect true conflicts."""
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        
        # Unit patterns for numerical values
        self.unit_patterns = {
            'voltage': r'(\d+(?:\.\d+)?)\s*(V|Volts?|volts?)',
            'current': r'(\d+(?:\.\d+)?)\s*(A|Amps?|amps?)',
            'temperature': r'(\d+(?:\.\d+)?)\s*(°C|°F|Celsius|Fahrenheit|C|F)',
            'length': r'(\d+(?:\.\d+)?)\s*(ft|feet|m|meters?|cm|centimeters?|inches?)',
            'weight': r'(\d+(?:\.\d+)?)\s*(oz|ounces?|g|grams?|kg|kilograms?|lbs?|pounds?)',
            'gauge': r'(\d+(?:\.\d+)?)\s*(AWG|awg|gauge)',
        }

    def normalize_value(self, value: str) -> str:
        """Normalize a value for comparison."""
        if not isinstance(value, str):
            value = str(value)
        
        # Convert to lowercase
        normalized = value.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Handle common abbreviations and variations
        replacements = {
            'awg': 'gauge',
            'volts': 'volt',
            'voltage': 'volt',
            'amps': 'amp',
            'amperage': 'amp',
            'celsius': 'c',
            'fahrenheit': 'f',
            'feet': 'ft',
            'meters': 'm',
            'centimeters': 'cm',
            'inches': 'in',
            'ounces': 'oz',
            'grams': 'g',
            'kilograms': 'kg',
            'pounds': 'lb',
            'polyvinylchloride': 'pvc',
            'tinned': 'tin',
            'galvanized': 'galv',
            'flame retardant': 'flameretardant',
            'single strand': 'singlestrand',
            'multi strand': 'multistrand',
            'stranded': 'strand',
            'solid': 'solid',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Apply stemming to remaining words
        words = normalized.split()
        stemmed_words = [self.stemmer.stem(word) for word in words]
        normalized = ' '.join(stemmed_words)
        
        return normalized

    def are_values_equivalent(self, val1: str, val2: str) -> bool:
        """Check if two values are equivalent after normalization."""
        if pd.isna(val1) and pd.isna(val2):
            return True
        elif pd.isna(val1) or pd.isna(val2):
            return False
        
        norm1 = self.normalize_value(str(val1))
        norm2 = self.normalize_value(str(val2))
        
        # Exact match after normalization
        if norm1 == norm2:
            return True
        
        # Check for numerical values with units
        for unit_type, pattern in self.unit_patterns.items():
            match1 = re.search(pattern, str(val1), re.IGNORECASE)
            match2 = re.search(pattern, str(val2), re.IGNORECASE)
            
            if match1 and match2:
                # Extract numerical values
                num1 = float(match1.group(1))
                num2 = float(match2.group(1))
                unit1 = match1.group(2).lower()
                unit2 = match2.group(2).lower()
                
                # Normalize units
                unit1 = unit1.replace('volts', 'volt').replace('amps', 'amp')
                unit2 = unit2.replace('volts', 'volt').replace('amps', 'amp')
                
                # If same unit type and same value, they're equivalent
                if unit1 == unit2 and abs(num1 - num2) < 0.01:
                    return True
        
        # Check semantic similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity > 0.9

class IntelligentColumnMerger:
    """Intelligent column merging using heuristics and patterns."""
    
    def __init__(self):
        # Download NLTK data if not available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        self.stemmer = PorterStemmer()
        
        # Semantic patterns for column matching
        self.semantic_patterns = {
            'rank': ['rank', 'seller', 'best', 'top'],
            'battery': ['batteri', 'battery', 'includ', 'requir'],
            'connector': ['connector', 'connect', 'type', 'typ'],
            'temperature': ['temperatur', 'temperature', 'rate', 'celsius', 'fahrenheit'],
            'voltage': ['voltage', 'volt', 'rating', 'rated'],
            'gauge': ['gauge', 'awg', 'wire'],
            'material': ['material', 'contact', 'insulation'],
            'color': ['color', 'colour'],
            'length': ['length', 'cable', 'extension'],
            'weight': ['weight', 'package', 'item'],
            'dimension': ['dimension', 'size', 'package', 'product'],
            'model': ['model', 'part', 'number', 'item'],
            'manufacturer': ['manufacturer', 'brand'],
            'asin': ['asin'],
            'upc': ['upc', 'global', 'trade', 'identification'],
        }

    def normalize_column_name(self, column_name: str) -> str:
        """Normalize column name using stemming and cleaning."""
        # Remove _origin suffix
        if column_name.endswith('_origin'):
            column_name = column_name[:-7]
        
        # Clean the name
        clean_name = re.sub(r'[^\w\s]', '', column_name.lower())
        words = clean_name.split()
        
        # Apply stemming
        stemmed_words = [self.stemmer.stem(word) for word in words]
        return '_'.join(stemmed_words)

    def calculate_semantic_similarity(self, col1: str, col2: str) -> float:
        """Calculate semantic similarity between two column names."""
        # Normalize both column names
        norm1 = self.normalize_column_name(col1)
        norm2 = self.normalize_column_name(col2)
        
        # Check for exact match after normalization
        if norm1 == norm2:
            return 1.0
        
        # Check semantic patterns
        for category, patterns in self.semantic_patterns.items():
            col1_matches = any(pattern in col1.lower() for pattern in patterns)
            col2_matches = any(pattern in col2.lower() for pattern in patterns)
            
            if col1_matches and col2_matches:
                return 0.9
        
        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Boost similarity if they share common words
        words1 = set(norm1.split('_'))
        words2 = set(norm2.split('_'))
        common_words = words1.intersection(words2)
        
        if common_words:
            similarity += 0.2 * len(common_words) / max(len(words1), len(words2))
        
        return min(similarity, 1.0)

    def should_merge_columns(self, col1: str, col2: str, df: pd.DataFrame, threshold: float = 0.7) -> Tuple[bool, str]:
        """Determine if two columns should be merged based on name similarity and data overlap."""
        
        # Calculate semantic similarity
        similarity = self.calculate_semantic_similarity(col1, col2)
        
        if similarity < threshold:
            return False, f"Low semantic similarity: {similarity:.2f}"
        
        # Check data overlap
        if col1 in df.columns and col2 in df.columns:
            both_have_data = df[col1].notna() & df[col2].notna()
            overlap_count = both_have_data.sum()
            
            if overlap_count > 0:
                return True, f"High similarity ({similarity:.2f}) + data overlap ({overlap_count} rows)"
            else:
                # Check if they have complementary data
                count1 = df[col1].notna().sum()
                count2 = df[col2].notna().sum()
                
                if count1 > 0 and count2 > 0:
                    return True, f"High similarity ({similarity:.2f}) + complementary data"
        
        return True, f"High semantic similarity: {similarity:.2f}"

class ProductDetailsExtractorV5:
    def __init__(self):
        """Initialize the extractor with intelligent column merging."""
        self.merger = IntelligentColumnMerger()
        self.normalizer = ValueNormalizer()
        
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
        
        self.extraction_stats = {
            'files_processed': 0,
            'conflicts_found': 0,
            'columns_merged': 0,
            'semantic_matches': 0
        }

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
        """Extract data using regex patterns from text, preserving units."""
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
                    
                    # Preserve full matches with units
                    for match in matches:
                        if isinstance(match, tuple):
                            # For patterns with multiple groups, reconstruct the full match
                            full_match = ' '.join(match)
                        else:
                            full_match = match
                        
                        # Find the actual text that matched
                        match_obj = re.search(pattern, text, re.IGNORECASE)
                        if match_obj:
                            full_match = match_obj.group(0)
                        
                        extracted_data[pattern_name].append(full_match)
                        origin_info[pattern_name].append({
                            'field': field_name,
                            'text': text[:100] + '...' if len(text) > 100 else text,
                            'match': full_match
                        })
        
        return extracted_data, origin_info

    def detect_conflicts(self, values_by_field: Dict[str, Any]) -> Tuple[Any, Dict[str, Any], bool]:
        """Detect conflicts during ASIN processing with proper value normalization."""
        
        if len(values_by_field) == 1:
            # Single value, no conflict
            field, value = list(values_by_field.items())[0]
            return value, values_by_field, False
        
        # Multiple values - check for conflicts
        unique_normalized_values = set()
        normalized_to_original = {}
        
        for field, value in values_by_field.items():
            if pd.notna(value):
                normalized = self.normalizer.normalize_value(str(value))
                unique_normalized_values.add(normalized)
                if normalized not in normalized_to_original:
                    normalized_to_original[normalized] = []
                normalized_to_original[normalized].append((field, value))
        
        # If all values normalize to the same thing, no conflict
        if len(unique_normalized_values) == 1:
            # Use the highest priority field's value
            sorted_fields = sorted(values_by_field.items(), 
                                 key=lambda x: self.field_priority.get(x[0], 999))
            primary_value = sorted_fields[0][1]
            return primary_value, values_by_field, False
        
        # There are truly different values - this is a real conflict
        # Use priority to select primary value
        sorted_fields = sorted(values_by_field.items(), 
                             key=lambda x: self.field_priority.get(x[0], 999))
        
        primary_value = sorted_fields[0][1]
        origin_info = dict(values_by_field)
        
        return primary_value, origin_info, True

    def process_single_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single product details file with conflict detection during processing."""
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
        
        # Collect all keys and their values with normalized keys
        key_values = defaultdict(dict)
        
        # Process structured fields (overview, details_table, technical_details)
        for field in ['overview', 'details_table', 'technical_details']:
            for item in field_data.get(field, []):
                if isinstance(item, dict) and 'name' in item and 'value' in item:
                    original_key = item['name'].strip()
                    normalized_key = self.merger.normalize_column_name(original_key)
                    value = item['value'].strip()
                    key_values[normalized_key][field] = value
        
        # Process variant_info
        for variant_info in field_data.get('variant_info', []):
            if isinstance(variant_info, str):
                # Extract gauge and conductor info from variant strings
                gauge_match = re.search(r'(\d+)\s*AWG', variant_info, re.IGNORECASE)
                conductor_match = re.search(r'(\d+)C', variant_info, re.IGNORECASE)
                
                if gauge_match:
                    key_values['gauge']['variant_info'] = gauge_match.group(0)  # Preserve full match
                if conductor_match:
                    key_values['conductor_count']['variant_info'] = conductor_match.group(0)
        
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
                    key_values['gauge']['variants'] = gauge_match.group(0)
        
        # Detect conflicts and add to result
        for key, values_by_field in list(key_values.items()):
            primary_value, origin_info, has_conflict = self.detect_conflicts(values_by_field)
            
            # Add primary value
            if has_conflict:
                result[key] = f"{CONFLICT_MARKER} {primary_value}"
                self.extraction_stats['conflicts_found'] += 1
            else:
                result[key] = primary_value
            
            # Add origin information
            result[f'{key}_origin'] = origin_info
        
        return result

    def merge_similar_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge similar columns using intelligent heuristics - only schema unification, no conflict detection."""
        
        columns = df.columns.tolist()
        data_columns = [col for col in columns if not col.endswith('_origin') and col not in ['asin', 'name', 'brand', 'price', 'rating', 'total_ratings', 'file_source']]
        
        # Find similar columns
        merge_groups = []
        processed = set()
        
        for i, col1 in enumerate(data_columns):
            if col1 in processed:
                continue
                
            similar_cols = [col1]
            
            for col2 in data_columns[i+1:]:
                if col2 in processed:
                    continue
                    
                should_merge, reason = self.merger.should_merge_columns(col1, col2, df)
                
                if should_merge:
                    similar_cols.append(col2)
                    processed.add(col2)
                    self.extraction_stats['semantic_matches'] += 1
                    logging.info(f"Semantic match found: {col1} ~ {col2} ({reason})")
            
            if len(similar_cols) > 1:
                merge_groups.append(similar_cols)
                processed.add(col1)
        
        # Merge columns in each group
        for group in merge_groups:
            if len(group) > 1:
                primary_col = group[0]
                merged_col = primary_col
                
                # Merge values from all columns in the group
                for col in group[1:]:
                    if col in df.columns:
                        # Merge values row by row - only combine non-null values
                        for idx in df.index:
                            val1 = df.at[idx, primary_col]
                            val2 = df.at[idx, col]
                            
                            # If primary column is empty and secondary has data, use secondary
                            if pd.isna(val1) and pd.notna(val2):
                                df.at[idx, primary_col] = val2
                            
                            # Merge origin data
                            origin_col1 = f"{primary_col}_origin"
                            origin_col2 = f"{col}_origin"
                            
                            if origin_col1 in df.columns and origin_col2 in df.columns:
                                origin1 = df.at[idx, origin_col1]
                                origin2 = df.at[idx, origin_col2]
                                
                                # Merge origin dictionaries
                                if pd.notna(origin1) and pd.notna(origin2):
                                    try:
                                        if isinstance(origin1, str):
                                            origin1_dict = eval(origin1)
                                        else:
                                            origin1_dict = origin1
                                        
                                        if isinstance(origin2, str):
                                            origin2_dict = eval(origin2)
                                        else:
                                            origin2_dict = origin2
                                        
                                        # Merge the dictionaries
                                        merged_origin = {**origin1_dict, **origin2_dict}
                                        df.at[idx, origin_col1] = str(merged_origin)
                                    except:
                                        # If parsing fails, keep the primary origin
                                        pass
                                elif pd.notna(origin2):
                                    # If only origin2 has data, use it
                                    df.at[idx, origin_col1] = origin2
                        
                        # Drop the merged column
                        df = df.drop(columns=[col])
                        
                        # Also drop corresponding origin column if it exists
                        origin_col = f"{col}_origin"
                        if origin_col in df.columns:
                            df = df.drop(columns=[origin_col])
                
                self.extraction_stats['columns_merged'] += len(group) - 1
                logging.info(f"Merged columns: {group} -> {merged_col}")
        
        return df

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
        
        # Merge similar columns (schema unification only)
        logging.info("Merging similar columns for schema unification...")
        df = self.merge_similar_columns(df)
        
        # Reorder columns
        column_order = ['asin', 'name', 'brand', 'price', 'rating', 'total_ratings', 'file_source']
        data_columns = [col for col in df.columns if not col.endswith('_origin') and col not in column_order]
        data_columns.sort()
        
        final_order = column_order.copy()
        for data_col in data_columns:
            final_order.append(data_col)
            origin_col = f"{data_col}_origin"
            if origin_col in df.columns:
                final_order.append(origin_col)
        
        df = df.reindex(columns=final_order)
        
        return df

    def generate_reports(self, df: pd.DataFrame, output_dir: str = '.'):
        """Generate comprehensive reports."""
        
        # Save main CSV
        csv_path = os.path.join(output_dir, 'extracted_product_details_v5.csv')
        df.to_csv(csv_path, index=False)
        logging.info(f"Main CSV saved to: {csv_path}")
        
        # Generate conflict report
        conflict_report = {
            'total_conflicts': self.extraction_stats['conflicts_found'],
            'columns_merged': self.extraction_stats['columns_merged'],
            'semantic_matches': self.extraction_stats['semantic_matches'],
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
        conflict_path = os.path.join(output_dir, 'conflict_report_v5.json')
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
            'columns_merged': self.extraction_stats['columns_merged'],
            'semantic_matches': self.extraction_stats['semantic_matches']
        }
        
        # Save statistics
        stats_path = os.path.join(output_dir, 'extraction_statistics_v5.json')
        with open(stats_path, 'w') as f:
            json.dump(stats_report, f, indent=2)
        logging.info(f"Extraction statistics saved to: {stats_path}")

def main():
    """Main function to run the extraction process."""
    current_dir = os.getcwd()
    
    logging.info("Starting V5 product details extraction with proper conflict detection...")
    
    # Initialize extractor
    extractor = ProductDetailsExtractorV5()
    
    # Extract all files
    logging.info("Extracting data from all files...")
    df = extractor.extract_all_files(current_dir)
    
    # Generate reports
    logging.info("Generating reports...")
    extractor.generate_reports(df)
    
    logging.info("Extraction completed successfully!")
    logging.info(f"Processed {extractor.extraction_stats['files_processed']} files")
    logging.info(f"Found {extractor.extraction_stats['conflicts_found']} conflicts")
    logging.info(f"Merged {extractor.extraction_stats['columns_merged']} columns")
    logging.info(f"Found {extractor.extraction_stats['semantic_matches']} semantic matches")
    logging.info(f"Generated {len(df.columns)} columns")

if __name__ == "__main__":
    main() 