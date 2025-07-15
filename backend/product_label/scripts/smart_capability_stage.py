"""
Smart capability labeling stage implementation

This module defines a SmartCapabilityStage that processes product batches
and assigns smart capability labels based on product titles.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from core.utils.llm_utils import safe_llm_call, extract_json, create_retry_error_details, ValidationResult
from .models import SmartCapabilityContext, SmartCapabilityResult

logger = logging.getLogger(__name__)

# Path to prompt template files
_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SMART_CAPABILITY_PROMPT_PATH = _PROMPTS_DIR / "smart_capability_prompt_v0.txt"
_RETRY_PROMPT_PATH = (
    Path(__file__).resolve().parents[3] / "core" / "prompts" / "shared_retry_prompt_v0.txt"
)

# Load prompt templates at module level
try:
    with open(_SMART_CAPABILITY_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _SMART_CAPABILITY_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required prompt template not found: {_SMART_CAPABILITY_PROMPT_PATH}")

try:
    with open(_RETRY_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _RETRY_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    # Fallback to a simple retry template if the shared one is not found
    _RETRY_PROMPT_TEMPLATE = """
The previous response failed validation with the following issues:
{{error_details}}

Please correct these issues and provide a valid response.
"""

class SmartCapabilityStage:
    """Stage for processing smart capability labeling"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        
    async def execute(self, context: SmartCapabilityContext) -> SmartCapabilityResult:
        """Execute smart capability labeling for a batch of products"""
        
        logger.info(f"Processing batch {context.batch_id} with {len(context.products)} products")
        
        # Build the prompt
        prompt = self._build_prompt(context)
        
        # Execute with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"LLM attempt {attempt} for batch {context.batch_id}")
                
                # Make LLM call with validation
                response = await safe_llm_call(
                    prompt=prompt,
                    validate_response=lambda resp: self._validate_response(resp, context),
                    retry_prompt_builder=lambda orig_prompt, validation_ctx: self._build_retry_prompt(orig_prompt, validation_ctx),
                    context={'batch_id': context.batch_id, 'attempt': attempt}
                )
                
                # Parse successful response
                result = self._parse_response(response, context, attempt)
                logger.info(f"Successfully processed batch {context.batch_id}")
                return result
                
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for batch {context.batch_id}: {e}")
                if attempt == self.max_retries:
                    logger.error(f"All attempts failed for batch {context.batch_id}")
                    return SmartCapabilityResult(
                        assignments={},
                        batch_id=context.batch_id,
                        success=False,
                        error_message=str(e),
                        attempts=attempt
                    )
                    
        # This should never be reached, but just in case
        return SmartCapabilityResult(
            assignments={},
            batch_id=context.batch_id,
            success=False,
            error_message="Unknown error occurred",
            attempts=self.max_retries
        )
        
    def _build_prompt(self, context: SmartCapabilityContext) -> str:
        """Build the prompt for batch processing"""
        
        # Format available labels
        labels_section = "\n".join([
            f"- {label}: {definition}" 
            for label, definition in context.available_labels.items()
        ])
        
        # Build output format example using actual label values
        output_format_example = self._build_output_format_example(context.available_labels, len(context.products))
        
        # Format product list
        products_section = "\n".join([
            f"[{i}] {product.title}"
            for i, product in enumerate(context.products)
        ])
        
        # Replace template variables
        prompt = _SMART_CAPABILITY_PROMPT_TEMPLATE.replace(
            "{{available_labels}}", labels_section
        ).replace(
            "{{output_format_example}}", output_format_example
        ).replace(
            "{{total_products}}", str(len(context.products) - 1)
        ).replace(
            "{{product_list}}", products_section
        )
        
        return prompt
        
    def _build_output_format_example(self, available_labels: Dict[str, str], num_products: int) -> str:
        """Build output format example using actual label values"""
        
        # Get actual label values (keys from available_labels)
        label_values = list(available_labels.keys())
        
        # Create example assignments using actual label values
        example_assignments = {}
        for i in range(min(4, num_products)):  # Show up to 4 examples
            # Cycle through available labels to show variety
            example_assignments[str(i)] = label_values[i % len(label_values)]
        
        # Format as JSON string
        example_json = json.dumps(example_assignments, indent=2)
        return example_json
        
    def _validate_response(self, response: str, context: SmartCapabilityContext) -> ValidationResult:
        """Validate the LLM response"""
        
        error_categories: Dict[str, List[str]] = {
            "format_errors": [],
            "validation_errors": [],
            "completeness_errors": [],
        }
        
        try:
            # Extract and parse JSON
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
                
        # Check if all values are valid labels
        valid_labels = set(context.available_labels.keys())
        for idx, label in result.items():
            if label not in valid_labels:
                error_categories["validation_errors"].append(
                    f"Invalid label '{label}' for index {idx}. Valid labels: {', '.join(sorted(valid_labels))}"
                )
                
        # Check for overall completeness
        all_errors = sum(len(v) for v in error_categories.values())
        if all_errors == 0:
            return ValidationResult(ok=True, error_categories=error_categories)
            
        return ValidationResult(ok=False, error_categories=error_categories)
        
    def _build_retry_prompt(self, original_prompt: str, validation_result: ValidationResult) -> str:
        """Build retry prompt with error details"""
        
        error_details = create_retry_error_details(validation_result.error_categories)
        retry_block = _RETRY_PROMPT_TEMPLATE.replace("{{error_details}}", error_details)
        
        return f"{original_prompt}\n\n{retry_block}"
        
    def _parse_response(self, response: str, context: SmartCapabilityContext, attempts: int) -> SmartCapabilityResult:
        """Parse a validated response into a result object"""
        
        json_text = extract_json(response)
        assignments = json.loads(json_text)
        
        return SmartCapabilityResult(
            assignments=assignments,
            batch_id=context.batch_id,
            success=True,
            error_message=None,
            attempts=attempts
        ) 