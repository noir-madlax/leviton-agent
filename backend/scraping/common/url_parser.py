import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional


def parse_amazon_url(url: str, max_products: int = 100, max_reviews: int = 50) -> Dict[str, Any]:
    """
    Parse Amazon URL and extract relevant information for scraping.
    
    Args:
        url (str): Amazon URL to parse
        max_products (int): Maximum number of products to scrape
        max_reviews (int): Maximum number of reviews to scrape
    
    Returns:
        dict: Dictionary containing parsed information
    """
    parsed_url = urlparse(url)
    
    # Determine the type of Amazon URL
    if "/dp/" in url or "/gp/product/" in url:
        # Product page URL
        asin = extract_asin_from_url(url)
        if not asin:
            raise ValueError("Could not extract ASIN from product URL")
        
        return {
            "url_type": "product",
            "asin": asin,
            "max_products": max_products,
            "max_reviews": max_reviews,
            "original_url": url
        }
    
    elif "/s?" in url:
        # Search results URL
        query_params = parse_qs(parsed_url.query)
        search_term = query_params.get('k', [''])[0]
        category_id = query_params.get('rh', [''])[0]
        
        # Extract category from rh parameter if present
        if category_id and 'n:' in category_id:
            category_match = re.search(r'n:(\d+)', category_id)
            if category_match:
                category_id = category_match.group(1)
        
        return {
            "url_type": "search",
            "search_term": search_term,
            "category_id": category_id,
            "max_products": max_products,
            "max_reviews": max_reviews,
            "original_url": url
        }
    
    elif "/zgbs/" in url or "/best-sellers/" in url:
        # Best sellers URL
        category_id = extract_category_from_bestsellers_url(url)
        
        return {
            "url_type": "bestsellers",
            "category_id": category_id,
            "max_products": max_products,
            "max_reviews": max_reviews,
            "original_url": url
        }
    
    elif re.search(r'/[a-zA-Z0-9-]+/dp/([A-Z0-9]{10})', url):
        # Alternative product URL format
        asin = re.search(r'/dp/([A-Z0-9]{10})', url).group(1)
        
        return {
            "url_type": "product",
            "asin": asin,
            "max_products": max_products,
            "max_reviews": max_reviews,
            "original_url": url
        }
    
    else:
        # Try to extract category from general category URLs
        category_id = extract_category_from_general_url(url)
        
        return {
            "url_type": "category",
            "category_id": category_id,
            "max_products": max_products,
            "max_reviews": max_reviews,
            "original_url": url
        }


def extract_asin_from_url(url: str) -> Optional[str]:
    """
    Extract ASIN from Amazon product URL.
    
    Args:
        url (str): Amazon product URL
    
    Returns:
        str: ASIN if found, None otherwise
    """
    # Common ASIN patterns
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
        r'asin=([A-Z0-9]{10})',
        r'/([A-Z0-9]{10})(?:[/?]|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_category_from_bestsellers_url(url: str) -> Optional[str]:
    """
    Extract category ID from Amazon best sellers URL.
    
    Args:
        url (str): Amazon best sellers URL
    
    Returns:
        str: Category ID if found, None otherwise
    """
    # Pattern for best sellers category URLs
    patterns = [
        r'/zgbs/[^/]+/(\d+)',
        r'/best-sellers/[^/]+/(\d+)',
        r'/zgbs/(\d+)',
        r'/best-sellers/(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_category_from_general_url(url: str) -> Optional[str]:
    """
    Extract category ID from general Amazon category URLs.
    
    Args:
        url (str): Amazon category URL
    
    Returns:
        str: Category ID if found, None otherwise
    """
    # Pattern for general category URLs
    patterns = [
        r'/b/ref=([^?]+)',
        r'node=(\d+)',
        r'/(\d+)(?:[/?]|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def validate_amazon_url(url: str) -> bool:
    """
    Validate if the URL is a valid Amazon URL.
    
    Args:
        url (str): URL to validate
    
    Returns:
        bool: True if valid Amazon URL, False otherwise
    """
    if not url:
        return False
    
    parsed_url = urlparse(url)
    amazon_domains = [
        'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr',
        'amazon.it', 'amazon.es', 'amazon.ca', 'amazon.com.au',
        'amazon.co.jp', 'amazon.in', 'amazon.com.br', 'amazon.com.mx'
    ]
    
    return any(domain in parsed_url.netloc.lower() for domain in amazon_domains)


def get_amazon_domain_from_url(url: str) -> str:
    """
    Extract Amazon domain from URL.
    
    Args:
        url (str): Amazon URL
    
    Returns:
        str: Amazon domain (e.g., 'amazon.com')
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc.lower().replace('www.', '') 