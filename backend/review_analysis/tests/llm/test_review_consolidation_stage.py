"""Tests for review analysis consolidation stage.

This module tests the consolidation stage with sample extraction results
and includes real LLM integration testing for comprehensive workflow validation.

Test Coverage:
--------------

1. **test_template_loading**: Tests prompt template loading functionality
2. **test_additional_template_vars**: Tests review-specific template variables
3. **test_build_prompt**: Tests prompt building with A_*/B_* taxonomy formatting
4. **test_validation_***: Tests validation logic with various response formats
5. **test_produce_result**: Tests result production from valid LLM responses
6. **test_real_llm_consolidation**: Real LLM integration test with orchestration
7. **test_orchestration_workflow**: End-to-end workflow similar to product_segment service

Configuration:
--------------
- Uses extraction results from test_data/sample_extraction_results.json
- Aspect types: physical, performance, use case
- Real LLM calls for integration testing
"""

import pytest
from unittest.mock import patch
import json
from pathlib import Path
from typing import Dict, Any

from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO
from core.llm_taxonomy_pipeline.consolidation_base import ConsolidationStageContext, ConsolidationStageResult, ConsolidatedTaxonomyDTO
from core.utils.batching import make_batches
from review_analysis.llm.review_consolidation_stage import ReviewConsolidationStage

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"
CATEGORIZATION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_categorization_results.json"
CONSOLIDATION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_consolidation_results.json"
PRODUCT_CATEGORY = "Kids Art and Craft Tool"


