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
• Automatic error fixing when validation fails after max retries.

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
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

from core.utils.llm_utils import ValidationResult, extract_json
from core.llm_taxonomy_pipeline.pipeline_stage import BaseStage, StageContext, StageResultBase
from core.utils.llm_utils import LLMCallError

from .validation import (
    parse_and_validate_review_response,
    ReviewValidationContext,
    create_retry_context,
    ReviewHierarchyValidator,
    ReviewValidationError
)
from .hierarchy_merger import (
    extract_used_ids,
    offset_id,
    create_id_mapping,
    remap_compound_reason
)

logger = logging.getLogger(__name__)

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
# Error fixing utilities
# ---------------------------------------------------------------------------

def _fix_invalid_review_ids(rid_list: List[Any], expected_review_ids: Set[int]) -> List[int]:
    """Fix invalid review IDs by filtering out invalid ones.
    
    Args:
        rid_list: List of review IDs (may contain invalid values)
        expected_review_ids: Set of valid review IDs
        
    Returns:
        List of valid review IDs only
    """
    fixed_ids = []
    for rid in rid_list:
        try:
            rid_int = int(rid)
            if rid_int in expected_review_ids:
                fixed_ids.append(rid_int)
        except (ValueError, TypeError):
            # Skip invalid IDs
            continue
    return fixed_ids


def _fix_invalid_sentiment(sentiment: str) -> str:
    """Fix invalid sentiment values.
    
    Args:
        sentiment: Input sentiment value
        
    Returns:
        Fixed sentiment ('+' or '-')
    """
    if sentiment in ['+', '-']:
        return sentiment
    
    # Try to map common variations
    sentiment_lower = str(sentiment).lower().strip()
    if sentiment_lower in ['positive', 'pos', 'good', 'great', 'excellent', '1', 'true']:
        return '+'
    elif sentiment_lower in ['negative', 'neg', 'bad', 'poor', 'terrible', '0', 'false']:
        return '-'
    
    # Default to positive if unclear
    return '+'


def _fix_invalid_id_format(id_str: str, id_type: str) -> str:
    """Fix invalid ID format by generating a valid one.
    
    Args:
        id_str: Input ID string
        id_type: Either 'PID' or 'perf_id'
        
    Returns:
        Valid ID string
    """
    if id_type == 'PID':
        # Generate valid PID (A, B, C... Z, AA, AB...)
        if not id_str or not isinstance(id_str, str):
            return 'A'
        
        # Try to extract valid characters
        valid_chars = ''.join(c for c in id_str.upper() if c.isalpha())
        if valid_chars:
            # Limit to reasonable length and ensure it's a valid PID format
            if len(valid_chars) <= 2:  # A, B, C... Z, AA, AB, etc.
                return valid_chars
            else:
                return 'A'  # Default if too long
        else:
            return 'A'
    elif id_type == 'perf_id':
        # Generate valid perf_id (a, b, c... z, aa, ab...)
        if not id_str or not isinstance(id_str, str):
            return 'a'
        
        # Try to extract valid characters
        valid_chars = ''.join(c for c in id_str.lower() if c.isalpha())
        if valid_chars:
            # Limit to reasonable length and ensure it's a valid perf_id format
            if len(valid_chars) <= 2:  # a, b, c... z, aa, ab, etc.
                return valid_chars
            else:
                return 'a'  # Default if too long
        else:
            return 'a'
    
    return id_str


def _fix_phy_section(phy_data: Dict[str, Any], expected_review_ids: Set[int]) -> Dict[str, Any]:
    """Fix validation errors in the physical section.
    
    Args:
        phy_data: Physical section data
        expected_review_ids: Set of valid review IDs
        
    Returns:
        Fixed physical section data
    """
    if not isinstance(phy_data, dict):
        return {}
    
    fixed_phy = {}
    for physical, details in phy_data.items():
        if not isinstance(details, dict):
            continue
        
        fixed_details = {}
        for pid_detail, sentiments in details.items():
            # Fix PID@DETAIL format
            if '@' not in pid_detail:
                # Try to split on common separators
                if ' ' in pid_detail:
                    parts = pid_detail.split(' ', 1)
                    pid = _fix_invalid_id_format(parts[0], 'PID')
                    detail = parts[1] if len(parts) > 1 else 'Unknown'
                    pid_detail = f"{pid}@{detail}"
                else:
                    pid = _fix_invalid_id_format(pid_detail, 'PID')
                    pid_detail = f"{pid}@Unknown"
            
            # Fix sentiments
            if isinstance(sentiments, dict):
                fixed_sentiments = {}
                for sent, rid_list in sentiments.items():
                    fixed_sent = _fix_invalid_sentiment(sent)
                    fixed_rids = _fix_invalid_review_ids(rid_list, expected_review_ids)
                    if fixed_rids:  # Only include if there are valid RIDs
                        fixed_sentiments[fixed_sent] = fixed_rids
                
                if fixed_sentiments:  # Only include if there are valid sentiments
                    fixed_details[pid_detail] = fixed_sentiments
        
        if fixed_details:  # Only include if there are valid details
            fixed_phy[physical] = fixed_details
    
    return fixed_phy


