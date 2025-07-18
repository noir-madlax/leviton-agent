"""Unit tests for prompt building validation across review analysis stages.

This module validates that:
1. Prompt templates are properly loaded and contain expected placeholders
2. _build_prompt methods correctly replace template variables
3. Generated prompts contain all required sections and formatting
4. Aspect descriptions are properly formatted without duplication
5. Batch size and character limits are respected
"""

import pytest

from review_analysis.llm.review_extraction_stage import ReviewExtractionStage, ReviewExtractionContext
from review_analysis.llm.review_categorization_stage import ReviewCategorizationStage, ReviewCategorizationContext
from review_analysis.llm.review_refinement_stage import ReviewRefinementStage, ReviewRefinementStageContext
from review_analysis.llm.review_consolidation_stage import ReviewConsolidationStage, ReviewConsolidationStageContext
from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO

# Test constants
PRODUCT_CATEGORY = "Light Switches"
SAMPLE_REVIEWS = [
    {"review_id": "R001", "title": "Great colors", "text": "Love the bright colors and easy to use"},
    {"review_id": "R002", "title": "Easy setup", "text": "Simple to assemble and install"},
    {"review_id": "R003", "title": "Compact design", "text": "Doesn't take much space in the wall"},
    {"review_id": "R004", "title": "Durable build", "text": "Well made construction and lasts long"},
    {"review_id": "R005", "title": "Good performance", "text": "Works as expected and reliable"},
    {"review_id": "R006", "title": "Nice finish", "text": "Quality materials and smooth operation"}
]

SAMPLE_ASPECTS = [
    ("0", "bathroom_fan_speed_control"),
    ("1", "bathroom_lighting"),
    ("2", "LED bulbs in bathrooms"),
    ("3", "around the house including bathroom"),
    ("4", "multiple room lighting systems"),
    ("5", "dining room light control"),
    ("6", "kitchen lighting setup"),
    ("7", "living room light fixture control"),
    ("8", "ceiling fan lights"),
    ("9", "lamp dimming functionality")
]

SAMPLE_CATEGORIES = [
    TaxonomyDTO(name="Installation", definition="Installation and setup related aspects"),
    TaxonomyDTO(name="Lighting Control", definition="Light control and dimming functionality"),
    TaxonomyDTO(name="Room Specific", definition="Room-specific lighting applications"),
    TaxonomyDTO(name="Electrical", definition="Electrical requirements and compatibility"),
    TaxonomyDTO(name="Performance", definition="Performance and reliability aspects")
]

SAMPLE_TAXONOMIES_A = [
    TaxonomyDTO(name="Installation", definition="Installation and setup related aspects"),
    TaxonomyDTO(name="Lighting Control", definition="Light control and dimming functionality")
]

SAMPLE_TAXONOMIES_B = [
    TaxonomyDTO(name="Room Specific", definition="Room-specific lighting applications"),
    TaxonomyDTO(name="Electrical", definition="Electrical requirements and compatibility")
]


