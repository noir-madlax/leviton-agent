#!/usr/bin/env python3
"""
Review Analysis Script

Process Amazon product reviews using the hierarchical review extraction prompt 
to extract comprehensive customer insights about physical aspects, performance, and use cases.

This script uses shared utilities for:
- Configuration management
- Rate limiting
- LLM management
- JSON processing
- Prompt management
- Caching
"""

import json
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path
from datetime import datetime
import asyncio
import re

# Import utility modules
from utils.config import get_process_review_config
from utils.llm_utils import initialize_global_llm, safe_llm_call
from utils.prompt_utils import load_prompt
from utils.json_utils import extract_json_from_response
from utils.cache_utils import LLMCache
from utils.rate_limiter import RateLimiter

# === CONFIGURATION ===
config = get_process_review_config()

# Data paths
REVIEW_DATA_DIR = config.get_data_path("scraped", "amazon", "review")
PRODUCTS_CSV_PATH = config.get_data_path("result", "product_segment", "combined_products_cleaned", "combined_products_with_final_categories.csv")

# Initialize LLM with configuration
llm_manager = initialize_global_llm(
    model_name=config.MODEL_NAME,
    temperature=config.MODEL_TEMPERATURE,
    max_tokens=config.MODEL_MAX_TOKENS
)

# Initialize cache and rate limiter
cache_manager = LLMCache(config.CACHE_DIR)
rate_limiter = RateLimiter(
    max_requests_per_minute=config.MAX_REQUESTS_PER_MINUTE,
    max_input_tokens_per_minute=config.MAX_INPUT_TOKENS_PER_MINUTE,
    max_output_tokens_per_minute=config.MAX_OUTPUT_TOKENS_PER_MINUTE,
    max_concurrent_requests=config.MAX_CONCURRENT_REQUESTS,
    model_max_tokens=config.MODEL_MAX_TOKENS
)

# Load extraction prompt
EXTRACT_PROMPT_TEMPLATE = load_prompt("extract_review_hierarchy_v0.txt", config.PROMPT_DIR)

# Load shared retry prompt template
SHARED_RETRY_PROMPT_TEMPLATE = load_prompt("shared_retry_prompt_v0.txt", config.PROMPT_DIR / "product_segment")

