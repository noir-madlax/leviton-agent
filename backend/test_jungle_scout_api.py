#!/usr/bin/env python3
"""
Test Jungle Scout API Connectivity

This script tests basic connectivity and permissions for the Jungle Scout API.
"""

import sys
import asyncio
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from scraping.common.jungle_scout_api import get_sales_history

async def test_jungle_scout_api():
    """Test Jungle Scout API connectivity."""
    
    print("Testing Jungle Scout API connectivity...")
    print("=" * 50)
    
    # Test with a single ASIN and recent date range
    test_asin = "B00NG0ELL0"  # One of the ASINs from the project
    start_date = "2025-07-01"
    end_date = "2025-07-21"
    
    print(f"Testing ASIN: {test_asin}")
    print(f"Date range: {start_date} to {end_date}")
    print()
    
    try:
        print("Making API call...")
        result = get_sales_history(test_asin, "us", start_date, end_date)
        
        print("API Response:")
        print(f"Type: {type(result)}")
        print(f"Content: {result}")
        
        if isinstance(result, dict):
            print("\nResponse keys:")
            for key in result.keys():
                print(f"  - {key}")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        
        # Check if it's an API permission error
        if "403" in str(e) or "Access denied" in str(e):
            print("\nThis appears to be a permission issue.")
            print("Possible causes:")
            print("1. API key doesn't have sales history permissions")
            print("2. API key is expired or invalid")
            print("3. Rate limiting")
            print("4. Account doesn't have access to sales history data")
        
        elif "401" in str(e) or "Unauthorized" in str(e):
            print("\nThis appears to be an authentication issue.")
            print("Check if the API key is valid.")
        
        elif "429" in str(e) or "rate limit" in str(e).lower():
            print("\nThis appears to be a rate limiting issue.")
            print("Try again later or check your API usage limits.")

if __name__ == "__main__":
    asyncio.run(test_jungle_scout_api()) 