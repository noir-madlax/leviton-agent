"""Tests for competitor analysis services."""

import pytest
from unittest.mock import Mock, AsyncMock

from ..service import CompetitorAnalysisChartService


class TestCompetitorAnalysisChartService:
    """Test CompetitorAnalysisChartService."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CompetitorAnalysisChartService(project_id="test-project-id")
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.project_id == "test-project-id"
        assert service.supabase is not None
    
    def test_get_data_returns_empty_list(self, service):
        """Test that get_data returns empty list as required by base class."""
        result = service.get_data()
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_competitor_summary_empty_asins(self, service):
        """Test competitor summary with empty ASIN list."""
        result = await service.get_competitor_summary([])
        assert result['products'] == []
        assert result['total_products'] == 0
        assert result['selected_asins'] == []
    
    @pytest.mark.asyncio
    async def test_get_competitor_summary_with_asins(self, service):
        """Test competitor summary with valid ASINs."""
        # Mock the service methods
        service._get_product_summary_data = AsyncMock(return_value={
            'B00NG0ELL0': {'title': 'Test Product', 'rating': 4.5, 'brand': 'Test Brand'}
        })
        service._get_unique_review_counts = AsyncMock(return_value={
            'B00NG0ELL0': 10
        })
        service._get_additional_metrics = AsyncMock(return_value={
            'B00NG0ELL0': {'sentiment_distribution': {'positive': 5, 'negative': 2, 'neutral': 3}}
        })
        
        result = await service.get_competitor_summary(['B00NG0ELL0'])
        
        assert len(result['products']) == 1
        assert result['total_products'] == 1
        assert result['selected_asins'] == ['B00NG0ELL0']
        assert result['products'][0]['asin'] == 'B00NG0ELL0'
        assert result['products'][0]['product_title'] == 'Test Product'
    
    @pytest.mark.asyncio
    async def test_get_matrix_view_data_empty_categories(self, service):
        """Test matrix view data with no categories found."""
        service._get_aspect_categories_with_options = AsyncMock(return_value=[])
        service._get_category_info = AsyncMock(return_value={})
        service._get_product_aspect_data = AsyncMock(return_value=[])
        
        result = await service.get_matrix_view_data(
            ['B00NG0ELL0'], 'phy_perf', {}
        )
        
        assert result['aspect_categories'] == []
        assert result['product_aspect_data'] == []
        assert result['total_categories'] == 0
    
    def test_apply_category_filters(self, service):
        """Test category filtering logic."""
        categories = [
            {'mentions': 10, 'reviews': 5, 'category_name': 'Quality'},
            {'mentions': 5, 'reviews': 3, 'category_name': 'Installation'},
            {'mentions': 15, 'reviews': 8, 'category_name': 'Performance'}
        ]
        
        # Test min_mentions filter
        options = {'min_mentions': 8}
        filtered = service._apply_category_filters(categories, options)
        assert len(filtered) == 2
        assert all(cat['total_mentions'] >= 8 for cat in filtered)
        
        # Test include_categories filter
        options = {'include_categories': ['Quality', 'Performance']}
        filtered = service._apply_category_filters(categories, options)
        assert len(filtered) == 2
        assert all(cat['category_name'] in ['Quality', 'Performance'] for cat in filtered)
    
    def test_apply_category_sorting(self, service):
        """Test category sorting logic."""
        categories = [
            {'mentions': 10, 'reviews': 5, 'category_name': 'Quality'},
            {'mentions': 5, 'reviews': 8, 'category_name': 'Installation'},
            {'mentions': 15, 'reviews': 3, 'category_name': 'Performance'}
        ]
        
        # Test sorting by mentions descending
        options = {'sort_by': 'mentions', 'sort_direction': 'desc'}
        sorted_cats = service._apply_category_sorting(categories, options)
        assert sorted_cats[0]['mentions'] == 15
        assert sorted_cats[1]['mentions'] == 10
        assert sorted_cats[2]['mentions'] == 5
        
        # Test sorting by reviews ascending
        options = {'sort_by': 'reviews', 'sort_direction': 'asc'}
        sorted_cats = service._apply_category_sorting(categories, options)
        assert sorted_cats[0]['reviews'] == 3
        assert sorted_cats[1]['reviews'] == 5
        assert sorted_cats[2]['reviews'] == 8 