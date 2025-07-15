#!/usr/bin/env python3
"""
Standalone script for smart capability labeling of products in project 36416581-f0e6-4785-9e65-ef09d0e3e82d

This script uses a modular architecture with separate components for:
- Data models and configuration
- LLM processing stages
- Database service operations
- Result validation and storage

Usage:
    python -m backend.product_label.scripts.label_smart_capability [--dry-run] [--batch-size N]
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database.connection import get_supabase_service_client
from .config import (
    LEVITON_PROJECT_ID, FIELD_NAME, FIELD_TYPE, FIELD_DESCRIPTION, 
    BATCH_SIZE, MAX_RETRIES, LLM_TEMPERATURE, SMART_CAPABILITY_LABELS,
    UI_CONFIG
)
from .models import LabelingConfiguration
from .smart_capability_service import SmartCapabilityService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Smart Capability Labeling Script')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Batch size for processing')
    
    args = parser.parse_args()
    
    # Validate batch size
    if args.batch_size < 1 or args.batch_size > 100:
        logger.error("❌ Batch size must be between 1 and 100")
        sys.exit(1)
        
    # Create configuration
    config = LabelingConfiguration(
        project_id=LEVITON_PROJECT_ID,
        field_name=FIELD_NAME,
        field_type=FIELD_TYPE,
        field_description=FIELD_DESCRIPTION,
        batch_size=args.batch_size,
        max_retries=MAX_RETRIES,
        llm_temperature=LLM_TEMPERATURE,
        available_labels=SMART_CAPABILITY_LABELS,
        ui_config=UI_CONFIG,
        dry_run=args.dry_run
    )
    
    # Create Supabase client
    supabase_client = get_supabase_service_client()
    
    # Create and run service
    service = SmartCapabilityService(supabase_client, config)
    stats = await service.execute_labeling()
    
    # Log final summary
    logger.info("📊 Final Statistics:")
    logger.info(f"   Success Rate: {stats.success_rate:.1f}%")
    logger.info(f"   Total Duration: {stats.duration_seconds:.1f}s")
    
    # Exit with appropriate code
    if stats.failed_labels > 0:
        logger.warning(f"⚠️  {stats.failed_labels} products failed to be labeled")
        sys.exit(1)
    else:
        logger.info("✅ All products processed successfully")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main()) 