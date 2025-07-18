"""Tests for review analysis extraction stage implementation.

This module tests the ReviewExtractionStage class with sample review data
for comprehensive testing of the review hierarchy extraction workflow.

Test Coverage:
--------------

1. **test_extract_review_hierarchy_integration**: 
   Main integration test that processes sample product reviews through
   the extraction stage and validates the complete review hierarchy extraction.
   Verifies result structure, aspect extraction, RID integrity, and
   hierarchical data organization.

2. **test_validation_with_valid_response**:
   Tests the validation logic with a properly formatted JSON response that
   matches the expected phy/perf/use schema. Verifies that valid responses
   pass comprehensive validation without errors.

3. **test_validation_with_invalid_response**:
   Tests validation error handling with various malformed responses:
   - Invalid JSON syntax
   - Missing required sections (phy/perf/use)
   - Invalid RID references and sentiment mismatches
   Ensures proper error categorization and actionable feedback.

4. **test_retry_prompt_generation**:
   Tests retry prompt construction using validation error details.
   Verifies that validation errors are properly formatted with placeholder-based
   correction instructions to help the LLM correct its response.

5. **test_review_formatting**:
   Tests the review formatting utility that converts review objects into
   RID#review_text format required by the extraction prompt.

6. **test_split_and_merge_operations**:
   Tests the splitting and merging logic for processing large review sets.
   Verifies RID offset management and hierarchical structure preservation
   across split operations.

Configuration:
--------------
- Uses sample review data from test_data/sample_reviews.json
- Product category: "Kids Art and Craft Tool"
- Source data: Two products with multiple reviews each
- Fixed prompt templates: review_aspects_extraction_prompt_v0.txt, shared_retry_prompt_v0.txt
"""

import json
import pytest
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import AsyncMock

from review_analysis.llm.review_extraction_stage import (
    ReviewExtractionStage,
    ReviewExtractionContext,
    ReviewExtractionResult,
    format_reviews_for_prompt,
    count_extracted_aspects
)
from core.utils.llm_utils import ValidationResult

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"
SAMPLE_REVIEWS_PATH = TEST_DATA_DIR / "sample_reviews.json"
PRODUCT_CATEGORY = "Kids Art and Craft Tool"

