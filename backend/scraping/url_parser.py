"""
Amazon URL Parser Service

This module provides functionality to parse different types of Amazon URLs
and extract relevant information for scraping operations.
"""

import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional, Tuple


def parse_amazon_url(url: str, max_products: int = 100, max_reviews: int = 50) -> Dict:
    """
    Parse Amazon URL and determine scraping strategy.
    
    Args:
        url (str): Amazon URL to parse
        max_products (int): Maximum number of products to scrape
        max_reviews (int): Maximum number of reviews to scrape
    
    Returns:
        Dict: Parsed URL information with scraping parameters
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    # Parse URL components
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path
    query_params = parse_qs(parsed_url.query)
    
    # Validate Amazon domain
    if not _is_amazon_domain(domain):
        raise ValueError(f"Not a valid Amazon URL: {url}")
    
    # Extract country code from domain
    country_code = _extract_country_code(domain)
    
    # Determine URL type and extract relevant information
    url_type, extracted_info = _analyze_url_path(path, query_params)
    
    # Build scraping parameters
    scraping_params = {
        "url": url,
        "url_type": url_type,
        "country_code": country_code,
        "max_products": max_products,
        "max_reviews": max_reviews,
        **extracted_info
    }
    
    # Determine scraping strategy
    strategy = _determine_scraping_strategy(url_type, extracted_info)
    scraping_params["strategy"] = strategy
    
    return scraping_params


def _is_amazon_domain(domain: str) -> bool:
    """Check if domain is a valid Amazon domain."""
    amazon_domains = [
        'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr',
        'amazon.it', 'amazon.es', 'amazon.ca', 'amazon.com.au',
        'amazon.co.jp', 'amazon.in', 'amazon.com.br', 'amazon.com.mx',
        'amazon.cn', 'amazon.sg', 'amazon.ae', 'amazon.sa',
        'amazon.nl', 'amazon.se', 'amazon.pl', 'amazon.tr'
    ]
    
    # Remove www. prefix if present
    domain = domain.replace('www.', '')
    
    return domain in amazon_domains


def _extract_country_code(domain: str) -> str:
    """Extract country code from Amazon domain."""
    domain_to_country = {
        'amazon.com': 'us',
        'amazon.co.uk': 'uk', 
        'amazon.de': 'de',
        'amazon.fr': 'fr',
        'amazon.it': 'it',
        'amazon.es': 'es',
        'amazon.ca': 'ca',
        'amazon.com.au': 'au',
        'amazon.co.jp': 'jp',
        'amazon.in': 'in',
        'amazon.com.br': 'br',
        'amazon.com.mx': 'mx',
        'amazon.cn': 'cn',
        'amazon.sg': 'sg',
        'amazon.ae': 'ae',
        'amazon.sa': 'sa',
        'amazon.nl': 'nl',
        'amazon.se': 'se',
        'amazon.pl': 'pl',
        'amazon.tr': 'tr'
    }
    
    domain = domain.replace('www.', '')
    return domain_to_country.get(domain, 'us')


def _analyze_url_path(path: str, query_params: Dict) -> Tuple[str, Dict]:
    """
    Analyze URL path and query parameters to determine URL type.
    
    Returns:
        Tuple[str, Dict]: (url_type, extracted_info)
    """
    path = path.lower()
    
    # Product page patterns
    if '/dp/' in path or '/gp/product/' in path:
        asin = _extract_asin_from_path(path)
        return 'product', {'asin': asin}
    
    # Search results
    if '/s' in path or 's?' in path:
        search_term = _extract_search_term(query_params)
        return 'search', {'search_term': search_term}
    
    # Best sellers / category pages
    if '/bestsellers/' in path or '/zgbs/' in path:
        category_info = _extract_category_info(path)
        return 'category', category_info
    
    # Store/brand pages
    if '/stores/' in path or '/brand/' in path:
        brand_info = _extract_brand_info(path, query_params)
        return 'brand', brand_info
    
    # Category pages with 'node' parameter
    if 'node' in query_params:
        category_id = query_params['node'][0]
        search_term = _extract_search_term(query_params)
        return 'category', {'category_id': category_id, 'search_term': search_term}
    
    # Default: try to extract search term from any query parameters
    search_term = _extract_search_term(query_params)
    if search_term:
        return 'search', {'search_term': search_term}
    
    # If nothing else matches, treat as general search
    return 'unknown', {'search_term': 'light switches'}


def _extract_asin_from_path(path: str) -> Optional[str]:
    """Extract ASIN from product URL path."""
    # Pattern for /dp/ASIN or /gp/product/ASIN
    asin_patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})'
    ]
    
    for pattern in asin_patterns:
        match = re.search(pattern, path, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def _extract_search_term(query_params: Dict) -> str:
    """Extract search term from query parameters."""
    # Common search parameter names
    search_keys = ['k', 'keywords', 'field-keywords', 'q', 'search']
    
    for key in search_keys:
        if key in query_params and query_params[key]:
            return query_params[key][0]  # Take first value
    
    # Default search term for electrical switches
    return None


def _extract_category_info(path: str) -> Dict:
    """Extract category information from bestsellers/category URLs."""
    # 尝试从路径中提取具体的category ID
    import re
    
    # 匹配Amazon category ID模式 (如 /hi/507840/ 或 /zgbs/hi/507840)
    category_id_match = re.search(r'/(?:hi|zgbs/hi)/(\d+)', path)
    if category_id_match:
        category_id = category_id_match.group(1)
        
        # 根据已知的category ID映射
        if category_id == "507840":
            return {
                'category_id': '507840',
                'category_name': 'Dimmer Switches',
                'search_term': 'dimmer switches'
            }
        elif category_id == "6291359011":
            return {
                'category_id': '6291359011',
                'category_name': 'Light Switches',
                'search_term': 'light switches'
            }
        else:
            # 未知category ID，使用默认
            return {
                'category_id': category_id,
                'category_name': 'Light Switches',  # 默认
                'search_term': 'light switches'
            }
    
    # 如果没有找到category ID，根据关键词推断
    category_mappings = {
        'dimmer': {'category_id': '507840', 'category_name': 'Dimmer Switches'},
        'switches': {'category_id': '6291359011', 'category_name': 'Light Switches'},
        'electrical': {'category_id': '6291359011', 'category_name': 'Light Switches'},
        'outlet': {'category_id': '6291359011', 'category_name': 'Light Switches'},
        'lighting': {'category_id': '6291359011', 'category_name': 'Light Switches'}
    }
    
    path_lower = path.lower()
    
    # Try to match category from path keywords
    for keyword, category_info in category_mappings.items():
        if keyword in path_lower:
            return {
                'category_id': category_info['category_id'],
                'category_name': category_info['category_name'],
                'search_term': category_info['category_name'].lower()
            }
    
    # Default to Light Switches category
    return {
        'category_id': '6291359011',
        'category_name': 'Light Switches',
        'search_term': 'light switches'
    }


def _extract_brand_info(path: str, query_params: Dict) -> Dict:
    """Extract brand information from store/brand URLs."""
    # Extract brand name from path or query
    brand_name = None
    
    # Try to extract from path
    brand_match = re.search(r'/stores/([^/]+)', path, re.IGNORECASE)
    if brand_match:
        brand_name = brand_match.group(1).replace('-', ' ').replace('_', ' ')
    
    # Try to extract from query parameters
    if not brand_name and 'brand' in query_params:
        brand_name = query_params['brand'][0]
    
    search_term = f"{brand_name} light switches" if brand_name else "light switches"
    
    return {
        'brand_name': brand_name,
        'search_term': search_term
    }


def _determine_scraping_strategy(url_type: str, extracted_info: Dict) -> str:
    """
    Determine the appropriate scraping strategy based on URL type.
    
    Args:
        url_type (str): Type of URL (product, search, category, etc.)
        extracted_info (Dict): Extracted information from URL
    
    Returns:
        str: Scraping strategy name
    """
    strategy_mapping = {
        'product': 'scrape_product_reviews',
        'search': 'scrape_search_results', 
        'category': 'scrape_category_products',
        'brand': 'scrape_search_results',
        'unknown': 'scrape_search_results'
    }
    
    return strategy_mapping.get(url_type, 'scrape_search_results')


# Test function for development
def test_url_parser():
    """Test the URL parser with various Amazon URLs."""
    test_urls = [
        "https://www.amazon.com/dp/B08N5WRWNW",
        "https://www.amazon.com/s?k=light+switches",
        "https://www.amazon.com/bestsellers/hi/507840",
        "https://www.amazon.com/stores/Leviton/page/12345",
        "https://amazon.com/gp/product/B08N5WRWNW?ref=sr_1_1"
    ]
    
    for url in test_urls:
        try:
            result = parse_amazon_url(url)
            print(f"URL: {url}")
            print(f"Result: {result}")
            print("-" * 50)
        except Exception as e:
            print(f"Error parsing {url}: {e}")
            print("-" * 50)


if __name__ == "__main__":
    test_url_parser() 