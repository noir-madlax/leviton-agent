import json
import os
import pandas as pd
from datetime import datetime
import glob
from typing import Dict, List, Any
import time
from src.competitor.amazon_api import get_amazon_product

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def extract_amazon_product(product: Dict[str, Any], category: str, extract_date: str) -> Dict[str, Any]:
    """Extract relevant fields from Amazon product data"""
    
    # Handle price - get the primary/current price
    price_usd = None
    list_price_usd = None
    
    if 'price' in product and product['price']:
        price_info = product['price']
        if isinstance(price_info, dict) and 'value' in price_info:
            price_usd = price_info['value']
            if 'list_price' in price_info:
                # Extract numeric value from list_price string like "$28.33"
                list_price_str = price_info['list_price'].replace('$', '').replace(',', '')
                try:
                    list_price_usd = float(list_price_str)
                except:
                    list_price_usd = None
    
    # Extract unit price if available
    unit_price = product.get('unit_price', '')
    
    # Extract recent sales info
    recent_sales = product.get('recent_sales', '')
    
    return {
        'source': 'amazon',
        'platform_id': product.get('asin', ''),
        'title': product.get('title', ''),
        'brand': extract_brand_from_title_or_api(product.get('title', ''), product.get('asin', '')),  # Extract from title or API
        'model_number': '',  # Not available in Amazon search results
        'price_usd': price_usd,
        'list_price_usd': list_price_usd,
        'rating': product.get('rating', ''),
        'reviews_count': product.get('ratings_total', ''),
        'position': product.get('position', ''),
        'category': category,
        'image_url': product.get('image', ''),
        'product_url': f"https://www.amazon.com/dp/{product.get('asin', '')}" if product.get('asin') else product.get('link', ''),
        'availability': product.get('availability', {}).get('raw', ''),
        'recent_sales': recent_sales,
        'is_bestseller': '',  # Amazon doesn't have explicit bestseller badge in search results
        'unit_price': unit_price,
        'collection': '',  # Not available in Amazon data
        'delivery_free': '',  # Not tracking this for Amazon
        'pickup_available': '',  # Not applicable for Amazon
        'features': '',  # Not available in search results
        'description': '',  # Not available in search results
        'extract_date': extract_date
    }

def extract_home_depot_product(product: Dict[str, Any], category: str, extract_date: str) -> Dict[str, Any]:
    """Extract relevant fields from Home Depot product data"""
    
    # Handle badges to check for bestseller
    badges = product.get('badges', [])
    is_bestseller = 'bestseller' in badges if badges else False
    
    # Handle delivery info
    delivery_info = product.get('delivery', {})
    delivery_free = delivery_info.get('free', False) if delivery_info else False
    
    # Handle pickup info
    pickup_info = product.get('pickup', {})
    pickup_available = pickup_info.get('quantity', 0) > 0 if pickup_info else False
    
    # Handle collection URL
    collection = product.get('collection', '')
    if collection and collection != 'https://www.homedepot.com':
        collection = collection
    else:
        collection = ''
    
    return {
        'source': 'home_depot',
        'platform_id': product.get('product_id', ''),
        'title': product.get('title', ''),
        'brand': product.get('brand', ''),
        'model_number': product.get('model_number', ''),
        'price_usd': product.get('price', ''),
        'list_price_usd': '',  # Home Depot doesn't typically show list price in search results
        'rating': product.get('rating', ''),
        'reviews_count': product.get('reviews', ''),
        'position': product.get('position', ''),
        'category': category,
        'image_url': get_primary_image_url(product.get('thumbnails', [])),
        'product_url': product.get('link', ''),
        'availability': '',  # Not explicitly available in search results
        'recent_sales': '',  # Not available for Home Depot
        'is_bestseller': is_bestseller,
        'unit_price': product.get('unit', ''),
        'collection': collection,
        'delivery_free': delivery_free,
        'pickup_available': pickup_available,
        'features': '',  # Not available in search results
        'description': '',  # Not available in search results
        'extract_date': extract_date
    }

