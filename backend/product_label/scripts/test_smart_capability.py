#!/usr/bin/env python3
"""
Test script for smart capability labeling with sample data

This script tests the labeling functionality with a small sample of products
to verify the LLM prompt and validation logic works correctly.

Usage:
    python -m backend.product_label.scripts.test_smart_capability
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .config import SMART_CAPABILITY_LABELS
from .models import SmartCapabilityContext, ProductData
from .smart_capability_stage import SmartCapabilityStage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample product data for testing
SAMPLE_PRODUCTS = [
    ProductData(product_id="1", title="Kasa Smart Light Switch WiFi HS200 Single Pole"),
    ProductData(product_id="2", title="Leviton Decora Standard Toggle Switch 15A White"),
    ProductData(product_id="3", title="Lutron Caseta Wireless Smart Dimmer Switch"),
    ProductData(product_id="4", title="GE Enbrighten Z-Wave Smart Toggle Switch"),
    ProductData(product_id="5", title="Lutron Maestro C.L Dimmer Switch for Dimmable LED"),
    ProductData(product_id="6", title="Switch Plate Cover Wall Outlet White 3-Gang"),
    ProductData(product_id="7", title="Philips Hue Smart Dimmer Switch with Bluetooth"),
    ProductData(product_id="8", title="Electrical Switch Assembly Component"),
    ProductData(product_id="9", title="Leviton Single Pole Quiet Switch 15A"),
    ProductData(product_id="10", title="TP-Link Kasa Smart Dimmer Switch KS220M")
]

class SmartCapabilityTester:
    """Test class for smart capability labeling"""
    
    def __init__(self):
        self.sample_products = SAMPLE_PRODUCTS
        self.stage = SmartCapabilityStage(max_retries=3)
        
    async def run_test(self) -> None:
        """Run the test with sample products"""
        logger.info("🧪 Starting smart capability labeling test")
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
            
    async def _test_batch_labeling(self) -> Optional[Dict[str, str]]:
        """Test the batch labeling process using the modular stage"""
        
        # Create context for the test
        context = SmartCapabilityContext(
            products=self.sample_products,
            available_labels=SMART_CAPABILITY_LABELS,
            batch_id=1,
            project_id="TEST_PROJECT"
        )
        
        # Execute the stage
        try:
            logger.info("🤖 Executing smart capability stage for test batch")
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
        """Display test results"""
        logger.info("="*60)
        logger.info("📊 SMART CAPABILITY LABELING TEST RESULTS")
        logger.info("="*60)
        
        # Group results by label
        label_groups = {}
        for idx, label in results.items():
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(int(idx))
            
        # Display results grouped by label
        for label, indices in label_groups.items():
            logger.info(f"\n🏷️  {label} ({len(indices)} products):")
            for idx in sorted(indices):
                product = self.sample_products[idx]
                logger.info(f"   [{idx}] {product.title}")
                
        logger.info("="*60)
        
        # Display expected vs actual for verification
        logger.info("🔍 Manual verification suggestions:")
        logger.info("Expected Smart: Products with 'Smart', 'WiFi', 'Bluetooth', 'Caseta', 'Z-Wave', 'Hue'")
        logger.info("Expected Non-Smart: Traditional switches without connectivity keywords")
        logger.info("Expected N/A: Switch plates, covers, electrical components")
        logger.info("Expected Unknown: Products with unclear titles")

async def main():
    """Main entry point"""
    tester = SmartCapabilityTester()
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main()) 