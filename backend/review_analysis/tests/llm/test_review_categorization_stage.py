"""Tests for review aspect categorization stage implementation.

This module tests the ReviewCategorizationStage using both mocked and real
LLM responses to ensure aspects are correctly categorized into new taxonomies.

Test Coverage:
--------------
1. **test_real_llm_categorization_with_extracted_aspects**:
   Main integration test that uses real extracted aspects from a previous
   test run, calls a real LLM to categorize them, and saves the resulting
   taxonomies for use in consolidation tests.

2. **test_build_prompt**:
   Verifies that the prompt is correctly constructed with all the necessary
   placeholders filled from the context.

3. **test_validation_with_valid_response**:
   Ensures that a correctly formatted JSON response (a flat object of
   category -> definition mappings) passes validation.

4. **test_validation_with_invalid_response**:
   Checks that various malformed responses are correctly identified and
   flagged by the validator (e.g., presence of 'ids', 'OUT_OF_SCOPE',
   missing 'definition').

5. **test_produce_result_conversion**:
   Tests the successful conversion of a valid raw JSON response into a
   structured CategorizationStageResult object.

6. **test_split_and_merge_operations**:
   Validates that the stage can correctly split a context with many aspects
   and then merge the results, deduplicating the created taxonomies by name.

Configuration:
--------------
- Uses extracted aspects from `test_data/real_amazon_extraction_results.json`.
- Saves new categorization results to `test_data/real_amazon_categorization_results.json`.
- Product category: "Kids Arts & Crafts".
- Fixed prompt templates: `review_aspects_categorization_prompt_v0.txt`, `shared_retry_prompt_v0.txt`.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List, Tuple

from review_analysis.llm.review_categorization_stage import (
    ReviewCategorizationStage,
    ReviewCategorizationContext,
)
from core.llm_taxonomy_pipeline.categorization_base import CategorizationStageResult
from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"
EXTRACTION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_extraction_results.json"
CATEGORIZATION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_categorization_results.json"
PRODUCT_CATEGORY = "Kids Arts & Crafts"


# Fixtures
@pytest.fixture
def extraction_results() -> Dict:
    """Load real extraction results from the extraction stage test."""
    if not EXTRACTION_RESULTS_PATH.exists():
        pytest.skip(f"Extraction results not found: {EXTRACTION_RESULTS_PATH}")
    with open(EXTRACTION_RESULTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def categorization_stage() -> ReviewCategorizationStage:
    """Create a ReviewCategorizationStage instance."""
    return ReviewCategorizationStage()


# Helper Functions
def extract_unique_aspects(hierarchy: Dict, section: str) -> List[Tuple[str, str]]:
    """Extracts unique aspect descriptions from a given section of the hierarchy."""
    unique_aspects: Dict[str, str] = {}
    if section in hierarchy:
        # 'use' section has a different structure: keys are the aspects
        if section == "use":
            for aspect_key in hierarchy[section].keys():
                if aspect_key not in unique_aspects:
                    unique_aspects[aspect_key] = str(len(unique_aspects))
        else:
            # phy/perf sections have nested categories
            for category in hierarchy[section].values():
                for aspect_key in category.keys():
                    # aspect_key is "A@description" or "a@description"
                    if '@' in aspect_key:
                        desc = aspect_key.split('@', 1)[1]
                    else:
                        desc = aspect_key
                    
                    # Use description as key to ensure uniqueness
                    if desc not in unique_aspects:
                        unique_aspects[desc] = str(len(unique_aspects))

    # Return as (id, description) tuples
    # Sorting by id (which is just insertion order)
    return sorted([(v, k) for k, v in unique_aspects.items()], key=lambda x: int(x[0]))


def save_categorization_results(
    categorization_results: Dict[str, CategorizationStageResult],
    metadata: Dict
):
    """Save categorization results to a JSON file."""
    from datetime import datetime
    
    saved_data = {
        "metadata": {
            "product_category": metadata.get("product_category", PRODUCT_CATEGORY),
            "asin": metadata.get("asin"),
            "product_title": metadata.get("product_title"),
            "categorization_timestamp": datetime.now().isoformat(),
            "source_file": str(EXTRACTION_RESULTS_PATH),
        },
        "categorization_results": {}
    }
    
    for aspect_type, result in categorization_results.items():
        saved_data["categorization_results"][aspect_type] = {
            "taxonomy_count": len(result.taxonomies_categorised),
            "taxonomies": [
                {"name": tax.name, "definition": tax.definition}
                for tax in result.taxonomies_categorised
            ]
        }

    with open(CATEGORIZATION_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(saved_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved categorization results to: {CATEGORIZATION_RESULTS_PATH}")


# Test Class
class TestCategorizationStage:
    """Test suite for the aspect categorization stage."""

    @pytest.mark.asyncio
    async def test_build_prompt(self, categorization_stage: ReviewCategorizationStage):
        """Verify that the prompt is built correctly."""
        context = ReviewCategorizationContext(
            product_category=PRODUCT_CATEGORY,
            aspects=[("0", "dries out quickly"), ("1", "easy to wash off")],
            aspect_type="performance",
            aspect_context="functional characteristics",
            input_description="Lines show performance aspects: [ID] description",
            product_categories={PRODUCT_CATEGORY}
        )
        prompt = await categorization_stage._build_prompt(context)

        # Print full prompt for manual inspection
        print("\n" + "="*80)
        print("🔍 FULL PROMPT FOR MANUAL INSPECTION")
        print("="*80)
        print(prompt)
        print("="*80)

        assert PRODUCT_CATEGORY in prompt
        assert "performance" in prompt
        assert "functional characteristics" in prompt
        assert "[0] dries out quickly" in prompt
        assert "[1] easy to wash off" in prompt
        print("\n✅ Prompt built successfully.")

    @pytest.mark.asyncio
    async def test_validation_with_valid_response(self, categorization_stage: ReviewCategorizationStage):
        """Test the validator with a correct response."""
        valid_response = json.dumps({
            "Durability": {"definition": "Issues related to the product drying out, e.g. markers drying up."},
            "Cleanliness": {"definition": "How easy the product is to clean, e.g. washes off skin easily."}
        })
        context = ReviewCategorizationContext(
            product_category=PRODUCT_CATEGORY,
            aspects=[("0", "dries out quickly"), ("1", "easy to wash off")],
            aspect_type="performance", aspect_context="", input_description="", product_categories=set()
        )
        result = categorization_stage._validate(valid_response, context)

        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - VALID RESPONSE")
        print("="*60)
        print(f"✅ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {valid_response}")
        print("="*60)
        
        assert result.ok is True
        print("\n✅ Validator correctly passed a valid response.")

    @pytest.mark.asyncio
    async def test_validation_with_invalid_response(self, categorization_stage: ReviewCategorizationStage):
        """Test the validator with various incorrect responses."""
        context = ReviewCategorizationContext(
            product_category=PRODUCT_CATEGORY,
            aspects=[("0", "test")],
            aspect_type="performance", aspect_context="", input_description="", product_categories=set()
        )

        # Case 1: Contains 'ids'
        invalid_ids = json.dumps({"Category A": {"definition": "def", "ids": ["0"]}})
        result = categorization_stage._validate(invalid_ids, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 1: Contains 'ids')")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {invalid_ids}")
        print("="*60)
        
        assert result.ok is False
        assert "contains unexpected fields" in result.error_categories["validation_errors"][0]

        # Case 2: Missing 'definition'
        missing_def = json.dumps({"Category A": {}})
        result = categorization_stage._validate(missing_def, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 2: Missing 'definition')")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {missing_def}")
        print("="*60)
        
        assert result.ok is False
        assert "missing 'definition' field" in result.error_categories["validation_errors"][0]

        # Case 3: Contains 'OUT_OF_SCOPE'
        has_oos = json.dumps({"OUT_OF_SCOPE": {"definition": "def"}})
        result = categorization_stage._validate(has_oos, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 3: Reserved name 'OUT_OF_SCOPE')")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {has_oos}")
        print("="*60)
        
        assert result.ok is False
        
        print("\n✅ Validator correctly rejected various invalid responses.")
    
    @pytest.mark.asyncio
    async def test_produce_result_conversion(self, categorization_stage: ReviewCategorizationStage):
        """Test conversion of a valid response to a result object."""
        raw_response = json.dumps({
            "Category A": {"definition": "def A"},
            "Category B": {"definition": "def B"}
        })
        context = ReviewCategorizationContext(
            product_category="", aspects=[], aspect_type="", aspect_context="", input_description="", product_categories=set()
        )
        result = await categorization_stage._produce_result(raw_response, context, 1)
        
        print("\n" + "="*60)
        print("🔍 RESULT CONVERSION")
        print("="*60)
        print(f"📝 Raw response: {raw_response}")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Taxonomies created: {len(result.taxonomies_categorised)}")
        print("📋 Converted taxonomies:")
        for tax in result.taxonomies_categorised:
            print(f"   - {tax.name}: {tax.definition}")
        print("="*60)

        assert isinstance(result, CategorizationStageResult)
        assert len(result.taxonomies_categorised) == 2
        assert result.taxonomies_categorised[0].name == "Category A"
        print("\n✅ Result produced successfully from raw response.")

    @pytest.mark.asyncio
    async def test_split_and_merge_operations(self, categorization_stage: ReviewCategorizationStage):
        """Test splitting a context and merging the results."""
        # 1. Split
        context = ReviewCategorizationContext(
            product_category="",
            aspects=[(str(i), f"aspect_{i}") for i in range(4)],
            aspect_type="", aspect_context="", input_description="", product_categories=set()
        )
        ctx_left, ctx_right = categorization_stage._split_context(context, 0)
        assert len(ctx_left.aspects) == 2
        assert len(ctx_right.aspects) == 2
        assert ctx_left.aspects[0][1] == "aspect_0"
        assert ctx_right.aspects[0][1] == "aspect_2"
        
        # 2. Merge
        res_left = CategorizationStageResult(taxonomies_categorised=[
            TaxonomyDTO(name="Cat A", definition="def A"),
            TaxonomyDTO(name="Cat B", definition="def B")
        ])
        res_right = CategorizationStageResult(taxonomies_categorised=[
            TaxonomyDTO(name="Cat B", definition="def B updated"), # Duplicate name
            TaxonomyDTO(name="Cat C", definition="def C")
        ])
        
        merged = await categorization_stage._merge_split_results(res_left, res_right, ctx_left, ctx_right, 0)
        
        assert isinstance(merged, CategorizationStageResult)
        assert len(merged.taxonomies_categorised) == 3 # A, B, C
        
        # Check that the first definition of Cat B was kept
        cat_b_merged = next(t for t in merged.taxonomies_categorised if t.name == "Cat B")
        assert cat_b_merged.definition == "def B"
        print("\n✅ Split and merge operations work as expected.")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_llm_categorization_with_extracted_aspects(
        self,
        categorization_stage: ReviewCategorizationStage,
        extraction_results: Dict,
    ):
        """
        Main integration test using a real LLM to categorize aspects
        extracted from a previous test run.
        """
        review_hierarchy = extraction_results.get("extraction_result", {}).get("review_hierarchy", {})
        metadata = extraction_results.get("test_metadata", {})

        print(f"\n\n🚀 Starting real LLM categorization for product: {metadata.get('product_title')}")
        
        final_results: Dict[str, CategorizationStageResult] = {}

        aspect_definitions = {
            "phy": ("physical", "physical product characteristics and attributes", "Physical aspect: [ID] description"),
            "perf": ("performance", "product functionality and operational characteristics", "Performance aspect: [ID] description"),
            "use": ("use case", "product applications and usage scenarios", "Use case: [ID] description")
        }

        for section, (aspect_type, aspect_context, input_desc) in aspect_definitions.items():
            print(f"\n---\nProcessing section: {section.upper()}\n---")
            unique_aspects = extract_unique_aspects(review_hierarchy, section)
            
            if not unique_aspects:
                print(f"⚠️ No unique aspects found for section '{section}'. Skipping.")
                continue

            print(f"Found {len(unique_aspects)} unique aspects to categorize.")
            print("   - Sample aspects:")
            for aspect_id, aspect_desc in unique_aspects[:8]:
                print(f"     [{aspect_id}] {aspect_desc}")
            if len(unique_aspects) > 8:
                print("     ...")
            
            context = ReviewCategorizationContext(
                product_category=metadata.get("product_category", PRODUCT_CATEGORY),
                aspects=unique_aspects,
                aspect_type=aspect_type,
                aspect_context=aspect_context,
                input_description=input_desc,
                product_categories={metadata.get("product_category", PRODUCT_CATEGORY)}
            )

            print(f"Executing categorization stage for '{section}'...")
            result = await categorization_stage.execute(context)
            final_results[section] = result

            print(f"✅ Section '{section}' categorized into {len(result.taxonomies_categorised)} taxonomies.")
            for tax in result.taxonomies_categorised[:8]: # Print first 8
                print(f"  - {tax.name}: {tax.definition}")
            if len(result.taxonomies_categorised) > 8:
                print("  ...")

        assert final_results, "Categorization should yield results for at least one section."
        
        # Save results for next stage
        save_categorization_results(final_results, metadata)
        
        print("\n🎉 Real LLM categorization test complete.") 