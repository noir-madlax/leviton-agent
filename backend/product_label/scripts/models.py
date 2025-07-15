"""
Data transfer objects for smart capability labeling
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass(slots=True, frozen=True)
class ProductData:
    """Represents a product with its ID and title for labeling"""
    product_id: str
    title: str

@dataclass(slots=True, frozen=True)
class SmartCapabilityContext:
    """Context for smart capability labeling batch processing"""
    products: List[ProductData]
    available_labels: Dict[str, str]
    batch_id: int = 0
    project_id: str = ""

@dataclass(slots=True, frozen=True)
class SmartCapabilityResult:
    """Result of smart capability labeling for a batch"""
    assignments: Dict[str, str]  # product_index -> label
    batch_id: int = 0
    success: bool = True
    error_message: Optional[str] = None
    attempts: int = 1

@dataclass
class LabelingStats:
    """Statistics tracking for the labeling process"""
    total_products: int = 0
    processed_products: int = 0
    successful_labels: int = 0
    failed_labels: int = 0
    batches_processed: int = 0
    batches_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_products == 0:
            return 0.0
        return (self.successful_labels / self.total_products) * 100

    @property
    def duration_seconds(self) -> float:
        """Calculate total duration in seconds"""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

@dataclass
class LabelingConfiguration:
    """Configuration for the smart capability labeling process"""
    project_id: str
    field_name: str
    field_type: str
    field_description: str
    batch_size: int
    max_retries: int
    llm_temperature: float
    available_labels: Dict[str, str]
    ui_config: Dict[str, any]
    dry_run: bool = False 