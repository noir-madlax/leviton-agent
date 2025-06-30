"""Database models for review analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# Constants for consistency
SENTIMENT_TYPES = ["positive", "negative", "neutral"]
ASPECT_TYPES = ["physical", "performance", "usability"]


class ReviewAnalysisStage(str, Enum):
    """Review analysis run stages."""
    INIT = "init"
    EXTRACTION = "extraction"
    CATEGORIZATION = "categorization"
    CONSOLIDATION = "consolidation"
    REFINEMENT = "refinement"
    COMPLETED = "completed"
    FAILED = "failed"


class AspectType(str, Enum):
    """Enumeration for aspect types."""

    PHY = "phy"
    PERF = "perf"
    USE = "use"


@dataclass
class ReviewAnalysisRun:
    """Review analysis run record."""
    id: str
    project_id: str
    stage: ReviewAnalysisStage
    llm_config: Dict[str, Any]
    processing_params: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ReviewAnalysisRequest:
    """Request model for starting review analysis."""
    project_id: str
    product_ids: List[str | int]  # ASINs or product IDs
    product_category: str = ""
    aspect_types: List[str] = None  # e.g. ["physical", "performance", "usability"]
    include_sentiment: bool = True  # Whether to perform sentiment analysis
    include_reasons: bool = True  # Whether to extract detailed reasons for perf/use
    
    def __post_init__(self):
        if self.aspect_types is None:
            self.aspect_types = ASPECT_TYPES.copy()
        
        # Validate aspect types
        invalid_types = [t for t in self.aspect_types if t not in ASPECT_TYPES]
        if invalid_types:
            raise ValueError(f"Invalid aspect types: {invalid_types}. Valid types: {ASPECT_TYPES}")


@dataclass
class ReviewAspectExtraction:
    """Review aspect extraction record."""
    id: Optional[int] = None
    run_id: str = ""
    product_id: str = ""  # ASIN
    review_id: str = ""
    aspect_type: str = ""  # physical, performance, usability
    aspect_id: str = ""  # PID (A, B, ...) or perf_id (a, b, ...) or use case name
    aspect_description: str = ""  # The <DETAIL> or <PERF> or <USE> text
    aspect_category: str = ""  # <PHYSICAL>, <PERF>, or <USE> - the parent category
    sentiment: str = ""  # + or - (from extraction prompt)
    review_ids: List[str] = None  # List of RIDs mentioning this aspect
    stage: str = "extraction"  # extraction, categorization, consolidation, refinement
    
    def __post_init__(self):
        if self.review_ids is None:
            self.review_ids = []


@dataclass
class ReviewAspectCategory:
    """Review aspect category definition."""
    id: Optional[int] = None
    project_id: str = ""
    run_id: str = ""
    aspect_type: str = ""  # physical, performance, usability
    category_name: str = ""
    definition: str = ""
    stage: str = ""  # categorization, consolidation, final


@dataclass
class ReviewRecord:
    """Complete review record with sentiment and metadata."""
    id: Optional[int] = None
    run_id: str = ""
    product_id: str = ""  # ASIN
    review_id: str = ""
    review_content: str = ""
    rating: Optional[int] = None  # 1-5 star rating
    verified: bool = False
    review_date: Optional[datetime] = None
    brand: Optional[str] = None
    overall_sentiment: Optional[str] = None  # positive, negative, neutral
    

@dataclass
class ReviewAspectReason:
    """Reasons linking performance/usability aspects to their causes."""
    id: Optional[int] = None
    run_id: str = ""
    extraction_id: int = 0  # Foreign key to ReviewAspectExtraction (the aspect being explained)
    reason_aspect_id: str = ""  # PID or perf_id that causes this aspect
    sentiment: str = ""  # + or - (must match the main aspect's sentiment)
    review_ids: List[str] = None  # List of RIDs where this reason is mentioned
    
    def __post_init__(self):
        if self.review_ids is None:
            self.review_ids = []


@dataclass
class ReviewAspectAssignment:
    """Review aspect assignment to categories."""
    id: Optional[int] = None
    run_id: str = ""
    project_id: str = ""
    extraction_id: int = 0  # Foreign key to ReviewAspectExtraction
    category_id_initial: Optional[int] = None  # Initial categorization
    category_id_refined: Optional[int] = None  # After refinement
    category_name: Optional[str] = None  # Final category name
    sentiment: Optional[str] = None  # positive, negative, neutral


@dataclass
class ExtractionResult:
    """Complete extraction result matching the LLM output format."""
    run_id: str = ""
    product_id: str = ""  # ASIN
    extraction_data: Dict[str, Any] = None  # Raw JSON from LLM
    
    def __post_init__(self):
        if self.extraction_data is None:
            self.extraction_data = {
                "phy": {},  # Physical aspects: {<PHYSICAL>: {<PID>@<DETAIL>: {<SENT>: [RID, ...]}}}
                "perf": {}, # Performance: {<PERF>: {<perf_id>@<DETAIL>: {<SENT>: {<PERF_REASON>: [RID, ...]}}}}
                "use": {}   # Use cases: {<USE>: {<SENT>: {<USE_REASON>: [RID, ...]}}}
            }
    
    def get_all_aspects(self) -> List[Dict[str, Any]]:
        """Extract all aspects from the nested JSON structure."""
        aspects = []
        
        # Physical aspects
        for physical_category, physical_aspects in self.extraction_data.get("phy", {}).items():
            for aspect_key, sentiments in physical_aspects.items():
                aspect_id, detail = aspect_key.split("@", 1)
                for sentiment, review_ids in sentiments.items():
                    aspects.append({
                        "aspect_type": "physical",
                        "aspect_id": aspect_id,
                        "aspect_category": physical_category,
                        "aspect_description": detail,
                        "sentiment": sentiment,
                        "review_ids": review_ids,
                        "reasons": []  # Physical aspects have no reasons
                    })
        
        # Performance aspects
        for perf_category, perf_aspects in self.extraction_data.get("perf", {}).items():
            for aspect_key, sentiments in perf_aspects.items():
                aspect_id, detail = aspect_key.split("@", 1)
                for sentiment, reason_data in sentiments.items():
                    reasons = []
                    review_ids = []
                    for reason_id, rids in reason_data.items():
                        if reason_id != "?":  # Skip unknown reasons
                            reasons.append(reason_id)
                        review_ids.extend(rids)
                    
                    aspects.append({
                        "aspect_type": "performance", 
                        "aspect_id": aspect_id,
                        "aspect_category": perf_category,
                        "aspect_description": detail,
                        "sentiment": sentiment,
                        "review_ids": list(set(review_ids)),  # Remove duplicates
                        "reasons": reasons
                    })
        
        # Use case aspects
        for use_case, sentiments in self.extraction_data.get("use", {}).items():
            for sentiment, reason_data in sentiments.items():
                reasons = []
                review_ids = []
                for reason_id, rids in reason_data.items():
                    if reason_id != "?":  # Skip unknown reasons
                        reasons.append(reason_id)
                    review_ids.extend(rids)
                
                aspects.append({
                    "aspect_type": "usability",
                    "aspect_id": use_case,  # Use case name as ID
                    "aspect_category": use_case,
                    "aspect_description": use_case,
                    "sentiment": sentiment,
                    "review_ids": list(set(review_ids)),  # Remove duplicates
                    "reasons": reasons
                })
        
        return aspects 


@dataclass
class Aspect:
    """Row in *aspect* table."""

    aspect_pk: Optional[int] = None
    project_id: str = ""
    product_id: str = ""
    aspect_type: AspectType = AspectType.PHY
    local_id: str = ""  # Prompt-local ID (A, a, … or full use-case string)
    parent_group_name: str = ""  # The <PHYSICAL>/<PERF>/<USE> header
    detail_text: str = ""
    category_pk: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class AspectOccurrence:
    """Row in *aspect_occurrence* fact table."""

    aspect_pk: int
    review_id: str
    sentiment: str  # "+" or "-"
    causes: List[int]  # aspect_pk array

    def model_dump(self) -> Dict[str, Any]:  # Helper for repository
        return {
            "aspect_pk": self.aspect_pk,
            "review_id": self.review_id,
            "sentiment": self.sentiment,
            "causes": self.causes,
        } 