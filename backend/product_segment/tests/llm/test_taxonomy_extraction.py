"""Tests for taxonomy extraction stage implementation.

This module tests the ExtractionStage class with real product data from
the Amazon light switches CSV file, using 4 * PRODUCTS_PER_TAXONOMY_PROMPT
titles for comprehensive testing.

Test Coverage:
--------------

1. **test_extract_taxonomies_from_light_switches**: 
   Main integration test that processes 160 light switch product titles through
   the extraction stage and validates the complete taxonomy extraction workflow.
   Verifies result structure, taxonomy quality, assignment completeness, and
   data integrity.

2. **test_validation_with_valid_response**:
   Tests the validation logic with a properly formatted JSON response that
   matches the expected schema (taxonomies array + assignments object).
   Verifies that valid responses pass validation without errors.

3. **test_validation_with_invalid_response**:
   Tests validation error handling with various malformed responses:
   - Invalid JSON syntax
   - Missing required top-level keys (taxonomies/assignments)  
   - Incomplete assignment mappings
   Ensures proper error categorization and reporting.

4. **test_retry_prompt_generation**:
   Tests retry prompt construction using the shared_retry_prompt_v0.txt template.
   Verifies that validation errors are properly formatted and included in
   retry instructions to help the LLM correct its response.

5. **test_produce_result_conversion**:
   Tests the conversion of valid raw JSON responses into ExtractionStageResult
   objects. Verifies proper parsing of taxonomies and assignments, including
   string-to-integer key conversion for assignments.

6. **test_merge_split_results**:
   Tests the merging logic for split processing scenarios where large product
   batches are automatically divided. Verifies taxonomy deduplication by name
   and proper assignment consolidation across splits.


Configuration:
--------------
- Uses 160 product titles (4 * PRODUCTS_PER_TAXONOMY_PROMPT = 4 * 40)
- Product category: "light switch" 
- Source data: amazon_light_switches.csv with real Amazon product data
- Fixed prompt templates: taxonomy_extraction_prompt_v0.txt, shared_retry_prompt_v0.txt
- No external configuration required - templates loaded automatically
"""

import asyncio
import csv
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock

from core.utils.llm_utils import ValidationResult
from product_segment.config import PRODUCTS_PER_TAXONOMY_PROMPT
from product_segment.llm.taxonomy_extraction import (
    ExtractionStage,
    ExtractionStageResult,
    ExtractionStageContext,
    TaxonomyDTO,
)
from product_segment.llm.taxonomy_pipeline_stage import StageContext


# Constants for test configuration
TEST_PRODUCT_COUNT = 4 * PRODUCTS_PER_TAXONOMY_PROMPT  # 160 products
PRODUCT_CATEGORY = "light switch"
TEST_CSV_PATH = Path(__file__).parent / "test_data" / "amazon_light_switches.csv"
TAXONOMY_RESULTS_PATH = Path(__file__).parent / "test_data" / "taxonomy_extraction_results.json"


