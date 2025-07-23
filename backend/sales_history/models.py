"""Sales History API models and data structures."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from decimal import Decimal

# ==================== Request Models ====================

class SalesHistoryScrapingRequest(BaseModel):
    """Sales history scraping request model."""
    asins: List[str] = Field(..., description="List of product ASINs to scrape", min_items=1, max_items=50)
    start_date: Optional[date] = Field(None, description="Start date for scraping (YYYY-MM-DD). If None, scrapes all available data")
    end_date: Optional[date] = Field(None, description="End date for scraping (YYYY-MM-DD). If None, scrapes up to yesterday")
    platform_source: str = Field(default="amazon", description="Platform source (amazon, walmart, etc.)")
    api_source: str = Field(default="jungle_scout", description="Data source API for scraping")
    
    @validator('asins')
    def validate_asins(cls, v):
        """Validate ASIN format."""
        for asin in v:
            if not asin or len(asin.strip()) == 0:
                raise ValueError("ASIN cannot be empty")
            if len(asin.strip()) > 20:
                raise ValueError("ASIN too long (max 20 characters)")
        return [asin.strip().upper() for asin in v]
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        """Validate date constraints."""
        if v is not None:
            today = date.today()
            max_old_date = today.replace(year=today.year - 1)  # 365 days ago
            
            if v < max_old_date:
                raise ValueError(f"Date cannot be earlier than {max_old_date}")
            if v > today:
                raise ValueError("Date cannot be in the future")
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate start_date <= end_date."""
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError("end_date cannot be earlier than start_date")
        return v

class SalesHistoryQueryRequest(BaseModel):
    """Sales history query request model."""
    asins: List[str] = Field(..., description="List of product ASINs to query", min_items=1, max_items=50)
    start_date: Optional[date] = Field(None, description="Start date filter (YYYY-MM-DD). If None, returns all available data")
    end_date: Optional[date] = Field(None, description="End date filter (YYYY-MM-DD). If None, returns all available data")
    platform_source: Optional[str] = Field(None, description="Filter by platform source")
    api_source: Optional[str] = Field(None, description="Filter by data source API")
    
    @validator('asins')
    def validate_asins(cls, v):
        """Validate ASIN format."""
        for asin in v:
            if not asin or len(asin.strip()) == 0:
                raise ValueError("ASIN cannot be empty")
        return [asin.strip().upper() for asin in v]

# ==================== Response Models ====================

class SalesHistoryDataPoint(BaseModel):
    """Individual sales history data point."""
    sales_date: date = Field(..., description="Sales date")
    estimated_units_sold: int = Field(..., description="Estimated units sold on this date", ge=0)
    last_known_price: Decimal = Field(..., description="Last known price on this date (USD)", ge=0)
    revenue: Decimal = Field(..., description="Calculated revenue (price * units) in USD", ge=0)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class SalesHistoryMonthlyDataPoint(BaseModel):
    """Individual monthly sales history data point."""
    year_month_date: date = Field(..., description="First day of the month (YYYY-MM-01)")
    total_units_sold: int = Field(..., description="Total units sold in the month", ge=0)
    average_price: Decimal = Field(..., description="Average price in the month (USD)", ge=0)
    total_revenue: Decimal = Field(..., description="Total revenue in the month (USD)", ge=0)
    days_in_month: int = Field(..., description="Number of days with data in the month", ge=1)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class SalesHistoryYearlyDataPoint(BaseModel):
    """Individual yearly sales history data point (rolling year from latest scraping date)."""
    year_start_date: date = Field(..., description="First day of the year period (YYYY-MM-DD)")
    year_end_date: date = Field(..., description="Last day of the year period (YYYY-MM-DD) - latest scraping date")
    total_units_sold: int = Field(..., description="Total units sold in the year", ge=0)
    average_price: Decimal = Field(..., description="Average price in the year (USD)", ge=0)
    total_revenue: Decimal = Field(..., description="Total revenue in the year (USD)", ge=0)
    months_in_year: int = Field(..., description="Number of months with data in the year", ge=1)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class SalesHistoryScrapingSummary(BaseModel):
    """Summary of scraping operation results."""
    total_requested: int = Field(..., description="Total number of ASINs requested")
    scraped: int = Field(..., description="Number of ASINs successfully scraped")
    skipped: int = Field(..., description="Number of ASINs skipped (already have data)")
    failed: int = Field(..., description="Number of ASINs that failed to scrape")
    invalid_asins: List[str] = Field(default_factory=list, description="ASINs not found in product database")
    scraping_errors: Dict[str, str] = Field(default_factory=dict, description="ASIN -> error message mapping")

class SalesHistoryScrapingResponse(BaseModel):
    """Response for sales history scraping operation."""
    success: bool = Field(..., description="Whether the scraping operation was successful")
    message: str = Field(..., description="Human-readable message about the operation")
    scraping_summary: SalesHistoryScrapingSummary = Field(..., description="Summary of scraping results")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    data: Dict[str, List[SalesHistoryDataPoint]] = Field(..., description="Scraped data by ASIN")

class SalesHistoryQueryResponse(BaseModel):
    """Response for sales history query operation."""
    success: bool = Field(..., description="Whether the query operation was successful")
    message: str = Field(..., description="Human-readable message about the operation")
    data: Dict[str, List[SalesHistoryDataPoint]] = Field(..., description="Sales data by ASIN")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    query_summary: Dict[str, Any] = Field(..., description="Query execution summary")

class SalesHistoryMonthlyQueryResponse(BaseModel):
    """Response for monthly sales history query operation."""
    success: bool = Field(..., description="Whether the query operation was successful")
    message: str = Field(..., description="Human-readable message about the operation")
    data: Dict[str, List[SalesHistoryMonthlyDataPoint]] = Field(..., description="Monthly sales data by ASIN")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    query_summary: Dict[str, Any] = Field(..., description="Query execution summary")

class SalesHistoryYearlyQueryResponse(BaseModel):
    """Response for yearly sales history query operation."""
    success: bool = Field(..., description="Whether the query operation was successful")
    message: str = Field(..., description="Human-readable message about the operation")
    data: Dict[str, List[SalesHistoryYearlyDataPoint]] = Field(..., description="Yearly sales data by ASIN (rolling year from latest scraping date)")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    query_summary: Dict[str, Any] = Field(..., description="Query execution summary")

class DateRange(BaseModel):
    """Date range for coverage checking."""
    start_date: date
    end_date: date
    
    def contains(self, other_start: date, other_end: date) -> bool:
        """Check if this range contains another range."""
        return self.start_date <= other_start and self.end_date >= other_end
    
    def overlaps(self, other_start: date, other_end: date) -> bool:
        """Check if this range overlaps with another range."""
        return self.start_date <= other_end and self.end_date >= other_start

class ScrapingResult(BaseModel):
    """Result of scraping a single ASIN."""
    asin: str
    success: bool
    data: List[SalesHistoryDataPoint] = Field(default_factory=list)
    error_message: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

class SalesHistoryStats(BaseModel):
    """Statistics for sales history data."""
    total_records: int = Field(..., description="Total number of records")
    date_range: Optional[DateRange] = Field(None, description="Date range of the data")
    total_units_sold: int = Field(..., description="Total units sold across all records")
    total_revenue: Decimal = Field(..., description="Total revenue across all records")
    average_price: Decimal = Field(..., description="Average price across all records")
    min_price: Decimal = Field(..., description="Minimum price")
    max_price: Decimal = Field(..., description="Maximum price")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        } 