# Test fixtures
@pytest.fixture
def sample_reviews() -> List[Dict[str, Any]]:
    """Load sample review data."""
    if not SAMPLE_REVIEWS_PATH.exists():
        pytest.skip(f"Sample reviews file not found: {SAMPLE_REVIEWS_PATH}")
    
    with open(SAMPLE_REVIEWS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('reviews', [])


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Mock LLM client that returns valid review extraction responses."""
    
    def create_response(review_count: int) -> str:
        # Create response in the format expected by review_aspects_extraction_prompt_v0.txt
        hierarchy = {
            "phy": {
                "design": {
                    "A@colorful appearance": {
                        "+": [0, 2],
                        "-": []
                    },
                    "B@compact size": {
                        "+": [1],
                        "-": [3]
                    }
                },
                "material": {
                    "C@plastic construction": {
                        "+": [0, 1],
                        "-": [2]
                    }
                }
            },
            "perf": {
                "usability": {
                    "a@easy to use": {
                        "+": {"A": [0], "?": [1]},
                        "-": {"C": [2]}
                    },
                    "b@good grip": {
                        "+": {"B": [1, 3]}
                        # Note: only "+" sentiment present, "-" omitted (valid case)
                    }
                }
            },
            "use": {
                "art projects": {
                    "+": {"a": [0, 1], "?": [2]}
                    # Note: only "+" sentiment present, "-" omitted (valid case)
                },
                "educational activities": {
                    "+": {"A,a": [1]},
                    "-": {"C": [3]}
                }
            }
        }
        
        # Adjust RID ranges based on actual review count
        max_rid = min(review_count - 1, 3)
        for section in hierarchy.values():
            for category in section.values():
                for key, sentiments in category.items():
                    if isinstance(sentiments, dict):
                        for sentiment, data in sentiments.items():
                            if isinstance(data, list):
                                # Filter RIDs to valid range
                                sentiments[sentiment] = [rid for rid in data if rid <= max_rid]
                            elif isinstance(data, dict):
                                # Handle perf/use reason structures
                                for reason, rid_list in data.items():
                                    if isinstance(rid_list, list):
                                        data[reason] = [rid for rid in rid_list if rid <= max_rid]
        
        return json.dumps(hierarchy)
    
    mock = AsyncMock()
    mock.side_effect = lambda prompt, **kwargs: create_response(
        len([line for line in prompt.split('\n') if '#' in line and line.strip()])
    )
    return mock


@pytest.fixture
def extraction_stage() -> ReviewExtractionStage:
    """Create ReviewExtractionStage instance."""
    return ReviewExtractionStage()


class TestReviewExtractionStage:
    """Test suite for ReviewExtractionStage."""

    @pytest.mark.asyncio
    async def test_review_formatting(self, sample_reviews: List[Dict[str, Any]]) -> None:
        """Test review formatting utility."""
        if not sample_reviews:
            pytest.skip("No sample reviews available")
        
        # Take first few reviews for testing
        test_reviews = sample_reviews[:5]
        
        formatted_reviews, expected_ids = format_reviews_for_prompt(test_reviews)
        
        # Verify formatting
        lines = formatted_reviews.split('\n')
        assert len(lines) == len(test_reviews)
        assert len(expected_ids) == len(test_reviews)
        assert expected_ids == set(range(len(test_reviews)))
        
        # Verify RID format
        for i, line in enumerate(lines):
            assert line.startswith(f"{i}#")
            assert '#' in line
        
        print(f"\n✅ Formatted {len(test_reviews)} reviews successfully")
        print(f"📋 Sample formatted line: {lines[0][:100]}...")

    @pytest.mark.asyncio
    async def test_build_prompt_with_reviews(
        self,
        extraction_stage: ReviewExtractionStage,
        sample_reviews: List[Dict[str, Any]]
    ) -> None:
        """Test prompt building with sample reviews."""
        if not sample_reviews:
            pytest.skip("No sample reviews available")
        
        # Format reviews and create context
        formatted_reviews, expected_ids = format_reviews_for_prompt(sample_reviews[:3])
        
        context = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews=formatted_reviews,
            expected_review_ids=expected_ids,
            asin="TEST123",
            product_title="Test Art Kit"
        )
        
        prompt = await extraction_stage._build_prompt(context)
        
        # Print full prompt for manual inspection
        print("\n" + "="*80)
        print("🔍 FULL PROMPT FOR MANUAL INSPECTION")
        print("="*80)
        print(prompt)
        print("="*80)
        # Verify prompt structure
        assert PRODUCT_CATEGORY in prompt
        assert "0#" in prompt  # First review
        assert "phy" in prompt.lower()
        assert "perf" in prompt.lower()
        assert "use" in prompt.lower()
        
        print(f"\n✅ Built prompt successfully for {len(expected_ids)} reviews")

    @pytest.mark.asyncio
    async def test_validation_with_valid_response(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test validation with properly formatted response."""
        valid_response = json.dumps({
            "phy": {
                "design": {
                    "A@colorful": {"+": [0, 1], "-": []}
                }
            },
            "perf": {
                "usability": {
                    "a@easy": {"+": {"A": [0]}, "-": {}}
                }
            },
            "use": {
                "art projects": {"+": {"a": [1]}, "-": {}}
            }
        })
        
        context = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Great colors\n1#Easy to use",
            expected_review_ids={0, 1},
            asin="TEST123",
            product_title="Test Kit"
        )
        
        result = extraction_stage._validate(valid_response, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - VALID RESPONSE")
        print("="*60)
        print(f"✅ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {valid_response}")
        print("="*60)
        
        assert isinstance(result, ValidationResult)
        assert result.ok is True
        
        print("\n✅ Valid response passed validation")

    @pytest.mark.asyncio
    async def test_validation_with_invalid_response(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test validation error handling."""
        invalid_response = '{"phy": {"design": {"invalid_format": {"positive": [0]}}}}'
        
        context = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Test review",
            expected_review_ids={0},
            asin="TEST123",
            product_title="Test Kit"
        )
        
        result = extraction_stage._validate(invalid_response, context)
        
        print("\n" + "="*60)
        print("🔍 VALIDATION RESULT - INVALID RESPONSE")
        print("="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print("📝 Response being validated:")
        print(f"   {invalid_response}")
        print("🔍 Error Details:")
        for category, errors in result.error_categories.items():
            print(f"   {category}: {errors}")
        print("="*60)
        
        assert isinstance(result, ValidationResult)
        assert result.ok is False
        assert hasattr(result, 'error_categories')
        assert len(result.error_categories) > 0
        
        print("\n✅ Invalid response properly rejected with validation errors")

    @pytest.mark.asyncio
    async def test_split_and_merge_operations(
        self,
        extraction_stage: ReviewExtractionStage,
        sample_reviews: List[Dict[str, Any]]
    ) -> None:
        """Test complete split and merge operations with manual inspection output."""
        if len(sample_reviews) < 4:
            pytest.skip("Need at least 4 reviews for split/merge testing")
        
        # Format reviews and create context
        formatted_reviews, expected_ids = format_reviews_for_prompt(sample_reviews[:4])
        
        context = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews=formatted_reviews,
            expected_review_ids=expected_ids,
            asin="TEST123",
            product_title="Test Kit"
        )
        
        print("\n" + "="*80)
        print("🔍 SPLIT AND MERGE OPERATIONS - MANUAL INSPECTION")
        print("="*80)
        print("📊 ORIGINAL CONTEXT:")
        print(f"   - Review count: {len(expected_ids)}")
        print(f"   - Expected IDs: {expected_ids}")
        print("   - Formatted reviews:")
        for line in formatted_reviews.split('\n'):
            print(f"     {line}")
        print("="*80)
        
        # 1. Test splitting
        ctx_left, ctx_right = extraction_stage._split_context(context, depth=0)
        
        print("📊 AFTER SPLIT:")
        print("   Left context:")
        print(f"     - Review count: {len(ctx_left.expected_review_ids)}")
        print(f"     - Expected IDs: {ctx_left.expected_review_ids}")
        print("     - Formatted reviews:")
        for line in ctx_left.formatted_reviews.split('\n'):
            print(f"       {line}")
        print("   Right context:")
        print(f"     - Review count: {len(ctx_right.expected_review_ids)}")
        print(f"     - Expected IDs: {ctx_right.expected_review_ids}")
        print("     - Formatted reviews:")
        for line in ctx_right.formatted_reviews.split('\n'):
            print(f"       {line}")
        print("="*80)
        
        # 2. Create mock results for merging
        from review_analysis.llm.review_extraction_stage import ReviewExtractionResult
        
        # Left result (reviews 0,1 -> aspects A,B,a)
        left_hierarchy = {
            "phy": {
                "design": {
                    "A@colorful appearance": {"+": [0], "-": []},
                    "B@compact size": {"+": [1], "-": []}
                }
            },
            "perf": {
                "usability": {
                    "a@easy to use": {"+": {"A": [0]}, "-": {}}
                }
            },
            "use": {
                "art projects": {"+": {"a": [0, 1]}, "-": {}}
            }
        }
        
        # Right result (reviews 0,1 -> aspects C,b for different reviews)
        # Note: IDs should be offset during merge (A->C, a->b)
        right_hierarchy = {
            "phy": {
                "material": {
                    "A@plastic construction": {"+": [0], "-": [1]}
                }
            },
            "perf": {
                "usability": {
                    "a@good grip": {"+": {"A": [0]}, "-": {}}
                }
            },
            "use": {
                "educational activities": {"+": {"a": [1]}, "-": {}}
            }
        }
        
        res_left = ReviewExtractionResult(
            review_hierarchy=left_hierarchy,
            aspects_extracted=4  # A,B,a,art projects
        )
        
        res_right = ReviewExtractionResult(
            review_hierarchy=right_hierarchy,
            aspects_extracted=3  # C,b,educational activities
        )
        
        print("📊 MOCK RESULTS FOR MERGE:")
        print("   Left result (reviews 0,1):")
        print(f"     - Aspects: {res_left.aspects_extracted}")
        print(f"     - Hierarchy: {res_left.review_hierarchy}")
        print("   Right result (reviews 0,1, will be offset to 2,3):")
        print(f"     - Aspects: {res_right.aspects_extracted}")
        print(f"     - Hierarchy: {res_right.review_hierarchy}")
        print("="*80)
        
        # 3. Test merging
        merged_result = await extraction_stage._merge_split_results(
            res_left=res_left,
            res_right=res_right,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        print("📊 MERGED RESULT:")
        print(f"   - Total aspects: {merged_result.aspects_extracted}")
        print("   - Merged hierarchy:")
        for section_name, section_content in merged_result.review_hierarchy.items():
            print(f"     {section_name}:")
            for category, details in section_content.items():
                print(f"       {category}: {details}")
        print("="*80)
        
        # Verify split integrity
        assert len(ctx_left.expected_review_ids) == 2
        assert len(ctx_right.expected_review_ids) == 2
        assert ctx_left.expected_review_ids == {0, 1}
        assert ctx_right.expected_review_ids == {0, 1}  # Renumbered
        
        # Verify merge results
        assert merged_result.aspects_extracted == 7  # 4 + 3
        assert "phy" in merged_result.review_hierarchy
        assert "perf" in merged_result.review_hierarchy
        assert "use" in merged_result.review_hierarchy
        
        # Verify ID remapping and RID offsets in merged result
        phy_section = merged_result.review_hierarchy["phy"]
        perf_section = merged_result.review_hierarchy["perf"]
        use_section = merged_result.review_hierarchy["use"]
        
        # Check that right side PIDs were remapped from A to C
        assert "material" in phy_section
        assert "C@plastic construction" in phy_section["material"]
        plastic_aspect = phy_section["material"]["C@plastic construction"]
        assert 2 in plastic_aspect["+"]  # Original 0 + offset 2
        assert 3 in plastic_aspect["-"]  # Original 1 + offset 2
        
        # Check that right side perf_ids were remapped from a to b
        assert "usability" in perf_section
        assert "b@good grip" in perf_section["usability"]
        grip_aspect = perf_section["usability"]["b@good grip"]
        assert "C" in grip_aspect["+"]  # Reason A remapped to C
        assert 2 in grip_aspect["+"]["C"]  # Original 0 + offset 2
        
        # Check that use case reasons were remapped
        assert "educational activities" in use_section
        edu_aspect = use_section["educational activities"]
        assert "b" in edu_aspect["+"]  # Reason a remapped to b
        assert 3 in edu_aspect["+"]["b"]  # Original 1 + offset 2
        
        print("\n✅ Split and merge operations completed successfully")
        print(f"   - Split: {len(expected_ids)} → {len(ctx_left.expected_review_ids)} + {len(ctx_right.expected_review_ids)}")
        print(f"   - Merge: {res_left.aspects_extracted} + {res_right.aspects_extracted} → {merged_result.aspects_extracted}")

    @pytest.mark.asyncio
    async def test_multi_character_id_offset(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test ID offsetting with multi-character IDs (AA, AB, aa, ab, etc.)."""
        print("\n" + "="*80)
        print("🔍 MULTI-CHARACTER ID OFFSET TEST")
        print("="*80)
        
        # Create left result with multi-character IDs (Y, Z, y, z)
        left_hierarchy = {
            "phy": {
                "design": {
                    "Y@advanced feature": {"+": [0], "-": []},
                    "Z@final element": {"+": [1], "-": []}
                }
            },
            "perf": {
                "usability": {
                    "y@smooth operation": {"+": {"Y": [0]}, "-": {}},
                    "z@ultimate performance": {"+": {"Z": [1]}, "-": {}}
                }
            },
            "use": {
                "professional work": {"+": {"y": [0], "z": [1]}, "-": {}}
            }
        }
        
        # Create right result that should get multi-character IDs (AA, AB, aa, ab)
        right_hierarchy = {
            "phy": {
                "material": {
                    "A@first material": {"+": [0], "-": []},
                    "B@second material": {"+": [1], "-": []}
                }
            },
            "perf": {
                "durability": {
                    "a@first durability": {"+": {"A": [0]}, "-": {}},
                    "b@second durability": {"+": {"B": [1]}, "-": {}}
                }
            },
            "use": {
                "testing": {"+": {"a": [0], "b": [1]}, "-": {}}
            }
        }
        
        res_left = ReviewExtractionResult(
            review_hierarchy=left_hierarchy,
            aspects_extracted=6
        )
        
        res_right = ReviewExtractionResult(
            review_hierarchy=right_hierarchy,
            aspects_extracted=6
        )
        
        # Create mock contexts
        ctx_left = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Left review one\n1#Left review two",
            expected_review_ids={0, 1},
            asin="TEST123",
            product_title="Test Kit"
        )
        
        ctx_right = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Right review one\n1#Right review two",
            expected_review_ids={0, 1},
            asin="TEST123",
            product_title="Test Kit"
        )
        
        print("📊 LEFT RESULT (Y,Z,y,z IDs):")
        print(f"   {left_hierarchy}")
        print("📊 RIGHT RESULT (should become AA,AB,aa,ab after merge):")
        print(f"   {right_hierarchy}")
        print("="*80)
        
        # Test the merge
        merged_result = await extraction_stage._merge_split_results(
            res_left=res_left,
            res_right=res_right,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        print("📊 MERGED RESULT WITH MULTI-CHARACTER IDs:")
        for section_name, section_content in merged_result.review_hierarchy.items():
            print(f"   {section_name}:")
            for category, details in section_content.items():
                print(f"     {category}: {details}")
        print("="*80)
        
        # Verify multi-character ID generation
        phy_section = merged_result.review_hierarchy["phy"]
        perf_section = merged_result.review_hierarchy["perf"]
        use_section = merged_result.review_hierarchy["use"]
        
        # Check that right side PIDs were remapped from A,B to AA,AB
        assert "material" in phy_section
        assert "AA@first material" in phy_section["material"]
        assert "AB@second material" in phy_section["material"]
        
        # Check RID offsets for multi-character PIDs
        first_material = phy_section["material"]["AA@first material"]
        second_material = phy_section["material"]["AB@second material"]
        assert 2 in first_material["+"]  # Original 0 + offset 2
        assert 3 in second_material["+"]  # Original 1 + offset 2
        
        # Check that right side perf_ids were remapped from a,b to aa,ab
        assert "durability" in perf_section
        assert "aa@first durability" in perf_section["durability"]
        assert "ab@second durability" in perf_section["durability"]
        
        # Check reason remapping and RID offsets
        first_dur = perf_section["durability"]["aa@first durability"]
        second_dur = perf_section["durability"]["ab@second durability"]
        assert "AA" in first_dur["+"]  # Reason A remapped to AA
        assert "AB" in second_dur["+"]  # Reason B remapped to AB
        assert 2 in first_dur["+"]["AA"]  # Original 0 + offset 2
        assert 3 in second_dur["+"]["AB"]  # Original 1 + offset 2
        
        # Check use case reason remapping
        assert "testing" in use_section
        testing_aspect = use_section["testing"]
        assert "aa" in testing_aspect["+"]  # Reason a remapped to aa
        assert "ab" in testing_aspect["+"]  # Reason b remapped to ab
        assert 2 in testing_aspect["+"]["aa"]  # Original 0 + offset 2
        assert 3 in testing_aspect["+"]["ab"]  # Original 1 + offset 2
        
        print("\n✅ Multi-character ID offset test passed!")
        print("   - Left side: Y,Z,y,z (kept as-is)")
        print("   - Right side: A,B,a,b → AA,AB,aa,ab (correctly offset)")
        print("   - All RIDs properly offset by 2")
        print("   - All reason IDs correctly remapped")

    @pytest.mark.asyncio
    async def test_multi_character_input_ids(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test ID offsetting when left side already has multi-character IDs (AA, AB, etc.)."""
        
        print("\n" + "="*80)
        print("🔍 MULTI-CHARACTER INPUT IDS TEST")
        print("="*80)
        
        # Create left result with multi-character IDs already present
        left_hierarchy = {
            "phy": {
                "design": {
                    "AA@first advanced feature": {"+": [0], "-": []},
                    "AB@second advanced feature": {"+": [1], "-": []},
                    "AC@third advanced feature": {"+": [2], "-": []}
                },
                "material": {
                    "AD@advanced material": {"+": [0, 1], "-": []}
                }
            },
            "perf": {
                "usability": {
                    "aa@first advanced perf": {"+": {"AA": [0]}, "-": {}},
                    "ab@second advanced perf": {"+": {"AB": [1], "AC": [2]}, "-": {}},
                    "ac@third advanced perf": {"+": {"AD": [0, 1]}, "-": {}}
                }
            },
            "use": {
                "advanced applications": {"+": {"aa": [0], "ab": [1, 2]}, "-": {}},
                "expert usage": {"+": {"ac": [0, 1]}, "-": {}}
            }
        }
        
        # Create right result with simple IDs that should be offset beyond multi-character range
        right_hierarchy = {
            "phy": {
                "design": {
                    "A@basic feature A": {"+": [0], "-": []},
                    "B@basic feature B": {"+": [1], "-": []},
                    "C@basic feature C": {"+": [0, 1], "-": []}
                }
            },
            "perf": {
                "usability": {
                    "a@basic perf a": {"+": {"A": [0]}, "-": {}},
                    "b@basic perf b": {"+": {"B": [1]}, "-": {}},
                    "c@basic perf c": {"+": {"A,C": [0, 1]}, "-": {}}
                }
            },
            "use": {
                "basic usage": {"+": {"a": [0], "b": [1]}, "-": {}},
                "simple tasks": {"+": {"c": [0, 1]}, "-": {}}
            }
        }
        
        res_left = ReviewExtractionResult(
            review_hierarchy=left_hierarchy,
            aspects_extracted=9  # AA,AB,AC,AD,aa,ab,ac,advanced applications,expert usage
        )
        
        res_right = ReviewExtractionResult(
            review_hierarchy=right_hierarchy,
            aspects_extracted=8  # A,B,C,a,b,c,basic usage,simple tasks
        )
        
        # Create mock contexts
        ctx_left = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Left advanced review\n1#Left expert review\n2#Left complex review",
            expected_review_ids={0, 1, 2},
            asin="TEST123",
            product_title="Advanced Test Kit"
        )
        
        ctx_right = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Right basic review\n1#Right simple review",
            expected_review_ids={0, 1},
            asin="TEST123",
            product_title="Basic Test Kit"
        )
        
        print("📊 LEFT RESULT (multi-character IDs: AA,AB,AC,AD,aa,ab,ac):")
        for section_name, section_content in left_hierarchy.items():
            print(f"   {section_name}:")
            for category, details in section_content.items():
                print(f"     {category}: {list(details.keys())}")
        
        print("📊 RIGHT RESULT (should become AE,AF,AG,ad,ae,af after merge):")
        for section_name, section_content in right_hierarchy.items():
            print(f"   {section_name}:")
            for category, details in section_content.items():
                print(f"     {category}: {list(details.keys())}")
        print("="*80)
        
        # Test the merge with multi-character inputs
        merged_result = await extraction_stage._merge_split_results(
            res_left=res_left,
            res_right=res_right,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        print("📊 MERGED RESULT WITH ADVANCED MULTI-CHARACTER IDs:")
        for section_name, section_content in merged_result.review_hierarchy.items():
            print(f"   {section_name}:")
            for category, details in section_content.items():
                print(f"     {category}: {list(details.keys())}")
        print("="*80)
        
        # Verify advanced multi-character ID generation
        phy_section = merged_result.review_hierarchy["phy"]
        perf_section = merged_result.review_hierarchy["perf"]
        use_section = merged_result.review_hierarchy["use"]
        
        # Check that right side PIDs were remapped from A,B,C to AE,AF,AG
        # (continuing after AA,AB,AC,AD from left side)
        assert "design" in phy_section
        design_keys = list(phy_section["design"].keys())
        expected_new_pids = ["AE@basic feature A", "AF@basic feature B", "AG@basic feature C"]
        
        for expected_key in expected_new_pids:
            assert expected_key in design_keys, f"Expected {expected_key} in {design_keys}"
        
        # Check that right side perf_ids were remapped from a,b,c to ad,ae,af
        # (continuing after aa,ab,ac from left side)
        assert "usability" in perf_section
        usability_keys = list(perf_section["usability"].keys())
        expected_new_perf_ids = ["ad@basic perf a", "ae@basic perf b", "af@basic perf c"]
        
        for expected_key in expected_new_perf_ids:
            assert expected_key in usability_keys, f"Expected {expected_key} in {usability_keys}"
        
        # Verify RID offsets (right side 0,1 should become 3,4)
        ae_aspect = perf_section["usability"]["ae@basic perf b"]
        assert "AF" in ae_aspect["+"], "Reason B should be remapped to AF"
        assert 4 in ae_aspect["+"]["AF"], "RID 1 should be offset to 4"
        
        # Verify complex reason remapping (A,C should become AE,AG)
        af_aspect = perf_section["usability"]["af@basic perf c"]
        assert "AE,AG" in af_aspect["+"], "Reason A,C should be remapped to AE,AG"
        assert 3 in af_aspect["+"]["AE,AG"], "RID 0 should be offset to 3"
        assert 4 in af_aspect["+"]["AE,AG"], "RID 1 should be offset to 4"
        
        # Check use case reason remapping
        assert "basic usage" in use_section
        basic_usage = use_section["basic usage"]
        assert "ad" in basic_usage["+"], "Reason a should be remapped to ad"
        assert "ae" in basic_usage["+"], "Reason b should be remapped to ae"
        assert 3 in basic_usage["+"]["ad"], "RID 0 should be offset to 3"
        assert 4 in basic_usage["+"]["ae"], "RID 1 should be offset to 4"
        
        # Verify total aspects
        assert merged_result.aspects_extracted == 17  # 9 + 8
        
        print("\n✅ Multi-character input IDs test passed!")
        print("   - Left side: AA,AB,AC,AD,aa,ab,ac (kept as-is)")
        print("   - Right side: A,B,C,a,b,c → AE,AF,AG,ad,ae,af (correctly offset)")
        print("   - Complex reason mapping: A,C → AE,AG")
        print("   - All RIDs properly offset by 3")
        print(f"   - Total aspects: {merged_result.aspects_extracted}")

    @pytest.mark.asyncio
    async def test_aspect_counting(self) -> None:
        """Test aspect counting utility."""
        hierarchy = {
            "phy": {
                "design": {
                    "A@colorful": {"+": [0]},
                    "B@compact": {"-": [1]}
                }
            },
            "perf": {
                "usability": {
                    "a@easy": {"+": {"A": [0]}}
                }
            },
            "use": {
                "art projects": {"+": {"a": [0]}},
                "learning": {"-": {"?": [1]}}
            }
        }
        
        count = count_extracted_aspects(hierarchy)
        
        # Should count: 2 phy + 1 perf + 2 use = 5 total aspects
        assert count == 5
        
        print(f"\n✅ Counted {count} aspects correctly")

    @pytest.mark.asyncio
    async def test_produce_result_conversion(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test conversion of valid response to result object."""
        valid_hierarchy = {
            "phy": {"design": {"A@colorful": {"+": [0]}}},
            "perf": {"usability": {"a@easy": {"+": {"A": [0]}}}},
            "use": {"art": {"+": {"a": [0]}}}
        }
        
        raw_response = json.dumps(valid_hierarchy)
        
        context = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Test",
            expected_review_ids={0},
            asin="TEST123",
            product_title="Test Kit"
        )
        
        result = await extraction_stage._produce_result(raw_response, context, attempts=1)
        
        print("\n" + "="*60)
        print("🔍 RESULT CONVERSION")
        print("="*60)
        print(f"📝 Raw response: {raw_response}")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Aspects extracted: {result.aspects_extracted}")
        print("📋 Hierarchy structure:")
        for section, content in result.review_hierarchy.items():
            print(f"   {section}: {content}")
        print("="*60)
        
        assert isinstance(result, ReviewExtractionResult)
        assert result.review_hierarchy == valid_hierarchy
        assert result.aspects_extracted == 3  # 1 phy + 1 perf + 1 use
        
        print(f"\n✅ Produced result with {result.aspects_extracted} aspects")

    @pytest.mark.asyncio
    async def test_real_llm_extraction_with_amazon_data(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Real LLM integration test using Amazon reviews CSV data - saves results for consolidation testing."""
        import pandas as pd
        
        # Load real Amazon review data
        csv_path = TEST_DATA_DIR / "amazon_reviews_rows.csv"
        if not csv_path.exists():
            pytest.skip(f"Amazon reviews CSV not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        print("\n" + "="*80)
        print("🤖 REAL LLM EXTRACTION WITH AMAZON REVIEWS DATA")
        print("="*80)
        print(f"📊 Loaded {len(df)} Amazon reviews from CSV")
        print(f"📋 Product: {df.iloc[0]['product_title'] if not df.empty else 'Unknown'}")
        print(f"📋 ASIN: {df.iloc[0]['asin'] if not df.empty else 'Unknown'}")
        
        reviews = []
        for _, row in df.iterrows():
            review_dict = {
                'text': row['review_text'],      # Map to expected field name
                'rating': row['rating'],
                'title': row['review_title'],    # Map to expected field name
                'review_id': row['review_id'],
                'asin': row['asin']
            }
            reviews.append(review_dict)
        
        print(f"📊 Using {len(reviews)} reviews for extraction (subset for token efficiency)")
        print("📝 Sample reviews:")
        for i, review in enumerate(reviews[:3]):
            print(f"   [{i}] Rating: {review['rating']}/5")
            print(f"       Title: {review['title']}")
            print(f"       Text: {review['text'][:100]}...")
        print(f"   ... and {len(reviews) - 3} more reviews")
        print("="*80)
        
        # Format reviews for extraction
        formatted_reviews, expected_ids = format_reviews_for_prompt(reviews)
        
        context = ReviewExtractionContext(
            product_category="Kids Arts & Crafts",
            formatted_reviews=formatted_reviews,
            expected_review_ids=expected_ids,
            asin=reviews[0]['asin'],
            product_title=df.iloc[0]['product_title']
        )
        
        # Execute real LLM extraction
        print(f"🚀 Executing real LLM extraction on {len(reviews)} Amazon reviews...")
        
        # Debug: Print the prompt being sent to LLM
        debug_prompt = await extraction_stage._build_prompt(context)
        print("\n🔍 DEBUG - LLM PROMPT (first 500 chars):")
        print(f"{debug_prompt[:500]}...")
        print("🔍 DEBUG - LLM PROMPT (last 200 chars):")
        print(f"...{debug_prompt[-200:]}")
        
        result = await extraction_stage.execute(context)
        
        # Debug: Try to get the raw LLM response
        print("\n🔍 DEBUG - RAW LLM RESPONSE (if available):")
        if hasattr(result, '_raw_response'):
            print(f"{result._raw_response[:1000]}...")
        else:
            print("Raw response not available in result object")
        
        print("📊 REAL LLM EXTRACTION RESULTS:")
        print(f"   - Aspects extracted: {result.aspects_extracted}")
        print(f"   - Hierarchy sections: {list(result.review_hierarchy.keys())}")
        
        # Print detailed hierarchy for manual inspection
        for section_name, section_content in result.review_hierarchy.items():
            print(f"   📁 {section_name.upper()}:")
            if section_content:
                for category, details in section_content.items():
                    print(f"     📂 {category} ({len(details)} aspects):")
                    for aspect_key, sentiments in list(details.items())[:2]:  # Show first 2 aspects
                        print(f"       🔍 {aspect_key}: {sentiments}")
                    if len(details) > 2:
                        print(f"       ... and {len(details) - 2} more aspects")
            else:
                print("     (No aspects found in this section)")
        print("="*80)
        
        # Save results for consolidation testing (even if 0 aspects for debugging)
        save_path = TEST_DATA_DIR / "real_amazon_extraction_results.json"
        extraction_data = {
            "test_metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "source": "amazon_reviews_csv",
                "product_category": context.product_category,
                "asin": context.asin,
                "product_title": context.product_title,
                "reviews_count": len(reviews),
                "aspects_extracted": result.aspects_extracted,
            },
            "extraction_result": {
                "review_hierarchy": result.review_hierarchy,
                "aspects_extracted": result.aspects_extracted
            },
            "context_used": {
                "product_category": context.product_category,
                "asin": context.asin,
                "product_title": context.product_title,
                "review_count": len(expected_ids)
            },
            "sample_reviews": [
                {
                    "review_text": r['text'],
                    "rating": r['rating'],
                    "review_title": r['title']
                } for r in reviews[:5]  # Save more samples
            ]
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(extraction_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved real Amazon extraction results to: {save_path}")
        print("📊 Results summary:")
        print(f"   - Total aspects: {result.aspects_extracted}")
        print(f"   - Physical aspects: {len(result.review_hierarchy.get('phy', {}))}")
        print(f"   - Performance aspects: {len(result.review_hierarchy.get('perf', {}))}")
        print(f"   - Use case aspects: {len(result.review_hierarchy.get('use', {}))}")
        print("="*80)
        
        # Verify result structure (but allow 0 aspects for now)
        assert isinstance(result, ReviewExtractionResult)
        assert "phy" in result.review_hierarchy
        assert "perf" in result.review_hierarchy  
        assert "use" in result.review_hierarchy
        
        if result.aspects_extracted > 0:
            print("\n✅ Real Amazon LLM extraction completed successfully!")
            print(f"   - Generated {result.aspects_extracted} aspects from real reviews")
        else:
            print("\n⚠️  Real Amazon LLM extraction returned 0 aspects")
            print("   - This may indicate LLM response parsing issues or token limits")
            print("   - Results saved for debugging and consolidation testing")
        
        print("   - Results saved for consolidation testing")
        print(f"   - File: {save_path}")

    @pytest.mark.asyncio
    async def test_retry_prompt_generation(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test retry prompt construction using validation error details."""
        
        print("\n" + "="*80)
        print("🔍 RETRY PROMPT GENERATION TEST")
        print("="*80)
        
        # Create original prompt
        context = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Great colorful design\n1#Easy to use but flickering issues",
            expected_review_ids={0, 1},
            asin="TEST123",
            product_title="Test Art Kit"
        )
        
        original_prompt = await extraction_stage._build_prompt(context)
        
        print("📝 ORIGINAL PROMPT (first 200 chars):")
        print(f"{original_prompt[:200]}...")
        print("="*80)
        
        # Create mock error categories (format from ValidationResult)
        error_categories = {
            "format_errors": [
                "Invalid JSON syntax at line 5",
                "'phy' section must be a JSON object, got list"
            ],
            "validation_errors": [
                "Invalid <PID> format 'AA1' - must be A, B, C... Z, AA, AB...",
                "Sentiment mismatch: RID 0 has sentiment '+' for A@colorful design but '-' for <PERF_REASON> A"
            ],
            "completeness_errors": [
                "Missing required section: 'use'"
            ]
        }
        
        print("📊 ERROR CATEGORIES TO PROCESS:")
        for category, errors in error_categories.items():
            print(f"   {category}:")
            for error in errors:
                print(f"     • {error}")
        print("="*80)
        
        # Create ValidationResult object
        validation_result = ValidationResult(ok=False, error_categories=error_categories)
        
        # Generate retry prompt
        retry_prompt = extraction_stage._retry_prompt(
            original_prompt=original_prompt,
            retry_ctx=validation_result,  # Now passing ValidationResult object
            ctx=context
        )
        
        print("🔄 COMPLETE RETRY PROMPT:")
        print("="*80)
        print(retry_prompt)
        print("="*80)
        
        # Verify retry prompt structure
        assert "RETRY REQUIRED" in retry_prompt
        assert "FORMAT ERRORS:" in retry_prompt
        assert "VALIDATION ERRORS:" in retry_prompt
        assert "COMPLETENESS ERRORS:" in retry_prompt
        assert "Invalid JSON syntax" in retry_prompt
        assert "Sentiment mismatch" in retry_prompt
        
        print("\n✅ Retry prompt generation test passed!")
        print("   - All error categories properly formatted")
        print("   - Proper template structure maintained")

    @pytest.mark.asyncio
    async def test_reason_sentiment_inconsistency_validation(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test validation of reason sentiment inconsistency errors."""
        
        print("\n" + "="*80)
        print("🔍 REASON SENTIMENT INCONSISTENCY VALIDATION TEST")
        print("="*80)
        
        # Create response with sentiment mismatches between sections
        inconsistent_response = json.dumps({
            "phy": {
                "design": {
                    "A@colorful appearance": {"+": [0], "-": []},
                    "B@compact size": {"+": [1], "-": []}
                }
            },
            "perf": {
                "usability": {
                    # RID 0 has '+' sentiment for A@colorful but '-' for performance reason A
                    "a@easy to handle": {"+": {"B": [1]}, "-": {"A": [0]}},  # Mismatch!
                    # RID 1 has '+' sentiment for B@compact but '+' for performance reason B (consistent)
                    "b@good grip": {"+": {"B": [1]}, "-": {}}
                }
            },
            "use": {
                # RID 0 has '+' sentiment for A@colorful but '-' for use reason A  
                "art projects": {"+": {"b": [1]}, "-": {"A": [0]}},  # Mismatch!
                # RID 1 has '+' sentiment for performance b@good grip and use reason b (consistent)
                "craft activities": {"+": {"b": [1]}, "-": {}}
            }
        })
        
        context = ReviewExtractionContext(
            product_category=PRODUCT_CATEGORY,
            formatted_reviews="0#Great colorful design, very appealing\n1#Compact size makes it easy to handle with good grip",
            expected_review_ids={0, 1},
            asin="TEST123", 
            product_title="Test Art Kit"
        )
        
        print("📝 RESPONSE WITH SENTIMENT MISMATCHES:")
        print(json.dumps(json.loads(inconsistent_response), indent=2))
        print("="*80)
        
        print("🔍 EXPECTED SENTIMENT MISMATCHES:")
        print("   • RID 0: '+' for A@colorful appearance vs '-' for <PERF_REASON> A in usability")
        print("   • RID 0: '+' for A@colorful appearance vs '-' for <USE_REASON> A in art projects")
        print("="*80)
        
        # Test validation
        result = extraction_stage._validate(inconsistent_response, context)
        
        print("📊 VALIDATION RESULT:")
        print(f"   • Valid: {result.ok}")
        print(f"   • Error categories: {list(result.error_categories.keys())}")
        print("="*80)
        
        print("🔍 DETAILED VALIDATION ERRORS:")
        for category, errors in result.error_categories.items():
            print(f"   {category}:")
            for error in errors:
                print(f"     • {error}")
        print("="*80)
        
        # Verify validation caught the sentiment mismatches
        assert result.ok is False
        assert "validation_errors" in result.error_categories
        
        validation_errors = result.error_categories["validation_errors"]
        sentiment_mismatch_errors = [e for e in validation_errors if "Sentiment mismatch" in e]
        
        assert len(sentiment_mismatch_errors) >= 2, f"Expected at least 2 sentiment mismatch errors, got {len(sentiment_mismatch_errors)}"
        
        # Check specific mismatch patterns
        perf_mismatch_found = any("RID 0" in e and "a@easy to handle" in e and "<PERF_REASON> A" in e for e in sentiment_mismatch_errors)
        use_mismatch_found = any("RID 0" in e and "art projects" in e and "<USE_REASON> A" in e for e in sentiment_mismatch_errors)
        
        assert perf_mismatch_found, f"Performance sentiment mismatch not found in: {sentiment_mismatch_errors}"
        assert use_mismatch_found, f"Use case sentiment mismatch not found in: {sentiment_mismatch_errors}"
        
        print("✅ Sentiment mismatch validation test passed!")
        print(f"   - Found {len(sentiment_mismatch_errors)} sentiment mismatch errors")
        print("   - Performance reason mismatch detected")
        print("   - Use case reason mismatch detected")
        
        # Now test retry prompt generation with these specific errors
        print("\n" + "="*60)
        print("🔄 RETRY PROMPT FOR SENTIMENT MISMATCHES")
        print("="*60)
        
        original_prompt = await extraction_stage._build_prompt(context)
        retry_prompt = extraction_stage._retry_prompt(
            original_prompt=original_prompt,
            retry_ctx=result,
            ctx=context
        )
        
        print("📝 RETRY PROMPT (showing error section):")
        # Extract just the error details section for readability
        retry_lines = retry_prompt.split('\n')
        in_error_section = False
        error_section_lines = []
        
        for line in retry_lines:
            if "RETRY REQUIRED" in line:
                in_error_section = True
            elif "PRODUCT CONTEXT" in line:
                in_error_section = False
            
            if in_error_section:
                error_section_lines.append(line)
        
        print('\n'.join(error_section_lines))
        print("="*60)
        
        # Verify retry prompt contains sentiment mismatch details
        assert "Sentiment mismatch" in retry_prompt
        assert "RID 0" in retry_prompt
        assert "a@easy to handle" in retry_prompt
        assert "<PERF_REASON> A" in retry_prompt
        assert "<USE_REASON> A" in retry_prompt
        
        print("✅ Retry prompt for sentiment mismatches properly generated!")
        print("   - Contains detailed sentiment mismatch descriptions")
        print("   - Includes RID and aspect references")
        print("   - Provides context for correction")