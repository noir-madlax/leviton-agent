"""
Test suite for ProjectService functionality, specifically terminal category grouping.

Tests verify that products are correctly grouped by their terminal categories
before segmentation, ensuring proper separation of product types.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from typing import List, Dict, Any

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from projects.services.project_service import ProjectService


class TestProjectServiceCategoryGrouping(unittest.TestCase):
    """Test category path grouping functionality in ProjectService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ProjectService()
        
        # Mock Supabase client
        self.mock_supabase = Mock()
        self.service.supabase = self.mock_supabase
    
    async def test_group_products_by_category_path_sql_success(self):
        """Test successful grouping of products by category paths using SQL."""
        # Arrange: Mock product data with different terminal categories
        mock_product_data = [
            {
                'platform_id': 'P001',
                'categories_flat': 'Home & Kitchen > Electrical > Wall Switches > Dimmer Switches',
                'category_deepest_level': 4,
                'category_l4_id': '507840',
                'category_l3_id': '6291358011',
                'category_l2_id': '123456',
                'category_l1_id': '654321',
                'category_id': '111111'
            },
            {
                'platform_id': 'P002', 
                'categories_flat': 'Home & Kitchen > Electrical > Wall Switches > Dimmer Switches',
                'category_deepest_level': 4,
                'category_l4_id': '507840',
                'category_l3_id': '6291358011',
                'category_l2_id': '123456',
                'category_l1_id': '654321',
                'category_id': '111111'
            },
            {
                'platform_id': 'P003',
                'categories_flat': 'Home & Kitchen > Electrical > Wall Switches > Light Switches',
                'category_deepest_level': 4,
                'category_l4_id': '6291359011',
                'category_l3_id': '6291358011',
                'category_l2_id': '123456',
                'category_l1_id': '654321',
                'category_id': '111111'
            },
            {
                'platform_id': 'P004',
                'categories_flat': 'Home & Kitchen > Electrical > Wall Switches > Timer Switches',
                'category_deepest_level': 4,
                'category_l4_id': '6291360011',
                'category_l3_id': '6291358011',
                'category_l2_id': '123456',
                'category_l1_id': '654321',
                'category_id': '111111'
            },
            {
                'platform_id': 'P005',
                'categories_flat': 'Home & Kitchen > Electrical > Wall Switches > Light Switches',
                'category_deepest_level': 4,
                'category_l4_id': '6291359011',
                'category_l3_id': '6291358011',
                'category_l2_id': '123456',
                'category_l1_id': '654321',
                'category_id': '111111'
            }
        ]
        
        # Mock Supabase table query chain
        mock_result = Mock()
        mock_result.data = mock_product_data
        
        mock_table = Mock()
        mock_table.select.return_value.in_.return_value.execute.return_value = mock_result
        self.mock_supabase.table.return_value = mock_table
        
        # Act: Call the method under test
        product_ids = ['P001', 'P002', 'P003', 'P004', 'P005']
        result = await self.service._group_products_by_category_path_sql(product_ids)
        
        # Assert: Verify correct grouping by full category path
        expected_groups = {
            'Home & Kitchen > Electrical > Wall Switches > Dimmer Switches': ['P001', 'P002'],
            'Home & Kitchen > Electrical > Wall Switches > Light Switches': ['P003', 'P005'], 
            'Home & Kitchen > Electrical > Wall Switches > Timer Switches': ['P004']
        }
        
        self.assertEqual(len(result), 3)
        self.assertIn('Home & Kitchen > Electrical > Wall Switches > Dimmer Switches', result)
        self.assertIn('Home & Kitchen > Electrical > Wall Switches > Light Switches', result)
        self.assertIn('Home & Kitchen > Electrical > Wall Switches > Timer Switches', result)
        
        # Verify product assignments
        self.assertCountEqual(result['Home & Kitchen > Electrical > Wall Switches > Dimmer Switches'], expected_groups['Home & Kitchen > Electrical > Wall Switches > Dimmer Switches'])
        self.assertCountEqual(result['Home & Kitchen > Electrical > Wall Switches > Light Switches'], expected_groups['Home & Kitchen > Electrical > Wall Switches > Light Switches'])
        self.assertCountEqual(result['Home & Kitchen > Electrical > Wall Switches > Timer Switches'], expected_groups['Home & Kitchen > Electrical > Wall Switches > Timer Switches'])
    
    async def test_group_products_by_category_path_sql_empty_input(self):
        """Test handling of empty product ID list."""
        # Act
        result = await self.service._group_products_by_category_path_sql([])
        
        # Assert
        self.assertEqual(result, {})
    
    async def test_group_products_by_category_path_sql_no_categories_flat(self):
        """Test handling of products with missing categories_flat."""
        # Arrange: Mock product data with missing categories_flat
        mock_product_data = [
            {
                'platform_id': 'P001',
                'categories_flat': None,
                'category_deepest_level': 0,
                'category_id': '111111'
            },
            {
                'platform_id': 'P002',
                'categories_flat': '',
                'category_deepest_level': 0,
                'category_id': '222222'
            }
        ]
        
        # Mock Supabase response
        mock_result = Mock()
        mock_result.data = mock_product_data
        
        mock_table = Mock()
        mock_table.select.return_value.in_.return_value.execute.return_value = mock_result
        self.mock_supabase.table.return_value = mock_table
        
        # Act
        result = await self.service._group_products_by_category_path_sql(['P001', 'P002'])
        
        # Assert: Should return empty groups since no valid categories
        self.assertEqual(result, {})
    
    async def test_group_products_by_category_path_sql_various_depths(self):
        """Test products with different category depths."""
        # Arrange: Products with different category hierarchy depths
        mock_product_data = [
            {
                'platform_id': 'P001',
                'categories_flat': 'Electronics > Switches > Smart Switches > WiFi Dimmer > Advanced',
                'category_deepest_level': 5,
                'category_l5_id': 'WIFI001',
                'category_l4_id': '507840',
                'category_l3_id': '6291358011',
                'category_l2_id': '123456',
                'category_l1_id': '654321',
                'category_id': '111111'
            },
            {
                'platform_id': 'P002',
                'categories_flat': 'Electronics > Basic Switch',
                'category_deepest_level': 2,
                'category_l2_id': 'BASIC001',
                'category_l1_id': '654321',
                'category_id': '111111'
            },
            {
                'platform_id': 'P003',
                'categories_flat': 'Single Category',
                'category_deepest_level': 1,
                'category_l1_id': 'SINGLE001',
                'category_id': '111111'
            }
        ]
        
        # Mock Supabase response
        mock_result = Mock()
        mock_result.data = mock_product_data
        
        mock_table = Mock()
        mock_table.select.return_value.in_.return_value.execute.return_value = mock_result
        self.mock_supabase.table.return_value = mock_table
        
        # Act
        result = await self.service._group_products_by_category_path_sql(['P001', 'P002', 'P003'])
        
        # Assert: Each product should be grouped by its full category path
        expected_groups = {
            'Electronics > Switches > Smart Switches > WiFi Dimmer > Advanced': ['P001'],
            'Electronics > Basic Switch': ['P002'],
            'Single Category': ['P003']
        }
        
        self.assertEqual(len(result), 3)
        for full_category_path, product_ids in expected_groups.items():
            self.assertIn(full_category_path, result)
            self.assertCountEqual(result[full_category_path], product_ids)
    
    async def test_group_products_by_category_path_sql_database_error(self):
        """Test handling of database errors."""
        # Arrange: Mock database error
        mock_table = Mock()
        mock_table.select.return_value.in_.return_value.execute.side_effect = Exception("Database connection error")
        self.mock_supabase.table.return_value = mock_table
        
        # Act
        result = await self.service._group_products_by_category_path_sql(['P001', 'P002'])
        
        # Assert: Should fallback to returning all products as "Unknown Category"
        expected_fallback = {"Unknown Category": ['P001', 'P002']}
        self.assertEqual(result, expected_fallback)
    
    async def test_group_products_by_category_path_direct_sql(self):
        """Test the main method using direct SQL implementation."""
        # Arrange: Mock successful SQL response
        mock_product_data = [
            {
                'platform_id': 'P001',
                'categories_flat': 'Home > Switches > Dimmer Switches'
            }
        ]
        
        mock_table_result = Mock()
        mock_table_result.data = mock_product_data
        
        mock_table = Mock()
        mock_table.select.return_value.in_.return_value.execute.return_value = mock_table_result
        self.mock_supabase.table.return_value = mock_table
        
        # Act
        result = await self.service._group_products_by_category_path(['P001'], "Wall Switches")
        
        # Assert: Should group correctly using SQL
        expected = {'Home > Switches > Dimmer Switches': ['P001']}
        self.assertEqual(result, expected)
        
        # Verify SQL query was called
        self.mock_supabase.table.assert_called_with('product_wide_table')
    
    async def test_real_world_category_data_grouping(self):
        """Test with real-world category data structure from Wall Switches example."""
        # Arrange: Use actual category data from the analysis
        mock_product_data = [
            # Dimmer Switches group
            {
                'platform_id': 'B001E9LP06',
                'categories_flat': 'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Dimmer Switches'
            },
            {
                'platform_id': 'B001E9LP07',
                'categories_flat': 'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Dimmer Switches'
            },
            # Light Switches group
            {
                'platform_id': 'B002ABC123',
                'categories_flat': 'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Light Switches'
            },
            # Timer Switches group  
            {
                'platform_id': 'B003DEF456',
                'categories_flat': 'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Timer Switches'
            },
            # Motion-Activated Switches group
            {
                'platform_id': 'B004GHI789',
                'categories_flat': 'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Motion-Activated Switches'
            }
        ]
        
        # Mock Supabase response
        mock_result = Mock()
        mock_result.data = mock_product_data
        
        mock_table = Mock()
        mock_table.select.return_value.in_.return_value.execute.return_value = mock_result
        self.mock_supabase.table.return_value = mock_table
        
        # Act
        product_ids = ['B001E9LP06', 'B001E9LP07', 'B002ABC123', 'B003DEF456', 'B004GHI789']
        result = await self.service._group_products_by_category_path_sql(product_ids)
        
        # Assert: Should match the 4 category paths identified in analysis
        expected_groups = {
            'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Dimmer Switches': ['B001E9LP06', 'B001E9LP07'],
            'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Light Switches': ['B002ABC123'],
            'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Timer Switches': ['B003DEF456'],
            'Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Motion-Activated Switches': ['B004GHI789']
        }
        
        self.assertEqual(len(result), 4)
        for full_category_path, expected_products in expected_groups.items():
            self.assertIn(full_category_path, result)
            self.assertCountEqual(result[full_category_path], expected_products)
        
        # Verify all products are accounted for
        all_grouped_products = []
        for products in result.values():
            all_grouped_products.extend(products)
        self.assertCountEqual(all_grouped_products, product_ids)

    def test_extract_terminal_category(self):
        """Test terminal category extraction from full category paths."""
        # Test normal cases
        self.assertEqual(
            self.service._extract_terminal_category('Home > Electronics > Switches > Dimmer Switches'),
            'Dimmer Switches'
        )
        
        self.assertEqual(
            self.service._extract_terminal_category('Tools & Home Improvement > Electrical > Wiring & Connecting > Wall Switches & Dimmers > Timer Switches'),
            'Timer Switches'
        )
        
        # Test single category
        self.assertEqual(
            self.service._extract_terminal_category('Single Category'),
            'Single Category'
        )
        
        # Test edge cases
        self.assertEqual(
            self.service._extract_terminal_category(''),
            'Unknown Category'
        )
        
        self.assertEqual(
            self.service._extract_terminal_category(None),
            'Unknown Category'
        )
        
        self.assertEqual(
            self.service._extract_terminal_category('   '),
            'Unknown Category'
        )
        
        # Test with extra spaces
        self.assertEqual(
            self.service._extract_terminal_category('  Home  >  Electronics  >  Switches  '),
            'Switches'
        )


if __name__ == '__main__':
    # Setup for running tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    unittest.main() 