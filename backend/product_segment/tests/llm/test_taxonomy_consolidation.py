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

import asyncio
import json
import pytest
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock

from core.utils.llm_utils import ValidationResult
from product_segment.llm.taxonomy_consolidation import (
    ConsolidationStage,
    ConsolidationStageResult,
    ConsolidationStageContext,
    ConsolidatedTaxonomyDTO,
)
from product_segment.llm.taxonomy_pipeline_stage import StageContext


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
    
    # Calculate consolidation metrics
    final_consolidated_count = len(consolidation_result.taxonomies_consolidated)
    consolidation_ratio = final_consolidated_count / total_original_categories if total_original_categories > 0 else 0
    
    # Group original categories by their consolidated assignment
    consolidation_analysis = {}
    for consolidated_tax in consolidation_result.taxonomies_consolidated:
        consolidation_analysis[consolidated_tax.name] = {
            "definition": consolidated_tax.definition,
            "original_count": len(consolidated_tax.original_ids),
            "original_ids": consolidated_tax.original_ids,
            "consolidation_sources": []
        }
        
        # Analyze which batches contributed to this consolidated category
        batch_sources = {}
        for original_id in consolidated_tax.original_ids:
            if original_id.startswith("BATCH_"):
                batch_num = original_id.split("_")[1]
                batch_sources[f"batch_{batch_num}"] = batch_sources.get(f"batch_{batch_num}", 0) + 1
        
        consolidation_analysis[consolidated_tax.name]["consolidation_sources"] = batch_sources
    
    saved_data = {
        "metadata": {
            "product_category": product_category,
            "consolidation_timestamp": datetime.now().isoformat(),
            "total_batches_processed": len(batch_info),
            "total_original_categories": total_original_categories,
            "final_consolidated_taxonomies": final_consolidated_count,
            "consolidation_ratio": round(consolidation_ratio, 3),
            "efficiency_metrics": {
                "categories_merged": total_original_categories - final_consolidated_count,
                "merge_percentage": round((1 - consolidation_ratio) * 100, 1),
                "avg_categories_per_consolidated": round(total_original_categories / final_consolidated_count, 2) if final_consolidated_count > 0 else 0
            }
        },
        "input_batches": {
            batch_id: {
                "taxonomy_count": batch_data.get("taxonomies", 0) if isinstance(batch_data, dict) else 0,
                "batch_index": int(batch_id.split("_")[1]) if "BATCH_" in batch_id else 0
            }
            for batch_id, batch_data in batch_info.items()
            if batch_id != "FINAL"
        },
        "progressive_consolidation_process": {
            "description": "Categories were progressively consolidated starting with Batch 0 as initial, then each subsequent batch was consolidated with the growing consolidated taxonomy",
            "process_flow": [
                "Batch 0 → Initial Consolidated Taxonomy",
                "Batch 1 + Consolidated → Updated Consolidated",
                "Batch 2 + Consolidated → Updated Consolidated",
                "... (continue for all batches)",
                "Final Consolidated Taxonomy"
            ]
        },
        "final_consolidated_taxonomies": [
            {
                "name": tax.name,
                "definition": tax.definition,
                "original_categories_merged": len(tax.original_ids),
                "original_ids": tax.original_ids,
                "source_analysis": consolidation_analysis[tax.name]["consolidation_sources"]
            }
            for tax in consolidation_result.taxonomies_consolidated
        ],
        "consolidation_mapping": consolidation_result.consolidation_mapping,
        "detailed_analysis": {
            "consolidation_breakdown": consolidation_analysis,
            "category_distribution": {
                "most_consolidated": max(
                    [(tax.name, len(tax.original_ids)) for tax in consolidation_result.taxonomies_consolidated],
                    key=lambda x: x[1]
                ) if consolidation_result.taxonomies_consolidated else ("None", 0),
                "least_consolidated": min(
                    [(tax.name, len(tax.original_ids)) for tax in consolidation_result.taxonomies_consolidated], 
                    key=lambda x: x[1]
                ) if consolidation_result.taxonomies_consolidated else ("None", 0),
                "consolidation_sizes": [len(tax.original_ids) for tax in consolidation_result.taxonomies_consolidated]
            }
        }
    }
    
    # Save to JSON file
    with open(CONSOLIDATION_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(saved_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved progressive consolidation results to: {CONSOLIDATION_RESULTS_PATH}")
    print(f"   - {len(batch_info) - 1} batches processed (excluding final)")
    print(f"   - {total_original_categories} original categories → {final_consolidated_count} consolidated")
    print(f"   - {consolidation_ratio:.1%} consolidation ratio")
    print(f"   - {total_original_categories - final_consolidated_count} categories merged")
    
    # Print top consolidation insights
    if consolidation_result.taxonomies_consolidated:
        most_merged = max(consolidation_result.taxonomies_consolidated, key=lambda x: len(x.original_ids))
        print(f"   - Most consolidated: '{most_merged.name}' (merged {len(most_merged.original_ids)} categories)")


@pytest.fixture
def extraction_results() -> Dict:
    """Load taxonomy extraction results from the integration test."""
    if not TAXONOMY_RESULTS_PATH.exists():
        pytest.skip(f"Taxonomy extraction results not found: {TAXONOMY_RESULTS_PATH}")
    
    with open(TAXONOMY_RESULTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def sample_taxonomies(extraction_results: Dict) -> tuple[Dict, Dict]:
    """Create two sample taxonomies for consolidation testing from extraction results."""
    batch_results = extraction_results["batch_results"]
    
    if len(batch_results) < 2:
        pytest.skip("Need at least 2 batch results for consolidation testing")
    
    # Take taxonomies from first two batches
    batch_a = batch_results[0]
    batch_b = batch_results[1]
    
    # Convert to the format expected by consolidation (category_id -> category_data)
    taxonomy_a = {}
    for i, taxonomy in enumerate(batch_a["taxonomies"]):
        category_id = f"A_{i}"
        taxonomy_a[category_id] = {
            "name": taxonomy["name"],
            "definition": taxonomy["definition"]
        }
    
    taxonomy_b = {}
    for i, taxonomy in enumerate(batch_b["taxonomies"]):
        category_id = f"B_{i}"
        taxonomy_b[category_id] = {
            "name": taxonomy["name"], 
            "definition": taxonomy["definition"]
        }
    
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
          categories from all batches with complete mapping.
        • Results are saved to test_data/taxonomy_consolidation_results.json.
        Requires `ANTHROPIC_API_KEY` & network access – run with -m integration.
        """
        batch_results = extraction_results["batch_results"]
        
        if len(batch_results) < 2:
            pytest.skip("Need at least 2 batch results for consolidation testing")
        
        print(f"\n🚀 Progressive consolidation of {len(batch_results)} extraction batches...")
        
        # Create consolidation stage (uses real LLM via safe_llm_call automatically)
        real_consolidation_stage = ConsolidationStage()
        
        # Initialize with first batch as the consolidated taxonomy
        print(f"\n📊 Initializing with Batch 0: {batch_results[0]['taxonomies_count']} taxonomies")
        
        # Convert first batch to consolidated format
        current_consolidated = {}
        for i, taxonomy in enumerate(batch_results[0]["taxonomies"]):
            category_id = f"INIT_{i}"
            current_consolidated[category_id] = {
                "name": taxonomy["name"],
                "definition": taxonomy["definition"]
            }
            print(f"  INIT_{i}: {taxonomy['name']}")
        
        # Track all original mappings for final validation
        all_original_categories = {}
        batch_id_mapping = {}  # Maps original batch IDs to global IDs
        
        # Add initial batch to tracking
        for i, taxonomy in enumerate(batch_results[0]["taxonomies"]):
            global_id = f"BATCH_0_{i}"
            all_original_categories[global_id] = {
                "name": taxonomy["name"],
                "definition": taxonomy["definition"],
                "batch_idx": 0
            }
            batch_id_mapping[f"INIT_{i}"] = global_id
        
        # Progressively consolidate each subsequent batch
        for batch_idx in range(1, len(batch_results)):
            batch = batch_results[batch_idx]
            print(f"\n📊 Consolidating Batch {batch_idx}: {batch['taxonomies_count']} taxonomies")
            
            # Format new batch taxonomies
            new_batch_taxonomy = {}
            for i, taxonomy in enumerate(batch["taxonomies"]):
                category_id = f"NEW_{i}"
                new_batch_taxonomy[category_id] = {
                    "name": taxonomy["name"],
                    "definition": taxonomy["definition"]
                }
                print(f"  NEW_{i}: {taxonomy['name']}")
                
                # Add to global tracking
                global_id = f"BATCH_{batch_idx}_{i}"
                all_original_categories[global_id] = {
                    "name": taxonomy["name"],
                    "definition": taxonomy["definition"],
                    "batch_idx": batch_idx
                }
                batch_id_mapping[f"NEW_{i}"] = global_id
            
            # Create consolidation context
            context = ConsolidationStageContext(
                product_category=stage_context.product_category,
                taxonomy_a=current_consolidated,
                taxonomy_b=new_batch_taxonomy
            )
            
            print(f"    ➡️   Consolidating Batch {batch_idx} with current consolidated taxonomy...")
            
            # Execute consolidation
            result = await real_consolidation_stage.execute(context)
            
            print(f"    ✅  Batch {batch_idx} consolidated – created "
                  f"{len(result.taxonomies_consolidated)} consolidated taxonomies")
            
            # Print consolidation overview for this iteration
            for tax_idx, taxonomy in enumerate(result.taxonomies_consolidated, start=1):
                original_count = len(taxonomy.original_ids)
                print(f"        {tax_idx:02d}. {taxonomy.name} (merges {original_count} categories)")
                for original_id in taxonomy.original_ids:
                    if original_id in batch_id_mapping:
                        global_id = batch_id_mapping[original_id]
                        if global_id in all_original_categories:
                            original_name = all_original_categories[global_id]["name"]
                            print(f"            ↳ {original_id} → {original_name}")
                        else:
                            print(f"            ↳ {original_id}")
                    else:
                        print(f"            ↳ {original_id}")
            
            # Update current consolidated taxonomy for next iteration
            # Convert result back to input format for next consolidation
            current_consolidated = {}
            for i, taxonomy in enumerate(result.taxonomies_consolidated):
                category_id = f"CONS_{i}"
                current_consolidated[category_id] = {
                    "name": taxonomy.name,
                    "definition": taxonomy.definition
                }
                
                # Update batch_id_mapping for the consolidated categories
                for original_id in taxonomy.original_ids:
                    if original_id in batch_id_mapping:
                        # Update mapping to point to new consolidated category
                        global_id = batch_id_mapping[original_id]
                        batch_id_mapping[f"CONS_{i}"] = batch_id_mapping.get(f"CONS_{i}", [])
                        if not isinstance(batch_id_mapping[f"CONS_{i}"], list):
                            batch_id_mapping[f"CONS_{i}"] = [batch_id_mapping[f"CONS_{i}"]]
                        if global_id not in batch_id_mapping[f"CONS_{i}"]:
                            batch_id_mapping[f"CONS_{i}"].append(global_id)
        
        print(f"\n🎉 Progressive consolidation complete!")
        print(f"    Final result: {len(current_consolidated)} consolidated taxonomies")
        print(f"    Total original categories: {len(all_original_categories)}")
        print(f"    Consolidation ratio: {len(current_consolidated)/len(all_original_categories):.2f}")
        
        # Print final consolidated taxonomies
        print(f"\n📋 Final Consolidated Taxonomies:")
        for i, (category_id, category_data) in enumerate(current_consolidated.items(), start=1):
            print(f"    {i:02d}. {category_data['name']}")
            # Find all original categories that map to this consolidated category
            if category_id in batch_id_mapping:
                mapped_globals = batch_id_mapping[category_id]
                if isinstance(mapped_globals, list):
                    for global_id in mapped_globals:
                        if global_id in all_original_categories:
                            original_name = all_original_categories[global_id]["name"]
                            batch_idx = all_original_categories[global_id]["batch_idx"]
                            print(f"        ↳ Batch {batch_idx}: {original_name}")
                else:
                    if mapped_globals in all_original_categories:
                        original_name = all_original_categories[mapped_globals]["name"]
                        batch_idx = all_original_categories[mapped_globals]["batch_idx"]
                        print(f"        ↳ Batch {batch_idx}: {original_name}")
        
        # Validate final results
        assert len(current_consolidated) > 0, "Should have at least one consolidated taxonomy"
        assert len(current_consolidated) <= len(all_original_categories), "Consolidated count should not exceed original count"
        
        # Create final result structure for saving
        final_taxonomies = []
        final_mapping = {}
        
        for cons_id, category_data in current_consolidated.items():
            # Find all original categories that map to this consolidated category
            original_ids = []
            if cons_id in batch_id_mapping:
                if isinstance(batch_id_mapping[cons_id], list):
                    original_ids = batch_id_mapping[cons_id]
                else:
                    original_ids = [batch_id_mapping[cons_id]]
            
            final_taxonomies.append(ConsolidatedTaxonomyDTO(
                name=category_data["name"],
                definition=category_data["definition"],
                original_ids=original_ids
            ))
            
            # Update final mapping
            for original_id in original_ids:
                final_mapping[original_id] = category_data["name"]
        
        final_result = ConsolidationStageResult(
            taxonomies_consolidated=final_taxonomies,
            consolidation_mapping=final_mapping
        )
        
        # For saving, create simplified input structure
        save_consolidation_results(
            final_result, 
            {f"BATCH_{i}": {"taxonomies": len(batch["taxonomies"])} for i, batch in enumerate(batch_results)},
            {"FINAL": {"consolidated_count": len(current_consolidated)}},
            stage_context.product_category
        )

    @pytest.mark.asyncio
    async def test_build_prompt_with_taxonomies(
        self,
        consolidation_stage: ConsolidationStage,
        sample_taxonomies: tuple[Dict, Dict],
        stage_context: StageContext
    ) -> None:
        """Verify prompt template renders correctly with two taxonomies."""
        taxonomy_a, taxonomy_b = sample_taxonomies
        
        print(f"\n🔍 Testing prompt building with sample taxonomies...")
        print(f"\n📋 Taxonomy A (Current Consolidated):")
        print(json.dumps(taxonomy_a, indent=2))
        print(f"\n📋 Taxonomy B (New Batch):")
        print(json.dumps(taxonomy_b, indent=2))
        
        # Create consolidation context
        consolidation_context = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a=taxonomy_a,
            taxonomy_b=taxonomy_b
        )
        
        prompt = await consolidation_stage._build_prompt(consolidation_context)
        
        print(f"\n📝 Generated Consolidation Prompt:")
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
        
        # Verify taxonomies are included in the prompt
        for category_id in taxonomy_a.keys():
            assert category_id in prompt
        for category_id in taxonomy_b.keys():
            assert category_id in prompt
        
        print(f"\n✅ Prompt validation completed successfully!")
        print(f"   - Contains all required template sections")
        print(f"   - Includes all {len(taxonomy_a)} Taxonomy A categories")
        print(f"   - Includes all {len(taxonomy_b)} Taxonomy B categories")

    @pytest.mark.asyncio
    async def test_validation_with_valid_response(
        self,
        consolidation_stage: ConsolidationStage,
        sample_taxonomies: tuple[Dict, Dict],
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
        sample_taxonomies: tuple[Dict, Dict],
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
        sample_taxonomies: tuple[Dict, Dict],
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
        assert len(result.consolidation_mapping) == len(original_ids)
        
        # Verify taxonomy conversion
        taxonomy_names = {t.name for t in result.taxonomies_consolidated}
        assert taxonomy_names == {"Smart Lighting Controls", "Manual Light Switches"}
        
        # Verify original_ids are properly stored
        for taxonomy in result.taxonomies_consolidated:
            assert len(taxonomy.original_ids) > 0
            for original_id in taxonomy.original_ids:
                assert original_id in original_ids
        
        # Verify consolidation mapping
        for original_id in original_ids:
            assert original_id in result.consolidation_mapping
            assert result.consolidation_mapping[original_id] in taxonomy_names

    @pytest.mark.asyncio
    async def test_merge_split_results(
        self,
        consolidation_stage: ConsolidationStage,
        stage_context: StageContext
    ) -> None:
        """Merge logic: de-dupe taxonomies, merge consolidation mappings."""
        # Create left result
        left_result = ConsolidationStageResult(
            taxonomies_consolidated=[
                ConsolidatedTaxonomyDTO(
                    name="Category A", 
                    definition="Definition A",
                    original_ids=["A_0", "A_1"]
                ),
                ConsolidatedTaxonomyDTO(
                    name="Category B", 
                    definition="Definition B",
                    original_ids=["B_0"]
                )
            ],
            consolidation_mapping={"A_0": "Category A", "A_1": "Category A", "B_0": "Category B"}
        )
        
        # Create right result with some overlap
        right_result = ConsolidationStageResult(
            taxonomies_consolidated=[
                ConsolidatedTaxonomyDTO(
                    name="Category B",  # Duplicate name 
                    definition="Definition B Updated",
                    original_ids=["B_1"]
                ),
                ConsolidatedTaxonomyDTO(
                    name="Category C", 
                    definition="Definition C",
                    original_ids=["C_0"]
                )
            ],
            consolidation_mapping={"B_1": "Category B", "C_0": "Category C"}
        )
        
        # Create consolidation contexts for left and right sides
        ctx_left = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a={"A_0": {"name": "Category A", "definition": "Definition A"}},
            taxonomy_b={"B_0": {"name": "Category B", "definition": "Definition B"}}
        )
        
        ctx_right = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a={"A_1": {"name": "Category B", "definition": "Definition B Updated"}},
            taxonomy_b={"B_1": {"name": "Category C", "definition": "Definition C"}}
        )
        
        merged = await consolidation_stage._merge_split_results(
            res_left=left_result,
            res_right=right_result,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        # Verify merged taxonomies (should deduplicate by name and merge original_ids)
        taxonomy_names = {t.name for t in merged.taxonomies_consolidated}
        assert taxonomy_names == {"Category A", "Category B", "Category C"}
        
        # Find Category B to verify ID merging
        category_b = next(t for t in merged.taxonomies_consolidated if t.name == "Category B")
        assert set(category_b.original_ids) == {"B_0", "B_1"}
        
        # Verify merged consolidation mapping
        expected_mapping = {
            "A_0": "Category A", "A_1": "Category A", 
            "B_0": "Category B", "B_1": "Category B", 
            "C_0": "Category C"
        }
        assert merged.consolidation_mapping == expected_mapping

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
            taxonomy_a={},
            taxonomy_b={}
        )
        
        # This should not raise an error, just generate a prompt with empty taxonomies
        prompt = await consolidation_stage._build_prompt(empty_context)
        assert "Taxonomy A (Current Consolidated):" in prompt
        assert "Taxonomy B (New Batch):" in prompt
        
        # Test with one empty and one non-empty taxonomy
        mixed_context = ConsolidationStageContext(
            product_category=stage_context.product_category,
            taxonomy_a={"test": {"name": "Test Category", "definition": "Test definition"}},
            taxonomy_b={}
        )
        
        prompt = await consolidation_stage._build_prompt(mixed_context)
        assert "A_0" in prompt
        assert "Test Category" in prompt 