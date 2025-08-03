#!/usr/bin/env python3
"""
Script to test the Unwrangle Amazon Product Data API by reading ASINs from an Excel file,
sampling 50 of them, and saving the API responses to JSON files.
"""

import os
import sys
import json
import random
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import time

# Add the backend directory to the path to import the amazon_api module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.amazon_api import get_amazon_product_details_unwrangle

# Constants
EXCEL_FILE_PATH = "/Users/maoc/MIT Dropbox/Chengfeng Mao/JMP/UX168 data and code/data/raw/电线电缆_495310_asin_review明细.xlsx"
OUTPUT_DIR = "unwrangle_product_responses"
SAMPLE_SIZE = 50
DELAY_BETWEEN_REQUESTS = 1  # seconds to avoid rate limiting

def create_output_directory() -> Path:
    """Create the output directory if it doesn't exist."""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    print(f"Output directory created/verified: {output_path.absolute()}")
    return output_path

def read_asins_from_excel(file_path: str) -> List[str]:
    """
    Read ASINs from the Excel file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        List of ASIN strings
    """
    try:
        print(f"Reading ASINs from: {file_path}")
        
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Print column names to help identify the ASIN column
        print(f"Available columns: {list(df.columns)}")
        
        # Try to find the ASIN column (common variations)
        asin_column = None
        possible_asin_columns = ['asin', 'ASIN', 'Asin', 'product_asin', 'Product_ASIN']
        
        for col in possible_asin_columns:
            if col in df.columns:
                asin_column = col
                break
        
        if asin_column is None:
            # If no exact match, look for columns containing 'asin'
            for col in df.columns:
                if 'asin' in col.lower():
                    asin_column = col
                    break
        
        if asin_column is None:
            raise ValueError(f"Could not find ASIN column. Available columns: {list(df.columns)}")
        
        print(f"Using ASIN column: {asin_column}")
        
        # Extract ASINs and remove duplicates
        asins = df[asin_column].dropna().astype(str).unique().tolist()
        
        # Clean ASINs (remove any whitespace, ensure they're valid format)
        cleaned_asins = []
        for asin in asins:
            asin = asin.strip()
            if len(asin) == 10 and asin.isalnum():  # Basic ASIN validation
                cleaned_asins.append(asin)
            else:
                print(f"Skipping invalid ASIN format: {asin}")
        
        print(f"Found {len(cleaned_asins)} valid ASINs")
        return cleaned_asins
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        raise

def sample_asins(asins: List[str], sample_size: int) -> List[str]:
    """
    Sample a subset of ASINs.
    
    Args:
        asins: List of all ASINs
        sample_size: Number of ASINs to sample
        
    Returns:
        List of sampled ASINs
    """
    if len(asins) <= sample_size:
        print(f"Total ASINs ({len(asins)}) is less than or equal to sample size ({sample_size}). Using all ASINs.")
        return asins
    
    # Set random seed for reproducibility
    random.seed(42)
    sampled_asins = random.sample(asins, sample_size)
    print(f"Sampled {len(sampled_asins)} ASINs from {len(asins)} total ASINs")
    return sampled_asins

def call_product_api(asin: str, output_dir: Path) -> Dict[str, Any]:
    """
    Call the Unwrangle product detail API for a single ASIN.
    
    Args:
        asin: Product ASIN
        output_dir: Directory to save the response
        
    Returns:
        API response data
    """
    try:
        print(f"Fetching product details for ASIN: {asin}")
        
        # Call the API
        response = get_amazon_product_details_unwrangle(asin=asin)
        
        if response is None:
            print(f"Failed to get response for ASIN: {asin}")
            return {"asin": asin, "error": "API call failed"}
        
        # Save response to JSON file
        output_file = output_dir / f"{asin}_product_details.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
        
        print(f"Saved response for ASIN {asin} to: {output_file}")
        
        # Add delay to avoid rate limiting
        time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return response
        
    except Exception as e:
        print(f"Error processing ASIN {asin}: {e}")
        return {"asin": asin, "error": str(e)}

def main():
    """Main function to orchestrate the process."""
    try:
        print("Starting Unwrangle Product API test script...")
        
        # Create output directory
        output_dir = create_output_directory()
        
        # Read ASINs from Excel file
        all_asins = read_asins_from_excel(EXCEL_FILE_PATH)
        
        if not all_asins:
            print("No valid ASINs found in the Excel file.")
            return
        
        # Sample ASINs
        sampled_asins = sample_asins(all_asins, SAMPLE_SIZE)
        
        # Process each sampled ASIN
        results = []
        for i, asin in enumerate(sampled_asins, 1):
            print(f"\nProcessing ASIN {i}/{len(sampled_asins)}: {asin}")
            result = call_product_api(asin, output_dir)
            results.append(result)
        
        # Save summary results
        summary_file = output_dir / "api_test_summary.json"
        summary = {
            "total_asins_processed": len(results),
            "successful_requests": len([r for r in results if "error" not in r]),
            "failed_requests": len([r for r in results if "error" in r]),
            "processed_asins": sampled_asins,
            "results": results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\nTest completed!")
        print(f"Total ASINs processed: {len(results)}")
        print(f"Successful requests: {summary['successful_requests']}")
        print(f"Failed requests: {summary['failed_requests']}")
        print(f"Summary saved to: {summary_file}")
        print(f"Individual responses saved to: {output_dir}")
        
    except Exception as e:
        print(f"Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main() 