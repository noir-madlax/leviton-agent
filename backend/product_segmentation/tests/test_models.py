"""
Tests for product segmentation models
"""
import pytest
from pydantic import ValidationError
from product_segmentation.models import (
    SegmentationRunCreate, SegmentationStatus, InteractionType,
    ProductTaxonomyCreate, ProductSegmentCreate, LLMInteractionIndexCreate,
    StartSegmentationRequest
)


class TestSegmentationModels:
    """Test cases for segmentation models"""
    
    def test_segmentation_run_create_valid(self):
        """Test valid segmentation run creation"""
        run_data = SegmentationRunCreate(
            id="RUN_20250618T120301Z_8d24",
            total_products=100,
            llm_config={"model": "gpt-4o", "temperature": 0.2}
        )
        
        assert run_data.id == "RUN_20250618T120301Z_8d24"
        assert run_data.total_products == 100
        assert run_data.status == SegmentationStatus.RUNNING
        assert run_data.processed_products == 0
    
    def test_segmentation_run_create_invalid_id(self):
        """Test invalid run ID validation"""
        with pytest.raises(ValidationError) as exc_info:
            SegmentationRunCreate(
                id="",  # Empty ID should fail
                total_products=100
            )
        
        assert "Run ID must be non-empty" in str(exc_info.value)
    
    def test_segmentation_run_create_long_id(self):
        """Test overly long run ID validation"""
        long_id = "x" * 51  # More than 50 characters
        
        with pytest.raises(ValidationError) as exc_info:
            SegmentationRunCreate(
                id=long_id,
                total_products=100
            )
        
        assert "50 characters" in str(exc_info.value)
    
    def test_product_taxonomy_create_valid(self):
        """Test valid taxonomy creation"""
        taxonomy = ProductTaxonomyCreate(
            run_id="RUN_TEST_123",
            category_name="Smart Switches",
            definition="WiFi-enabled smart switches",
            product_count=25
        )
        
        assert taxonomy.run_id == "RUN_TEST_123"
        assert taxonomy.category_name == "Smart Switches"
        assert taxonomy.product_count == 25
    
    def test_product_segment_create_valid(self):
        """Test valid segment creation"""
        segment = ProductSegmentCreate(
            run_id="RUN_TEST_123",
            product_id=456,
            taxonomy_id=789
        )
        
        assert segment.run_id == "RUN_TEST_123"
        assert segment.product_id == 456
        assert segment.taxonomy_id == 789
    
    def test_product_segment_invalid_confidence(self):
        """Test invalid confidence score validation"""
        with pytest.raises(ValidationError):
            ProductSegmentCreate(
                run_id="RUN_TEST_123",
                product_id=456,
                taxonomy_id=789,
                confidence=1.5  # > 1.0 should fail
            )
        
        with pytest.raises(ValidationError):
            ProductSegmentCreate(
                run_id="RUN_TEST_123",
                product_id=456,
                taxonomy_id=789,
                confidence=-0.1  # < 0.0 should fail
            )
    
    def test_llm_interaction_index_create_valid(self):
        """Test valid LLM interaction index creation"""
        interaction = LLMInteractionIndexCreate(
            run_id="RUN_TEST_123",
            interaction_type=InteractionType.SEGMENTATION,
            batch_id=1,
            attempt=1,
            file_path="/path/to/interaction.json",
            prompt_file="/path/to/prompt.txt",
            cache_key="abc123"
        )
        
        assert interaction.run_id == "RUN_TEST_123"
        assert interaction.interaction_type == InteractionType.SEGMENTATION
        assert interaction.batch_id == 1
        assert interaction.attempt == 1
        assert interaction.file_path == "/path/to/interaction.json"
    
    def test_start_segmentation_request_valid(self):
        """Test valid segmentation start request"""
        request = StartSegmentationRequest(
            product_ids=[1, 2, 3, 4, 5],
            category="Electronics",
            batch_size=10
        )
        
        assert len(request.product_ids) == 5
        assert request.category == "Electronics"
        assert request.batch_size == 10
    
    def test_start_segmentation_request_invalid_product_ids(self):
        """Test product IDs validation"""
        with pytest.raises(ValidationError):
            StartSegmentationRequest(product_ids=[])
    
    def test_start_segmentation_request_invalid_batch_size(self):
        """Test batch size validation"""
        with pytest.raises(ValidationError):
            StartSegmentationRequest(product_ids=[1, 2, 3], batch_size=-1) 