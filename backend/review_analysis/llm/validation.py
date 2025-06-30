"""Review analysis validation system with modernized structure.

This module ports the comprehensive validation logic from the legacy system
while modernizing the structure to integrate with the core pipeline framework.
"""

import re
import json
from typing import Dict, List, Tuple, Set, Any
from dataclasses import dataclass

from core.utils.llm_utils import ValidationResult
from core.utils.llm_utils import extract_json


@dataclass
class ReviewValidationContext:
    """Context for review-specific validation."""
    expected_review_ids: Set[int]
    product_title: str
    asin: str


class ReviewValidationError:
    """Structured error information for validation failures."""
    
    def __init__(self, category: str, message: str):
        self.category = category  # format_errors, validation_errors, completeness_errors
        self.message = message
    
    def __str__(self) -> str:
        result = f"{self.category}: {self.message}"
        return result


class ReviewHierarchyValidator:
    """Validates the hierarchical review extraction JSON structure.
    
    Ports all validation logic from the legacy system with modernized structure.
    """
    
    @staticmethod
    def validate_id_format(id_str: str, id_type: str) -> bool:
        """Validate ID format according to prompt rules.
        
        Args:
            id_str: ID string to validate
            id_type: Either 'PID' (A, B, C...) or 'perf_id' (a, b, c...)
        
        Returns:
            True if valid format
        """
        if id_type == 'PID':
            # PID: A, B, C... Z, AA, AB, AC...
            pattern = r'^[A-Z]+$'
        elif id_type == 'perf_id':
            # perf_id: a, b, c... z, aa, ab, ac...
            pattern = r'^[a-z]+$'
        else:
            return False
        
        return bool(re.match(pattern, id_str))
    
    @staticmethod
    def validate_sentiment(sent: str) -> bool:
        """Validate sentiment is either '+' or '-'."""
        return sent in ['+', '-']
    
    @staticmethod
    def validate_review_ids(ids: Any, expected_review_ids: Set[int]) -> Tuple[bool, str]:
        """Validate review IDs are valid integers and exist in expected set.
        
        Args:
            ids: List of review IDs
            expected_review_ids: Set of valid review IDs
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(ids, list):
            return False, "Review IDs must be a list"
        
        invalid_ids = []
        missing_ids = []
        
        for id_val in ids:
            try:
                id_int = int(id_val)
                if id_int not in expected_review_ids:
                    missing_ids.append(id_int)
            except (ValueError, TypeError):
                invalid_ids.append(id_val)
        
        errors = []
        if invalid_ids:
            errors.append(f"Invalid ID format: {invalid_ids}")
        if missing_ids:
            errors.append(f"IDs not in input: {missing_ids}")
        
        return len(errors) == 0, "; ".join(errors)
    
    def validate_phy_section(self, phy_data: Dict[str, Any], expected_review_ids: Set[int]) -> List[ReviewValidationError]:
        """Validate the 'phy' section structure.
        
        The 'phy' section contains physical product characteristics organized as:
        {
            "<PHYSICAL>": {
                "<PID>@<DETAIL>": {
                    "<SENT>": [RID, RID, ...]
                }
            }
        }
        
        Placeholder Definitions:
        - <PHYSICAL>: Components or inherent physical properties without external interaction
        - <PID>: Unique ID for physical aspect, starting from A. After Z, continue with AA, AB, etc.
        - <DETAIL>: Self-contained detail summarized from the reviews
        - <SENT>: Sentiment polarity (- for negative, + for positive)
        - RID: Review IDs mentioning the <DETAIL>
        
        Examples:
        ✅ Correct:
        {
            "<PHYSICAL>": {
                "<PID>@<DETAIL>": {"<SENT>": [RID, ...]},
                "<PID>@<DETAIL>": {"<SENT>": [RID, ...]}
            }
        }
        
        ❌ Incorrect:
        {
            "<PHYSICAL>": {
                "<DETAIL>": {"<SENT>": [RID]},  # Missing <PID>@ format
                "<PID>@<DETAIL>": {"positive": [RID]}  # Wrong <SENT> key
            }
        }
        
        Args:
            phy_data: The 'phy' section data to validate
            expected_review_ids: Set of valid RID values from input
            
        Returns:
            List of validation errors found in the physical section
        """
        errors = []
        
        if not isinstance(phy_data, dict):
            errors.append(ReviewValidationError(
                "format_errors",
                f"'phy' section must be a JSON object, got {type(phy_data).__name__}. Use format: {{'<PHYSICAL>': {{'<PID>@<DETAIL>': {{'<SENT>': [RID]}}}}}}"
            ))
            return errors
        
        for physical, details in phy_data.items():
            if not isinstance(details, dict):
                errors.append(ReviewValidationError(
                    "format_errors",
                    f"Physical aspect '{physical}' must be a JSON object with <PID>@<DETAIL> keys (got {type(details).__name__}). Use format: {{'<PID>@<DETAIL>': {{'<SENT>': [RID]}}}}"
                ))
                continue
            
            for pid_detail, sentiments in details.items():
                # Validate <PID>@<DETAIL> format
                if '@' not in pid_detail:
                    errors.append(ReviewValidationError(
                        "validation_errors",
                        f"Invalid format '{pid_detail}' in physical aspect '{physical}' - must be <PID>@<DETAIL>. Use format: <PID>@<DETAIL> where <PID> is A,B,C... and <DETAIL> is aspect detail"
                    ))
                    continue
                
                pid, detail = pid_detail.split('@', 1)
                if not self.validate_id_format(pid, 'PID'):
                    errors.append(ReviewValidationError(
                        "validation_errors",
                        f"Invalid <PID> format '{pid}' in '{pid_detail}' - must be A, B, C... Z, AA, AB, etc."
                    ))
                
                if not isinstance(sentiments, dict):
                    errors.append(ReviewValidationError(
                        "format_errors",
                        f"Sentiments for '{pid_detail}' must be a JSON object with <SENT> keys (got {type(sentiments).__name__}). Use format: {{'<SENT>': [RID]}} where <SENT> is '+' or '-'"
                    ))
                    continue
                
                for sent, ids in sentiments.items():
                    if not self.validate_sentiment(sent):
                        errors.append(ReviewValidationError(
                            "validation_errors",
                            f"Invalid <SENT> '{sent}' in '{pid_detail}' - must be '+' for positive or '-' for negative"
                        ))
                    
                    is_valid, id_error = self.validate_review_ids(ids, expected_review_ids)
                    if not is_valid:
                        errors.append(ReviewValidationError(
                            "validation_errors",
                            f"Invalid RID in {pid_detail}[{sent}] in physical aspect '{physical}': {id_error}. Use only RID from input: {sorted(list(expected_review_ids))}"
                        ))
        
        return errors
    
    def validate_perf_section(self, perf_data: Dict[str, Any], expected_review_ids: Set[int]) -> List[ReviewValidationError]:
        """Validate the 'perf' section structure.
        
        The 'perf' section contains performance characteristics organized as:
        {
            "<PERF>": {
                "<perf_id>@<DETAIL>": {
                    "<SENT>": {"<PERF_REASON>": [RID, RID, ...]}
                }
            }
        }
        
        Placeholder Definitions:
        - <PERF>: Product performance or behaviors under various conditions
        - <perf_id>: Unique ID for performance, starting from a. After z, continue with aa, ab, etc.
        - <DETAIL>: Self-contained detail summarized from the reviews
        - <SENT>: Sentiment polarity (- for negative, + for positive)
        - <PERF_REASON>: <PID> of <PHYSICAL> causing the <PERF>, or "?" if no reason mentioned
        - RID: Review IDs mentioning the aspect
        
        Examples:
        ✅ Correct:
        {
            "<PERF>": {
                "<perf_id>@<DETAIL>": {
                    "<SENT>": {"<PERF_REASON>": [RID, ...], "?": [RID, ...]}
                }
            }
        }
        
        ❌ Incorrect:
        {
            "<PERF>": {
                "<DETAIL>": {"<SENT>": [RID]},  # Missing <perf_id>@ format
                "<perf_id>@<DETAIL>": {"<SENT>": [RID]}  # Missing <PERF_REASON> structure
            }
        }
        
        Args:
            perf_data: The 'perf' section data to validate
            expected_review_ids: Set of valid RID values from input
            
        Returns:
            List of validation errors found in the performance section
        """
        errors = []
        
        if not isinstance(perf_data, dict):
            errors.append(ReviewValidationError(
                "format_errors",
                f"'perf' section must be a JSON object, got {type(perf_data).__name__}"
            ))
            return errors
        
        for perf, details in perf_data.items():
            if not isinstance(details, dict):
                errors.append(ReviewValidationError(
                    "format_errors",
                    f"Performance aspect '{perf}' must be a JSON object with perf_id@DETAIL keys (got {type(details).__name__})"
                ))
                continue
            
            for perf_id_detail, sentiments in details.items():
                # Validate perf_id@DETAIL format
                if '@' not in perf_id_detail:
                    errors.append(ReviewValidationError(
                        "validation_errors",
                        f"Invalid format '{perf_id_detail}' in performance aspect '{perf}' - must be perf_id@DETAIL"
                    ))
                    continue
                
                perf_id, detail = perf_id_detail.split('@', 1)
                if not self.validate_id_format(perf_id, 'perf_id'):
                    errors.append(ReviewValidationError(
                        "validation_errors",
                        f"Invalid perf_id format '{perf_id}' in '{perf_id_detail}' - must be a, b, c... z, aa, ab..."
                    ))
                
                if not isinstance(sentiments, dict):
                    errors.append(ReviewValidationError(
                        "format_errors",
                        f"Sentiments for '{perf_id_detail}' must be a JSON object with '+'/'-' keys (got {type(sentiments).__name__})"
                    ))
                    continue
                
                for sent, reasons in sentiments.items():
                    if not self.validate_sentiment(sent):
                        errors.append(ReviewValidationError(
                            "validation_errors",
                            f"Invalid sentiment '{sent}' in '{perf_id_detail}' - must be '+' or '-'"
                        ))
                    
                    if not isinstance(reasons, dict):
                        errors.append(ReviewValidationError(
                            "format_errors",
                            f"Reasons for '{perf_id_detail}[{sent}]' must be a JSON object (got {type(reasons).__name__})"
                        ))
                        continue
                    
                    for reason, ids in reasons.items():
                        # Validate <PERF_REASON> format
                        if reason != "?":
                            # Split by comma and validate each part
                            reason_parts = [r.strip() for r in reason.split(',')]
                            invalid_parts = []
                            for part in reason_parts:
                                if not (self.validate_id_format(part, 'PID') or self.validate_id_format(part, 'perf_id')):
                                    invalid_parts.append(part)
                            
                            if invalid_parts:
                                errors.append(ReviewValidationError(
                                    "validation_errors",
                                    f"Invalid <PERF_REASON> format '{reason}' in '{perf_id_detail}[{sent}]' - invalid parts: {invalid_parts}. Use <PERF_REASON> format: <PID>, <perf_id>, '?', or combinations like 'A,b'. Each part must be <PID>, <perf_id>, or '?'"
                                ))
                        
                        is_valid, id_error = self.validate_review_ids(ids, expected_review_ids)
                        if not is_valid:
                            errors.append(ReviewValidationError(
                                "validation_errors",
                                f"Invalid review IDs in {perf_id_detail}[{sent}][{reason}] in performance aspect '{perf}': {id_error}"
                            ))
        
        return errors
    
    def validate_use_section(self, use_data: Dict[str, Any], expected_review_ids: Set[int]) -> List[ReviewValidationError]:
        """Validate the 'use' section structure.
        
        The 'use' section contains use cases organized as:
        {
            "<USE>": {
                "<SENT>": {"<USE_REASON>": [RID, RID, ...]}
            }
        }
        
        Placeholder Definitions:
        - <USE>: Specific application, applicable object, method, tool, or environment for the product
        - <SENT>: Sentiment polarity (- for negative, + for positive)
        - <USE_REASON>: <perf_id> or <PID> causing the <USE> sentiment, or "?" if no reason
        - RID: Review IDs mentioning the use case
        
        Examples:
        ✅ Correct:
        {
            "<USE>": {
                "<SENT>": {"<USE_REASON>": [RID, ...], "?": [RID, ...]}
            }
        }
        
        ❌ Incorrect:
        {
            "<USE>": {
                "<SENT>": [RID]  # Missing <USE_REASON> structure
            }
        }
        
        Args:
            use_data: The 'use' section data to validate
            expected_review_ids: Set of valid RID values from input
            
        Returns:
            List of validation errors found in the use section
        """
        errors = []
        
        if not isinstance(use_data, dict):
            errors.append(ReviewValidationError(
                "format_errors",
                f"'use' section must be a JSON object, got {type(use_data).__name__}"
            ))
            return errors
        
        for use, sentiments in use_data.items():
            if not isinstance(sentiments, dict):
                errors.append(ReviewValidationError(
                    "format_errors",
                    f"Use case '{use}' must be a JSON object with '+'/'-' keys (got {type(sentiments).__name__})"
                ))
                continue
            
            for sent, reasons in sentiments.items():
                if not self.validate_sentiment(sent):
                    errors.append(ReviewValidationError(
                        "validation_errors",
                        f"Invalid sentiment '{sent}' in use case '{use}' - must be '+' or '-'"
                    ))
                
                if not isinstance(reasons, dict):
                    errors.append(ReviewValidationError(
                        "format_errors",
                        f"Reasons for '{use}[{sent}]' must be a JSON object (got {type(reasons).__name__})"
                    ))
                    continue
                
                for reason, ids in reasons.items():
                    # Validate <USE_REASON> format
                    if reason != "?":
                        # Split by comma and validate each part
                        reason_parts = [r.strip() for r in reason.split(',')]
                        invalid_parts = []
                        for part in reason_parts:
                            if not (self.validate_id_format(part, 'PID') or self.validate_id_format(part, 'perf_id')):
                                invalid_parts.append(part)
                        
                        if invalid_parts:
                            errors.append(ReviewValidationError(
                                "validation_errors",
                                f"Invalid <USE_REASON> format '{reason}' in '{use}[{sent}]' - invalid parts: {invalid_parts}. Use <USE_REASON> format: <PID>, <perf_id>, '?', or combinations like 'A,b'. Each part must be <PID>, <perf_id>, or '?'"
                            ))
                    
                    is_valid, id_error = self.validate_review_ids(ids, expected_review_ids)
                    if not is_valid:
                        errors.append(ReviewValidationError(
                            "validation_errors",
                            f"Invalid review IDs in {use}[{sent}][{reason}] in use case '{use}': {id_error}"
                        ))
        
        return errors
    
    def validate_cross_references(self, result: Dict[str, Any]) -> List[ReviewValidationError]:
        """Validate sentiment agreement between perf/use and their reasons.
        
        Critical Rules from prompt:
        - <PERF_REASON> and <PERF> must have same <SENT> in same RID
        - <USE_REASON> and <USE> must have same <SENT> in same RID
        
        Args:
            result: Complete parsed JSON result
            
        Returns:
            List of cross-reference validation errors
        """
        errors = []
        
        # Build RID-sentiment maps for all <PID> and <perf_id>
        pid_rid_sentiments = {}  # {RID: {<PID>: <SENT>}}
        perf_id_rid_sentiments = {}  # {RID: {<perf_id>: <SENT>}}
        
        # Extract sentiments from phy section for <PID> references
        if 'phy' in result and isinstance(result['phy'], dict):
            for physical_category, details in result['phy'].items():
                if isinstance(details, dict):
                    for pid_detail, sentiments in details.items():
                        if '@' in pid_detail and isinstance(sentiments, dict):
                            pid = pid_detail.split('@', 1)[0]
                            for sentiment, rid_list in sentiments.items():
                                if isinstance(rid_list, list) and sentiment in ['+', '-']:
                                    for rid in rid_list:
                                        if isinstance(rid, int):
                                            if rid not in pid_rid_sentiments:
                                                pid_rid_sentiments[rid] = {}
                                            pid_rid_sentiments[rid][pid] = sentiment
        
        # Extract sentiments from perf section for <perf_id> references
        if 'perf' in result and isinstance(result['perf'], dict):
            for perf_category, details in result['perf'].items():
                if isinstance(details, dict):
                    for perf_id_detail, sentiments in details.items():
                        if '@' in perf_id_detail and isinstance(sentiments, dict):
                            perf_id = perf_id_detail.split('@', 1)[0]
                            for sentiment, reasons in sentiments.items():
                                if isinstance(reasons, dict) and sentiment in ['+', '-']:
                                    for reason, rid_list in reasons.items():
                                        if isinstance(rid_list, list):
                                            for rid in rid_list:
                                                if isinstance(rid, int):
                                                    if rid not in perf_id_rid_sentiments:
                                                        perf_id_rid_sentiments[rid] = {}
                                                    perf_id_rid_sentiments[rid][perf_id] = sentiment
        
        # Validate perf section cross-references
        if 'perf' in result and isinstance(result['perf'], dict):
            for perf_category, details in result['perf'].items():
                if isinstance(details, dict):
                    for perf_id_detail, sentiments in details.items():
                        if isinstance(sentiments, dict):
                            for sentiment, reasons in sentiments.items():
                                if isinstance(reasons, dict) and sentiment in ['+', '-']:
                                    for reason, rid_list in reasons.items():
                                        if isinstance(rid_list, list) and reason != "?":
                                            # Parse reason (could be comma-separated)
                                            reason_parts = [r.strip() for r in reason.split(',')]
                                            for part in reason_parts:
                                                # Check <PID> references
                                                if self.validate_id_format(part, 'PID'):
                                                    for rid in rid_list:
                                                        if isinstance(rid, int):
                                                            if rid in pid_rid_sentiments and part in pid_rid_sentiments[rid]:
                                                                expected_sentiment = pid_rid_sentiments[rid][part]
                                                                if sentiment != expected_sentiment:
                                                                    errors.append(ReviewValidationError(
                                                                        "validation_errors",
                                                                        f"Sentiment mismatch: RID {rid} has sentiment '{sentiment}' for {perf_id_detail} "
                                                                        f"but '{expected_sentiment}' for <PERF_REASON> {part}. Same RID must have same sentiment for <PERF> and <PERF_REASON>. "
                                                                        f"Double check whether {perf_id_detail} is mentioned in the review {rid}, if its sentiment is {expected_sentiment}, if the <PERF_REASON> {part} is mentioned as a reason for the {perf_id_detail} in the review {rid}, and if its sentiment is {sentiment}"
                                                                    ))
                                                # Check <perf_id> references
                                                elif self.validate_id_format(part, 'perf_id'):
                                                    for rid in rid_list:
                                                        if isinstance(rid, int):
                                                            if rid in perf_id_rid_sentiments and part in perf_id_rid_sentiments[rid]:
                                                                expected_sentiment = perf_id_rid_sentiments[rid][part]
                                                                if sentiment != expected_sentiment:
                                                                    errors.append(ReviewValidationError(
                                                                        "validation_errors",
                                                                        f"Sentiment mismatch: RID {rid} has sentiment '{sentiment}' for {perf_id_detail} "
                                                                        f"but '{expected_sentiment}' for <PERF_REASON> {part}. Same RID must have same sentiment for <PERF> and <PERF_REASON>. "
                                                                        f"Double check whether {perf_id_detail} is mentioned in the review {rid}, if its sentiment is {expected_sentiment}, if the <PERF_REASON> {part} is mentioned as a reason for the {perf_id_detail} in the review {rid}, and if its sentiment is {sentiment}"
                                                                    ))
        
        # Validate use section cross-references
        if 'use' in result and isinstance(result['use'], dict):
            for use_case, sentiments in result['use'].items():
                if isinstance(sentiments, dict):
                    for sentiment, reasons in sentiments.items():
                        if isinstance(reasons, dict) and sentiment in ['+', '-']:
                            for reason, rid_list in reasons.items():
                                if isinstance(rid_list, list) and reason != "?":
                                    # Parse reason (could be comma-separated)
                                    reason_parts = [r.strip() for r in reason.split(',')]
                                    for part in reason_parts:
                                        # Check <PID> references
                                        if self.validate_id_format(part, 'PID'):
                                            for rid in rid_list:
                                                if isinstance(rid, int):
                                                    if rid in pid_rid_sentiments and part in pid_rid_sentiments[rid]:
                                                        expected_sentiment = pid_rid_sentiments[rid][part]
                                                        if sentiment != expected_sentiment:
                                                            errors.append(ReviewValidationError(
                                                                "validation_errors",
                                                                f"Sentiment mismatch: RID {rid} has sentiment '{sentiment}' for <USE> '{use_case}' "
                                                                f"but '{expected_sentiment}' for <USE_REASON> {part}. Same RID must have same sentiment for <USE> and <USE_REASON>. "
                                                                f"Double check whether {use_case} is mentioned in the review {rid}, if its sentiment is {expected_sentiment}, if the <USE_REASON> {part} is mentioned as a reason for the {use_case} in the review {rid}, and if its sentiment is {sentiment}"
                                                            ))
                                        # Check <perf_id> references
                                        elif self.validate_id_format(part, 'perf_id'):
                                            for rid in rid_list:
                                                if isinstance(rid, int):
                                                    if rid in perf_id_rid_sentiments and part in perf_id_rid_sentiments[rid]:
                                                        expected_sentiment = perf_id_rid_sentiments[rid][part]
                                                        if sentiment != expected_sentiment:
                                                            errors.append(ReviewValidationError(
                                                                "validation_errors",
                                                                f"Sentiment mismatch: RID {rid} has sentiment '{sentiment}' for <USE> '{use_case}' "
                                                                f"but '{expected_sentiment}' for <USE_REASON> {part}. Same RID must have same sentiment for <USE> and <USE_REASON>. "
                                                                f"Double check whether {use_case} is mentioned in the review {rid}, if its sentiment is {expected_sentiment}, if the <USE_REASON> {part} is mentioned as a reason for the {use_case} in the review {rid}, and if its sentiment is {sentiment}"
                                                            ))
        
        return errors
    
    def validate_hierarchy_structure(self, result: Dict[str, Any], validation_ctx: ReviewValidationContext) -> List[ReviewValidationError]:
        """Validate the complete hierarchical review extraction JSON structure.
        
        Args:
            result: Parsed JSON result
            validation_ctx: Review validation context
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required top-level sections
        required_sections = ['phy', 'perf', 'use']
        for section in required_sections:
            if section not in result:
                errors.append(ReviewValidationError(
                    "completeness_errors",
                    f"Missing required section: '{section}'"
                ))
                continue
            
            if not isinstance(result[section], dict):
                errors.append(ReviewValidationError(
                    "format_errors",
                    f"Section '{section}' must be a JSON object containing aspect categories (got {type(result[section]).__name__})"
                ))
                continue
        
        # Validate each section
        if 'phy' in result and isinstance(result['phy'], dict):
            errors.extend(self.validate_phy_section(result['phy'], validation_ctx.expected_review_ids))
        
        if 'perf' in result and isinstance(result['perf'], dict):
            errors.extend(self.validate_perf_section(result['perf'], validation_ctx.expected_review_ids))
        
        if 'use' in result and isinstance(result['use'], dict):
            errors.extend(self.validate_use_section(result['use'], validation_ctx.expected_review_ids))
        
        # Validate cross-references (sentiment agreement between sections)
        # TODO: Re-enable this once we have a way to handle the cross-references
        # errors.extend(self.validate_cross_references(result))
        
        return errors


