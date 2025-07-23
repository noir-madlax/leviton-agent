"""
Sales History Service

This module provides a comprehensive service for scraping, storing, and retrieving
sales history data from Jungle Scout API.

Features:
- Smart scraping logic to avoid duplicate data collection
- Daily and monthly aggregated data storage
- Comprehensive API endpoints for data retrieval
- Integration with existing product database
- Automatic monthly aggregation from daily data

Usage:
    from sales_history.api import router
    from sales_history.services.sales_history_service import SalesHistoryService
"""

from .api import router
from .services.sales_history_service import SalesHistoryService
from .models import (
    SalesHistoryScrapingRequest,
    SalesHistoryQueryRequest,
    SalesHistoryScrapingResponse,
    SalesHistoryQueryResponse,
    SalesHistoryMonthlyQueryResponse,
    SalesHistoryYearlyQueryResponse
)

__all__ = [
    "router",
    "SalesHistoryService",
    "SalesHistoryScrapingRequest",
    "SalesHistoryQueryRequest", 
    "SalesHistoryScrapingResponse",
    "SalesHistoryQueryResponse",
    "SalesHistoryMonthlyQueryResponse",
    "SalesHistoryYearlyQueryResponse"
] 