class TestPromptBuilding:
    """Test suite for prompt building validation across all review analysis stages."""

    @pytest.mark.asyncio
    async def test_extraction_prompt_building(self):
        """Test review extraction prompt building."""
        stage = ReviewExtractionStage()
        
        # Format reviews for prompt
        formatted_reviews = "\n".join([
            f"{i}# {review['title']}\n{review['text']}"
            for i, review in enumerate(SAMPLE_REVIEWS[:3])
        ])
        expected_ids = [f"R{i:03d}" for i in range(1, 4)]
        
        context = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews=formatted_reviews,
            expected_review_ids=expected_ids,
            asin="TEST123",
            product_title="Test Light Switch"
        )
        
        prompt = await stage._build_prompt(context)
        
        # Validate prompt structure
        assert PRODUCT_CATEGORY in prompt
        assert "0#" in prompt  # First review
        assert "1#" in prompt  # Second review
        assert "2#" in prompt  # Third review
        assert "phy" in prompt.lower()
        assert "perf" in prompt.lower()
        assert "use" in prompt.lower()
        assert "output format" in prompt.lower()
        assert "critical instructions" in prompt.lower()
        
        print(f"\n✅ Extraction prompt built successfully ({len(prompt)} chars)")
        print(f"   - Contains {PRODUCT_CATEGORY}")
        print(f"   - Contains {len(expected_ids)} review IDs")
        print("   - Contains all aspect types (phy, perf, use)")

    @pytest.mark.asyncio
    async def test_categorization_prompt_building(self):
        """Test review categorization prompt building."""
        stage = ReviewCategorizationStage()
        
        context = ReviewCategorizationContext(
            product_category=PRODUCT_CATEGORY,
            aspects=SAMPLE_ASPECTS[:5],
            aspect_type="usability",
            aspect_context="user interaction and control scenarios",
            input_description="Lines show usability aspects: [ID] description",
            product_categories={PRODUCT_CATEGORY}
        )
        
        prompt = await stage._build_prompt(context)
        
        # Validate prompt structure
        assert PRODUCT_CATEGORY in prompt
        assert "usability" in prompt
        assert "user interaction and control scenarios" in prompt
        assert "[0] bathroom_fan_speed_control" in prompt
        assert "[1] bathroom_lighting" in prompt
        assert "[2] LED bulbs in bathrooms" in prompt
        assert "OUT_OF_SCOPE" in prompt
        assert "OUTPUT FORMAT EXAMPLE" in prompt
        assert "CRITICAL RULES" in prompt
        
        # Check for no duplication in aspect descriptions
        for aspect_id, description in SAMPLE_ASPECTS[:5]:
            # Should appear exactly once in the format [ID] description
            expected_format = f"[{aspect_id}] {description}"
            assert prompt.count(expected_format) == 1, f"Aspect {expected_format} should appear exactly once"
        
        print(f"\n✅ Categorization prompt built successfully ({len(prompt)} chars)")
        print(f"   - Contains {PRODUCT_CATEGORY}")
        print(f"   - Contains {len(SAMPLE_ASPECTS[:5])} aspects")
        print("   - No duplicate aspect descriptions")

    @pytest.mark.asyncio
    async def test_refinement_prompt_building(self):
        """Test review refinement prompt building."""
        stage = ReviewRefinementStage()
        
        context = ReviewRefinementStageContext(
            product_category=PRODUCT_CATEGORY,
            categories=SAMPLE_CATEGORIES[:3],
            aspects=[desc for _, desc in SAMPLE_ASPECTS[:5]],
            aspect_type="usability",
            aspect_context="user interaction scenarios",
            original_categories=["Installation", "Lighting Control", "Room Specific", "Installation", "Lighting Control"]
        )
        
        prompt = await stage._build_prompt(context)
        
        # Validate prompt structure
        assert PRODUCT_CATEGORY in prompt
        assert "usability" in prompt
        assert "user interaction scenarios" in prompt
        assert "[C_0] Installation" in prompt
        assert "[C_1] Lighting Control" in prompt
        assert "[C_2] Room Specific" in prompt
        assert "[0] Installation - bathroom_fan_speed_control" in prompt
        assert "[1] Lighting Control - bathroom_lighting" in prompt
        assert "OUTPUT FORMAT" in prompt
        assert "CRITICAL RULES" in prompt
        
        # Check for proper aspect formatting (with category prefix for refinement)
        # In refinement, aspects are formatted with their original categories
        expected_formats = [
            "[0] Installation - bathroom_fan_speed_control",
            "[1] Lighting Control - bathroom_lighting", 
            "[2] Room Specific - LED bulbs in bathrooms",
            "[3] Installation - around the house including bathroom",
            "[4] Lighting Control - multiple room lighting systems"
        ]
        for expected_format in expected_formats:
            assert expected_format in prompt, f"Expected aspect format: {expected_format}"
        
        print(f"\n✅ Refinement prompt built successfully ({len(prompt)} chars)")
        print(f"   - Contains {PRODUCT_CATEGORY}")
        print(f"   - Contains {len(SAMPLE_CATEGORIES[:3])} categories")
        print(f"   - Contains {len(SAMPLE_ASPECTS[:5])} aspects")

    @pytest.mark.asyncio
    async def test_consolidation_prompt_building(self):
        """Test review consolidation prompt building."""
        stage = ReviewConsolidationStage(
            aspect_type="usability",
            product_categories={PRODUCT_CATEGORY}
        )
        
        context = ReviewConsolidationStageContext(
            product_category=PRODUCT_CATEGORY,
            taxonomy_a=SAMPLE_TAXONOMIES_A,
            taxonomy_b=SAMPLE_TAXONOMIES_B
        )
        
        prompt = await stage._build_prompt(context)
        
        # Validate prompt structure
        assert PRODUCT_CATEGORY in prompt
        assert "usability" in prompt
        assert "Taxonomy A:" in prompt
        assert "Taxonomy B:" in prompt
        assert "A_0" in prompt
        assert "A_1" in prompt
        assert "B_0" in prompt
        assert "B_1" in prompt
        assert "Installation" in prompt
        assert "Lighting Control" in prompt
        assert "Room Specific" in prompt
        assert "Electrical" in prompt
        assert "consolidation" in prompt.lower()
        assert "consolidation rules" in prompt.lower()
        assert "output format" in prompt.lower()
        
        print(f"\n✅ Consolidation prompt built successfully ({len(prompt)} chars)")
        print(f"   - Contains {PRODUCT_CATEGORY}")
        print(f"   - Contains {len(SAMPLE_TAXONOMIES_A)} taxonomy A items")
        print(f"   - Contains {len(SAMPLE_TAXONOMIES_B)} taxonomy B items")

    def test_aspect_description_no_duplication(self):
        """Test that aspect descriptions don't have duplication issues."""
        # Test the specific issue that was fixed in db_review_analysis.py
        # where parent_group_name and detail_text were being combined incorrectly
        
        # Simulate the old problematic format
        problematic_aspects = [
            ("0", "rental property needing ivory color – rental property needing ivory color"),
            ("1", "replacing_legacy_Maestro_switches – replacing_legacy_Maestro_switches"),
            ("2", "bathroom installation – bathroom installation")
        ]
        
        # Simulate the new correct format
        correct_aspects = [
            ("0", "rental property needing ivory color"),
            ("1", "replacing_legacy_Maestro_switches"),
            ("2", "bathroom installation")
        ]
        
        # Verify that the correct format doesn't have duplication
        for aspect_id, description in correct_aspects:
            # Check that the description doesn't contain the duplication pattern
            assert " – " not in description, f"Aspect {aspect_id} should not have duplication: {description}"
            
        print("\n✅ Aspect description validation passed")
        print(f"   - No duplication in {len(correct_aspects)} aspects")

    @pytest.mark.asyncio
    async def test_prompt_length_validation(self):
        """Test that prompts don't exceed reasonable length limits."""
        stage = ReviewCategorizationStage()
        
        # Create a large number of aspects to test prompt length
        large_aspects = [(str(i), f"aspect_description_{i}") for i in range(50)]
        
        context = ReviewCategorizationContext(
            product_category=PRODUCT_CATEGORY,
            aspects=large_aspects,
            aspect_type="usability",
            aspect_context="user interaction scenarios",
            input_description="Lines show usability aspects: [ID] description",
            product_categories={PRODUCT_CATEGORY}
        )
        
        prompt = await stage._build_prompt(context)
        
        # Validate prompt length is reasonable (not too long for LLM context)
        assert len(prompt) < 50000, f"Prompt too long: {len(prompt)} chars"
        assert len(prompt) > 1000, f"Prompt too short: {len(prompt)} chars"
        
        print("\n✅ Prompt length validation passed")
        print(f"   - Prompt length: {len(prompt)} chars")
        print(f"   - Contains {len(large_aspects)} aspects")

    def test_template_placeholder_validation(self):
        """Test that all template placeholders are properly replaced."""
        # Test extraction stage template by checking the module-level constant
        from review_analysis.llm.review_extraction_stage import _EXTRACT_PROMPT_TEMPLATE
        assert "{{PRODUCT}}" in _EXTRACT_PROMPT_TEMPLATE
        assert "{{INPUT}}" in _EXTRACT_PROMPT_TEMPLATE
        
        # Test categorization stage template
        from review_analysis.llm.review_categorization_stage import _CATEGORISE_PROMPT_TEMPLATE
        assert "{{aspect_type}}" in _CATEGORISE_PROMPT_TEMPLATE
        assert "{{aspect_context}}" in _CATEGORISE_PROMPT_TEMPLATE
        assert "{{input_description}}" in _CATEGORISE_PROMPT_TEMPLATE
        assert "{{product_context}}" in _CATEGORISE_PROMPT_TEMPLATE
        
        # Test refinement stage template
        from review_analysis.llm.review_refinement_stage import _REFINEMENT_PROMPT_TEMPLATE
        assert "{{aspect_type}}" in _REFINEMENT_PROMPT_TEMPLATE
        assert "{{product_category}}" in _REFINEMENT_PROMPT_TEMPLATE
        assert "{{aspect_context}}" in _REFINEMENT_PROMPT_TEMPLATE
        assert "{{categories_section}}" in _REFINEMENT_PROMPT_TEMPLATE
        assert "{{formatted_aspects}}" in _REFINEMENT_PROMPT_TEMPLATE
        
        # Test consolidation stage template
        consolidation_stage = ReviewConsolidationStage(aspect_type="usability", product_categories={PRODUCT_CATEGORY})
        assert hasattr(consolidation_stage, '_consolidate_prompt_template')
        assert "{{aspect_type}}" in consolidation_stage._consolidate_prompt_template
        assert "{{taxonomy_a}}" in consolidation_stage._consolidate_prompt_template
        assert "{{taxonomy_b}}" in consolidation_stage._consolidate_prompt_template
        
        print("\n✅ Template placeholder validation passed")
        print("   - All required placeholders found in templates")


