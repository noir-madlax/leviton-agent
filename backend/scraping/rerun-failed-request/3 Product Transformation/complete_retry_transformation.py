#!/usr/bin/env python3
"""
Complete Retry Failed Data Transformation Tool

This tool implements the complete retry functionality including
actual data transformation execution.
"""

import argparse
import asyncio
import sys
import os
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from decimal import Decimal
import re
import json

# Add parent directories to path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))  # rerun-failed-request
scraping_dir = os.path.dirname(current_dir)  # scraping
backend_dir = os.path.dirname(scraping_dir)  # backend
project_root = os.path.dirname(backend_dir)  # project root
sys.path.insert(0, project_root)

from supabase import create_client, Client
from backend.config import settings
from retry_config import (
    RetryConfig, 
    TransformationStatus, 
    WorkflowStage,
    TABLES,
    MAX_RECORDS_PER_BATCH,
    SUPPORTED_STATUSES
)


@dataclass
class TransformationResult:
    """Result of a transformation operation"""
    success: bool
    processed_count: int
    skipped_count: int
    error_count: int
    errors: List[str]
    duration_seconds: float
    summary: Dict[str, Any]


class CompleteRetryTransformationTool:
    """Complete tool for retrying failed data transformations"""
    
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
    
    async def _get_request_by_batch_id(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """Get request info by batch_id"""
        try:
            # First try to find products with this batch_id
            result = self.supabase.table(TABLES["AMAZON_PRODUCTS"])\
                .select("*")\
                .eq("batch_id", batch_id)\
                .limit(1)\
                .execute()
            
            if not result.data:
                self.logger.warning(f"No products found for batch_id: {batch_id}")
                return None
            
            # Count total products in this batch
            count_result = self.supabase.table(TABLES["AMAZON_PRODUCTS"])\
                .select("*", count="exact")\
                .eq("batch_id", batch_id)\
                .execute()
            
            total_products = count_result.count if count_result.count else 0
            
            # Try to find the scraping request with matching product count
            requests_result = self.supabase.table(TABLES["SCRAPING_REQUESTS"])\
                .select("*")\
                .eq("products_scraped", total_products)\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()
            
            if requests_result.data:
                # Find the most likely match - prefer failed transformations
                for request in requests_result.data:
                    if request.get("transformation_status") == TransformationStatus.FAILED:
                        return request
                
                # If no failed transformation found, return the first one
                return requests_result.data[0]
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting request for batch_id {batch_id}: {e}")
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
        
        # Step 4: Execute retry
        if self.config.dry_run:
            self.logger.info(f"✅ DRY RUN: Would retry transformation for batch {batch_id}")
            self.logger.info(f"✅ DRY RUN: All validations passed, ready for actual retry")
            return True
        
        return await self._execute_transformation(request_id, batch_id)
    
    async def _execute_transformation(self, request_id: int, batch_id: int) -> bool:
        """Execute the actual transformation"""
        try:
            self.logger.info(f"🚀 Starting transformation execution for batch {batch_id}")
            start_time = time.time()
            
            # Update status to processing
            await self._update_request_status(
                request_id, 
                TransformationStatus.PROCESSING, 
                WorkflowStage.TRANSFORMING
            )
            
            # Get source data with deduplication
            source_data = await self._get_deduplicated_source_data(batch_id)
            
            if not source_data:
                self.logger.error(f"❌ No valid source data found for batch {batch_id}")
                await self._update_request_status(
                    request_id, 
                    TransformationStatus.FAILED, 
                    WorkflowStage.FAILED,
                    {'error': 'No valid source data found'}
                )
                return False
            
            self.logger.info(f"📊 Processing {len(source_data)} deduplicated records")
            
            # Transform data
            transformed_data = []
            processed_count = 0
            error_count = 0
            errors = []
            
            for record in source_data:
                try:
                    transformed = await self._transform_single_product(record)
                    if transformed:
                        transformed_data.append(transformed)
                        processed_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Failed to transform product {record.get('platform_id', 'unknown')}")
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error transforming {record.get('platform_id', 'unknown')}: {str(e)}")
                    self.logger.warning(f"Failed to transform product {record.get('platform_id', 'unknown')}: {e}")
            
            # Bulk insert transformed data
            if transformed_data:
                await self._bulk_upsert(transformed_data)
                self.logger.info(f"✅ Successfully inserted {len(transformed_data)} records")
            
            # Calculate results
            duration = time.time() - start_time
            success = processed_count > 0 and error_count < len(source_data) * 0.5
            
            summary = {
                'processed_count': processed_count,
                'error_count': error_count,
                'success_rate': round(processed_count / len(source_data) * 100, 2) if source_data else 0,
                'duration_seconds': round(duration, 2),
                'total_source_records': len(source_data)
            }
            
            # Update final status
            final_status = TransformationStatus.COMPLETED if success else TransformationStatus.FAILED
            final_stage = WorkflowStage.COMPLETED if success else WorkflowStage.FAILED
            
            await self._update_request_status(
                request_id,
                final_status,
                final_stage,
                {
                    'retry_success': success,
                    'retry_timestamp': datetime.now().isoformat(),
                    'retry_summary': summary,
                    'retry_errors': errors[:5] if errors else []
                }
            )
            
            # Update products_transformed count
            if success:
                await self._update_products_transformed_count(request_id, processed_count)
            
            if success:
                self.logger.info(f"✅ Transformation completed successfully")
                self.logger.info(f"📊 Processed {processed_count} records in {duration:.2f}s")
                return True
            else:
                self.logger.error(f"❌ Transformation failed")
                self.logger.error(f"Errors: {errors[:3]}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error executing transformation: {e}")
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
    
    async def _get_deduplicated_source_data(self, batch_id: int) -> List[Dict[str, Any]]:
        """Get source data with deduplication"""
        try:
            # Get all records for this batch
            result = self.supabase.table(TABLES["AMAZON_PRODUCTS"])\
                .select("*")\
                .eq("batch_id", batch_id)\
                .neq("platform_id", None)\
                .neq("title", None)\
                .order("id", desc=True)\
                .execute()
            
            if not result.data:
                return []
            
            # Deduplicate by platform_id, keeping the first occurrence (most recent due to DESC order)
            seen_platform_ids = set()
            deduped_data = []
            
            for record in result.data:
                platform_id = record.get('platform_id')
                if platform_id and platform_id not in seen_platform_ids:
                    seen_platform_ids.add(platform_id)
                    deduped_data.append(record)
            
            if len(result.data) != len(deduped_data):
                self.logger.info(f"🔄 Deduplicated {len(result.data)} records to {len(deduped_data)} records")
            
            return deduped_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting deduplicated source data: {e}")
            return []
    
    async def _transform_single_product(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform a single product record"""
        try:
            # Extract basic fields
            platform_id = record.get('platform_id')
            title = record.get('title')
            
            if not platform_id or not title:
                self.logger.warning(f"Missing required fields: platform_id={platform_id}, title='{title}'")
                return None
            
            # Build transformed data with all required fields from original service
            transformed = {
                # Direct mappings
                'source': 'amazon',
                'platform_id': platform_id,
                'title': title,
                'brand': record.get('brand'),
                'model_number': record.get('model_number'),
                'category': record.get('category'),
                'image_url': record.get('image_url'),
                'product_url': record.get('product_url'),
                'availability': record.get('availability'),
                'collection': record.get('collection'),
                'delivery_free': record.get('delivery_free'),
                'pickup_available': record.get('pickup_available'),
                'features': record.get('features'),
                'description': record.get('description'),
                'extract_date': record.get('extract_date'),
                'is_bestseller': record.get('is_bestseller'),
                'unit_price': record.get('unit_price'),
                
                # Price fields
                'price_usd': self._safe_decimal_conversion(record.get('price_usd')),
                'list_price_usd': self._safe_decimal_conversion(record.get('list_price_usd')),
                'rating': self._safe_float_conversion(record.get('rating')),
                'reviews_count': self._safe_int_conversion(record.get('reviews_count')),
                'position': record.get('position') or 0,  # Default to 0 if position is null
                'recent_sales': record.get('recent_sales'),
                
                # Calculated fields - simplified without complex parsers
                'monthly_sales_volume': None,  # Would need SalesVolumeParser
                'estimated_revenue': None,     # Would need calculation
                'pack_count': 1,               # Default to 1
                'unit_price_calculated': None, # Would need calculation
                'unit_price_numeric': None,    # Would need calculation
                'estimated_volume': None,      # Would need calculation
                'cleaned_title': title,        # Simplified
                
                # Additional fields from amazon_products
                'batch_id': record.get('batch_id'),
                'leaf_category_id': record.get('leaf_category_id'),
                'leaf_category_name': record.get('leaf_category_name'),
                'categories_flat': record.get('categories_flat'),
                
                # Default/placeholder fields
                'product_segment': record.get('product_segment'),
                'refined_category': record.get('refined_category'),
                'category_definition': record.get('category_definition'),
            }
            
            # Extract category hierarchy information using same logic as original
            category_hierarchy = record.get('category_hierarchy')
            if category_hierarchy:
                hierarchy_data = self._extract_category_hierarchy_from_json(category_hierarchy)
            else:
                # Fallback to categories_flat
                hierarchy_data = self._extract_category_hierarchy_from_flat(record.get('categories_flat'))
            
            transformed.update(hierarchy_data)
            
            return transformed
            
        except Exception as e:
            self.logger.error(f"Error transforming product {record.get('platform_id', 'unknown')}: {e}")
            return None
    
    def _extract_category_hierarchy_from_json(self, category_hierarchy: Union[str, Dict, List]) -> Dict[str, Any]:
        """Extract category hierarchy from JSON data using same logic as original service"""
        hierarchy_data = {
            'category_l1_id': None,
            'category_l2_id': None,
            'category_l3_id': None,
            'category_l4_id': None,
            'category_l5_id': None,
            'category_l6_id': None,
            'category_deepest_level': 0
        }
        
        try:
            # Parse the category hierarchy if it's a string
            if isinstance(category_hierarchy, str):
                try:
                    category_data = json.loads(category_hierarchy)
                except json.JSONDecodeError:
                    return hierarchy_data
            else:
                category_data = category_hierarchy
            
            # Extract from category_hierarchy structure
            if isinstance(category_data, dict) and 'categories' in category_data:
                categories = category_data['categories']
                
                if isinstance(categories, list) and categories:
                    # Extract category IDs by level
                    for i, category in enumerate(categories[:6]):  # Max 6 levels
                        if isinstance(category, dict) and 'category_id' in category:
                            level = i + 1
                            category_id = str(category['category_id'])
                            
                            hierarchy_data[f'category_l{level}_id'] = category_id
                            hierarchy_data['category_deepest_level'] = level
                            
                            self.logger.debug(f"Extracted L{level}: {category.get('name', 'Unknown')} -> {category_id}")
                    
                    self.logger.debug(f"Extracted {hierarchy_data['category_deepest_level']} levels from category_hierarchy")
            
        except Exception as e:
            self.logger.error(f"Failed to extract category hierarchy from JSON: {e}")
        
        return hierarchy_data
    
    def _extract_category_hierarchy_from_flat(self, categories_flat: Optional[str]) -> Dict[str, Any]:
        """Extract category hierarchy from flat string (fallback method)"""
        hierarchy_data = {
            'category_l1_id': None,
            'category_l2_id': None,
            'category_l3_id': None,
            'category_l4_id': None,
            'category_l5_id': None,
            'category_l6_id': None,
            'category_deepest_level': 0
        }
        
        if not categories_flat:
            return hierarchy_data
        
        try:
            # Parse categories_flat path
            category_names = [name.strip() for name in categories_flat.split(' > ')]
            
            if not category_names:
                return hierarchy_data
            
            # Query database for category IDs
            result = self.supabase.table('amazon_categories')\
                .select('name, category_id, level')\
                .in_('name', category_names)\
                .execute()
            
            if not result.data:
                self.logger.debug(f"No category IDs found for names: {category_names}")
                return hierarchy_data
            
            # Build name to ID mapping
            name_to_id_map = {}
            for cat in result.data:
                name_to_id_map[cat['name']] = {
                    'category_id': str(cat['category_id']),
                    'level': cat.get('level', 0)
                }
            
            # Extract hierarchy information by order
            for i, category_name in enumerate(category_names[:6]):  # Max 6 levels
                if category_name in name_to_id_map:
                    level = i + 1  # Position-based level
                    category_id = name_to_id_map[category_name]['category_id']
                    
                    hierarchy_data[f'category_l{level}_id'] = category_id
                    hierarchy_data['category_deepest_level'] = level
                    
                    self.logger.debug(f"Mapped L{level}: {category_name} -> {category_id}")
                else:
                    self.logger.debug(f"Category not found in database: {category_name}")
            
            self.logger.debug(f"Extracted hierarchy: {hierarchy_data['category_deepest_level']} levels")
            
        except Exception as e:
            self.logger.error(f"Failed to extract category hierarchy from '{categories_flat}': {e}")
        
        return hierarchy_data
    
    def _safe_decimal_conversion(self, value) -> Optional[float]:
        """Safely convert value to decimal/float for database storage"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Clean the string
                cleaned = re.sub(r'[^\d.-]', '', value)
                if cleaned:
                    return float(cleaned)
            
            return None
        except (ValueError, TypeError):
            return None

    def _extract_category_data(self, category_hierarchy: Union[str, Dict, List]) -> Dict[str, Any]:
        """Deprecated - use _extract_category_hierarchy_from_json instead"""
        return self._extract_category_hierarchy_from_json(category_hierarchy)
    
    def _safe_float_conversion(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Clean the string
                cleaned = re.sub(r'[^\d.-]', '', value)
                if cleaned:
                    return float(cleaned)
            
            return None
        except (ValueError, TypeError):
            return None
    
    def _safe_int_conversion(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if value is None:
            return None
        
        try:
            if isinstance(value, int):
                return value
            
            if isinstance(value, float):
                return int(value)
            
            if isinstance(value, str):
                # Clean the string
                cleaned = re.sub(r'[^\d]', '', value)
                if cleaned:
                    return int(cleaned)
            
            return None
        except (ValueError, TypeError):
            return None
    
    async def _bulk_upsert(self, data: List[Dict[str, Any]]) -> None:
        """Bulk upsert data to product_wide_table"""
        try:
            # Use upsert to handle duplicates
            self.supabase.table(TABLES["PRODUCT_WIDE_TABLE"])\
                .upsert(data, on_conflict="platform_id")\
                .execute()
            
            self.logger.info(f"✅ Bulk upserted {len(data)} records")
            
        except Exception as e:
            self.logger.error(f"❌ Bulk upsert failed: {e}")
            raise
    
    async def _update_products_transformed_count(self, request_id: int, count: int):
        """Update products_transformed count in scraping_requests"""
        try:
            self.supabase.table(TABLES["SCRAPING_REQUESTS"])\
                .update({'products_transformed': count})\
                .eq('id', request_id)\
                .execute()
            
            self.logger.info(f"📝 Updated products_transformed count to {count}")
        except Exception as e:
            self.logger.error(f"❌ Error updating products_transformed count: {e}")
    
    async def _validate_request_state(self, request_id: int, batch_id: int) -> bool:
        """Validate that the request is in a retryable state"""
        try:
            result = self.supabase.table(TABLES["SCRAPING_REQUESTS"])\
                .select("*")\
                .eq("id", request_id)\
                .single()\
                .execute()
            
            if not result.data:
                self.logger.error(f"❌ Request {request_id} not found")
                return False
            
            request_info = result.data
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
            
            # Check for duplicates
            platform_ids = [r.get('platform_id') for r in result.data if r.get('platform_id')]
            unique_platform_ids = len(set(platform_ids))
            duplicate_count = total_records - unique_platform_ids
            
            self.logger.info(f"📊 Source data: {total_records} total records, {valid_records} valid records")
            if duplicate_count > 0:
                self.logger.warning(f"⚠️ Found {duplicate_count} duplicate platform_id records")
                
                # Show duplicate details
                platform_id_counts = {}
                for pid in platform_ids:
                    platform_id_counts[pid] = platform_id_counts.get(pid, 0) + 1
                
                duplicates = {pid: count for pid, count in platform_id_counts.items() if count > 1}
                if duplicates:
                    self.logger.info(f"🔍 Duplicate platform_ids: {list(duplicates.keys())[:5]}...")
            
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
                current_result = self.supabase.table(TABLES["SCRAPING_REQUESTS"])\
                    .select("transformation_metadata")\
                    .eq("id", request_id)\
                    .single()\
                    .execute()
                
                current_metadata = current_result.data.get('transformation_metadata', {}) if current_result.data else {}
                
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
    parser = argparse.ArgumentParser(description='Complete retry failed data transformation')
    parser.add_argument('--batch-id', type=int, required=True, help='Batch ID to retry')
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be done')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Create config
    config = RetryConfig(
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    # Create retry tool
    retry_tool = CompleteRetryTransformationTool(config)
    
    # Execute retry
    success = False
    try:
        success = await retry_tool.retry_by_batch_id(args.batch_id)
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