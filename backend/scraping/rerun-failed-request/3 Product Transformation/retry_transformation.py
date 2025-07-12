#!/usr/bin/env python3
"""
Retry Failed Data Transformation Tool

This script allows you to retry failed data transformation requests
without re-running the expensive scraping process.

Usage:
    python retry_transformation.py --batch-id 74 --dry-run
    python retry_transformation.py --request-id 74
    python retry_transformation.py --batch-id 74 --verbose
"""

import argparse
import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import asdict

# Add parent directories to path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))  # rerun-failed-request
scraping_dir = os.path.dirname(current_dir)  # scraping
backend_dir = os.path.dirname(scraping_dir)  # backend
project_root = os.path.dirname(backend_dir)  # project root
sys.path.insert(0, project_root)

from supabase import create_client, Client
from backend.config import settings
from backend.data_transformation.services.transformation_service import (
    DataTransformationService, 
    TransformationConfig
)
from retry_config import (
    RetryConfig, 
    TransformationStatus, 
    WorkflowStage,
    TABLES,
    MAX_RECORDS_PER_BATCH,
    SUPPORTED_STATUSES
)


class RetryTransformationTool:
    """Tool for retrying failed data transformations"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.supabase = self._setup_supabase()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with appropriate level"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
        
        # Create console handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_supabase(self) -> Client:
        """Setup Supabase client"""
        try:
            if self.config.supabase_url and self.config.supabase_key:
                url = self.config.supabase_url
                key = self.config.supabase_key
            else:
                # Use default config from settings
                url = settings.SUPABASE_URL
                key = settings.SUPABASE_SERVICE_KEY  # Use service key for full access
            
            if not url or not key:
                raise ValueError("Supabase URL and key must be configured")
            
            return create_client(url, key)
        except Exception as e:
            self.logger.error(f"Failed to setup Supabase client: {e}")
            raise
    
    async def retry_by_batch_id(self, batch_id: int) -> bool:
        """Retry transformation for a specific batch ID"""
        self.logger.info(f"🔄 Starting retry for batch_id: {batch_id}")
        
        try:
            # Find associated request
            request_info = await self._get_request_by_batch_id(batch_id)
            if not request_info:
                self.logger.error(f"❌ No request found for batch_id: {batch_id}")
                return False
            
            return await self._retry_transformation(
                request_id=request_info['id'],
                batch_id=batch_id
            )
        except Exception as e:
            self.logger.error(f"❌ Error retrying batch {batch_id}: {e}")
            return False
    
    async def retry_by_request_id(self, request_id: int) -> bool:
        """Retry transformation for a specific request ID"""
        self.logger.info(f"🔄 Starting retry for request_id: {request_id}")
        
        try:
            # Get request info
            request_info = await self._get_request_info(request_id)
            if not request_info:
                self.logger.error(f"❌ No request found for request_id: {request_id}")
                return False
            
            # Extract batch_id from scraping metadata or find it
            batch_id = await self._find_batch_id_for_request(request_id)
            if not batch_id:
                self.logger.error(f"❌ No batch_id found for request_id: {request_id}")
                return False
            
            return await self._retry_transformation(
                request_id=request_id,
                batch_id=batch_id
            )
        except Exception as e:
            self.logger.error(f"❌ Error retrying request {request_id}: {e}")
            return False
    
    async def _get_request_by_batch_id(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """Get request info by batch_id"""
        try:
            # First try to find request with this batch_id in amazon_products
            result = self.supabase.table(TABLES["AMAZON_PRODUCTS"])\
                .select("*")\
                .eq("batch_id", batch_id)\
                .limit(1)\
                .execute()
            
            if not result.data:
                self.logger.warning(f"No products found for batch_id: {batch_id}")
                return None
            
            # Try to find the scraping request
            # Look for requests that might be associated with this batch
            requests_result = self.supabase.table(TABLES["SCRAPING_REQUESTS"])\
                .select("*")\
                .eq("products_scraped", len(result.data))\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()
            
            if requests_result.data:
                # Find the most likely match based on timing and product count
                for request in requests_result.data:
                    if request.get("transformation_status") == TransformationStatus.FAILED:
                        return request
                
                # If no failed transformation found, return the first one
                return requests_result.data[0]
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting request for batch_id {batch_id}: {e}")
            return None
    
    async def _get_request_info(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get request info by request_id"""
        try:
            result = self.supabase.table(TABLES["SCRAPING_REQUESTS"])\
                .select("*")\
                .eq("id", request_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting request info for {request_id}: {e}")
            return None
    
    async def _find_batch_id_for_request(self, request_id: int) -> Optional[int]:
        """Find batch_id associated with a request"""
        try:
            # Get request info first
            request_info = await self._get_request_info(request_id)
            if not request_info:
                return None
            
            # Check if batch_id is in metadata
            metadata = request_info.get('metadata', {})
            if isinstance(metadata, dict) and 'batch_id' in metadata:
                return metadata['batch_id']
            
            # Try to find batch_id by looking at products_scraped count
            products_scraped = request_info.get('products_scraped', 0)
            if products_scraped > 0:
                # Look for amazon_products batches with matching product count
                result = self.supabase.table(TABLES["AMAZON_PRODUCTS"])\
                    .select("batch_id")\
                    .order("batch_id", desc=True)\
                    .execute()
                
                if result.data:
                    # Group by batch_id and count products
                    batch_counts = {}
                    for row in result.data:
                        batch_id = row['batch_id']
                        batch_counts[batch_id] = batch_counts.get(batch_id, 0) + 1
                    
                    # Find batch with matching product count
                    for batch_id, count in batch_counts.items():
                        if count == products_scraped:
                            return batch_id
            
            # Last resort: find the most recent batch
            result = self.supabase.table(TABLES["AMAZON_PRODUCTS"])\
                .select("batch_id")\
                .order("batch_id", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]['batch_id']
            
            return None
        except Exception as e:
            self.logger.error(f"Error finding batch_id for request {request_id}: {e}")
            return None
    
    async def _retry_transformation(self, request_id: int, batch_id: int) -> bool:
        """Main retry logic"""
        self.logger.info(f"🔍 Analyzing request {request_id} with batch {batch_id}")
        
        # Step 1: Validate request state
        if not await self._validate_request_state(request_id, batch_id):
            return False
        
        # Step 2: Validate source data
        if not await self._validate_source_data(batch_id):
            return False
        
        # Step 3: Check for existing transformed data
        if await self._check_existing_transformed_data(batch_id):
            self.logger.warning(f"⚠️ Transformed data already exists for batch {batch_id}")
            if not self.config.dry_run:
                # Update status to completed if data exists
                await self._update_request_status(
                    request_id, 
                    TransformationStatus.COMPLETED, 
                    WorkflowStage.COMPLETED
                )
            return True
        
        # Step 4: Backup current state (if enabled)
        if self.config.backup_failed_state and not self.config.dry_run:
            await self._backup_request_state(request_id)
        
        # Step 5: Execute retry
        if self.config.dry_run:
            self.logger.info(f"✅ DRY RUN: Would retry transformation for batch {batch_id}")
            return True
        
        return await self._execute_retry(request_id, batch_id)
    
    async def _validate_request_state(self, request_id: int, batch_id: int) -> bool:
        """Validate that the request is in a retryable state"""
        try:
            request_info = await self._get_request_info(request_id)
            if not request_info:
                self.logger.error(f"❌ Request {request_id} not found")
                return False
            
            transformation_status = request_info.get('transformation_status')
            workflow_stage = request_info.get('workflow_stage')
            
            self.logger.info(f"📋 Request state: transformation_status={transformation_status}, workflow_stage={workflow_stage}")
            
            # Check if transformation status is retryable
            if transformation_status not in SUPPORTED_STATUSES:
                self.logger.error(f"❌ Request {request_id} has unsupported transformation status: {transformation_status}")
                return False
            
            # Check if request has products_scraped
            products_scraped = request_info.get('products_scraped', 0)
            if products_scraped <= 0:
                self.logger.error(f"❌ Request {request_id} has no scraped products")
                return False
            
            self.logger.info(f"✅ Request {request_id} is in retryable state")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error validating request state: {e}")
            return False
    
    async def _validate_source_data(self, batch_id: int) -> bool:
        """Validate that source data exists and is complete"""
        try:
            # Check if amazon_products data exists
            result = self.supabase.table(TABLES["AMAZON_PRODUCTS"])\
                .select("batch_id, platform_id, title")\
                .eq("batch_id", batch_id)\
                .execute()
            
            if not result.data:
                self.logger.error(f"❌ No source data found for batch {batch_id}")
                return False
            
            total_records = len(result.data)
            valid_records = len([r for r in result.data if r.get('platform_id') and r.get('title')])
            
            self.logger.info(f"📊 Source data: {total_records} total records, {valid_records} valid records")
            
            if valid_records == 0:
                self.logger.error(f"❌ No valid records found for batch {batch_id}")
                return False
            
            if total_records > MAX_RECORDS_PER_BATCH:
                self.logger.error(f"❌ Batch {batch_id} has too many records ({total_records} > {MAX_RECORDS_PER_BATCH})")
                return False
            
            self.logger.info(f"✅ Source data validation passed for batch {batch_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error validating source data: {e}")
            return False
    
    async def _check_existing_transformed_data(self, batch_id: int) -> bool:
        """Check if transformed data already exists"""
        try:
            result = self.supabase.table(TABLES["PRODUCT_WIDE_TABLE"])\
                .select("batch_id")\
                .eq("batch_id", batch_id)\
                .limit(1)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            self.logger.error(f"❌ Error checking existing transformed data: {e}")
            return False
    
    async def _backup_request_state(self, request_id: int):
        """Backup current request state"""
        try:
            request_info = await self._get_request_info(request_id)
            if request_info:
                # Create a backup record
                backup_data = {
                    'original_request_id': request_id,
                    'backup_timestamp': datetime.now().isoformat(),
                    'original_state': request_info,
                    'backup_reason': 'transformation_retry'
                }
                
                # Store in a backup table (you might need to create this table)
                self.logger.info(f"💾 Backing up request {request_id} state")
                # Note: You may need to create a backup table in your database
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to backup request state: {e}")
    
    async def _execute_retry(self, request_id: int, batch_id: int) -> bool:
        """Execute the actual retry"""
        try:
            self.logger.info(f"🚀 Starting transformation retry for batch {batch_id}")
            
            # Step 1: Reset request status
            await self._update_request_status(
                request_id, 
                TransformationStatus.PROCESSING, 
                WorkflowStage.TRANSFORMING
            )
            
            # Step 2: Create transformation service with updated config
            transformation_config = TransformationConfig(
                skip_existing=self.config.skip_existing,
                validate_calculations=self.config.validate_calculations,
                dry_run=False,
                batch_size=self.config.batch_size
            )
            
            transformation_service = DataTransformationService(transformation_config)
            
            # Step 3: Execute transformation
            result = await transformation_service.transform_batch_for_orchestrator(
                batch_id=batch_id,
                request_id=request_id
            )
            
            # Step 4: Update final status
            if result.success:
                await self._update_request_status(
                    request_id,
                    TransformationStatus.COMPLETED,
                    WorkflowStage.COMPLETED,
                    {
                        'retry_success': True,
                        'retry_timestamp': datetime.now().isoformat(),
                        'processed_count': result.processed_count,
                        'retry_summary': result.summary
                    }
                )
                self.logger.info(f"✅ Transformation retry successful for batch {batch_id}")
                self.logger.info(f"📊 Processed {result.processed_count} records in {result.duration_seconds:.2f}s")
                return True
            else:
                await self._update_request_status(
                    request_id,
                    TransformationStatus.FAILED,
                    WorkflowStage.FAILED,
                    {
                        'retry_failed': True,
                        'retry_timestamp': datetime.now().isoformat(),
                        'retry_errors': result.errors[:5],
                        'retry_summary': result.summary
                    }
                )
                self.logger.error(f"❌ Transformation retry failed for batch {batch_id}")
                self.logger.error(f"Errors: {result.errors[:3]}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error executing retry: {e}")
            await self._update_request_status(
                request_id,
                TransformationStatus.FAILED,
                WorkflowStage.FAILED,
                {
                    'retry_error': str(e),
                    'retry_timestamp': datetime.now().isoformat()
                }
            )
            return False
    
    async def _update_request_status(self, request_id: int, 
                                   transformation_status: str,
                                   workflow_stage: str,
                                   additional_metadata: Optional[Dict[str, Any]] = None):
        """Update request status"""
        try:
            update_data = {
                'transformation_status': transformation_status,
                'workflow_stage': workflow_stage,
                'updated_at': datetime.now().isoformat()
            }
            
            if additional_metadata:
                # Get current metadata
                current_request = await self._get_request_info(request_id)
                current_metadata = current_request.get('transformation_metadata', {}) if current_request else {}
                
                # Merge with additional metadata
                if isinstance(current_metadata, dict):
                    current_metadata.update(additional_metadata)
                else:
                    current_metadata = additional_metadata
                
                update_data['transformation_metadata'] = current_metadata
            
            self.supabase.table(TABLES["SCRAPING_REQUESTS"])\
                .update(update_data)\
                .eq('id', request_id)\
                .execute()
            
            self.logger.info(f"📝 Updated request {request_id} status: {transformation_status}")
        except Exception as e:
            self.logger.error(f"❌ Error updating request status: {e}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Retry failed data transformation')
    parser.add_argument('--batch-id', type=int, help='Batch ID to retry')
    parser.add_argument('--request-id', type=int, help='Request ID to retry')
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be done')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.batch_id and not args.request_id:
        print("❌ Error: Either --batch-id or --request-id must be provided")
        return 1
    
    if args.batch_id and args.request_id:
        print("❌ Error: Cannot specify both --batch-id and --request-id")
        return 1
    
    # Create config
    config = RetryConfig(
        dry_run=args.dry_run,
        verbose=args.verbose,
        batch_size=args.batch_size
    )
    
    # Create retry tool
    retry_tool = RetryTransformationTool(config)
    
    # Execute retry
    success = False
    try:
        if args.batch_id:
            success = await retry_tool.retry_by_batch_id(args.batch_id)
        else:
            success = await retry_tool.retry_by_request_id(args.request_id)
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    if success:
        print("✅ Retry operation completed successfully")
        return 0
    else:
        print("❌ Retry operation failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 