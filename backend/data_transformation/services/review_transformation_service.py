"""Review transformation service for converting amazon_reviews to product_reviews."""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.database.connection import get_supabase_client
from ..models import TransformationResult, TransformationConfig
from ..validators.data_validator import DataValidator

logger = logging.getLogger(__name__)


class ReviewTransformationService:
    """Service for transforming amazon_reviews data to product_reviews format."""
    
    def __init__(self, config: Optional[TransformationConfig] = None):
        """Initialize review transformation service.
        
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
        """Transform a batch of reviews from amazon_reviews to product_reviews.
        
        Args:
            limit: Maximum number of reviews to process
            
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
                logger.warning("No source review data found to transform")
                return TransformationResult(
                    success=True,
                    processed_count=0,
                    skipped_count=0,
                    error_count=0,
                    errors=[],
                    duration_seconds=time.time() - start_time,
                    summary={"message": "No review data to process"}
                )
            
            logger.info(f"Found {len(source_data)} reviews to transform")
            
            # Process in batches
            batch_size = self.config.batch_size
            for i in range(0, len(source_data), batch_size):
                batch = source_data[i:i + batch_size]
                batch_result = self._process_batch(batch)
                
                processed_count += batch_result['processed']
                skipped_count += batch_result['skipped']
                error_count += batch_result['errors']
                errors.extend(batch_result['error_messages'])
                
                logger.info(f"Processed review batch {i//batch_size + 1}: "
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
            logger.error(f"Review transformation failed: {e}")
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
        """Get source data from amazon_reviews table.
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            List of review records
        """
        try:
            query = self.supabase.table('amazon_reviews').select('*')
            
            # Apply filters for quality data
            query = query.neq('asin', None)
            query = query.neq('review_id', None)
            
            # Skip existing if configured  
            if self.config.skip_existing:
                # For now, we'll handle duplicates at application level
                # Future: implement proper skip logic if needed
                logger.info("Skip existing is enabled, will handle duplicates carefully")
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Order by scrape_date for consistent processing
            query = query.order('scrape_date', desc=True)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get review source data: {e}")
            return []
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a batch of reviews.
        
        Args:
            batch: List of review records
            
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
                transformed = self._transform_single_review(record)
                
                if transformed:
                    # Validate transformed data
                    if self._validate_review_data(transformed):
                        transformed_data.append(transformed)
                        processed += 1
                    else:
                        error_messages.append(f"Validation failed for review {record.get('review_id', 'unknown')}")
                        errors += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                error_messages.append(f"Transform error for review {record.get('review_id', 'unknown')}: {str(e)}")
                errors += 1
                logger.warning(f"Failed to transform review {record.get('review_id', 'unknown')}: {e}")
        
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
    
    def _transform_single_review(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform a single review record.
        
        Args:
            record: Source review record
            
        Returns:
            Transformed review data or None if skipped
        """
        try:
            # Extract basic fields
            asin = record.get('asin')
            review_id = record.get('review_id')
            
            if not asin or not review_id:
                logger.warning(f"Missing required fields: asin={asin}, review_id={review_id}")
                return None
            
            # Build transformed data
            transformed = {
                # Map review_id as integer (product_reviews uses integer)
                'review_id': int(review_id) if str(review_id).isdigit() else hash(review_id) % 2147483647,
                'product_id': asin,  # asin -> product_id
                'review_text': record.get('review_text'),
                'review_title': record.get('review_title'),
                'rating': record.get('rating'),
                'review_date': record.get('review_date'),
                'verified': record.get('verified'),
                'user_name': record.get('user_name'),
                'number_of_helpful': record.get('number_of_helpful'),
                'aspect_key': None,  # This will be filled by review analysis
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming review {record.get('review_id', 'unknown')}: {e}")
            return None
    
    def _validate_review_data(self, data: Dict[str, Any]) -> bool:
        """Validate transformed review data.
        
        Args:
            data: Transformed review data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not data.get('review_id') or not data.get('product_id'):
                return False
            
            # Validate review_id is integer
            if not isinstance(data.get('review_id'), int):
                return False
            
            # Validate product_id exists in product_wide_table
            if self.config.validate_calculations:
                product_result = self.supabase.table('product_wide_table')\
                    .select('platform_id')\
                    .eq('platform_id', data['product_id'])\
                    .limit(1)\
                    .execute()
                
                if not product_result.data:
                    logger.warning(f"Product {data['product_id']} not found in product_wide_table")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating review data: {e}")
            return False
    
    def _bulk_upsert(self, data: List[Dict[str, Any]]) -> None:
        """Bulk upsert review data to product_reviews table.
        
        Args:
            data: List of transformed review data
        """
        try:
            # Serialize data for JSON compatibility
            serialized_data = self._serialize_data_for_json(data)
            
            # Use insert instead of upsert to avoid constraint issues
            # Skip_existing logic is handled at query level
            result = self.supabase.table('product_reviews')\
                .insert(serialized_data)\
                .execute()
            
            logger.info(f"Successfully inserted {len(data)} reviews")
            
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            raise
    
    def _serialize_data_for_json(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Serialize data for JSON compatibility.
        
        Args:
            data: List of data dictionaries
            
        Returns:
            Serialized data list
        """
        serialized = []
        for item in data:
            serialized_item = {}
            for key, value in item.items():
                if value is None:
                    serialized_item[key] = None
                elif isinstance(value, (datetime,)):
                    serialized_item[key] = value.isoformat()
                else:
                    serialized_item[key] = value
            serialized.append(serialized_item)
        return serialized
    
    async def transform_batch_for_orchestrator(self, batch_id: int, request_id: Optional[int] = None) -> TransformationResult:
        """Transform reviews from a specific scraping batch for orchestrator integration.
        
        Args:
            batch_id: The batch ID from scraping process
            request_id: Optional scraping request ID for status updates
            
        Returns:
            Transformation result with batch-specific statistics
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting review transformation for batch_id: {batch_id}")
            
            # Update scraping request status to transforming
            if request_id:
                await self._update_scraping_request_status(
                    request_id, 
                    'transforming_reviews', 
                    'processing',
                    start_time
                )
            
            # Get reviews for specific batch
            source_data = self._get_batch_source_data(batch_id)
            
            if not source_data:
                logger.warning(f"No reviews found for batch_id: {batch_id}")
                result = TransformationResult(
                    success=True,
                    processed_count=0,
                    skipped_count=0,
                    error_count=0,
                    errors=[],
                    duration_seconds=time.time() - start_time,
                    summary={"message": f"No reviews found for batch_id: {batch_id}"}
                )
                
                if request_id:
                    await self._complete_scraping_request_transformation(request_id, result)
                
                return result
            
            logger.info(f"Found {len(source_data)} reviews to transform for batch_id: {batch_id}")
            
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
            
            logger.info(f"Batch {batch_id} review transformation completed: {result.processed_count} processed, {result.error_count} errors")
            return result
            
        except Exception as e:
            logger.error(f"Batch {batch_id} review transformation failed: {e}")
            
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
            List of review records for the batch
        """
        try:
            query = self.supabase.table('amazon_reviews').select('*')
            query = query.eq('scrape_batch_id', batch_id)
            query = query.neq('asin', None)
            query = query.neq('review_id', None)
            query = query.order('id')
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get batch review source data for batch_id {batch_id}: {e}")
            return []
    
    async def _update_scraping_request_status(self, request_id: int, workflow_stage: str, 
                                            transformation_status: str, start_time: float):
        """Update scraping request review transformation status."""
        try:
            update_data = {
                'workflow_stage': workflow_stage,
                'review_transformation_status': transformation_status,
                'review_transformation_started_at': datetime.fromtimestamp(start_time).isoformat()
            }
            
            self.supabase.table('scraping_requests')\
                .update(update_data)\
                .eq('id', request_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Failed to update scraping request review transformation status: {e}")
    
    async def _complete_scraping_request_transformation(self, request_id: int, result: TransformationResult):
        """Complete scraping request review transformation with results."""
        try:
            update_data = {
                'workflow_stage': 'completed' if result.success else 'failed',
                'review_transformation_status': 'completed' if result.success else 'failed',
                'review_transformation_completed_at': datetime.now().isoformat(),
                'review_transformation_duration_seconds': int(result.duration_seconds),
                'reviews_transformed': result.processed_count,
                'review_transformation_metadata': {
                    'summary': result.summary,
                    'errors': result.errors[:10]  # Limit errors to prevent large JSON
                }
            }
            
            self.supabase.table('scraping_requests')\
                .update(update_data)\
                .eq('id', request_id)\
                .execute()
                
        except Exception as e:
            logger.warning(f"Failed to complete scraping request {request_id} review transformation: {e}")
    
    async def _fail_scraping_request_transformation(self, request_id: int, error_message: str):
        """Fail scraping request review transformation with error."""
        try:
            update_data = {
                'workflow_stage': 'failed',
                'review_transformation_status': 'failed',
                'review_transformation_completed_at': datetime.now().isoformat(),
                'review_transformation_metadata': {
                    'error': error_message
                }
            }
            
            self.supabase.table('scraping_requests')\
                .update(update_data)\
                .eq('id', request_id)\
                .execute()
                
        except Exception as e:
            logger.warning(f"Failed to fail scraping request {request_id} review transformation: {e}")
    
    async def transform_batch_reviews(self, batch_id: int, config: Optional[TransformationConfig] = None, 
                                    limit: Optional[int] = None) -> TransformationResult:
        """Transform reviews for a specific batch_id with optional limit.
        
        This method is designed for legacy migration purposes.
        
        Args:
            batch_id: The scraping batch ID to process
            config: Optional transformation configuration
            limit: Optional limit on number of records to process
            
        Returns:
            TransformationResult with processing details
        """
        # Use provided config or instance config
        if config:
            old_config = self.config
            self.config = config
        
        start_time = time.time()
        processed_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        logger.info(f"🔄 Starting batch review transformation for batch_id: {batch_id}")
        
        try:
            # Get batch-specific source data
            source_data = self._get_batch_source_data_with_limit(batch_id, limit)
            
            if not source_data:
                logger.info(f"No source data found for batch_id: {batch_id}")
                return TransformationResult(
                    success=True,
                    processed_count=0,
                    skipped_count=0,
                    error_count=0,
                    errors=[],
                    duration_seconds=time.time() - start_time,
                    summary={"message": f"No data found for batch_id {batch_id}"}
                )
            
            logger.info(f"Found {len(source_data)} reviews in batch_id: {batch_id}")
            
            # Process in smaller batches
            batch_size = self.config.batch_size
            total_batches = (len(source_data) + batch_size - 1) // batch_size
            
            for i in range(0, len(source_data), batch_size):
                batch_num = i // batch_size + 1
                batch = source_data[i:i + batch_size]
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")
                
                batch_stats = self._process_batch(batch)
                
                processed_count += batch_stats['processed']
                skipped_count += batch_stats['skipped']
                error_count += batch_stats['errors']
                errors.extend(batch_stats['error_messages'])
                
                logger.info(f"Batch {batch_num} completed: {batch_stats['processed']} processed, {batch_stats['errors']} errors")
            
            duration = time.time() - start_time
            success = error_count < len(source_data) * 0.5  # Success if < 50% errors
            
            summary = {
                "batch_id": batch_id,
                "total_source_records": len(source_data),
                "processed_records": processed_count,
                "skipped_records": skipped_count,
                "error_records": error_count,
                "success_rate": round(processed_count / len(source_data) * 100, 2) if source_data else 0,
                "processing_speed": round(len(source_data) / duration, 2) if duration > 0 else 0,
                "limit_applied": limit is not None
            }
            
            logger.info(f"✅ Batch transformation completed for batch_id {batch_id}")
            logger.info(f"   📊 Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")
            logger.info(f"   ⏱️  Duration: {duration:.2f}s, Speed: {summary['processing_speed']:.1f} records/s")
            
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
            logger.error(f"❌ Batch review transformation failed for batch_id {batch_id}: {e}")
            return TransformationResult(
                success=False,
                processed_count=processed_count,
                skipped_count=skipped_count,
                error_count=error_count + 1,
                errors=errors + [str(e)],
                duration_seconds=time.time() - start_time,
                summary={"error": str(e), "batch_id": batch_id}
            )
        
        finally:
            # Restore original config if changed
            if config:
                self.config = old_config
    
    def _get_batch_source_data_with_limit(self, batch_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get source data for a specific batch with optional limit.
        
        Args:
            batch_id: The scraping batch ID
            limit: Optional limit on number of records
            
        Returns:
            List of review records
        """
        try:
            query = self.supabase.table('amazon_reviews').select('*')
            
            # Filter by batch_id
            query = query.eq('scrape_batch_id', batch_id)
            
            # Apply filters for quality data
            query = query.neq('asin', None)
            query = query.neq('review_id', None)
            
            # Skip existing if configured
            if self.config.skip_existing:
                # Get existing review_ids to skip
                existing_result = self.supabase.table('product_reviews')\
                    .select('review_id').execute()
                
                if existing_result.data:
                    existing_ids = [str(item['review_id']) for item in existing_result.data]
                    if existing_ids:
                        query = query.not_.in_('review_id', existing_ids)
                        logger.info(f"Skipping {len(existing_ids)} existing reviews")
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Order by created_at for consistent processing
            query = query.order('created_at', desc=False)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get batch source data for batch_id {batch_id}: {e}")
            return [] 