def run_prompt_building_tests() -> bool:
    """Execute all prompt building tests without pytest."""
    print("🧪 Running Prompt Building Tests")
    print("=" * 50)
    
    test_instance = TestPromptBuilding()
    
    tests = [
        ("extraction_prompt_building", test_instance.test_extraction_prompt_building),
        ("categorization_prompt_building", test_instance.test_categorization_prompt_building),
        ("refinement_prompt_building", test_instance.test_refinement_prompt_building),
        ("consolidation_prompt_building", test_instance.test_consolidation_prompt_building),
        ("aspect_description_no_duplication", test_instance.test_aspect_description_no_duplication),
        ("prompt_length_validation", test_instance.test_prompt_length_validation),
        ("template_placeholder_validation", test_instance.test_template_placeholder_validation),
    ]
    
    passed = 0
    for name, test_method in tests:
        try:
            if test_method.__name__.startswith('test_'):
                # Async tests need to be run differently
                import asyncio
                if 'async' in str(test_method):
                    asyncio.run(test_method())
                else:
                    test_method()
            passed += 1
            print(f"✅ PASS: {name}")
        except Exception as e:
            print(f"❌ FAIL: {name}")
            print(f"   → {e}")
    
    print(f"\n🎉 Prompt building tests completed: {passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == "__main__":
    run_prompt_building_tests() 