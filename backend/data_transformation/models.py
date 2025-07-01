"""Data models for transformation operations."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime


@dataclass
class TransformationResult:
    """Result of data transformation operation."""
    success: bool
    processed_count: int
    skipped_count: int
    error_count: int
    errors: List[str]
    duration_seconds: float
    summary: Dict[str, Any]


@dataclass  
class ProductTransformationData:
    """Structured data for product transformation."""
    # Direct mapping fields
    platform_id: str
    title: Optional[str]
    brand: Optional[str]
    model_number: Optional[str]
    category: Optional[str]
    categories_flat: Optional[str]  # 完整的类别路径
    image_url: Optional[str]
    product_url: Optional[str]
    availability: Optional[str]
    collection: Optional[str]
    delivery_free: Optional[str]
    pickup_available: Optional[str]
    features: Optional[str]
    description: Optional[str]
    extract_date: Optional[str]
    
    # Price fields (raw)
    price_usd: Optional[Decimal]
    rating: Optional[Decimal]
    reviews_count: Optional[Decimal]
    position: int
    recent_sales: Optional[str]
    is_bestseller: Optional[str]
    unit_price: Optional[str]
    
    # Calculated fields (will be computed)
    list_price_usd: Optional[Decimal] = None
    monthly_sales_volume: Optional[int] = None
    estimated_revenue: Optional[Decimal] = None
    pack_count: int = 1
    unit_price_calculated: Optional[Decimal] = None
    unit_price_numeric: Optional[Decimal] = None
    estimated_volume: Optional[Decimal] = None
    
    # Default values
    source: str = "amazon"
    cleaned_title: Optional[str] = None
    product_segment: Optional[str] = None
    refined_category: Optional[str] = None
    category_definition: Optional[str] = None


@dataclass
class TransformationConfig:
    """Configuration for transformation operations."""
    batch_size: int = 100
    skip_existing: bool = True
    validate_calculations: bool = True
    log_level: str = "INFO"
    dry_run: bool = False 