"""
Repository for product segment data access
"""
from typing import Optional, List
from supabase import Client
import logging
from product_segmentation.models import (
    ProductSegment,
    ProductSegmentCreate,
    RunProduct,
    RunProductCreate,
    RefinedProductSegment,
    RefinedProductSegmentCreate,
)

logger = logging.getLogger(__name__)


class ProductSegmentRepository:
    """Repository for product segment data access"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.segments_table = 'product_segments'
        self.refined_segments_table = 'refined_product_segments'
        self.run_products_table = 'run_products'
    
    async def add_products_to_run(self, run_id: str, product_ids: List[int]) -> bool:
        """
        Add products to a segmentation run
        
        Args:
            run_id: Run identifier
            product_ids: List of product IDs to add
            
        Returns:
            True if added successfully
        """
        try:
            # Prepare batch insert data
            run_products = [
                {"run_id": run_id, "product_id": pid}
                for pid in product_ids
            ]
            
            result = self.client.table(self.run_products_table).insert(run_products).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Added {len(result.data)} products to run {run_id}")
                return True
            else:
                logger.error(f"Failed to add products to run: {run_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding products to run: {e}")
            return False
    
    async def get_run_products(self, run_id: str) -> List[int]:
        """
        Get product IDs for a run
        
        Args:
            run_id: Run identifier
            
        Returns:
            List of product IDs
        """
        try:
            result = self.client.table(self.run_products_table)\
                .select("product_id")\
                .eq('run_id', run_id)\
                .execute()
            
            if result.data:
                return [row['product_id'] for row in result.data]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting run products: {e}")
            return []
    
    async def batch_create_segments(self, segments: List[ProductSegmentCreate]) -> bool:
        """
        Batch create product segments
        
        Args:
            segments: List of segment creation data
            
        Returns:
            True if created successfully
        """
        try:
            # Exclude optional columns that may not exist in the DB schema
            segment_data = []
            for s in segments:
                row = s.dict(exclude_none=True)
                # `category_name` is not present in *product_segments*
                row.pop("category_name", None)
                segment_data.append(row)

            result = self.client.table(self.segments_table).insert(segment_data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Created {len(result.data)} product segments")
                return True
            else:
                logger.error("Failed to create product segments")
                return False
                
        except Exception as e:
            logger.error(f"Error creating product segments: {e}")
            return False
    
    async def get_segments_by_run(self, run_id: str) -> List[ProductSegment]:
        """
        Get all segments for a run
        
        Args:
            run_id: Run identifier
            
        Returns:
            List of product segments
        """
        try:
            result = self.client.table(self.segments_table)\
                .select("*")\
                .eq('run_id', run_id)\
                .execute()
            
            if result.data:
                return [ProductSegment.parse_obj(row) for row in result.data]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting segments by run: {e}")
            return []
    
    async def get_segments_by_product(self, product_id: int) -> List[ProductSegment]:
        """
        Get all segments for a product across runs
        
        Args:
            product_id: Product identifier
            
        Returns:
            List of product segments
        """
        try:
            result = self.client.table(self.segments_table)\
                .select("*")\
                .eq('product_id', product_id)\
                .order('created_at', desc=True)\
                .execute()
            
            if result.data:
                return [ProductSegment.parse_obj(row) for row in result.data]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting segments by product: {e}")
            return []
    
    async def get_segment(self, run_id: str, product_id: int) -> Optional[ProductSegment]:
        """
        Get specific product segment
        
        Args:
            run_id: Run identifier
            product_id: Product identifier
            
        Returns:
            Product segment or None if not found
        """
        try:
            result = self.client.table(self.segments_table)\
                .select("*")\
                .eq('run_id', run_id)\
                .eq('product_id', product_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return ProductSegment.parse_obj(result.data[0])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting segment: {e}")
            return None
    
    async def delete_segments_by_run(self, run_id: str) -> bool:
        """
        Delete all segments for a run
        
        Args:
            run_id: Run identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = (
                self.client.table(self.segments_table)
                .delete()
                .eq("run_id", run_id)
                .execute()
            )
            return bool(result.data)
            
        except Exception as exc:
            logger.exception("Failed to delete segments: %s", exc)
            return False
    
    async def batch_create_refined_segments(
        self, segments: List[RefinedProductSegmentCreate]
    ) -> bool:
        """
        Create multiple refined product segments in one call
        
        Args:
            segments: List of refined segment objects to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            segment_dicts = []
            for s in segments:
                row = s.dict(exclude_none=True)
                row.pop("category_name", None)
                segment_dicts.append(row)

            result = (
                self.client.table(self.refined_segments_table)
                .insert(segment_dicts)
                .execute()
            )
            return bool(result.data)
            
        except Exception as exc:
            logger.exception("Failed to create refined segments: %s", exc)
            return False

    async def get_refined_segments_by_run(self, run_id: str) -> List[RefinedProductSegment]:
        """
        Get all refined segments for a run
        
        Args:
            run_id: Run identifier
            
        Returns:
            List[RefinedProductSegment]: List of refined segments
        """
        try:
            result = (
                self.client.table(self.refined_segments_table)
                .select("*")
                .eq("run_id", run_id)
                .execute()
            )
            return [RefinedProductSegment(**row) for row in result.data] if result.data else []
            
        except Exception as exc:
            logger.exception("Failed to get refined segments: %s", exc)
            return []

    async def create_run_products(self, run_id: str, product_ids: List[int]) -> bool:
        """Create product list for a run.

        Parameters
        ----------
        run_id
            The run ID to create products for.
        product_ids
            List of product IDs to create.

        Returns
        -------
        bool
            True if created successfully.
        """
        try:
            # Create a list of product IDs for this run
            products = [{"run_id": run_id, "product_id": pid} for pid in product_ids]
            result = self.client.table("run_products").insert(products).execute()
            return bool(result.data)
        except Exception as e:
            logger.error("Failed to create run products: %s", e)
            return False 