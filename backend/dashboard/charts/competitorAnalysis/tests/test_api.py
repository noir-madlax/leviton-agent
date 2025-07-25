"""Tests for competitor analysis API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from dashboard.charts.api import router


class TestCompetitorAnalysisAPI:
    """Test competitor analysis API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_competitor_summary_request_validation(self, client):
        """Test request validation for competitor summary endpoint."""
        # Test missing project_id
        response = client.post("/competitor-analysis/summary", json={
            "selected_asins": ["B00NG0ELL0"]
        })
        assert response.status_code == 422
        
        # Test missing selected_asins
        response = client.post("/competitor-analysis/summary", json={
            "project_id": "test-project-id"
        })
        assert response.status_code == 422
        
        # Test valid request
        response = client.post("/competitor-analysis/summary", json={
            "project_id": "test-project-id",
            "selected_asins": ["B00NG0ELL0", "B0BVKZLT3B"]
        })
        # Should return 200 since our service handles invalid project IDs gracefully
        assert response.status_code == 200
    
    def test_competitor_matrix_view_request_validation(self, client):
        """Test request validation for competitor matrix view endpoint."""
        # Test missing required fields
        response = client.post("/competitor-analysis/matrix-view", json={
            "project_id": "test-project-id",
            "selected_asins": ["B00NG0ELL0"]
        })
        assert response.status_code == 422
        
        # Test invalid aspect_type
        response = client.post("/competitor-analysis/matrix-view", json={
            "project_id": "test-project-id",
            "selected_asins": ["B00NG0ELL0"],
            "aspect_type": "invalid",
            "options": {}
        })
        assert response.status_code == 422
        
        # Test valid request
        response = client.post("/competitor-analysis/matrix-view", json={
            "project_id": "test-project-id",
            "selected_asins": ["B00NG0ELL0"],
            "aspect_type": "phy_perf",
            "options": {
                "sort_by": "mentions",
                "max_categories": 5
            }
        })
        # Should return 200 since our service handles invalid project IDs gracefully
        assert response.status_code == 200
    
    @patch('dashboard.charts.api.CompetitorAnalysisChartService')
    def test_competitor_summary_success(self, mock_service_class, client):
        """Test successful competitor summary request."""
        # Mock the service
        mock_service = AsyncMock()
        mock_service.get_competitor_summary.return_value = {
            'products': [
                {
                    'asin': 'B00NG0ELL0',
                    'product_title': 'Test Product',
                    'rating': 4.5,
                    'brand': 'Test Brand',
                    'product_url': 'http://test.com',
                    'list_price': 29.99,
                    'unique_reviews_count': 10,
                    'additional_metrics': {}
                }
            ],
            'total_products': 1,
            'selected_asins': ['B00NG0ELL0']
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/competitor-analysis/summary", json={
            "project_id": "test-project-id",
            "selected_asins": ["B00NG0ELL0"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['products']) == 1
        assert data['data']['products'][0]['asin'] == 'B00NG0ELL0'
    
    @patch('dashboard.charts.api.CompetitorAnalysisChartService')
    def test_competitor_matrix_view_success(self, mock_service_class, client):
        """Test successful competitor matrix view request."""
        # Mock the service
        mock_service = AsyncMock()
        mock_service.get_matrix_view_data.return_value = {
            'aspect_categories': [
                {
                    'category_id': 1,
                    'category_name': 'Quality',
                    'definition': 'Product quality aspects'
                }
            ],
            'product_aspect_data': [
                {
                    'asin': 'B00NG0ELL0',
                    'aspect_data': []
                }
            ],
            'selected_asins': ['B00NG0ELL0'],
            'aspect_type': 'phy_perf',
            'total_categories': 1
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/competitor-analysis/matrix-view", json={
            "project_id": "test-project-id",
            "selected_asins": ["B00NG0ELL0"],
            "aspect_type": "phy_perf",
            "options": {
                "sort_by": "mentions",
                "max_categories": 5
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['aspect_categories']) == 1
        assert data['data']['aspect_categories'][0]['category_name'] == 'Quality' 