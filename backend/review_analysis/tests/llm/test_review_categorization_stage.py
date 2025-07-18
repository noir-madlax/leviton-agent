"""Tests for review aspect categorization stage implementation.

This module tests the ReviewCategorizationStage using both mocked and real
LLM responses to ensure aspects are correctly categorized into new taxonomies
with proper aspect ID assignment tracking.

Test Coverage:
--------------
1. **test_real_llm_categorization_with_extracted_aspects**:
   Main integration test that uses real extracted aspects from a previous
   test run, calls a real LLM to categorize them, and saves the resulting
   taxonomies with aspect assignments for use in consolidation tests.

2. **test_build_prompt**:
   Verifies that the prompt is correctly constructed with all the necessary
   placeholders filled from the context.

3. **test_validation_with_valid_response**:
   Ensures that a correctly formatted JSON response (categories with definitions
   and ids arrays) passes validation.

4. **test_validation_with_invalid_response**:
   Checks that various malformed responses are correctly identified and
   flagged by the validator (e.g., missing 'ids', invalid aspect IDs,
   duplicate assignments).

5. **test_produce_result_conversion**:
   Tests the successful conversion of a valid raw JSON response into a
   structured ReviewCategorizationResult object with aspect assignments.

6. **test_split_and_merge_operations**:
   Validates that the stage can correctly split a context with many aspects
   and then merge the results, deduplicating the created taxonomies by name
   and merging aspect assignments.

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
    ReviewCategorizationResult,
)
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

def extract_unique_aspects(review_hierarchy: Dict, section: str) -> List[Tuple[str, str]]:
    """Extract unique aspects from a review hierarchy section."""
    unique_aspects = {}
    section_data = review_hierarchy.get(section, {})
    
    aspect_id_counter = 0
    
    for group_name, group_data in section_data.items():
        if not isinstance(group_data, dict):
            continue
            
        for aspect_key, sentiment_data in group_data.items():
            if "@" in aspect_key:
                aspect_id, detail = aspect_key.split("@", 1)
                aspect_description = f"{group_name} – {detail}"
                
                if aspect_description not in unique_aspects.values():
                    unique_aspects[str(aspect_id_counter)] = aspect_description
                    aspect_id_counter += 1
    
    return list(unique_aspects.items())

def save_categorization_results(results: Dict[str, ReviewCategorizationResult], metadata: Dict) -> None:
    """Save categorization results to JSON file."""
    output_data = {
        "test_metadata": {
            "timestamp": metadata.get("timestamp"),
            "product_category": metadata.get("product_category", PRODUCT_CATEGORY),
            "product_title": metadata.get("product_title"),
            "total_sections_processed": len(results)
        },
        "categorization_results": {}
    }
    
    for section, result in results.items():
        output_data["categorization_results"][section] = {
            "taxonomies": [
                {"name": tax.name, "definition": tax.definition}
                for tax in result.taxonomies_categorised
            ],
            "assignments": result.assignments_initial,
            "total_categories": len(result.taxonomies_categorised),
            "total_assignments": len(result.assignments_initial)
        }
    
    with open(CATEGORIZATION_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Categorization results saved to: {CATEGORIZATION_RESULTS_PATH}")


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
        assert "OUT_OF_SCOPE" in prompt  # Should include OUT_OF_SCOPE in example
        print("\n✅ Prompt built successfully.")

    @pytest.mark.asyncio
    async def test_validation_with_valid_response(self, categorization_stage: ReviewCategorizationStage):
        """Test the validator with a correct response including aspect IDs."""
        valid_response = json.dumps({
            "Durability": {
                "definition": "Issues related to the product drying out, e.g. markers drying up.",
                "ids": [0]
            },
            "Cleanliness": {
                "definition": "How easy the product is to clean, e.g. washes off skin easily.",
                "ids": [1]
            }
        })
        context = ReviewCategorizationContext(
            product_category=PRODUCT_CATEGORY,
            aspects=[("0", "dries out quickly"), ("1", "easy to wash off")],
            aspect_type="performance", 
            aspect_context="", 
            input_description="", 
            product_categories=set()
        )
        result = categorization_stage._validate(valid_response, context)

        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - VALID RESPONSE WITH ASPECT IDS")
        print("="*60)
        print(f"✅ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {valid_response}")
        print("="*60)
        
        assert result.ok is True
        print("\n✅ Validator correctly passed a valid response with aspect IDs.")

    @pytest.mark.asyncio
    async def test_validation_with_out_of_scope(self, categorization_stage: ReviewCategorizationStage):
        """Test the validator with OUT_OF_SCOPE category."""
        valid_response = json.dumps({
            "Durability": {
                "definition": "Issues related to the product drying out, e.g. markers drying up.",
                "ids": [0]
            },
            "OUT_OF_SCOPE": {
                "definition": "Aspects that are too vague, generic, or irrelevant to performance, e.g. unclear feedback",
                "ids": [1, 2]
            }
        })
        context = ReviewCategorizationContext(
            product_category=PRODUCT_CATEGORY,
            aspects=[("0", "dries out quickly"), ("1", "general comment"), ("2", "vague feedback")],
            aspect_type="performance", 
            aspect_context="", 
            input_description="", 
            product_categories=set()
        )
        result = categorization_stage._validate(valid_response, context)

        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - VALID RESPONSE WITH OUT_OF_SCOPE")
        print("="*60)
        print(f"✅ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {valid_response}")
        print("="*60)
        
        assert result.ok is True
        print("\n✅ Validator correctly passed a valid response with OUT_OF_SCOPE.")

    @pytest.mark.asyncio
    async def test_validation_with_invalid_response(self, categorization_stage: ReviewCategorizationStage):
        """Test the validator with various incorrect responses."""
        context = ReviewCategorizationContext(
            product_category=PRODUCT_CATEGORY,
            aspects=[("0", "test aspect"), ("1", "another test")],
            aspect_type="performance", 
            aspect_context="", 
            input_description="", 
            product_categories=set()
        )

        # Case 1: Missing 'ids' field
        missing_ids = json.dumps({"Category A": {"definition": "def"}})
        result = categorization_stage._validate(missing_ids, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 1: Missing 'ids')")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {missing_ids}")
        print("="*60)
        
        assert result.ok is False
        assert "missing 'ids' field" in result.error_categories["validation_errors"][0]

        # Case 2: Invalid aspect ID
        invalid_id = json.dumps({"Category A": {"definition": "def", "ids": [99]}})
        result = categorization_stage._validate(invalid_id, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 2: Invalid aspect ID)")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {invalid_id}")
        print("="*60)
        
        assert result.ok is False
        assert "contains invalid id" in result.error_categories["completeness_errors"][0]

        # Case 3: Duplicate aspect ID assignment
        duplicate_id = json.dumps({
            "Category A": {"definition": "def A", "ids": [0]},
            "Category B": {"definition": "def B", "ids": [0, 1]}
        })
        result = categorization_stage._validate(duplicate_id, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 3: Duplicate aspect ID)")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {duplicate_id}")
        print("="*60)
        
        assert result.ok is False
        assert "appears in multiple categories" in result.error_categories["completeness_errors"][0]

        # Case 4: Missing aspect assignments
        missing_assignment = json.dumps({"Category A": {"definition": "def", "ids": [0]}})
        result = categorization_stage._validate(missing_assignment, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 4: Missing assignments)")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {missing_assignment}")
        print("="*60)
        
        assert result.ok is False
        assert "Missing assignments for ids" in result.error_categories["completeness_errors"][0]
        
        print("\n✅ Validator correctly rejected various invalid responses.")
    
    @pytest.mark.asyncio
    async def test_produce_result_conversion(self, categorization_stage: ReviewCategorizationStage):
        """Test conversion of a valid response to a result object with assignments."""
        raw_response = json.dumps({
            "Category A": {
                "definition": "def A",
                "ids": [0, 2]
            },
            "Category B": {
                "definition": "def B", 
                "ids": [1]
            },
            "OUT_OF_SCOPE": {
                "definition": "Irrelevant aspects",
                "ids": [3]
            }
        })
        context = ReviewCategorizationContext(
            product_category="", 
            aspects=[("0", "aspect 0"), ("1", "aspect 1"), ("2", "aspect 2"), ("3", "aspect 3")], 
            aspect_type="", 
            aspect_context="", 
            input_description="", 
            product_categories=set()
        )
        result = await categorization_stage._produce_result(raw_response, context, 1)
        
        print("\n" + "="*60)
        print("🔍 RESULT CONVERSION WITH ASPECT ASSIGNMENTS")
        print("="*60)
        print(f"📝 Raw response: {raw_response}")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Taxonomies created: {len(result.taxonomies_categorised)}")
        print(f"📊 Assignments created: {len(result.assignments_initial)}")
        print("📋 Converted taxonomies:")
        for tax in result.taxonomies_categorised:
            print(f"   - {tax.name}: {tax.definition}")
        print("📋 Aspect assignments:")
        for aspect_id, category_name in result.assignments_initial.items():
            print(f"   - Aspect {aspect_id} → {category_name}")
        print("="*60)

        assert isinstance(result, ReviewCategorizationResult)
        assert len(result.taxonomies_categorised) == 3  # A, B, OUT_OF_SCOPE
        assert len(result.assignments_initial) == 4  # All 4 aspects assigned
        assert result.assignments_initial["0"] == "Category A"
        assert result.assignments_initial["1"] == "Category B"
        assert result.assignments_initial["2"] == "Category A"
        assert result.assignments_initial["3"] == "OUT_OF_SCOPE"
        print("\n✅ Result with assignments produced successfully from raw response.")

    @pytest.mark.asyncio
    async def test_split_and_merge_operations(self, categorization_stage: ReviewCategorizationStage):
        """Test splitting a context and merging the results with assignments."""
        # 1. Split
        context = ReviewCategorizationContext(
            product_category="",
            aspects=[(str(i), f"aspect_{i}") for i in range(4)],
            aspect_type="test", 
            aspect_context="", 
            input_description="", 
            product_categories=set()
        )
        ctx_left, ctx_right = categorization_stage._split_context(context, 0)
        assert len(ctx_left.aspects) == 2
        assert len(ctx_right.aspects) == 2
        assert ctx_left.aspects[0][1] == "aspect_0"
        assert ctx_right.aspects[0][1] == "aspect_2"
        
        # 2. Merge
        res_left = ReviewCategorizationResult(
            taxonomies_categorised=[
                TaxonomyDTO(name="Cat A", definition="def A"),
                TaxonomyDTO(name="Cat B", definition="def B")
            ],
            assignments_initial={"0": "Cat A", "1": "Cat B"}
        )
        res_right = ReviewCategorizationResult(
            taxonomies_categorised=[
                TaxonomyDTO(name="Cat B", definition="def B updated"), # Duplicate name
                TaxonomyDTO(name="Cat C", definition="def C")
            ],
            assignments_initial={"2": "Cat B", "3": "Cat C"}
        )
        
        merged = await categorization_stage._merge_split_results(res_left, res_right, ctx_left, ctx_right, 0)
        
        assert isinstance(merged, ReviewCategorizationResult)
        assert len(merged.taxonomies_categorised) == 3  # A, B, C (B deduplicated)
        assert len(merged.assignments_initial) == 4  # All assignments merged
        
        # Check that assignments are preserved
        assert merged.assignments_initial["0"] == "Cat A"
        assert merged.assignments_initial["1"] == "Cat B"
        assert merged.assignments_initial["2"] == "Cat B"
        assert merged.assignments_initial["3"] == "Cat C"
        
        # Check that the first definition of Cat B was kept
        cat_b_merged = next(t for t in merged.taxonomies_categorised if t.name == "Cat B")
        assert cat_b_merged.definition == "def B"
        print("\n✅ Split and merge operations work as expected with assignments.")

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
        
        final_results: Dict[str, ReviewCategorizationResult] = {}

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

            print(f"✅ Section '{section}' categorized into {len(result.taxonomies_categorised)} categories.")
            print(f"📊 Assignments created: {len(result.assignments_initial)}")
            print("📋 Categories:")
            for tax in result.taxonomies_categorised[:8]: # Print first 8
                print(f"  - {tax.name}: {tax.definition}")
            if len(result.taxonomies_categorised) > 8:
                print("  ...")
            
            print("📋 Sample assignments:")
            sample_assignments = list(result.assignments_initial.items())[:8]
            for aspect_id, category_name in sample_assignments:
                aspect_desc = next((desc for aid, desc in unique_aspects if aid == aspect_id), "Unknown")
                print(f"  - Aspect {aspect_id} ({aspect_desc[:30]}...) → {category_name}")
            if len(result.assignments_initial) > 8:
                print("  ...")

        assert final_results, "Categorization should yield results for at least one section."
        
        # Validate that all aspects were assigned
        for section, result in final_results.items():
            section_aspects = extract_unique_aspects(review_hierarchy, section)
            expected_aspect_ids = {aid for aid, _ in section_aspects}
            assigned_aspect_ids = set(result.assignments_initial.keys())
            
            assert expected_aspect_ids == assigned_aspect_ids, (
                f"Section {section}: Aspect assignment mismatch. "
                f"Expected {len(expected_aspect_ids)} aspects, got {len(assigned_aspect_ids)} assignments."
            )
        
        # Save results for next stage
        save_categorization_results(final_results, metadata)
        
        print("\n🎉 Real LLM categorization test complete with aspect assignments.") 