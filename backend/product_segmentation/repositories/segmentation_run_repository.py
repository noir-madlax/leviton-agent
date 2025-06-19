"""
Repository for segmentation run data access
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging
from backend.product_segmentation.models import (
    SegmentationRun,
    SegmentationRunCreate,
    SegmentationStatus,
)
import json

logger = logging.getLogger(__name__)


class SegmentationRunRepository:
    """Repository for segmentation run data access"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.table_name = 'segmentation_runs'
    
    async def _ensure_table_exists(self) -> None:
        """Ensure the segmentation_runs table exists."""
        try:
            # Check if table exists by attempting to select from it
            self.client.table(self.table_name).select("id").limit(1).execute()
            logger.debug("✅ Table %s exists", self.table_name)
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Table %s does not exist, attempting to create: %s", self.table_name, e)
            try:
                # Create table with minimal schema, just enough to store the run
                self.client.table(self.table_name).create({
                    "id": "text primary key",
                    "status": "text not null",
                    "total_products": "integer",
                    "processed_products": "integer",
                    "llm_config": "jsonb",
                    "processing_params": "jsonb",
                    "result_summary": "jsonb",
                    "created_at": "timestamp with time zone default now()",
                    "updated_at": "timestamp with time zone default now()"
                }).execute()
                logger.info("✅ Created table %s", self.table_name)
            except Exception as create_error:  # pylint: disable=broad-except
                logger.error("Failed to create table %s: %s", self.table_name, create_error)
                raise

    async def create(self, run_data: SegmentationRunCreate) -> Optional[SegmentationRun]:
        """
        Create a new segmentation run
        
        Args:
            run_data: Run data to create
            
        Returns:
            Created run or None if failed
        """
        try:
            await self._ensure_table_exists()
            
            # Convert to dict and handle JSON fields
            data_dict = run_data.dict()
            json_cols = ['llm_config', 'processing_params', 'result_summary']
            
            # Convert dict fields to JSON strings for storage
            payload = {
                k: json.dumps(v) if k in json_cols and v is not None else v
                for k, v in data_dict.items()
            }
            
            payload_list = [payload]
            logger.debug("⏩ Inserting segmentation_run payload after JSON conversion: %s", payload_list)
            
            try:
                result = self.client.table(self.table_name).insert(payload_list).execute()
                if result.data:
                    # Convert JSON strings back to dicts before creating SegmentationRun
                    row = result.data[0]
                    for col in json_cols:
                        if col in row and isinstance(row[col], str):
                            try:
                                row[col] = json.loads(row[col])
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode JSON for {col}, leaving as string")
                    return SegmentationRun(**row)
                return None
            except Exception as first_exc:  # pylint: disable=broad-except
                logger.warning("Primary insert with JSON columns failed: %s – retry without JSONB fields", first_exc)
                minimal_payload = [
                    {k: v for k, v in payload.items() if k not in json_cols}
                ]
                logger.debug("⏩ Fallback minimal payload without JSON columns: %s", minimal_payload)
                result = self.client.table(self.table_name).insert(minimal_payload).execute()
                if result.data:
                    return SegmentationRun(**result.data[0])
                return None

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to create segmentation run: %s", e)
            return None
                
    
    async def get_by_id(self, run_id: str) -> Optional[SegmentationRun]:
        """
        Get segmentation run by ID
        
        Args:
            run_id: Run identifier
            
        Returns:
            Segmentation run or None if not found
        """
        try:
            result = self.client.table(self.table_name).select("*").eq('id', run_id).execute()
            
            if result.data and len(result.data) > 0:
                # Convert JSON strings back to dicts
                row = result.data[0]
                json_cols = ['llm_config', 'processing_params', 'result_summary']
                for col in json_cols:
                    if col in row and isinstance(row[col], str):
                        try:
                            row[col] = json.loads(row[col])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON for {col}, leaving as string")
                return SegmentationRun(**row)
            else:
                logger.warning(f"Segmentation run not found: {run_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting segmentation run: {e}")
            return None
    
    async def update_status(self, run_id: str, status: SegmentationStatus) -> bool:
        """
        Update run status
        
        Args:
            run_id: Run identifier
            status: New status
            
        Returns:
            True if updated successfully
        """
        try:
            result = self.client.table(self.table_name)\
                .update({"status": status.value})\
                .eq('id', run_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Updated run {run_id} status to {status.value}")
                return True
            else:
                logger.error(f"Failed to update run status: {run_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating run status: {e}")
            return False
    
    async def update_progress(self, run_id: str, processed_products: int, total_products: Optional[int] = None) -> bool:
        """Update run progress.

        Parameters
        ----------
        run_id
            The run ID to update.
        processed_products
            Number of products processed so far.
        total_products
            Optional total number of products to process.
        """
        try:
            update_data = {"processed_products": processed_products}
            if total_products is not None:
                update_data["total_products"] = total_products

            result = await self.client.table(self.table_name).update(update_data).eq("id", run_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error("Failed to update run progress: %s", e)
            return False
    
    async def complete_run(self, run_id: str, result_summary: Dict[str, Any]) -> bool:
        """
        Complete a segmentation run
        
        Args:
            run_id: Run identifier
            result_summary: Summary of results
            
        Returns:
            True if completed successfully
        """
        try:
            result = self.client.table(self.table_name)\
                .update({
                    "status": SegmentationStatus.COMPLETED.value,
                    "result_summary": json.dumps(result_summary)
                })\
                .eq('id', run_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Completed segmentation run: {run_id}")
                return True
            else:
                logger.error(f"Failed to complete run: {run_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error completing run: {e}")
            return False
    
    async def get_recent_runs(self, limit: int = 10) -> List[SegmentationRun]:
        """
        Get recent segmentation runs
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of recent runs
        """
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            if result.data:
                runs = []
                json_cols = ['llm_config', 'processing_params', 'result_summary']
                for row in result.data:
                    # Convert JSON strings back to dicts
                    for col in json_cols:
                        if col in row and isinstance(row[col], str):
                            try:
                                row[col] = json.loads(row[col])
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode JSON for {col}, leaving as string")
                    runs.append(SegmentationRun(**row))
                return runs
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting recent runs: {e}")
            return []
    
    async def get_runs_by_status(self, status: SegmentationStatus) -> List[SegmentationRun]:
        """
        Get runs by status
        
        Args:
            status: Status to filter by
            
        Returns:
            List of runs with specified status
        """
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq('status', status.value)\
                .order('created_at', desc=True)\
                .execute()
            
            if result.data:
                runs = []
                json_cols = ['llm_config', 'processing_params', 'result_summary']
                for row in result.data:
                    # Convert JSON strings back to dicts
                    for col in json_cols:
                        if col in row and isinstance(row[col], str):
                            try:
                                row[col] = json.loads(row[col])
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode JSON for {col}, leaving as string")
                    runs.append(SegmentationRun(**row))
                return runs
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting runs by status: {e}")
            return []
    
    async def delete(self, run_id: str) -> bool:
        """Delete a run and all its related data.

        This will cascade delete all related data in other tables due to
        foreign key constraints.
        """
        try:
            result = (
                self.client.table(self.table_name)
                .delete()
                .eq("id", run_id)
                .execute()
            )
            if result.data and len(result.data) > 0:
                logger.info("Deleted run %s", run_id)
                return True
            logger.error("Failed to delete run %s – empty response", run_id)
            return False
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error deleting run %s: %s", run_id, exc)
            return False 