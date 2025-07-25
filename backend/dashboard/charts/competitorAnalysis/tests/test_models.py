"""Tests for competitor analysis models."""

import pytest
from pydantic import ValidationError

from ..models import (
    CompetitorSummaryRequest, CompetitorSummaryResponse,
    CompetitorMatrixViewRequest, CompetitorMatrixViewResponse,
    CompetitorMatrixViewOptions
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
        options = CompetitorMatrixViewOptions(
            sort_by="mentions",
            max_categories=5
        )
        request = CompetitorMatrixViewRequest(
            project_id="test-project-id",
            selected_asins=["B00NG0ELL0"],
            aspect_type="phy_perf",
            options=options
        )
        assert request.project_id == "test-project-id"
        assert request.selected_asins == ["B00NG0ELL0"]
        assert request.aspect_type == "phy_perf"
        assert request.options.sort_by == "mentions"
    
    def test_invalid_aspect_type(self):
        """Test validation error for invalid aspect_type."""
        options = CompetitorMatrixViewOptions()
        with pytest.raises(ValidationError):
            CompetitorMatrixViewRequest(
                project_id="test-project-id",
                selected_asins=["B00NG0ELL0"],
                aspect_type="invalid",
                options=options
            )


class TestCompetitorMatrixViewOptions:
    """Test CompetitorMatrixViewOptions model."""
    
    def test_default_values(self):
        """Test default option values."""
        options = CompetitorMatrixViewOptions()
        assert options.sort_by == "mentions"
        assert options.sort_direction == "desc"
        assert options.max_categories == 10
    
    def test_custom_values(self):
        """Test custom option values."""
        options = CompetitorMatrixViewOptions(
            sort_by="reviews",
            sort_direction="asc",
            max_categories=5,
            min_mentions=10,
            sentiment_filter="positive_only"
        )
        assert options.sort_by == "reviews"
        assert options.sort_direction == "asc"
        assert options.max_categories == 5
        assert options.min_mentions == 10
        assert options.sentiment_filter == "positive_only"
    
    def test_max_categories_validation(self):
        """Test max_categories validation."""
        with pytest.raises(ValidationError):
            CompetitorMatrixViewOptions(max_categories=0)
        
        with pytest.raises(ValidationError):
            CompetitorMatrixViewOptions(max_categories=51) 