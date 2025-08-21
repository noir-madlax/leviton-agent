#!/usr/bin/env python3
"""
Test script to check value normalization and identify false positives.
"""

import re
import nltk
from nltk.stem import PorterStemmer
from difflib import SequenceMatcher
import pandas as pd

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

def test_normalization():
    """Test the normalization with known false positives."""
    
    normalizer = ValueNormalizer()
    
    print("Testing Value Normalization")
    print("=" * 50)
    
    # Test cases from the conflicts
    test_cases = [
        # Material conflicts
        ("24AWGPVCSolidWire", "24 AWG PVC Solid Wire"),
        ("AlloySteel,Plastic", "Alloy Steel, Plastic"),
        ("PolyvinylChloride", "Polyvinyl Chloride"),
        
        # Wire/Gauge conflicts
        ("10AWG", "10 AWG"),
        ("22AWG", "14AWG"),  # This should be a real conflict
        
        # Conductor conflicts
        ("4 Conductor", "5 conductor"),
        ("4 Conductor", "3C"),
    ]
    
    for val1, val2 in test_cases:
        norm1 = normalizer.normalize_value(val1)
        norm2 = normalizer.normalize_value(val2)
        equivalent = normalizer.are_values_equivalent(val1, val2)
        
        print(f"\n🔍 Testing: '{val1}' vs '{val2}'")
        print(f"   Normalized 1: '{norm1}'")
        print(f"   Normalized 2: '{norm2}'")
        print(f"   Equivalent: {equivalent}")
        print(f"   Should be conflict: {not equivalent}")

def test_improved_normalization():
    """Test with improved normalization rules."""
    
    print("\n" + "=" * 50)
    print("Testing Improved Normalization")
    print("=" * 50)
    
    # Improved normalization function
    def improved_normalize(value: str) -> str:
        if not isinstance(value, str):
            value = str(value)
        
        # Convert to lowercase
        normalized = value.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation but keep some
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Handle specific format differences
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
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    # Test cases
    test_cases = [
        ("24AWGPVCSolidWire", "24 AWG PVC Solid Wire"),
        ("AlloySteel,Plastic", "Alloy Steel, Plastic"),
        ("PolyvinylChloride", "Polyvinyl Chloride"),
        ("10AWG", "10 AWG"),
        ("22AWG", "14AWG"),
        ("4 Conductor", "5 conductor"),
        ("4 Conductor", "3C"),
    ]
    
    for val1, val2 in test_cases:
        norm1 = improved_normalize(val1)
        norm2 = improved_normalize(val2)
        equivalent = norm1 == norm2
        
        print(f"\n🔍 Testing: '{val1}' vs '{val2}'")
        print(f"   Normalized 1: '{norm1}'")
        print(f"   Normalized 2: '{norm2}'")
        print(f"   Equivalent: {equivalent}")
        print(f"   Should be conflict: {not equivalent}")

if __name__ == "__main__":
    test_normalization()
    test_improved_normalization() 