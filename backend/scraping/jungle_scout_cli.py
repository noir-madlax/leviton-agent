#!/usr/bin/env python3
"""
Jungle Scout Sales History CLI

This script provides a command-line interface to fetch sales history data
from Jungle Scout API for Amazon products.

Usage:
    python jungle_scout_cli.py <ASIN> [options]
    python jungle_scout_cli.py --batch <ASIN_FILE> [options]

Examples:
    # Get sales history for a single ASIN
    python jungle_scout_cli.py B08N5WRWNW
    
    # Get sales history with custom date range
    python jungle_scout_cli.py B08N5WRWNW --marketplace us --start-date 2024-01-01 --end-date 2024-01-31
    
    # Get sales history for multiple ASINs from file
    python jungle_scout_cli.py --batch asins.txt --marketplace us
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add the common directory to the path to import the API client
sys.path.append(str(Path(__file__).parent / "common"))

from jungle_scout_api import get_sales_history, get_sales_history_batch, JungleScoutAPIError

def load_asins_from_file(file_path: str) -> List[str]:
    """Load ASINs from a text file (one ASIN per line)"""
    try:
        with open(file_path, 'r') as f:
            asins = [line.strip() for line in f if line.strip()]
        return asins
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        sys.exit(1)

def save_results_to_file(results: Dict[str, Any], output_file: str):
    """Save results to a JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving results to file: {e}")

def print_results(results: Dict[str, Any], asin: str = None):
    """Print results in a formatted way"""
    if asin:
        # Single ASIN result
        print(f"\n=== Sales History for ASIN: {asin} ===")
        print(json.dumps(results, indent=2))
    else:
        # Batch results
        print(f"\n=== Batch Results ({len(results)} ASINs) ===")
        for asin, data in results.items():
            print(f"\n--- ASIN: {asin} ---")
            if "error" in data:
                print(f"Error: {data['error']}")
            else:
                print(json.dumps(data, indent=2))

def main():
    parser = argparse.ArgumentParser(
        description="Fetch sales history from Jungle Scout API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # ASIN input options
    asin_group = parser.add_mutually_exclusive_group(required=True)
    asin_group.add_argument(
        "asin",
        nargs="?",
        help="Amazon product ASIN"
    )
    asin_group.add_argument(
        "--batch",
        metavar="FILE",
        help="File containing ASINs (one per line)"
    )
    
    # API parameters
    parser.add_argument(
        "--marketplace",
        default="us",
        choices=["us", "uk", "de", "in", "ca", "fr", "it", "es", "mx", "jp"],
        help="Marketplace country code (default: us)"
    )
    parser.add_argument(
        "--start-date",
        metavar="YYYY-MM-DD",
        help="Start date for sales data (default: 30 days ago)"
    )
    parser.add_argument(
        "--end-date",
        metavar="YYYY-MM-DD",
        help="End date for sales data (default: yesterday)"
    )
    
    # Output options
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output (useful with --output)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.batch:
            # Batch processing
            asins = load_asins_from_file(args.batch)
            print(f"Processing {len(asins)} ASINs from file: {args.batch}")
            
            results = get_sales_history_batch(
                asins=asins,
                marketplace=args.marketplace,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            if not args.quiet:
                print_results(results)
            
            if args.output:
                save_results_to_file(results, args.output)
                
        else:
            # Single ASIN processing
            results = get_sales_history(
                asin=args.asin,
                marketplace=args.marketplace,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            if not args.quiet:
                print_results(results, args.asin)
            
            if args.output:
                save_results_to_file(results, args.output)
    
    except JungleScoutAPIError as e:
        print(f"Jungle Scout API Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 