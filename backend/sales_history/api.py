"""FastAPI routes for sales history service."""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from .models import (
    SalesHistoryScrapingRequest,
    SalesHistoryQueryRequest,
    SalesHistoryScrapingResponse,
    SalesHistoryQueryResponse,
    SalesHistoryMonthlyQueryResponse
)
from .services.sales_history_service import SalesHistoryService

# Import for project service
from core.database.connection import get_supabase_client

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/sales-history", tags=["sales-history"])

# Service instance
_sales_history_service: Optional[SalesHistoryService] = None

def get_sales_history_service() -> SalesHistoryService:
    """Get or create sales history service instance."""
    global _sales_history_service
    if _sales_history_service is None:
        _sales_history_service = SalesHistoryService()
    return _sales_history_service

@router.post("/scrape", response_model=SalesHistoryScrapingResponse)
async def scrape_sales_history(
    request: SalesHistoryScrapingRequest,
    service: SalesHistoryService = Depends(get_sales_history_service)
):
    """
    Scrape sales history data for multiple ASINs.
    
    This endpoint uses smart logic to:
    - Validate ASINs exist in product database
    - Check existing data coverage to avoid duplicate scraping
    - Apply date constraints (max 365 days back)
    - Return all available data if no date range specified
    
    **Smart Scraping Logic:**
    - If start_date and end_date are provided: Only scrape if we don't have complete coverage
    - If only start_date is provided: Scrape from start_date to yesterday
    - If only end_date is provided: Scrape from 365 days ago to end_date
    - If no dates provided: Scrape all available data (up to 365 days)
    
    **Response includes:**
    - Scraped data by ASIN
    - Summary of scraping results (scraped, skipped, failed)
    - Warnings for invalid ASINs or scraping errors
    """
    try:
        logger.info(f"Received scraping request for {len(request.asins)} ASINs")
        
        response = await service.scrape_sales_history(request)
        
        # Return appropriate HTTP status based on success
        if response.success:
            return response
        else:
            # If no ASINs were successfully processed, return 400
            if response.scraping_summary.scraped == 0 and response.scraping_summary.skipped == 0:
                return JSONResponse(
                    status_code=400,
                    content=response.dict()
                )
            # If some ASINs were processed but there were issues, return 207 (Multi-Status)
            return JSONResponse(
                status_code=207,
                content=response.dict()
            )
            
    except Exception as e:
        logger.error(f"Error in scrape_sales_history endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/scrape/project/{project_id}", response_model=SalesHistoryScrapingResponse)