def get_amazon_product_details(asin: str) -> Dict[str, Any]:
    """Get detailed product information from Amazon API and save to file"""
    # Define the amazon directory path
    amazon_dir = os.path.join(DATA_DIR, "amazon")
    os.makedirs(amazon_dir, exist_ok=True)
    
    # Check if file already exists
    filename = f"amazon_product_{asin}.json"
    filepath = os.path.join(amazon_dir, filename)
    
    if os.path.exists(filepath):
        print(f"Loading existing product details for ASIN: {asin}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading existing file for {asin}: {str(e)}")
    
    # File doesn't exist, fetch from API
    print(f"Fetching product details for ASIN: {asin}")
    try:
        product_details = get_amazon_product(asin)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(product_details, f, indent=2, ensure_ascii=False)
        
        print(f"Saved product details to: {filename}")
        
        # Add small delay to be respectful to the API
        time.sleep(0.5)
        
        return product_details
        
    except Exception as e:
        print(f"Error fetching product details for {asin}: {str(e)}")
        return {}

def extract_brand_from_title_or_api(title: str, asin: str = '') -> str:
    """Extract brand from Amazon product title or fetch from API if unknown"""
    if not title:
        return ''
    
    # Common brand names in switch/dimmer market
    brands = ['Amazon', 'ELEGRP', 'Leviton', 'Kasa', 'BESTTEN', 'Lutron', 'Cloudy Bay',
    'TP-Link', 'MOES', 'TREATLIFE', 'Reliance Controls', 'Commercial Electric',
    'Hunter', 'Defiant', 'Intermatic', 'myTouchSmart', 'Hampton Bay', 'Carlon',
    'LINJO', 'Home Decorators Collection', 'Cantex', 'GE', 'Legrand', 'ABB',
    'Square D', 'HDX', 'Adamax', 'MINKA-AIRE', 'Philips Hue', 'TP-LINK', 'Halex',
    'Siemens', 'Eaton']
    
    title_upper = title.upper()
    for brand in brands:
        if brand.upper() in title_upper:
            return brand
    
    # Brand not found in known list, try to get it from Amazon API
    if asin:
        print(f"Unknown brand for '{title[:50]}...', fetching details from Amazon API")
        product_details = get_amazon_product_details(asin)
        
        if product_details and 'brand' in product_details:
            api_brand = product_details.get('brand', '').strip()
            if api_brand:
                print(f"Found brand from API: {api_brand}")
                return api_brand
    
    return ''

def get_primary_image_url(thumbnails: List[List[str]]) -> str:
    """Extract primary image URL from Home Depot thumbnails"""
    if not thumbnails or not thumbnails[0]:
        return ''
    
    # Get the highest resolution image (usually the last one in the list)
    primary_images = thumbnails[0]
    return primary_images[-1] if primary_images else ''

