"""Core data transformation service for converting amazon_products to product_wide_table."""

import logging
import time
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from core.database.connection import get_supabase_client
from ..models import TransformationResult, ProductTransformationData, TransformationConfig
from ..parsers import SalesVolumeParser, PackParser, PriceCalculator
from ..validators.data_validator import DataValidator

logger = logging.getLogger(__name__)


class DataTransformationService:
    """Service for transforming amazon_products data to product_wide_table format."""
    
    def __init__(self, config: Optional[TransformationConfig] = None):
        """Initialize transformation service.
        
        Args:
            config: Transformation configuration
        """
        self.config = config or TransformationConfig()
        self.supabase = get_supabase_client()
        self.validator = DataValidator()
        
        # Setup logging
        log_level = getattr(logging, self.config.log_level, logging.INFO)
        logger.setLevel(log_level)
    
    def transform_batch(self, limit: Optional[int] = None) -> TransformationResult:
        """Transform a batch of products from amazon_products to product_wide_table.
        
        Args:
            limit: Maximum number of products to process
            
        Returns:
            Transformation result with statistics
        """
        start_time = time.time()
        processed_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        try:
            # Get source data
            source_data = self._get_source_data(limit)
            
            if not source_data:
                logger.warning("No source data found to transform")
                return TransformationResult(
                    success=True,
                    processed_count=0,
                    skipped_count=0,
                    error_count=0,
                    errors=[],
                    duration_seconds=time.time() - start_time,
                    summary={"message": "No data to process"}
                )
            
            logger.info(f"Found {len(source_data)} products to transform")
            
            # Process in batches
            batch_size = self.config.batch_size
            for i in range(0, len(source_data), batch_size):
                batch = source_data[i:i + batch_size]
                batch_result = self._process_batch(batch)
                
                processed_count += batch_result['processed']
                skipped_count += batch_result['skipped']
                error_count += batch_result['errors']
                errors.extend(batch_result['error_messages'])
                
                logger.info(f"Processed batch {i//batch_size + 1}: "
                           f"{batch_result['processed']} processed, "
                           f"{batch_result['skipped']} skipped, "
                           f"{batch_result['errors']} errors")
            
            duration = time.time() - start_time
            success = error_count < len(source_data) * 0.5  # Success if < 50% errors
            
            summary = {
                "total_source_records": len(source_data),
                "processed_records": processed_count,
                "skipped_records": skipped_count,
                "error_records": error_count,
                "success_rate": round(processed_count / len(source_data) * 100, 2) if source_data else 0,
                "processing_speed": round(len(source_data) / duration, 2) if duration > 0 else 0
            }
            
            return TransformationResult(
                success=success,
                processed_count=processed_count,
                skipped_count=skipped_count,
                error_count=error_count,
                errors=errors,
                duration_seconds=duration,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            return TransformationResult(
                success=False,
                processed_count=processed_count,
                skipped_count=skipped_count,
                error_count=error_count + 1,
                errors=errors + [str(e)],
                duration_seconds=time.time() - start_time,
                summary={"error": str(e)}
            )
    
    def _get_source_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get source data from amazon_products table.
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            List of product records
        """
        try:
            query = self.supabase.table('amazon_products').select('*')
            
            # Apply filters for quality data
            query = query.neq('platform_id', None)
            query = query.neq('title', None)
            
            # Skip existing if configured
            if self.config.skip_existing:
                # Get existing platform_ids to skip
                existing_result = self.supabase.table('product_wide_table')\
                    .select('platform_id').execute()
                
                if existing_result.data:
                    existing_ids = [item['platform_id'] for item in existing_result.data]
                    if existing_ids:
                        query = query.not_.in_('platform_id', existing_ids)
                        logger.info(f"Skipping {len(existing_ids)} existing products")
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Order by extract_date for consistent processing
            query = query.order('extract_date', desc=True)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get source data: {e}")
            return []
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a batch of products.
        
        Args:
            batch: List of product records
            
        Returns:
            Processing statistics
        """
        processed = 0
        skipped = 0
        errors = 0
        error_messages = []
        transformed_data = []
        
        for record in batch:
            try:
                # Transform single record
                transformed = self._transform_single_product(record)
                
                if transformed:
                    # Validate transformed data
                    if self.validator.validate_product_data(transformed):
                        transformed_data.append(transformed)
                        processed += 1
                    else:
                        error_messages.append(f"Validation failed for {record.get('platform_id', 'unknown')}")
                        errors += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                error_messages.append(f"Transform error for {record.get('platform_id', 'unknown')}: {str(e)}")
                errors += 1
                logger.warning(f"Failed to transform product {record.get('platform_id', 'unknown')}: {e}")
        
        # Bulk insert/update if not dry run
        if transformed_data and not self.config.dry_run:
            try:
                self._bulk_upsert(transformed_data)
            except Exception as e:
                error_messages.append(f"Bulk insert failed: {str(e)}")
                errors += len(transformed_data)
                processed = 0
        
        return {
            'processed': processed,
            'skipped': skipped,
            'errors': errors,
            'error_messages': error_messages
        }
    
    def _transform_single_product(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform a single product record.
        
        Args:
            record: Source product record
            
        Returns:
            Transformed product data or None if skipped
        """
        try:
            # Extract basic fields
            platform_id = record.get('platform_id')
            title = record.get('title')
            
            if not platform_id or not title:
                logger.warning(f"Missing required fields: platform_id={platform_id}, title='{title}'")
                return None
            
            # Parse pack information
            pack_count = PackParser.parse_pack_count(title)
            cleaned_title = PackParser.extract_base_product_name(title)
            
            # Parse sales volume
            recent_sales = record.get('recent_sales')
            monthly_sales_volume = SalesVolumeParser.parse(recent_sales)
            
            # Convert price
            price_usd = PriceCalculator.safe_decimal_conversion(record.get('price_usd'))
            
            # Calculate prices
            list_price_usd, unit_price_calculated = PriceCalculator.estimate_list_price(
                price_usd, pack_count, title
            )
            
            # Calculate revenue
            estimated_revenue = PriceCalculator.calculate_estimated_revenue(
                price_usd, monthly_sales_volume
            )
            
            # Build transformed data
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
                'price_usd': price_usd,
                'list_price_usd': list_price_usd,
                'rating': self._safe_float_conversion(record.get('rating')),
                'reviews_count': self._safe_int_conversion(record.get('reviews_count')),
                'position': record.get('position') or 0,  # Default to 0 if position is null
                'recent_sales': recent_sales,
                
                # Calculated fields
                'monthly_sales_volume': monthly_sales_volume,
                'estimated_revenue': estimated_revenue,
                'pack_count': pack_count,
                'unit_price_calculated': unit_price_calculated,
                'unit_price_numeric': unit_price_calculated,  # Same as unit_price_calculated
                'estimated_volume': float(monthly_sales_volume) if monthly_sales_volume else None,
                'cleaned_title': cleaned_title,
                
                # Additional fields from amazon_products
                'batch_id': record.get('batch_id'),
                'leaf_category_id': record.get('leaf_category_id'),
                'leaf_category_name': record.get('leaf_category_name'),
                'categories_flat': record.get('categories_flat'),
                
                # Default/placeholder fields (will be set by product_segment module)
                'product_segment': record.get('product_segment'),  # Keep existing if present
                'refined_category': record.get('refined_category'),  # Keep existing if present
                'category_definition': record.get('category_definition'),  # Keep existing if present
            }
            
            # Log transformation details for debugging
            logger.debug(f"Transformed {platform_id}: pack_count={pack_count}, "
                        f"monthly_sales={monthly_sales_volume}, revenue={estimated_revenue}")
            
            return transformed
            
        except Exception as e:
            logger.error(f"Failed to transform product {record.get('platform_id', 'unknown')}: {e}")
            return None
    
    def _bulk_upsert(self, data: List[Dict[str, Any]]) -> None:
        """Bulk insert/update data to product_wide_table.
        
        Args:
            data: List of transformed product data
        """
        try:
            # Convert Decimal objects to float for JSON serialization
            serialized_data = self._serialize_data_for_json(data)
            
            # Use upsert to handle existing records
            result = self.supabase.table('product_wide_table')\
                .upsert(serialized_data, on_conflict='platform_id')\
                .execute()
            
            if result.data:
                logger.info(f"Successfully upserted {len(result.data)} records")
            else:
                logger.warning("Upsert completed but no data returned")
                
        except Exception as e:
            logger.error(f"Bulk upsert failed: {e}")
            raise
    
    def _serialize_data_for_json(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Decimal and other non-JSON-serializable objects for database insertion.
        
        Args:
            data: List of data dictionaries that may contain Decimal objects
            
        Returns:
            List of data dictionaries with JSON-serializable values
        """
        serialized_data = []
        
        for record in data:
            serialized_record = {}
            for key, value in record.items():
                if isinstance(value, Decimal):
                    # Convert Decimal to float
                    serialized_record[key] = float(value)
                elif isinstance(value, datetime):
                    # Convert datetime to ISO format string
                    serialized_record[key] = value.isoformat()
                elif value is None:
                    # Keep None values as-is
                    serialized_record[key] = None
                else:
                    # Keep other types as-is
                    serialized_record[key] = value
            
            serialized_data.append(serialized_record)
        
        return serialized_data
    
    def _safe_float_conversion(self, value):
        """Safely convert value to float.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value or None if conversion fails
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert '{value}' to float")
            return None
    
    def _safe_int_conversion(self, value):
        """Safely convert value to int.
        
        Args:
            value: Value to convert
            
        Returns:
            Int value or None if conversion fails
        """
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert '{value}' to int")
            return None

    def get_transformation_stats(self) -> Dict[str, Any]:
        """Get statistics about transformation coverage.
        
        Returns:
            Dictionary with transformation statistics
        """
        try:
            # Count source records
            source_result = self.supabase.table('amazon_products')\
                .select('platform_id', count='exact')\
                .execute()
            source_count = source_result.count or 0
            
            # Count transformed records
            target_result = self.supabase.table('product_wide_table')\
                .select('platform_id', count='exact')\
                .eq('source', 'amazon')\
                .execute()
            target_count = target_result.count or 0
            
            # Calculate coverage
            coverage_percent = round(target_count / source_count * 100, 2) if source_count > 0 else 0
            
            return {
                'source_records': source_count,
                'transformed_records': target_count,
                'coverage_percent': coverage_percent,
                'remaining_records': source_count - target_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get transformation stats: {e}")
            return {
                'error': str(e)
            }
    
    async def transform_batch_for_orchestrator(self, batch_id: int, request_id: Optional[int] = None) -> TransformationResult:
        """Transform products from a specific scraping batch for orchestrator integration.
        
        Args:
            batch_id: The batch ID from scraping process
            request_id: Optional scraping request ID for status updates
            
        Returns:
            Transformation result with batch-specific statistics
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting transformation for batch_id: {batch_id}")
            
            # Update scraping request status to transforming
            if request_id:
                await self._update_scraping_request_status(
                    request_id, 
                    'transforming', 
                    'processing',
                    start_time
                )
            
            # Get products for specific batch
            source_data = self._get_batch_source_data(batch_id)
            
            if not source_data:
                logger.warning(f"No products found for batch_id: {batch_id}")
                result = TransformationResult(
                    success=True,
                    processed_count=0,
                    skipped_count=0,
                    error_count=0,
                    errors=[],
                    duration_seconds=time.time() - start_time,
                    summary={"message": f"No products found for batch_id: {batch_id}"}
                )
                
                if request_id:
                    await self._complete_scraping_request_transformation(request_id, result)
                
                return result
            
            logger.info(f"Found {len(source_data)} products to transform for batch_id: {batch_id}")
            
            # Process the batch
            batch_result = self._process_batch(source_data)
            
            duration = time.time() - start_time
            success = batch_result['errors'] == 0
            
            result = TransformationResult(
                success=success,
                processed_count=batch_result['processed'],
                skipped_count=batch_result['skipped'],
                error_count=batch_result['errors'],
                errors=batch_result['error_messages'],
                duration_seconds=duration,
                summary={
                    "batch_id": batch_id,
                    "total_source_records": len(source_data),
                    "processed_records": batch_result['processed'],
                    "skipped_records": batch_result['skipped'],
                    "error_records": batch_result['errors'],
                    "success_rate": round(batch_result['processed'] / len(source_data) * 100, 2) if source_data else 0,
                    "processing_speed": round(len(source_data) / duration, 2) if duration > 0 else 0
                }
            )
            
            # Update scraping request status to completed
            if request_id:
                await self._complete_scraping_request_transformation(request_id, result)
            
            logger.info(f"Batch {batch_id} transformation completed: {result.processed_count} processed, {result.error_count} errors")
            return result
            
        except Exception as e:
            logger.error(f"Batch {batch_id} transformation failed: {e}")
            
            # Update scraping request status to failed
            if request_id:
                await self._fail_scraping_request_transformation(request_id, str(e))
            
            return TransformationResult(
                success=False,
                processed_count=0,
                skipped_count=0,
                error_count=1,
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
                summary={"error": str(e), "batch_id": batch_id}
            )
    
    def _get_batch_source_data(self, batch_id: int) -> List[Dict[str, Any]]:
        """Get source data for a specific batch.
        
        Args:
            batch_id: The batch ID to filter by
            
        Returns:
            List of product records for the batch
        """
        try:
            query = self.supabase.table('amazon_products').select('*')
            query = query.eq('batch_id', batch_id)
            query = query.neq('platform_id', None)
            query = query.neq('title', None)
            query = query.order('id')
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get batch source data for batch_id {batch_id}: {e}")
            return []
    
    async def _update_scraping_request_status(self, request_id: int, workflow_stage: str, 
                                            transformation_status: str, start_time: float):
        """Update scraping request transformation status."""
        try:
            update_data = {
                'workflow_stage': workflow_stage,
                'transformation_status': transformation_status,
                'transformation_started_at': datetime.fromtimestamp(start_time).isoformat()
            }
            
            self.supabase.table('scraping_requests')\
                .update(update_data)\
                .eq('id', request_id)\
                .execute()
                
        except Exception as e:
            logger.warning(f"Failed to update scraping request {request_id} status: {e}")
    
    async def _complete_scraping_request_transformation(self, request_id: int, result: TransformationResult):
        """Complete scraping request transformation with results."""
        try:
            update_data = {
                'workflow_stage': 'completed' if result.success else 'failed',
                'transformation_status': 'completed' if result.success else 'failed',
                'transformation_completed_at': datetime.now().isoformat(),
                'transformation_duration_seconds': int(result.duration_seconds),
                'products_transformed': result.processed_count,
                'transformation_metadata': {
                    'summary': result.summary,
                    'errors': result.errors[:10]  # Limit errors to prevent large JSON
                }
            }
            
            self.supabase.table('scraping_requests')\
                .update(update_data)\
                .eq('id', request_id)\
                .execute()
                
        except Exception as e:
            logger.warning(f"Failed to complete scraping request {request_id} transformation: {e}")
    
    async def _fail_scraping_request_transformation(self, request_id: int, error_message: str):
        """Mark scraping request transformation as failed."""
        try:
            update_data = {
                'workflow_stage': 'failed',
                'transformation_status': 'failed',
                'transformation_completed_at': datetime.now().isoformat(),
                'transformation_metadata': {
                    'error': error_message
                }
            }
            
            self.supabase.table('scraping_requests')\
                .update(update_data)\
                .eq('id', request_id)\
                .execute()
                
        except Exception as e:
            logger.warning(f"Failed to mark scraping request {request_id} as failed: {e}") 