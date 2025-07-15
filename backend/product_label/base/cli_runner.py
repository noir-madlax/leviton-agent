#!/usr/bin/env python3
"""
Generic CLI runner for product labeling services

This script can run any labeling service by loading the appropriate configuration
and prompt template.

Usage:
    python -m backend.product_label.base.cli_runner smart_capability [options]
    python -m backend.product_label.base.cli_runner package_type [options]
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import importlib

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database.connection import get_supabase_service_client
from .models import LabelingConfiguration
from .base_service import BaseService
from .base_stage import BaseStage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_BATCH_SIZE = 25
DEFAULT_MAX_RETRIES = 3
DEFAULT_LLM_TEMPERATURE = 0.1

def load_labeling_config(labeling_type: str) -> Dict[str, Any]:
    """Load configuration for a specific labeling type"""
    try:
        # Import the config module for the labeling type
        config_module = importlib.import_module(f'backend.product_label.{labeling_type}.config')
        
        # Extract all uppercase constants from the config
        config = {}
        for attr_name in dir(config_module):
            if attr_name.isupper():
                config[attr_name] = getattr(config_module, attr_name)
                
        return config
    except ImportError as e:
        logger.error(f"❌ Failed to load config for {labeling_type}: {e}")
        logger.error(f"Available labeling types: smart_capability, package_type")
        sys.exit(1)

def get_prompt_template_path(labeling_type: str) -> str:
    """Get the path to the prompt template for a labeling type"""
    base_path = Path(__file__).parent.parent
    prompt_path = base_path / labeling_type / "prompts" / f"{labeling_type}_prompt_v0.txt"
    
    if not prompt_path.exists():
        logger.error(f"❌ Prompt template not found: {prompt_path}")
        sys.exit(1)
        
    return str(prompt_path)

def create_stage(labeling_type: str, prompt_template_path: str, max_retries: int) -> BaseStage:
    """Create the appropriate stage for a labeling type"""
    
    # Try to import and use labeling-type specific stage if available
    try:
        if labeling_type == "package_type":
            from backend.product_label.package_type import PackageTypeStage
            return PackageTypeStage(prompt_template_path, max_retries)
        elif labeling_type == "smart_capability":
            # Use generic base stage for smart capability
            return BaseStage(prompt_template_path, max_retries)
        else:
            # Default to base stage for unknown types
            logger.warning(f"Unknown labeling type '{labeling_type}', using generic BaseStage")
            return BaseStage(prompt_template_path, max_retries)
            
    except ImportError as e:
        logger.warning(f"Failed to import specific stage for {labeling_type}: {e}")
        logger.info(f"Falling back to generic BaseStage")
        return BaseStage(prompt_template_path, max_retries)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generic Product Labeling CLI')
    parser.add_argument('labeling_type', help='Type of labeling (smart_capability, package_type)')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size for processing')
    parser.add_argument('--sample-size', type=int, help='Limit processing to N products for testing')
    parser.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES, help='Maximum LLM retry attempts')
    
    args = parser.parse_args()
    
    # Validate batch size
    if args.batch_size < 1 or args.batch_size > 100:
        logger.error("❌ Batch size must be between 1 and 100")
        sys.exit(1)
        
    # Load labeling-specific configuration
    labeling_config = load_labeling_config(args.labeling_type)
    
    # Get prompt template path
    prompt_template_path = get_prompt_template_path(args.labeling_type)
    
    # Create configuration
    config = LabelingConfiguration(
        project_id=labeling_config['PROJECT_ID'],
        field_name=labeling_config['FIELD_NAME'],
        field_type=labeling_config.get('FIELD_TYPE', 'product_label'),
        field_description=labeling_config['FIELD_DESCRIPTION'],
        batch_size=args.batch_size,
        max_retries=args.max_retries,
        llm_temperature=labeling_config.get('LLM_TEMPERATURE', DEFAULT_LLM_TEMPERATURE),
        available_labels=labeling_config['LABELS'],
        ui_config=labeling_config['UI_CONFIG'],
        dry_run=args.dry_run,
        prompt_template_path=prompt_template_path,
        sample_size=args.sample_size
    )
    
    # Create Supabase client
    supabase_client = get_supabase_service_client()
    
    # Create stage and service
    stage = create_stage(args.labeling_type, prompt_template_path, args.max_retries)
    service = BaseService(supabase_client, config, stage)
    
    # Run labeling
    logger.info(f"🚀 Starting {args.labeling_type} labeling")
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