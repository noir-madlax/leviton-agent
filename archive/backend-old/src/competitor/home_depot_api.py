from serpapi import GoogleSearch
import json
import dotenv
import os
import requests

dotenv.load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")
BIGBOX_API_KEY = os.getenv("BIGBOX_API_KEY")

def home_depot_search(query, page=1, sort_by="top_sellers", hd_filter_tokens=None, delivery_zip=None, 
                     store_id=None, nao=None, ps=48, lowerbound=None, upperbound=None, 
                     no_cache=False, async_search=False, zero_trace=False, output="json"):
    """
    Search Home Depot products with flexible sorting options. Documentation: https://serpapi.com/home-depot-search-api and https://serpapi.com/home-depot-sorting
    
    Args:
        query (str): Search query (required)
        page (int): Page number (default: 1)
        sort_by (str): Sorting option - 'top_sellers', 'price_low_to_high', 'price_high_to_low', 'top_rated', 'best_match'
        hd_filter_tokens (str): Filter tokens divided by comma (optional)
        delivery_zip (str): ZIP Postal code to filter shipping products by area (optional)
        store_id (str): Store ID to filter products by specific store (optional)
        nao (int): Offset for products result (48 products per page: 0, 48, 96, etc.) (optional)
        ps (int): Number of items per page (default: 48, max: 48) (optional)
        lowerbound (float): Lower bound for price in USD (optional)
        upperbound (float): Upper bound for price in USD (optional)
        no_cache (bool): Force fresh results (default: False) (optional)
        async_search (bool): Submit search asynchronously (default: False) (optional)
        zero_trace (bool): Enterprise only - skip storing search data (default: False) (optional)
        output (str): Output format - 'json' or 'html' (default: 'json') (optional)
    
    Returns:
        dict: API response
    """
    params = {
        "engine": "home_depot",
        "q": query,
        "api_key": SERP_API_KEY,
        "page": page,
        "hd_sort": sort_by,
        "ps": ps,
        "output": output
    }
    
    # Add optional parameters if provided
    if hd_filter_tokens is not None:
        params["hd_filter_tokens"] = hd_filter_tokens
    if delivery_zip is not None:
        params["delivery_zip"] = delivery_zip
    if store_id is not None:
        params["store_id"] = store_id
    if nao is not None:
        params["nao"] = nao
    if lowerbound is not None:
        params["lowerbound"] = lowerbound
    if upperbound is not None:
        params["upperbound"] = upperbound
    if no_cache:
        params["no_cache"] = "true"
    if async_search:
        params["async"] = "true"
    if zero_trace:
        params["zero_trace"] = "true"
    
    search = GoogleSearch(params)
    results = search.get_dict()
    return results

def home_depot_best_sellers(query, page=1, hd_filter_tokens=None, delivery_zip=None, 
                           store_id=None, nao=None, ps=24, lowerbound=None, upperbound=None):
    """
    Get best selling products from Home Depot
    
    Args:
        query (str): Search query (required)
        page (int): Page number (default: 1)
        hd_filter_tokens (str): Filter tokens divided by comma (optional)
        delivery_zip (str): ZIP Postal code to filter shipping products by area (optional)
        store_id (str): Store ID to filter products by specific store (optional)
        nao (int): Offset for products result (optional)
        ps (int): Number of items per page (default: 24, max: 48) (optional)
        lowerbound (float): Lower bound for price in USD (optional)
        upperbound (float): Upper bound for price in USD (optional)
    
    Returns:
        dict: API response with best sellers
    """
    return home_depot_search(
        query=query, 
        page=page, 
        sort_by="top_sellers",
        hd_filter_tokens=hd_filter_tokens,
        delivery_zip=delivery_zip,
        store_id=store_id,
        nao=nao,
        ps=ps,
        lowerbound=lowerbound,
        upperbound=upperbound
    )

def home_depot_product_reviews(item_id=None, gtin=None, url=None, sort_by="most_helpful", 
                              search_term=None, reviewer_type="verified_purchase", 
                              five_star=None, four_star=None, three_star=None, 
                              two_star=None, one_star=None, page=1, max_page=None):
    """
    Get customer reviews for a Home Depot product using BigBox API. https://docs.trajectdata.com/bigboxapi/homedepot-product-data-api/parameters/reviews
    
    Args:
        item_id (str): Home Depot item ID to retrieve reviews for (required if gtin/url not provided)
        gtin (str): GTIN/ISBN/UPC code to look up matching product (optional)
        url (str): Home Depot reviews page URL to retrieve reviews from (optional)
        sort_by (str): Sort order - 'photo_reviews', 'most_helpful', 'newest_to_oldest', 
                      'oldest_to_newest', 'high_to_low_rating', 'low_to_high_rating' (default: 'most_helpful')
        search_term (str): Search term to use to search reviews (optional)
        reviewer_type (str): Type of reviewer - 'verified_purchase' or 'all' (default: 'verified_purchase')
        five_star (bool): Filter to only 5-star reviews (optional)
        four_star (bool): Filter to only 4-star reviews (optional)
        three_star (bool): Filter to only 3-star reviews (optional)
        two_star (bool): Filter to only 2-star reviews (optional)
        one_star (bool): Filter to only 1-star reviews (optional)
        page (int): Current page of reviews to retrieve (default: 1, max 10 reviews per page)
        max_page (int): Get multiple pages in one request (optional)
    
    Returns:
        dict: API response with customer reviews
    """
    # Validate required parameters
    if not item_id and not gtin and not url:
        return {"error": "One of item_id, gtin, or url is required"}
    
    # Set up the request parameters
    params = {
        'api_key': BIGBOX_API_KEY,
        'type': 'reviews',
        'sort_by': sort_by,
        'reviewer_type': reviewer_type,
        'page': page
    }
    
    # Add identification parameter (priority: item_id > gtin > url)
    if item_id:
        params['item_id'] = item_id
    elif gtin:
        params['gtin'] = gtin
    elif url:
        params['url'] = url
    
    # Add optional parameters if provided
    if search_term is not None:
        params['search_term'] = search_term
    if five_star is not None:
        params['five_star'] = str(five_star).lower()
    if four_star is not None:
        params['four_star'] = str(four_star).lower()
    if three_star is not None:
        params['three_star'] = str(three_star).lower()
    if two_star is not None:
        params['two_star'] = str(two_star).lower()
    if one_star is not None:
        params['one_star'] = str(one_star).lower()
    if max_page is not None:
        params['max_page'] = max_page
    
    # Make the HTTP GET request to BigBox API
    api_result = requests.get('https://api.bigboxapi.com/request', params)
    return api_result.json()
    