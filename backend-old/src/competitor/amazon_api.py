import requests
import dotenv
import os

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
    
    # Add authentication options
    if use_system_cookie:
        params["use_system_cookie"] = "true"
    elif cookie:
        params["cookie"] = cookie
    elif AMAZON_COOKIE:
        # Fall back to environment variable cookie
        params["cookie"] = AMAZON_COOKIE
    
    try:
        response = requests.get(UNWRANGLE_REVIEWS_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch Amazon reviews: {str(e)}")

def get_amazon_product(asin, domain="com", country="us", postal_code=None, language=None):
    """
    Get Amazon product details using ScrapingDog API. Documentation: https://docs.scrapingdog.com/amazon-scraper-api/amazon-product-scraper
    
    Args:
        asin (str): Amazon product ASIN (required)
        domain (str): Amazon TLD extension (e.g., "com", "co.uk", "de", "fr", "ca", "in") (default: "com")
        country (str): Country code (e.g., "us", "gb", "de", "fr", "ca", "in") (default: "us")
        postal_code (str): Postal code to get data from a particular location (optional)
        language (str): Language code using ISO 639-1 codes (e.g., "en", "de", "fr") (optional)
    
    Returns:
        dict: JSON response containing product details including title, price, images, description, etc.
        
    Supported domains:
        - com (amazon.com)
        - co.uk (amazon.co.uk)
        - ca (amazon.ca)
        - de (amazon.de)
        - es (amazon.es)
        - fr (amazon.fr)
        - it (amazon.it)
        - co.jp (amazon.co.jp)
        - in (amazon.in)
        - cn (amazon.cn)
        - com.sg (amazon.com.sg)
        - com.mx (amazon.com.mx)
        - ae (amazon.ae)
        - com.br (amazon.com.br)
        - nl (amazon.com.nl)
        - com.au (amazon.com.au)
        - com.tr (amazon.com.tr)
        - sa (amazon.sa)
        - se (amazon.se)
        - pl (amazon.pl)
        
    Supported countries:
        - us (United States)
        - gb (United Kingdom)
        - ca (Canada)
        - de (Germany)
        - es (Spain)
        - fr (France)
        - it (Italy)
        - jp (Japan)
        - in (India)
        - cn (China)
        - sg (Singapore)
        - mx (Mexico)
        - br (Brazil)
        - nl (Netherlands)
        - au (Australia)
        - tr (Turkey)
        - pl (Poland)
    """
    if not SCRAPINGDOG_API_KEY:
        raise ValueError("SCRAPINGDOG_API_KEY environment variable is required")
    
    if not asin:
        raise ValueError("ASIN is required")
    
    # Set up request parameters
    params = {
        "api_key": SCRAPINGDOG_API_KEY,
        "domain": domain,
        "asin": asin,
        "country": country
    }
    
    # Add optional parameters if provided
    if postal_code:
        params["postal_code"] = postal_code
    if language:
        params["language"] = language
    
    response = requests.get(SCRAPINGDOG_PRODUCT_URL, params=params)
    response.raise_for_status()
    return response.json()

def amazon_search(search_term=None, amazon_domain="amazon.com", number_of_results=None, fields=None,
                  include_products_count=None, refinements=None, category_id=None, sort_by=None,
                  exclude_sponsored=False, page=1, max_page=None, url=None, direct_search=False):
    """
    Search Amazon products using Rainforest API. Documentation: https://docs.trajectdata.com/rainforestapi/product-data-api/parameters/search
    
    Args:
        search_term (str): Search term to use for product search (required if url not provided)
        amazon_domain (str): Amazon domain to search (default: "amazon.com")
        number_of_results (int): Desired number of search results (optional)
        fields (str): Comma-separated list of fields to include in results (optional)
        include_products_count (int): Number of top results to include full product data for (costs extra credits) (optional)
        refinements (str): Comma-separated list of refinement values to filter results (optional)
        category_id (str): Category ID to limit search results to (optional)
        sort_by (str): Sort order for results (optional)
        exclude_sponsored (bool): Whether to exclude sponsored results (default: False)
        page (int): Current page of search results to retrieve (default: 1)
        max_page (int): Get multiple pages in one request (optional)
        url (str): Amazon search results page URL (alternative to search_term) (optional)
        direct_search (bool): Disable auto-correction of search terms (default: False)
    
    Returns:
        dict: JSON response containing search results
        
    Valid sort_by values:
        - "most_recent": Sort by newest arrivals
        - "price_low_to_high": Sort by lowest to highest price
        - "price_high_to_low": Sort by highest to lowest price
        - "featured": Sort by featured first
        - "average_review": Sort by average customer review
        - "relevance": Sort by most relevant first
        - "bestsellers": Sort by best sellers first (Audible only)
        - "running_time_ascending": Sort by shortest running time first (Audible only)
        - "running_time_descending": Sort by longest running time first (Audible only)
        - "title_ascending": Sort alphabetically A-Z (Audible only)
        - "title_descending": Sort alphabetically Z-A (Audible only)
        
    Supported Amazon domains:
        - amazon.com (US)
        - amazon.co.uk (UK)
        - amazon.ca (Canada)
        - amazon.de (Germany)
        - amazon.es (Spain)
        - amazon.fr (France)
        - amazon.it (Italy)
        - amazon.co.jp (Japan)
        - amazon.in (India)
        - amazon.com.au (Australia)
        - amazon.com.br (Brazil)
        - amazon.com.mx (Mexico)
        - And more...
    """
    if not RAINFOREST_API_KEY:
        raise ValueError("RAINFOREST_API_KEY environment variable is required")
    
    if not search_term and not url:
        raise ValueError("Either search_term or url parameter is required")
    
    if search_term and url:
        raise ValueError("Cannot specify both search_term and url parameters")
    
    # Set up required parameters
    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "search",
        "amazon_domain": amazon_domain,
        "page": page
    }
    
    # Add search term or URL
    if search_term:
        params["search_term"] = search_term
    if url:
        params["url"] = url
    
    # Add optional parameters if provided
    if number_of_results is not None:
        params["number_of_results"] = number_of_results
    if fields is not None:
        params["fields"] = fields
    if include_products_count is not None:
        params["include_products_count"] = include_products_count
    if refinements is not None:
        params["refinements"] = refinements
    if category_id is not None:
        params["category_id"] = category_id
    if sort_by is not None:
        params["sort_by"] = sort_by
    if exclude_sponsored:
        params["exclude_sponsored"] = "true"
    if max_page is not None:
        params["max_page"] = max_page
    if direct_search:
        params["direct_search"] = "true"
    
    response = requests.get(RAINFOREST_API_URL, params=params)
    response.raise_for_status()
    return response.json()

