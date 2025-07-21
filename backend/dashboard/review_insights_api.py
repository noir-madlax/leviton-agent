#!/usr/bin/env python3
"""
Review Insights API module that provides standardized data using the same logic 
as fetch_top_review_aspects.py for consistent data across frontend charts.
"""

import logging
from typing import Dict, Any, Optional
import sys
import os

# Add backend to path if not already there
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fetch_top_review_aspects import get_top_insights_data, ANALYSIS_TYPES
from core.database.connection import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

def get_standardized_insights(project_id: str, analysis_type: str = 'delights', 
                             asin: Optional[str] = None, max_categories: int = 10) -> Dict[str, Any]:
    """
    Get standardized insights data using the same logic as fetch_top_review_aspects.py
    
    Args:
        project_id: Project ID to analyze
        analysis_type: 'delights', 'pain_points', or 'use_cases'
        asin: Optional ASIN filter
        max_categories: Maximum number of categories to return
    
    Returns:
        Dictionary with standardized insights data
    """
    logger.info(f"get_standardized_insights called with project_id={project_id}, analysis_type={analysis_type}")
    
    if analysis_type not in ANALYSIS_TYPES:
        error_msg = f"Invalid analysis type: {analysis_type}. Must be one of: {list(ANALYSIS_TYPES.keys())}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase = get_supabase_client()
        
        # Get the data using the same logic as the Python script
        logger.info(f"Calling get_top_insights_data for {analysis_type}...")
        result = get_top_insights_data(
            supabase=supabase,
            project_id=project_id,
            analysis_type=analysis_type,
            asin=asin,
            max_categories=max_categories
        )
        
        logger.info(f"Successfully retrieved {analysis_type} data for project {project_id}: {len(result)} categories")
        logger.debug(f"Result keys: {list(result.keys())}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting standardized insights: {e}", exc_info=True)
        raise

def get_multiple_insights(project_id: str, max_categories: int = 10) -> Dict[str, Any]:
    """
    Get all three types of insights in one call for better performance.
    
    Args:
        project_id: Project ID to analyze
        max_categories: Maximum number of categories to return per analysis type
    
    Returns:
        Dictionary containing all three analysis types
    """
    logger.info(f"get_multiple_insights called with project_id={project_id}, max_categories={max_categories}")
    logger.info(f"Available analysis types: {list(ANALYSIS_TYPES.keys())}")
    
    try:
        results = {}
        for analysis_type in ANALYSIS_TYPES.keys():
            logger.info(f"Processing analysis type: {analysis_type}")
            results[analysis_type] = get_standardized_insights(
                project_id=project_id,
                analysis_type=analysis_type,
                max_categories=max_categories
            )
            logger.info(f"Completed {analysis_type}: {len(results[analysis_type])} categories")
        
        logger.info(f"get_multiple_insights completed successfully. Total results: {len(results)}")
        return results
        
    except Exception as e:
        logger.error(f"Error getting multiple insights: {e}", exc_info=True)
        raise