import requests
import dotenv
import os
from typing import Optional, Dict, Any

dotenv.load_dotenv()

RAPID_API_KEY = os.getenv("RAPID_API_KEY")
UNWRANGLE_API_KEY = os.getenv("UNWRANGLE_API_KEY")
SCRAPINGDOG_API_KEY = os.getenv("SCRAPINGDOG_API_KEY")
RAINFOREST_API_KEY = os.getenv("RAINFOREST_API_KEY")

AMAZON_BEST_SELLERS_URL = "https://axesso-axesso-amazon-data-service-v1.p.rapidapi.com/amz/amazon-best-sellers-list"
AMAZON_PRODUCT_REVIEWS_URL = "https://axesso-axesso-amazon-data-service-v1.p.rapidapi.com/amz/amazon-review-details"
UNWRANGLE_REVIEWS_URL = "https://data.unwrangle.com/api/getter/"
SCRAPINGDOG_PRODUCT_URL = "https://api.scrapingdog.com/amazon/product"
RAINFOREST_API_URL = "https://api.rainforestapi.com/request"
AMAZON_COOKIE = os.getenv("AMAZON_COOKIE")
AMAZON_BEST_SELLERS_URL_DICT = {
    "Dimmer Switches": "https://www.amazon.com/Best-Sellers-Tools-Home-Improvement-Dimmer-Switches/zgbs/hi/507840/ref=zg_bs_nav_hi_4_6291358011",
    "Light Switches": "https://www.amazon.com/Best-Sellers-Tools-Home-Improvement-Electrical-Light-Switches/zgbs/hi/6291359011/ref=zg_bs_nav_hi_4_507840"
}

def amazon_best_sellers_list(category, page=1):
    """
    Get Amazon best sellers list using Axesso API. Documentation: https://axesso.developer.azure-api.net/api-details#api=axesso-amazon-data-service&operation=best-seller
    
    Args:
        category (str): Product category - must be one of the predefined categories
        page (int): Page number to retrieve (default: 1)
    
    Returns:
        dict: JSON response containing best sellers data
        
    Available categories:
        - Dimmer Switches
        - Light Switches  
    """
    if not RAPID_API_KEY:
        raise ValueError("RAPID_API_KEY environment variable is required")
    
    if category not in AMAZON_BEST_SELLERS_URL_DICT:
        available_categories = list(AMAZON_BEST_SELLERS_URL_DICT.keys())
        raise ValueError(f"Category '{category}' not supported. Available categories: {available_categories}")
    
    querystring = {
        "url": AMAZON_BEST_SELLERS_URL_DICT[category],
        "page": str(page)
    }
    
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "axesso-axesso-amazon-data-service-v1.p.rapidapi.com"
    }
    
    response = requests.get(AMAZON_BEST_SELLERS_URL, headers=headers, params=querystring)
    response.raise_for_status()
    return response.json()

