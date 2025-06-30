"""Abstract consolidation stage base for taxonomy pipelines."""

from __future__ import annotations
import abc
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from ..utils.llm_utils import extract_json, create_retry_error_details, ValidationResult
from .pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
    TaxonomyDTO,
)

__all__: list[str] = [
    "ConsolidatedTaxonomyDTO",
    "ConsolidationStageContext",
    "ConsolidationStageResult",
    "ConsolidationStage",
]


@dataclass(slots=True, frozen=True)
class ConsolidatedTaxonomyDTO:  # noqa: D401
    taxonomy: TaxonomyDTO
    original_taxonomies: list[TaxonomyDTO]


@dataclass(slots=True, frozen=True)
class ConsolidationStageContext(StageContext):
    taxonomy_a: list[TaxonomyDTO]
    taxonomy_b: list[TaxonomyDTO]


@dataclass(slots=True, frozen=True)
class ConsolidationStageResult(StageResultBase):
    taxonomies_consolidated: List[ConsolidatedTaxonomyDTO]


class ConsolidationStage(BaseStage, abc.ABC):
    """Abstract base class for consolidation stages."""

    def __init__(self, consolidate_prompt_template: str, retry_prompt_template: str):
        """Initialize with prompt templates."""
        self._consolidate_prompt_template = consolidate_prompt_template
        self._retry_prompt_template = retry_prompt_template

    @classmethod
    def load_templates(cls, prompts_dir: Path, consolidate_filename: str, 
                      retry_filename: str = "shared_retry_prompt_v0.txt") -> tuple[str, str]:
        """Load consolidation and retry prompt templates."""
        consolidate_path = prompts_dir / consolidate_filename
        retry_path = prompts_dir.parents[1] / "core" / "prompts" / retry_filename
        
        try:
            with open(consolidate_path, 'r', encoding='utf-8') as f:
                consolidate_template = f.read()
        except FileNotFoundError:
            raise RuntimeError(f"Required prompt template not found: {consolidate_path}")
        
        try:
            with open(retry_path, 'r', encoding='utf-8') as f:
                retry_template = f.read()
        except FileNotFoundError:
            raise RuntimeError(f"Required retry template not found: {retry_path}")
        
        return consolidate_template, retry_template

    async def _build_prompt(self, ctx: ConsolidationStageContext) -> str:
        """Build consolidation prompt with A_*/B_* taxonomy formatting."""
        taxonomy_a_formatted = {}
        for i, entry in enumerate(ctx.taxonomy_a):
            a_id = f"A_{i}"
            taxonomy_a_formatted[a_id] = {
                "name": entry.name,
                "definition": entry.definition
            }
        
        taxonomy_b_formatted = {}
        for i, entry in enumerate(ctx.taxonomy_b):
            b_id = f"B_{i}"
            taxonomy_b_formatted[b_id] = {
                "name": entry.name,
                "definition": entry.definition
            }
        
        # Build mapping of placeholder → replacement strings.
        template_vars = {
            "taxonomy_a": json.dumps(taxonomy_a_formatted, indent=2),
            "taxonomy_b": json.dumps(taxonomy_b_formatted, indent=2),
        }
        template_vars.update(self._get_additional_template_vars(ctx))

        prompt = self._consolidate_prompt_template

        # Expect placeholders in the template to be wrapped in double braces, e.g. {{taxonomy_a}}
        for key, value in template_vars.items():
            placeholder = f"{{{{{key}}}}}"
            prompt = prompt.replace(placeholder, value)

        return prompt

    def _validate(self, raw_response: str, ctx: ConsolidationStageContext) -> ValidationResult:
        """Validate consolidation response with A_*/B_* ID checking."""
        expected_ids = set()
        for i in range(len(ctx.taxonomy_a)):
            expected_ids.add(f"A_{i}")
        for i in range(len(ctx.taxonomy_b)):
            expected_ids.add(f"B_{i}")

        error_categories: Dict[str, List[str]] = {
            "format_errors": [],
            "validation_errors": [],
            "completeness_errors": [],
        }

        try:
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
        for category_name, category_data in parsed.items():
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

    def _retry_prompt(self, original_prompt: str, validation_result: ValidationResult, 
                     ctx: ConsolidationStageContext) -> str:
        """Build retry prompt with error details."""
        error_details = create_retry_error_details(validation_result.error_categories)
        retry_block = self._retry_prompt_template.replace("{{error_details}}", error_details)
        return f"{original_prompt}\n\n{retry_block}"

    async def _produce_result(self, raw_response: str, ctx: ConsolidationStageContext, 
                            attempts: int) -> ConsolidationStageResult:
        """Convert valid response to ConsolidationStageResult."""
        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        taxonomies = []
        for category_name, category_data in payload.items():
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

    async def _merge_split_results(self, res_left: ConsolidationStageResult,
                                 res_right: ConsolidationStageResult,
                                 ctx_left: ConsolidationStageContext,
                                 ctx_right: ConsolidationStageContext,
                                 depth: int) -> ConsolidationStageResult:
        """Merge split results by deduplicating by name."""
        taxonomy_by_name: Dict[str, ConsolidatedTaxonomyDTO] = {}
        for t in res_left.taxonomies_consolidated + res_right.taxonomies_consolidated:
            if t.taxonomy.name in taxonomy_by_name:
                existing = taxonomy_by_name[t.taxonomy.name]
                merged_originals = existing.original_taxonomies + t.original_taxonomies
                seen_names = set()
                unique_originals = []
                for orig in merged_originals:
                    if orig.name not in seen_names:
                        unique_originals.append(orig)
                        seen_names.add(orig.name)
                
                taxonomy_by_name[t.taxonomy.name] = ConsolidatedTaxonomyDTO(
                    taxonomy=t.taxonomy,
                    original_taxonomies=unique_originals
                )
            else:
                taxonomy_by_name[t.taxonomy.name] = t

        return ConsolidationStageResult(
            taxonomies_consolidated=list(taxonomy_by_name.values())
        )

    def _split_context(self, ctx: ConsolidationStageContext, depth: int
                      ) -> tuple[ConsolidationStageContext, ConsolidationStageContext]:
        """ConsolidationStage typically cannot be split further."""
        raise NotImplementedError("ConsolidationStage contexts cannot be split")
    
    def _get_additional_template_vars(self, ctx: ConsolidationStageContext) -> Dict[str, str]:
        """Override to add domain-specific template variables."""
        return {} 