def process_amazon_files(scraped_dir: str) -> List[Dict[str, Any]]:
    """Process all Amazon JSON files"""
    amazon_dir = os.path.join(scraped_dir, 'amazon')
    products = []
    seen_asins = set()  # For deduplication
    
    print(f"Looking for files in: {amazon_dir}")
    
    # Find all Amazon JSON files
    json_files = glob.glob(os.path.join(amazon_dir, '*.json'))
    print(f"Found {len(json_files)} Amazon JSON files")
    
    for file_path in json_files:
        print(f"Processing Amazon file: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract category from filename
            filename = os.path.basename(file_path)
            if 'dimmer_switches' in filename:
                category = 'Dimmer Switches'
            elif 'light_switches' in filename:
                category = 'Light Switches'
            else:
                category = 'Unknown'
            
            # Extract date from filename or use current date
            extract_date = datetime.now().strftime('%Y-%m-%d')
            if len(filename.split('_')) > 0:
                date_part = filename.split('_')[-1].replace('.json', '')
                if len(date_part) == 8 and date_part.isdigit():
                    extract_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            
            # Process search results
            search_results = data.get('search_results', [])
            for product in search_results:
                asin = product.get('asin', '')
                
                # Skip duplicates
                if asin and asin in seen_asins:
                    continue
                
                if asin:
                    seen_asins.add(asin)
                
                extracted_product = extract_amazon_product(product, category, extract_date)
                products.append(extracted_product)
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    print(f"Processed {len(products)} unique Amazon products")
    return products

def process_home_depot_files(scraped_dir: str) -> List[Dict[str, Any]]:
    """Process all Home Depot JSON files"""
    home_depot_dir = os.path.join(scraped_dir, 'home_depot')
    products = []
    seen_products = set()  # For deduplication (product_id + model_number)
    
    print(f"Looking for files in: {home_depot_dir}")
    
    # Find all Home Depot JSON files
    json_files = glob.glob(os.path.join(home_depot_dir, '*.json'))
    print(f"Found {len(json_files)} Home Depot JSON files")
    
    for file_path in json_files:
        print(f"Processing Home Depot file: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract category from filename
            filename = os.path.basename(file_path)
            if 'dimmer_switch' in filename:
                category = 'Dimmer Switches'
            elif 'light_switch' in filename:
                category = 'Light Switches'
            else:
                category = 'Unknown'
            
            # Extract date from filename or use current date
            extract_date = datetime.now().strftime('%Y-%m-%d')
            if len(filename.split('_')) > 0:
                date_part = filename.split('_')[-1].replace('.json', '')
                if len(date_part) == 8 and date_part.isdigit():
                    extract_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            
            # Process products
            products_data = data.get('products', [])
            for product in products_data:
                product_id = product.get('product_id', '')
                model_number = product.get('model_number', '')
                
                # Create unique identifier for deduplication
                unique_id = f"{product_id}_{model_number}"
                
                # Skip duplicates
                if unique_id in seen_products:
                    continue
                
                seen_products.add(unique_id)
                
                extracted_product = extract_home_depot_product(product, category, extract_date)
                products.append(extracted_product)
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    print(f"Processed {len(products)} unique Home Depot products")
    return products

def main():
    """Main function to process all scraped data and create unified CSV"""
    print("Starting data processing...")
    print("=" * 50)
    
    # Debug information
    print(f"ROOT_DIR: {ROOT_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Define paths
    scraped_dir = os.path.join(DATA_DIR, "scraped")
    processed_dir = os.path.join(DATA_DIR, "processed")
    
    print(f"Scraped directory: {scraped_dir}")
    print(f"Processed directory: {processed_dir}")
    print(f"Scraped dir exists: {os.path.exists(scraped_dir)}")
    
    # Create processed directory if it doesn't exist
    os.makedirs(processed_dir, exist_ok=True)
    
    # Process data from both sources
    print("\n🔄 PROCESSING AMAZON DATA")
    print("-" * 30)
    amazon_products = process_amazon_files(scraped_dir)
    
    print("\n🔄 PROCESSING HOME DEPOT DATA")
    print("-" * 30)
    home_depot_products = process_home_depot_files(scraped_dir)
    
    # Combine all products
    all_products = amazon_products + home_depot_products
    
    # Create DataFrame
    df = pd.DataFrame(all_products)
    
    # Define column order based on approved header
    columns = [
        'source', 'platform_id', 'title', 'brand', 'model_number', 'price_usd', 'list_price_usd',
        'rating', 'reviews_count', 'position', 'category', 'image_url', 'product_url',
        'availability', 'recent_sales', 'is_bestseller', 'unit_price', 'collection',
        'delivery_free', 'pickup_available', 'features', 'description', 'extract_date'
    ]
    
    # Handle empty DataFrame case
    if df.empty:
        # Create empty DataFrame with proper columns
        df = pd.DataFrame(columns=columns)
        print("Warning: No products found to process. Creating empty CSV with headers.")
    else:
        # Reorder columns
        df = df[columns]
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(processed_dir, f'combined_products_{timestamp}.csv')
    
    # Save to CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(df['brand'].unique())
    # Summary
    print("\n" + "=" * 50)
    print("📊 PROCESSING SUMMARY")
    print("=" * 50)
    print(f"Amazon products: {len(amazon_products)}")
    print(f"Home Depot products: {len(home_depot_products)}")
    print(f"Total products: {len(all_products)}")
    print(f"Output file: {output_file}")
    print("=" * 50)
    
    # Display sample of data
    if not df.empty:
        print(f"\n📋 SAMPLE DATA (first 5 rows):")
        print("-" * 50)
        print(df.head().to_string(index=False, max_cols=8))
    else:
        print(f"\n📋 No data to display - empty dataset")

if __name__ == "__main__":
    main() 