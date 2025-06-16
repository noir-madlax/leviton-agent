import json
import os
import time
from datetime import datetime
from .amazon_api import amazon_search, get_bestsellers_rainforest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def create_directories():
    """Create necessary directories for storing scraped data"""
    base_dir = os.path.join(DATA_DIR, "scraped")
    amazon_dir = os.path.join(base_dir, "amazon")
    home_depot_dir = os.path.join(base_dir, "home_depot")
    
    os.makedirs(amazon_dir, exist_ok=True)
    os.makedirs(home_depot_dir, exist_ok=True)
    
    return amazon_dir, home_depot_dir

def scrape_products_from_amazon(category_id: str, search_term: str, target_count: int = 100, save_dir: str = os.path.join(DATA_DIR, "scraped", "amazon")):
    """
    Scrape Amazon products for a given category_id and search_term using Rainforest API.
    If search_term is None, it will fetch bestsellers for the given category_id.
    
    Args:
        category_id (str): The Amazon category ID to search within.
        search_term (str): The search term to use. Can be None.
        target_count (int): Target number of products to scrape.
        save_dir (str): Directory to save results.
    """
    
    # If no search term, we are fetching bestsellers for a category
    is_bestsellers_scrape = not search_term

    if is_bestsellers_scrape:
        print(f"Scraping Amazon Bestsellers for category ID {category_id}...")
        # For bestsellers, we usually get one comprehensive list, so pagination logic is simpler.
        # We will make one call and handle the results.
        try:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"amazon_bestsellers_cat_{category_id}_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)

            if os.path.exists(filepath):
                print(f"  Skipping (file exists): {filename}")
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_result = json.load(f)
                products = existing_result.get('bestsellers', [])
                return len(products), products, filepath

            print(f"  Fetching Amazon Bestsellers for category '{category_id}'...")
            result = get_bestsellers_rainforest(
                amazon_domain="amazon.com",
                category_id=category_id
            )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"    Saved: {filename}")
            
            products = result.get('bestsellers', [])
            print(f"  Completed Amazon Bestsellers: {len(products)} products scraped")
            
            # Since bestsellers often come in one go, we save the full list directly
            final_filepath = os.path.join(save_dir, f"amazon_bestsellers_cat_{category_id}_all_products_{timestamp}.json")
            with open(final_filepath, "w") as f:
                json.dump(products, f, indent=4)
            
            return len(products), products, final_filepath

        except Exception as e:
            print(f"    Error fetching bestsellers: {str(e)}")
            return 0, [], ""
    
    # --- Existing logic for when search_term is present ---
    print(f"Scraping Amazon for '{search_term}' in category ID {category_id}...")
    
    all_products = []
    page = 1
    
    while len(all_products) < target_count:
        try:
            # Create filename with parameters first to check if it exists
            timestamp = datetime.now().strftime("%Y%m%d")
            search_term_clean = search_term.replace(" ", "_").lower()
            filename = f"amazon_search_{search_term_clean}_cat_{category_id}_page_{page}_sort_featured_{timestamp}.json"
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
            
            print(f"  Fetching Amazon page {page} for '{search_term}'...")
            result = amazon_search(
                search_term=search_term,
                amazon_domain="amazon.com",
                category_id=category_id,
                sort_by="featured",
                page=page,
                exclude_sponsored=True
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
                    print(f"    Reached end of results for {search_term}")
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
    
    print(f"  Completed Amazon '{search_term}': {len(all_products)} products scraped")
    
    # Save the final consolidated list of products
    timestamp = datetime.now().strftime("%Y%m%d")
    search_term_clean = search_term.replace(" ", "_").lower()
    final_filename = f"amazon_search_{search_term_clean}_cat_{category_id}_all_products_{timestamp}.json"
    final_filepath = os.path.join(save_dir, final_filename)
    
    with open(final_filepath, "w") as f:
        json.dump(all_products, f, indent=4)

    return len(all_products), all_products, final_filepath

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