async def scrape_project_sales_history(
    project_id: str,
    start_date: Optional[str] = Query(None, description="Start date for scraping (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for scraping (YYYY-MM-DD)"),
    platform_source: str = Query(default="amazon", description="Platform source (amazon, walmart, etc.)"),
    api_source: str = Query(default="jungle_scout", description="Data source API for scraping"),
    service: SalesHistoryService = Depends(get_sales_history_service)
):
    """
    Scrape sales history data for all products in a project.
    
    This endpoint automatically retrieves the selected_product_asins from the project
    and scrapes sales history for all those products.
    
    **Project-based Scraping:**
    - Retrieves selected_product_asins from the specified project
    - Validates that the project exists and has ASINs
    - Applies the same smart scraping logic as the regular scrape endpoint
    - Returns comprehensive results for all project products
    
    **Date Parameters:**
    - If start_date and end_date are provided: Only scrape if we don't have complete coverage
    - If only start_date is provided: Scrape from start_date to yesterday
    - If only end_date is provided: Scrape from 365 days ago to end_date
    - If no dates provided: Scrape all available data (up to 365 days)
    
    **Response includes:**
    - Scraped data by ASIN for all project products
    - Summary of scraping results (scraped, skipped, failed)
    - Warnings for invalid ASINs or scraping errors
    - Project information in the response
    """
    try:
        logger.info(f"Received project scraping request for project: {project_id}")
        
        # Get project ASINs from database
        supabase = get_supabase_client()
        project_result = supabase.table('projects').select('selected_product_asins, project_name').eq('id', project_id).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        project_data = project_result.data
        project_asins = project_data.get('selected_product_asins', [])
        project_name = project_data.get('project_name', 'Unknown Project')
        
        if not project_asins:
            raise HTTPException(
                status_code=400, 
                detail=f"Project {project_id} has no selected product ASINs"
            )
        
        logger.info(f"Found {len(project_asins)} ASINs in project {project_id}: {project_name}")
        
        # Convert date strings to date objects
        from datetime import date
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None
        
        # Create scraping request
        request = SalesHistoryScrapingRequest(
            asins=project_asins,
            start_date=start_date_obj,
            end_date=end_date_obj,
            platform_source=platform_source,
            api_source=api_source
        )
        
        # Call the existing scraping service
        response = await service.scrape_sales_history(request)
        
        # Add project information to the response
        response_dict = response.dict()
        response_dict['project_info'] = {
            'project_id': project_id,
            'project_name': project_name,
            'total_asins_requested': len(project_asins)
        }
        
        # Return appropriate HTTP status based on success
        if response.success:
            return JSONResponse(content=response_dict)
        else:
            # If no ASINs were successfully processed, return 400
            if response.scraping_summary.scraped == 0 and response.scraping_summary.skipped == 0:
                return JSONResponse(
                    status_code=400,
                    content=response_dict
                )
            # If some ASINs were processed but there were issues, return 207 (Multi-Status)
            return JSONResponse(
                status_code=207,
                content=response_dict
            )
            
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid date format in scrape_project_sales_history: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error in scrape_project_sales_history endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/daily", response_model=SalesHistoryQueryResponse)
async def get_daily_sales_history(
    asins: List[str] = Query(..., description="List of product ASINs to query"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    platform_source: Optional[str] = Query(None, description="Filter by platform source"),
    api_source: Optional[str] = Query(None, description="Filter by data source API"),
    service: SalesHistoryService = Depends(get_sales_history_service)
):
    """
    Get daily sales history data for multiple ASINs.
    
    This endpoint returns existing data from the database without scraping.
    If no data is available for requested ASINs, empty arrays are returned.
    
    **Date Filtering:**
    - If start_date and end_date provided: Returns data within that range
    - If only start_date provided: Returns data from start_date onwards
    - If only end_date provided: Returns data up to end_date
    - If no dates provided: Returns all available data
    
    **Response includes:**
    - Daily sales data by ASIN
    - Warnings for ASINs with no data
    - Query execution summary
    """
    try:
        logger.info(f"Received daily sales history query for {len(asins)} ASINs")
        
        # Convert date strings to date objects
        from datetime import date
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None
        
        # Create query request
        request = SalesHistoryQueryRequest(
            asins=asins,
            start_date=start_date_obj,
            end_date=end_date_obj,
            platform_source=platform_source,
            api_source=api_source
        )
        
        response = await service.get_daily_sales_history(request)
        
        # Return appropriate HTTP status
        if response.success:
            return response
        else:
            # If no data found, return 404
            if response.query_summary.get("total_records", 0) == 0:
                return JSONResponse(
                    status_code=404,
                    content=response.dict()
                )
            # Otherwise return 200 with warnings
            return response
            
    except ValueError as e:
        logger.error(f"Invalid date format in get_daily_sales_history: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_daily_sales_history endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/monthly", response_model=SalesHistoryMonthlyQueryResponse)
async def get_monthly_sales_history(
    asins: List[str] = Query(..., description="List of product ASINs to query"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    platform_source: Optional[str] = Query(None, description="Filter by platform source"),
    api_source: Optional[str] = Query(None, description="Filter by data source API"),
    service: SalesHistoryService = Depends(get_sales_history_service)
):
    """
    Get monthly aggregated sales history data for multiple ASINs.
    
    This endpoint returns monthly aggregated data from the database.
    Monthly data is automatically aggregated from daily data up to the latest complete month.
    
    **Monthly Aggregation:**
    - Sums daily units_sold for each month
    - Averages daily prices for each month
    - Only includes complete months (excludes current month)
    
    **Date Filtering:**
    - If start_date and end_date provided: Returns months within that range
    - If only start_date provided: Returns months from start_date onwards
    - If only end_date provided: Returns months up to end_date
    - If no dates provided: Returns all available monthly data
    
    **Response includes:**
    - Monthly aggregated data by ASIN
    - Warnings for ASINs with no data
    - Query execution summary
    """
    try:
        logger.info(f"Received monthly sales history query for {len(asins)} ASINs")
        
        # Convert date strings to date objects
        from datetime import date
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None
        
        # Create query request
        request = SalesHistoryQueryRequest(
            asins=asins,
            start_date=start_date_obj,
            end_date=end_date_obj,
            platform_source=platform_source,
            api_source=api_source
        )
        
        response = await service.get_monthly_sales_history(request)
        
        # Return appropriate HTTP status
        if response.success:
            return response
        else:
            # If no data found, return 404
            if response.query_summary.get("total_months", 0) == 0:
                return JSONResponse(
                    status_code=404,
                    content=response.dict()
                )
            # Otherwise return 200 with warnings
            return response
            
    except ValueError as e:
        logger.error(f"Invalid date format in get_monthly_sales_history: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_monthly_sales_history endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/stats/{asin}")
async def get_sales_stats(
    asin: str,
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    platform_source: Optional[str] = Query(None, description="Filter by platform source"),
    api_source: Optional[str] = Query(None, description="Filter by data source API"),
    service: SalesHistoryService = Depends(get_sales_history_service)
):
    """
    Get statistics for an ASIN's sales data.
    
    Returns comprehensive statistics for both daily and monthly data.
    
    **Statistics include:**
    - Total records, date ranges
    - Total units sold, average/min/max prices
    - For monthly data: total months, total days covered
    """
    try:
        logger.info(f"Getting sales stats for ASIN: {asin}")
        
        # Convert date strings to date objects
        from datetime import date
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None
        
        stats = await service.get_sales_stats(asin, start_date_obj, end_date_obj, platform_source, api_source)
        
        return {
            "success": True,
            "data": stats
        }
        
    except ValueError as e:
        logger.error(f"Invalid date format in get_sales_stats: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_sales_stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{asin}")
async def delete_sales_data(
    asin: str,
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    platform_source: Optional[str] = Query(None, description="Filter by platform source"),
    api_source: Optional[str] = Query(None, description="Filter by data source API"),
    service: SalesHistoryService = Depends(get_sales_history_service)
):
    """
    Delete sales data for an ASIN within a date range.
    
    **Deletion behavior:**
    - If no dates provided: Deletes all data for the ASIN
    - If start_date provided: Deletes from start_date onwards
    - If end_date provided: Deletes up to end_date
    - If both dates provided: Deletes within the range
    
    **Returns:**
    - Number of records deleted from daily and monthly tables
    """
    try:
        logger.info(f"Deleting sales data for ASIN: {asin}")
        
        # Convert date strings to date objects
        from datetime import date
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None
        
        result = await service.delete_sales_data(asin, start_date_obj, end_date_obj, platform_source, api_source)
        
        return {
            "success": True,
            "message": f"Successfully deleted {result['total_records_deleted']} records for ASIN {asin}",
            "data": result
        }
        
    except ValueError as e:
        logger.error(f"Invalid date format in delete_sales_data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error in delete_sales_data endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for sales history service."""
    return {
        "status": "healthy",
        "service": "sales-history",
        "timestamp": "2024-01-01T00:00:00Z"
    } 