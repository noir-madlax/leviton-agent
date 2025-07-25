"""Tests for competitor analysis models."""

import pytest
from pydantic import ValidationError

from ..models import (
    CompetitorSummaryRequest, CompetitorSummaryResponse,
    CompetitorMatrixViewRequest, CompetitorMatrixViewResponse,
    ReviewRetrievalRequest, ReviewRetrievalResponse
)


class TestCompetitorSummaryRequest:
    """Test CompetitorSummaryRequest model."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        request = CompetitorSummaryRequest(
            project_id="test-project-id",
            selected_asins=["B00NG0ELL0", "B0BVKZLT3B"]
        )
        assert request.project_id == "test-project-id"
        assert request.selected_asins == ["B00NG0ELL0", "B0BVKZLT3B"]
    
    def test_missing_project_id(self):
        """Test validation error for missing project_id."""
        with pytest.raises(ValidationError):
            CompetitorSummaryRequest(selected_asins=["B00NG0ELL0"])
    
    def test_missing_selected_asins(self):
        """Test validation error for missing selected_asins."""
        with pytest.raises(ValidationError):
            CompetitorSummaryRequest(project_id="test-project-id")


class TestCompetitorMatrixViewRequest:
    """Test CompetitorMatrixViewRequest model."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        filter_options = {
            "sort_by": "mentions",
            "max_categories": 5
        }
        request = CompetitorMatrixViewRequest(
            project_id="test-project-id",
            selected_asins=["B00NG0ELL0"],
            aspect_type="phy_perf",
            filter=filter_options
        )
        assert request.project_id == "test-project-id"
        assert request.selected_asins == ["B00NG0ELL0"]
        assert request.aspect_type == "phy_perf"
        assert request.filter["sort_by"] == "mentions"
    
    def test_invalid_aspect_type(self):
        """Test validation error for invalid aspect_type."""
        filter_options = {}
        with pytest.raises(ValidationError):
            CompetitorMatrixViewRequest(
                project_id="test-project-id",
                selected_asins=["B00NG0ELL0"],
                aspect_type="invalid",
                filter=filter_options
            )


class TestReviewRetrievalRequest:
    """Test ReviewRetrievalRequest model."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        request = ReviewRetrievalRequest(
            project_id="test-project-id",
            category_id=1,
            product_id="B00NG0ELL0",
            limit=10,
            offset=0,
            sort_by="date",
            sort_order="desc"
        )
        assert request.project_id == "test-project-id"
        assert request.category_id == 1
        assert request.product_id == "B00NG0ELL0"
        assert request.limit == 10
        assert request.offset == 0
        assert request.sort_by == "date"
        assert request.sort_order == "desc"
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError):
            ReviewRetrievalRequest(
                project_id="test-project-id",
                category_id=1
                # Missing product_id
            )
        
        with pytest.raises(ValidationError):
            ReviewRetrievalRequest(
                project_id="test-project-id",
                product_id="B00NG0ELL0"
                # Missing category_id
            )
    
    def test_invalid_sort_by(self):
        """Test validation error for invalid sort_by."""
        with pytest.raises(ValidationError):
            ReviewRetrievalRequest(
                project_id="test-project-id",
                category_id=1,
                product_id="B00NG0ELL0",
                sort_by="invalid"
            )
    
    def test_invalid_sort_order(self):
        """Test validation error for invalid sort_order."""
        with pytest.raises(ValidationError):
            ReviewRetrievalRequest(
                project_id="test-project-id",
                category_id=1,
                product_id="B00NG0ELL0",
                sort_order="invalid"
            ) 