"""Tests for taxonomy refinement stage implementation.

This module tests the RefinementStage class using real taxonomy data from
the Amazon light switches extraction results, refining product assignments
to ensure they are in the most appropriate subcategories.

Test Coverage:
--------------

1. **test_refine_taxonomies_from_extraction_results**: 
   Main integration test that takes taxonomies and assignments from extraction
   results and processes them through the refinement stage. Validates
   the complete refinement workflow including result structure, assignment
   quality, and data integrity.

2. **test_validation_with_valid_response**:
   Tests the validation logic with a properly formatted JSON response that
   matches the expected refinement schema (product reassignments or empty object).

3. **test_validation_with_invalid_response**:
   Tests validation error handling with various malformed responses:
   - Invalid JSON syntax
   - Invalid product or subcategory IDs
   - Self-assignments (products assigned to current category)
   Ensures proper error categorization and reporting.

4. **test_retry_prompt_generation**:
   Tests retry prompt construction using the shared_retry_prompt_v0.txt template.
   Verifies that validation errors are properly formatted and included in
   retry instructions to help the LLM correct its response.

5. **test_produce_result_conversion**:
   Tests the conversion of valid raw JSON responses into RefinementStageResult
   objects. Verifies proper parsing of reassignments and conversion of
   product/subcategory IDs.

6. **test_merge_split_results**:
   Tests the merging logic for split processing scenarios. Verifies proper
   index adjustment and reassignment consolidation across splits.

Configuration:
--------------
- Uses taxonomy and assignment results from taxonomy_extraction_results.json
- Product category: "light switch" 
- Fixed prompt templates: taxonomy_refinement_prompt_v0.txt, shared_retry_prompt_v0.txt
- No external configuration required - templates loaded automatically
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock

from core.utils.llm_utils import ValidationResult
from product_segment.llm.taxonomy_refinement import (
    RefinementStage,
    RefinementStageResult,
    RefinementStageContext,
)
from product_segment.llm.taxonomy_pipeline_stage import StageContext, TaxonomyDTO


# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TAXONOMY_RESULTS_PATH = TEST_DATA_DIR / "taxonomy_extraction_results.json"
REFINEMENT_RESULTS_PATH = TEST_DATA_DIR / "taxonomy_refinement_results.json"


def save_refinement_results(
    refinement_result: RefinementStageResult,
    original_assignments: dict[int, str],
    taxonomies: list[TaxonomyDTO],
    product_titles: list[str],
    product_category: str
) -> None:
    """Save taxonomy refinement results to JSON file for analysis.
    
    Args:
        refinement_result: Result from the refinement stage
        original_assignments: Original product assignments before refinement
        taxonomies: List of available taxonomies
        product_titles: Product titles indexed by product ID
        product_category: Product category that was processed
    """
    from datetime import datetime
    
    # Calculate final assignments by applying reassignments to original assignments
    final_assignments = dict(original_assignments)
    final_assignments.update(refinement_result.reassignments)
    
    # Count reassignments by taxonomy
    reassignment_counts = {}
    for product_id, new_taxonomy in refinement_result.reassignments.items():
        old_taxonomy = original_assignments.get(product_id, "UNASSIGNED")
        reassignment_key = f"{old_taxonomy} → {new_taxonomy}"
        reassignment_counts[reassignment_key] = reassignment_counts.get(reassignment_key, 0) + 1
    
    saved_data = {
        "metadata": {
            "product_category": product_category,
            "refinement_timestamp": datetime.now().isoformat(),
            "total_products": len(product_titles),
            "total_taxonomies": len(taxonomies),
            "products_reassigned": len(refinement_result.reassignments),
            "reassignment_percentage": round(len(refinement_result.reassignments) / len(product_titles) * 100, 2),
        },
        "taxonomies": [
            {"name": taxonomy.name, "definition": taxonomy.definition}
            for taxonomy in taxonomies
        ],
        "product_titles": product_titles,
        "original_assignments": {str(k): v for k, v in original_assignments.items()},
        "reassignments": {str(k): v for k, v in refinement_result.reassignments.items()},
        "final_assignments": {str(k): v for k, v in final_assignments.items()},
        "reassignment_summary": reassignment_counts,
        "reassigned_products": [
            {
                "product_id": product_id,
                "product_title": product_titles[product_id] if product_id < len(product_titles) else "UNKNOWN",
                "original_taxonomy": original_assignments.get(product_id, "UNASSIGNED"),
                "new_taxonomy": new_taxonomy,
                "reassignment_reason": f"Better fit in {new_taxonomy}"
            }
            for product_id, new_taxonomy in refinement_result.reassignments.items()
        ]
    }
    
    # Save to JSON file
    with open(REFINEMENT_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(saved_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved refinement results to: {REFINEMENT_RESULTS_PATH}")
    print(f"   - {len(refinement_result.reassignments)} products reassigned")
    print(f"   - {saved_data['metadata']['reassignment_percentage']}% reassignment rate")
    
    # Print top reassignment patterns
    if reassignment_counts:
        print(f"   - Top reassignment patterns:")
        for pattern, count in sorted(reassignment_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"     • {pattern}: {count} products")


@pytest.fixture
def extraction_results() -> Dict:
    """Load taxonomy extraction results from the integration test."""
    if not TAXONOMY_RESULTS_PATH.exists():
        pytest.skip(f"Taxonomy extraction results not found: {TAXONOMY_RESULTS_PATH}")
    
    with open(TAXONOMY_RESULTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def sample_refinement_data(extraction_results: Dict) -> tuple[list[TaxonomyDTO], dict[int, str], list[str]]:
    """Create sample data for refinement testing from extraction results."""
    
    # Convert taxonomies to TaxonomyDTO
    taxonomies = [
        TaxonomyDTO(name=taxonomy["name"], definition=taxonomy["definition"])
        for taxonomy in extraction_results["taxonomies"]
    ]
    
    # Convert assignments to int keys
    assignments = {
        int(k): v for k, v in extraction_results["assignments"].items()
    }
    
    # Get product titles
    product_titles = extraction_results["product_titles"]
    
    return taxonomies, assignments, product_titles


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Mock LLM client that returns valid taxonomy refinement responses."""
    
    def create_refinement_response(prompt: str) -> str:
        # Parse the prompt to find products and their current assignments
        # For testing, we'll simulate some reassignments
        
        # Extract product count from prompt (count P_* entries)
        product_count = len([line for line in prompt.split('\n') if 'P_' in line and '→' in line])
        
        # Simulate some reassignments (about 10% of products)
        reassignments = {}
        reassignment_count = max(1, product_count // 10)
        
        for i in range(reassignment_count):
            product_id = f"P_{i}"
            # Simulate reassigning to different subcategory
            subcategory_id = f"S_{(i + 1) % 5}"  # Rotate through first 5 subcategories
            reassignments[product_id] = subcategory_id
        
        return json.dumps(reassignments)
    
    mock = AsyncMock()
    mock.side_effect = lambda prompt, **kwargs: create_refinement_response(prompt)
    return mock


@pytest.fixture
def stage_context() -> StageContext:
    """Create base stage context for testing."""
    return StageContext(
        product_category="light switch"
    )


@pytest.fixture
def refinement_stage(mock_llm_client: AsyncMock) -> RefinementStage:
    """Create RefinementStage instance with mocked LLM client."""
    stage = RefinementStage()
    stage._llm_client = mock_llm_client
    return stage


class TestRefinementStage:
    """Test cases for RefinementStage."""

    @pytest.mark.asyncio
    @pytest.mark.integration  # Mark as integration test requiring real LLM
    async def test_refine_taxonomies_from_extraction_results(
        self,
        extraction_results: Dict,
        stage_context: StageContext
    ) -> None:
        """Integration test – real LLM refinement of extraction results in batches.

        • Input: Taxonomies and assignments from taxonomy_extraction_results.json
        • Behaviour under test: end-to-end `RefinementStage.execute` in parallel batches
          including prompt construction, validation / retry loop, and JSON → DTO parsing.
        • Expectation: returns valid `RefinementStageResult`s with reassignments that
          improve the original taxonomy assignments, aggregated across all batches.
        • Results are saved to test_data/taxonomy_refinement_results.json for analysis.
        Requires `ANTHROPIC_API_KEY` & network access – run with -m integration.
        """
        import asyncio
        from product_segment.config import PRODUCTS_PER_REFINEMENT
        
        print(f"\n🚀 Starting taxonomy refinement of extraction results in batches...")
        
        # Extract data from extraction results
        taxonomies = [
            TaxonomyDTO(name=taxonomy["name"], definition=taxonomy["definition"])
            for taxonomy in extraction_results["taxonomies"]
        ]
        
        assignments = {
            int(k): v for k, v in extraction_results["assignments"].items()
        }
        
        product_titles = extraction_results["product_titles"]
        
        print(f"📊 Input data:")
        print(f"   - {len(taxonomies)} taxonomies")
        print(f"   - {len(assignments)} product assignments")
        print(f"   - {len(product_titles)} product titles")
        
        print(f"\n📋 Available Taxonomies:")
        for i, taxonomy in enumerate(taxonomies):
            print(f"  {i:02d}. {taxonomy.name}")
            print(f"      {taxonomy.definition}")
        
        # Count assignments per taxonomy
        assignment_counts = {}
        for product_id, taxonomy_name in assignments.items():
            assignment_counts[taxonomy_name] = assignment_counts.get(taxonomy_name, 0) + 1
        
        print(f"\n📈 Current Assignment Distribution:")
        for taxonomy_name, count in sorted(assignment_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = round(count / len(assignments) * 100, 1)
            print(f"   - {taxonomy_name}: {count} products ({percentage}%)")
        
        # Create refinement stage (uses real LLM via safe_llm_call automatically)
        real_refinement_stage = RefinementStage()

        # Split into batches for processing
        batch_size = PRODUCTS_PER_REFINEMENT
        batches: list[tuple[list[str], dict[int, str]]] = []
        
        for i in range(0, len(product_titles), batch_size):
            batch_titles = product_titles[i:i + batch_size]
            # Create batch assignments with local indices (0-based for each batch)
            batch_assignments = {}
            for local_idx, global_idx in enumerate(range(i, min(i + batch_size, len(product_titles)))):
                if global_idx in assignments:
                    batch_assignments[local_idx] = assignments[global_idx]
            
            batches.append((batch_titles, batch_assignments))

        print(f"\n🚀 Processing {len(batches)} batches in parallel...")
        print(f"📊 Batch size: {batch_size} products per batch")
        
        # Create all batch contexts
        batch_contexts = []
        for batch_idx, (batch_titles, batch_assignments) in enumerate(batches, start=1):
            print(f"\n🟡  Batch {batch_idx}/{len(batches)} – {len(batch_titles)} titles")
            for i, title in enumerate(batch_titles[:3]):  # Show first 3 titles
                current_taxonomy = batch_assignments.get(i, "UNASSIGNED")
                print(f"  [{i}] {title} → {current_taxonomy}")
            if len(batch_titles) > 3:
                print(f"  ... and {len(batch_titles) - 3} more products")
                
            context = RefinementStageContext(
                product_category=stage_context.product_category,
                taxonomies=taxonomies,
                current_assignments=batch_assignments,
                input_texts=batch_titles,
            )
            batch_contexts.append((batch_idx, batch_titles, batch_assignments, context))

        print("\n➡️   Calling real LLM for all batches in parallel...")
        
        # Execute all batches in parallel
        async def process_batch(
            batch_idx: int, 
            batch_titles: List[str], 
            batch_assignments: dict[int, str], 
            context: RefinementStageContext
        ) -> RefinementStageResult:
            result = await real_refinement_stage.execute(context)
            print(f"✅  Batch {batch_idx} finished – {len(result.reassignments)} reassignments")
            
            # Print reassignments for this batch
            if result.reassignments:
                for local_idx, new_taxonomy in result.reassignments.items():
                    old_taxonomy = batch_assignments.get(local_idx, "UNASSIGNED")
                    product_title = batch_titles[local_idx] if local_idx < len(batch_titles) else "UNKNOWN"
                    print(f"    Batch {batch_idx} - P_{local_idx}: {old_taxonomy} → {new_taxonomy}")
                    print(f"      Product: {product_title[:60]}...")
            else:
                print(f"    Batch {batch_idx} - No reassignments needed")
            
            return result
        
        # Run all batches concurrently
        tasks = [
            process_batch(batch_idx, batch_titles, batch_assignments, context)
            for batch_idx, batch_titles, batch_assignments, context in batch_contexts
        ]
        
        all_results = await asyncio.gather(*tasks)

        # Aggregate results across all batches
        print(f"\n🔄 Aggregating results from {len(all_results)} batches...")
        
        final_reassignments = {}
        batch_offset = 0
        
        for batch_idx, result in enumerate(all_results):
            # Adjust local indices to global indices
            for local_idx, new_taxonomy in result.reassignments.items():
                global_idx = batch_offset + local_idx
                final_reassignments[global_idx] = new_taxonomy
            
            batch_offset += len(batches[batch_idx][0])  # Add batch size
        
        # Create aggregated result
        aggregated_result = RefinementStageResult(reassignments=final_reassignments)
        
        print(f"\n✅ Refinement completed across all batches!")
        print(f"   - {len(aggregated_result.reassignments)} total products reassigned")
        
        if aggregated_result.reassignments:
            reassignment_percentage = round(len(aggregated_result.reassignments) / len(product_titles) * 100, 2)
            print(f"   - {reassignment_percentage}% reassignment rate")
            
            print(f"\n📋 All Reassignments Made:")
            for product_id, new_taxonomy in sorted(aggregated_result.reassignments.items()):
                old_taxonomy = assignments.get(product_id, "UNASSIGNED")
                product_title = product_titles[product_id] if product_id < len(product_titles) else "UNKNOWN"
                print(f"   • P_{product_id}: {old_taxonomy} → {new_taxonomy}")
                print(f"     Product: {product_title}")
            
            # Count reassignments by new taxonomy
            new_taxonomy_counts = {}
            for new_taxonomy in aggregated_result.reassignments.values():
                new_taxonomy_counts[new_taxonomy] = new_taxonomy_counts.get(new_taxonomy, 0) + 1
            
            print(f"\n📈 Reassignments by New Taxonomy:")
            for taxonomy_name, count in sorted(new_taxonomy_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {taxonomy_name}: {count} products")
        else:
            print(f"   - No reassignments needed - all products optimally assigned")
        
        # Validate aggregated results
        assert isinstance(aggregated_result, RefinementStageResult)
        assert isinstance(aggregated_result.reassignments, dict)
        
        # Verify all reassigned product IDs are valid
        for product_id in aggregated_result.reassignments.keys():
            assert 0 <= product_id < len(product_titles), f"Invalid product ID: {product_id}"
        
        # Verify all new taxonomy names are valid
        valid_taxonomy_names = {taxonomy.name for taxonomy in taxonomies}
        for new_taxonomy in aggregated_result.reassignments.values():
            assert new_taxonomy in valid_taxonomy_names, f"Invalid taxonomy name: {new_taxonomy}"
        
        # Verify no product is reassigned to its current taxonomy
        for product_id, new_taxonomy in aggregated_result.reassignments.items():
            current_taxonomy = assignments.get(product_id)
            assert new_taxonomy != current_taxonomy, f"Product {product_id} reassigned to current taxonomy"
        
        # Save aggregated results for analysis
        save_refinement_results(
            aggregated_result,
            assignments,
            taxonomies,
            product_titles,
            stage_context.product_category
        )

    @pytest.mark.asyncio
    async def test_build_prompt_with_taxonomies_and_assignments(
        self,
        refinement_stage: RefinementStage,
        sample_refinement_data: tuple[list[TaxonomyDTO], dict[int, str], list[str]],
        stage_context: StageContext
    ) -> None:
        """Verify prompt template renders correctly with taxonomies and current assignments."""
        taxonomies, assignments, product_titles = sample_refinement_data
        
        # Take a smaller sample for faster testing
        sample_size = 10
        sample_taxonomies = taxonomies[:5]  # First 5 taxonomies
        sample_assignments = {i: assignments[i] for i in range(sample_size) if i in assignments}
        sample_titles = product_titles[:sample_size]
        
        print(f"\n🔍 Testing prompt building with {len(sample_taxonomies)} taxonomies and {sample_size} products...")
        print(f"\n📋 Sample Taxonomies:")
        for i, taxonomy in enumerate(sample_taxonomies):
            print(f"  S_{i}: {taxonomy.name}")
            print(f"      {taxonomy.definition}")
        
        print(f"\n📋 Sample Product Assignments:")
        for i, title in enumerate(sample_titles):
            current_taxonomy = sample_assignments.get(i, "UNASSIGNED")
            print(f"  P_{i}: {title} → {current_taxonomy}")
        
        # Create refinement context
        refinement_context = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=sample_taxonomies,
            current_assignments=sample_assignments,
            input_texts=sample_titles
        )
        
        prompt = await refinement_stage._build_prompt(refinement_context)
        
        print(f"\n📝 Generated Refinement Prompt:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        print(f"Prompt length: {len(prompt)} characters")
        
        # Verify key elements from taxonomy_refinement_prompt_v0.txt are present
        assert "product taxonomy refinement specialist" in prompt.lower()
        assert "SUBCATEGORIES" in prompt
        assert "PRODUCTS" in prompt
        assert "CRITICAL RULES" in prompt
        assert "REQUIRED OUTPUT FORMAT" in prompt
        
        # Verify taxonomies are included with S_* IDs
        for i in range(len(sample_taxonomies)):
            assert f"S_{i}:" in prompt
        
        # Verify products are included with P_* IDs and current assignments
        for i in range(sample_size):
            assert f"P_{i}:" in prompt
            if i in sample_assignments:
                assert f"→" in prompt  # Assignment arrow should be present
        
        print(f"\n✅ Prompt validation completed successfully!")
        print(f"   - Contains all required template sections")
        print(f"   - Includes all {len(sample_taxonomies)} taxonomies with S_* IDs")
        print(f"   - Includes all {sample_size} products with P_* IDs and current assignments")

    @pytest.mark.asyncio
    async def test_validation_with_valid_response(
        self,
        refinement_stage: RefinementStage,
        stage_context: StageContext
    ) -> None:
        """Valid JSON response should pass validation without errors."""
        # Create simple test data
        taxonomies = [
            TaxonomyDTO(name="Smart Switches", definition="Smart home switches"),
            TaxonomyDTO(name="Manual Switches", definition="Traditional switches")
        ]
        assignments = {0: "Smart Switches", 1: "Manual Switches"}
        product_titles = ["Smart Switch A", "Manual Switch B"]
        
        # Create refinement context
        refinement_context = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=taxonomies,
            current_assignments=assignments,
            input_texts=product_titles
        )
        
        # Valid response with one reassignment
        valid_response = json.dumps({
            "P_0": "S_1"  # Reassign product 0 to subcategory 1
        })
        
        validation_result = refinement_stage._validate(
            valid_response, refinement_context
        )
        
        assert validation_result.ok is True
        assert sum(len(errors) for errors in validation_result.error_categories.values()) == 0
        
        # Empty response should also be valid
        empty_response = json.dumps({})
        validation_result = refinement_stage._validate(
            empty_response, refinement_context
        )
        
        assert validation_result.ok is True
        assert sum(len(errors) for errors in validation_result.error_categories.values()) == 0

    @pytest.mark.asyncio
    async def test_validation_with_invalid_response(
        self,
        refinement_stage: RefinementStage,
        stage_context: StageContext
    ) -> None:
        """Validation should categorise format / schema / completeness errors."""
        # Create simple test data
        taxonomies = [
            TaxonomyDTO(name="Smart Switches", definition="Smart home switches"),
            TaxonomyDTO(name="Manual Switches", definition="Traditional switches")
        ]
        assignments = {0: "Smart Switches", 1: "Manual Switches"}
        product_titles = ["Smart Switch A", "Manual Switch B"]
        
        # Create refinement context
        refinement_context = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=taxonomies,
            current_assignments=assignments,
            input_texts=product_titles
        )
        
        # Test invalid JSON
        invalid_json = "This is not JSON"
        result = refinement_stage._validate(invalid_json, refinement_context)
        assert result.ok is False
        assert len(result.error_categories["format_errors"]) > 0
        
        # Test invalid product ID
        invalid_product_id = json.dumps({
            "P_99": "S_0"  # Product ID doesn't exist
        })
        result = refinement_stage._validate(invalid_product_id, refinement_context)
        assert result.ok is False
        assert len(result.error_categories["completeness_errors"]) > 0
        
        # Test invalid subcategory ID
        invalid_subcategory_id = json.dumps({
            "P_0": "S_99"  # Subcategory ID doesn't exist
        })
        result = refinement_stage._validate(invalid_subcategory_id, refinement_context)
        assert result.ok is False
        assert len(result.error_categories["completeness_errors"]) > 0
        
        # Test self-assignment (product assigned to its current category)
        self_assignment = json.dumps({
            "P_0": "S_0"  # Product 0 is already in category 0 (Smart Switches)
        })
        result = refinement_stage._validate(self_assignment, refinement_context)
        assert result.ok is False
        assert len(result.error_categories["validation_errors"]) > 0

    @pytest.mark.asyncio
    async def test_retry_prompt_generation(
        self,
        refinement_stage: RefinementStage,
        stage_context: StageContext
    ) -> None:
        """Retry prompt generation – ensure error details are injected."""
        original_prompt = "Original refinement prompt content"
        
        validation_result = ValidationResult(
            ok=False,
            error_categories={
                "format_errors": ["Invalid JSON structure"],
                "validation_errors": ["Product P_0 assigned to current subcategory S_0"],
                "completeness_errors": ["Invalid product ID P_99"]
            }
        )
        
        # Create refinement context
        refinement_context = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=[TaxonomyDTO(name="Test", definition="Test taxonomy")],
            current_assignments={0: "Test"},
            input_texts=["Test product"]
        )
        
        retry_prompt = refinement_stage._retry_prompt(
            original_prompt, validation_result, refinement_context
        )
        
        # Verify original prompt is included
        assert original_prompt in retry_prompt
        
        # Verify retry template elements are present (from shared_retry_prompt_v0.txt)
        assert "RETRY REQUIRED" in retry_prompt
        assert "END RETRY INSTRUCTIONS" in retry_prompt
        
        # Verify error details are included in the retry prompt
        assert "Invalid JSON structure" in retry_prompt
        assert "Product P_0 assigned to current subcategory S_0" in retry_prompt
        assert "Invalid product ID P_99" in retry_prompt

    @pytest.mark.asyncio
    async def test_produce_result_conversion(
        self,
        refinement_stage: RefinementStage,
        stage_context: StageContext
    ) -> None:
        """_produce_result converts valid JSON → DTOs & reassignment mapping."""
        # Create test data
        taxonomies = [
            TaxonomyDTO(name="Smart Switches", definition="Smart home switches"),
            TaxonomyDTO(name="Manual Switches", definition="Traditional switches")
        ]
        assignments = {0: "Smart Switches", 1: "Manual Switches", 2: "Smart Switches"}
        product_titles = ["Smart Switch A", "Manual Switch B", "Smart Switch C"]
        
        raw_response = json.dumps({
            "P_1": "S_0",  # Move product 1 from Manual to Smart
            "P_2": "S_1"   # Move product 2 from Smart to Manual
        })
        
        # Create refinement context
        refinement_context = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=taxonomies,
            current_assignments=assignments,
            input_texts=product_titles
        )
        
        result = await refinement_stage._produce_result(
            raw_response, refinement_context, attempts=1
        )
        
        assert isinstance(result, RefinementStageResult)
        assert len(result.reassignments) == 2
        
        # Verify reassignment conversion (P_* and S_* IDs -> int indices and taxonomy names)
        assert result.reassignments[1] == "Smart Switches"  # P_1 -> S_0 (Smart Switches)
        assert result.reassignments[2] == "Manual Switches"  # P_2 -> S_1 (Manual Switches)

    @pytest.mark.asyncio
    async def test_merge_split_results(
        self,
        refinement_stage: RefinementStage,
        stage_context: StageContext
    ) -> None:
        """Merge logic: combine reassignments with proper index adjustment."""
        # Create test taxonomies
        taxonomies = [
            TaxonomyDTO(name="Smart Switches", definition="Smart switches"),
            TaxonomyDTO(name="Manual Switches", definition="Manual switches")
        ]
        
        # Create left result (products 0-1)
        left_result = RefinementStageResult(
            reassignments={0: "Manual Switches"}  # Product 0 reassigned
        )
        
        # Create right result (products 0-1 in right context, which map to 2-3 globally)
        right_result = RefinementStageResult(
            reassignments={1: "Smart Switches"}  # Product 1 in right context (global product 3)
        )
        
        # Create refinement contexts for left and right sides
        ctx_left = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=taxonomies,
            current_assignments={0: "Smart Switches", 1: "Smart Switches"},
            input_texts=["Product 0", "Product 1"]
        )
        
        ctx_right = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=taxonomies,
            current_assignments={0: "Manual Switches", 1: "Manual Switches"},  # Local indices
            input_texts=["Product 2", "Product 3"]
        )
        
        merged = await refinement_stage._merge_split_results(
            res_left=left_result,
            res_right=right_result,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        # Verify merged reassignments with proper index adjustment
        assert len(merged.reassignments) == 2
        assert merged.reassignments[0] == "Manual Switches"  # From left side
        assert merged.reassignments[3] == "Smart Switches"   # From right side (1 + left_size(2) = 3)

    @pytest.mark.asyncio
    async def test_input_validation_with_empty_assignments(
        self,
        refinement_stage: RefinementStage,
        stage_context: StageContext
    ) -> None:
        """RefinementStage should handle empty assignments gracefully."""
        taxonomies = [TaxonomyDTO(name="Test Category", definition="Test definition")]
        
        # Test with empty assignments
        empty_context = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=taxonomies,
            current_assignments={},
            input_texts=["Test product"]
        )
        
        # This should not raise an error, just generate a prompt with unassigned products
        prompt = await refinement_stage._build_prompt(empty_context)
        assert "SUBCATEGORIES:" in prompt
        assert "PRODUCTS:" in prompt
        assert "P_0:" in prompt
        assert "UNASSIGNED" in prompt

    @pytest.mark.asyncio
    async def test_no_refinement_needed(
        self,
        refinement_stage: RefinementStage,
        stage_context: StageContext
    ) -> None:
        """Test scenario where no refinement is needed (empty response)."""
        taxonomies = [
            TaxonomyDTO(name="Perfect Category", definition="Perfectly defined category")
        ]
        assignments = {0: "Perfect Category"}
        product_titles = ["Perfectly categorized product"]
        
        # Create refinement context
        refinement_context = RefinementStageContext(
            product_category=stage_context.product_category,
            taxonomies=taxonomies,
            current_assignments=assignments,
            input_texts=product_titles
        )
        
        # Empty response (no refinements needed)
        empty_response = json.dumps({})
        
        # Validation should pass
        validation_result = refinement_stage._validate(empty_response, refinement_context)
        assert validation_result.ok is True
        
        # Result production should work
        result = await refinement_stage._produce_result(
            empty_response, refinement_context, attempts=1
        )
        assert isinstance(result, RefinementStageResult)
        assert len(result.reassignments) == 0 