def create_retry_context(validation_errors: List[ReviewValidationError], 
                        response_text: str, validation_ctx: ReviewValidationContext) -> Dict[str, Any]:
    """Create standardized retry context from validation errors.
    
    Args:
        validation_errors: List of validation errors
        response_text: Original response text
        validation_ctx: Validation context
    
    Returns:
        Standardized retry context for prompt building
    """
    # Categorize errors
    error_categories = {
        "format_errors": [],
        "validation_errors": [],
        "completeness_errors": []
    }
    
    for error in validation_errors:
        error_categories[error.category].append(str(error))
    
    # Build content sections
    content_sections = {}
    
    # Try to extract JSON for better error display
    json_text = ""
    try:
        json_text = extract_json(response_text)
    except Exception:
        json_text = "(No valid JSON found)"
    
    # Previous attempt section
    if json_text and json_text != "(No valid JSON found)":
        content_sections["previous_attempt"] = {
            "title": "YOUR PREVIOUS JSON ATTEMPT",
            "content": json_text[:500] + "..." if len(json_text) > 500 else json_text
        }
    else:
        content_sections["previous_attempt"] = {
            "title": "YOUR PREVIOUS RESPONSE",
            "content": response_text[:500] + "..." if len(response_text) > 500 else response_text
        }
    
    # Context section
    content_sections["product_context"] = {
        "title": "PRODUCT CONTEXT",
        "content": f"ASIN: {validation_ctx.asin}\nProduct: {validation_ctx.product_title}\nExpected Review IDs: {sorted(list(validation_ctx.expected_review_ids))}"
    }
    
    # Create summary
    all_errors = validation_errors
    issues_summary = " | ".join([e.message for e in all_errors[:3]])
    if len(all_errors) > 3:
        issues_summary += f" (and {len(all_errors)-3} more)"
    
    return {
        "issues_summary": issues_summary,
        "error_categories": error_categories,
        "content_sections": content_sections
    }


