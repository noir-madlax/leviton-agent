"""
Configuration for retry transformation tool
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RetryConfig:
    """Configuration for retry operations"""
    
    # Supabase connection settings
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    # Retry behavior
    dry_run: bool = False
    verbose: bool = False
    batch_size: int = 50
    
    # Safety checks
    max_retries: int = 3
    validate_source_data: bool = True
    backup_failed_state: bool = True
    
    # Transformation settings
    skip_existing: bool = False
    validate_calculations: bool = True


# Status constants
class TransformationStatus:
    """Transformation status constants"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStage:
    """Workflow stage constants"""
    SCRAPING = "scraping"
    IMPORTING = "importing"
    TRANSFORMING = "transforming"
    COMPLETED = "completed"
    FAILED = "failed"


# Validation constants
MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 1000
SUPPORTED_STATUSES = [
    TransformationStatus.FAILED,
    TransformationStatus.PENDING
]

# Database tables
TABLES = {
    "SCRAPING_REQUESTS": "scraping_requests",
    "AMAZON_PRODUCTS": "amazon_products",
    "PRODUCT_WIDE_TABLE": "product_wide_table"
}

# Retry safety limits
MAX_RECORDS_PER_BATCH = 500
MAX_CONCURRENT_RETRIES = 1  # Only allow one retry at a time for safety 