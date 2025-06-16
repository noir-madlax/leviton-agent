import json
import os
import time
from datetime import datetime
from .amazon_api import amazon_search, get_bestsellers_rainforest, get_products_from_category_rainforest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def get_bestsellers_url(category_id: str, domain: str = "amazon.com") -> str:
    """Constructs the URL for Amazon Bestsellers for a given category ID."""
    return f"https://www.{domain}/gp/bestsellers/{category_id}"

def create_directories():
    """Create necessary directories for storing scraped data"""
    base_dir = os.path.join(DATA_DIR, "scraped")
    amazon_dir = os.path.join(base_dir, "amazon")
    home_depot_dir = os.path.join(base_dir, "home_depot")
    
    os.makedirs(amazon_dir, exist_ok=True)
    os.makedirs(home_depot_dir, exist_ok=True)
    
    return amazon_dir, home_depot_dir

def scrape_products_from_amazon(
    category_id: str, 
    search_term: str, 
    target_count: int = 100, 
    save_dir: str = os.path.join(DATA_DIR, "scraped", "amazon"),
    url_type: str = None,
    original_url: str = None
):
    """
    Scrape Amazon products using Rainforest API based on the type of request.
    
    Args:
        category_id (str): The Amazon category ID.
        search_term (str): The search term to use. Can be None.
        target_count (int): Target number of products to scrape.
        save_dir (str): Directory to save results.
        url_type (str): The type of the original URL ('search', 'category', 'bestsellers').
        original_url (str): The original URL provided by the user.
    """
    
    # --- Logic for search terms ---
    if search_term:
        print(f"Scraping Amazon for '{search_term}' in category ID {category_id}...")
        all_products = []
        page = 1
        
        while len(all_products) < target_count:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                search_term_clean = search_term.replace(" ", "_").lower()
                filename = f"amazon_search_{search_term_clean}_cat_{category_id}_page_{page}_sort_featured_{timestamp}.json"
                filepath = os.path.join(save_dir, filename)
                
                if os.path.exists(filepath):
                    print(f"  Skipping (file exists): {filename}")
                    with open(filepath, 'r', encoding='utf-8') as f:
                        existing_result = json.load(f)
                    if 'search_results' in existing_result and existing_result['search_results']:
                        products = existing_result['search_results']
                        all_products.extend(products)
                        print(f"    Found {len(products)} products (total: {len(all_products)})")
                    page += 1
                    continue
                
                print(f"  Fetching Amazon page {page} for '{search_term}'...")
                result = amazon_search(
                    search_term=search_term,
                    amazon_domain="amazon.com",
                    category_id=category_id,
                    sort_by="featured",
                    page=page,
                    exclude_sponsored=True
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"    Saved: {filename}")
                
                if 'search_results' in result and result['search_results']:
                    products = result['search_results']
                    all_products.extend(products)
                    print(f"    Found {len(products)} products (total: {len(all_products)})")
                    
                    if len(products) < 10:
                        print(f"    Reached end of results for {search_term}")
                        break
                else:
                    print(f"    No products found in response for page {page}")
                    break
                
                page += 1
                time.sleep(1)
                
            except Exception as e:
                print(f"    Error fetching page {page}: {str(e)}")
                break
        
        print(f"  Completed Amazon '{search_term}': {len(all_products)} products scraped")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        search_term_clean = search_term.replace(" ", "_").lower()
        final_filename = f"amazon_search_{search_term_clean}_cat_{category_id}_all_products_{timestamp}.json"
        final_filepath = os.path.join(save_dir, final_filename)
        
        with open(final_filepath, "w") as f:
            json.dump(all_products, f, indent=4)

        return len(all_products), all_products, final_filepath

    # --- Logic for browsing a category or bestsellers page (no search term) ---
    elif url_type in ['category', 'bestsellers']:
        print(f"Scraping Amazon {url_type} page for category ID {category_id}...")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"amazon_{url_type}_cat_{category_id}_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)

            if os.path.exists(filepath):
                print(f"  Skipping (file exists): {filename}")
                with open(filepath, 'r', encoding='utf-8') as f:
                    result = json.load(f)
            else:
                print(f"  Fetching Amazon {url_type} page using category ID: {category_id}")
                if url_type == 'category':
                    result = get_products_from_category_rainforest(category_id=category_id)
                else: # 'bestsellers'
                    # Bestsellers still requires a full URL to be constructed or passed
                    if not original_url:
                         raise ValueError("Bestsellers scraping requires a URL.")
                    print(f"  Fetching Amazon {url_type} page: {original_url}")
                    result = get_bestsellers_rainforest(url=original_url)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"    Saved: {filename}")

            products = result.get('category_results', []) if url_type == 'category' else result.get('bestsellers', [])
            print(f"  Completed Amazon {url_type}: {len(products)} products scraped")

            final_filepath = os.path.join(save_dir, f"amazon_{url_type}_cat_{category_id}_all_products_{timestamp}.json")
            with open(final_filepath, "w") as f:
                json.dump(products, f, indent=4)
            
            return len(products), products, final_filepath

        except Exception as e:
            print(f"    Error fetching {url_type} page: {str(e)}")
            return 0, [], ""
            
    else:
        print(f"Warning: No valid scraping strategy for url_type='{url_type}' and no search_term.")
        return 0, [], ""

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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
    
    # This main block is now for manual testing only. 
    # The new dynamic logic is handled by the scraping_service.
    print("Running manual test for scrape_products_from_amazon...")
    try:
        # Example: Scrape "Dimmer Switches"
        count, _ = scrape_products_from_amazon(
            category_id="507840",
            search_term="dimmer switches",
            target_count=20,
            save_dir=amazon_dir
        )
        print(f"Scraped {count} products for Dimmer Switches.")
    except Exception as e:
        print(f"Error scraping Amazon: {str(e)}")

if __name__ == "__main__":
    main() 