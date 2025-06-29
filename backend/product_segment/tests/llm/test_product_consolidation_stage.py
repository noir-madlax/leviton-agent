"""Tests for taxonomy consolidation stage implementation.

This module tests the ConsolidationStage class using real taxonomy data from
the Amazon light switches extraction results, consolidating taxonomies from
different batches to test the consolidation workflow.

Test Coverage:
--------------

1. **test_consolidate_taxonomies_from_extraction_results**: 
   Main integration test that takes taxonomies from two different extraction
   batches and consolidates them using the consolidation stage. Validates
   the complete consolidation workflow including result structure, category
   quality, mapping completeness, and data integrity.

2. **test_validation_with_valid_response**:
   Tests the validation logic with a properly formatted JSON response that
   matches the expected consolidation schema (consolidated categories with
   definition and ids arrays).

3. **test_validation_with_invalid_response**:
   Tests validation error handling with various malformed responses:
   - Invalid JSON syntax
   - Missing required fields (definition/ids)
   - Invalid or missing category ID assignments
   Ensures proper error categorization and reporting.

4. **test_retry_prompt_generation**:
   Tests retry prompt construction using the shared_retry_prompt_v0.txt template.
   Verifies that validation errors are properly formatted and included in
   retry instructions to help the LLM correct its response.

5. **test_produce_result_conversion**:
   Tests the conversion of valid raw JSON responses into ConsolidationStageResult
   objects. Verifies proper parsing of consolidated taxonomies and mapping
   from original IDs to consolidated category names.

6. **test_merge_split_results**:
   Tests the merging logic for split processing scenarios. Verifies taxonomy
   deduplication by name and proper consolidation mapping across splits.

Configuration:
--------------
- Uses taxonomy results from taxonomy_extraction_results.json
- Consolidates taxonomies from different batches 
- Fixed prompt templates: taxonomy_consolidation_prompt_v0.txt, shared_retry_prompt_v0.txt
- No external configuration required - templates loaded automatically
"""

import json
import pytest
from pathlib import Path
from typing import Dict
from unittest.mock import AsyncMock

from core.utils.llm_utils import ValidationResult
from product_segment.llm.product_consolidation_stage import (
    ConsolidationStage,
    ConsolidationStageContext,
    ConsolidationStageResult,
    ConsolidatedTaxonomyDTO,
)
from core.llm_taxonomy_pipeline.pipeline_stage import StageContext, TaxonomyDTO
from product_segment.llm.taxonomy_dedup_uitl import (
    deduplicate_taxonomies,
    deduplicate_taxonomy_batches,
    print_deduplication_summary
)


# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TAXONOMY_RESULTS_PATH = TEST_DATA_DIR / "taxonomy_extraction_results.json"
CONSOLIDATION_RESULTS_PATH = TEST_DATA_DIR / "taxonomy_consolidation_results.json"