def _fix_perf_section(perf_data: Dict[str, Any], expected_review_ids: Set[int]) -> Dict[str, Any]:
    """Fix validation errors in the performance section.
    
    Args:
        perf_data: Performance section data
        expected_review_ids: Set of valid review IDs
        
    Returns:
        Fixed performance section data
    """
    if not isinstance(perf_data, dict):
        return {}
    
    fixed_perf = {}
    for perf, details in perf_data.items():
        if not isinstance(details, dict):
            continue
        
        fixed_details = {}
        for perf_id_detail, sentiments in details.items():
            # Fix perf_id@DETAIL format
            if '@' not in perf_id_detail:
                # Try to split on common separators
                if ' ' in perf_id_detail:
                    parts = perf_id_detail.split(' ', 1)
                    perf_id = _fix_invalid_id_format(parts[0], 'perf_id')
                    detail = parts[1] if len(parts) > 1 else 'Unknown'
                    perf_id_detail = f"{perf_id}@{detail}"
                else:
                    perf_id = _fix_invalid_id_format(perf_id_detail, 'perf_id')
                    perf_id_detail = f"{perf_id}@Unknown"
            
            # Fix sentiments and reasons
            if isinstance(sentiments, dict):
                fixed_sentiments = {}
                for sent, reasons in sentiments.items():
                    fixed_sent = _fix_invalid_sentiment(sent)
                    
                    if isinstance(reasons, dict):
                        fixed_reasons = {}
                        for reason, rid_list in reasons.items():
                            # Fix reason format (should be PID, perf_id, or '?')
                            if reason != '?':
                                # Try to fix invalid reason references
                                reason_parts = [r.strip() for r in reason.split(',')]
                                fixed_parts = []
                                for part in reason_parts:
                                    if (ReviewHierarchyValidator.validate_id_format(part, 'PID') or 
                                        ReviewHierarchyValidator.validate_id_format(part, 'perf_id')):
                                        fixed_parts.append(part)
                                    else:
                                        # Replace invalid part with '?'
                                        fixed_parts.append('?')
                                fixed_reason = ','.join(fixed_parts) if fixed_parts else '?'
                            else:
                                fixed_reason = '?'
                            
                            fixed_rids = _fix_invalid_review_ids(rid_list, expected_review_ids)
                            if fixed_rids:  # Only include if there are valid RIDs
                                fixed_reasons[fixed_reason] = fixed_rids
                        
                        if fixed_reasons:  # Only include if there are valid reasons
                            fixed_sentiments[fixed_sent] = fixed_reasons
                
                if fixed_sentiments:  # Only include if there are valid sentiments
                    fixed_details[perf_id_detail] = fixed_sentiments
        
        if fixed_details:  # Only include if there are valid details
            fixed_perf[perf] = fixed_details
    
    return fixed_perf


