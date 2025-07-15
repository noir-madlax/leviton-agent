#!/usr/bin/env python3
"""
Generic test runner for product labeling services

This script tests labeling functionality with sample data without hitting the database.

Usage:
    python -m backend.product_label.base.test_runner smart_capability
    python -m backend.product_label.base.test_runner package_type
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
import importlib
import pandas as pd

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .models import LabelingContext, ProductData
from .base_stage import BaseStage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LabelingTester:
    """Generic test class for product labeling"""
    
    def __init__(self, labeling_type: str):
        self.labeling_type = labeling_type
        self.sample_products = self._load_sample_products()
        self.config = self._load_config()
        self.stage = self._create_stage()
        
    def _load_sample_products(self) -> List[ProductData]:
        """Load sample products for the labeling type"""
        try:
            # Import the sample data module for the labeling type
            sample_module = importlib.import_module(f'backend.product_label.{self.labeling_type}.sample_data')
            return sample_module.SAMPLE_PRODUCTS
        except ImportError:
            # Use default sample products if specific ones don't exist
            logger.warning(f"No sample data found for {self.labeling_type}, using defaults")
            return self._get_default_sample_products()
            
    def _get_default_sample_products(self) -> List[ProductData]:
        """Default sample products for testing"""
        return [
            ProductData(product_id="1", title="Kasa Smart Light Switch WiFi HS200 Single Pole"),
            ProductData(product_id="2", title="Leviton Decora Standard Toggle Switch 15A White"),
            ProductData(product_id="3", title="Lutron Caseta Wireless Smart Dimmer Switch"),
            ProductData(product_id="4", title="GE Enbrighten Z-Wave Smart Toggle Switch 3-Pack"),
            ProductData(product_id="5", title="Lutron Maestro C.L Dimmer Switch for Dimmable LED"),
            ProductData(product_id="6", title="Switch Plate Cover Wall Outlet White 3-Gang Set of 5"),
            ProductData(product_id="7", title="Philips Hue Smart Dimmer Switch with Bluetooth"),
            ProductData(product_id="8", title="Electrical Switch Assembly Component Bundle Kit"),
            ProductData(product_id="9", title="Leviton Single Pole Quiet Switch 15A Pair"),
            ProductData(product_id="10", title="TP-Link Kasa Smart Dimmer Switch KS220M 6-Pack")
        ]
        
    def _load_config(self) -> Dict:
        """Load configuration for the labeling type"""
        config_module = importlib.import_module(f'backend.product_label.{self.labeling_type}.config')
        
        config = {}
        for attr_name in dir(config_module):
            if attr_name.isupper():
                config[attr_name] = getattr(config_module, attr_name)
                
        return config
        
    def _create_stage(self) -> BaseStage:
        """Create the appropriate labeling stage"""
        base_path = Path(__file__).parent.parent
        prompt_path = base_path / self.labeling_type / "prompts" / f"{self.labeling_type}_prompt_v0.txt"
        
        # Try to use labeling-type specific stage if available
        try:
            if self.labeling_type == "package_type":
                from backend.product_label.package_type import PackageTypeStage
                return PackageTypeStage(str(prompt_path), max_retries=3)
            elif self.labeling_type == "smart_capability":
                # Use generic base stage for smart capability  
                return BaseStage(str(prompt_path), max_retries=3)
            else:
                # Default to base stage for unknown types
                logger.warning(f"Unknown labeling type '{self.labeling_type}', using generic BaseStage")
                return BaseStage(str(prompt_path), max_retries=3)
                
        except ImportError as e:
            logger.warning(f"Failed to import specific stage for {self.labeling_type}: {e}")
            logger.info(f"Falling back to generic BaseStage")
            return BaseStage(str(prompt_path), max_retries=3)
        
    async def run_test(self) -> None:
        """Run the test with sample products"""
        logger.info(f"🧪 Starting {self.labeling_type} labeling test")
        logger.info(f"📊 Testing with {len(self.sample_products)} sample products")
        
        try:
            # Test the labeling process
            result = await self._test_batch_labeling()
            
            if result and result.success:
                self._display_results(result.assignments)
                logger.info("✅ Test completed successfully")
            else:
                logger.error(f"❌ Test failed: {result.error_message if result else 'No result'}")
                
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}", exc_info=True)
            raise
            
    async def _test_batch_labeling(self) -> Optional:
        """Test the batch labeling process using the stage"""
        
        # Create context for the test
        context = LabelingContext(
            products=self.sample_products,
            available_labels=self.config['LABELS'],
            batch_id=1,
            project_id="TEST_PROJECT"
        )
        
        # Execute the stage
        try:
            logger.info(f"🤖 Executing {self.labeling_type} stage for test batch")
            result = await self.stage.execute(context)
            
            if result.success:
                logger.info("✅ Stage execution successful")
                return result
            else:
                logger.error(f"❌ Stage execution failed: {result.error_message}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Stage execution failed with error: {e}")
            return None
        
    def _display_results(self, results: Dict[str, str]) -> None:
        """Display test results in a formatted table"""
        logger.info("="*100)
        logger.info(f"📊 {self.labeling_type.upper()} LABELING TEST RESULTS")
        logger.info("="*100)
        
        # Prepare data for table
        results_data = []
        for idx, label in results.items():
            product = self.sample_products[int(idx)]
            results_data.append({
                'Index': int(idx),
                'Product_ID': product.product_id,
                'Title': product.title[:70] + "..." if len(product.title) > 70 else product.title,
                'Label': label
            })
            
        # Sort by index
        results_data.sort(key=lambda x: x['Index'])
        
        # Create DataFrame for nice formatting
        df = pd.DataFrame(results_data)
        logger.info(f"\n{df.to_string(index=False)}")
        
        # Group results by label for summary
        logger.info("\n📋 Results Summary by Label:")
        label_groups = {}
        for data in results_data:
            label = data['Label']
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(data['Index'])
            
        for label, indices in sorted(label_groups.items()):
            logger.info(f"   {label}: {len(indices)} products (indices: {indices})")
        
        logger.info("="*100)

async def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        logger.error("Usage: python -m backend.product_label.base.test_runner <labeling_type>")
        logger.error("Available types: smart_capability, package_type")
        sys.exit(1)
        
    labeling_type = sys.argv[1]
    
    tester = LabelingTester(labeling_type)
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main()) 