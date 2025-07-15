"""
Smart capability labeling service

This module provides a service class that orchestrates the entire smart capability
labeling process including database operations, batch processing, and result storage.
"""

import logging
from datetime import datetime
from typing import List, Optional

from supabase import Client
from core.utils.batching import make_batches
from .models import (
    ProductData, SmartCapabilityContext, SmartCapabilityResult, 
    LabelingStats, LabelingConfiguration
)
from .smart_capability_stage import SmartCapabilityStage

logger = logging.getLogger(__name__)

class SmartCapabilityService:
    """Service for managing smart capability labeling operations"""
    
    def __init__(self, supabase_client: Client, config: LabelingConfiguration):
        self.supabase = supabase_client
        self.config = config
        self.stage = SmartCapabilityStage(max_retries=config.max_retries)
        self.stats = LabelingStats()
        self.field_id: Optional[int] = None
        
    async def execute_labeling(self) -> LabelingStats:
        """Execute the complete labeling process"""
        
        self.stats.start_time = datetime.utcnow()
        logger.info("🚀 Starting smart capability labeling service")
        logger.info(f"📊 Project ID: {self.config.project_id}")
        logger.info(f"🏷️  Field Name: {self.config.field_name}")
        logger.info(f"📦 Batch Size: {self.config.batch_size}")
        logger.info(f"🔄 Dry Run: {self.config.dry_run}")
        
        try:
            # Step 1: Setup field
            await self._setup_field()
            
            # Step 2: Get product data
            product_data = await self._get_product_data()
            if not product_data:
                logger.warning("No products found to label")
                return self.stats
                
            self.stats.total_products = len(product_data)
            
            # Step 3: Process in batches
            await self._process_batches(product_data)
            
            # Step 4: Finalize
            self.stats.end_time = datetime.utcnow()
            self._log_final_results()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Service failed: {e}", exc_info=True)
            self.stats.end_time = datetime.utcnow()
            raise
            
    async def _setup_field(self) -> None:
        """Create or find the smart_capability field in project_extend_fields"""
        logger.info("🔧 Setting up smart capability field...")
        
        try:
            # First check if field already exists
            existing_field = self.supabase.table('project_extend_fields').select(
                'id, field_name, filter_options'
            ).eq('project_id', self.config.project_id).eq('field_name', self.config.field_name).execute()
            
            if existing_field.data:
                self.field_id = existing_field.data[0]['id']
                logger.info(f"✅ Found existing field with ID: {self.field_id}")
                return
                
            # Create new field
            if not self.config.dry_run:
                # Use the correct field structure based on existing schema
                filter_options = self.config.ui_config.copy()
                filter_options['description'] = self.config.field_description
                
                field_data = {
                    'project_id': self.config.project_id,
                    'field_name': self.config.field_name,
                    'display_name': self.config.field_name.replace('_', ' ').title(),
                    'field_type': 'select',  # Based on the existing schema usage
                    'filter_options': filter_options,
                    'is_active': True,
                    'sort_order': 1
                }
                
                result = self.supabase.table('project_extend_fields').insert(field_data).execute()
                self.field_id = result.data[0]['id']
                logger.info(f"✅ Created new field with ID: {self.field_id}")
            else:
                logger.info("🔄 [DRY RUN] Would create new field")
                self.field_id = -1  # Placeholder for dry run
                
        except Exception as e:
            logger.error(f"❌ Failed to setup field: {e}")
            raise
            
    async def _get_product_data(self) -> List[ProductData]:
        """Get product IDs and titles for labeling"""
        logger.info("📥 Retrieving product data...")
        
        try:
            # Get product ASINs from project_extend_data
            product_asins_query = self.supabase.table('project_extend_data').select(
                'asins'
            ).eq('project_id', self.config.project_id)
            
            # Get unique product ASINs
            product_asins_result = product_asins_query.execute()
            if not product_asins_result.data:
                logger.warning("No products found in project_extend_data")
                return []
                
            product_asins = list(set([row['asins'] for row in product_asins_result.data]))
            logger.info(f"📊 Found {len(product_asins)} unique products in project")
            
            # Get product titles from product_wide_table using platform_id
            titles_query = self.supabase.table('product_wide_table').select(
                'id, platform_id, title'
            ).in_('platform_id', product_asins).neq('title', None)
            
            titles_result = titles_query.execute()
            if not titles_result.data:
                logger.warning("No product titles found")
                return []
                
            product_data = [
                ProductData(product_id=str(row['id']), title=row['title']) 
                for row in titles_result.data
            ]
            
            logger.info(f"✅ Retrieved {len(product_data)} products with titles")
            return product_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get product data: {e}")
            raise
            
    async def _process_batches(self, product_data: List[ProductData]) -> None:
        """Process products in batches through the labeling stage"""
        logger.info(f"🔄 Processing {len(product_data)} products in batches of {self.config.batch_size}")
        
        # Create batches
        batches = make_batches(product_data, self.config.batch_size)
        total_batches = len(batches)
        
        logger.info(f"📦 Created {total_batches} batches")
        
        for batch_idx, batch in enumerate(batches, 1):
            logger.info(f"⏳ Processing batch {batch_idx}/{total_batches} ({len(batch)} products)")
            
            try:
                # Create context for this batch
                context = SmartCapabilityContext(
                    products=batch,
                    available_labels=self.config.available_labels,
                    batch_id=batch_idx,
                    project_id=self.config.project_id
                )
                
                # Process batch through stage
                result = await self.stage.execute(context)
                
                # Store results
                if result.success:
                    await self._store_batch_results(batch, result)
                    self.stats.batches_processed += 1
                    self.stats.successful_labels += len(result.assignments)
                    logger.info(f"✅ Batch {batch_idx} completed successfully")
                else:
                    self.stats.batches_failed += 1
                    self.stats.failed_labels += len(batch)
                    logger.warning(f"⚠️  Batch {batch_idx} failed: {result.error_message}")
                    
            except Exception as e:
                logger.error(f"❌ Batch {batch_idx} failed with error: {e}")
                self.stats.batches_failed += 1
                self.stats.failed_labels += len(batch)
                continue
                
            self.stats.processed_products += len(batch)
            
    async def _store_batch_results(self, batch: List[ProductData], result: SmartCapabilityResult) -> None:
        """Store batch results in project_extend_data"""
        if self.config.dry_run:
            logger.info(f"🔄 [DRY RUN] Would store {len(result.assignments)} labels")
            for idx, label in result.assignments.items():
                product = batch[int(idx)]
                product_title = product.title[:50]
                logger.info(f"  Product {product.product_id}: {product_title}... → {label}")
            return
            
        try:
            # Get platform_id mapping for products
            product_platform_mapping = {}
            for product in batch:
                # Get platform_id from the product_wide_table
                platform_query = self.supabase.table('product_wide_table').select(
                    'platform_id'
                ).eq('id', product.product_id).execute()
                
                if platform_query.data:
                    product_platform_mapping[product.product_id] = platform_query.data[0]['platform_id']
            
            # Prepare data for upsert using the project_extend_data structure
            upsert_data = []
            for idx, label in result.assignments.items():
                product = batch[int(idx)]
                platform_id = product_platform_mapping.get(product.product_id)
                
                if platform_id:
                    # Store as extend field data
                    extend_data = {self.config.field_name: label}
                    
                    upsert_data.append({
                        'project_id': self.config.project_id,
                        'asins': platform_id,
                        'extend': extend_data
                    })
                
            # Upsert to database
            db_result = self.supabase.table('project_extend_data').upsert(
                upsert_data,
                on_conflict='project_id,asins'
            ).execute()
            
            if db_result.data:
                logger.info(f"✅ Stored {len(db_result.data)} labels in database")
            else:
                logger.warning("⚠️  No data returned from upsert operation")
                
        except Exception as e:
            logger.error(f"❌ Failed to store batch results: {e}")
            raise
            
    def _log_final_results(self) -> None:
        """Log final results and statistics"""
        logger.info("="*60)
        logger.info("📊 SMART CAPABILITY LABELING RESULTS")
        logger.info("="*60)
        logger.info(f"Total Products: {self.stats.total_products}")
        logger.info(f"Processed Products: {self.stats.processed_products}")
        logger.info(f"Successful Labels: {self.stats.successful_labels}")
        logger.info(f"Failed Labels: {self.stats.failed_labels}")
        logger.info(f"Batches Processed: {self.stats.batches_processed}")
        logger.info(f"Batches Failed: {self.stats.batches_failed}")
        logger.info(f"Success Rate: {self.stats.success_rate:.1f}%")
        logger.info(f"Duration: {self.stats.duration_seconds:.1f} seconds")
        logger.info("="*60)
        
        if self.config.dry_run:
            logger.info("🔄 This was a dry run - no data was actually modified")
        else:
            logger.info("✅ Service completed successfully") 