# === UNIFIED RETRY SYSTEM ===
def create_retry_context(error_categories: Dict[str, List[str]], content_sections: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """
    Create standardized retry context for all LLM validation failures.
    
    Args:
        error_categories: Categorized errors {"format_errors": [...], "validation_errors": [...], "completeness_errors": [...]}
        content_sections: Dynamic content sections {"section_key": {"title": "...", "content": "..."}}
    
    Returns:
        Standardized retry context dictionary
        
    Data Contract:
        - error_categories must have keys: format_errors, validation_errors, completeness_errors
        - content_sections values must have 'title' and 'content' keys
        - All counts must be non-negative integers
    """
    all_errors = error_categories["format_errors"] + error_categories["validation_errors"] + error_categories["completeness_errors"]
    
    return {
        "issues_summary": " | ".join(all_errors[:3]) + (f" (and {len(all_errors)-3} more)" if len(all_errors) > 3 else ""),
        "error_categories": error_categories,
        "content_sections": content_sections
    }

def build_retry_prompt(original_prompt: str, retry_context: Dict[str, Any], **additional_kwargs) -> str:
    """
    Build standardized retry prompt by appending shared retry template to original prompt.
    
    Args:
        original_prompt: Original prompt to append retry instructions to
        retry_context: Standardized retry context from create_retry_context()
        **additional_kwargs: Additional template variables
    
    Returns:
        Original prompt + formatted retry instructions
        
    Data Contract:
        - original_prompt can be any valid prompt string
        - retry_context must be from create_retry_context()
        - Returns original_prompt + shared retry template
        - All retry template placeholders are satisfied by context + additional_kwargs
    """
    # Build error analysis by category with count information
    error_analysis_sections = []
    
    # Add categorized errors
    for category, errors in retry_context['error_categories'].items():
        if errors:
            category_title = category.replace('_', ' ').title()
            error_analysis_sections.append(f"**{category_title}:**")
            for error in errors:
                error_analysis_sections.append(f"- {error}")
            error_analysis_sections.append("")
    
    error_details = "\n".join(error_analysis_sections).strip()
    
    # Build content sections dynamically
    content_sections_text = []
    for section_key, section_data in retry_context['content_sections'].items():
        content_sections_text.append(f"**{section_data['title']}:**\n{section_data['content']}\n")
    
    # Combine template variables
    template_vars = {
        "error_details": error_details,
        "content_sections": "\n".join(content_sections_text),
        **additional_kwargs
    }
    
    # Format the shared retry template
    retry_instructions = SHARED_RETRY_PROMPT_TEMPLATE.format(**template_vars)
    
    # Append retry instructions to original prompt
    return original_prompt + retry_instructions

# === VALIDATION RULES ===
def validate_id_format(id_str: str, id_type: str) -> bool:
    """
    Validate ID format according to prompt rules
    
    Args:
        id_str: ID string to validate
        id_type: Either 'PID' (A, B, C...) or 'perf_id' (a, b, c...)
    
    Returns:
        True if valid format
    """
    if id_type == 'PID':
        # PID: A, B, C... Z, AA, AB, AC...
        pattern = r'^[A-Z]+$'
    elif id_type == 'perf_id':
        # perf_id: a, b, c... z, aa, ab, ac...
        pattern = r'^[a-z]+$'
    else:
        return False
    
    return bool(re.match(pattern, id_str))

def validate_sentiment(sent: str) -> bool:
    """Validate sentiment is either '+' or '-'"""
    return sent in ['+', '-']

def validate_review_ids(ids: Any, expected_review_ids: Set[int]) -> Tuple[bool, str]:
    """
    Validate review IDs are valid integers and exist in expected set
    
    Args:
        ids: List of review IDs
        expected_review_ids: Set of valid review IDs
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(ids, list):
        return False, "Review IDs must be a list"
    
    invalid_ids = []
    missing_ids = []
    
    for id_val in ids:
        try:
            id_int = int(id_val)
            if id_int not in expected_review_ids:
                missing_ids.append(id_int)
        except (ValueError, TypeError):
            invalid_ids.append(id_val)
    
    errors = []
    if invalid_ids:
        errors.append(f"Invalid ID format: {invalid_ids}")
    if missing_ids:
        errors.append(f"IDs not in input: {missing_ids}")
    
    return len(errors) == 0, "; ".join(errors)

def validate_sentiment_consistency(reason_codes: str, current_sentiment: str, aspect_sentiments: Dict[str, Set[str]], context: str) -> List[str]:
    """
    Validate that referenced reason codes have consistent sentiment with current context
    
    Args:
        reason_codes: Comma/semicolon-separated reason codes (e.g., 'A,b,c')
        current_sentiment: Current sentiment context ('+' or '-')
        aspect_sentiments: Dict mapping aspect codes to their available sentiments
        context: Context string for error reporting
    
    Returns:
        List of error messages
    """
    errors = []
    
    if reason_codes == "?":
        return errors  # Unknown reasons are ok
    
    # Split by comma
    reason_parts = [r.strip() for r in reason_codes.split(',') if r.strip()]
    
    for reason_code in reason_parts:
        if reason_code in aspect_sentiments:
            available_sentiments = aspect_sentiments[reason_code]
            if current_sentiment not in available_sentiments:
                available_str = ', '.join(sorted(available_sentiments))
                errors.append(f"Sentiment mismatch in {context}: reason '{reason_code}' only has sentiments [{available_str}] but is referenced in '{current_sentiment}' context")
    
    return errors

def validate_hierarchy_structure(result: Dict[str, Any], expected_review_ids: Set[int]) -> Tuple[bool, List[str]]:
    """
    Validate the hierarchical review extraction JSON structure
    
    Args:
        result: Parsed JSON result
        expected_review_ids: Set of valid review IDs from input
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required top-level sections
    required_sections = ['phy', 'perf', 'use']
    for section in required_sections:
        if section not in result:
            errors.append(f"Missing required section: '{section}'")
            continue
        
        if not isinstance(result[section], dict):
            errors.append(f"Section '{section}' must be a JSON object containing aspect categories, got {type(result[section]).__name__}")
            continue
    
    # First pass: collect all aspects and their available sentiments for cross-reference validation
    aspect_sentiments = {}  # {aspect_code: {'+', '-'}} - tracks which sentiments each aspect has
    
    # Collect from 'phy' section
    if 'phy' in result and isinstance(result['phy'], dict):
        for physical, details in result['phy'].items():
            if isinstance(details, dict):
                for pid_detail, sentiments in details.items():
                    if '@' in pid_detail and isinstance(sentiments, dict):
                        pid = pid_detail.split('@', 1)[0]
                        aspect_sentiments[pid] = set(sentiments.keys())
    
    # Collect from 'perf' section
    if 'perf' in result and isinstance(result['perf'], dict):
        for perf, details in result['perf'].items():
            if isinstance(details, dict):
                for perf_id_detail, sentiments in details.items():
                    if '@' in perf_id_detail and isinstance(sentiments, dict):
                        perf_id = perf_id_detail.split('@', 1)[0]
                        aspect_sentiments[perf_id] = set(sentiments.keys())
    
    # Validate 'phy' section
    if 'phy' in result and isinstance(result['phy'], dict):
        for physical, details in result['phy'].items():
            if not isinstance(details, dict):
                errors.append(f"Physical aspect '{physical}' must be a JSON object with PID@DETAIL keys, got {type(details).__name__}")
                continue
            
            for pid_detail, sentiments in details.items():
                # Validate PID@DETAIL format
                if '@' not in pid_detail:
                    errors.append(f"Invalid format '{pid_detail}' - must be PID@DETAIL")
                    continue
                
                pid, detail = pid_detail.split('@', 1)
                if not validate_id_format(pid, 'PID'):
                    errors.append(f"Invalid PID format '{pid}' - must be A, B, C... Z, AA, AB...")
                
                if not isinstance(sentiments, dict):
                    errors.append(f"Sentiments for '{pid_detail}' must be a JSON object with '+'/'-' keys mapping to review ID arrays, got {type(sentiments).__name__}")
                    continue
                
                for sent, ids in sentiments.items():
                    if not validate_sentiment(sent):
                        errors.append(f"Invalid sentiment '{sent}' - must be '+' or '-'")
                    
                    is_valid, id_error = validate_review_ids(ids, expected_review_ids)
                    if not is_valid:
                        errors.append(f"Invalid review IDs in {pid_detail}[{sent}]: {id_error}")
    
    # Validate 'perf' section
    if 'perf' in result and isinstance(result['perf'], dict):
        for perf, details in result['perf'].items():
            if not isinstance(details, dict):
                errors.append(f"Performance aspect '{perf}' must be a JSON object with perf_id@DETAIL keys, got {type(details).__name__}")
                continue
            
            for perf_id_detail, sentiments in details.items():
                # Validate perf_id@DETAIL format
                if '@' not in perf_id_detail:
                    errors.append(f"Invalid format '{perf_id_detail}' - must be perf_id@DETAIL")
                    continue
                
                perf_id, detail = perf_id_detail.split('@', 1)
                if not validate_id_format(perf_id, 'perf_id'):
                    errors.append(f"Invalid perf_id format '{perf_id}' - must be a, b, c... z, aa, ab...")
                
                if not isinstance(sentiments, dict):
                    errors.append(f"Sentiments for '{perf_id_detail}' must be a JSON object with '+'/'-' keys mapping to reason objects, got {type(sentiments).__name__}")
                    continue
                
                for sent, reasons in sentiments.items():
                    if not validate_sentiment(sent):
                        errors.append(f"Invalid sentiment '{sent}' - must be '+' or '-'")
                    
                    if not isinstance(reasons, dict):
                        errors.append(f"Reasons for '{perf_id_detail}[{sent}]' must be a JSON object with reason keys (PID/perf_id/'?') mapping to review ID arrays, got {type(reasons).__name__}")
                        continue
                    
                    for reason, ids in reasons.items():
                        # Validate reason format (PID, perf_id, "?", or comma-separated like "F,p")
                        if reason != "?":
                            # Split by comma and validate each part
                            reason_parts = [r.strip() for r in reason.split(',') if r.strip()]
                            invalid_parts = []
                            for part in reason_parts:
                                if not (validate_id_format(part, 'PID') or validate_id_format(part, 'perf_id')):
                                    invalid_parts.append(part)
                            
                            if invalid_parts:
                                errors.append(f"Invalid reason format '{reason}' - invalid parts: {invalid_parts}. Each part must be PID, perf_id, or '?'")
                        
                        # Validate sentiment consistency
                        sentiment_errors = validate_sentiment_consistency(
                            reason, sent, aspect_sentiments, 
                            f"{perf_id_detail}[{sent}][{reason}]"
                        )
                        errors.extend(sentiment_errors)
                        
                        is_valid, id_error = validate_review_ids(ids, expected_review_ids)
                        if not is_valid:
                            errors.append(f"Invalid review IDs in {perf_id_detail}[{sent}][{reason}]: {id_error}")
    
    # Validate 'use' section
    if 'use' in result and isinstance(result['use'], dict):
        for use, sentiments in result['use'].items():
            if not isinstance(sentiments, dict):
                errors.append(f"Use case '{use}' must be a JSON object with '+'/'-' keys mapping to reason objects, got {type(sentiments).__name__}")
                continue
            
            for sent, reasons in sentiments.items():
                if not validate_sentiment(sent):
                    errors.append(f"Invalid sentiment '{sent}' - must be '+' or '-'")
                
                if not isinstance(reasons, dict):
                    errors.append(f"Reasons for '{use}[{sent}]' must be a JSON object with reason keys (PID/perf_id/'?') mapping to review ID arrays, got {type(reasons).__name__}")
                    continue
                
                for reason, ids in reasons.items():
                    # Validate reason format (PID, perf_id, "?", or comma-separated like "F,p")
                    if reason != "?":
                        # Split by comma and validate each part
                        reason_parts = [r.strip() for r in reason.split(',') if r.strip()]
                        invalid_parts = []
                        for part in reason_parts:
                            if not (validate_id_format(part, 'PID') or validate_id_format(part, 'perf_id')):
                                invalid_parts.append(part)
                        
                        if invalid_parts:
                            errors.append(f"Invalid reason format '{reason}' - invalid parts: {invalid_parts}. Each part must be PID, perf_id, or '?'")
                    
                    # Validate sentiment consistency
                    sentiment_errors = validate_sentiment_consistency(
                        reason, sent, aspect_sentiments, 
                        f"{use}[{sent}][{reason}]"
                    )
                    errors.extend(sentiment_errors)
                    
                    is_valid, id_error = validate_review_ids(ids, expected_review_ids)
                    if not is_valid:
                        errors.append(f"Invalid review IDs in {use}[{sent}][{reason}]: {id_error}")
    
    return len(errors) == 0, errors

def parse_and_validate_response(response_text: str, expected_review_ids: Set[int], 
                               product_title: str, asin: str) -> Tuple[bool, Any]:
    """
    Parse LLM response and validate completeness for review hierarchy extraction.
    
    Args:
        response_text: Raw LLM response text
        expected_review_ids: Set of expected review IDs
        product_title: Product title for context
        asin: Product ASIN for context
    
    Returns:
        Tuple of (is_valid: bool, result: Dict or structured_retry_context)
        
    Data Contract:
        - On success: returns (True, parsed_hierarchy_dict)
        - On failure: returns (False, standardized_retry_context)
        - parsed_hierarchy_dict follows extract_review_hierarchy_v0.txt schema
        - retry_context follows create_retry_context() format
    """
    
    # Try to extract JSON from response
    json_text = ""
    result = {}
    json_error = ""
    
    try:
        json_text = extract_json_from_response(response_text)
        result = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        json_error = f"Could not extract valid JSON: {e}"
    
    # Validate JSON structure if parsed successfully
    validation_errors = []
    if json_error:
        structure_errors = [json_error]
    else:
        structure_errors = []
        if not isinstance(result, dict):
            structure_errors.append("Response must be a JSON object")
        else:
            # Perform detailed validation
            is_valid, validation_errors = validate_hierarchy_structure(result, expected_review_ids)
            if not is_valid:
                pass  # validation_errors already populated
    
    # Categorize errors logically
    error_categories = {
        "format_errors": structure_errors,
        "validation_errors": validation_errors,
        "completeness_errors": []
    }
    
    # Count total errors
    all_errors = error_categories["format_errors"] + error_categories["validation_errors"] + error_categories["completeness_errors"]
    
    # If no errors, return success
    if not all_errors:
        return True, result
    
    # Build content sections based on available data
    content_sections = {}
    
    # Previous attempt section
    if json_error:
        content_sections["previous_attempt"] = {
            "title": "YOUR PREVIOUS RESPONSE",
            "content": response_text[:500] + "..." if len(response_text) > 500 else response_text
        }
    elif json_text and json_text != "(No valid JSON found)":
        content_sections["previous_attempt"] = {
            "title": "YOUR PREVIOUS JSON ATTEMPT", 
            "content": json_text[:500] + "..." if len(json_text) > 500 else json_text
        }
    
    # Context section
    content_sections["product_context"] = {
        "title": "PRODUCT CONTEXT",
        "content": f"ASIN: {asin}\nProduct: {product_title}\nExpected Review IDs: {sorted(list(expected_review_ids))}"
    }
    
    # Create standardized retry context
    retry_context = create_retry_context(
        error_categories=error_categories,
        content_sections=content_sections
    )
    
    return False, retry_context

# === DATA LOADING ===
def load_products_mapping() -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Load product ASIN to category mapping from the final categories CSV
    
    Returns:
        Tuple of (asin_to_category, asin_to_title) mappings
    """
    # Try to load from final categories CSV first (with product_segment)
    
    try:
        products_df = pd.read_csv(PRODUCTS_CSV_PATH)
        if 'product_segment' in products_df.columns:
            asin_to_category = dict(zip(products_df['platform_id'], products_df['product_segment']))
            asin_to_title = dict(zip(products_df['platform_id'], products_df['title']))
            print(f"Loaded {len(asin_to_category)} product category mappings from final categories CSV")
            return asin_to_category, asin_to_title
    except FileNotFoundError:
        print(f"Final categories CSV not found at {PRODUCTS_CSV_PATH}")


def get_review_files() -> List[Path]:
    """Get all review JSON files from the review directory"""
    if not REVIEW_DATA_DIR.exists():
        raise FileNotFoundError(f"Review directory not found: {REVIEW_DATA_DIR}")
    
    review_files = [f for f in REVIEW_DATA_DIR.glob("*.json") 
                   if not f.name.startswith("scrape_summary")]
    
    print(f"Found {len(review_files)} review files")
    return review_files

def load_review_file(file_path: Path) -> Tuple[str, str, List[Dict[str, Any]]]:
    """Load reviews from a single JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        asin = file_path.stem.split('_')[0]
        reviews = data.get('reviews_data', {}).get('reviews', [])
        if not reviews:
            return asin, "", []
        
        product_title = reviews[0].get('productTitle', '')
        
        valid_reviews = []
        for i, review in enumerate(reviews):
            review_text = review.get('text', '').strip()
            if review_text and len(review_text) > 10:
                valid_reviews.append({
                    'id': i,
                    'text': review_text,
                    'rating': review.get('rating', ''),
                    'title': review.get('title', ''),
                    'date': review.get('date', ''),
                    'verified': review.get('verified', False)
                })
        
        print(f"Loaded {len(valid_reviews)} valid reviews for {asin}")
        return asin, product_title, valid_reviews
        
    except Exception as e:
        print(f"Error loading review file {file_path}: {e}")
        return "", "", []

# === REVIEW PROCESSING ===

def format_reviews_for_prompt(reviews: List[Dict[str, Any]]) -> str:
    """Format reviews for the extraction prompt input, following extract_review_hierarchy.py style"""
    formatted_reviews = []
    for idx, review in enumerate(reviews):
        title = review.get('title', '')
        if title and not title.endswith(('.', '?', '!', ',', ';', ':')):
            title = title + '. '
        elif title:
            title = title + ' '
        
        body = review.get('text', '')
        review_text = f"{title}{body}"
        
        # Escape special characters that could cause JSON issues
        escaped_text = review_text.replace('\\', '\\\\').replace('\n', ' ').replace('\r', ' ')
        formatted_reviews.append(f"{idx}#{escaped_text}")
    
    return "\n".join(formatted_reviews)

def create_cache_context(asin: str, product_category: str, review_count: int) -> Dict[str, Any]:
    """Create context for caching"""
    return {
        "asin": asin,
        "product_category": product_category,
        "review_count": review_count,
        "script_type": "review_hierarchy_extraction",
        "model": config.MODEL_NAME
    }

async def process_reviews_with_retry(asin: str, product_category: str, reviews: List[Dict[str, Any]], 
                                   max_retries: int = 3) -> Dict[str, Any]:
    """
    Process all reviews for a single product with validation and retry logic using rate limiter
    
    Args:
        asin: Product ASIN
        product_category: Product category (from product_segment column)
        reviews: List of review dictionaries
        max_retries: Maximum number of retry attempts
    
    Returns:
        Extracted hierarchy or empty dict on failure
    """
    if not reviews:
        return {}
    
    print(f"\nProcessing {len(reviews)} reviews for {asin} (category: {product_category})...")
    
    # Create cache context
    cache_context = create_cache_context(asin, product_category, len(reviews))
    
    # Build prompt using product category instead of title
    formatted_reviews = format_reviews_for_prompt(reviews)
    base_prompt = EXTRACT_PROMPT_TEMPLATE.replace('{{PRODUCT}}', product_category)
    full_prompt = base_prompt.replace('{{INPUT}}', formatted_reviews)
    
    # Check cache first
    cached_response = cache_manager.load_llm_response(full_prompt, cache_context)
    if cached_response:
        print(f"✓ Using cached response for {asin}")
        try:
            # Create expected IDs as 0, 1, 2, ... based on review count
            expected_review_ids = set(range(len(reviews)))
            is_valid, result = parse_and_validate_response(cached_response, expected_review_ids, product_category, asin)
            
            if is_valid:
                print(f"✓ Cached result validated for {asin}")
                return result
            else:
                print(f"⚠️ Cached result invalid for {asin}, re-processing")
        except Exception as e:
            print(f"⚠️ Error parsing cached result for {asin}: {e}, re-processing")
    
    # Process with unified retry logic and rate limiting
    expected_review_ids = set(range(len(reviews)))  # 0, 1, 2, ... based on review positions
    prompt = full_prompt
    
    for attempt in range(max_retries):
        try:
            print(f"   Attempt {attempt + 1}/{max_retries} for {asin}")
            
            # Estimate tokens and acquire rate limit permission
            estimated_input_tokens = rate_limiter.estimate_tokens(prompt)
            await rate_limiter.acquire(estimated_input_tokens)
            
            try:
                response_text = await safe_llm_call(prompt)
                
                # Release rate limiter
                actual_output_tokens = rate_limiter.estimate_tokens(response_text)
                rate_limiter.release(estimated_input_tokens, actual_output_tokens)
                
            except Exception as e:
                # Always release on error
                rate_limiter.release()
                raise e
            
            # Save to cache regardless of validation outcome
            cache_manager.save_llm_response(full_prompt, response_text, cache_context)
            
            # Use unified validation and retry logic
            is_valid, result = parse_and_validate_response(response_text, expected_review_ids, product_category, asin)
            
            if is_valid:
                print(f"✓ Analysis complete for {asin}")
                return result
            else:
                print(f"✗ Validation failed for {asin} (attempt {attempt + 1}): {result['issues_summary']}")
                
                if attempt < max_retries - 1:
                    # Use unified retry prompt builder
                    retry_prompt = build_retry_prompt(
                        original_prompt=base_prompt.replace('{{INPUT}}', formatted_reviews),
                        retry_context=result,
                        product_category=product_category,
                        asin=asin
                    )
                    
                    prompt = retry_prompt  # Replace prompt with retry version
                    print(f"   Built comprehensive retry prompt with {len(result['error_categories']['format_errors'] + result['error_categories']['validation_errors'] + result['error_categories']['completeness_errors'])} detailed errors")
                
        except Exception as e:
            print(f"✗ Error processing {asin} (attempt {attempt + 1}): {e}")
    
    print(f"❌ Failed to process {asin} after {max_retries} attempts")
    return {}

async def process_single_asin(review_file: Path, asin_to_category: Dict[str, str], 
                             asin_to_title: Dict[str, str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Process a single ASIN's reviews"""
    try:
        asin, product_title_from_file, reviews = load_review_file(review_file)
        
        if not reviews:
            print(f"Skipping {asin}: no valid reviews")
            return asin, None
        
        # Use product category from mapping, fallback to file title or default
        product_category = asin_to_category.get(asin, "Products")
        product_title = asin_to_title.get(asin, product_title_from_file)
        if not product_title:
            product_title = f"Product {asin}"
        
        result = await process_reviews_with_retry(asin, product_category, reviews, max_retries=config.DEFAULT_MAX_RETRIES)
        
        if result:
            analysis_data = {
                'product_title': product_title,
                'product_category': product_category,
                'total_reviews': len(reviews),
                'review_analysis': result,
                'processed_date': datetime.now().isoformat()
            }
            
            individual_result_path = config.get_file_path(f"{asin}_review_analysis.json")
            with open(individual_result_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved review analysis for {asin} (category: {product_category})")
            return asin, analysis_data
        else:
            return asin, None
            
    except Exception as e:
        print(f"❌ Error processing {review_file}: {e}")
        return "", None

# === MAIN PROCESSING ===
async def process_all_reviews():
    """Process all review files and generate hierarchical analyses (concurrent processing)"""
    print("Starting hierarchical review processing...")
    
    asin_to_category, asin_to_title = load_products_mapping()
    review_files = get_review_files()
    
    if not review_files:
        print("No review files found!")
        return
    
    print(f"Processing {len(review_files)} review files concurrently...")
    
    # Process all ASINs concurrently
    tasks = [
        process_single_asin(review_file, asin_to_category, asin_to_title)
        for review_file in review_files
    ]
    
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect successful results
    results = {}
    processed_count = 0
    
    for result in results_list:
        if isinstance(result, Exception):
            print(f"⚠️ ASIN processing failed with exception: {result}")
            continue
        
        asin, analysis_data = result
        if analysis_data:
            results[asin] = analysis_data
            processed_count += 1
    
    if results:
        consolidated_path = config.get_file_path("consolidated_review_results.json")
        consolidated_data = {
            'processing_summary': {
                'total_products_processed': processed_count,
                'total_products_attempted': len(review_files),
                'processing_date': datetime.now().isoformat(),
                'model_used': config.MODEL_NAME,
                'configuration': config.to_dict()
            },
            'results': results
        }
        
        with open(consolidated_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Processing complete!")
        print(f"✓ Processed {processed_count} products concurrently")
        print(f"✓ Results saved to {config.OUTPUT_ROOT_DIR}")
    else:
        print("\n❌ No results generated")

# === MAIN EXECUTION ===
async def main():
    """Main execution function"""
    try:
        await process_all_reviews()
    except Exception as e:
        print(f"Error during processing: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 