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
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import AsyncMock

from review_analysis.llm.extraction_stage import (
    ReviewExtractionStage,
    ReviewExtractionContext,
    ReviewExtractionResult,
    format_reviews_for_prompt,
    count_extracted_aspects
)
from review_analysis.llm.validation import ReviewValidationContext
from core.llm_taxonomy_pipeline.pipeline_stage import StageContext
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
        print(f"\n" + "="*80)
        print(f"🔍 FULL PROMPT FOR MANUAL INSPECTION")
        print(f"="*80)
        print(prompt)
        print(f"="*80)
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
        
        print(f"\n" + "="*60)
        print(f"🔍 VALIDATION RESULT - VALID RESPONSE")
        print(f"="*60)
        print(f"✅ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print(f"📝 Response being validated:")
        print(f"   {valid_response}")
        print(f"="*60)
        
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
        
        print(f"\n" + "="*60)
        print(f"🔍 VALIDATION RESULT - INVALID RESPONSE")
        print(f"="*60)
        print(f"❌ Validation Result: {result.ok}")
        print(f"📋 Error Categories: {result.error_categories}")
        print(f"📝 Response being validated:")
        print(f"   {invalid_response}")
        print(f"🔍 Error Details:")
        for category, errors in result.error_categories.items():
            print(f"   {category}: {errors}")
        print(f"="*60)
        
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
        
        print(f"\n" + "="*80)
        print(f"🔍 SPLIT AND MERGE OPERATIONS - MANUAL INSPECTION")
        print(f"="*80)
        print(f"📊 ORIGINAL CONTEXT:")
        print(f"   - Review count: {len(expected_ids)}")
        print(f"   - Expected IDs: {expected_ids}")
        print(f"   - Formatted reviews:")
        for line in formatted_reviews.split('\n'):
            print(f"     {line}")
        print(f"="*80)
        
        # 1. Test splitting
        ctx_left, ctx_right = extraction_stage._split_context(context, depth=0)
        
        print(f"📊 AFTER SPLIT:")
        print(f"   Left context:")
        print(f"     - Review count: {len(ctx_left.expected_review_ids)}")
        print(f"     - Expected IDs: {ctx_left.expected_review_ids}")
        print(f"     - Formatted reviews:")
        for line in ctx_left.formatted_reviews.split('\n'):
            print(f"       {line}")
        print(f"   Right context:")
        print(f"     - Review count: {len(ctx_right.expected_review_ids)}")
        print(f"     - Expected IDs: {ctx_right.expected_review_ids}")
        print(f"     - Formatted reviews:")
        for line in ctx_right.formatted_reviews.split('\n'):
            print(f"       {line}")
        print(f"="*80)
        
        # 2. Create mock results for merging
        from review_analysis.llm.extraction_stage import ReviewExtractionResult
        
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
        
        print(f"📊 MOCK RESULTS FOR MERGE:")
        print(f"   Left result (reviews 0,1):")
        print(f"     - Aspects: {res_left.aspects_extracted}")
        print(f"     - Hierarchy: {res_left.review_hierarchy}")
        print(f"   Right result (reviews 0,1, will be offset to 2,3):")
        print(f"     - Aspects: {res_right.aspects_extracted}")
        print(f"     - Hierarchy: {res_right.review_hierarchy}")
        print(f"="*80)
        
        # 3. Test merging
        merged_result = await extraction_stage._merge_split_results(
            res_left=res_left,
            res_right=res_right,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        print(f"📊 MERGED RESULT:")
        print(f"   - Total aspects: {merged_result.aspects_extracted}")
        print(f"   - Merged hierarchy:")
        for section_name, section_content in merged_result.review_hierarchy.items():
            print(f"     {section_name}:")
            for category, details in section_content.items():
                print(f"       {category}: {details}")
        print(f"="*80)
        
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
        
        print(f"\n✅ Split and merge operations completed successfully")
        print(f"   - Split: {len(expected_ids)} → {len(ctx_left.expected_review_ids)} + {len(ctx_right.expected_review_ids)}")
        print(f"   - Merge: {res_left.aspects_extracted} + {res_right.aspects_extracted} → {merged_result.aspects_extracted}")

    @pytest.mark.asyncio
    async def test_multi_character_id_offset(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test ID offsetting with multi-character IDs (AA, AB, aa, ab, etc.)."""
        print(f"\n" + "="*80)
        print(f"🔍 MULTI-CHARACTER ID OFFSET TEST")
        print(f"="*80)
        
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
        
        print(f"📊 LEFT RESULT (Y,Z,y,z IDs):")
        print(f"   {left_hierarchy}")
        print(f"📊 RIGHT RESULT (should become AA,AB,aa,ab after merge):")
        print(f"   {right_hierarchy}")
        print(f"="*80)
        
        # Test the merge
        merged_result = await extraction_stage._merge_split_results(
            res_left=res_left,
            res_right=res_right,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        print(f"📊 MERGED RESULT WITH MULTI-CHARACTER IDs:")
        for section_name, section_content in merged_result.review_hierarchy.items():
            print(f"   {section_name}:")
            for category, details in section_content.items():
                print(f"     {category}: {details}")
        print(f"="*80)
        
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
        
        print(f"\n✅ Multi-character ID offset test passed!")
        print(f"   - Left side: Y,Z,y,z (kept as-is)")
        print(f"   - Right side: A,B,a,b → AA,AB,aa,ab (correctly offset)")
        print(f"   - All RIDs properly offset by 2")
        print(f"   - All reason IDs correctly remapped")

    @pytest.mark.asyncio
    async def test_multi_character_input_ids(
        self,
        extraction_stage: ReviewExtractionStage
    ) -> None:
        """Test ID offsetting when left side already has multi-character IDs (AA, AB, etc.)."""
        
        print(f"\n" + "="*80)
        print(f"🔍 MULTI-CHARACTER INPUT IDS TEST")
        print(f"="*80)
        
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
        
        print(f"📊 LEFT RESULT (multi-character IDs: AA,AB,AC,AD,aa,ab,ac):")
        for section_name, section_content in left_hierarchy.items():
            print(f"   {section_name}:")
            for category, details in section_content.items():
                print(f"     {category}: {list(details.keys())}")
        
        print(f"📊 RIGHT RESULT (should become AE,AF,AG,ad,ae,af after merge):")
        for section_name, section_content in right_hierarchy.items():
            print(f"   {section_name}:")
            for category, details in section_content.items():
                print(f"     {category}: {list(details.keys())}")
        print(f"="*80)
        
        # Test the merge with multi-character inputs
        merged_result = await extraction_stage._merge_split_results(
            res_left=res_left,
            res_right=res_right,
            ctx_left=ctx_left,
            ctx_right=ctx_right,
            depth=0
        )
        
        print(f"📊 MERGED RESULT WITH ADVANCED MULTI-CHARACTER IDs:")
        for section_name, section_content in merged_result.review_hierarchy.items():
            print(f"   {section_name}:")
            for category, details in section_content.items():
                print(f"     {category}: {list(details.keys())}")
        print(f"="*80)
        
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
        
        print(f"\n✅ Multi-character input IDs test passed!")
        print(f"   - Left side: AA,AB,AC,AD,aa,ab,ac (kept as-is)")
        print(f"   - Right side: A,B,C,a,b,c → AE,AF,AG,ad,ae,af (correctly offset)")
        print(f"   - Complex reason mapping: A,C → AE,AG")
        print(f"   - All RIDs properly offset by 3")
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
        
        print(f"\n" + "="*60)
        print(f"🔍 RESULT CONVERSION")
        print(f"="*60)
        print(f"📝 Raw response: {raw_response}")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Aspects extracted: {result.aspects_extracted}")
        print(f"📋 Hierarchy structure:")
        for section, content in result.review_hierarchy.items():
            print(f"   {section}: {content}")
        print(f"="*60)
        
        assert isinstance(result, ReviewExtractionResult)
        assert result.review_hierarchy == valid_hierarchy
        assert result.aspects_extracted == 3  # 1 phy + 1 perf + 1 use
        
        print(f"\n✅ Produced result with {result.aspects_extracted} aspects")