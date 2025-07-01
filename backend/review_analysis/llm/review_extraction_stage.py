"""Review analysis extraction stage implementation.

This module defines a ReviewExtractionStage that converts a sequence of product
reviews into hierarchical review analysis structures with physical, performance,
and use case aspects.

The stage is built on the generic BaseStage utilities which provide automatic
retry, split-and-conquer, and persistence mechanics. The review-specific
responsibilities are:

• Prompt construction with review formatting.
• Response validation using comprehensive review hierarchy validation.
• Retry-prompt construction with detailed error feedback.
• Split/merge operations that preserve RID integrity across splits.

The expected LLM output is a hierarchical JSON structure:

{
    "phy": {
        "<PHYSICAL>": {
            "<PID>@<DETAIL>": {
                "<SENT>": [RID, RID, ...]
            }
        }
    },
    "perf": {
        "<PERF>": {
            "<perf_id>@<DETAIL>": {
                "<SENT>": {"<PERF_REASON>": [RID, ...]}
            }
        }
    },
    "use": {
        "<USE>": {
            "<SENT>": {"<USE_REASON>": [RID, ...]}
        }
    }
}
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from core.utils.llm_utils import ValidationResult, extract_json
from core.llm_taxonomy_pipeline.pipeline_stage import BaseStage, StageContext, StageResultBase

from .validation import (
    parse_and_validate_review_response,
    ReviewValidationContext,
    create_retry_context
)
from .hierarchy_merger import (
    extract_used_ids,
    offset_id,
    create_id_mapping,
    remap_compound_reason
)

__all__ = [
    "ReviewExtractionContext",
    "ReviewExtractionResult", 
    "ReviewExtractionStage",
    "format_reviews_for_prompt",
]

# ---------------------------------------------------------------------------
# Data-transfer objects
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ReviewExtractionContext(StageContext):
    """Context object carrying review extraction inputs."""
    
    formatted_reviews: str  # Pre-formatted RID#review strings
    expected_review_ids: Set[int]  # For validation
    asin: str  # Product identifier
    product_title: str  # For error context


@dataclass(slots=True, frozen=True)
class ReviewExtractionResult(StageResultBase):
    """Result payload for review extraction stages."""
    
    review_hierarchy: Dict[str, Any]  # Raw phy/perf/use structure
    aspects_extracted: int  # Count of aspects found


# ---------------------------------------------------------------------------
# Review formatting utilities
# ---------------------------------------------------------------------------

def format_reviews_for_prompt(reviews: List[Dict[str, Any]]) -> Tuple[str, Set[int]]:
    """Format reviews as RID#review_text strings for prompt input.
    
    Args:
        reviews: List of review dictionaries with 'title' and 'text' fields
        
    Returns:
        Tuple of (formatted_string, expected_review_ids)
    """
    formatted_lines = []
    expected_ids = set()
    
    for idx, review in enumerate(reviews):
        title = review.get('title', '')
        body = review.get('text', '')
        
        # Format title properly
        if title and not title.endswith(('.', '?', '!', ',', ';', ':')):
            title = title + '. '
        elif title:
            title = title + ' '
        
        # Combine and clean text
        review_text = f"{title}{body}"
        escaped_text = review_text.replace('\\', '\\\\').replace('\n', ' ').replace('\r', ' ')
        
        formatted_lines.append(f"{idx}#{escaped_text}")
        expected_ids.add(idx)
    
    return "\n".join(formatted_lines), expected_ids


def count_extracted_aspects(hierarchy: Dict[str, Any]) -> int:
    """Count total aspects extracted across all sections.
    
    Args:
        hierarchy: Parsed review hierarchy structure
        
    Returns:
        Total count of aspects found
    """
    count = 0
    
    # Count physical aspects
    if 'phy' in hierarchy and isinstance(hierarchy['phy'], dict):
        for category, details in hierarchy['phy'].items():
            if isinstance(details, dict):
                count += len([k for k in details.keys() if '@' in k])
    
    # Count performance aspects  
    if 'perf' in hierarchy and isinstance(hierarchy['perf'], dict):
        for category, details in hierarchy['perf'].items():
            if isinstance(details, dict):
                count += len([k for k in details.keys() if '@' in k])
    
    # Count use case aspects
    if 'use' in hierarchy and isinstance(hierarchy['use'], dict):
        count += len(hierarchy['use'])
    
    return count


# ---------------------------------------------------------------------------
# Fixed prompt templates
# ---------------------------------------------------------------------------

# Path to prompt template files
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_EXTRACT_PROMPT_PATH = _PROMPTS_DIR / "review_aspects_extraction_prompt_v0.txt"

# Shared retry template from core
_RETRY_PROMPT_PATH = (
    Path(__file__).resolve().parents[2]  # points to .../backend
    / "core" / "prompts" / "shared_retry_prompt_v0.txt"
)

# Load prompt templates at module level
try:
    with open(_EXTRACT_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _EXTRACT_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required prompt template not found: {_EXTRACT_PROMPT_PATH}")

if not _RETRY_PROMPT_PATH.exists():
    raise RuntimeError(f"Required retry template not found: {_RETRY_PROMPT_PATH}")

with open(_RETRY_PROMPT_PATH, "r", encoding="utf-8") as f:
    _RETRY_PROMPT_TEMPLATE = f.read()


# ---------------------------------------------------------------------------
# ReviewExtractionStage implementation
# ---------------------------------------------------------------------------

class ReviewExtractionStage(BaseStage):
    """Review hierarchy extraction stage built on BaseStage."""

    # --------------------- BaseStage abstract hooks -------------------------

    async def _build_prompt(self, ctx: ReviewExtractionContext) -> str:
        """Build the review extraction prompt with formatted reviews."""
        
        # Use string replacement instead of .format() to avoid issues with JSON braces
        rendered_prompt = _EXTRACT_PROMPT_TEMPLATE.replace("{{PRODUCT}}", ctx.product_category)
        rendered_prompt = rendered_prompt.replace("{{INPUT}}", ctx.formatted_reviews)

        return rendered_prompt

    def _validate(self, raw_response: str, ctx: ReviewExtractionContext) -> ValidationResult:
        """Validate review extraction response using comprehensive validation."""
        
        # Create validation context
        validation_ctx = ReviewValidationContext(
            expected_review_ids=ctx.expected_review_ids,
            product_title=ctx.product_title,
            asin=ctx.asin
        )
        
        # Use the comprehensive review validation system
        return parse_and_validate_review_response(raw_response, validation_ctx)

    def _retry_prompt(
        self, 
        original_prompt: str, 
        retry_ctx: Any, 
        ctx: ReviewExtractionContext
    ) -> str:
        """Build retry prompt using shared retry template."""
        
        # retry_ctx is the error_categories dict from ValidationResult
        if not isinstance(retry_ctx, dict):
            # Fallback for unexpected retry context format
            return f"{original_prompt}\n\nPlease fix the errors and provide a valid JSON response."
        
        # Format error details
        error_lines = []
        for category, errors in retry_ctx.items():
            if errors:  # Only include categories with errors
                error_lines.append(f"\n{category.upper().replace('_', ' ')}:")
                for error in errors:
                    error_lines.append(f"  • {error}")
        
        error_details = "\n".join(error_lines) if error_lines else "Unknown validation errors"
        
        # Use the shared retry template with structured error details
        try:
            retry_block = _RETRY_PROMPT_TEMPLATE.replace("{{error_details}}", error_details)
            return f"{original_prompt}\n\n{retry_block}"
        except Exception as exc:
            # Fallback if template replacement fails
            return f"{original_prompt}\n\nValidation failed with errors: {error_details}\n\nPlease fix the errors and provide a valid JSON response."

    async def _produce_result(
        self,
        raw_response: str,
        ctx: ReviewExtractionContext,
        attempts: int,
    ) -> ReviewExtractionResult:
        """Convert a valid raw response into a ReviewExtractionResult."""
        
        # Extract and parse the JSON response
        json_text = extract_json(raw_response)
        hierarchy = json.loads(json_text)
        
        # Count extracted aspects
        aspects_count = count_extracted_aspects(hierarchy)
        
        return ReviewExtractionResult(
            review_hierarchy=hierarchy,
            aspects_extracted=aspects_count
        )

    def _split_context(
        self, ctx: ReviewExtractionContext, depth: int
    ) -> tuple[ReviewExtractionContext, ReviewExtractionContext]:
        """Split review context into two parts for recursive processing."""
        
        if len(ctx.expected_review_ids) <= 1:
            raise NotImplementedError("Cannot split context with single review")
        
        # Parse formatted_reviews back into individual review lines
        review_lines = ctx.formatted_reviews.strip().split('\n')
        mid = len(review_lines) // 2
        
        # Split the formatted reviews
        left_reviews = '\n'.join(review_lines[:mid])
        right_reviews = '\n'.join(review_lines[mid:])
        
        # Create expected IDs for each half (renumbered from 0)
        left_ids = {i for i in range(mid)}
        right_ids = {i for i in range(len(review_lines) - mid)}
        
        # Renumber the right side reviews to start from 0
        right_review_lines = []
        for i, line in enumerate(review_lines[mid:]):
            if '#' in line:
                _, content = line.split('#', 1)
                right_review_lines.append(f"{i}#{content}")
            else:
                right_review_lines.append(f"{i}#{line}")
        right_reviews = '\n'.join(right_review_lines)
        
        ctx_left = ReviewExtractionContext(
            product_category=ctx.product_category,
            formatted_reviews=left_reviews,
            expected_review_ids=left_ids,
            asin=ctx.asin,
            product_title=ctx.product_title
        )
        
        ctx_right = ReviewExtractionContext(
            product_category=ctx.product_category,
            formatted_reviews=right_reviews,
            expected_review_ids=right_ids,
            asin=ctx.asin,
            product_title=ctx.product_title
        )
        
        return ctx_left, ctx_right

    async def _merge_split_results(
        self,
        res_left: ReviewExtractionResult,
        res_right: ReviewExtractionResult,
        ctx_left: ReviewExtractionContext,
        ctx_right: ReviewExtractionContext,
        depth: int,
    ) -> ReviewExtractionResult:
        """Merge two partial review extraction results."""
        
        # Initialize merged hierarchy
        merged_hierarchy = {
            "phy": {},
            "perf": {},
            "use": {}
        }
        
        left_size = len(ctx_left.expected_review_ids)
        
        # Extract used IDs from left result and create mappings for right result
        used_pids, used_perf_ids = extract_used_ids(res_left.review_hierarchy)
        pid_mapping, perf_id_mapping = create_id_mapping(res_right.review_hierarchy, used_pids, used_perf_ids)
        
        def merge_phy_section():
            """Merge physical aspects section."""
            left_phy = res_left.review_hierarchy.get("phy", {})
            right_phy = res_right.review_hierarchy.get("phy", {})
            
            merged_phy = {}
            
            # Merge left section as-is
            for category, details in left_phy.items():
                merged_phy[category] = details.copy()
            
            # Merge right section with RID offset and ID remapping
            for category, details in right_phy.items():
                if category not in merged_phy:
                    merged_phy[category] = {}
                
                for pid_detail, sentiments in details.items():
                    if isinstance(sentiments, dict) and "@" in pid_detail:
                        # Remap PID using the mapping
                        original_pid, detail = pid_detail.split("@", 1)
                        new_pid = pid_mapping.get(original_pid, original_pid)
                        new_pid_detail = f"{new_pid}@{detail}"
                        
                        offset_sentiments = {}
                        for sentiment, rid_list in sentiments.items():
                            if isinstance(rid_list, list):
                                offset_sentiments[sentiment] = [rid + left_size for rid in rid_list]
                        
                        if new_pid_detail in merged_phy[category]:
                            # Merge sentiment arrays
                            for sentiment, rid_list in offset_sentiments.items():
                                if sentiment in merged_phy[category][new_pid_detail]:
                                    merged_phy[category][new_pid_detail][sentiment].extend(rid_list)
                                else:
                                    merged_phy[category][new_pid_detail][sentiment] = rid_list
                        else:
                            merged_phy[category][new_pid_detail] = offset_sentiments
            
            return merged_phy

        def merge_perf_section():
            """Merge performance aspects section."""
            left_perf = res_left.review_hierarchy.get("perf", {})
            right_perf = res_right.review_hierarchy.get("perf", {})
            
            merged_perf = {}
            
            # Merge left section as-is
            for category, details in left_perf.items():
                merged_perf[category] = details.copy()
            
            # Merge right section with RID offset and ID remapping
            for category, details in right_perf.items():
                if category not in merged_perf:
                    merged_perf[category] = {}
                
                for perf_id_detail, sentiments in details.items():
                    if isinstance(sentiments, dict) and "@" in perf_id_detail:
                        # Remap perf_id using the mapping
                        original_perf_id, detail = perf_id_detail.split("@", 1)
                        new_perf_id = perf_id_mapping.get(original_perf_id, original_perf_id)
                        new_perf_id_detail = f"{new_perf_id}@{detail}"
                        
                        offset_sentiments = {}
                        for sentiment, reasons in sentiments.items():
                            if isinstance(reasons, dict):
                                offset_reasons = {}
                                for reason, rid_list in reasons.items():
                                    # Remap reason IDs (handles both single and compound reasons)
                                    new_reason = remap_compound_reason(reason, pid_mapping, perf_id_mapping)
                                    
                                    if isinstance(rid_list, list):
                                        offset_reasons[new_reason] = [rid + left_size for rid in rid_list]
                                offset_sentiments[sentiment] = offset_reasons
                        
                        if new_perf_id_detail in merged_perf[category]:
                            # Merge reason structures
                            for sentiment, reasons in offset_sentiments.items():
                                if sentiment in merged_perf[category][new_perf_id_detail]:
                                    for reason, rid_list in reasons.items():
                                        if reason in merged_perf[category][new_perf_id_detail][sentiment]:
                                            merged_perf[category][new_perf_id_detail][sentiment][reason].extend(rid_list)
                                        else:
                                            merged_perf[category][new_perf_id_detail][sentiment][reason] = rid_list
                                else:
                                    merged_perf[category][new_perf_id_detail][sentiment] = reasons
                        else:
                            merged_perf[category][new_perf_id_detail] = offset_sentiments
            
            return merged_perf

        def merge_use_section():
            """Merge use case aspects section."""
            left_use = res_left.review_hierarchy.get("use", {})
            right_use = res_right.review_hierarchy.get("use", {})
            
            merged_use = {}
            
            # Merge left section as-is  
            for use_case, sentiments in left_use.items():
                merged_use[use_case] = sentiments.copy()
            
            # Merge right section with RID offset and reason ID remapping
            for use_case, sentiments in right_use.items():
                if isinstance(sentiments, dict):
                    offset_sentiments = {}
                    for sentiment, reasons in sentiments.items():
                        if isinstance(reasons, dict):
                            offset_reasons = {}
                            for reason, rid_list in reasons.items():
                                # Remap reason IDs (handles both single and compound reasons)
                                new_reason = remap_compound_reason(reason, pid_mapping, perf_id_mapping)
                                
                                if isinstance(rid_list, list):
                                    offset_reasons[new_reason] = [rid + left_size for rid in rid_list]
                            offset_sentiments[sentiment] = offset_reasons
                    
                    if use_case in merged_use:
                        # Merge reason structures
                        for sentiment, reasons in offset_sentiments.items():
                            if sentiment in merged_use[use_case]:
                                for reason, rid_list in reasons.items():
                                    if reason in merged_use[use_case][sentiment]:
                                        merged_use[use_case][sentiment][reason].extend(rid_list)
                                    else:
                                        merged_use[use_case][sentiment][reason] = rid_list
                            else:
                                merged_use[use_case][sentiment] = reasons
                    else:
                        merged_use[use_case] = offset_sentiments
            
            return merged_use

        # Merge all sections
        merged_hierarchy["phy"] = merge_phy_section()
        merged_hierarchy["perf"] = merge_perf_section()
        merged_hierarchy["use"] = merge_use_section()
        
        return ReviewExtractionResult(
            review_hierarchy=merged_hierarchy,
            aspects_extracted=res_left.aspects_extracted + res_right.aspects_extracted
        )