def _fix_use_section(use_data: Dict[str, Any], expected_review_ids: Set[int]) -> Dict[str, Any]:
    """Fix validation errors in the use case section.
    
    Args:
        use_data: Use case section data
        expected_review_ids: Set of valid review IDs
        
    Returns:
        Fixed use case section data
    """
    if not isinstance(use_data, dict):
        return {}
    
    fixed_use = {}
    for use_case, sentiments in use_data.items():
        if not isinstance(sentiments, dict):
            continue
        
        fixed_sentiments = {}
        for sent, reasons in sentiments.items():
            fixed_sent = _fix_invalid_sentiment(sent)
            
            if isinstance(reasons, dict):
                fixed_reasons = {}
                for reason, rid_list in reasons.items():
                    # Fix reason format (should be PID, perf_id, or '?')
                    if reason != '?':
                        # Try to fix invalid reason references
                        reason_parts = [r.strip() for r in reason.split(',')]
                        fixed_parts = []
                        for part in reason_parts:
                            if (ReviewHierarchyValidator.validate_id_format(part, 'PID') or 
                                ReviewHierarchyValidator.validate_id_format(part, 'perf_id')):
                                fixed_parts.append(part)
                            else:
                                # Replace invalid part with '?'
                                fixed_parts.append('?')
                        fixed_reason = ','.join(fixed_parts) if fixed_parts else '?'
                    else:
                        fixed_reason = '?'
                    
                    fixed_rids = _fix_invalid_review_ids(rid_list, expected_review_ids)
                    if fixed_rids:  # Only include if there are valid RIDs
                        fixed_reasons[fixed_reason] = fixed_rids
                
                if fixed_reasons:  # Only include if there are valid reasons
                    fixed_sentiments[fixed_sent] = fixed_reasons
        
        if fixed_sentiments:  # Only include if there are valid sentiments
            fixed_use[use_case] = fixed_sentiments
    
    return fixed_use


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
        retry_ctx: ValidationResult, 
        ctx: ReviewExtractionContext,
        previous_response: str
    ) -> str:
        """Build retry prompt using shared retry template."""
        
        # retry_ctx is now a ValidationResult object
        if not isinstance(retry_ctx, ValidationResult):
            # Fallback for unexpected retry context format
            return f"{original_prompt}\n\nPlease fix the errors and provide a valid JSON response."
        
        # Extract error_categories from ValidationResult
        error_categories = retry_ctx.error_categories
        
        # Format error details
        error_lines = []
        for category, errors in error_categories.items():
            if errors:  # Only include categories with errors
                error_lines.append(f"\n{category.upper().replace('_', ' ')}:")
                for error in errors:
                    error_lines.append(f"  • {error}")
        
        error_details = "\n".join(error_lines) if error_lines else "Unknown validation errors"
        
        # Include the previous response in the retry instructions
        previous_response_section = f"""
=== PREVIOUS RESPONSE (INCORRECT) ===
{previous_response}
=== END PREVIOUS RESPONSE ===

"""
        
        # Use the shared retry template with structured error details and previous response
        try:
            retry_block = _RETRY_PROMPT_TEMPLATE.replace("{{error_details}}", error_details)
            return f"{original_prompt}\n\n{previous_response_section}{retry_block}"
        except Exception as exc:
            # Fallback if template replacement fails
            return f"{original_prompt}\n\n=== PREVIOUS RESPONSE (INCORRECT) ===\n{previous_response}\n=== END PREVIOUS RESPONSE ===\n\nValidation failed with errors: {error_details}\n\nPlease fix the errors and provide a valid JSON response."

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

    # --------------------- Error fixing methods -------------------------

    def _attempt_error_fixing(self, raw_response: str, ctx: ReviewExtractionContext) -> Optional[ReviewExtractionResult]:
        """Attempt to automatically fix validation errors in the response.
        
        This method tries to fix common validation errors like:
        - Invalid review IDs (filter out invalid ones)
        - Invalid sentiment values (map to '+' or '-')
        - Invalid ID formats (generate valid IDs)
        - Missing required sections (create empty ones)
        - Invalid JSON structure (try to extract valid parts)
        
        Args:
            raw_response: Raw LLM response that failed validation
            ctx: Review extraction context
            
        Returns:
            Fixed ReviewExtractionResult if fixable, None if not fixable
        """
        try:
            # Try to extract JSON from the response
            json_text = extract_json(raw_response)
            hierarchy = json.loads(json_text)
            
            if not isinstance(hierarchy, dict):
                logger.warning("Response is not a JSON object, cannot fix")
                return None
            
            # Ensure all required sections exist
            if 'phy' not in hierarchy:
                hierarchy['phy'] = {}
            if 'perf' not in hierarchy:
                hierarchy['perf'] = {}
            if 'use' not in hierarchy:
                hierarchy['use'] = {}
            
            # Fix each section
            hierarchy['phy'] = _fix_phy_section(hierarchy['phy'], ctx.expected_review_ids)
            hierarchy['perf'] = _fix_perf_section(hierarchy['perf'], ctx.expected_review_ids)
            hierarchy['use'] = _fix_use_section(hierarchy['use'], ctx.expected_review_ids)
            
            # Validate the fixed hierarchy
            validation_ctx = ReviewValidationContext(
                expected_review_ids=ctx.expected_review_ids,
                product_title=ctx.product_title,
                asin=ctx.asin
            )
            
            validation_result = parse_and_validate_review_response(
                json.dumps(hierarchy, ensure_ascii=False), 
                validation_ctx
            )
            
            if validation_result.ok:
                # Successfully fixed!
                aspects_count = count_extracted_aspects(hierarchy)
                logger.info(f"Successfully fixed validation errors for product {ctx.asin}")
                return ReviewExtractionResult(
                    review_hierarchy=hierarchy,
                    aspects_extracted=aspects_count
                )
            else:
                # Still has validation errors after fixing
                logger.warning(f"Could not fix all validation errors for product {ctx.asin}: {validation_result.error_categories}")
                return None
                
        except Exception as exc:
            logger.warning(f"Error during automatic fixing for product {ctx.asin}: {exc}")
            return None

    # --------------------- Override execute method for error fixing -------------------------

    async def execute(self, ctx: ReviewExtractionContext) -> ReviewExtractionResult:
        """Override execute method to add automatic error fixing when all retries are exhausted."""
        
        try:
            # Try normal execution first
            return await super().execute(ctx)
            
        except LLMCallError as exc:
            # All retries exhausted, try automatic error fixing
            logger.info(f"All retries exhausted for product {ctx.asin}, attempting automatic error fixing")
            
            # Check if we have the last failed response
            if exc.last_response:
                # Attempt to fix the validation errors
                fixed_result = self._attempt_error_fixing(exc.last_response, ctx)
                if fixed_result:
                    logger.info(f"Successfully fixed validation errors for product {ctx.asin}")
                    return fixed_result
                else:
                    logger.warning(f"Could not fix validation errors for product {ctx.asin}, proceeding with split-and-conquer")
            else:
                logger.warning(f"No last response available for error fixing for product {ctx.asin}")
            
            # If error fixing failed or no response available, proceed with normal split-and-conquer
            raise exc