import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from product_segmentation.api import router as segmentation_router
import time
from typing import Dict, Any, Optional, List


@pytest.fixture(scope="module")
def client() -> TestClient:  # noqa: D401 – test fixture
    _app = FastAPI()
    _app.include_router(segmentation_router, prefix="/api/segmentation")
    return TestClient(_app)


def test_segmentation_end_to_end(client: TestClient) -> None:  # noqa: D401 – integration test
    # 1) Start a new segmentation run
    payload = {
        "product_ids": [101, 102, 103],
        "category": "Lighting",
        "batch_size": 20  # Optional but we provide it for testing
    }
    start_resp = client.post("/api/segmentation/start", json=payload)
    assert start_resp.status_code == 200, start_resp.text
    
    data = start_resp.json()
    assert "run_id" in data
    assert data["status"] == "started"
    assert data["total_products"] == len(payload["product_ids"])
    
    run_id = data["run_id"]
    
    # 2) Poll status until complete
    max_retries = 10
    for _ in range(max_retries):
        status_resp = client.get(f"/api/segmentation/{run_id}/status")
        assert status_resp.status_code == 200
        
        status_data = status_resp.json()
        if status_data["status"] in ["completed", "failed"]:
            break
            
        time.sleep(0.5)  # Short delay between polls
    
    assert status_data["status"] == "completed"
    
    # 3) Get final results
    results_resp = client.get(f"/api/segmentation/{run_id}/results")
    assert results_resp.status_code == 200
    
    results = results_resp.json()
    assert len(results["segments"]) == len(payload["product_ids"])
    
    # All three products must be present in segments list
    segment_product_ids = {s["product_id"] for s in results["segments"]}
    assert segment_product_ids == {101, 102, 103}
    
    # Verify refined segments are returned
    refined_segments = results.get("refined_segments", [])
    assert len(refined_segments) == 3
    
    # Verify taxonomies are present
    taxonomies = results.get("taxonomies", [])
    assert len(taxonomies) > 0
    assert all("category_name" in t for t in taxonomies)
    assert all("definition" in t for t in taxonomies)
    assert all("product_count" in t for t in taxonomies)


class _InMemorySegmentationRunRepository:
    """In-memory fake of SegmentationRunRepository."""

    def __init__(self) -> None:
        self._data = {}

    async def create(self, run_data):  # type: ignore[override]
        self._data[run_data.id] = run_data
        return run_data

    async def get_by_id(self, run_id):  # type: ignore[override]
        return self._data.get(run_id)

    async def update_progress(self, run_id: str, processed_products: int, total_products: Optional[int] = None) -> bool:  # type: ignore[override]
        """Update run progress."""
        run = self._data[run_id]
        run.processed_products = processed_products
        if total_products is not None:
            run.total_products = total_products
        return True 


class _InMemoryProductSegmentRepository:
    """In-memory fake of ProductSegmentRepository."""

    def __init__(self):
        self._segments = []
        self._run_products = {}

    async def create_run_products(self, run_id: str, product_ids: List[int]) -> bool:
        """Create product list for a run."""
        self._run_products[run_id] = product_ids
        return True

    async def get_run_products(self, run_id: str) -> List[int]:
        """Get products for a run."""
        return self._run_products.get(run_id, [])

    async def batch_create_segments(self, segments: List[Dict[str, Any]]) -> bool:
        """Store segments in memory."""
        self._segments.extend(segments)
        return True

    async def get_segments_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Get segments for a run."""
        return [s for s in self._segments if s["run_id"] == run_id]

    async def batch_create_refined_segments(self, segments: List[Dict[str, Any]]) -> bool:
        """Store refined segments in memory."""
        return await self.batch_create_segments(segments) 