"""API endpoints for data transformation operations."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .services.transformation_service import DataTransformationService
from .models import TransformationConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data-transformation", tags=["data-transformation"])


class TransformationRequest(BaseModel):
    """Request model for data transformation."""
    limit: Optional[int] = None
    batch_size: int = 100
    skip_existing: bool = True
    validate_calculations: bool = True
    dry_run: bool = False


class TransformationResponse(BaseModel):
    """Response model for transformation results."""
    success: bool
    processed_count: int
    skipped_count: int
    error_count: int
    duration_seconds: float
    summary: dict
    errors: list


@router.post("/transform", response_model=TransformationResponse)
async def transform_data(request: TransformationRequest):
    """Transform amazon_products data to product_wide_table format.
    
    Args:
        request: Transformation configuration
        
    Returns:
        Transformation result with statistics
    """
    try:
        # Create configuration
        config = TransformationConfig(
            batch_size=request.batch_size,
            skip_existing=request.skip_existing,
            validate_calculations=request.validate_calculations,
            dry_run=request.dry_run
        )
        
        # Execute transformation
        service = DataTransformationService(config)
        result = service.transform_batch(request.limit)
        
        logger.info(f"Transformation completed: {result.processed_count} processed, "
                   f"{result.error_count} errors")
        
        return TransformationResponse(
            success=result.success,
            processed_count=result.processed_count,
            skipped_count=result.skipped_count,
            error_count=result.error_count,
            duration_seconds=result.duration_seconds,
            summary=result.summary,
            errors=result.errors
        )
        
    except Exception as e:
        logger.error(f"Transformation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_transformation_stats():
    """Get statistics about transformation coverage.
    
    Returns:
        Transformation statistics
    """
    try:
        service = DataTransformationService()
        stats = service.get_transformation_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_transformation():
    """Validate existing transformed data quality.
    
    Returns:
        Validation results
    """
    try:
        # This would implement validation of existing data
        # For now, return placeholder
        return {
            "success": True,
            "message": "Validation endpoint not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Validation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 