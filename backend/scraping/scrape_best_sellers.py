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
        
        # Variables to store API metadata from first page
        first_page_metadata = {}
        
        while len(all_products) < target_count:
            try:
                print(f"  Fetching Amazon page {page} for '{search_term}'...")
                result = amazon_search(
                    search_term=search_term,
                    amazon_domain="amazon.com",
                    category_id=category_id,
                    sort_by="featured",
                    page=page,
                    exclude_sponsored=True
                )
                
                # Save metadata from first page
                if page == 1:
                    first_page_metadata = {
                        "request_info": result.get("request_info", {}),
                        "request_parameters": result.get("request_parameters", {}),
                        "request_metadata": result.get("request_metadata", {}),
                        "search_information": result.get("search_information", {}),
                        "pagination": result.get("pagination", {})
                    }
                
                if 'search_results' in result and result['search_results']:
                    products = result['search_results']
                    all_products.extend(products)
                    print(f"    Found {len(products)} products on page {page} (total: {len(all_products)})")
                    
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
        
        # Save only the final consolidated file with complete request information
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        search_term_clean = search_term.replace(" ", "_").lower()
        final_filename = f"amazon_search_{search_term_clean}_cat_{category_id}_all_products_{timestamp}.json"
        final_filepath = os.path.join(save_dir, final_filename)
        
        # Create structured data with complete API response information
        combined_data = {
            "request_info": first_page_metadata.get("request_info", {}),
            "request_parameters": first_page_metadata.get("request_parameters", {}),
            "request_metadata": first_page_metadata.get("request_metadata", {}),
            "search_information": first_page_metadata.get("search_information", {}),
            "pagination": first_page_metadata.get("pagination", {}),
            "scraping_summary": {
                "type": "search",
                "search_term": search_term,
                "category_id": category_id,
                "amazon_domain": "amazon.com",
                "total_pages_scraped": page - 1,
                "total_products": len(all_products),
                "max_products_requested": target_count,
                "sort_by": "featured",
                "exclude_sponsored": True
            },
            "search_results": all_products
        }
        
        with open(final_filepath, "w") as f:
            json.dump(combined_data, f, indent=4)

        return len(all_products), all_products, final_filepath

    # --- Logic for browsing a category or bestsellers page (no search term) ---
    elif url_type in ['category', 'bestsellers']:
        print(f"Scraping Amazon {url_type} page for category ID {category_id}...")
        
        # Define amazon_domain at the beginning of this branch
        amazon_domain = "amazon.com"
        
        if url_type == 'category':
            # For category scraping, implement pagination to get target_count products
            all_products = []
            page = 1
            
            # Variables to store API metadata from first page
            first_page_metadata = {}
            
            while len(all_products) < target_count:
                try:
                    print(f"  Fetching page {page}...")
                    
                    # Use the original get_products_from_category_rainforest function with page parameter
                    page_data = get_products_from_category_rainforest(
                        category_id=category_id,
                        page=page,
                        amazon_domain=amazon_domain
                    )
                    
                    # Save metadata from first page
                    if page == 1:
                        first_page_metadata = {
                            "request_info": page_data.get("request_info", {}),
                            "request_parameters": page_data.get("request_parameters", {}),
                            "request_metadata": page_data.get("request_metadata", {}),
                            "search_information": page_data.get("search_information", {}),
                            "category_information": page_data.get("category_information", {}),
                            "pagination": page_data.get("pagination", {})
                        }
                    
                    if not page_data or 'category_results' not in page_data:
                        print(f"  No data returned for page {page}, stopping")
                        break
                    
                    page_products = page_data.get('category_results', [])
                    if not page_products:
                        print(f"  No products found on page {page}, stopping")
                        break
                    
                    print(f"  Found {len(page_products)} products on page {page}")
                    all_products.extend(page_products)
                    
                    # If we have enough products, truncate to target_count
                    if len(all_products) >= target_count:
                        all_products = all_products[:target_count]
                        print(f"  Reached target of {target_count} products, stopping")
                        break
                    
                    page += 1
                    
                    # Add a small delay between pages to be respectful
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  Error fetching page {page}: {str(e)}")
                    break
            
            # Save the combined results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"amazon_{url_type}_cat_{category_id}_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)
            
            # Create combined data structure with complete API response information
            combined_data = {
                "request_info": first_page_metadata.get("request_info", {}),
                "request_parameters": first_page_metadata.get("request_parameters", {}),
                "request_metadata": first_page_metadata.get("request_metadata", {}),
                "search_information": first_page_metadata.get("search_information", {}),
                "category_information": first_page_metadata.get("category_information", {}),
                "pagination": first_page_metadata.get("pagination", {}),
                "scraping_summary": {
                    "type": "category",
                    "category_id": category_id,
                    "amazon_domain": amazon_domain,
                    "total_pages_scraped": page - 1,
                    "total_products": len(all_products),
                    "max_products_requested": target_count
                },
                "category_results": all_products
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)
            
            print(f"  Saved {len(all_products)} products to: {filename}")
            # Return 3 values as expected by scraping_service
            return len(all_products), all_products, filepath
            
        else:  # bestsellers
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"amazon_{url_type}_cat_{category_id}_{timestamp}.json"
            filepath = os.path.join(save_dir, filename)

            if os.path.exists(filepath):
                print(f"  Skipping (file exists): {filename}")
                # Return 3 values as expected by scraping_service
                return 0, [], filepath

            data = get_products_from_category_rainforest(
                category_id=category_id,
                amazon_domain=amazon_domain
            )

            if not data:
                print("  No data returned from API")
                # Return 3 values as expected by scraping_service
                return 0, [], filepath

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            products = data.get('category_results', [])
            print(f"  Saved {len(products)} products to: {filename}")
            # Return 3 values as expected by scraping_service
            return len(products), products, filepath
            
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