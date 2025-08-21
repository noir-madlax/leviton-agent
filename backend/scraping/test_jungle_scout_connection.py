#!/usr/bin/env python3
"""
Test Jungle Scout API Connection

This script tests the connection to Jungle Scout API to verify:
1. API key is properly configured
2. API endpoint is accessible
3. Basic request/response functionality

Usage:
    python test_jungle_scout_connection.py
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to the path to import modules
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import the Jungle Scout API client
from common.jungle_scout_api import get_sales_history, JungleScoutAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_key_configuration():
    """Test if the API key is properly configured"""
    logger.info("Testing API key configuration...")
    
    # Check if environment variable is set
    api_key = os.getenv("JUNGLE_SCOUT_API_KEY")
    if not api_key:
        logger.error("❌ JUNGLE_SCOUT_API_KEY environment variable is not set")
        return False
    
    # Check if API key has the correct format
    if ":" not in api_key:
        logger.warning("⚠️ JUNGLE_SCOUT_API_KEY is not in 'KEY_NAME:API_KEY' format")
        logger.info("Using API key directly (fallback mode)")
        logger.info("For better compatibility, consider setting as 'KEY_NAME:API_KEY'")
    
    logger.info("✅ API key is properly configured")
    return True

def test_api_connection():
    """Test API connection with a sample ASIN"""
    logger.info("Testing API connection...")
    
    # Use a sample ASIN for testing (Amazon Echo Dot)
    test_asin = "B07FZ8S74R"
    
    try:
        logger.info(f"Testing with ASIN: {test_asin}")
        
        # Try to fetch sales history for a short date range
        result = get_sales_history(
            asin=test_asin,
            marketplace="us",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        logger.info("✅ API connection successful!")
        logger.info(f"Response type: {type(result)}")
        
        # Log response structure for debugging
        if isinstance(result, dict):
            logger.info(f"Response keys: {list(result.keys())}")
            if 'data' in result:
                data = result['data']
                if isinstance(data, list):
                    logger.info(f"Number of data records: {len(data)}")
                    if data:
                        logger.info(f"Sample record keys: {list(data[0].keys())}")
                else:
                    logger.info(f"Data type: {type(data)}")
        else:
            logger.info(f"Response: {result}")
        
        return True
        
    except JungleScoutAPIError as e:
        logger.error(f"❌ Jungle Scout API error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting Jungle Scout API Connection Test")
    logger.info("=" * 50)
    
    # Test 1: API key configuration
    key_ok = test_api_key_configuration()
    
    if not key_ok:
        logger.error("API key configuration failed. Please check your .env file.")
        return
    
    # Test 2: API connection
    connection_ok = test_api_connection()
    
    # Summary
    logger.info("=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    if key_ok and connection_ok:
        logger.info("✅ All tests passed! Jungle Scout API is working correctly.")
        logger.info("You can now run the Leviton sales history script.")
    else:
        logger.error("❌ Some tests failed. Please check the error messages above.")
        
        if not key_ok:
            logger.error("Fix: Set JUNGLE_SCOUT_API_KEY in your .env file")
        if not connection_ok:
            logger.error("Fix: Check your API key permissions and network connection")

if __name__ == "__main__":
    main() 