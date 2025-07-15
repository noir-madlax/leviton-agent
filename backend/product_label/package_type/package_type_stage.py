"""
Package type specific stage implementation

This module provides a specialized stage for package type labeling that handles
the Multiple-{number} format validation and provides consistent examples.
"""

import json
import logging
from typing import Dict, List

from core.utils.llm_utils import ValidationResult
from backend.product_label.base.base_stage import BaseStage
from backend.product_label.base.models import LabelingContext

logger = logging.getLogger(__name__)

class PackageTypeStage(BaseStage):
    """Specialized stage for package type labeling with Multiple-{number} support"""
    
    def _is_valid_label(self, label: str, valid_labels: set) -> bool:
        """Package type specific label validation with Multiple-{number} support"""
        # Check exact match first for base labels
        if label in valid_labels:
            return True
            
        # Check for Multiple-{number} format if "Multiple" is in valid labels
        if "Multiple" in valid_labels and label.startswith("Multiple-"):
            # Extract the number part
            try:
                number_part = label[9:]  # Remove "Multiple-" prefix
                number = int(number_part)
                # Validate it's a positive integer
                return number > 0
            except ValueError:
                return False
                
        return False
        
    def _build_output_format_example(self, available_labels: Dict[str, str], num_products: int) -> str:
        """Build output format example with consistent Multiple-{number} format"""
        
        # For package type, we want to show realistic examples including Multiple-N format
        package_type_examples = {
            "0": "Single",
            "1": "Multiple-2", 
            "2": "Multiple-3",
            "3": "Bundle"
        }
        
        # Limit to actual number of products
        example_assignments = {}
        for i in range(min(len(package_type_examples), num_products)):
            example_assignments[str(i)] = list(package_type_examples.values())[i]
        
        # Format as JSON string
        example_json = json.dumps(example_assignments, indent=2)
        return example_json
        
    def _validate_response(self, response: str, context: LabelingContext) -> ValidationResult:
        """Package type specific validation with Multiple-{number} support"""
        
        error_categories: Dict[str, List[str]] = {
            "format_errors": [],
            "validation_errors": [],
            "completeness_errors": [],
        }
        
        try:
            # Extract and parse JSON
            from core.utils.llm_utils import extract_json
            json_text = extract_json(response)
            result = json.loads(json_text)
        except Exception as e:
            error_categories["format_errors"].append(f"JSON parsing error: {str(e)}")
            return ValidationResult(ok=False, error_categories=error_categories)
            
        # Check if result is a dictionary
        if not isinstance(result, dict):
            error_categories["format_errors"].append("Response must be a JSON object")
            return ValidationResult(ok=False, error_categories=error_categories)
            
        # Check if all indices are covered
        expected_indices = set(str(i) for i in range(len(context.products)))
        actual_indices = set(result.keys())
        
        if expected_indices != actual_indices:
            missing_indices = expected_indices - actual_indices
            extra_indices = actual_indices - expected_indices
            
            if missing_indices:
                error_categories["completeness_errors"].append(
                    f"Missing indices: {', '.join(sorted(missing_indices))}"
                )
            if extra_indices:
                error_categories["completeness_errors"].append(
                    f"Extra indices: {', '.join(sorted(extra_indices))}"
                )
                
        # Package type specific label validation
        valid_labels = set(context.available_labels.keys())
        for idx, label in result.items():
            if not self._is_valid_label(label, valid_labels):
                # Provide package type specific error message
                base_labels = ', '.join(sorted(valid_labels))
                error_categories["validation_errors"].append(
                    f"Invalid label '{label}' for index {idx}. Valid labels: {base_labels}. For multiple quantities, use format Multiple-{{number}} (e.g., Multiple-2, Multiple-6)"
                )
                
        # Check for overall completeness
        all_errors = sum(len(v) for v in error_categories.values())
        if all_errors == 0:
            return ValidationResult(ok=True, error_categories=error_categories)
            
        return ValidationResult(ok=False, error_categories=error_categories) 