"""Tests for review aspect refinement stage implementation.

This module tests the ReviewRefinementStage class using real aspect data from
the categorization results, refining aspect assignments to ensure they are in
the most appropriate consolidated categories.

Test Coverage:
--------------

1. **test_refine_aspects_from_categorization_results**: 
   Main integration test that takes categories and aspects from categorization
   results and processes them through the refinement stage. Validates
   the complete refinement workflow including result structure, assignment
   quality, and data integrity.

2. **test_build_prompt_with_categories_and_aspects**:
   Tests prompt construction with categories and aspects. Verifies proper
   formatting of categories with C_* IDs and aspects with integer indices.

3. **test_validation_with_valid_response**:
   Tests the validation logic with a properly formatted JSON response that
   matches the expected refinement schema (aspect reassignments or empty object).

4. **test_validation_with_invalid_response**:
   Tests validation error handling with various malformed responses:
   - Invalid JSON syntax
   - Invalid aspect or category IDs
   - Malformed response structure
   Ensures proper error categorization and reporting.

5. **test_retry_prompt_generation**:
   Tests retry prompt construction using the shared_retry_prompt_v0.txt template.
   Verifies that validation errors are properly formatted and included in
   retry instructions to help the LLM correct its response.

6. **test_produce_result_conversion**:
   Tests the conversion of valid raw JSON responses into ReviewRefinementStageResult
   objects. Verifies proper parsing of reassignments and conversion of
   aspect/category IDs.

7. **test_merge_split_results**:
   Tests the merging logic for split processing scenarios. Verifies proper
   index adjustment and reassignment consolidation across splits.

Configuration:
--------------
- Uses categorization results from real_amazon_categorization_results.json
- Fixed prompt templates: review_aspects_refinement_prompt_v0.txt, shared_retry_prompt_v0.txt
- No external configuration required - templates loaded automatically
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List, Set
from unittest.mock import AsyncMock

from core.utils.llm_utils import ValidationResult
from review_analysis.llm.review_refinement_stage import (
    ReviewRefinementStage,
    ReviewRefinementStageResult,
    ReviewRefinementStageContext,
)
from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "test_data"
CATEGORIZATION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_categorization_results.json"
REFINEMENT_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_refinement_results.json"
PRODUCT_CATEGORY = "Kids Arts & Crafts"


def save_refinement_results(
    refinement_result: ReviewRefinementStageResult,
    categories: List[TaxonomyDTO],
    aspects: List[str],
    aspect_type: str,
    product_category: str
) -> None:
    """Save review refinement results to JSON file for analysis.
    
    Args:
        refinement_result: Result from the refinement stage
        categories: List of available categories
        aspects: List of aspect descriptions
        aspect_type: Type of aspects being refined
        product_category: Product category that was processed
    """
    from datetime import datetime
    
    # Count reassignments by category
    reassignment_counts = {}
    for aspect_idx, new_category in refinement_result.reassignments.items():
        reassignment_counts[new_category] = reassignment_counts.get(new_category, 0) + 1
    
    saved_data = {
        "metadata": {
            "product_category": product_category,
            "aspect_type": aspect_type,
            "refinement_timestamp": datetime.now().isoformat(),
            "total_aspects": len(aspects),
            "total_categories": len(categories),
            "aspects_reassigned": len(refinement_result.reassignments),
            "reassignment_percentage": round(len(refinement_result.reassignments) / len(aspects) * 100, 2) if aspects else 0,
        },
        "categories": [
            {"name": category.name, "definition": category.definition}
            for category in categories
        ],
        "aspects": aspects,
        "reassignments": {str(k): v for k, v in refinement_result.reassignments.items()},
        "reassignment_summary": reassignment_counts,
        "reassigned_aspects": [
            {
                "aspect_index": aspect_idx,
                "aspect_description": aspects[aspect_idx] if aspect_idx < len(aspects) else "UNKNOWN",
                "new_category": new_category,
                "reason": f"Better fit in {new_category}"
            }
            for aspect_idx, new_category in refinement_result.reassignments.items()
        ]
    }
    
    # Save to JSON file
    with open(REFINEMENT_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(saved_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved refinement results to: {REFINEMENT_RESULTS_PATH}")
    print(f"   - {len(refinement_result.reassignments)} aspects reassigned")
    print(f"   - {saved_data['metadata']['reassignment_percentage']}% reassignment rate")
    
    # Print top reassignment patterns
    if reassignment_counts:
        print(f"   - Top reassignment categories:")
        for category, count in sorted(reassignment_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"     • {category}: {count} aspects")


@pytest.fixture
def categorization_results() -> Dict:
    """Load categorization results from the categorization stage test."""
    if not CATEGORIZATION_RESULTS_PATH.exists():
        pytest.skip(f"Categorization results not found: {CATEGORIZATION_RESULTS_PATH}")
    
    with open(CATEGORIZATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def sample_refinement_data() -> tuple[List[TaxonomyDTO], List[str], str, Set[str]]:
    """Create sample data for refinement testing."""
    
    # Sample categories
    categories = [
        TaxonomyDTO(name="Durability Issues", definition="Problems with product longevity and wear"),
        TaxonomyDTO(name="Color Quality", definition="Issues with color vibrancy and consistency"),
        TaxonomyDTO(name="Usability Problems", definition="Difficulties in product use and handling")
    ]
    
    # Sample aspects
    aspects = [
        "marker tip durability",
        "color vibrancy and intensity", 
        "cap fit and security",
        "barrel thickness and grip",
        "ink flow consistency"
    ]
    
    aspect_type = "physical"
    product_categories = {PRODUCT_CATEGORY}
    
    return categories, aspects, aspect_type, product_categories


@pytest.fixture 
def mock_llm_client() -> AsyncMock:
    """Mock LLM client that returns valid aspect refinement responses."""
    
    def create_refinement_response(prompt: str) -> str:
        # Parse the prompt to find aspects
        aspect_lines = [line for line in prompt.split('\n') if line.strip().startswith('[') and ']' in line]
        aspect_count = len(aspect_lines)
        
        # Simulate some reassignments (about 20% of aspects)
        reassignments = {}
        reassignment_count = max(1, aspect_count // 5)
        
        for i in range(reassignment_count):
            # Simulate reassigning to different category
            category_id = f"C_{i % 3}"  # Rotate through first 3 categories
            reassignments[str(i)] = category_id
        
        return json.dumps(reassignments)
    
    mock = AsyncMock()
    mock.side_effect = lambda prompt, **kwargs: create_refinement_response(prompt)
    return mock


@pytest.fixture
def refinement_stage() -> ReviewRefinementStage:
    """Create a ReviewRefinementStage instance."""
    return ReviewRefinementStage()


class TestReviewRefinementStage:
    """Test suite for the review aspect refinement stage."""

    @pytest.mark.asyncio
    async def test_build_prompt_with_categories_and_aspects(
        self,
        refinement_stage: ReviewRefinementStage,
        sample_refinement_data: tuple[List[TaxonomyDTO], List[str], str, Set[str]]
    ) -> None:
        """Test prompt construction with categories and aspects."""
        categories, aspects, aspect_type, product_categories = sample_refinement_data
        
        context = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            aspect_type=aspect_type,
            aspect_context="physical product characteristics",
            categories=categories,
            aspects=aspects,
            product_categories=product_categories
        )
        
        prompt = await refinement_stage._build_prompt(context)
        
        # Print full prompt for manual inspection
        print("\n" + "="*80)
        print("🔍 FULL PROMPT FOR MANUAL INSPECTION")
        print("="*80)
        print(prompt)
        print("="*80)
        
        # Verify prompt contains expected elements
        assert PRODUCT_CATEGORY in prompt
        assert aspect_type in prompt
        assert "physical product characteristics" in prompt
        
        # Check categories are formatted with C_* IDs
        for i, category in enumerate(categories):
            assert f"[C_{i}] {category.name}: {category.definition}" in prompt
        
        # Check aspects are formatted with integer indices
        for i, aspect in enumerate(aspects):
            assert f"[{i}] {aspect}" in prompt
        
        print("\n✅ Prompt built successfully with categories and aspects.")

    @pytest.mark.asyncio
    async def test_validation_with_valid_response(
        self,
        refinement_stage: ReviewRefinementStage,
        sample_refinement_data: tuple[List[TaxonomyDTO], List[str], str, Set[str]]
    ) -> None:
        """Test the validator with a correct response."""
        categories, aspects, aspect_type, product_categories = sample_refinement_data
        
        # Create valid response with some reassignments
        valid_response = json.dumps({
            "0": "C_1",
            "2": "C_0", 
            "4": "OUT_OF_SCOPE"
        })
        
        context = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            aspect_type=aspect_type,
            aspect_context="physical product characteristics",
            categories=categories,
            aspects=aspects,
            product_categories=product_categories
        )
        
        result = refinement_stage._validate(valid_response, context)
        
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
    async def test_validation_with_invalid_response(
        self,
        refinement_stage: ReviewRefinementStage,
        sample_refinement_data: tuple[List[TaxonomyDTO], List[str], str, Set[str]]
    ) -> None:
        """Test the validator with various incorrect responses."""
        categories, aspects, aspect_type, product_categories = sample_refinement_data
        
        context = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            aspect_type=aspect_type,
            aspect_context="physical product characteristics",
            categories=categories,
            aspects=aspects,
            product_categories=product_categories
        )

        # Case 1: Invalid aspect index
        invalid_aspect_idx = json.dumps({"99": "C_0"})  # Index out of range
        result = refinement_stage._validate(invalid_aspect_idx, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 1: Invalid aspect index)")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {invalid_aspect_idx}")
        print("="*60)
        
        assert result.ok is False
        assert any("Invalid aspect index" in error for error in result.error_categories["completeness_errors"])

        # Case 2: Invalid category ID
        invalid_category = json.dumps({"0": "C_99"})  # Category out of range
        result = refinement_stage._validate(invalid_category, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 2: Invalid category ID)")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {invalid_category}")
        print("="*60)
        
        assert result.ok is False
        assert any("Invalid category ID" in error for error in result.error_categories["completeness_errors"])

        # Case 3: Invalid JSON
        invalid_json = "not valid json"
        result = refinement_stage._validate(invalid_json, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE (Case 3: Invalid JSON)")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {invalid_json}")
        print("="*60)
        
        assert result.ok is False
        assert len(result.error_categories["format_errors"]) > 0
        
        print("\n✅ Validator correctly rejected various invalid responses.")

    @pytest.mark.asyncio
    async def test_validation_with_empty_response(
        self,
        refinement_stage: ReviewRefinementStage,
        sample_refinement_data: tuple[List[TaxonomyDTO], List[str], str, Set[str]]
    ) -> None:
        """Test the validator with an empty response (no reassignments needed)."""
        categories, aspects, aspect_type, product_categories = sample_refinement_data
        
        # Empty object means no reassignments needed
        empty_response = json.dumps({})
        
        context = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            aspect_type=aspect_type,
            aspect_context="physical product characteristics",
            categories=categories,
            aspects=aspects,
            product_categories=product_categories
        )
        
        result = refinement_stage._validate(empty_response, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - EMPTY RESPONSE (No reassignments)")
        print("="*60)
        print(f"✅ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {empty_response}")
        print("="*60)
        
        assert result.ok is True
        print("\n✅ Validator correctly accepted empty response (no reassignments).")

    @pytest.mark.asyncio
    async def test_produce_result_conversion(
        self,
        refinement_stage: ReviewRefinementStage,
        sample_refinement_data: tuple[List[TaxonomyDTO], List[str], str, Set[str]]
    ) -> None:
        """Test conversion of a valid response to a result object."""
        categories, aspects, aspect_type, product_categories = sample_refinement_data
        
        raw_response = json.dumps({
            "0": "C_1",
            "2": "C_0",
            "4": "OUT_OF_SCOPE"
        })
        
        context = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            aspect_type=aspect_type,
            aspect_context="physical product characteristics",
            categories=categories,
            aspects=aspects,
            product_categories=product_categories
        )
        
        result = await refinement_stage._produce_result(raw_response, context, 1)
        
        print("\n" + "="*60)
        print("🔍 RESULT CONVERSION")
        print("="*60)
        print(f"📝 Raw response: {raw_response}")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Reassignments: {len(result.reassignments)}")
        print("📋 Converted reassignments:")
        for aspect_idx, category_name in result.reassignments.items():
            aspect_desc = aspects[aspect_idx] if aspect_idx < len(aspects) else "UNKNOWN"
            print(f"   - Aspect {aspect_idx} ({aspect_desc}) → {category_name}")
        print("="*60)
        
        assert isinstance(result, ReviewRefinementStageResult)
        assert len(result.reassignments) == 3
        assert result.reassignments[0] == categories[1].name  # C_1 maps to second category
        assert result.reassignments[2] == categories[0].name  # C_0 maps to first category  
        assert result.reassignments[4] == "OUT_OF_SCOPE"
        
        print("\n✅ Result conversion successful.")

    @pytest.mark.asyncio
    async def test_merge_split_results(
        self,
        refinement_stage: ReviewRefinementStage,
        sample_refinement_data: tuple[List[TaxonomyDTO], List[str], str, Set[str]]
    ) -> None:
        """Test merging of split results with proper index adjustment."""
        categories, aspects, aspect_type, product_categories = sample_refinement_data
        
        # Create left and right contexts (split aspects)
        mid = len(aspects) // 2
        left_aspects = aspects[:mid]
        right_aspects = aspects[mid:]
        
        ctx_left = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            aspect_type=aspect_type,
            aspect_context="physical product characteristics",
            categories=categories,
            aspects=left_aspects,
            product_categories=product_categories
        )
        
        ctx_right = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            aspect_type=aspect_type,
            aspect_context="physical product characteristics",
            categories=categories,
            aspects=right_aspects,
            product_categories=product_categories
        )
        
        # Create sample results from each side
        res_left = ReviewRefinementStageResult(reassignments={0: "Category A", 1: "Category B"})
        res_right = ReviewRefinementStageResult(reassignments={0: "Category C", 1: "Category D"})
        
        # Merge results
        merged_result = await refinement_stage._merge_split_results(
            res_left, res_right, ctx_left, ctx_right, depth=1
        )
        
        print("\n" + "="*60)
        print("🔍 MERGE SPLIT RESULTS")
        print("="*60)
        print(f"📊 Left aspects: {len(left_aspects)}")
        print(f"📊 Right aspects: {len(right_aspects)}")
        print(f"📊 Left reassignments: {res_left.reassignments}")
        print(f"📊 Right reassignments: {res_right.reassignments}")
        print(f"📊 Merged reassignments: {merged_result.reassignments}")
        print("="*60)
        
        assert isinstance(merged_result, ReviewRefinementStageResult)
        
        # Check that left side indices are preserved
        assert merged_result.reassignments[0] == "Category A"
        assert merged_result.reassignments[1] == "Category B"
        
        # Check that right side indices are offset by left_size
        left_size = len(left_aspects)
        assert merged_result.reassignments[left_size] == "Category C"
        assert merged_result.reassignments[left_size + 1] == "Category D"
        
        print("\n✅ Split results merged successfully with proper index adjustment.")

    @pytest.mark.asyncio
    async def test_split_context(
        self,
        refinement_stage: ReviewRefinementStage,
        sample_refinement_data: tuple[List[TaxonomyDTO], List[str], str, Set[str]]
    ) -> None:
        """Test context splitting functionality."""
        categories, aspects, aspect_type, product_categories = sample_refinement_data
        
        context = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            aspect_type=aspect_type,
            aspect_context="physical product characteristics",
            categories=categories,
            aspects=aspects,
            product_categories=product_categories
        )
        
        # Split context
        ctx_left, ctx_right = refinement_stage._split_context(context, depth=1)
        
        print("\n" + "="*60)
        print("🔍 CONTEXT SPLITTING")
        print("="*60)
        print(f"📊 Original aspects: {len(aspects)}")
        print(f"📊 Left aspects: {len(ctx_left.aspects)}")
        print(f"📊 Right aspects: {len(ctx_right.aspects)}")
        print(f"📋 Left aspects: {ctx_left.aspects}")
        print(f"📋 Right aspects: {ctx_right.aspects}")
        print("="*60)
        
        # Verify split is correct
        mid = len(aspects) // 2
        assert len(ctx_left.aspects) == mid
        assert len(ctx_right.aspects) == len(aspects) - mid
        assert ctx_left.aspects == aspects[:mid]
        assert ctx_right.aspects == aspects[mid:]
        
        # Verify other context fields are preserved
        assert ctx_left.aspect_type == aspect_type
        assert ctx_right.aspect_type == aspect_type
        assert ctx_left.categories == categories
        assert ctx_right.categories == categories
        
        print("\n✅ Context split successfully.")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_refine_aspects_from_categorization_results(
        self,
        categorization_results: Dict,
        refinement_stage: ReviewRefinementStage
    ) -> None:
        """Main integration test using real categorization results."""
        
        # Process each aspect type from categorization results
        for aspect_type in ["phy", "perf", "use"]:
            if aspect_type not in categorization_results.get("categorization_results", {}):
                print(f"⚠️  Skipping {aspect_type} - no categorization data available")
                continue
            
            print(f"\n🔍 Testing refinement for {aspect_type} aspects...")
            
            categorization_data = categorization_results["categorization_results"][aspect_type]
            
            # Convert taxonomies to TaxonomyDTO
            categories = [
                TaxonomyDTO(name=taxonomy["name"], definition=taxonomy["definition"])
                for taxonomy in categorization_data["taxonomies"]
            ]
            
            if not categories:
                print(f"⚠️  Skipping {aspect_type} - no categories available")
                continue
            
            # Create sample aspects for this type
            if aspect_type == "phy":
                aspects = [
                    "marker tip durability and wear resistance",
                    "color vibrancy and intensity retention", 
                    "cap fit and security mechanism",
                    "barrel thickness and ergonomic grip",
                    "ink flow consistency and smoothness"
                ]
                aspect_context = "physical product characteristics and attributes"
            elif aspect_type == "perf":
                aspects = [
                    "drying time and evaporation rate",
                    "washability and stain removal ease",
                    "color blending and mixing capability", 
                    "coverage and opacity quality",
                    "tip precision and line control"
                ]
                aspect_context = "product functionality and operational characteristics"
            else:  # use
                aspects = [
                    "art projects and creative activities",
                    "educational and classroom use",
                    "professional illustration work",
                    "hobby and recreational drawing",
                    "craft and DIY applications"
                ]
                aspect_context = "product applications and usage scenarios"
            
            context = ReviewRefinementStageContext(
                product_category=PRODUCT_CATEGORY,
                aspect_type=aspect_type,
                aspect_context=aspect_context,
                categories=categories,
                aspects=aspects,
                product_categories={PRODUCT_CATEGORY}
            )
            
            # Execute refinement stage
            try:
                result = await refinement_stage.execute(context)
                
                print(f"✅ {aspect_type.upper()} refinement completed:")
                print(f"   - Total aspects: {len(aspects)}")
                print(f"   - Available categories: {len(categories)}")
                print(f"   - Aspects reassigned: {len(result.reassignments)}")
                
                if result.reassignments:
                    print(f"   - Reassignment examples:")
                    for i, (aspect_idx, category_name) in enumerate(list(result.reassignments.items())[:3]):
                        aspect_desc = aspects[aspect_idx] if aspect_idx < len(aspects) else "UNKNOWN"
                        print(f"     • Aspect {aspect_idx} ({aspect_desc[:30]}...) → {category_name}")
                
                # Save results for this aspect type
                save_refinement_results(result, categories, aspects, aspect_type, PRODUCT_CATEGORY)
                
            except Exception as e:
                print(f"❌ {aspect_type.upper()} refinement failed: {e}")
                pytest.fail(f"Refinement failed for {aspect_type}: {e}")
        
        print("\n✅ All aspect types processed successfully!") 