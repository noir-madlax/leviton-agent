"""Tests for Review Analysis models."""

import pytest
from pydantic import ValidationError

from ..models import (
    TopCategoriesRequest, TopCategoriesResponse, TopCategoriesData,
    ReviewsByCategoryRequest, ReviewsByCategoryResponse, ReviewsByCategoryData,
    CategorySummary, ReviewWithProductInfo
)


class TestTopCategoriesRequest:
    """Test TopCategoriesRequest model."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        request = TopCategoriesRequest(
            project_id="test-project",
            filters={},
            date_range=None,
            options={
                "aspect_type": "phy_perf",
                "sort_by": "mentions",
                "max_categories": 10
            }
        )
        
        assert request.project_id == "test-project"
        assert request.options["aspect_type"] == "phy_perf"
        assert request.options["sort_by"] == "mentions"
        
        # Test with empty options
        request = TopCategoriesRequest(
            project_id="test-project",
            filters={},
            date_range=None,
            options={}
        )
    
    def test_missing_project_id(self):
        """Test validation error for missing project_id."""
        with pytest.raises(ValidationError):
            TopCategoriesRequest(
                options={}
            )


class TestReviewsByCategoryRequest:
    """Test ReviewsByCategoryRequest model."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        request = ReviewsByCategoryRequest(
            project_id="test-project-id",
            category_id=12345,
            limit=20,
            offset=0,
            sort_by="date",
            sort_order="desc"
        )
        assert request.project_id == "test-project-id"
        assert request.category_id == 12345
        assert request.limit == 20
        assert request.sort_by == "date"
    
    def test_default_values(self):
        """Test default values."""
        request = ReviewsByCategoryRequest(
            project_id="test-project-id",
            category_id=12345
        )
        assert request.limit == 100
        assert request.offset == 0
        assert request.sort_by == "review_id"
        assert request.sort_order == "desc"


class TestCategorySummary:
    """Test CategorySummary model."""
    
    def test_valid_category_summary(self):
        """Test valid category summary creation."""
        category = CategorySummary(
            category_id=12345,
            category_name="Test Category",
            definition="Test definition",
            aspect_type="phy",
            total_mentions=100,
            positive_mentions=70,
            negative_mentions=20,
            neutral_mentions=10,
            total_reviews=50,
            positive_reviews=35,
            negative_reviews=10,
            positive_ratio=0.7
        )
        assert category.category_id == 12345
        assert category.category_name == "Test Category"
        assert category.positive_ratio == 0.7


class TestReviewWithProductInfo:
    """Test ReviewWithProductInfo model."""
    
    def test_valid_review_with_product_info(self):
        """Test valid review with product info creation."""
        from ...reviewCore.models import ReviewAspectBase
        
        aspects = [
            ReviewAspectBase(
                aspect_description="Easy installation",
                sentiment="+",
                aspect_type="phy"
            )
        ]
        
        review = ReviewWithProductInfo(
            review_id="R123456789",
            review_title="Great product",
            review_text="This product works great",
            rating=5,
            verified=True,
            review_date="2024-01-15",
            aspects=aspects,
            product_id="B00NG0ELL0",
            product_title="Test Product",
            product_brand="Test Brand",
            product_url="https://example.com"
        )
        assert review.review_id == "R123456789"
        assert review.product_id == "B00NG0ELL0"
        assert len(review.aspects) == 1
        assert review.aspects[0].aspect_description == "Easy installation" 