def get_amazon_reviews(asin=None, url=None, country_code="US", page=1, max_pages=1, 
                      filter_by_star=None, sort_by=None, media_type=None, 
                      format_type=None, filter_by_keyword=None, reviewer_type=None,
                      cookie=None, use_system_cookie=False):
    """
    Get Amazon product reviews using Unwrangle API. 
    Documentation: https://docs.unwrangle.com/amazon-product-reviews-api/
    
    Args:
        asin (str): Amazon product ASIN (required if url not provided)
        url (str): Amazon product URL (alternative to asin, optional)
        country_code (str): Country code - US, CA, GB, FR, DE, ES, JP, AU, IN, BR, IT, BE (default: "US")
        page (int): Page number to start from (default: 1)
        max_pages (int): Maximum pages to fetch in one request, up to 10 (default: 1)
        filter_by_star (str): Filter reviews by rating:
                              - 'critical': 1-2 star reviews
                              - 'positive': 4-5 star reviews
                              - None: all reviews (default)
        sort_by (str): Sort order for reviews:
                       - 'recent': Sort by most recent (default)
                       - 'helpful': Sort by most helpful
                       - 'top_reviews': Sort by top reviews
        media_type (str): Filter by media type:
                          - 'media_reviews_only': Reviews with images/videos only
                          - 'all_content': All reviews (default)
        format_type (str): Product variant filter:
                          - 'all_formats': Reviews for all product variants (default)
                          - 'current_format': Reviews for current product variant only
        filter_by_keyword (str): Filter reviews containing specific keyword/phrase (case-insensitive)
        reviewer_type (str): Type of reviews:
                            - 'all_reviews': All reviews (default)
                            - 'avp_only_reviews': Verified Purchase only
        cookie (str): Amazon account cookie for accessing more than 8 reviews (optional)
        use_system_cookie (bool): Use system-managed cookie (US, DE, GB only) - costs 10 credits per page (default: False)
    
    Returns:
        dict: JSON response containing reviews and metadata including:
              - reviews: List of review objects
              - meta_data: Rating distribution, total ratings, etc.
              - pages_fetched: Number of pages actually fetched
              - credits_used: Credits consumed for this request
              - remaining_credits: Remaining API credits
    
    Supported Countries:
        - US: Amazon.com (USA)
        - CA: Amazon.ca (Canada) 
        - GB: Amazon.co.uk (UK)
        - FR: Amazon.fr (France)
        - DE: Amazon.de (Germany)
        - ES: Amazon.es (Spain)
        - JP: Amazon.co.jp (Japan)
        - AU: Amazon.com.au (Australia)
        - IN: Amazon.in (India)
        - BR: Amazon.com.br (Brazil)
        - IT: Amazon.it (Italy)
        - BE: Amazon.com.be (Belgium)
    
    Rate Limiting & Credits:
        - US: 1 credit per page
        - Other countries: 2.5 credits per page
        - System cookie: 10 credits per page (US, DE, GB only)
        - Multi-page requests: Base cost × pages fetched
    
    Authentication Notes:
        - As of Nov 2024, Amazon requires login to view reviews
        - Without cookie: Limited to ~8 most recent reviews
        - With cookie or use_system_cookie=True: Full access to all reviews
        - System cookie available for US, DE, GB markets only
    """
    if not UNWRANGLE_API_KEY:
        raise ValueError("UNWRANGLE_API_KEY environment variable is required")
    
    if not asin and not url:
        raise ValueError("Either 'asin' or 'url' parameter is required")
    
    if asin and url:
        raise ValueError("Cannot specify both 'asin' and 'url' parameters")
    
    # Validate country code
    valid_countries = ["US", "CA", "GB", "FR", "DE", "ES", "JP", "AU", "IN", "BR", "IT", "BE"]
    if country_code.upper() not in valid_countries:
        raise ValueError(f"Invalid country_code '{country_code}'. Must be one of: {valid_countries}")
    
    # Validate max_pages
    if max_pages < 1 or max_pages > 10:
        raise ValueError("max_pages must be between 1 and 10")
    
    # Validate filter_by_star
    valid_star_filters = ["all_stars", "five_star", "four_star", "three_star", "two_star", "one_star", "positive", "critical"]
    if filter_by_star and filter_by_star not in valid_star_filters:
        raise ValueError(f"filter_by_star must be one of {valid_star_filters} or None")
    
    # Validate sort_by
    if sort_by and sort_by not in ["recent", "helpful"]:
        raise ValueError("sort_by must be 'recent', 'helpful', or None")
    
    # Validate media_type
    if media_type and media_type not in ["all_content", "media_reviews_only"]:
        raise ValueError("media_type must be 'all_content', 'media_reviews_only', or None")
    
    # Validate format_type
    if format_type and format_type not in ["all_formats", "current_format"]:
        raise ValueError("format_type must be 'all_formats', 'current_format', or None")
        
    # Validate reviewer_type
    if reviewer_type and reviewer_type not in ["all_reviews", "avp_only_reviews"]:
        raise ValueError("reviewer_type must be 'all_reviews', 'avp_only_reviews', or None")
    
    # Validate use_system_cookie availability
    if use_system_cookie and country_code.upper() not in ["US", "DE", "GB"]:
        raise ValueError("use_system_cookie is only available for US, DE, and GB markets")
    
    # Build request parameters
    params = {
        "platform": "amazon_reviews",
        "country_code": country_code.upper(),
        "page": page,
        "max_pages": max_pages,
        "api_key": UNWRANGLE_API_KEY
    }
    
    # Add Amazon cookie if available (required for more than 8 reviews)
    if AMAZON_COOKIE:
        params["cookie"] = AMAZON_COOKIE
    # Add asin or url
    if asin:
        params["asin"] = asin
    if url:
        params["url"] = url
    
    # Add optional filtering parameters
    if filter_by_star:
        params["filter_by_star"] = filter_by_star
    if sort_by:
        params["sort_by"] = sort_by
    if media_type:
        params["media_type"] = media_type
    if format_type:
        params["format_type"] = format_type
    if filter_by_keyword:
        params["filter_by_keyword"] = filter_by_keyword
    if reviewer_type:
        params["reviewer_type"] = reviewer_type
    if use_system_cookie:
        params["use_system_cookie"] = "1"  # String format for URL params
    
    # Add optional cookie parameter
    if cookie:
        params["cookie"] = cookie
    
    try:
        response = requests.get(UNWRANGLE_REVIEWS_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching reviews: {e}")
        return None

def get_amazon_product(asin, domain="com", country="us", postal_code=None, language=None):
    """
    Get Amazon product details using ScrapingDog API.
    
    Args:
        asin (str): Amazon product ASIN
        domain (str): Amazon domain (com, ca, co.uk, de, fr, it, es)
        country (str): Country code (us, ca, gb, de, fr, it, es)
        postal_code (str): Postal code for location-based pricing (optional)
        language (str): Language code (en, de, fr, it, es) (optional)
    
    Returns:
        dict: Product data including price, availability, reviews, etc.
    """
    if not SCRAPINGDOG_API_KEY:
        raise ValueError("SCRAPINGDOG_API_KEY environment variable is required")
    
    params = {
        "api_key": SCRAPINGDOG_API_KEY,
        "asin": asin,
        "domain": domain,
        "country": country
    }
    
    # Add optional parameters
    if postal_code:
        params["postal_code"] = postal_code
    if language:
        params["language"] = language
    
    try:
        response = requests.get(SCRAPINGDOG_PRODUCT_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching product: {e}")
        return None

def get_product_details_rainforest(asin: str, amazon_domain: str = "amazon.com"):
    """
    Get product details using Rainforest API.
    
    Args:
        asin (str): Amazon product ASIN
        amazon_domain (str): Amazon domain (default: amazon.com)
    
    Returns:
        dict: Product details from Rainforest API
    """
    if not RAINFOREST_API_KEY:
        raise ValueError("RAINFOREST_API_KEY environment variable is required")
    
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "product",
        "asin": asin,
        "amazon_domain": amazon_domain
    }
    
    try:
        response = requests.get(RAINFOREST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching product details: {e}")
        return None

def get_bestsellers_rainforest(amazon_domain: str = "amazon.com", category_id: str = None, url: str = None):
    """
    Get Amazon bestsellers using Rainforest API.
    
    Args:
        amazon_domain (str): Amazon domain (default: amazon.com)
        category_id (str): Category ID (optional if url provided)
        url (str): Direct URL to bestsellers page (optional if category_id provided)
    
    Returns:
        dict: Bestsellers data from Rainforest API
    """
    if not RAINFOREST_API_KEY:
        raise ValueError("RAINFOREST_API_KEY environment variable is required")
    
    if not category_id and not url:
        raise ValueError("Either category_id or url must be provided")
    
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "bestsellers",
        "amazon_domain": amazon_domain
    }
    
    if category_id:
        params["category_id"] = category_id
    if url:
        params["url"] = url
    
    try:
        response = requests.get(RAINFOREST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bestsellers: {e}")
        return None

def amazon_search(search_term: str, category_id: str, amazon_domain: str = "amazon.com", 
                  sort_by: str = "featured", page: int = 1, exclude_sponsored: bool = True):
    """
    Search Amazon products using Rainforest API.
    
    Args:
        search_term (str): Search query
        category_id (str): Amazon category ID
        amazon_domain (str): Amazon domain (default: amazon.com)
        sort_by (str): Sort order (featured, price_low_to_high, price_high_to_low, etc.)
        page (int): Page number (default: 1)
        exclude_sponsored (bool): Exclude sponsored results (default: True)
    
    Returns:
        dict: Search results from Rainforest API
    """
    if not RAINFOREST_API_KEY:
        raise ValueError("RAINFOREST_API_KEY environment variable is required")
    
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "search",
        "query": search_term,
        "amazon_domain": amazon_domain,
        "sort_by": sort_by,
        "page": page
    }
    
    if category_id:
        params["category_id"] = category_id
    
    if exclude_sponsored:
        params["exclude_sponsored"] = "true"
    
    try:
        response = requests.get(RAINFOREST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching Amazon: {e}")
        return None

def search_for_category_rainforest(category_name: str) -> Optional[Dict[str, Any]]:
    """
    Search for category information using Rainforest API.
    
    Args:
        category_name (str): Name of the category to search for
    
    Returns:
        dict: Category search results or None if failed
    """
    if not RAINFOREST_API_KEY:
        raise ValueError("RAINFOREST_API_KEY environment variable is required")
    
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "category",
        "query": category_name,
        "amazon_domain": "amazon.com"
    }
    
    try:
        response = requests.get(RAINFOREST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching for category: {e}")
        return None

def get_products_from_category_rainforest(category_id: str, amazon_domain: str = "amazon.com", page: int = 1):
    """
    Get products from a specific category using Rainforest API.
    
    Args:
        category_id (str): Amazon category ID
        amazon_domain (str): Amazon domain (default: amazon.com)
        page (int): Page number (default: 1)
    
    Returns:
        dict: Category products from Rainforest API
    """
    if not RAINFOREST_API_KEY:
        raise ValueError("RAINFOREST_API_KEY environment variable is required")
    
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "category",
        "category_id": category_id,
        "amazon_domain": amazon_domain,
        "page": page
    }
    
    try:
        response = requests.get(RAINFOREST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching category products: {e}")
        return None 