#!/usr/bin/env python3
"""
V7: Enhanced product details extraction with improved data capture.
Key improvements:
- Enhanced product name parsing for specifications
- Improved features extraction with better regex patterns
- Variant size extraction
- Better handling of technical specifications
- More comprehensive regex patterns for electrical products
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
        logging.FileHandler('extraction_log_v7.txt'),
        logging.StreamHandler()
    ]
)

class EnhancedValueNormalizer:
    """Enhanced value normalizer with improved format handling."""
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        
        # Enhanced unit patterns for numerical values
        self.unit_patterns = {
            'voltage': r'(\d+(?:\.\d+)?)\s*(V|Volts?|volts?)',
            'current': r'(\d+(?:\.\d+)?)\s*(A|Amps?|amps?)',
            'temperature': r'(\d+(?:\.\d+)?)\s*(°C|°F|Celsius|Fahrenheit|C|F)',
            'length': r'(\d+(?:\.\d+)?)\s*(ft|feet|m|meters?|cm|centimeters?|inches?)',
            'weight': r'(\d+(?:\.\d+)?)\s*(oz|ounces?|g|grams?|kg|kilograms?|lbs?|pounds?)',
            'gauge': r'(\d+(?:\.\d+)?)\s*(AWG|awg|gauge)',
        }

    def normalize_value(self, value: str) -> str:
        """Normalize a value for comparison with improved format handling."""
        if not isinstance(value, str):
            value = str(value)
        
        # Convert to lowercase
        normalized = value.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Handle specific format differences before removing punctuation
        # Replace common punctuation with spaces to preserve word boundaries
        normalized = re.sub(r'[,.]', ' ', normalized)
        
        # Handle specific abbreviations and variations
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
            'polyvinyl chloride': 'pvc',
            'tinned': 'tin',
            'galvanized': 'galv',
            'flame retardant': 'flameretardant',
            'single strand': 'singlestrand',
            'multi strand': 'multistrand',
            'stranded': 'strand',
            'solid': 'solid',
            'alloy steel': 'alloysteel',
            'alloysteel': 'alloysteel',
            'plastic': 'plastic',
            'conductor': 'conductor',
            'conductors': 'conductor',
            'steel': 'steel',
            'copper': 'copper',
            'aluminum': 'aluminum',
            'aluminium': 'aluminum',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove remaining punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
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
        
        # Check semantic similarity for close matches
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity > 0.95  # Higher threshold for more strict matching

class EnhancedProductNameParser:
    """Enhanced parser for extracting specifications from product names."""
    
    def __init__(self):
        # Patterns for extracting specifications from product names
        self.name_patterns = {
            # Gauge/Conductor patterns: "8/2", "12/3", "18/4"
            'gauge_conductor': r'(\d+)/(\d+)\s*(?:AWG|awg|gauge)?',
            
            # Gauge patterns: "18AWG", "22 Gauge", "12 gauge"
            'gauge': r'(\d+)\s*(?:AWG|awg|gauge)',
            
            # Length patterns: "25Ft Cut", "100FT", "50m"
            'length': r'(\d+(?:\.\d+)?)\s*(?:ft|feet|FT|Ft|m|meter|M)\s*(?:cut|Cut)?',
            
            # Conductor patterns: "4 Conductor", "2C", "3C"
            'conductor': r'(\d+)\s*(?:conductor|conductors?|C)',
            
            # Voltage patterns: "300V", "12v", "24V"
            'voltage': r'(\d+(?:\.\d+)?)\s*(?:V|v|Volts?|volts?)',
            
            # Temperature patterns: "392°F", "200°C"
            'temperature': r'(\d+(?:\.\d+)?)\s*(?:°F|°C|F|C)',
            
            # Material patterns: "Copper", "Aluminum", "PVC"
            'material': r'\b(Copper|Aluminum|Aluminium|Steel|PVC|Silicone|Tinned\s+Copper|Galvanized)\b',
            
            # Color patterns: "Black", "Red", "White"
            'color': r'\b(Black|Red|Yellow|White|Green|Blue|Brown|Orange|Purple|Gray|Silver|Gold)\b',
        }
    
    def extract_from_product_name(self, product_name: str) -> Dict[str, Any]:
        """Extract specifications from product name."""
        extracted_data = {}
        
        if not product_name:
            return extracted_data
        
        # Extract gauge/conductor combination (e.g., "8/2" -> gauge=8, conductor=2)
        gauge_conductor_match = re.search(self.name_patterns['gauge_conductor'], product_name, re.IGNORECASE)
        if gauge_conductor_match:
            gauge = gauge_conductor_match.group(1)
            conductor = gauge_conductor_match.group(2)
            extracted_data['gauge'] = f"{gauge}AWG"
            extracted_data['conductor_count'] = conductor
        
        # Extract individual gauge if not already found
        if 'gauge' not in extracted_data:
            gauge_match = re.search(self.name_patterns['gauge'], product_name, re.IGNORECASE)
            if gauge_match:
                extracted_data['gauge'] = f"{gauge_match.group(1)}AWG"
        
        # Extract conductor count if not already found
        if 'conductor_count' not in extracted_data:
            conductor_match = re.search(self.name_patterns['conductor'], product_name, re.IGNORECASE)
            if conductor_match:
                extracted_data['conductor_count'] = conductor_match.group(1)
        
        # Extract length
        length_match = re.search(self.name_patterns['length'], product_name, re.IGNORECASE)
        if length_match:
            length_value = length_match.group(1)
            # Determine unit from context
            if 'ft' in product_name.lower() or 'feet' in product_name.lower():
                extracted_data['length'] = f"{length_value} ft"
            elif 'm' in product_name.lower() or 'meter' in product_name.lower():
                extracted_data['length'] = f"{length_value} m"
        
        # Extract voltage
        voltage_match = re.search(self.name_patterns['voltage'], product_name, re.IGNORECASE)
        if voltage_match:
            extracted_data['voltage'] = f"{voltage_match.group(1)}V"
        
        # Extract temperature
        temp_match = re.search(self.name_patterns['temperature'], product_name, re.IGNORECASE)
        if temp_match:
            temp_value = temp_match.group(1)
            if '°F' in product_name or 'F' in product_name:
                extracted_data['temperature'] = f"{temp_value}°F"
            elif '°C' in product_name or 'C' in product_name:
                extracted_data['temperature'] = f"{temp_value}°C"
        
        # Extract material
        material_match = re.search(self.name_patterns['material'], product_name, re.IGNORECASE)
        if material_match:
            extracted_data['material'] = material_match.group(1)
        
        # Extract color
        color_match = re.search(self.name_patterns['color'], product_name, re.IGNORECASE)
        if color_match:
            extracted_data['color'] = color_match.group(1)
        
        return extracted_data

class EnhancedRegexExtractor:
    """Enhanced regex extractor with improved patterns for electrical products."""
    
    def __init__(self):
        # Enhanced regex patterns for extracting specifications
        self.regex_patterns = {
            # Enhanced voltage patterns
            'voltage': [
                r'\b(\d+(?:\.\d+)?)\s*(?:V|Volts?|volts?)\b',
                r'\b(\d+(?:\.\d+)?)\s*(?:V|Volts?)\s*(?:rated?|rating)\b',
                r'\b(\d+(?:\.\d+)?)\s*(?:V|Volts?)\s*(?:max|maximum)\b',
                r'rated\s+for\s+(\d+(?:\.\d+)?)\s*(?:V|Volts?)',
            ],
            
            # Enhanced current patterns
            'current': [
                r'\b(\d+(?:\.\d+)?)\s*(?:A|Amps?|amps?)\b',
                r'rated\s+for\s+(\d+(?:\.\d+)?)\s*(?:A|Amps?)',
                r'thhn\s+ampere\s+rating:\s*rated\s+for\s+(\d+(?:\.\d+)?)\s*(?:A|Amps?)',
            ],
            
            # Enhanced temperature patterns
            'temperature': [
                r'\b(-?\d+(?:\.\d+)?)\s*(?:°C|°F|Celsius|Fahrenheit)\b',
                r'\b(\d+(?:\.\d+)?)\s*(?:°F|°C)\s*(?:high-temperature|high\s+temp)',
                r'temperature\s+rating:\s*(\d+(?:\.\d+)?)\s*(?:°F|°C)',
            ],
            
            # Enhanced length patterns
            'length': [
                r'\b(\d+(?:\.\d+)?)\s*(?:ft|feet|m|meters?|cm|centimeters?)\b',
                r'(\d+(?:\.\d+)?)\s*(?:ft|feet|m|meter)\s*(?:cut|Cut)',
                r'length:\s*(\d+(?:\.\d+)?)\s*(?:ft|feet|m|meter)',
            ],
            
            # Enhanced gauge patterns
            'gauge': [
                r'\b(\d+(?:\.\d+)?)\s*(?:AWG|awg|gauge)\b',
                r'(\d+)\s*(?:AWG|awg|gauge)\s*(?:wire|cable)',
                r'gauge:\s*(\d+(?:\.\d+)?)\s*(?:AWG|awg)',
            ],
            
            # Enhanced conductor patterns
            'conductor': [
                r'\b(\d+)\s*(?:conductor|conductors?)\b',
                r'(\d+)C\b',  # e.g., "3C", "4C"
                r'(\d+)\s*(?:strand|strands?)\s*(?:copper|conductor)',
            ],
            
            # Enhanced wire count patterns
            'wire_count': [
                r'\b(\d+)\s*(?:wire|wires?)\b',
                r'(\d+)\s*(?:wire|wires?)\s*(?:pack|bundle)',
            ],
            
            # Enhanced package weight patterns
            'package_weight': [
                r'\b(\d+(?:\.\d+)?)\s*(?:oz|ounces?|g|grams?|kg|kilograms?)\b',
                r'package\s+weight:\s*(\d+(?:\.\d+)?)\s*(?:oz|ounces?|g|grams?|kg|kilograms?)',
            ],
            
            # Enhanced dimensions patterns
            'dimensions': [
                r'\b(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:inches?|cm|mm)\b',
                r'package\s*dimensions:\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)',
            ],
            
            # Enhanced material patterns
            'material': [
                r'\b(Copper|Aluminum|Steel|PVC|Silicone|Tinned\s+Copper|Galvanized|Polyvinyl\s+Chloride)\b',
                r'material:\s*(Copper|Aluminum|Steel|PVC|Silicone)',
            ],
            
            # Enhanced color patterns
            'color': [
                r'\b(Black|Red|Yellow|White|Green|Blue|Brown|Orange|Purple|Gray|Silver|Gold)\b',
                r'color:\s*(Black|Red|Yellow|White|Green|Blue|Brown|Orange|Purple|Gray|Silver|Gold)',
            ],
            
            # Enhanced certification patterns
            'certification': [
                r'\b(UL|CSA|CE|RoHS|VW-1|FT1|Flame\s+Retardant)\b',
                r'meets\s+(UL|CSA|CE|RoHS)\s+standards?',
                r'ul\s+(\d+)',  # UL numbers
            ],
            
            # Enhanced temperature range patterns
            'temperature_range': [
                r'\b(-?\d+(?:\.\d+)?)\s*(?:°C|°F)\s*to\s*(-?\d+(?:\.\d+)?)\s*(?:°C|°F)\b',
                r'temperature\s+range:\s*(-?\d+(?:\.\d+)?)\s*(?:°C|°F)\s*to\s*(-?\d+(?:\.\d+)?)\s*(?:°C|°F)',
            ],
            
            # Enhanced variant patterns
            'variant_gauge_conductor': [
                r'(\d+)\s*AWG-(\d+)C',
                r'(\d+)/(\d+)\s*(?:AWG|awg)',
            ],
            
            'variant_size': [
                r'(\d+(?:\.\d+)?)\s*(?:FT|ft|M|m)\s*(?:cut|Cut)',
                r'(\d+(?:\.\d+)?)\s*(?:ft|feet|m|meter)',
            ],
        }
    
    def extract_enhanced_data(self, text_list: List[str], field_name: str) -> Dict[str, Any]:
        """Extract data using enhanced regex patterns from text."""
        extracted_data = {}
        origin_info = {}
        
        for text in text_list:
            if not isinstance(text, str):
                continue
                
            for pattern_name, patterns in self.regex_patterns.items():
                if pattern_name not in extracted_data:
                    extracted_data[pattern_name] = []
                    origin_info[pattern_name] = []
                
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
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

class ProductDetailsExtractorV7:
    def __init__(self):
        """Initialize the extractor with enhanced extraction capabilities."""
        self.merger = IntelligentColumnMerger()
        self.normalizer = EnhancedValueNormalizer()
        self.name_parser = EnhancedProductNameParser()
        self.regex_extractor = EnhancedRegexExtractor()
        
        # Field priority for conflict resolution
        self.field_priority = {
            'details_table': 1,
            'overview': 2,
            'technical_details': 3,
            'variant_info': 4,
            'from_the_manufacturer': 5,
            'features': 6,
            'product_name': 7  # Lowest priority for name-extracted data
        }
        
        self.extraction_stats = {
            'files_processed': 0,
            'conflicts_found': 0,
            'columns_merged': 0,
            'semantic_matches': 0,
            'name_extractions': 0,
            'enhanced_extractions': 0
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

    def detect_conflicts(self, values_by_field: Dict[str, Any]) -> Tuple[Any, Dict[str, Any], bool]:
        """Detect conflicts during ASIN processing with improved value normalization."""
        
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
        """Process a single product details file with enhanced extraction."""
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
        
        # Extract specifications from product name
        product_name = detail.get('name', '')
        name_extracted_data = self.name_parser.extract_from_product_name(product_name)
        if name_extracted_data:
            self.extraction_stats['name_extractions'] += 1
            logging.info(f"Extracted {len(name_extracted_data)} specifications from product name: {list(name_extracted_data.keys())}")
        
        # Extract field data
        field_data = self.extract_field_data(product_data)
        
        # Collect all keys and their values with normalized keys
        key_values = defaultdict(dict)
        
        # Add name-extracted data with lowest priority
        for key, value in name_extracted_data.items():
            normalized_key = self.merger.normalize_column_name(key)
            key_values[normalized_key]['product_name'] = value
        
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
        
        # Process manufacturer text with enhanced regex
        manufacturer_text = field_data.get('from_the_manufacturer', [])
        if manufacturer_text:
            regex_data, regex_origin = self.regex_extractor.extract_enhanced_data(manufacturer_text, 'from_the_manufacturer')
            for pattern_name, matches in regex_data.items():
                if matches:
                    key_values[pattern_name]['from_the_manufacturer'] = matches[0]
                    if pattern_name not in result:
                        result[f'{pattern_name}_origin'] = regex_origin[pattern_name]
        
        # Process features with enhanced regex
        features = field_data.get('features', [])
        if features:
            regex_data, regex_origin = self.regex_extractor.extract_enhanced_data(features, 'features')
            for pattern_name, matches in regex_data.items():
                if matches:
                    if pattern_name not in key_values:
                        key_values[pattern_name] = {}
                    key_values[pattern_name]['features'] = matches[0]
                    if pattern_name not in result:
                        result[f'{pattern_name}_origin'] = regex_origin[pattern_name]
        
        # Process variants with enhanced extraction
        for variant in field_data.get('variants', []):
            if isinstance(variant, dict) and 'name' in variant:
                variant_name = variant['name']
                
                # Extract specifications from variant names
                variant_extracted = self.name_parser.extract_from_product_name(variant_name)
                for key, value in variant_extracted.items():
                    normalized_key = self.merger.normalize_column_name(key)
                    if normalized_key not in key_values:
                        key_values[normalized_key] = {}
                    key_values[normalized_key]['variants'] = value
        
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
        csv_path = os.path.join(output_dir, 'extracted_product_details_v7.csv')
        df.to_csv(csv_path, index=False)
        logging.info(f"Main CSV saved to: {csv_path}")
        
        # Generate conflict report
        conflict_report = {
            'total_conflicts': self.extraction_stats['conflicts_found'],
            'columns_merged': self.extraction_stats['columns_merged'],
            'semantic_matches': self.extraction_stats['semantic_matches'],
            'name_extractions': self.extraction_stats['name_extractions'],
            'enhanced_extractions': self.extraction_stats['enhanced_extractions'],
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
        conflict_path = os.path.join(output_dir, 'conflict_report_v7.json')
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
            'semantic_matches': self.extraction_stats['semantic_matches'],
            'name_extractions': self.extraction_stats['name_extractions'],
            'enhanced_extractions': self.extraction_stats['enhanced_extractions']
        }
        
        # Save statistics
        stats_path = os.path.join(output_dir, 'extraction_statistics_v7.json')
        with open(stats_path, 'w') as f:
            json.dump(stats_report, f, indent=2)
        logging.info(f"Extraction statistics saved to: {stats_path}")

def main():
    """Main function to run the extraction process."""
    current_dir = os.getcwd()
    
    logging.info("Starting V7 product details extraction with enhanced data capture...")
    
    # Initialize extractor
    extractor = ProductDetailsExtractorV7()
    
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
    logging.info(f"Extracted {extractor.extraction_stats['name_extractions']} specifications from product names")
    logging.info(f"Generated {len(df.columns)} columns")

if __name__ == "__main__":
    main() 