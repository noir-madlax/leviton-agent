#!/usr/bin/env python3
"""
Comprehensive tests for automatic error fixing feature in ReviewExtractionStage.

This test suite tests the automatic error fixing functionality:
1. Normal success (no error fixing needed)
2. Automatic error fixing method functionality
3. Execute method override verification
4. Error fixing with invalid responses
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from review_analysis.llm import ReviewExtractionStage, ReviewExtractionContext
from review_analysis.llm.review_extraction_stage import ReviewExtractionResult
from core.utils.llm_utils import LLMCallError, ValidationResult
from core.llm_taxonomy_pipeline.pipeline_stage import StageProtocolError


class TestAutomaticErrorFixing:
    """Test suite for automatic error fixing feature."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock ReviewExtractionContext."""
        context = MagicMock(spec=ReviewExtractionContext)
        context.reviews = [
            {"review_id": 1, "review_text": "Great product, works well."},
            {"review_id": 2, "review_text": "Compact design, very functional."}
        ]
        context.product_id = "TEST123"
        context.batch_id = "batch_1"
        context.product_category = "Wall Switches"
        context.formatted_reviews = "0#Great product, works well.\n1#Compact design, very functional."
        context.expected_review_ids = {0, 1}
        context.asin = "TEST123"
        context.product_title = "Test Product"
        return context
    
    @pytest.fixture
    def extraction_stage(self):
        """Create ReviewExtractionStage instance."""
        return ReviewExtractionStage()
    
    @pytest.mark.asyncio
    async def test_normal_success_no_error_fixing_needed(self, extraction_stage, mock_context):
        """Test normal success case where no error fixing is needed."""
        
        # Mock safe_llm_call to return valid response
        with patch('core.utils.llm_utils.safe_llm_call', new_callable=AsyncMock) as mock_safe_llm_call:
            mock_safe_llm_call.return_value = '{"phy": {"size": {"A@compact design": {"+": [0, 1]}}}}'
            
            # Execute the stage
            result = await extraction_stage.execute(mock_context)
            
            # Verify results
            assert isinstance(result, ReviewExtractionResult)
            assert mock_safe_llm_call.call_count >= 1  # At least one call needed
    
    @pytest.mark.asyncio
    async def test_automatic_error_fixing_method_success(self, extraction_stage, mock_context):
        """Test the _attempt_error_fixing method with a fixable response."""
        
        # Test the method directly with a response that can be fixed
        last_response = '{"phy": {"size": {"A@compact design": {"+": [0, 1]}}}}'
        
        result = extraction_stage._attempt_error_fixing(
            last_response, mock_context
        )
        
        # Verify results
        assert result is not None
        assert isinstance(result, ReviewExtractionResult)
        assert "phy" in result.review_hierarchy
        assert result.aspects_extracted > 0
    
    @pytest.mark.asyncio
    async def test_automatic_error_fixing_method_failure(self, extraction_stage, mock_context):
        """Test the _attempt_error_fixing method with an unfixable response."""
        
        # Test the method directly with a response that cannot be fixed
        last_response = "invalid json response"
        
        result = extraction_stage._attempt_error_fixing(
            last_response, mock_context
        )
        
        # Verify results
        assert result is None  # Should return None for unfixable responses
    
    @pytest.mark.asyncio
    async def test_execute_method_override(self, extraction_stage, mock_context):
        """Test that the execute method is properly overridden."""
        
        # Verify that the execute method is overridden (not the base class method)
        base_execute = extraction_stage.__class__.__bases__[0].execute
        current_execute = extraction_stage.execute
        
        assert current_execute != base_execute, "Execute method should be overridden"
        
        # Verify the method has the automatic error fixing logic
        source_code = current_execute.__code__.co_consts
        assert any("automatic error fixing" in str(const) for const in source_code if isinstance(const, str))
    
    @pytest.mark.asyncio
    async def test_error_fixing_with_invalid_review_ids(self, extraction_stage, mock_context):
        """Test automatic error fixing with invalid review IDs."""
        
        # Test with response containing invalid review IDs
        last_response = '{"phy": {"size": {"A@compact design": {"+": [999, 1000]}}}}'  # Invalid RIDs
        
        result = extraction_stage._attempt_error_fixing(
            last_response, mock_context
        )
        
        # Verify results - should filter out invalid review IDs
        assert result is not None
        assert isinstance(result, ReviewExtractionResult)
        # The invalid review IDs should be filtered out
        if "phy" in result.review_hierarchy and "size" in result.review_hierarchy["phy"]:
            for aspect in result.review_hierarchy["phy"]["size"].values():
                for rid_list in aspect.values():
                    assert all(rid in mock_context.expected_review_ids for rid in rid_list)
    
    @pytest.mark.asyncio
    async def test_error_fixing_with_missing_sections(self, extraction_stage, mock_context):
        """Test automatic error fixing with missing required sections."""
        
        # Test with response missing required sections
        last_response = '{"phy": {"size": {"A@compact design": {"+": [0, 1]}}}}'  # Missing perf and use
        
        result = extraction_stage._attempt_error_fixing(
            last_response, mock_context
        )
        
        # Verify results - should add missing sections
        assert result is not None
        assert isinstance(result, ReviewExtractionResult)
        assert "phy" in result.review_hierarchy
        assert "perf" in result.review_hierarchy
        assert "use" in result.review_hierarchy
    
    @pytest.mark.asyncio
    async def test_error_fixing_with_invalid_sentiment(self, extraction_stage, mock_context):
        """Test automatic error fixing with invalid sentiment values."""
        
        # Test with response containing invalid sentiment values
        last_response = '{"phy": {"size": {"A@compact design": {"invalid": [0, 1]}}}}'  # Invalid sentiment
        
        result = extraction_stage._attempt_error_fixing(
            last_response, mock_context
        )
        
        # Verify results - should fix invalid sentiment values
        assert result is not None
        assert isinstance(result, ReviewExtractionResult)
        # The sentiment should be fixed to valid values
        if "phy" in result.review_hierarchy and "size" in result.review_hierarchy["phy"]:
            for aspect in result.review_hierarchy["phy"]["size"].values():
                for sentiment in aspect.keys():
                    assert sentiment in ["+", "-"]  # Only valid sentiments


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 