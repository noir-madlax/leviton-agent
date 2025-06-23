"""Data models for Dashboard API responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class BrandCategoryData(BaseModel):
    """Brand category revenue/volume data model.
    
    Matches the exact format expected by frontend components.
    """
    brand: str = Field(description="Brand name")
    dimmerRevenue: float = Field(default=0, description="Dimmer switches revenue")
    switchRevenue: float = Field(default=0, description="Light switches revenue")
    dimmerVolume: float = Field(default=0, description="Dimmer switches volume")
    switchVolume: float = Field(default=0, description="Light switches volume")


class BrandAnalysisResponse(BaseModel):
    """Response model for brand analysis API."""
    data: List[BrandCategoryData] = Field(description="Brand category data")
    project_id: str = Field(description="Project ID used for filtering")
    total_brands: int = Field(description="Total number of brands")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter") 