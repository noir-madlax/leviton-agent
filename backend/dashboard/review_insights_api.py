#!/usr/bin/env python3
"""
Review Insights API module that provides standardized data using the same logic 
as fetch_top_review_aspects.py for consistent data across frontend charts.
"""

import logging
from typing import Dict, Any, Optional
from backend.fetch_top_review_aspects import get_top_insights_data, ANALYSIS_TYPES
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
    if analysis_type not in ANALYSIS_TYPES:
        raise ValueError(f"Invalid analysis type: {analysis_type}. Must be one of: {list(ANALYSIS_TYPES.keys())}")
    
    try:
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        # Get the data using the same logic as the Python script
        result = get_top_insights_data(
            supabase=supabase,
            project_id=project_id,
            analysis_type=analysis_type,
            asin=asin,
            max_categories=max_categories
        )
        
        logger.info(f"Successfully retrieved {analysis_type} data for project {project_id}: {len(result)} categories")
        return result
        
    except Exception as e:
        logger.error(f"Error getting standardized insights: {e}")
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
    try:
        results = {}
        for analysis_type in ANALYSIS_TYPES.keys():
            results[analysis_type] = get_standardized_insights(
                project_id=project_id,
                analysis_type=analysis_type,
                max_categories=max_categories
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting multiple insights: {e}")
        raise