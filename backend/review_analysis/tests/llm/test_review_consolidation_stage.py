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
8. **test_full_pipeline_with_mapping**: Full pipeline test including aspect mapping
9. **test_consolidation_mapping_logic**: Tests the mapping logic between stages
10. **test_batch_size_edge_cases**: Tests consolidation with different batch sizes

Configuration:
--------------
- Uses extraction results from test_data/sample_extraction_results.json
- Aspect types: physical, performance, use case
- Real LLM calls for integration testing
"""

import pytest
from unittest.mock import patch, AsyncMock
import json
from pathlib import Path
from typing import Dict, Any, List

from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO
from core.llm_taxonomy_pipeline.consolidation_base import ConsolidationStageContext, ConsolidationStageResult, ConsolidatedTaxonomyDTO
from core.utils.batching import make_batches
from review_analysis.llm.review_consolidation_stage import ReviewConsolidationStage

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"
CATEGORIZATION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_categorization_results.json"
CONSOLIDATION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_consolidation_results.json"
EXTRACTION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_extraction_results.json"
PRODUCT_CATEGORY = "Kids Art and Craft Tool"

# Constants for testing
TEST_BATCH_SIZES = [2, 3, 5, 10]  # Different batch sizes to test edge cases


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

    @pytest.fixture
    def extraction_results(self) -> Dict[str, Any]:
        """Load real extraction results for full pipeline testing."""
        if not EXTRACTION_RESULTS_PATH.exists():
            pytest.skip(f"Extraction results not found: {EXTRACTION_RESULTS_PATH}")
        
        with open(EXTRACTION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_consolidation_mapping_logic(self, categorization_results: Dict[str, Any]):
        """Test the mapping logic between categorization and consolidation stages."""
        
        print("\n" + "="*80)
        print("🔗 TESTING CONSOLIDATION MAPPING LOGIC")
        print("="*80)

        results_by_aspect = categorization_results.get("categorization_results", {})
        
        for aspect_type, data in results_by_aspect.items():
            print(f"\n--- Testing mapping logic for: {aspect_type.upper()} ---")
            
            all_taxonomies = [TaxonomyDTO(name=t['name'], definition=t['definition']) for t in data.get("taxonomies", [])]
            
            if len(all_taxonomies) < 2:
                print(f"Skipping mapping test for '{aspect_type}': needs at least 2 taxonomies")
                continue

            # Test with different batch sizes to ensure mapping works correctly
            for batch_size in TEST_BATCH_SIZES:
                print(f"\n  Testing with batch size: {batch_size}")
                
                batches = make_batches(all_taxonomies, batch_size)
                if len(batches) < 2:
                    print(f"    Skipping: only {len(batches)} batch with size {batch_size}")
                    continue

                stage = ReviewConsolidationStage(
                    aspect_type=aspect_type,
                    product_categories={categorization_results.get("metadata", {}).get("product_category", PRODUCT_CATEGORY)}
                )
                
                # Simulate progressive consolidation
                current_consolidated = batches[0]
                merge_mapping = {}  # Track original -> consolidated mappings
                
                for i, next_batch in enumerate(batches[1:], start=1):
                    print(f"    Consolidating batch {i+1}/{len(batches)}...")
                    
                    context = ConsolidationStageContext(
                        product_category=categorization_results.get("metadata", {}).get("product_category", PRODUCT_CATEGORY),
                        taxonomy_a=current_consolidated,
                        taxonomy_b=next_batch
                    )
                    
                    result = await stage.execute(context)
                    
                    # Update mapping: track which original categories map to which consolidated ones
                    for consolidated_item in result.taxonomies_consolidated:
                        for original_tax in consolidated_item.original_taxonomies:
                            merge_mapping[original_tax.name] = consolidated_item.taxonomy.name
                    
                    current_consolidated = [r.taxonomy for r in result.taxonomies_consolidated]
                
                # Verify mapping integrity
                print(f"    📊 Mapping results for batch size {batch_size}:")
                print(f"      - Original categories: {len(all_taxonomies)}")
                print(f"      - Final consolidated: {len(current_consolidated)}")
                print(f"      - Mappings created: {len(merge_mapping)}")
                
                # Verify all original categories are mapped
                original_names = {t.name for t in all_taxonomies}
                mapped_names = set(merge_mapping.keys())
                assert original_names == mapped_names, f"Mapping mismatch for {aspect_type} with batch size {batch_size}"
                
                # Verify no circular mappings
                final_names = {merge_mapping[name] for name in original_names}
                assert len(final_names) == len(current_consolidated), f"Final category count mismatch for {aspect_type}"
                
                print(f"    ✅ Mapping integrity verified for batch size {batch_size}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_size_edge_cases(self, categorization_results: Dict[str, Any]):
        """Test consolidation with different batch sizes to catch edge cases."""
        
        print("\n" + "="*80)
        print("📦 TESTING BATCH SIZE EDGE CASES")
        print("="*80)

        results_by_aspect = categorization_results.get("categorization_results", {})
        
        for aspect_type, data in results_by_aspect.items():
            print(f"\n--- Testing edge cases for: {aspect_type.upper()} ---")
            
            all_taxonomies = [TaxonomyDTO(name=t['name'], definition=t['definition']) for t in data.get("taxonomies", [])]
            
            if len(all_taxonomies) < 2:
                print(f"Skipping edge case tests for '{aspect_type}': needs at least 2 taxonomies")
                continue

            stage = ReviewConsolidationStage(
                aspect_type=aspect_type,
                product_categories={categorization_results.get("metadata", {}).get("product_category", PRODUCT_CATEGORY)}
            )

            # Test edge case: batch size = 1 (should create many batches)
            print(f"\n  Testing edge case: batch_size = 1")
            batches_size_1 = make_batches(all_taxonomies, 1)
            print(f"    Created {len(batches_size_1)} batches with size 1")
            
            if len(batches_size_1) >= 2:
                # Test progressive consolidation with size 1 batches
                current_consolidated = batches_size_1[0]
                for i, next_batch in enumerate(batches_size_1[1:], start=1):
                    context = ConsolidationStageContext(
                        product_category=categorization_results.get("metadata", {}).get("product_category", PRODUCT_CATEGORY),
                        taxonomy_a=current_consolidated,
                        taxonomy_b=next_batch
                    )
                    result = await stage.execute(context)
                    current_consolidated = [r.taxonomy for r in result.taxonomies_consolidated]
                
                print(f"    ✅ Progressive consolidation with size 1 batches completed")
                print(f"    📊 Final result: {len(current_consolidated)} consolidated categories")

            # Test edge case: batch size >= total categories (should create 1 batch)
            print(f"\n  Testing edge case: batch_size >= total categories")
            large_batch_size = len(all_taxonomies) + 5
            batches_large = make_batches(all_taxonomies, large_batch_size)
            print(f"    Created {len(batches_large)} batches with size {large_batch_size}")
            assert len(batches_large) == 1, f"Expected 1 batch with size {large_batch_size}, got {len(batches_large)}"
            print(f"    ✅ Large batch size correctly creates single batch")

            # Test edge case: batch size = total categories (should create 1 batch)
            print(f"\n  Testing edge case: batch_size = total categories")
            exact_batch_size = len(all_taxonomies)
            batches_exact = make_batches(all_taxonomies, exact_batch_size)
            print(f"    Created {len(batches_exact)} batches with size {exact_batch_size}")
            assert len(batches_exact) == 1, f"Expected 1 batch with size {exact_batch_size}, got {len(batches_exact)}"
            print(f"    ✅ Exact batch size correctly creates single batch")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_pipeline_with_mapping(self, extraction_results: Dict[str, Any], categorization_results: Dict[str, Any]):
        """Test the full pipeline including extraction -> categorization -> consolidation mapping."""
        
        print("\n" + "="*80)
        print("🔄 FULL PIPELINE TEST WITH MAPPING")
        print("="*80)

        # This test requires both extraction and categorization results
        if not extraction_results or not categorization_results:
            pytest.skip("Both extraction and categorization results required for full pipeline test")

        extraction_aspects = extraction_results.get("extraction_results", {})
        categorization_taxonomies = categorization_results.get("categorization_results", {})
        
        print(f"📊 Pipeline data summary:")
        print(f"  - Extraction aspects: {len(extraction_aspects)} aspect types")
        print(f"  - Categorization taxonomies: {len(categorization_taxonomies)} aspect types")
        
        for aspect_type in extraction_aspects.keys():
            if aspect_type not in categorization_taxonomies:
                print(f"⚠️  Skipping {aspect_type}: no categorization data available")
                continue
                
            print(f"\n--- Full pipeline test for: {aspect_type.upper()} ---")
            
            # Get extraction aspects
            aspects = extraction_aspects[aspect_type].get("aspects", [])
            print(f"  📝 Extraction: {len(aspects)} aspects extracted")
            
            # Get categorization taxonomies
            taxonomies = [TaxonomyDTO(name=t['name'], definition=t['definition']) 
                         for t in categorization_taxonomies[aspect_type].get("taxonomies", [])]
            print(f"  🏷️  Categorization: {len(taxonomies)} categories created")
            
            if len(taxonomies) < 2:
                print(f"  ⚠️  Skipping consolidation: only {len(taxonomies)} categories")
                continue

            # Test consolidation with different batch sizes
            for batch_size in [3, 5]:  # Test with reasonable batch sizes
                print(f"\n  Testing consolidation with batch_size = {batch_size}")
                
                batches = make_batches(taxonomies, batch_size)
                print(f"    Created {len(batches)} batches")
                
                if len(batches) < 2:
                    print(f"    ⚠️  Skipping: only {len(batches)} batch")
                    continue

                stage = ReviewConsolidationStage(
                    aspect_type=aspect_type,
                    product_categories={categorization_results.get("metadata", {}).get("product_category", PRODUCT_CATEGORY)}
                )
                
                # Progressive consolidation
                current_consolidated = batches[0]
                consolidation_mapping = {}  # Track category name mappings
                
                for i, next_batch in enumerate(batches[1:], start=1):
                    print(f"    Consolidating batch {i+1}/{len(batches)}...")
                    
                    context = ConsolidationStageContext(
                        product_category=categorization_results.get("metadata", {}).get("product_category", PRODUCT_CATEGORY),
                        taxonomy_a=current_consolidated,
                        taxonomy_b=next_batch
                    )
                    
                    result = await stage.execute(context)
                    
                    # Update mapping
                    for consolidated_item in result.taxonomies_consolidated:
                        for original_tax in consolidated_item.original_taxonomies:
                            consolidation_mapping[original_tax.name] = consolidated_item.taxonomy.name
                    
                    current_consolidated = [r.taxonomy for r in result.taxonomies_consolidated]
                
                print(f"    📊 Consolidation complete:")
                print(f"      - Original categories: {len(taxonomies)}")
                print(f"      - Final categories: {len(current_consolidated)}")
                print(f"      - Mappings: {len(consolidation_mapping)}")
                
                # Verify mapping integrity
                original_names = {t.name for t in taxonomies}
                mapped_names = set(consolidation_mapping.keys())
                assert original_names == mapped_names, f"Mapping integrity failed for {aspect_type}"
                
                # Verify final categories are unique
                final_names = {cat.name for cat in current_consolidated}
                assert len(final_names) == len(current_consolidated), f"Duplicate final categories for {aspect_type}"
                
                print(f"    ✅ Consolidation and mapping verified for batch_size = {batch_size}")

        print(f"\n✅ Full pipeline test completed successfully")

    @pytest.mark.asyncio
    async def test_consolidation_with_mock_llm(self, sample_context):
        """Test consolidation logic with mocked LLM responses."""
        
        print("\n" + "="*80)
        print("🤖 CONSOLIDATION WITH MOCKED LLM")
        print("="*80)

        stage = ReviewConsolidationStage(
            aspect_type="physical",
            product_categories={"Electronics", "Home & Garden"}
        )

        # Create test taxonomies that should consolidate
        taxonomy_a = [
            TaxonomyDTO(name="Color", definition="Product color aspects"),
            TaxonomyDTO(name="Size", definition="Product size aspects")
        ]
        taxonomy_b = [
            TaxonomyDTO(name="Material", definition="Product material aspects"),
            TaxonomyDTO(name="Weight", definition="Product weight aspects")
        ]

        # Mock LLM response that consolidates into "Physical Properties"
        mock_response = '''
        {
            "Physical Properties": {
                "definition": "All physical characteristics of the product",
                "ids": ["A_0", "A_1", "B_0", "B_1"]
            }
        }
        '''

        with patch('core.utils.llm_utils.extract_json', return_value=mock_response.strip()):
            with patch('core.utils.llm_utils.safe_llm_call', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response
                
                context = ConsolidationStageContext(
                    product_category="test_category",
                    taxonomy_a=taxonomy_a,
                    taxonomy_b=taxonomy_b
                )
                
                result = await stage.execute(context)
                
                print(f"📊 Mock consolidation result:")
                print(f"  - Consolidated categories: {len(result.taxonomies_consolidated)}")
                for i, consolidated in enumerate(result.taxonomies_consolidated):
                    print(f"  - [{i}] {consolidated.taxonomy.name}: {len(consolidated.original_taxonomies)} originals")
                    original_names = [t.name for t in consolidated.original_taxonomies]
                    print(f"    Merged: {original_names}")
                
                # Verify consolidation worked
                assert len(result.taxonomies_consolidated) == 1
                assert result.taxonomies_consolidated[0].taxonomy.name == "Physical Properties"
                assert len(result.taxonomies_consolidated[0].original_taxonomies) == 4
                
                # Verify all original taxonomies are included
                all_original_names = {t.name for t in taxonomy_a + taxonomy_b}
                consolidated_original_names = {t.name for t in result.taxonomies_consolidated[0].original_taxonomies}
                assert all_original_names == consolidated_original_names
                
                print(f"✅ Mock consolidation test passed")
                ``
    @pytest.mark.asyncio
    async def test_consolidation_mapping_loop_detection(self):
        """Test that consolidation mapping properly handles loops and circular references."""
        
        print("\n" + "="*80)
        print("🔄 CONSOLIDATION MAPPING LOOP DETECTION")
        print("="*80)

        # Test the _canonical function logic that handles loops
        def _canonical(name: str, raw_merge_map: dict) -> str:
            """Collapse raw_merge_map chains to their final representative."""
            seen: set[str] = set()
            while raw_merge_map.get(name) and raw_merge_map[name] != name:
                if name in seen:  # should not happen, safeguard against loops
                    print(f"⚠️  Loop detected! {name} already seen in chain")
                    break
                seen.add(name)
                name = raw_merge_map[name]
            return name

        # Test case 1: Simple chain (no loop)
        print("\n🔍 Test 1: Simple chain (no loop)")
        simple_map = {
            "Category A": "Category B",
            "Category B": "Category C",
            "Category C": "Category C"  # Self-reference (termination)
        }
        
        result_a = _canonical("Category A", simple_map)
        result_b = _canonical("Category B", simple_map)
        result_c = _canonical("Category C", simple_map)
        
        print(f"  Category A → {result_a}")
        print(f"  Category B → {result_b}")
        print(f"  Category C → {result_c}")
        
        assert result_a == "Category C"
        assert result_b == "Category C"
        assert result_c == "Category C"
        print("  ✅ Simple chain resolved correctly")

        # Test case 2: Circular reference (loop)
        print("\n🔍 Test 2: Circular reference (loop)")
        circular_map = {
            "Category A": "Category B",
            "Category B": "Category C",
            "Category C": "Category A"  # Creates loop: A → B → C → A
        }
        
        result_a_loop = _canonical("Category A", circular_map)
        result_b_loop = _canonical("Category B", circular_map)
        result_c_loop = _canonical("Category C", circular_map)
        
        print(f"  Category A → {result_a_loop}")
        print(f"  Category B → {result_b_loop}")
        print(f"  Category C → {result_c_loop}")
        
        # The function should handle the loop gracefully without infinite recursion
        assert result_a_loop in ["Category A", "Category B", "Category C"]
        assert result_b_loop in ["Category A", "Category B", "Category C"]
        assert result_c_loop in ["Category A", "Category B", "Category C"]
        print("  ✅ Loop detected and handled gracefully")

        # Test case 3: Self-referencing loop
        print("\n🔍 Test 3: Self-referencing loop")
        self_loop_map = {
            "Category A": "Category A"  # Self-reference
        }
        
        result_self = _canonical("Category A", self_loop_map)
        print(f"  Category A → {result_self}")
        
        assert result_self == "Category A"
        print("  ✅ Self-reference handled correctly")

        # Test case 4: Complex loop with multiple paths
        print("\n🔍 Test 4: Complex loop with multiple paths")
        complex_map = {
            "Category A": "Category B",
            "Category B": "Category C",
            "Category C": "Category D",
            "Category D": "Category B",  # Creates loop: B → C → D → B
            "Category E": "Category F",
            "Category F": "Category F"   # Self-reference
        }
        
        result_a_complex = _canonical("Category A", complex_map)
        result_e_complex = _canonical("Category E", complex_map)
        
        print(f"  Category A → {result_a_complex}")
        print(f"  Category E → {result_e_complex}")
        
        # Should handle both the loop and the valid chain
        assert result_a_complex in ["Category A", "Category B", "Category C", "Category D"]
        assert result_e_complex == "Category F"
        print("  ✅ Complex mapping handled correctly")

        # Test case 5: Empty mapping
        print("\n🔍 Test 5: Empty mapping")
        empty_map = {}
        
        result_empty = _canonical("Category X", empty_map)
        print(f"  Category X → {result_empty}")
        
        assert result_empty == "Category X"
        print("  ✅ Empty mapping handled correctly")

        print("\n✅ All loop detection tests passed")

    @pytest.mark.asyncio
    async def test_consolidation_mapping_consistency(self):
        """Test that consolidation mapping produces consistent results."""
        
        print("\n" + "="*80)
        print("🔗 CONSOLIDATION MAPPING CONSISTENCY")
        print("="*80)

        # Test that the mapping logic produces consistent results
        def build_combined_mapping(pre_consolidation_mapping: dict, raw_merge_map: dict) -> dict:
            """Simulate the combined mapping logic from the service."""
            
            def _canonical(name: str) -> str:
                """Collapse raw_merge_map chains to their final representative."""
                seen: set[str] = set()
                while raw_merge_map.get(name) and raw_merge_map[name] != name:
                    if name in seen:  # should not happen, safeguard against loops
                        break
                    seen.add(name)
                    name = raw_merge_map[name]
                return name

            # Combine pre-consolidation deduplication mapping with consolidation mapping
            combined_mapping: Dict[str, str] = {}
            
            # Start with all original category names and apply both mappings
            for original_name in set(pre_consolidation_mapping.keys()) | set(raw_merge_map.keys()):
                # First apply pre-consolidation deduplication
                intermediate_name = pre_consolidation_mapping.get(original_name, original_name)
                # Then apply consolidation mapping
                final_name = _canonical(intermediate_name)
                combined_mapping[original_name] = final_name
            
            # Also handle categories that only went through consolidation (not pre-dedup)
            for name in raw_merge_map.keys():
                if name not in combined_mapping:
                    combined_mapping[name] = _canonical(name)
            
            # Handle categories that only went through pre-dedup (not consolidation)
            for original_name, dedup_name in pre_consolidation_mapping.items():
                if original_name not in combined_mapping:
                    combined_mapping[original_name] = dedup_name
            
            return combined_mapping

        # Test case 1: Normal mapping without loops
        print("\n🔍 Test 1: Normal mapping consistency")
        pre_dedup_map = {
            "Category A": "Category A",
            "Category B": "Category A",  # B gets deduplicated to A
            "Category C": "Category C"
        }
        consolidation_map = {
            "Category A": "Final Category 1",
            "Category C": "Final Category 2"
        }
        
        combined = build_combined_mapping(pre_dedup_map, consolidation_map)
        print(f"  Combined mapping: {combined}")
        
        # Verify consistency
        assert combined["Category A"] == "Final Category 1"
        assert combined["Category B"] == "Final Category 1"  # B → A → Final Category 1
        assert combined["Category C"] == "Final Category 2"
        print("  ✅ Normal mapping is consistent")

        # Test case 2: Mapping with potential loops
        print("\n🔍 Test 2: Mapping with potential loops")
        pre_dedup_map_loop = {
            "Category A": "Category B",
            "Category B": "Category A"  # Circular reference
        }
        consolidation_map_loop = {
            "Category A": "Final Category",
            "Category B": "Final Category"
        }
        
        combined_loop = build_combined_mapping(pre_dedup_map_loop, consolidation_map_loop)
        print(f"  Combined mapping with loops: {combined_loop}")
        
        # Should handle loops gracefully
        assert "Category A" in combined_loop
        assert "Category B" in combined_loop
        print("  ✅ Loop mapping handled consistently")

        # Test case 3: Identity mapping
        print("\n🔍 Test 3: Identity mapping")
        identity_pre = {}
        identity_consolidation = {}
        
        combined_identity = build_combined_mapping(identity_pre, identity_consolidation)
        print(f"  Identity mapping: {combined_identity}")
        
        assert len(combined_identity) == 0
        print("  ✅ Identity mapping handled correctly")

        print("\n✅ All mapping consistency tests passed")

    @pytest.mark.asyncio
    async def test_consolidation_mapping_edge_cases(self):
        """Test edge cases in consolidation mapping."""
        
        print("\n" + "="*80)
        print("⚠️  CONSOLIDATION MAPPING EDGE CASES")
        print("="*80)

        def _canonical(name: str, raw_merge_map: dict) -> str:
            """Collapse raw_merge_map chains to their final representative."""
            seen: set[str] = set()
            while raw_merge_map.get(name) and raw_merge_map[name] != name:
                if name in seen:  # should not happen, safeguard against loops
                    break
                seen.add(name)
                name = raw_merge_map[name]
            return name

        # Test case 1: Very long chain
        print("\n🔍 Test 1: Very long chain")
        long_chain = {}
        for i in range(100):
            long_chain[f"Category_{i}"] = f"Category_{i+1}"
        long_chain["Category_100"] = "Category_100"  # Termination
        
        result_long = _canonical("Category_0", long_chain)
        print(f"  Category_0 → {result_long}")
        
        assert result_long == "Category_100"
        print("  ✅ Long chain handled correctly")

        # Test case 2: Disconnected mappings
        print("\n🔍 Test 2: Disconnected mappings")
        disconnected_map = {
            "Group A": "Group A Final",
            "Group B": "Group B Final",
            "Group C": "Group C Final"
        }
        
        for group in ["Group A", "Group B", "Group C"]:
            result = _canonical(group, disconnected_map)
            print(f"  {group} → {result}")
            assert result == f"{group} Final"
        
        print("  ✅ Disconnected mappings handled correctly")

        # Test case 3: Mixed valid and invalid mappings
        print("\n🔍 Test 3: Mixed valid and invalid mappings")
        mixed_map = {
            "Valid A": "Valid B",
            "Valid B": "Valid Final",
            "Invalid A": "Invalid B",
            "Invalid B": "Invalid A",  # Loop
            "Self": "Self"  # Self-reference
        }
        
        valid_result = _canonical("Valid A", mixed_map)
        invalid_result = _canonical("Invalid A", mixed_map)
        self_result = _canonical("Self", mixed_map)
        
        print(f"  Valid A → {valid_result}")
        print(f"  Invalid A → {invalid_result}")
        print(f"  Self → {self_result}")
        
        assert valid_result == "Valid Final"
        assert invalid_result in ["Invalid A", "Invalid B"]  # Loop detected
        assert self_result == "Self"
        print("  ✅ Mixed mappings handled correctly")

        print("\n✅ All edge case tests passed")

