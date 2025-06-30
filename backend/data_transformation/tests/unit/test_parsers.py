#!/usr/bin/env python3
"""
Unit tests for data transformation parsers.

测试各种解析器的功能：
- SalesVolumeParser: 销量文本解析
- PackParser: 包装数量解析
- PriceCalculator: 价格计算和转换
"""

import unittest
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from data_transformation.parsers import SalesVolumeParser, PackParser, PriceCalculator
from decimal import Decimal


class TestSalesVolumeParser(unittest.TestCase):
    """Test sales volume parser functionality."""
    
    def test_k_format_parsing(self):
        """Test parsing of K format sales volumes."""
        test_cases = [
            ("20K+ bought in past month", 20000),
            ("1.5K bought in past month", 1500),
            ("2.7K+ bought in past month", 2700),
            ("3K bought", 3000),
            ("500+ bought in past month", 500),
            ("10+ bought", 10),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = SalesVolumeParser.parse(text)
                self.assertEqual(result, expected, f"Failed to parse '{text}'")
    
    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        invalid_cases = [
            None,
            "",
            "No sales data",
            "Recently viewed",
        ]
        
        for text in invalid_cases:
            with self.subTest(text=text):
                result = SalesVolumeParser.parse(text)
                self.assertEqual(result, 0, f"Should return 0 for '{text}'")


class TestPackParser(unittest.TestCase):
    """Test pack parser functionality."""
    
    def test_pack_count_detection(self):
        """Test detection of pack counts in product titles."""
        test_cases = [
            ("[50 Pack] Light Switch", 50),
            ("(12 Pack) Outlet Cover", 12),
            ("24-Pack Screws", 24),
            ("Pack Of 10 Wall Plates", 10),
            ("6 Pack Switch Plates", 6),
            ("Count of 12 Switches", 12),
            ("Set of 4 Dimmers", 4),
            ("Single Light Switch", 1),  # Default case
        ]
        
        for title, expected in test_cases:
            with self.subTest(title=title):
                result = PackParser.parse_pack_count(title)
                self.assertEqual(result, expected, f"Failed to parse pack count from '{title}'")
    
    def test_base_product_name_extraction(self):
        """Test extraction of base product names."""
        test_cases = [
            ("[50 Pack] Light Switch Cover", "Light Switch Cover"),
            ("(12-Pack) Outlet Plates White", "Outlet Plates White"),
            ("24 Pack Wall Switch - White", "Wall Switch - White"),
            ("Regular Switch", "Regular Switch"),  # No pack info
        ]
        
        for title, expected in test_cases:
            with self.subTest(title=title):
                result = PackParser.extract_base_product_name(title)
                self.assertEqual(result, expected, f"Failed to extract base name from '{title}'")


class TestPriceCalculator(unittest.TestCase):
    """Test price calculator functionality."""
    
    def test_decimal_conversion(self):
        """Test safe decimal conversion."""
        test_cases = [
            ("19.99", Decimal("19.99")),
            (19.99, Decimal("19.99")),
            (None, None),
            ("", None),
            ("invalid", None),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                result = PriceCalculator.safe_decimal_conversion(input_val)
                self.assertEqual(result, expected, f"Failed to convert '{input_val}'")
    
    def test_revenue_calculation(self):
        """Test estimated revenue calculation."""
        test_cases = [
            (Decimal("19.99"), 1000, Decimal("19990.00")),
            (Decimal("25.50"), 500, Decimal("12750.00")),
            (None, 1000, None),
            (Decimal("10.00"), 0, None),
        ]
        
        for price, volume, expected in test_cases:
            with self.subTest(price=price, volume=volume):
                result = PriceCalculator.calculate_estimated_revenue(price, volume)
                self.assertEqual(result, expected, f"Failed to calculate revenue for price={price}, volume={volume}")
    
    def test_list_price_estimation(self):
        """Test list price estimation for pack products."""
        test_cases = [
            # (price, pack_count, title, expected_list_price, expected_unit_price)
            (Decimal("19.99"), 1, "Single Switch", Decimal("19.99"), Decimal("19.99")),
            (Decimal("50.00"), 10, "[10 Pack] Switches", Decimal("5.00"), Decimal("5.00")),
            (Decimal("24.99"), 6, "6-Pack Outlets", Decimal("4.17"), Decimal("4.17")),
        ]
        
        for price, pack_count, title, expected_list, expected_unit in test_cases:
            with self.subTest(price=price, pack_count=pack_count):
                list_price, unit_price = PriceCalculator.estimate_list_price(price, pack_count, title)
                self.assertAlmostEqual(float(list_price), float(expected_list), places=2)
                self.assertAlmostEqual(float(unit_price), float(expected_unit), places=2)


if __name__ == "__main__":
    unittest.main() 