def parse_and_validate_review_response(response_text: str, validation_ctx: ReviewValidationContext) -> ValidationResult:
    """Parse and validate review hierarchy extraction response.
    
    Args:
        response_text: Raw LLM response text
        validation_ctx: Review validation context
    
    Returns:
        ValidationResult with ok flag and retry context
    """
    validator = ReviewHierarchyValidator()
    
    # Try to extract and parse JSON
    try:
        json_text = extract_json(response_text)
        result = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        # JSON parsing failed
        return ValidationResult(ok=False, error_categories={"format_errors": [f"Could not extract valid JSON: {e}"]})
    
    # Validate structure
    if not isinstance(result, dict):
        return ValidationResult(ok=False, error_categories={"format_errors": ["Response must be a JSON object"]})
    
    # Perform detailed validation
    validation_errors = validator.validate_hierarchy_structure(result, validation_ctx)
    
    if not validation_errors:
        return ValidationResult(ok=True, error_categories={})
    
    # Create retry context with all errors
    retry_ctx = create_retry_context(validation_errors, response_text, validation_ctx)
    
    # Convert to error categories format
    error_categories = {}
    for error in validation_errors:
        if error.category not in error_categories:
            error_categories[error.category] = []
        error_categories[error.category].append(error.message)
    
    return ValidationResult(ok=False, error_categories=error_categories)