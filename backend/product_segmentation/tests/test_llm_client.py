"""Tests for ProductSegmentationLLMClient."""

import pytest
import json
import pytest_asyncio
from product_segmentation.llm.product_segmentation_client import ProductSegmentationLLMClient
from product_segmentation.utils.cache import create_llm_cache


class TestProductSegmentationLLMClient:
    """Test the LLM client."""

    @pytest_asyncio.fixture
    async def llm_client(self):
        """Create a test LLM client."""
        prompts = {
            "extract_taxonomy": "Test prompt for taxonomy extraction",
            "consolidate_taxonomy": "Test prompt for taxonomy consolidation",
            "refine_assignments": "Test prompt for assignment refinement"
        }
        
        class StubLLM:
            async def __call__(self, prompt: str) -> str:
                return json.dumps({
                    "Category A": {
                        "definition": "First category",
                        "ids": ["0", "1"]
                    }
                })

        return ProductSegmentationLLMClient(
            llm_client=StubLLM(),
            prompts=prompts,
            cache=None,
            interaction_repo=None,
            storage_service=None,
            max_retries=2
        )

    @pytest.mark.asyncio
    async def test_segment_products_basic(self, llm_client):
        """Test basic product segmentation."""
        products = [1, 2, 3]
        result = await llm_client.segment_products(products, category="Electronics")

        assert "segments" in result
        assert "taxonomies" in result
        assert len(result["segments"]) == len(products)
        assert len(result["taxonomies"]) == 1
        assert result["taxonomies"][0]["category_name"] == "Category A"

    @pytest.mark.asyncio
    async def test_refine_assignments_with_taxonomy(self, llm_client):
        """Test refinement with taxonomy context."""
        original_segments = [
            {"product_id": 1, "taxonomy_id": 1, "category_name": "Category A"},
            {"product_id": 2, "taxonomy_id": 1, "category_name": "Category A"},
        ]
        taxonomies = [
            {
                "category_name": "Category A",
                "definition": "First category",
                "product_count": 2
            },
            {
                "category_name": "Category B",
                "definition": "Second category",
                "product_count": 0
            }
        ]

        updated = await llm_client.refine_assignments(original_segments, taxonomies)
        assert "segments" in updated
        assert len(updated["segments"]) == len(original_segments)
        assert all("taxonomy_id" in s for s in updated["segments"])


class _StubLLM:
    """Stub LLM client that returns deterministic responses."""

    def __init__(self, fail_consolidation: bool = False, fail_refinement: bool = False):
        self.fail_consolidation = fail_consolidation
        self.fail_refinement = fail_refinement

    async def __call__(self, prompt: str, model: str = None, temperature: float = None) -> str:
        """Return deterministic response based on prompt."""
        if "Extract taxonomy" in prompt:
            return json.dumps({
                "Category A": {
                    "definition": "First category",
                    "ids": [0, 1, 2]
                }
            })
        elif "Consolidate taxonomies" in prompt:
            if self.fail_consolidation:
                raise RuntimeError("Simulated consolidation failure")
            return json.dumps({
                "Category A": {
                    "definition": "First category",
                    "ids": ["A_0"]
                }
            })
        elif "Refine assignments" in prompt:
            if self.fail_refinement:
                raise RuntimeError("Simulated refinement failure")
            return json.dumps({
                "P_0": "S_0",
                "P_1": "S_0"
            })
        return "{}"


@pytest.mark.asyncio
async def test_segment_products_basic(llm_client):
    """Test basic product segmentation."""
    products = [1, 2, 3]
    result = await llm_client.segment_products(products, category="Electronics")
    
    assert "segments" in result
    assert "taxonomies" in result
    assert len(result["segments"]) == len(products)
    assert len(result["taxonomies"]) == 1
    assert result["taxonomies"][0]["category_name"] == "Category A"


