import json
import os
import time
from datetime import datetime
from src.competitor.amazon_api import amazon_search
from src.competitor.home_depot_api import home_depot_best_sellers

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")

# Map categories to Amazon category IDs and search terms
CATEGORY_MAPPING = {
    "Dimmer Switches": {
        "search_term": "dimmer switches",
        "category_id": "507840"
    },
    "Light Switches": {
        "search_term": "light switches", 
        "category_id": "6291359011"
    }
}

def create_directories():
    """Create necessary directories for storing scraped data"""
    base_dir = os.path.join(DATA_DIR, "scraped")
    amazon_dir = os.path.join(base_dir, "amazon")
    home_depot_dir = os.path.join(base_dir, "home_depot")
    
    os.makedirs(amazon_dir, exist_ok=True)
    os.makedirs(home_depot_dir, exist_ok=True)
    
    return amazon_dir, home_depot_dir

def scrape_amazon_best_sellers(category, target_count=100, save_dir=os.path.join(DATA_DIR, "scraped", "amazon")):
    """
    Scrape Amazon best sellers for a given category using Rainforest API search
    
    Args:
        category (str): Product category (e.g., "Dimmer Switches", "Light Switches")
        target_count (int): Target number of products to scrape
        save_dir (str): Directory to save results
    """
    print(f"Scraping Amazon best sellers for {category}...")
    
    if category not in CATEGORY_MAPPING:
        raise ValueError(f"Category '{category}' not supported. Available categories: {list(CATEGORY_MAPPING.keys())}")
    
    search_term = CATEGORY_MAPPING[category]["search_term"]
    category_id = CATEGORY_MAPPING[category]["category_id"]
    
    all_products = []
    page = 1
    
    while len(all_products) < target_count:
        try:
            # Create filename with parameters first to check if exists
            timestamp = datetime.now().strftime("%Y%m%d")
            category_clean = category.replace(" ", "_").lower()
            filename = f"amazon_search_{category_clean}_cat_{category_id}_page_{page}_sort_featured_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                print(f"  Skipping (file exists): {filename}")
                # Load existing file to count products
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_result = json.load(f)
                if 'search_results' in existing_result and existing_result['search_results']:
                    products = existing_result['search_results']
                    all_products.extend(products)
                    print(f"    Found {len(products)} products (total: {len(all_products)})")
                page += 1
                continue
            
            print(f"  Fetching Amazon page {page} for {category}...")
            result = amazon_search(
                search_term=search_term,
                amazon_domain="amazon.com",
                category_id=category_id,  # Use specific Amazon category ID
                sort_by="featured",  # Get featured/best selling products (bestsellers only works for Audible)
                page=page,
                exclude_sponsored=True  # Exclude sponsored results for cleaner data
            )
            
            # Save raw response
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"    Saved: {filename}")
            
            # Extract products from response (Rainforest API uses 'search_results')
            if 'search_results' in result and result['search_results']:
                products = result['search_results']
                all_products.extend(products)
                print(f"    Found {len(products)} products (total: {len(all_products)})")
                
                # If we have fewer products than expected, we might have hit the end
                if len(products) < 10:  # Rainforest API typical page size varies
                    print(f"    Reached end of results for {category}")
                    break
            else:
                print(f"    No products found in response for page {page}")
                break
            
            page += 1
            
            # Add delay to be respectful to the API
            time.sleep(1)
            
        except Exception as e:
            print(f"    Error fetching page {page}: {str(e)}")
            break
    
    print(f"  Completed Amazon {category}: {len(all_products)} products scraped")
    return len(all_products)

def scrape_home_depot_best_sellers(query, target_count=144, save_dir=os.path.join(DATA_DIR, "scraped", "home_depot")):
    """
    Scrape Home Depot best sellers for a given query
    
    Args:
        query (str): Search query (e.g., "dimmer switch", "light switch")
        target_count (int): Target number of products to scrape
        save_dir (str): Directory to save results
    """
    print(f"Scraping Home Depot best sellers for {query}...")
    
    # Home Depot API allows max 48 products per page
    products_per_page = 48
    pages_needed = (target_count + products_per_page - 1) // products_per_page  # Ceiling division
    
    all_products = []
    
    for page in range(1, pages_needed + 1):
        try:
            # Create filename with parameters first to check if exists
            timestamp = datetime.now().strftime("%Y%m%d")
            query_clean = query.replace(" ", "_").lower()
            filename = f"home_depot_best_sellers_{query_clean}_page_{page}_ps_{products_per_page}_sort_top_sellers_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                print(f"  Skipping (file exists): {filename}")
                # Load existing file to count products
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_result = json.load(f)
                if 'products' in existing_result and existing_result['products']:
                    products = existing_result['products']
                    all_products.extend(products)
                    print(f"    Found {len(products)} products (total: {len(all_products)})")
                continue
            
            print(f"  Fetching Home Depot page {page} for {query}...")
            result = home_depot_best_sellers(
                query=query,
                page=page,
                ps=products_per_page
            )
            
            # Save raw response
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"    Saved: {filename}")
            
            # Extract products from response
            if 'products' in result and result['products']:
                products = result['products']
                all_products.extend(products)
                print(f"    Found {len(products)} products (total: {len(all_products)})")
            else:
                print(f"    No products found in response for page {page}")
                break
            
            # Add delay to be respectful to the API
            time.sleep(1)
            
        except Exception as e:
            print(f"    Error fetching page {page}: {str(e)}")
            break
    
    print(f"  Completed Home Depot {query}: {len(all_products)} products scraped")
    return len(all_products)

def main():
    """Main function to orchestrate the scraping process"""
    print("Starting best sellers scraping process...")
    print("=" * 50)
    
    # Create directories
    amazon_dir, home_depot_dir = create_directories()
    
    # Categories to scrape
    amazon_categories = ["Dimmer Switches", "Light Switches"]
    home_depot_queries = ["dimmer switch", "light switch"]
    
    total_amazon_products = 0
    total_home_depot_products = 0
    
    # Scrape Amazon best sellers
    print("\n🔄 AMAZON SCRAPING")
    print("-" * 30)
    for category in amazon_categories:
        try:
            count = scrape_amazon_best_sellers(category, target_count=150, save_dir=amazon_dir)
            total_amazon_products += count
        except Exception as e:
            print(f"Error scraping Amazon {category}: {str(e)}")
    
    # Scrape Home Depot best sellers
    print("\n🔄 HOME DEPOT SCRAPING")
    print("-" * 30)
    for query in home_depot_queries:
        try:
            count = scrape_home_depot_best_sellers(query, target_count=144, save_dir=home_depot_dir)
            total_home_depot_products += count
        except Exception as e:
            print(f"Error scraping Home Depot {query}: {str(e)}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SCRAPING SUMMARY")
    print("=" * 50)
    print(f"Amazon products scraped: {total_amazon_products}")
    print(f"Home Depot products scraped: {total_home_depot_products}")
    print(f"Total products scraped: {total_amazon_products + total_home_depot_products}")
    print(f"Files saved in: {DATA_DIR}/scraped/")
    print("=" * 50)

if __name__ == "__main__":
    main() 