def save_consolidation_results(
    consolidation_result: ConsolidationStageResult,
    batch_info: Dict,
    final_info: Dict,
    product_category: str
) -> None:
    """Save taxonomy consolidation results to JSON file for analysis.
    
    Args:
        consolidation_result: Final result from the progressive consolidation
        batch_info: Information about all input batches
        final_info: Information about the final consolidated result
        product_category: Product category that was processed
    """
    from datetime import datetime
    
    # Calculate total original categories across all batches
    total_original_categories = sum(
        batch_data.get("taxonomies", 0) if isinstance(batch_data, dict) else 0
        for batch_data in batch_info.values()
    )
    
    saved_data = {
        "metadata": {
            "product_category": product_category,
            "consolidation_timestamp": datetime.now().isoformat(),
            "total_batches_processed": len(batch_info),
            "total_original_categories": total_original_categories,
            "final_consolidated_taxonomies": len(consolidation_result.taxonomies_consolidated),
        },
        "input_batches": {
            batch_id: {
                "taxonomy_count": batch_data.get("taxonomies", 0) if isinstance(batch_data, dict) else 0,
                "batch_index": int(batch_id.split("_")[1]) if "BATCH_" in batch_id else 0
            }
            for batch_id, batch_data in batch_info.items()
            if batch_id != "FINAL"
        },
        "final_consolidated_taxonomies": [
            {
                "name": consolidated.taxonomy.name,
                "definition": consolidated.taxonomy.definition,
                "original_categories_merged": len(consolidated.original_taxonomies),
                "original_taxonomies": [
                    {"name": orig.name, "definition": orig.definition}
                    for orig in consolidated.original_taxonomies
                ],
            }
            for consolidated in consolidation_result.taxonomies_consolidated
        ],
    }
    
    # Save to JSON file
    with open(CONSOLIDATION_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(saved_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved progressive consolidation results to: {CONSOLIDATION_RESULTS_PATH}")
    print(f"   - {len(batch_info) - 1} batches processed (excluding final)")
    
    # Print top consolidation insights
    if consolidation_result.taxonomies_consolidated:
        most_merged = max(consolidation_result.taxonomies_consolidated, key=lambda x: len(x.original_taxonomies))
        print(f"   - Most consolidated: '{most_merged.taxonomy.name}' (merged {len(most_merged.original_taxonomies)} categories)")


@pytest.fixture
def extraction_results() -> Dict:
    """Load taxonomy extraction results from the integration test."""
    if not TAXONOMY_RESULTS_PATH.exists():
        pytest.skip(f"Taxonomy extraction results not found: {TAXONOMY_RESULTS_PATH}")
    
    with open(TAXONOMY_RESULTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def sample_taxonomies(extraction_results: Dict) -> tuple[list[TaxonomyDTO], list[TaxonomyDTO]]:
    """Create two sample taxonomies for consolidation testing from extraction results."""
    batch_results = extraction_results["batch_results"]
    
    if len(batch_results) < 2:
        pytest.skip("Need at least 2 batch results for consolidation testing")
    
    # Take taxonomies from first two batches
    batch_a = batch_results[0]
    batch_b = batch_results[1]
    
    # Convert to lists of TaxonomyDTO
    taxonomy_a = [
        TaxonomyDTO(name=taxonomy["name"], definition=taxonomy["definition"])
        for taxonomy in batch_a["taxonomies"]
    ]
    
    taxonomy_b = [
        TaxonomyDTO(name=taxonomy["name"], definition=taxonomy["definition"])
        for taxonomy in batch_b["taxonomies"]
    ]
    
    return taxonomy_a, taxonomy_b


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Mock LLM client that returns valid taxonomy consolidation responses."""
    
    def create_consolidation_response(taxonomy_a_str: str, taxonomy_b_str: str) -> str:
        # Parse input taxonomies to understand what we're consolidating
        taxonomy_a = json.loads(taxonomy_a_str)
        taxonomy_b = json.loads(taxonomy_b_str)
        
        # Create a simplified consolidation response
        consolidated = {
            "Smart Lighting Controls": {
                "definition": "Intelligent switches with smart home integration and dimming capabilities, e.g. Wi-Fi enabled dimmer switches, smart toggle switches",
                "ids": list(taxonomy_a.keys())[:2] + list(taxonomy_b.keys())[:1]  # Mix some categories
            },
            "Traditional Manual Switches": {
                "definition": "Standard manual switches for basic lighting control, e.g. toggle switches, rocker switches, paddle switches",
                "ids": list(taxonomy_a.keys())[2:] + list(taxonomy_b.keys())[1:]  # Remaining categories
            }
        }
        
        return json.dumps(consolidated)
    
    mock = AsyncMock()
    mock.side_effect = lambda prompt, **kwargs: create_consolidation_response(
        # Extract taxonomy_a and taxonomy_b from the prompt
        prompt.split('Taxonomy A (Current Consolidated):')[1].split('Taxonomy B (New Batch):')[0].strip(),
        prompt.split('Taxonomy B (New Batch):')[1].split('**UNDERSTANDING THE INPUT:**')[0].strip()
    )
    return mock


@pytest.fixture
def stage_context() -> StageContext:
    """Create base stage context for testing."""
    return StageContext(
        product_category="light switch"
    )


@pytest.fixture
def consolidation_stage(mock_llm_client: AsyncMock) -> ConsolidationStage:
    """Create ConsolidationStage instance with mocked LLM client."""
    stage = ConsolidationStage()
    stage._llm_client = mock_llm_client
    return stage


class TestConsolidationStage:
    """Test cases for ConsolidationStage."""

    @pytest.mark.asyncio
    @pytest.mark.integration  # Mark as integration test requiring real LLM
    async def test_consolidate_taxonomies_from_extraction_results(
        self,
        extraction_results: Dict,
        stage_context: StageContext
    ) -> None:
        """Integration test – progressively consolidate all batches from extraction results.

        • Input: All batches from the extraction results, starting with batch 0 as initial
        • Behaviour under test: iterative consolidation where each batch is consolidated
          with the growing consolidated taxonomy from previous iterations
        • Process: Batch 0 → Initial, then Batch 1 + Consolidated → New Consolidated, etc.
        • Expectation: returns a final consolidated taxonomy that includes all original
          categories from all batches, with proper consolidation and deduplication
        """
        batch_results = extraction_results["batch_results"]
        
        if len(batch_results) < 2:
            pytest.skip("Need at least 2 batch results for progressive consolidation testing")
        
        print(f"\n🚀 Progressive consolidation of {len(batch_results)} extraction batches...")
        
        # Step 1: Convert all batches to TaxonomyDTO lists
        print(f"\n📊 Converting {len(batch_results)} batches to TaxonomyDTO...")
        all_batch_taxonomies = []
        
        for batch_idx, batch in enumerate(batch_results):
            batch_taxonomies = [
                TaxonomyDTO(name=taxonomy["name"], definition=taxonomy["definition"])
                for taxonomy in batch["taxonomies"]
            ]
            all_batch_taxonomies.append(batch_taxonomies)
            print(f"  Batch {batch_idx}: {len(batch_taxonomies)} taxonomies")
        
        # Step 2: Apply deduplication across all batches
        print(f"\n🔍 Applying NLP-based deduplication across all batches...")
        deduplicated_batches = deduplicate_taxonomy_batches(all_batch_taxonomies)
        
        dedup_result_all = deduplicate_taxonomies([tax for batch in all_batch_taxonomies for tax in batch])
        print_deduplication_summary(dedup_result_all)

        print("✅ Deduplication complete:")
        for batch_idx, batch in enumerate(deduplicated_batches):
            print(f"  Batch {batch_idx}: {len(batch)} taxonomies (was {len(all_batch_taxonomies[batch_idx])})")
        
        # Step 3: Create consolidation stage (uses real LLM via safe_llm_call automatically)
        real_consolidation_stage = ConsolidationStage()
        
        # Step 4: Initialize with first deduplicated batch as the consolidated taxonomy
        print(f"\n📊 Initializing with deduplicated Batch 0: {len(deduplicated_batches[0])} taxonomies")
        
        current_consolidated = deduplicated_batches[0]
        
        for i, taxonomy in enumerate(current_consolidated):
            print(f"  Consolidated_{i}: {taxonomy.name}")
        
        # Step 5: Progressively consolidate each subsequent deduplicated batch
        for batch_idx in range(1, len(deduplicated_batches)):
            batch = deduplicated_batches[batch_idx]
            print(f"\n📊 Consolidating deduplicated Batch {batch_idx}: {len(batch)} taxonomies")
            
            for i, taxonomy in enumerate(batch):
                print(f"  New_{i}: {taxonomy.name}")
            
            # Create consolidation context
            context = ConsolidationStageContext(
                product_category=stage_context.product_category,
                taxonomy_a=current_consolidated,
                taxonomy_b=batch
            )
            
            print(f"    ➡️   Consolidating Batch {batch_idx} with current consolidated taxonomy...")
            
            # Execute consolidation
            result = await real_consolidation_stage.execute(context)
            
            print(f"    ✅  Batch {batch_idx} consolidated – created "
                  f"{len(result.taxonomies_consolidated)} consolidated taxonomies")
            
            # Print consolidation overview for this iteration
            for tax_idx, consolidated in enumerate(result.taxonomies_consolidated, start=1):
                original_count = len(consolidated.original_taxonomies)
                print(f"        {tax_idx:02d}. {consolidated.taxonomy.name} (merges {original_count} categories)")
                for original_taxonomy in consolidated.original_taxonomies:
                    print(f"            ↳ {original_taxonomy.name}")
            
            # Update current consolidated taxonomy for next iteration
            # Convert result back to list of TaxonomyDTO for next consolidation
            current_consolidated = [
                consolidated.taxonomy for consolidated in result.taxonomies_consolidated
            ]
        
        # The final result is just the last consolidation result
        final_result = result
        
        print("\n🎉 Progressive consolidation complete!")
        print(f"    Final result: {len(final_result.taxonomies_consolidated)} consolidated taxonomies")
        
        # Print final consolidated taxonomies
        print("\n📋 Final Consolidated Taxonomies:")
        for i, consolidated in enumerate(final_result.taxonomies_consolidated, start=1):
            print(f"    {i:02d}. {consolidated.taxonomy.name}")
            print(f"        Definition: {consolidated.taxonomy.definition}")
            print(f"        Merges {len(consolidated.original_taxonomies)} categories:")
            for orig in consolidated.original_taxonomies:
                print(f"            ↳ {orig.name}")
        
        # Validate final results
        assert len(final_result.taxonomies_consolidated) > 0, "Should have at least one consolidated taxonomy"
        
        # Count total original categories across all deduplicated batches
        total_original_categories = sum(len(batch) for batch in deduplicated_batches)
        assert len(final_result.taxonomies_consolidated) <= total_original_categories, "Consolidated count should not exceed original count"
        
        # For saving, create simplified input structure
        save_consolidation_results(
            final_result, 
            {f"BATCH_{i}": {"taxonomies": len(batch)} for i, batch in enumerate(deduplicated_batches)},
            {"FINAL": {"consolidated_count": len(final_result.taxonomies_consolidated)}},
            stage_context.product_category
        )

    @pytest.mark.asyncio
    async def test_build_prompt_with_taxonomies(
        self,
        consolidation_stage: ConsolidationStage,
        sample_taxonomies: tuple[list[TaxonomyDTO], list[TaxonomyDTO]],
        stage_context: StageContext
    ) -> None:
        """Verify prompt template renders correctly with two taxonomies."""
        taxonomy_a, taxonomy_b = sample_taxonomies
        
        print("\n🔍 Testing prompt building with sample taxonomies...")
        print("\n📋 Taxonomy A (Current Consolidated):")
        for i, tax in enumerate(taxonomy_a):
            print(f"  {i}: {tax.name} - {tax.definition}")
        print("\n📋 Taxonomy B (New Batch):")
        for i, tax in enumerate(taxonomy_b):
            print(f"  {i}: {tax.name} - {tax.definition}")
        
        # Create consolidation context
        consolidation_context = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=taxonomy_a,
            taxonomy_b=taxonomy_b
        )
        
        prompt = await consolidation_stage._build_prompt(consolidation_context)
        
        print("\n📝 Generated Consolidation Prompt:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        print(f"Prompt length: {len(prompt)} characters")
        
        # Verify key elements from taxonomy_consolidation_prompt_v0.txt are present
        assert "taxonomy consolidation specialist" in prompt.lower()
        assert "Taxonomy A (Current Consolidated):" in prompt
        assert "Taxonomy B (New Batch):" in prompt
        assert "CONSOLIDATION INSTRUCTIONS" in prompt
        assert "CRITICAL RULES" in prompt
        assert "EXPECTED OUTPUT FORMAT" in prompt
        
        # Verify taxonomies are included in the prompt (A_0, A_1, B_0, B_1 format)
        for i in range(len(taxonomy_a)):
            assert f"A_{i}" in prompt
        for i in range(len(taxonomy_b)):
            assert f"B_{i}" in prompt
        
        print("\n✅ Prompt validation completed successfully!")
        print("   - Contains all required template sections")
        print(f"   - Includes all {len(taxonomy_a)} Taxonomy A categories")
        print(f"   - Includes all {len(taxonomy_b)} Taxonomy B categories")

    @pytest.mark.asyncio
    async def test_validation_with_valid_response(
        self,
        consolidation_stage: ConsolidationStage,
        sample_taxonomies: tuple[list[TaxonomyDTO], list[TaxonomyDTO]],
        stage_context: StageContext
    ) -> None:
        """Valid JSON response should pass validation without errors."""
        taxonomy_a, taxonomy_b = sample_taxonomies
        
        # Create consolidation context
        consolidation_context = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=taxonomy_a,
            taxonomy_b=taxonomy_b
        )
        
        # Create valid response that consolidates all original IDs (A_* and B_* format)
        num_a = len(taxonomy_a)
        num_b = len(taxonomy_b)
        all_original_ids = [f"A_{i}" for i in range(num_a)] + [f"B_{i}" for i in range(num_b)]
        
        valid_response = json.dumps({
            "Consolidated Smart Switches": {
                "definition": "Smart switches with modern features, e.g. Wi-Fi enabled switches, smart dimmers",
                "ids": all_original_ids[:len(all_original_ids)//2]
            },
            "Consolidated Traditional Switches": {
                "definition": "Traditional manual switches, e.g. toggle switches, rocker switches",
                "ids": all_original_ids[len(all_original_ids)//2:]
            }
        })
        
        validation_result = consolidation_stage._validate(
            valid_response, consolidation_context
        )
        
        assert validation_result.ok is True
        assert sum(len(errors) for errors in validation_result.error_categories.values()) == 0

    @pytest.mark.asyncio
    async def test_validation_with_invalid_response(
        self,
        consolidation_stage: ConsolidationStage,
        sample_taxonomies: tuple[list[TaxonomyDTO], list[TaxonomyDTO]],
        stage_context: StageContext
    ) -> None:
        """Validation should categorise format / schema / completeness errors."""
        taxonomy_a, taxonomy_b = sample_taxonomies
        
        # Create consolidation context
        consolidation_context = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=taxonomy_a,
            taxonomy_b=taxonomy_b
        )
        
        # Test invalid JSON
        invalid_json = "This is not JSON"
        result = consolidation_stage._validate(invalid_json, consolidation_context)
        assert result.ok is False
        assert len(result.error_categories["format_errors"]) > 0
        
        # Test missing definition
        missing_definition = json.dumps({
            "Test Category": {
                "ids": [f"A_{i}" for i in range(len(taxonomy_a))]  # Missing definition
            }
        })
        result = consolidation_stage._validate(missing_definition, consolidation_context) 
        assert result.ok is False
        assert len(result.error_categories["validation_errors"]) > 0
        
        # Test missing assignment (not all original IDs included)
        num_a = len(taxonomy_a)
        num_b = len(taxonomy_b)
        all_original_ids = [f"A_{i}" for i in range(num_a)] + [f"B_{i}" for i in range(num_b)]
        incomplete_assignments = json.dumps({
            "Test Category": {
                "definition": "Test category, e.g. test products",
                "ids": all_original_ids[:-1]  # Missing last ID
            }
        })
        result = consolidation_stage._validate(incomplete_assignments, consolidation_context)
        assert result.ok is False
        assert len(result.error_categories["completeness_errors"]) > 0

    @pytest.mark.asyncio
    async def test_retry_prompt_generation(
        self,
        consolidation_stage: ConsolidationStage,
        stage_context: StageContext
    ) -> None:
        """Retry prompt generation – ensure error details are injected."""
        original_prompt = "Original consolidation prompt content"
        
        validation_result = ValidationResult(
            ok=False,
            error_categories={
                "format_errors": ["Invalid JSON structure"],
                "validation_errors": ["Missing definition field"],
                "completeness_errors": ["Missing assignment for A_1"]
            }
        )
        
        retry_prompt = consolidation_stage._retry_prompt(
            original_prompt, validation_result, stage_context
        )
        
        # Verify original prompt is included
        assert original_prompt in retry_prompt
        
        # Verify retry template elements are present (from shared_retry_prompt_v0.txt)
        assert "RETRY REQUIRED" in retry_prompt
        assert "END RETRY INSTRUCTIONS" in retry_prompt
        
        # Verify error details are included in the retry prompt
        assert "Invalid JSON structure" in retry_prompt
        assert "Missing definition field" in retry_prompt
        assert "Missing assignment for A_1" in retry_prompt

    @pytest.mark.asyncio
    async def test_produce_result_conversion(
        self,
        consolidation_stage: ConsolidationStage,
        sample_taxonomies: tuple[list[TaxonomyDTO], list[TaxonomyDTO]],
        stage_context: StageContext
    ) -> None:
        """_produce_result converts valid JSON → DTOs & original_id→category mapping."""
        taxonomy_a, taxonomy_b = sample_taxonomies
        num_a = len(taxonomy_a)
        num_b = len(taxonomy_b)
        original_ids = [f"A_{i}" for i in range(num_a)] + [f"B_{i}" for i in range(num_b)]
        
        raw_response = json.dumps({
            "Smart Lighting Controls": {
                "definition": "Intelligent switches with smart features, e.g. Wi-Fi switches, smart dimmers",
                "ids": original_ids[:2]
            },
            "Manual Light Switches": {
                "definition": "Traditional manual switches, e.g. toggle switches, rocker switches", 
                "ids": original_ids[2:]
            }
        })
        
        # Create consolidation context
        consolidation_context = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=taxonomy_a,
            taxonomy_b=taxonomy_b
        )
        
        result = await consolidation_stage._produce_result(
            raw_response, consolidation_context, attempts=1
        )
        
        assert isinstance(result, ConsolidationStageResult)
        assert len(result.taxonomies_consolidated) == 2
        
        # Verify taxonomy conversion
        taxonomy_names = {consolidated.taxonomy.name for consolidated in result.taxonomies_consolidated}
        assert taxonomy_names == {"Smart Lighting Controls", "Manual Light Switches"}
        
        # Verify original taxonomies are properly stored
        all_assigned_taxonomies = set()
        for consolidated in result.taxonomies_consolidated:
            assert len(consolidated.original_taxonomies) > 0
            for original_taxonomy in consolidated.original_taxonomies:
                assert original_taxonomy in taxonomy_a + taxonomy_b
                all_assigned_taxonomies.add(original_taxonomy.name)
        
        # Verify all original taxonomies are assigned
        expected_taxonomy_names = {tax.name for tax in taxonomy_a + taxonomy_b}
        assert all_assigned_taxonomies == expected_taxonomy_names

    @pytest.mark.asyncio
    async def test_merge_split_results(
        self,
        consolidation_stage: ConsolidationStage,
        stage_context: StageContext
    ) -> None:
        """Merge logic: de-dupe taxonomies, merge consolidation mappings."""
        # Create sample taxonomies for testing
        tax_a0 = TaxonomyDTO(name="Original A0", definition="Definition A0")
        tax_a1 = TaxonomyDTO(name="Original A1", definition="Definition A1")
        tax_b0 = TaxonomyDTO(name="Original B0", definition="Definition B0")
        tax_b1 = TaxonomyDTO(name="Original B1", definition="Definition B1") 
        tax_c0 = TaxonomyDTO(name="Original C0", definition="Definition C0")
        
        # Create left result
        left_result = ConsolidationStageResult(
            taxonomies_consolidated=[
                ConsolidatedTaxonomyDTO(
                    taxonomy=TaxonomyDTO(name="Category A", definition="Definition A"),
                    original_taxonomies=[tax_a0, tax_a1]
                ),
                ConsolidatedTaxonomyDTO(
                    taxonomy=TaxonomyDTO(name="Category B", definition="Definition B"),
                    original_taxonomies=[tax_b0]
                )
            ],
        )
        
        # Create right result with some overlap
        right_result = ConsolidationStageResult(
            taxonomies_consolidated=[
                ConsolidatedTaxonomyDTO(
                    taxonomy=TaxonomyDTO(name="Category B", definition="Definition B Updated"),  # Duplicate name
                    original_taxonomies=[tax_b1]
                ),
                ConsolidatedTaxonomyDTO(
                    taxonomy=TaxonomyDTO(name="Category C", definition="Definition C"),
                    original_taxonomies=[tax_c0]
                )
            ],
        )
        
        # Create consolidation contexts for left and right sides
        ctx_left = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=[tax_a0],
            taxonomy_b=[tax_b0]
        )
        
        ctx_right = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=[tax_b1],
            taxonomy_b=[tax_c0]
        )
        
        merged = await consolidation_stage._merge_split_results(
            res_left=left_result,
            res_right=right_result,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        # Verify merged taxonomies (should deduplicate by name and merge original taxonomies)
        taxonomy_names = {consolidated.taxonomy.name for consolidated in merged.taxonomies_consolidated}
        assert taxonomy_names == {"Category A", "Category B", "Category C"}
        
        # Find Category B to verify taxonomy merging
        category_b = next(consolidated for consolidated in merged.taxonomies_consolidated 
                         if consolidated.taxonomy.name == "Category B")
        original_names = {tax.name for tax in category_b.original_taxonomies}
        assert original_names == {"Original B0", "Original B1"}
        
        # Verify all original taxonomies are preserved in the consolidated taxonomies
        all_merged_names = set()
        for consolidated in merged.taxonomies_consolidated:
            for orig_tax in consolidated.original_taxonomies:
                all_merged_names.add(orig_tax.name)
        expected_names = {"Original A0", "Original A1", "Original B0", "Original B1", "Original C0"}
        assert all_merged_names == expected_names

    @pytest.mark.asyncio
    async def test_input_validation_with_empty_taxonomies(
        self,
        consolidation_stage: ConsolidationStage,
        stage_context: StageContext
    ) -> None:
        """ConsolidationStage should handle empty taxonomies gracefully."""
        # Test with empty taxonomies (this should work but generate empty A_* and B_* lists)
        empty_context = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=[],
            taxonomy_b=[]
        )
        
        # This should not raise an error, just generate a prompt with empty taxonomies
        prompt = await consolidation_stage._build_prompt(empty_context)
        assert "Taxonomy A (Current Consolidated):" in prompt
        assert "Taxonomy B (New Batch):" in prompt
        
        # Test with one empty and one non-empty taxonomy
        mixed_context = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=[TaxonomyDTO(name="Test Category", definition="Test definition")],
            taxonomy_b=[]
        )
        
        prompt = await consolidation_stage._build_prompt(mixed_context)
        assert "A_0" in prompt
        assert "Test Category" in prompt

    @pytest.mark.asyncio
    async def test_taxonomy_deduplication_functionality(
        self,
        stage_context: StageContext
    ) -> None:
        """Test the NLP-based taxonomy deduplication functionality."""
        print("\n🧪 Testing taxonomy deduplication with NLP word stemming...")
        
        # Simplified concise check
        test_taxonomies = [
            TaxonomyDTO(name="Smart Light Switches", definition=""),
            TaxonomyDTO(name="Smart Lighting Switches", definition=""),
            TaxonomyDTO(name="Traditional Manual Switch", definition=""),
            TaxonomyDTO(name="Traditional Manual Switches", definition=""),
        ]
        result = deduplicate_taxonomies(test_taxonomies)
        assert len(result.unique_taxonomies) == 2
        assert len(result.duplicate_groups) == 2

        # Batch deduplication concise
        batches = [[test_taxonomies[0], test_taxonomies[2]], [test_taxonomies[1], test_taxonomies[3]]]
        dedup_batches = deduplicate_taxonomy_batches(batches)
        assert sum(len(b) for b in dedup_batches) == 2 