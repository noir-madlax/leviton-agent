#!/usr/bin/env python3
"""
Comprehensive API test script for Competitor Analysis endpoints.

This script tests all competitor analysis API endpoints with real POST requests
and documents the requests and expected outputs.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test constants
API_BASE_URL = "http://localhost:8000/api/v1/dashboard/charts"
TEST_PROJECT_ID = "d2c02b80-4c82-44cc-8093-56708a7883f7"
TEST_ASINS = [
    'B00NG0ELL0',  # Leviton DSL06 - Mid-tier brand representative
    'B0BVKZLT3B',  # Leviton D215S - Mid-tier brand representative
    'B0BVKYKKRK',  # Leviton D26HD - Mid-tier brand representative
    'B0BSHKS26L',  # Lutron Caseta Diva - Mid-tier brand representative
    'B085D8M2MR',  # Lutron Diva - Mid-tier brand representative
    "B01EZV35QU",  # TP Link Switch
]


class APITester:
    """API testing class for competitor analysis endpoints."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.test_results = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the specified endpoint."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.info(f"Making POST request to {url}")
            logger.info(f"Request data: {json.dumps(data, indent=2)}")
            
            async with self.session.post(url, json=data) as response:
                response_text = await response.text()
                
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    response_data = json.loads(response_text)
                    logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
                    return {
                        'success': True,
                        'status_code': response.status,
                        'data': response_data
                    }
                else:
                    logger.error(f"Request failed with status {response.status}")
                    logger.error(f"Response text: {response_text}")
                    return {
                        'success': False,
                        'status_code': response.status,
                        'error': response_text
                    }
                    
        except Exception as e:
            logger.error(f"Request failed with exception: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def test_competitor_summary(self) -> Dict[str, Any]:
        """Test the competitor summary endpoint."""
        logger.info("=" * 60)
        logger.info("Testing Competitor Summary API")
        logger.info("=" * 60)
        
        request_data = {
            "project_id": TEST_PROJECT_ID,
            "selected_asins": TEST_ASINS
        }
        
        result = await self.make_request("competitor-analysis/summary", request_data)
        self.test_results['competitor_summary'] = {
            'request': request_data,
            'response': result
        }
        return result
    
    async def test_competitor_matrix_view(self) -> Dict[str, Any]:
        """Test the competitor matrix view endpoint."""
        logger.info("=" * 60)
        logger.info("Testing Competitor Matrix View API")
        logger.info("=" * 60)
        
        request_data = {
            "project_id": TEST_PROJECT_ID,
            "selected_asins": TEST_ASINS[:3],  # Use first 3 ASINs for testing
            "aspect_type": "phy_perf",
            "filter": {
                "sort_by": "mentions",
                "sort_direction": "desc",
                "max_categories": 5,
                "min_mentions": 3
            }
        }
        
        result = await self.make_request("competitor-analysis/matrix-view", request_data)
        self.test_results['competitor_matrix_view'] = {
            'request': request_data,
            'response': result
        }
        return result
    
    async def test_review_retrieval(self) -> Dict[str, Any]:
        """Test the review retrieval endpoint."""
        logger.info("=" * 60)
        logger.info("Testing Review Retrieval API")
        logger.info("=" * 60)
        
        # First, we need to get a valid category_id and product_id
        # For now, we'll use some common values, but in a real scenario,
        # you'd get these from the matrix view or summary response
        
        request_data = {
            "project_id": TEST_PROJECT_ID,
            "category_id": 12499,  # Use a valid category_id from matrix view results
            "product_id": TEST_ASINS[0],  # Use first ASIN
            "limit": 5,
            "offset": 0,
            "sort_by": "date",
            "sort_order": "desc"
        }
        
        result = await self.make_request("competitor-analysis/reviews", request_data)
        self.test_results['review_retrieval'] = {
            'request': request_data,
            'response': result
        }
        return result
    
    async def test_review_retrieval_with_valid_category(self) -> Dict[str, Any]:
        """Test the review retrieval endpoint with a valid category from matrix view."""
        logger.info("=" * 60)
        logger.info("Testing Review Retrieval API with Valid Category")
        logger.info("=" * 60)
        
        # Use category_id 12499 (Physical Installation Process) from matrix view results
        request_data = {
            "project_id": TEST_PROJECT_ID,
            "category_id": 12499,  # Physical Installation Process
            "product_id": TEST_ASINS[0],  # B00NG0ELL0
            "limit": 10,
            "offset": 0,
            "sort_by": "date",
            "sort_order": "desc"
        }
        
        result = await self.make_request("competitor-analysis/reviews", request_data)
        self.test_results['review_retrieval_valid_category'] = {
            'request': request_data,
            'response': result
        }
        return result
    
    async def test_all_endpoints(self) -> Dict[str, Any]:
        """Test all endpoints and return comprehensive results."""
        logger.info("🚀 Starting comprehensive API testing")
        logger.info(f"Testing project: {TEST_PROJECT_ID}")
        logger.info(f"Testing ASINs: {TEST_ASINS}")
        
        # Test all endpoints
        await self.test_competitor_summary()
        await self.test_competitor_matrix_view()
        await self.test_review_retrieval()
        await self.test_review_retrieval_with_valid_category() # Added new test
        
        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'project_id': TEST_PROJECT_ID,
            'test_asins': TEST_ASINS,
            'results': self.test_results
        }
        
        logger.info("=" * 60)
        logger.info("API Testing Summary")
        logger.info("=" * 60)
        
        for endpoint, result in self.test_results.items():
            status = "✅ PASS" if result['response'].get('success') else "❌ FAIL"
            logger.info(f"{endpoint}: {status}")
        
        return summary
    
    def save_results(self, filename: str = "api_test_results.json"):
        """Save test results to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"Test results saved to {filename}")


async def main():
    """Main test function."""
    async with APITester(API_BASE_URL) as tester:
        results = await tester.test_all_endpoints()
        tester.save_results()
        
        # Print summary
        print("\n" + "=" * 60)
        print("API TESTING COMPLETED")
        print("=" * 60)
        print(f"Results saved to: api_test_results.json")
        print(f"Test timestamp: {results['timestamp']}")
        print(f"Project ID: {results['project_id']}")
        print(f"Test ASINs: {len(results['test_asins'])} ASINs")
        
        # Count successes
        success_count = sum(1 for result in results['results'].values() 
                           if result['response'].get('success'))
        total_count = len(results['results'])
        
        print(f"Success rate: {success_count}/{total_count} endpoints")
        
        if success_count == total_count:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    asyncio.run(main()) 