def save_taxonomy_results(
    all_results: List[ExtractionStageResult],
    light_switch_titles: List[str],
    product_category: str
) -> None:
    """Save taxonomy extraction results to JSON file for next stage testing.
    
    Args:
        all_results: List of ExtractionStageResult from all batches
        light_switch_titles: Original product titles used in extraction
        product_category: Product category that was processed
    """
    # Aggregate all taxonomies (deduplicate by name)
    all_taxonomies = {}
    for result in all_results:
        for taxonomy in result.taxonomies_extracted:
            all_taxonomies[taxonomy.name] = {
                "name": taxonomy.name,
                "definition": taxonomy.definition
            }
    
    # Aggregate all assignments (adjust indices for batch offsets)
    all_assignments = {}
    batch_size = PRODUCTS_PER_TAXONOMY_PROMPT
    
    for batch_idx, result in enumerate(all_results):
        batch_offset = batch_idx * batch_size
        for product_idx, taxonomy_name in result.assignments_initial.items():
            global_idx = batch_offset + product_idx
            all_assignments[str(global_idx)] = taxonomy_name
    
    # Create the complete result structure
    saved_data = {
        "metadata": {
            "product_category": product_category,
            "total_products": len(light_switch_titles),
            "total_batches": len(all_results),
            "total_taxonomies": len(all_taxonomies),
            "batch_size": batch_size,
            "extraction_timestamp": datetime.now().isoformat()
        },
        "product_titles": light_switch_titles,
        "taxonomies": list(all_taxonomies.values()),
        "assignments": all_assignments,
        "batch_results": [
            {
                "batch_idx": idx,
                "taxonomies_count": len(result.taxonomies_extracted),
                "assignments_count": len(result.assignments_initial),
                "taxonomies": [
                    {"name": t.name, "definition": t.definition}
                    for t in result.taxonomies_extracted
                ],
                "assignments": dict(result.assignments_initial)
            }
            for idx, result in enumerate(all_results)
        ]
    }
    
    # Save to JSON file
    with open(TAXONOMY_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(saved_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved taxonomy results to: {TAXONOMY_RESULTS_PATH}")
    print(f"   - {len(all_taxonomies)} unique taxonomies")
    print(f"   - {len(all_assignments)} product assignments")
    print(f"   - {len(all_results)} batch results")


@pytest.fixture
def light_switch_titles() -> List[str]:
    """Load light switch product titles from CSV file."""
    titles = []
    with open(TEST_CSV_PATH, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            if i >= TEST_PRODUCT_COUNT:
                break
            titles.append(row['title'])
    
    if len(titles) < TEST_PRODUCT_COUNT:
        pytest.skip(f"CSV file has only {len(titles)} products, need {TEST_PRODUCT_COUNT}")
    
    return titles


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Mock LLM client that returns valid taxonomy extraction responses."""
    
    def create_response(seq_len: int) -> str:
        # Create response in the format expected by taxonomy_extraction_prompt_v0.txt
        categories = {
            "Smart Dimmer Switches": {
                "definition": "Wi-Fi enabled dimmer switches with smart home integration, e.g. Amazon Alexa compatible switches",
                "ids": []
            },
            "Traditional Toggle Switches": {
                "definition": "Standard toggle switches for basic on/off control, e.g. wall mounted toggle switches",
                "ids": []
            },
            "Rocker Paddle Switches": {
                "definition": "Modern rocker-style switches with paddle design, e.g. decorator paddle switches",
                "ids": []
            },
            "3-Way Light Switches": {
                "definition": "Switches designed for multi-location lighting control, e.g. three way wiring compatible switches",
                "ids": []
            }
        }
        
        # Distribute product IDs across categories
        category_names = list(categories.keys())
        for i in range(seq_len):
            category_idx = i % len(category_names)
            category_name = category_names[category_idx]
            categories[category_name]["ids"].append(i)
        
        return json.dumps(categories)
    
    mock = AsyncMock()
    mock.side_effect = lambda prompt, **kwargs: create_response(
        len([line for line in prompt.split('\n') if line.strip().startswith('[') and ']' in line])
    )
    return mock


@pytest.fixture
def stage_context() -> StageContext:
    """Create base stage context for testing."""
    return StageContext(
        product_category=PRODUCT_CATEGORY
    )


@pytest.fixture
def saved_taxonomy_results() -> dict:
    """Load saved taxonomy results from the integration test.
    
    Returns:
        Dictionary containing the saved taxonomy extraction results
    """
    if not TAXONOMY_RESULTS_PATH.exists():
        pytest.skip(f"Taxonomy results file not found: {TAXONOMY_RESULTS_PATH}")
    
    with open(TAXONOMY_RESULTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def extraction_stage(mock_llm_client: AsyncMock) -> ExtractionStage:
    """Create ExtractionStage instance with mocked LLM client."""
    stage = ExtractionStage()
    stage._llm_client = mock_llm_client
    return stage


class TestExtractionStage:
    """Test cases for ExtractionStage."""

    @pytest.mark.asyncio
    @pytest.mark.integration  # Mark as integration test requiring real LLM
    async def test_extract_taxonomies_from_light_switches(
        self,
        light_switch_titles: List[str],
        stage_context: StageContext
    ) -> None:
        """Integration test – real LLM, 160 titles processed in parallel batches.

        • Input: 4 batches × 40 "light-switch" titles from the Amazon CSV (total 160).
        • Behaviour under test: end-to-end `ExtractionStage.execute` for all batches
          concurrently, including prompt construction, validation / retry loop, and 
          JSON → DTO parsing.
        • Expectation: each batch returns a valid `ExtractionStageResult` with
          non-empty taxonomies and a complete `assignments_initial` covering
          all 40 indices; results are aggregated to 160 assignments overall.
        • Results are saved to test_data/taxonomy_extraction_results.json for next stage.
        Requires `ANTHROPIC_API_KEY` & network access – run with -m integration.
        """
        from product_segment.config import PRODUCTS_PER_TAXONOMY_PROMPT

        # Create extraction stage (uses real LLM via safe_llm_call automatically)
        real_extraction_stage = ExtractionStage()

        batch_size = PRODUCTS_PER_TAXONOMY_PROMPT
        batches: list[list[str]] = [
            light_switch_titles[i : i + batch_size]
            for i in range(0, len(light_switch_titles), batch_size)
        ]

        print(f"\n🚀 Processing {len(batches)} batches in parallel...")
        print(f"📊 Total products: {len(light_switch_titles)}")
        
        # Create all batch contexts
        batch_contexts = []
        for batch_idx, batch_titles in enumerate(batches, start=1):
            print(f"\n🟡  Batch {batch_idx}/{len(batches)} – {len(batch_titles)} titles")
            for i, title in enumerate(batch_titles):
                print(f"  [{i}] {title}")
                
            context = ExtractionStageContext(
                product_category=stage_context.product_category,
                input_texts=batch_titles,
            )
            batch_contexts.append((batch_idx, batch_titles, context))

        print("\n➡️   Calling real LLM for all batches in parallel...")
        
        # Execute all batches in parallel
        async def process_batch(batch_idx: int, batch_titles: List[str], context: ExtractionStageContext) -> ExtractionStageResult:
            result = await real_extraction_stage.execute(context)
            print(f"✅  Batch {batch_idx} finished – extracted "
                  f"{len(result.taxonomies_extracted)} taxonomies and "
                  f"{len(result.assignments_initial)} assignments")
            
            # Print taxonomy overview for this batch
            for tax_idx, taxonomy in enumerate(result.taxonomies_extracted, start=1):
                print(f"    Batch {batch_idx} - {tax_idx:02d}. {taxonomy.name}  →  {taxonomy.definition[:80]}…")
            
            return result
        
        # Run all batches concurrently
        tasks = [
            process_batch(batch_idx, batch_titles, context)
            for batch_idx, batch_titles, context in batch_contexts
        ]
        
        all_results = await asyncio.gather(*tasks)

        # Validate results
        for batch_idx, result in enumerate(all_results, start=1):
            expected_batch_size = len(batches[batch_idx - 1])
            assert len(result.assignments_initial) == expected_batch_size
            assigned_ids = set(result.assignments_initial.keys())
            assert assigned_ids == set(range(expected_batch_size))

        # Aggregate assertions across all batches
        total_taxonomies = sum(len(r.taxonomies_extracted) for r in all_results)
        print("\n" + "=" * 80)
        print(f"🎉 Completed all batches – total taxonomies extracted: {total_taxonomies}")

        save_taxonomy_results(all_results, light_switch_titles, PRODUCT_CATEGORY)

    @pytest.mark.asyncio
    async def test_build_prompt_with_context(
        self,
        extraction_stage: ExtractionStage,
        light_switch_titles: List[str],
        stage_context: StageContext
    ) -> None:
        """Verify prompt template renders correctly for 10 sample titles."""
        # Take first 10 titles for faster testing
        sample_titles = light_switch_titles[:10]
        
        print(f"\n🔍 Testing extraction prompt building with {len(sample_titles)} sample titles...")
        print(f"\n📋 Input Texts:")
        for i, title in enumerate(sample_titles):
            print(f"  [{i}] {title}")
        
        # Create extraction context
        extraction_context = ExtractionStageContext(
            product_category=stage_context.product_category,
            input_texts=sample_titles
        )
        
        prompt = await extraction_stage._build_prompt(extraction_context)
        
        print(f"\n📝 Generated Extraction Prompt:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Prompt lines: {len(prompt.split(chr(10)))} lines")
        
        # Verify context variables were replaced  
        assert PRODUCT_CATEGORY in prompt
        
        # Verify key elements from taxonomy_extraction_prompt_v0.txt are present
        assert "product taxonomy extraction specialist" in prompt.lower()
        assert "INPUT FORMAT" in prompt
        assert "REQUIRED OUTPUT FORMAT" in prompt
        assert "CRITICAL RULES" in prompt
        assert "OUT_OF_SCOPE" in prompt
        
        # Verify product enumeration matches expected format [<ID>] <title>
        for i, title in enumerate(sample_titles):
            expected_line = f"[{i}] {title}"
            assert expected_line in prompt
        
        print(f"\n✅ Extraction prompt validation completed successfully!")
        print(f"   - Contains all required template sections")
        print(f"   - Includes all {len(sample_titles)} input texts with proper indexing")
        print(f"   - Product category '{PRODUCT_CATEGORY}' properly substituted")

    @pytest.mark.asyncio
    async def test_validation_with_valid_response(
        self,
        extraction_stage: ExtractionStage,
        stage_context: StageContext
    ) -> None:
        """Valid JSON response should pass validation without errors."""
        sample_titles = ["Smart Switch", "Toggle Switch"]
        
        # Create extraction context
        extraction_context = ExtractionStageContext(
            product_category=stage_context.product_category,
            input_texts=sample_titles
        )
        
        valid_response = json.dumps({
            "Smart Switches": {
                "definition": "Wi-Fi enabled switches, e.g. smart home compatible switches",
                "ids": [0, 1]  # Both products assigned
            }
        })
        
        validation_result = extraction_stage._validate(
            valid_response, extraction_context
        )
        
        assert validation_result.ok is True
        assert sum(len(errors) for errors in validation_result.error_categories.values()) == 0

    @pytest.mark.asyncio
    async def test_validation_with_invalid_response(
        self,
        extraction_stage: ExtractionStage,
        stage_context: StageContext
    ) -> None:
        """Validation should categorise format / schema / completeness errors.

        Three deliberately bad payloads are supplied to `_validate()` –
        (1) non-JSON text, (2) JSON missing the `definition` field, and
        (3) JSON missing an assignment.  Each must set `ok=False` and populate
        the appropriate error category.
        """
        sample_titles = ["Switch 1", "Switch 2"]
        
        # Create extraction context
        extraction_context = ExtractionStageContext(
            product_category=stage_context.product_category,
            input_texts=sample_titles
        )
        
        # Test invalid JSON
        invalid_json = "This is not JSON"
        result = extraction_stage._validate(invalid_json, extraction_context)
        assert result.ok is False
        assert len(result.error_categories["format_errors"]) > 0
        
        # Test missing definition
        missing_definition = json.dumps({
            "Test Category": {
                "ids": [0, 1]  # Missing definition
            }
        })
        result = extraction_stage._validate(missing_definition, extraction_context) 
        assert result.ok is False
        assert len(result.error_categories["validation_errors"]) > 0
        
        # Test missing assignment
        incomplete_assignments = json.dumps({
            "Test Category": {
                "definition": "Test category, e.g. test products",
                "ids": [0]  # Missing assignment for index 1
            }
        })
        result = extraction_stage._validate(incomplete_assignments, extraction_context)
        assert result.ok is False
        assert len(result.error_categories["completeness_errors"]) > 0

    @pytest.mark.asyncio
    async def test_retry_prompt_generation(
        self,
        extraction_stage: ExtractionStage,
        stage_context: StageContext
    ) -> None:
        """Retry prompt generation – ensure error details are injected.

        Given a `ValidationResult` with one error in each category the helper
        must embed those messages between the "RETRY REQUIRED" … "END" markers
        while preserving the original prompt text.
        """
        original_prompt = "Original prompt content"
        
        validation_result = ValidationResult(
            ok=False,
            error_categories={
                "format_errors": ["Invalid JSON structure"],
                "validation_errors": ["Missing taxonomy name"],
                "completeness_errors": ["Missing assignment for index 1"]
            }
        )
        
        # Create extraction context
        extraction_context = ExtractionStageContext(
            product_category=stage_context.product_category,
            input_texts=["Switch 1"]
        )
        
        retry_prompt = extraction_stage._retry_prompt(
            original_prompt, validation_result, extraction_context
        )
        
        # Verify original prompt is included
        assert original_prompt in retry_prompt
        
        # Verify retry template elements are present (from shared_retry_prompt_v0.txt)
        assert "RETRY REQUIRED" in retry_prompt
        assert "END RETRY INSTRUCTIONS" in retry_prompt
        
        # Verify error details are included in the retry prompt
        assert "Invalid JSON structure" in retry_prompt
        assert "Missing taxonomy name" in retry_prompt
        assert "Missing assignment for index 1" in retry_prompt

    @pytest.mark.asyncio
    async def test_produce_result_conversion(
        self,
        extraction_stage: ExtractionStage,
        stage_context: StageContext
    ) -> None:
        """_produce_result converts valid JSON → DTOs & id→category mapping."""
        raw_response = json.dumps({
            "Smart Switches": {
                "definition": "Wi-Fi enabled smart switches, e.g. smart home compatible switches",
                "ids": [0, 2]
            },
            "Manual Switches": {
                "definition": "Traditional manual switches, e.g. toggle and rocker switches", 
                "ids": [1]
            }
        })
        
        sample_titles = ["Switch 1", "Switch 2", "Switch 3"]
        
        # Create extraction context
        extraction_context = ExtractionStageContext(
            product_category=stage_context.product_category,
            input_texts=sample_titles
        )
        
        result = await extraction_stage._produce_result(
            raw_response, extraction_context, attempts=1
        )
        
        assert isinstance(result, ExtractionStageResult)
        assert len(result.taxonomies_extracted) == 2
        assert len(result.assignments_initial) == 3
        
        # Verify taxonomy conversion
        taxonomy_names = {t.name for t in result.taxonomies_extracted}
        assert taxonomy_names == {"Smart Switches", "Manual Switches"}
        
        # Verify assignment conversion (string keys -> int keys)
        assert result.assignments_initial[0] == "Smart Switches"
        assert result.assignments_initial[1] == "Manual Switches"
        assert result.assignments_initial[2] == "Smart Switches"

    @pytest.mark.asyncio
    async def test_merge_split_results(
        self,
        extraction_stage: ExtractionStage,
        stage_context: StageContext
    ) -> None:
        """Merge logic: de-dupe taxonomies, offset right-hand indices."""
        # Create left result
        left_result = ExtractionStageResult(
            taxonomies_extracted=[
                TaxonomyDTO(name="Category A", definition="Definition A"),
                TaxonomyDTO(name="Category B", definition="Definition B")
            ],
            assignments_initial={0: "Category A", 1: "Category B"}
        )
        
        # Create right result
        right_result = ExtractionStageResult(
            taxonomies_extracted=[
                TaxonomyDTO(name="Category B", definition="Definition B"),  # Duplicate
                TaxonomyDTO(name="Category C", definition="Definition C")
            ],
            assignments_initial={0: "Category B", 1: "Category C"}  # Indices relative to right sequence
        )
        
        # Create extraction contexts for left and right sides
        ctx_left = ExtractionStageContext(
            product_category=stage_context.product_category,
            input_texts=["item1", "item2"]
        )
        
        ctx_right = ExtractionStageContext(
            product_category=stage_context.product_category,
            input_texts=["item3", "item4"]
        )
        
        merged = await extraction_stage._merge_split_results(
            res_left=left_result,
            res_right=right_result,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        # Verify merged taxonomies (should deduplicate by name)
        taxonomy_names = {t.name for t in merged.taxonomies_extracted}
        assert taxonomy_names == {"Category A", "Category B", "Category C"}
        
        # Verify merged assignments
        assert len(merged.assignments_initial) == 4
        assert merged.assignments_initial[0] == "Category A"
        assert merged.assignments_initial[1] == "Category B"
        assert merged.assignments_initial[2] == "Category B"  # Right side index 0 + left_size(2) = 2
        assert merged.assignments_initial[3] == "Category C"  # Right side index 1 + left_size(2) = 3

    @pytest.mark.asyncio
    async def test_saved_taxonomy_results_structure(
        self,
        saved_taxonomy_results: dict
    ) -> None:
        """Verify that saved taxonomy results have the expected structure."""
        # Check metadata
        metadata = saved_taxonomy_results["metadata"]
        assert metadata["product_category"] == PRODUCT_CATEGORY
        assert metadata["total_products"] == TEST_PRODUCT_COUNT
        assert metadata["total_batches"] == 4  # 4 batches of 40 products each
        assert metadata["batch_size"] == PRODUCTS_PER_TAXONOMY_PROMPT
        assert "extraction_timestamp" in metadata
        
        # Check product titles
        assert len(saved_taxonomy_results["product_titles"]) == TEST_PRODUCT_COUNT
        assert all(isinstance(title, str) for title in saved_taxonomy_results["product_titles"])
        
        # Check taxonomies
        taxonomies = saved_taxonomy_results["taxonomies"]
        assert len(taxonomies) > 0
        for taxonomy in taxonomies:
            assert "name" in taxonomy
            assert "definition" in taxonomy
            assert isinstance(taxonomy["name"], str)
            assert isinstance(taxonomy["definition"], str)
        
        # Check assignments
        assignments = saved_taxonomy_results["assignments"]
        assert len(assignments) == TEST_PRODUCT_COUNT
        # Keys are saved as strings in JSON, so check that they can be converted to int
        assert all(idx.isdigit() for idx in assignments.keys())
        assert all(isinstance(name, str) for name in assignments.values())
        
        # Check batch results
        batch_results = saved_taxonomy_results["batch_results"]
        assert len(batch_results) == 4
        for batch in batch_results:
            assert "batch_idx" in batch
            assert "taxonomies_count" in batch
            assert "assignments_count" in batch
            assert "taxonomies" in batch
            assert "assignments" in batch 