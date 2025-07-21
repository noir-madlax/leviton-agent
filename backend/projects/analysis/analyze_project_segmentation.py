#!/usr/bin/env python3
"""
Script to analyze segmentation data for a specific project and export to CSV.

This script:
1. Finds all hashed project IDs (segmentation run groups) for a given project
2. Extracts all product segment assignments with product details
3. Exports the data to CSV with product titles, category paths, deepest category, etc.
"""

import asyncio
import csv
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database.connection import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectSegmentationAnalyzer:
    """Analyzer for project segmentation data."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def _generate_expected_hashed_project_ids(self, project_id: str, categories_flat: List[str]) -> List[str]:
        """
        Generate expected hashed project IDs based on the old logic.
        
        Args:
            project_id: The actual project ID
            categories_flat: List of category paths used for grouping
            
        Returns:
            List of expected hashed project IDs
        """
        hashed_ids = []
        for category_path in categories_flat:
            run_group_id_str = f"{project_id}_{category_path}"
            hashed_id = hashlib.sha1(run_group_id_str.encode()).hexdigest()
            hashed_ids.append(hashed_id)
        
        return hashed_ids
    
    async def find_project_segmentation_data(self, project_id: str) -> Tuple[List[str], Set[str]]:
        """
        Find all hashed project IDs and ASINs that belong to the given project.
        
        Args:
            project_id: The actual project ID
            
        Returns:
            Tuple of (hashed_project_ids, project_asins)
        """
        try:
            # Get project details
            project_result = self.supabase.table('projects')\
                .select('selected_product_asins, selected_categories')\
                .eq('id', project_id)\
                .single()\
                .execute()
            
            if not project_result.data:
                logger.error(f"Project {project_id} not found")
                return [], set()
            
            project_data = project_result.data
            project_asins = set(project_data.get('selected_product_asins', []))
            
            if not project_asins:
                logger.warning(f"No ASINs found for project {project_id}")
                return [], set()
            
            logger.info(f"Project has {len(project_asins)} ASINs")
            
            # Get all product_wide_table records for these ASINs to find categories_flat
            products_result = self.supabase.table('product_wide_table')\
                .select('platform_id, categories_flat')\
                .in_('platform_id', list(project_asins))\
                .execute()
            
            if not products_result.data:
                logger.warning(f"No product_wide_table records found for project ASINs")
                return [], set()
            
            # Extract unique categories_flat paths
            categories_flat = set()
            for product in products_result.data:
                categories_flat_path = product.get('categories_flat')
                if categories_flat_path and categories_flat_path.strip():
                    categories_flat.add(categories_flat_path.strip())
            
            logger.info(f"Found {len(categories_flat)} unique category paths")
            
            # Generate expected hashed project IDs
            expected_hashed_ids = self._generate_expected_hashed_project_ids(
                project_id, list(categories_flat)
            )
            
            # Find actual hashed project IDs that exist in the database
            actual_hashed_ids = []
            for hashed_id in expected_hashed_ids:
                count_result = self.supabase.table('product_segment_assignments')\
                    .select('product_id', count='exact')\
                    .eq('project_id', hashed_id)\
                    .execute()
                
                if count_result.count and count_result.count > 0:
                    actual_hashed_ids.append(hashed_id)
                    logger.info(f"Found hashed project ID {hashed_id} with {count_result.count} assignments")
            
            logger.info(f"Total hashed project IDs found: {len(actual_hashed_ids)}")
            return actual_hashed_ids, project_asins
            
        except Exception as e:
            logger.error(f"Error finding project segmentation data: {e}")
            return [], set()
    
    async def _find_additional_hashed_ids(self, project_asins: Set[str]) -> List[str]:
        """
        Find additional hashed project IDs that contain the project's ASINs.
        
        Args:
            project_asins: Set of ASINs belonging to the project
            
        Returns:
            List of additional hashed project IDs
        """
        try:
            # Get product IDs for these ASINs
            products_result = self.supabase.table('product_wide_table')\
                .select('id, platform_id')\
                .in_('platform_id', list(project_asins))\
                .execute()
            
            if not products_result.data:
                return []
            
            product_ids = [p['id'] for p in products_result.data]
            
            # Find all project_ids that have assignments for these product_ids
            assignments_result = self.supabase.table('product_segment_assignments')\
                .select('project_id')\
                .in_('product_id', product_ids)\
                .execute()
            
            if not assignments_result.data:
                return []
            
            additional_hashed_ids = list(set([a['project_id'] for a in assignments_result.data]))
            logger.info(f"Found {len(additional_hashed_ids)} additional hashed project IDs")
            
            return additional_hashed_ids
            
        except Exception as e:
            logger.error(f"Error finding additional hashed IDs: {e}")
            return []
    
    async def get_segmentation_assignments(self, hashed_project_ids: List[str]) -> List[Dict]:
        """
        Get all segmentation assignments for the given hashed project IDs.
        
        Args:
            hashed_project_ids: List of hashed project IDs
            
        Returns:
            List of assignment data with product details
        """
        try:
            all_assignments = []
            
            for hashed_project_id in hashed_project_ids:
                logger.info(f"Processing hashed project ID: {hashed_project_id}")
                
                # Get assignments for this hashed project ID
                assignments_result = self.supabase.table('product_segment_assignments')\
                    .select('run_id, product_id, segment_name, taxonomy_id_initial, taxonomy_id_refined')\
                    .eq('project_id', hashed_project_id)\
                    .execute()
                
                if not assignments_result.data:
                    logger.warning(f"No assignments found for hashed project ID {hashed_project_id}")
                    continue
                
                # Get product details for these assignments
                product_ids = [a['product_id'] for a in assignments_result.data]
                
                products_result = self.supabase.table('product_wide_table')\
                    .select('id, platform_id, title, category, categories_flat, category_l1_id, category_l2_id, category_l3_id, category_l4_id, category_l5_id, category_l6_id, category_deepest_level')\
                    .in_('id', product_ids)\
                    .execute()
                
                if not products_result.data:
                    logger.warning(f"No product details found for assignments in {hashed_project_id}")
                    continue
                
                # Create product lookup
                product_lookup = {p['id']: p for p in products_result.data}
                
                # Get taxonomy details
                taxonomy_ids = set()
                for assignment in assignments_result.data:
                    if assignment.get('taxonomy_id_initial'):
                        taxonomy_ids.add(assignment['taxonomy_id_initial'])
                    if assignment.get('taxonomy_id_refined'):
                        taxonomy_ids.add(assignment['taxonomy_id_refined'])
                
                taxonomies_result = self.supabase.table('product_segment_taxonomies')\
                    .select('id, segment_name, definition, stage')\
                    .in_('id', list(taxonomy_ids))\
                    .execute()
                
                taxonomy_lookup = {t['id']: t for t in taxonomies_result.data} if taxonomies_result.data else {}
                
                # Combine assignment data with product and taxonomy details
                for assignment in assignments_result.data:
                    product_id = assignment['product_id']
                    product = product_lookup.get(product_id)
                    
                    if not product:
                        logger.warning(f"Product {product_id} not found in product_wide_table")
                        continue
                    
                    # Get taxonomy details
                    initial_taxonomy = taxonomy_lookup.get(assignment.get('taxonomy_id_initial'))
                    refined_taxonomy = taxonomy_lookup.get(assignment.get('taxonomy_id_refined'))
                    
                    # Determine deepest category ID based on category_deepest_level
                    deepest_category_id = self._get_deepest_category_id(product)
                    
                    assignment_data = {
                        'hashed_project_id': hashed_project_id,
                        'run_id': assignment['run_id'],
                        'product_id': product_id,
                        'platform_id': product['platform_id'],
                        'title': product['title'],
                        'category': product['category'],
                        'categories_flat': product['categories_flat'],
                        'category_deepest_level': product.get('category_deepest_level'),
                        'deepest_category_id': deepest_category_id,
                        'segment_name': assignment.get('segment_name'),
                        'initial_taxonomy_name': initial_taxonomy.get('segment_name') if initial_taxonomy else None,
                        'initial_taxonomy_definition': initial_taxonomy.get('definition') if initial_taxonomy else None,
                        'refined_taxonomy_name': refined_taxonomy.get('segment_name') if refined_taxonomy else None,
                        'refined_taxonomy_definition': refined_taxonomy.get('definition') if refined_taxonomy else None,
                        'taxonomy_stage': refined_taxonomy.get('stage') if refined_taxonomy else None,
                    }
                    
                    all_assignments.append(assignment_data)
            
            logger.info(f"Total assignments processed: {len(all_assignments)}")
            return all_assignments
            
        except Exception as e:
            logger.error(f"Error getting segmentation assignments: {e}")
            return []
    
    def _get_deepest_category_id(self, product: Dict) -> str:
        """
        Get the deepest category ID based on category_deepest_level.
        
        Args:
            product: Product data from product_wide_table
            
        Returns:
            The deepest category ID
        """
        deepest_level = product.get('category_deepest_level', 1)
        
        if deepest_level == 1 and product.get('category_id'):
            return product['category_id']
        elif deepest_level == 2 and product.get('category_l1_id'):
            return product['category_l1_id']
        elif deepest_level == 3 and product.get('category_l2_id'):
            return product['category_l2_id']
        elif deepest_level == 4 and product.get('category_l3_id'):
            return product['category_l3_id']
        elif deepest_level == 5 and product.get('category_l4_id'):
            return product['category_l4_id']
        elif deepest_level == 6 and product.get('category_l5_id'):
            return product['category_l5_id']
        elif deepest_level == 7 and product.get('category_l6_id'):
            return product['category_l6_id']
        else:
            # Fallback to category_id if available, otherwise return 'unknown'
            return product.get('category_id', 'unknown')
    
    def export_to_csv(self, assignments: List[Dict], output_file: str):
        """
        Export assignment data to CSV.
        
        Args:
            assignments: List of assignment data
            output_file: Output CSV file path
        """
        try:
            if not assignments:
                logger.warning("No assignments to export")
                return
            
            # Define CSV columns
            fieldnames = [
                'hashed_project_id',
                'run_id',
                'product_id',
                'platform_id',
                'title',
                'category',
                'categories_flat',
                'category_deepest_level',
                'deepest_category_id',
                'segment_name',
                'initial_taxonomy_name',
                'initial_taxonomy_definition',
                'refined_taxonomy_name',
                'refined_taxonomy_definition',
                'taxonomy_stage'
            ]
            
            # Create output directory if it doesn't exist
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for assignment in assignments:
                    writer.writerow(assignment)
            
            logger.info(f"Exported {len(assignments)} assignments to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    async def analyze_project(self, project_id: str, output_file: str = None):
        """
        Main method to analyze a project's segmentation data.
        
        Args:
            project_id: The project ID to analyze
            output_file: Optional output CSV file path
        """
        try:
            logger.info(f"Starting analysis for project: {project_id}")
            
            # Find hashed project IDs and ASINs
            hashed_project_ids, project_asins = await self.find_project_segmentation_data(project_id)
            
            if not hashed_project_ids:
                logger.warning(f"No segmentation data found for project {project_id}")
                return
            
            # Get all assignments
            assignments = await self.get_segmentation_assignments(hashed_project_ids)
            
            if not assignments:
                logger.warning(f"No assignments found for project {project_id}")
                return
            
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"project_segmentation_analysis_{project_id}_{timestamp}.csv"
            
            # Export to CSV
            self.export_to_csv(assignments, output_file)
            
            # Print summary
            logger.info(f"\n=== Analysis Summary ===")
            logger.info(f"Project ID: {project_id}")
            logger.info(f"Hashed Project IDs: {len(hashed_project_ids)}")
            logger.info(f"Total Assignments: {len(assignments)}")
            logger.info(f"Unique Products: {len(set(a['platform_id'] for a in assignments))}")
            logger.info(f"Unique Segments: {len(set(a['segment_name'] for a in assignments if a['segment_name']))}")
            logger.info(f"Output File: {output_file}")
            
        except Exception as e:
            logger.error(f"Error analyzing project: {e}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze project segmentation data and export to CSV')
    parser.add_argument('project_id', help='Project ID to analyze')
    parser.add_argument('--output', '-o', help='Output CSV file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = ProjectSegmentationAnalyzer()
    await analyzer.analyze_project(args.project_id, args.output)


if __name__ == '__main__':
    asyncio.run(main()) 