@pytest.mark.asyncio
async def test_refine_assignments_with_taxonomy(llm_client):
    """Test refinement with taxonomy context."""
    original_segments = [
        {"product_id": 1, "taxonomy_id": 1, "category_name": "Category A"},
        {"product_id": 2, "taxonomy_id": 1, "category_name": "Category A"},
    ]
    taxonomies = [
        {
            "category_name": "Category A",
            "definition": "First category",
            "product_count": 2
        },
        {
            "category_name": "Category B",
            "definition": "Second category",
            "product_count": 0
        }
    ]

    updated = await llm_client.refine_assignments(original_segments, taxonomies)
    assert "segments" in updated
    assert len(updated["segments"]) == len(original_segments)
    assert all("taxonomy_id" in s for s in updated["segments"])
    
    @pytest.mark.asyncio
    async def test_consolidate_taxonomy_basic(self, llm_client):
        """Test basic taxonomy consolidation."""
        taxonomies = [
            {"category_a": {"definition": "Category A", "product_count": 2}},
            {"category_b": {"definition": "Category B", "product_count": 1}}
        ]
        
        result = await llm_client.consolidate_taxonomy(taxonomies)
        
        # Verify response structure
        assert "consolidated" in result
        assert isinstance(result["consolidated"], dict)
    
    @pytest.mark.asyncio
    async def test_consolidate_taxonomy_empty(self, llm_client):
        """Test consolidation with empty input."""
        result = await llm_client.consolidate_taxonomy([])
        
        assert result["consolidated"] == {}
    
    @pytest.mark.asyncio
    async def test_consolidate_taxonomy_single(self, llm_client):
        """Test consolidation with single taxonomy."""
        taxonomies = [{"category_a": {"definition": "Category A", "product_count": 2}}]
        
        result = await llm_client.consolidate_taxonomy(taxonomies)
        
        assert result["consolidated"] == taxonomies[0]
    
    def test_json_extraction(self, llm_client):
        """Test JSON extraction from response."""
        response_text = """
        Here is the analysis:
        {
            "category": {
                "definition": "test",
                "ids": [1, 2]
            }
        }
        Some trailing text.
        """
        
        json_text = llm_client._extract_json_from_response(response_text)
        parsed = json.loads(json_text)
        
        assert "category" in parsed
        assert parsed["category"]["definition"] == "test"
        assert parsed["category"]["ids"] == [1, 2]
    
    def test_json_extraction_no_json(self, llm_client):
        """Test JSON extraction when no JSON present."""
        response_text = "No JSON here at all"
        
        with pytest.raises(ValueError, match="No JSON found"):
            llm_client._extract_json_from_response(response_text)
    
    def test_validation_success(self, llm_client):
        """Test successful response validation."""
        taxonomy = {
            "Category A": {
                "definition": "Test category",
                "ids": [0, 1]
            },
            "Category B": {
                "definition": "Another category",
                "ids": [2]
            }
        }
        
        is_valid, result = llm_client._parse_and_validate_response(
            json.dumps(taxonomy), {0, 1, 2}, [10, 20, 30]
        )
        
        assert is_valid
        assert result == taxonomy
    
    def test_validation_missing_ids(self, llm_client):
        """Test validation with missing product IDs."""
        taxonomy = {
            "Category A": {
                "definition": "Test category",
                "ids": [0]  # Missing IDs 1, 2
            }
        }
        
        is_valid, result = llm_client._parse_and_validate_response(
            json.dumps(taxonomy), {0, 1, 2}, [10, 20, 30]
        )
        
        assert not is_valid
        assert "missing_ids" in result
        assert set(result["missing_ids"]) == {1, 2}
    
    def test_validation_duplicate_ids(self, llm_client):
        """Test validation with duplicate IDs."""
        taxonomy = {
            "Category A": {
                "definition": "Test category",
                "ids": [0, 1]
            },
            "Category B": {
                "definition": "Another category",
                "ids": [1, 2]  # ID 1 is duplicate
            }
        }
        
        is_valid, result = llm_client._parse_and_validate_response(
            json.dumps(taxonomy), {0, 1, 2}, [10, 20, 30]
        )
        
        assert not is_valid
        assert "validation_errors" in result
        assert any("Duplicate ID 1" in error for error in result["validation_errors"])
    
    def test_conversion_to_service_format(self, llm_client):
        """Test conversion to service expected format."""
        taxonomy = {
            "Category A": {
                "definition": "Test category A",
                "ids": [0, 1]
            },
            "Category B": {
                "definition": "Test category B", 
                "ids": [2]
            }
        }
        
        result = llm_client._convert_to_service_format(taxonomy, [10, 20, 30])
        
        # Check taxonomies
        assert len(result["taxonomies"]) == 2
        tax_a = result["taxonomies"][0]
        assert tax_a["category_name"] == "Category A"
        assert tax_a["definition"] == "Test category A"
        assert tax_a["product_count"] == 2
        
        # Check segments
        assert len(result["segments"]) == 3
        segments_by_product = {seg["product_id"]: seg for seg in result["segments"]}
        
        assert segments_by_product[10]["taxonomy_id"] == 1  # Category A
        assert segments_by_product[20]["taxonomy_id"] == 1  # Category A
        assert segments_by_product[30]["taxonomy_id"] == 2  # Category B
    
    @pytest.mark.asyncio
    async def test_refine_assignments_no_taxonomy(self, llm_client):
        """Test that refinement without taxonomy context returns original segments."""
        original_segments = [
            {"product_id": 1, "taxonomy_id": 1},
            {"product_id": 2, "taxonomy_id": 1},
        ]

        updated = await llm_client.refine_assignments(original_segments, None)

        assert "segments" in updated
        assert updated["segments"] == original_segments
        assert "cache_key" in updated
        assert updated["cache_key"] is None 