class TestReviewConsolidationStage:
    """Test consolidation stage functionality."""

    @pytest.fixture
    def stage(self):
        """Create consolidation stage with test context."""
        return ReviewConsolidationStage(
            aspect_type="physical",
            product_categories={"Electronics", "Home & Garden"}
        )

    @pytest.fixture
    def categorization_results(self) -> Dict[str, Any]:
        """Load real categorization results for consolidation testing."""
        if not CATEGORIZATION_RESULTS_PATH.exists():
            pytest.skip(f"Categorization results not found: {CATEGORIZATION_RESULTS_PATH}")
        
        with open(CATEGORIZATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    @pytest.fixture
    def sample_context(self):
        """Create sample consolidation context."""
        taxonomy_a = [
            TaxonomyDTO(name="Color", definition="Product color aspects"),
            TaxonomyDTO(name="Size", definition="Product size aspects")
        ]
        taxonomy_b = [
            TaxonomyDTO(name="Material", definition="Product material aspects"),
            TaxonomyDTO(name="Weight", definition="Product weight aspects")
        ]
        return ConsolidationStageContext(
            product_category="test_category",
            taxonomy_a=taxonomy_a, 
            taxonomy_b=taxonomy_b
        )

    @pytest.mark.asyncio
    async def test_prompt_templates_and_build(self, stage, sample_context):
        """Combined test for template loading, additional vars, and prompt building."""

        # ------------------------------------------------------------------
        # 1. Template loading assertions
        # ------------------------------------------------------------------
        print("\n🔍 [1/3] Testing template loading functionality (real templates)")

        assert stage._consolidate_prompt_template, (
            "Consolidate prompt template should not be empty"
        )
        assert "{{taxonomy_a}}" in stage._consolidate_prompt_template
        assert "{{taxonomy_b}}" in stage._consolidate_prompt_template
        assert "{{aspect_definition}}" in stage._consolidate_prompt_template

        assert stage._retry_prompt_template, (
            "Retry prompt template should not be empty"
        )
        assert "{error_details}" in stage._retry_prompt_template
        print("✅ Template loading validated")

        # ------------------------------------------------------------------
        # 2. Additional template variables assertions
        # ------------------------------------------------------------------
        print("\n🔍 [2/3] Testing additional template variables")
        vars = stage._get_additional_template_vars(sample_context)

        print("📋 Template variables:")
        for k, v in vars.items():
            preview = v if len(v) < 120 else v[:117] + "..."
            print(f"   - {k}: {preview}")

        assert vars["aspect_type"] == "physical"
        assert "Electronics" in vars["product_context"]
        assert "Home & Garden" in vars["product_context"]
        assert vars.get("aspect_definition"), "aspect_definition should not be empty"
        print("✅ Additional template variables validated")

        # ------------------------------------------------------------------
        # 3. Prompt building assertions
        # ------------------------------------------------------------------
        print("\n🔍 [3/3] Testing prompt building with A_*/B_* taxonomy formatting")

        prompt = await stage._build_prompt(sample_context)

        print("=" * 40 + " GENERATED PROMPT " + "=" * 40)
        print(prompt)
        print("=" * 100)

        # Check for IDs and expected content in the prompt
        assert "A_0" in prompt
        assert "A_1" in prompt
        assert "B_0" in prompt
        assert "B_1" in prompt
        assert "Color" in prompt
        assert "physical" in prompt
        assert "Components or inherent physical properties" in prompt
        print("✅ Prompt built and validated successfully")

    def test_validation_success(self, stage, sample_context):
        """Test successful validation."""
        print("\n🔍 Testing successful validation")
        valid_response = '''
        {
            "Appearance": {
                "definition": "Visual aspects",
                "ids": ["A_0", "B_0"]
            },
            "Physical Properties": {
                "definition": "Physical characteristics", 
                "ids": ["A_1", "B_1"]
            }
        }
        '''
        
        result = stage._validate(valid_response, sample_context)
        print(f"📊 Validation result: {result.ok}")
        print(f"📋 Error categories: {result.error_categories}")
        assert result.ok == True
        assert len(result.error_categories["format_errors"]) == 0
        print("✅ Successful validation test passed")

    def test_validation_missing_ids(self, stage, sample_context):
        """Test validation with missing IDs."""
        print("\n🔍 Testing validation with missing IDs")
        invalid_response = '''
        {
            "Appearance": {
                "definition": "Visual aspects",
                "ids": ["A_0"]
            }
        }
        '''
        
        result = stage._validate(invalid_response, sample_context)
        print(f"📊 Validation result: {result.ok}")
        print(f"📋 Error categories: {result.error_categories}")
        assert result.ok == False
        assert any("Missing assignments" in error 
                  for error in result.error_categories["completeness_errors"])
        print("✅ Missing IDs validation test passed")

    def test_validation_duplicate_ids(self, stage, sample_context):
        """Test validation with duplicate IDs."""
        invalid_response = '''
        {
            "Category1": {
                "definition": "Test",
                "ids": ["A_0", "A_1"]
            },
            "Category2": {
                "definition": "Test", 
                "ids": ["A_0", "B_0", "B_1"]
            }
        }
        '''
        
        result = stage._validate(invalid_response, sample_context)
        assert result.ok == False
        assert any("appears in multiple categories" in error
                  for error in result.error_categories["completeness_errors"])

    @pytest.mark.asyncio
    async def test_produce_result(self, stage, sample_context):
        """Test result production."""
        print("\n🔍 Testing result production")
        valid_response = '''
        {
            "Appearance": {
                "definition": "Visual aspects", 
                "ids": ["A_0", "B_0"]
            },
            "Physical Properties": {
                "definition": "Physical characteristics",
                "ids": ["A_1", "B_1"] 
            }
        }
        '''
        
        with patch('core.utils.llm_utils.extract_json', return_value=valid_response.strip()):
            result = await stage._produce_result(valid_response, sample_context, 1)
            
            print("📊 Result produced:")
            print(f"   - Consolidated taxonomies: {len(result.taxonomies_consolidated)}")
            for i, tax in enumerate(result.taxonomies_consolidated):
                print(f"   - [{i}] {tax.taxonomy.name}: {len(tax.original_taxonomies)} original taxonomies")
            
            assert len(result.taxonomies_consolidated) == 2
            assert result.taxonomies_consolidated[0].taxonomy.name == "Appearance"
            assert len(result.taxonomies_consolidated[0].original_taxonomies) == 2
            print("✅ Result production test passed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_llm_progressive_consolidation(
        self,
        categorization_results: Dict[str, Any]
    ) -> None:
        """Real LLM consolidation test using categorized review aspects."""
        
        print("\n" + "="*80)
        print("🤖 REAL LLM PROGRESSIVE CONSOLIDATION WITH CATEGORIZATION DATA")
        print("="*80)

        results_by_aspect = categorization_results.get("categorization_results", {})
        final_consolidation_results = {}

        for aspect_type, data in results_by_aspect.items():
            print(f"\n--- Processing aspect type: {aspect_type.upper()} ---")
            
            all_taxonomies = [TaxonomyDTO(name=t['name'], definition=t['definition']) for t in data.get("taxonomies", [])]
            
            if len(all_taxonomies) < 2:
                print(f"Skipping consolidation for '{aspect_type}': needs at least 2 taxonomies, found {len(all_taxonomies)}")
                continue

            batches = make_batches(all_taxonomies, 5)
            if len(batches) < 2:
                print(f"Skipping consolidation for '{aspect_type}': needs at least 2 batches to consolidate, found {len(batches)}")
                continue

            print(f"Consolidating {len(all_taxonomies)} taxonomies in {len(batches)} batches.")

            stage = ReviewConsolidationStage(
                aspect_type=aspect_type,
                product_categories={categorization_results.get("metadata", {}).get("product_category", PRODUCT_CATEGORY)}
            )
            
            # Start with the first batch as the initial consolidated set
            initial_batch = batches[0]
            progressive_result = ConsolidationStageResult(
                taxonomies_consolidated=[ConsolidatedTaxonomyDTO(taxonomy=t, original_taxonomies=[t]) for t in initial_batch]
            )

            # Iteratively consolidate remaining batches
            for i, next_batch in enumerate(batches[1:], start=1):
                print(f"  Consolidating with batch {i+1}/{len(batches)}...")
                context = ConsolidationStageContext(
                    product_category=categorization_results.get("metadata", {}).get("product_category", PRODUCT_CATEGORY),
                    taxonomy_a=[r.taxonomy for r in progressive_result.taxonomies_consolidated],
                    taxonomy_b=next_batch
                )
                print(f"    -> Input A ({len(context.taxonomy_a)}): {[t.name for t in context.taxonomy_a]}")
                print(f"    -> Input B ({len(context.taxonomy_b)}): {[t.name for t in context.taxonomy_b]}")
                progressive_result = await stage.execute(context)

            print(f"📊 CONSOLIDATION COMPLETE for '{aspect_type}':")
            print(f"   - Input: {len(all_taxonomies)} taxonomies")
            print(f"   - Output: {len(progressive_result.taxonomies_consolidated)} consolidated taxonomies")

            for i, consolidated_item in enumerate(progressive_result.taxonomies_consolidated):
                print(f"    - Consolidated Taxonomy #{i+1}: {consolidated_item.taxonomy.name}")
                print(f"      Definition: {consolidated_item.taxonomy.definition}")
                original_names = [t.name for t in consolidated_item.original_taxonomies]
                print(f"      Merged ({len(original_names)}): {original_names}")

            final_consolidation_results[aspect_type] = progressive_result

            total_originals = sum(len(cons.original_taxonomies) for cons in progressive_result.taxonomies_consolidated)
            assert total_originals == len(all_taxonomies), f"Mismatch in original taxonomy count for {aspect_type}"

        # Save results for inspection
        with open(CONSOLIDATION_RESULTS_PATH, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": categorization_results.get("metadata"),
                "consolidation_results": {
                    aspect: {
                        "consolidated_count": len(res.taxonomies_consolidated),
                        "taxonomies": [
                            {
                                "name": t.taxonomy.name, 
                                "definition": t.taxonomy.definition,
                                "merged_count": len(t.original_taxonomies),
                                "original_names": [ot.name for ot in t.original_taxonomies]
                            } for t in res.taxonomies_consolidated
                        ]
                    } for aspect, res in final_consolidation_results.items()
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved progressive consolidation results to: {CONSOLIDATION_RESULTS_PATH}")
        assert final_consolidation_results, "Consolidation should have produced results for at least one aspect type."
        print("\n✅ Progressive consolidation test completed successfully.")

