import pandas as pd
import logging
import re
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data" / "processed"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def process_products_data(input_file, output_file):
    """
    Process the products data by:
    1. Removing duplicates based on platform_id
    2. Removing "Store" from brand values
    3. Changing category to "Dimmer Switches" if title contains "dimmer"
    4. Logging all deleted/modified rows
    """
    
    logging.info(f"Starting processing of {input_file}")
    
    # Read the CSV file
    try:
        df = pd.read_csv(input_file)
        logging.info(f"Successfully loaded {len(df)} rows from {input_file}")
        print(f"Original data shape: {df.shape}")
    except Exception as e:
        logging.error(f"Error reading file {input_file}: {e}")
        return
    
    original_count = len(df)
    
    # 1. Remove duplicates based on platform_id
    logging.info("Processing duplicates based on platform_id...")
    
    # Find duplicates
    duplicate_mask = df.duplicated(subset=['platform_id'], keep='first')
    duplicate_rows = df[duplicate_mask]
    
    if len(duplicate_rows) > 0:
        logging.info(f"Found {len(duplicate_rows)} duplicate rows based on platform_id")
        for idx, row in duplicate_rows.iterrows():
            logging.info(f"DELETED DUPLICATE - platform_id: {row['platform_id']}, title: {row['title'][:50]}...")
    else:
        logging.info("No duplicates found based on platform_id")
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['platform_id'], keep='first')
    dedup_count = len(df)
    
    logging.info(f"After deduplication: {dedup_count} rows (removed {original_count - dedup_count} duplicates)")
    
    # 2. Remove "Store" from brand values (case insensitive)
    logging.info("Processing brand values to remove 'Store' (case insensitive)...")
    
    brand_modifications = 0
    for idx in df.index:
        original_brand = df.at[idx, 'brand']
        if pd.notna(original_brand) and 'store' in str(original_brand).lower():
            new_brand = str(original_brand)
            # Remove various forms of "Store" case insensitively
            new_brand = re.sub(r'\s+store\s*', ' ', new_brand, flags=re.IGNORECASE).strip()
            new_brand = re.sub(r'\s+', ' ', new_brand)  # Clean up multiple spaces
            df.at[idx, 'brand'] = new_brand
            brand_modifications += 1
            logging.info(f"MODIFIED BRAND - Row {idx}: '{original_brand}' -> '{new_brand}'")
    
    logging.info(f"Modified {brand_modifications} brand values to remove 'Store'")
    
    # 3. Change category to "Dimmer Switches" if title contains "dimmer"
    logging.info("Processing categories for dimmer products...")
    
    category_modifications = 0
    for idx in df.index:
        title = str(df.at[idx, 'title']).lower()
        current_category = df.at[idx, 'category']
        
        if 'dimmer' in title and current_category != 'Dimmer Switches':
            df.at[idx, 'category'] = 'Dimmer Switches'
            category_modifications += 1
            logging.info(f"MODIFIED CATEGORY - Row {idx}: '{current_category}' -> 'Dimmer Switches' (title contains 'dimmer') for title: {title}")
    
    logging.info(f"Modified {category_modifications} categories to 'Dimmer Switches'")
    
    # 4. Create cleaned_title column with brand words removed (case insensitive)
    logging.info("Creating cleaned_title column with brand words removed...")
            
    cleaned_title_count = 0
    df['cleaned_title'] = df['title'].copy()
    
    for idx in df.index:
        original_title = str(df.at[idx, 'title'])
        brand = df.at[idx, 'brand']
        cleaned_title = original_title
        matches = []  # Initialize matches list
        
        if pd.notna(brand) and brand.strip():
            # Create a pattern to match the whole brand name with flexible word boundaries
            brand_words = [word.strip() for word in str(brand).split() if word.strip()]
            if brand_words:
                # Escape each word and join with flexible word boundaries (spaces, punctuation)
                escaped_words = [re.escape(word) for word in brand_words]
                pattern = r'\b' + r'\s+'.join(escaped_words) + r'\b'
                
                # Find all matches before replacing to log them
                matches = re.findall(pattern, cleaned_title, flags=re.IGNORECASE)
                
                # Replace all brand word matches in one operation
                cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE)
                
                # Clean up extra spaces and commas
                cleaned_title = re.sub(r'\s*,\s*', ', ', cleaned_title)  # Fix comma spacing
                cleaned_title = re.sub(r'\s+', ' ', cleaned_title)  # Fix multiple spaces
                cleaned_title = cleaned_title.strip()
                cleaned_title = cleaned_title.strip(',')  # Remove leading/trailing commas
        
        df.at[idx, 'cleaned_title'] = cleaned_title
        cleaned_title_count += 1
        
        if original_title != cleaned_title:
            removed_words_str = f" (removed: {matches})" if matches else ""
            logging.info(f"CLEANED TITLE - Row {idx}: '{original_title[:50]}...' -> '{cleaned_title[:50]}...'{removed_words_str}")
    
    logging.info(f"Created cleaned_title for {cleaned_title_count} rows")
    
    # Save processed data
    try:
        df.to_csv(output_file, index=False)
        logging.info(f"Successfully saved processed data to {output_file}")
        print(f"Processed data saved to: {output_file}")
    except Exception as e:
        logging.error(f"Error saving file {output_file}: {e}")
        return
    
    # Summary
    final_count = len(df)
    logging.info("="*50)
    logging.info("PROCESSING SUMMARY")
    logging.info("="*50)
    logging.info(f"Original rows: {original_count}")
    logging.info(f"Rows after deduplication: {dedup_count}")
    logging.info(f"Duplicates removed: {original_count - dedup_count}")
    logging.info(f"Brand modifications: {brand_modifications}")
    logging.info(f"Category modifications: {category_modifications}")
    logging.info(f"Cleaned titles created: {cleaned_title_count}")
    logging.info(f"Final rows: {final_count}")
    logging.info(f"Output file: {output_file}")
    logging.info("="*50)
    
    print("\nProcessing Summary:")
    print(f"Original rows: {original_count}")
    print(f"Duplicates removed: {original_count - dedup_count}")
    print(f"Brand modifications: {brand_modifications}")
    print(f"Category modifications: {category_modifications}")
    print(f"Cleaned titles created: {cleaned_title_count}")
    print(f"Final rows: {final_count}")

if __name__ == "__main__":
    input_file = DATA_DIR / "combined_products_20250606.csv"
    output_file = DATA_DIR / "combined_products_cleaned.csv"
    
    process_products_data(input_file, output_file) 