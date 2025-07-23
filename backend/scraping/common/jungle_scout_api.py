import requests
import os
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Jungle Scout API Configuration
JUNGLE_SCOUT_API_KEY = os.getenv("JUNGLE_SCOUT_API_KEY")
JUNGLE_SCOUT_BASE_URL = "https://developer.junglescout.com"
SALES_ESTIMATES_ENDPOINT = "/api/sales_estimates_query"

# Supported marketplaces
SUPPORTED_MARKETPLACES = ["us", "uk", "de", "in", "ca", "fr", "it", "es", "mx", "jp"]

class JungleScoutAPIError(Exception):
    """Custom exception for Jungle Scout API errors"""
    pass

def _validate_api_key():
    """Validate that the Jungle Scout API key is available"""
    if not JUNGLE_SCOUT_API_KEY:
        raise JungleScoutAPIError("JUNGLE_SCOUT_API_KEY environment variable is required")
    
    # API key should be in format "KEY_NAME:API_KEY"
    if ":" not in JUNGLE_SCOUT_API_KEY:
        # Try to use the API key directly as a fallback
        logger.warning("JUNGLE_SCOUT_API_KEY is not in 'KEY_NAME:API_KEY' format. Using as API key only.")
        logger.warning("For better compatibility, please set JUNGLE_SCOUT_API_KEY as 'KEY_NAME:API_KEY'")
        return False
    
    return True

def _validate_marketplace(marketplace: str):
    """Validate marketplace parameter"""
    if marketplace.lower() not in SUPPORTED_MARKETPLACES:
        available_marketplaces = ", ".join(SUPPORTED_MARKETPLACES)
        raise JungleScoutAPIError(
            f"Marketplace '{marketplace}' not supported. Available marketplaces: {available_marketplaces}"
        )

def _validate_date_format(date_str: str, date_name: str):
    """Validate date format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise JungleScoutAPIError(f"{date_name} must be in YYYY-MM-DD format")

def _validate_date_range(start_date: str, end_date: str):
    """Validate that end_date is after start_date and before current date"""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    current_date = date.today()
    
    if end_dt <= start_dt:
        raise JungleScoutAPIError("end_date must be after start_date")
    
    if end_dt >= current_date:
        raise JungleScoutAPIError("end_date must be before current date")

def get_sales_history(
    asin: str,
    marketplace: str = "us",
    start_date: str = None,
    end_date: str = None
) -> Dict[str, Any]:
    """
    Get sales history for a specific ASIN using Jungle Scout API.
    
    Args:
        asin (str): Amazon product ASIN to search for
        marketplace (str): Marketplace country code (default: "us")
        start_date (str): Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date (str): End date in YYYY-MM-DD format (default: yesterday)
    
    Returns:
        dict: JSON response containing sales estimates data
        
    Raises:
        JungleScoutAPIError: If API key is missing, parameters are invalid, or API request fails
        
    Example:
        >>> get_sales_history("B08N5WRWNW", "us", "2024-01-01", "2024-01-31")
    """
    # Validate API key
    has_key_name = _validate_api_key()
    
    # Validate marketplace
    _validate_marketplace(marketplace)
    
    # Set default dates if not provided
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Validate date formats
    _validate_date_format(start_date, "start_date")
    _validate_date_format(end_date, "end_date")
    
    # Validate date range
    _validate_date_range(start_date, end_date)
    
    # Prepare headers
    if has_key_name:
        # Use the full KEY_NAME:API_KEY format
        headers = {
            "Authorization": JUNGLE_SCOUT_API_KEY,
            "X-API-Type": "junglescout",
            "Accept": "application/vnd.junglescout.v1+json",
            "Content-Type": "application/vnd.api+json"
        }
    else:
        # Use just the API key (fallback for older format)
        headers = {
            "Authorization": JUNGLE_SCOUT_API_KEY,
            "X-API-Type": "junglescout",
            "Accept": "application/vnd.junglescout.v1+json",
            "Content-Type": "application/vnd.api+json"
        }
    
    # Prepare query parameters
    params = {
        "marketplace": marketplace.lower(),
        "asin": asin,
        "start_date": start_date,
        "end_date": end_date
    }
    
    # Make API request
    url = f"{JUNGLE_SCOUT_BASE_URL}{SALES_ESTIMATES_ENDPOINT}"
    
    try:
        logger.info(f"Fetching sales history for ASIN {asin} in marketplace {marketplace}")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        response = requests.get(url, headers=headers, params=params)
        
        # Log response status
        logger.info(f"API Response Status: {response.status_code}")
        
        # Handle different response status codes
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully retrieved sales data for ASIN {asin} with response: {data}")
            return data
        elif response.status_code == 401:
            raise JungleScoutAPIError("Authentication failed. Please check your API key.")
        elif response.status_code == 403:
            raise JungleScoutAPIError("Access denied. Please check your API key permissions.")
        elif response.status_code == 404:
            raise JungleScoutAPIError(f"No sales data found for ASIN {asin}")
        elif response.status_code == 429:
            raise JungleScoutAPIError("Rate limit exceeded. Please try again later.")
        else:
            # Try to get error details from response
            try:
                error_data = response.json()
                error_message = error_data.get("errors", [{}])[0].get("detail", "Unknown error")
            except:
                error_message = f"HTTP {response.status_code}: {response.text}"
            
            raise JungleScoutAPIError(f"API request failed: {error_message}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching sales history: {str(e)}")
        raise JungleScoutAPIError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching sales history: {str(e)}")
        raise JungleScoutAPIError(f"Unexpected error: {str(e)}")

def get_sales_history_batch(
    asins: list,
    marketplace: str = "us",
    start_date: str = None,
    end_date: str = None
) -> Dict[str, Dict[str, Any]]:
    """
    Get sales history for multiple ASINs.
    
    Args:
        asins (list): List of Amazon product ASINs
        marketplace (str): Marketplace country code (default: "us")
        start_date (str): Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date (str): End date in YYYY-MM-DD format (default: yesterday)
    
    Returns:
        dict: Dictionary with ASIN as key and sales data as value
        
    Example:
        >>> get_sales_history_batch(["B08N5WRWNW", "B07ZPKBL9V"], "us", "2024-01-01", "2024-01-31")
    """
    results = {}
    
    for asin in asins:
        try:
            results[asin] = get_sales_history(asin, marketplace, start_date, end_date)
        except JungleScoutAPIError as e:
            logger.error(f"Failed to get sales history for ASIN {asin}: {str(e)}")
            results[asin] = {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error for ASIN {asin}: {str(e)}")
            results[asin] = {"error": f"Unexpected error: {str(e)}"}
    
    return results

# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python jungle_scout_api.py <ASIN> [marketplace] [start_date] [end_date]")
        print("Example: python jungle_scout_api.py B08N5WRWNW us 2024-01-01 2024-01-31")
        sys.exit(1)
    
    asin = sys.argv[1]
    marketplace = sys.argv[2] if len(sys.argv) > 2 else "us"
    start_date = sys.argv[3] if len(sys.argv) > 3 else None
    end_date = sys.argv[4] if len(sys.argv) > 4 else None
    
    try:
        result = get_sales_history(asin, marketplace, start_date, end_date)
        print(f"Sales history for ASIN {asin}:")
        print(result)
    except JungleScoutAPIError as e:
        print(f"Error: {e}")
        sys.exit(1) 