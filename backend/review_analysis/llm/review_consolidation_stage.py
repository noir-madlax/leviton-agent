"""Review-specific consolidation stage implementation.

This module provides consolidation for review aspects (physical, performance, use case)
by inheriting from the generic core consolidation implementation and adding only 
review-specific template variables and deduplication logic.
"""

from pathlib import Path
from typing import Dict, List
import json

from core.llm_taxonomy_pipeline.consolidation_base import (
    ConsolidationStage as BaseConsolidationStage,
    ConsolidationStageContext as ReviewConsolidationStageContext,
    ConsolidationStageResult,
    ConsolidatedTaxonomyDTO,
)
from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO

__all__ = [
    "ConsolidatedTaxonomyDTO",
    "ConsolidationStageResult", 
    "ReviewConsolidationStageContext",
    "ReviewConsolidationStage",
]

# Prompt template paths
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_CONSOLIDATE_PROMPT_FILE = "review_aspects_consolidation_prompt_v0.txt"


class ReviewConsolidationStage(BaseConsolidationStage):
    """Review aspect consolidation stage with deduplication support."""

    def __init__(self, aspect_type: str = "", product_categories: set = None):
        """Initialize with review-specific context."""
        consolidate_template, retry_template = self.load_templates(
            _PROMPTS_DIR, _CONSOLIDATE_PROMPT_FILE
        )
        super().__init__(consolidate_template, retry_template)
        
        self.aspect_type = aspect_type
        self.product_categories = product_categories or set()

        # Provide default aspect definitions that match extraction prompt semantics
        self._aspect_type_definitions: Dict[str, str] = {
            "physical": (
                "Components or inherent physical properties of the product, such as "
                "dimensions, appearance, or material composition."
            ),
            "performance": (
                "Performance characteristics or behaviours of the product under various "
                "conditions, e.g. durability, reliability, speed, flexibility."
            ),
            "use": (
                "Specific applications, objects, methods, tools, or environments that "
                "illustrate how customers use the product."
            ),
        }

    def _get_additional_template_vars(self, ctx: ReviewConsolidationStageContext) -> Dict[str, str]:
        """Add review-specific template variables."""
        # Resolve aspect definition, fall back to empty string if not available
        aspect_definition = self._aspect_type_definitions.get(self.aspect_type.lower(), "")

        product_context = ""
        if self.product_categories:
            categories_list = ', '.join(sorted(self.product_categories))
            product_context = (
                f"\n\n**PRODUCT CATEGORIES IN DATASET:** {categories_list}\n"
                f"Consider how {self.aspect_type} aspects relate to customer needs "
                f"across these {len(self.product_categories)} product categories."
            )
        
        return {
            "aspect_type": self.aspect_type,
            "aspect_definition": aspect_definition,
            "product_context": product_context,
        }

    def _validate(self, raw_response: str, ctx: ReviewConsolidationStageContext):
        """Override to handle the special __KEEP__ field in validation."""
        expected_ids = set()
        for i in range(len(ctx.taxonomy_a)):
            expected_ids.add(f"A_{i}")
        for i in range(len(ctx.taxonomy_b)):
            expected_ids.add(f"B_{i}")

        error_categories: Dict[str, list] = {
            "format_errors": [],
            "validation_errors": [],
            "completeness_errors": [],
        }

        try:
            from core.utils.llm_utils import extract_json, ValidationResult
            json_text = extract_json(raw_response)
            parsed = json.loads(json_text)
        except Exception as exc:
            error_categories["format_errors"].append(str(exc))
            return ValidationResult(ok=False, error_categories=error_categories)

        if not isinstance(parsed, dict):
            error_categories["format_errors"].append("Top-level JSON must be an object")
            return ValidationResult(ok=False, error_categories=error_categories)

        if not parsed:
            error_categories["format_errors"].append("JSON object cannot be empty")
            return ValidationResult(ok=False, error_categories=error_categories)

        all_assigned_ids = set()
        
        # Handle the special __KEEP__ field
        if "__KEEP__" in parsed:
            keep_field = parsed["__KEEP__"]
            if not isinstance(keep_field, list):
                error_categories["validation_errors"].append("__KEEP__ field must be a list")
            else:
                for idx, id_val in enumerate(keep_field):
                    if not isinstance(id_val, str):
                        error_categories["validation_errors"].append(
                            f"__KEEP__[{idx}] must be a string"
                        )
                    else:
                        if id_val not in expected_ids:
                            error_categories["completeness_errors"].append(
                                f"__KEEP__ contains invalid id {id_val}"
                            )
                        elif id_val in all_assigned_ids:
                            error_categories["completeness_errors"].append(
                                f"ID {id_val} appears multiple times (in __KEEP__ and elsewhere)"
                            )
                        else:
                            all_assigned_ids.add(id_val)

        # Process regular categories (excluding __KEEP__)
        for category_name, category_data in parsed.items():
            if category_name == "__KEEP__":
                continue  # Skip the special field
                
            if not isinstance(category_data, dict):
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' must be an object"
                )
                continue
                
            if "definition" not in category_data:
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' missing 'definition' field"
                )
            elif not isinstance(category_data["definition"], str):
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' definition must be a string"
                )
                
            if "ids" not in category_data:
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' missing 'ids' field"
                )
            elif not isinstance(category_data["ids"], list):
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' ids must be a list"
                )
            else:
                category_ids = category_data["ids"]
                for idx, id_val in enumerate(category_ids):
                    if not isinstance(id_val, str):
                        error_categories["validation_errors"].append(
                            f"Category '{category_name}' ids[{idx}] must be a string"
                        )
                    else:
                        if id_val not in expected_ids:
                            error_categories["completeness_errors"].append(
                                f"Category '{category_name}' contains invalid id {id_val}"
                            )
                        elif id_val in all_assigned_ids:
                            error_categories["completeness_errors"].append(
                                f"ID {id_val} appears in multiple categories"
                            )
                        else:
                            all_assigned_ids.add(id_val)

        missing_ids = expected_ids - all_assigned_ids
        if missing_ids:
            error_categories["completeness_errors"].append(
                f"Missing assignments for ids: {sorted(missing_ids)}"
            )

        all_errors = sum(len(v) for v in error_categories.values())
        return ValidationResult(ok=all_errors == 0, error_categories=error_categories)

    async def _produce_result(self, raw_response: str, ctx: ReviewConsolidationStageContext, attempts: int):
        """Override to handle the special __KEEP__ field in result production."""
        from core.utils.llm_utils import extract_json
        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        taxonomies = []
        
        # Handle the special __KEEP__ field - preserve original taxonomies unchanged
        if "__KEEP__" in payload:
            keep_ids = payload["__KEEP__"]
            for original_id in keep_ids:
                if original_id.startswith("A_"):
                    idx = int(original_id[2:])
                    if idx < len(ctx.taxonomy_a):
                        original_taxonomy = ctx.taxonomy_a[idx]
                        taxonomies.append(ConsolidatedTaxonomyDTO(
                            taxonomy=original_taxonomy,  # Keep original unchanged
                            original_taxonomies=[original_taxonomy]
                        ))
                elif original_id.startswith("B_"):
                    idx = int(original_id[2:])
                    if idx < len(ctx.taxonomy_b):
                        original_taxonomy = ctx.taxonomy_b[idx]
                        taxonomies.append(ConsolidatedTaxonomyDTO(
                            taxonomy=original_taxonomy,  # Keep original unchanged
                            original_taxonomies=[original_taxonomy]
                        ))
        
        # Handle regular consolidated categories (excluding __KEEP__)
        for category_name, category_data in payload.items():
            if category_name == "__KEEP__":
                continue  # Skip the special field
                
            if isinstance(category_data, dict) and "definition" in category_data and "ids" in category_data:
                consolidated_taxonomy = TaxonomyDTO(
                    name=category_name,
                    definition=category_data["definition"]
                )
                
                original_taxonomies = []
                for original_id in category_data["ids"]:
                    if original_id.startswith("A_"):
                        idx = int(original_id[2:])
                        if idx < len(ctx.taxonomy_a):
                            original_taxonomies.append(ctx.taxonomy_a[idx])
                    elif original_id.startswith("B_"):
                        idx = int(original_id[2:])
                        if idx < len(ctx.taxonomy_b):
                            original_taxonomies.append(ctx.taxonomy_b[idx])
                
                taxonomies.append(ConsolidatedTaxonomyDTO(
                    taxonomy=consolidated_taxonomy,
                    original_taxonomies=original_taxonomies
                ))
        
        return ConsolidationStageResult(taxonomies_consolidated=taxonomies)