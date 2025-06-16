#!/usr/bin/env python3
"""
Review Aspect Categorization Script

Process consolidated review hierarchy results and categorize phy, perf, and use aspects
into meaningful subcategories for analysis.

This script:
1. Loads consolidated review results from process_reviews.py
2. Extracts and formats phy, perf, and use aspects
3. Applies categorization prompts to group similar aspects
4. Saves categorized results for further analysis
"""

import json
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime
import asyncio

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
PRODUCTS_CSV_PATH = config.get_data_path("result", "product_segment", "combined_products_cleaned", "combined_products_with_final_categories.csv")

# Categorization batch size - number of aspects to process in each LLM call
CATEGORIZATION_BATCH_SIZE = 150

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

# Load categorization prompt template
CATEGORIZE_PROMPT_TEMPLATE = load_prompt("categorize_review_aspects_prompt_v0.txt", config.PROMPT_DIR)

# Load consolidation prompt template
CONSOLIDATE_PROMPT_TEMPLATE = load_prompt("consolidate_aspect_categories_prompt_v0.txt", config.PROMPT_DIR)

# Load final assignment prompt template
FINAL_ASSIGN_PROMPT_TEMPLATE = load_prompt("final_assign_aspects_prompt_v0.txt", config.PROMPT_DIR)

# Load shared retry prompt template  
SHARED_RETRY_PROMPT_TEMPLATE = load_prompt("shared_retry_prompt_v0.txt", config.PROMPT_DIR / "product_segment")

# === DATA LOADING ===
def load_product_categories_from_csv() -> set:
    """
    Load product categories from the CSV file's category column
    
    Returns:
        Set of unique product categories
    """
    try:
        products_df = pd.read_csv(PRODUCTS_CSV_PATH)
        if 'category' in products_df.columns:
            categories = set(products_df['category'].dropna().unique())
            print(f"Loaded {len(categories)} product categories from CSV category column")
            return categories
        else:
            print(f"Warning: 'category' column not found in {PRODUCTS_CSV_PATH}")
            print(f"Available columns: {list(products_df.columns)}")
            return set()
    except FileNotFoundError:
        print(f"Products CSV not found at {PRODUCTS_CSV_PATH}")
        return set()
    except Exception as e:
        print(f"Error loading product categories from CSV: {e}")
        return set()

# === DATA PROCESSING ===
def simple_stem(word: str) -> str:
    """Simple stemming function to normalize words for deduplication"""
    word = word.lower().strip()
    # Remove common suffixes
    suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ness', 'ment', 'able', 'ible', 'ful', 'less']
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]
    return word

def extract_phy_aspects(phy_data: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """
    Extract physical aspects in simplified format
    
    Args:
        phy_data: Physical aspects section from review hierarchy
    
    Returns:
        List of (aspect_id, category, detail) tuples
    """
    aspects = []
    
    for physical_category, details in phy_data.items():
        for pid_detail, sentiments in details.items():
            # Parse PID@DETAIL format
            pid, detail = pid_detail.split('@', 1) if '@' in pid_detail else (pid_detail, "")
            
            # Simple format: just "category: detail"
            formatted_desc = f"{physical_category}: {detail}" if detail else physical_category
            
            # Use the original PID as aspect_id
            aspects.append((pid, physical_category, formatted_desc))
    
    return aspects

def extract_perf_aspects(perf_data: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """
    Extract performance aspects in simplified format
    
    Args:
        perf_data: Performance aspects section from review hierarchy
    
    Returns:
        List of (aspect_id, category, detail) tuples
    """
    aspects = []
    
    for perf_category, details in perf_data.items():
        for perf_id_detail, sentiments in details.items():
            # Parse perf_id@DETAIL format
            perf_id, detail = perf_id_detail.split('@', 1) if '@' in perf_id_detail else (perf_id_detail, "")
            
            # Simple format: just "category: detail"
            formatted_desc = f"{perf_category}: {detail}" if detail else perf_category
            
            # Use the original perf_id as aspect_id
            aspects.append((perf_id, perf_category, formatted_desc))
    
    return aspects

def extract_use_aspects(use_data: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """
    Extract use case aspects in simplified format
    
    Args:
        use_data: Use cases section from review hierarchy
    
    Returns:
        List of (aspect_id, category, detail) tuples
    """
    aspects = []
    
    for use_case, sentiments in use_data.items():
        # Simple format: just the use case name
        formatted_desc = use_case
        
        # Use the use_case itself as the aspect_id for use cases
        aspects.append((use_case, "use case", formatted_desc))
    
    return aspects

def format_aspects_for_prompt(aspects: List[Tuple[str, str]]) -> str:
    """Format aspects for the categorization prompt"""
    formatted_lines = []
    for aspect_id, description in aspects:
        formatted_lines.append(f"[{aspect_id}] {description}")
    
    return "\n".join(formatted_lines)

def calculate_optimal_aspect_batch_sizes(total_aspects: int, target_batch_size: int) -> List[int]:
    """Calculate optimal batch sizes for aspects to avoid small remainders"""
    if total_aspects <= target_batch_size:
        return [total_aspects]
    
    # Calculate number of batches needed
    num_batches = max(1, round(total_aspects / target_batch_size))
    
    # Calculate base size and remainder
    base_size = total_aspects // num_batches
    remainder = total_aspects % num_batches
    
    # Distribute remainder across batches
    batch_sizes = [base_size] * num_batches
    for i in range(remainder):
        batch_sizes[i] += 1
    
    return batch_sizes

def make_aspect_batches(aspects: List[Tuple[str, str]], target_batch_size: int) -> List[List[Tuple[str, str]]]:
    """Create evenly-sized batches from aspects list"""
    if not aspects:
        return []
    
    # Calculate optimal batch sizes
    optimal_sizes = calculate_optimal_aspect_batch_sizes(len(aspects), target_batch_size)
    print(f"Creating {len(optimal_sizes)} aspect batches with sizes: {optimal_sizes}")
    
    batches = []
    start_idx = 0
    
    for target_size in optimal_sizes:
        end_idx = start_idx + target_size
        if start_idx < len(aspects):
            batch = aspects[start_idx:end_idx]
            batches.append(batch)
            start_idx = end_idx
        else:
            break
    
    actual_sizes = [len(batch) for batch in batches]
    print(f"Created {len(batches)} aspect batches with actual sizes: {actual_sizes}")
    return batches

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

# === VALIDATION FUNCTIONS ===
def parse_and_validate_categorization_response(response_text: str, expected_ids: set, 
                                             aspect_type: str) -> Tuple[bool, Any]:
    """
    Parse LLM response and validate for aspect categorization with unified retry system.
    
    Args:
        response_text: Raw LLM response text
        expected_ids: Set of expected aspect IDs
        aspect_type: Type of aspects being categorized
    
    Returns:
        Tuple of (is_valid: bool, result: Dict or structured_retry_context)
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
    
    # Validate JSON structure
    structure_errors = []
    if json_error:
        structure_errors = [json_error]
    else:
        if not isinstance(result, dict):
            structure_errors.append("Response must be a JSON object")
    
    # Collect all IDs and validation errors
    found_ids = set()
    duplicate_ids = []
    validation_errors = []
    
    if isinstance(result, dict):
        for category, category_data in result.items():
            if not isinstance(category_data, dict):
                validation_errors.append(f"Category '{category}' must be an object with 'definition' and 'ids' fields")
                continue
                
            if "definition" not in category_data:
                validation_errors.append(f"Category '{category}' missing required 'definition' field")
                
            if "ids" not in category_data:
                validation_errors.append(f"Category '{category}' missing required 'ids' field")
                continue
                
            ids = category_data["ids"]
            if not isinstance(ids, list):
                validation_errors.append(f"Category '{category}' 'ids' field must be a list")
                continue
            
            for id_val in ids:
                if id_val in found_ids:
                    duplicate_ids.append(id_val)
                else:
                    found_ids.add(id_val)
    
    # Check for missing/extra IDs
    missing_ids = expected_ids - found_ids
    extra_ids = found_ids - expected_ids
    
    # Categorize errors logically
    error_categories = {
        "format_errors": structure_errors,
        "validation_errors": validation_errors,
        "completeness_errors": []
    }
    
    if duplicate_ids:
        error_categories["completeness_errors"].append(f"Duplicate IDs found: {sorted(duplicate_ids)}")
    if missing_ids:
        error_categories["completeness_errors"].append(f"Missing IDs: {sorted(missing_ids)}")
    if extra_ids:
        error_categories["completeness_errors"].append(f"Extra IDs not in input: {sorted(extra_ids)}")
    
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
    
    # Missing IDs section
    if missing_ids:
        content_sections["missing_ids"] = {
            "title": "MISSING IDs TO CATEGORIZE",
            "content": str(sorted(missing_ids))
        }
    
    # Extra IDs section
    if extra_ids:
        content_sections["extra_ids"] = {
            "title": "EXTRA IDs TO REMOVE",
            "content": str(sorted(extra_ids))
        }
    
    # Create standardized retry context
    retry_context = create_retry_context(
        error_categories=error_categories,
        content_sections=content_sections
    )
    
    return False, retry_context

def parse_and_validate_consolidate_response(response_text: str, expected_a_ids: set, 
                                          expected_b_ids: set, aspect_type: str) -> Tuple[bool, Any]:
    """
    Parse and validate consolidate response for aspect category merging.
    
    Args:
        response_text: Raw LLM response text
        expected_a_ids: Set of expected category IDs from taxonomy A (A_0, A_1, ...)
        expected_b_ids: Set of expected category IDs from taxonomy B (B_0, B_1, ...)
        aspect_type: Type of aspects being consolidated
    
    Returns:
        Tuple of (is_valid: bool, result: Dict or structured_retry_context)
    """
    try:
        # Extract JSON from response
        json_text = extract_json_from_response(response_text)
        consolidated_structure = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        error_categories = {
            "format_errors": [f"Could not extract valid JSON: {e}"],
            "validation_errors": [],
            "completeness_errors": []
        }
        content_sections = {
            "previous_response": {
                "title": "YOUR PREVIOUS RESPONSE",
                "content": response_text[:500] + "..." if len(response_text) > 500 else response_text
            }
        }
        retry_context = create_retry_context(
            error_categories=error_categories,
            content_sections=content_sections
        )
        return False, retry_context
    
    if not isinstance(consolidated_structure, dict):
        error_categories = {
            "format_errors": ["Response must be a JSON object"],
            "validation_errors": [],
            "completeness_errors": []
        }
        content_sections = {
            "previous_json": {
                "title": "YOUR PREVIOUS JSON ATTEMPT",
                "content": json_text
            }
        }
        retry_context = create_retry_context(
            error_categories=error_categories,
            content_sections=content_sections
        )
        return False, retry_context
    
    # Collect all IDs from the consolidated structure
    found_ids = set()
    found_a_ids = set()
    found_b_ids = set()
    validation_errors = []
    duplicate_ids = []
    
    for category, category_data in consolidated_structure.items():
        if not isinstance(category_data, dict):
            validation_errors.append(f"Category '{category}' must be an object with 'definition' and 'ids' fields")
            continue
            
        if "definition" not in category_data:
            validation_errors.append(f"Category '{category}' missing required 'definition' field")
            
        if "ids" not in category_data:
            validation_errors.append(f"Category '{category}' missing required 'ids' field")
            continue
            
        ids = category_data["ids"]
        if not isinstance(ids, list):
            validation_errors.append(f"Category '{category}' 'ids' field must be a list")
            continue
        
        for cat_id in ids:
            if not isinstance(cat_id, str):
                validation_errors.append(f"Invalid ID '{cat_id}' in category '{category}' - must be a string")
                continue
                
            if cat_id in found_ids:
                duplicate_ids.append(cat_id)
            else:
                found_ids.add(cat_id)
                
            if cat_id.startswith("A_"):
                found_a_ids.add(cat_id)
            elif cat_id.startswith("B_"):
                found_b_ids.add(cat_id)
            else:
                validation_errors.append(f"Invalid category ID format '{cat_id}' - must start with 'A_' or 'B_'")
    
    # Check completeness
    all_expected = expected_a_ids | expected_b_ids
    missing_ids = all_expected - found_ids
    extra_ids = found_ids - all_expected
    
    # Categorize errors
    error_categories = {
        "format_errors": [],
        "validation_errors": validation_errors,
        "completeness_errors": []
    }
    
    if duplicate_ids:
        error_categories["completeness_errors"].append(f"Duplicate category IDs found: {sorted(duplicate_ids)}")
    if missing_ids:
        error_categories["completeness_errors"].append(f"Missing category IDs: {sorted(missing_ids)}")
    if extra_ids:
        error_categories["completeness_errors"].append(f"Extra category IDs (not expected): {sorted(extra_ids)}")
    
    all_errors = error_categories["format_errors"] + error_categories["validation_errors"] + error_categories["completeness_errors"]
    
    if not all_errors:
        return True, consolidated_structure
    
    # Build content sections for retry
    content_sections = {}
    
    if json_text:
        content_sections["previous_json"] = {
            "title": "YOUR PREVIOUS JSON ATTEMPT",
            "content": json_text
        }
    
    content_sections["expected_ids"] = {
        "title": "EXPECTED CATEGORY IDs",
        "content": f"Taxonomy A: {sorted(expected_a_ids)}\nTaxonomy B: {sorted(expected_b_ids)}"
    }
    
    if missing_ids:
        content_sections["missing_ids"] = {
            "title": "MISSING CATEGORY IDs TO INCLUDE",
            "content": str(sorted(missing_ids))
        }
    
    if extra_ids:
        content_sections["extra_ids"] = {
            "title": "EXTRA CATEGORY IDs TO REMOVE",
            "content": str(sorted(extra_ids))
        }
    
    retry_context = create_retry_context(
        error_categories=error_categories,
        content_sections=content_sections
    )
    
    return False, retry_context

# === CATEGORIZATION ===
async def categorize_aspects_batch(aspects: List[Tuple[str, str]], aspect_type: str, 
                                 aspect_context: str, input_description: str,
                                 product_categories: set, max_retries: int = 3) -> Dict[str, Any]:
    """
    Categorize a batch of aspects using the LLM with category and product context
    
    Args:
        aspects: List of (aspect_id, description) tuples
        aspect_type: Type of aspects (physical, performance, use case)
        aspect_context: Context description for the aspects
        input_description: Description of input format
        product_categories: Set of product categories found
        max_retries: Maximum retry attempts
    
    Returns:
        Categorization result or empty dict on failure
    """
    if not aspects:
        return {}
    
    print(f"Categorizing batch of {len(aspects)} {aspect_type} aspects...")
    
    # Format aspects for prompt
    formatted_aspects = format_aspects_for_prompt(aspects)
    
    # Add category context to the prompt
    category_context = ""
    if product_categories:
        category_context += f"\n\n**PRODUCT CATEGORIES IN DATASET:** {', '.join(sorted(product_categories))}"
        category_context += f"\nConsider how {aspect_type} aspects relate to customer needs across these {len(product_categories)} product categories."
    
    # Build prompt with template substitution
    prompt = CATEGORIZE_PROMPT_TEMPLATE.format(
        aspect_type=aspect_type,
        aspect_context=aspect_context,
        input_description=input_description
    )
    
    full_prompt = prompt + category_context + "\n\n**INPUT:**\n" + formatted_aspects
    
    # Create cache context
    cache_context = {
        "aspect_type": aspect_type,
        "aspect_count": len(aspects),
        "script_type": "review_aspect_categorization",
        "model": config.MODEL_NAME
    }
    
    # Check cache first
    cached_response = cache_manager.load_llm_response(full_prompt, cache_context)
    if cached_response:
        print(f"✓ Using cached response for {aspect_type} categorization")
        try:
            json_text = extract_json_from_response(cached_response)
            result = json.loads(json_text)
            print(f"✓ Cached result loaded for {aspect_type}")
            return result
        except Exception as e:
            print(f"⚠️ Error parsing cached result for {aspect_type}: {e}, re-processing")
    
    # Process with retry logic and rate limiting
    base_prompt = prompt + category_context + "\n\n**INPUT:**\n" + formatted_aspects
    current_prompt = full_prompt
    
    for attempt in range(max_retries):
        try:
            print(f"   Attempt {attempt + 1}/{max_retries} for {aspect_type} categorization")
            
            # Estimate tokens and acquire rate limit permission
            estimated_input_tokens = rate_limiter.estimate_tokens(current_prompt)
            await rate_limiter.acquire(estimated_input_tokens)
            
            try:
                response_text = await safe_llm_call(current_prompt)
                
                # Release rate limiter
                actual_output_tokens = rate_limiter.estimate_tokens(response_text)
                rate_limiter.release(estimated_input_tokens, actual_output_tokens)
                
            except Exception as e:
                # Always release on error
                rate_limiter.release()
                raise e
            
            # Save to cache
            cache_manager.save_llm_response(full_prompt, response_text, cache_context)
            
            # Parse JSON response (only JSON validation, no other validation)
            try:
                json_text = extract_json_from_response(response_text)
                result = json.loads(json_text)
                print(f"✓ {aspect_type} categorization complete")
                return result
            except (json.JSONDecodeError, ValueError) as e:
                print(f"✗ JSON parsing failed for {aspect_type} (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    # Create retry context for JSON error only
                    error_categories = {
                        "format_errors": [f"Could not extract valid JSON: {e}"],
                        "validation_errors": [],
                        "completeness_errors": []
                    }
                    content_sections = {
                        "previous_response": {
                            "title": "YOUR PREVIOUS RESPONSE",
                            "content": response_text
                        }
                    }
                    retry_context = create_retry_context(
                        error_categories=error_categories,
                        content_sections=content_sections
                    )
                    
                    # Build retry prompt
                    retry_prompt = build_retry_prompt(
                        original_prompt=base_prompt,
                        retry_context=retry_context,
                        aspect_type=aspect_type
                    )
                    
                    current_prompt = retry_prompt
                    print(f"   Built JSON retry prompt for {aspect_type}")
                
        except Exception as e:
            print(f"✗ Error processing {aspect_type} categorization (attempt {attempt + 1}): {e}")
    
    print(f"❌ Failed to categorize {aspect_type} aspects after {max_retries} attempts")
    return {}

async def categorize_aspects(aspects: List[Tuple[str, str]], aspect_type: str, 
                           aspect_context: str, input_description: str,
                           product_categories: set, max_retries: int = 3) -> Dict[str, Any]:
    """
    Categorize aspects by splitting into batches and combining results
    
    Args:
        aspects: List of (aspect_id, description) tuples
        aspect_type: Type of aspects (physical, performance, use case)
        aspect_context: Context description for the aspects
        input_description: Description of input format
        product_categories: Set of product categories found
        max_retries: Maximum retry attempts
    
    Returns:
        Combined categorization result from all batches
    """
    if not aspects:
        return {}
    
    print(f"Categorizing {len(aspects)} {aspect_type} aspects in batches...")
    
    # Create optimal batches using batch creation utility
    batches = make_aspect_batches(aspects, CATEGORIZATION_BATCH_SIZE)
    
    # Process all batches concurrently
    batch_tasks = [
        categorize_aspects_batch(
            batch, aspect_type, aspect_context, 
            input_description, product_categories, max_retries
        )
        for batch in batches
    ]
    
    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
    
    # Combine results from all batches
    combined_result = {}
    successful_batches = 0
    
    for i, result in enumerate(batch_results):
        if isinstance(result, Exception):
            print(f"⚠️ Batch {i+1} failed: {result}")
            continue
        
        if result:
            # Merge batch result into combined result
            for category_name, category_data in result.items():
                if category_name not in combined_result:
                    combined_result[category_name] = {
                        'definition': category_data.get('definition', ''),
                        'ids': []
                    }
                
                # Add IDs from this batch
                combined_result[category_name]['ids'].extend(category_data.get('ids', []))
            
            successful_batches += 1
    
    print(f"✓ Successfully processed {successful_batches}/{len(batches)} batches for {aspect_type}")
    return combined_result

# === CONSOLIDATION FUNCTIONS ===
def create_taxonomy_with_ids(taxonomy: Dict[str, Dict[str, Any]], prefix: str) -> Dict[str, Dict[str, Any]]:
    """Create taxonomy with prefixed category IDs for consolidation"""
    taxonomy_with_ids = {}
    categories = list(taxonomy.keys())
    
    for i, category in enumerate(categories):
        category_id = f"{prefix}_{i}"
        category_info = taxonomy[category]
        taxonomy_with_ids[category] = {
            "definition": category_info.get("definition", f"Aspects from {category} category"),
            "ids": [category_id]
        }
    
    return taxonomy_with_ids

async def consolidate_taxonomies(taxonomy_a: Dict[str, Dict[str, Any]], taxonomy_b: Dict[str, Dict[str, Any]], 
                          aspect_type: str, aspect_context: str, product_categories: set, 
                          max_tries: int = 3) -> Dict[str, Dict[str, Any]]:
    """
    Consolidate two aspect taxonomies into one coherent structure using AI-guided merging with validation.
    
    Args:
        taxonomy_a: Existing consolidated taxonomy
        taxonomy_b: New batch taxonomy to merge in
        aspect_type: Type of aspects being consolidated
        aspect_context: Context description for the aspects
        product_categories: Set of product categories for context
        max_tries: Maximum retry attempts for consolidation
        
    Returns:
        Consolidated taxonomy structure
    """
    # Create taxonomies with IDs for consolidation
    taxonomy_a_with_ids = create_taxonomy_with_ids(taxonomy_a, "A")
    taxonomy_b_with_ids = create_taxonomy_with_ids(taxonomy_b, "B")
    
    # Add product context
    product_context = ""
    if product_categories:
        product_context += f"\n\n**PRODUCT CATEGORIES IN DATASET:** {', '.join(sorted(product_categories))}"
        product_context += f"\nConsider how {aspect_type} aspects relate to customer needs across these {len(product_categories)} product categories."
    
    base_prompt = CONSOLIDATE_PROMPT_TEMPLATE.format(
        aspect_type=aspect_type,
        aspect_context=aspect_context,
        taxonomy_a=json.dumps(taxonomy_a_with_ids, indent=2),
        taxonomy_b=json.dumps(taxonomy_b_with_ids, indent=2),
        product_context=product_context
    )
    prompt = base_prompt
    
    # Expected IDs for validation
    expected_a_ids = {f"A_{i}" for i in range(len(taxonomy_a))}
    expected_b_ids = {f"B_{i}" for i in range(len(taxonomy_b))}
    
    # Create cache context for consolidation
    cache_context = {
        "taxonomy_a_categories": sorted(list(taxonomy_a.keys())),
        "taxonomy_b_categories": sorted(list(taxonomy_b.keys())),
        "aspect_type": aspect_type,
        "script_type": "aspect_consolidation"
    }
    
    # Check cache first
    cached_response = cache_manager.load_llm_response(prompt, cache_context)
    if cached_response:
        print("✓ Using cached consolidation result")
        try:
            json_text = extract_json_from_response(cached_response)
            result = json.loads(json_text)
            return result
        except Exception as e:
            print(f"⚠️ Error parsing cached consolidation result: {e}, re-processing")
    
    print(f"Consolidating {aspect_type} taxonomies - A: {sorted(expected_a_ids)}, B: {sorted(expected_b_ids)}")
    
    for attempt in range(max_tries):
        try:
            print(f"Consolidation attempt {attempt + 1}/{max_tries}")
            
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
            
            # Save to cache
            cache_manager.save_llm_response(prompt, response_text, cache_context)
            
            # Validate consolidation response
            is_valid, result = parse_and_validate_consolidate_response(
                response_text, expected_a_ids, expected_b_ids, aspect_type
            )
            
            if is_valid:
                consolidated_structure = result
                print(f"✓ {aspect_type} taxonomies consolidated successfully into {len(consolidated_structure)} categories")
                return consolidated_structure
            else:
                print(f"✗ Consolidation validation failed (attempt {attempt + 1}): {result['issues_summary']}")
                
                if attempt < max_tries - 1:
                    # Use unified retry prompt builder
                    retry_prompt = build_retry_prompt(
                        original_prompt=base_prompt,
                        retry_context=result,
                        aspect_type=aspect_type
                    )
                    
                    prompt = retry_prompt
                    print(f"Built consolidation retry prompt")
                
        except Exception as e:
            print(f"✗ Error during {aspect_type} consolidation (attempt {attempt + 1}): {e}")
    
    print(f"❌ Failed to consolidate {aspect_type} taxonomies after {max_tries} attempts")
    return {}

def resolve_consolidated_structure_to_taxonomy(consolidated_structure: Dict[str, Dict[str, Any]], 
                                             taxonomy_a: Dict[str, Dict[str, Any]], 
                                             taxonomy_b: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Convert consolidated category structure back to taxonomy format"""
    # Create ordered lists for deterministic ID→category mapping
    taxonomy_a_categories = list(taxonomy_a.keys())
    taxonomy_b_categories = list(taxonomy_b.keys())
    
    new_taxonomy = {}
    
    for new_category_name, category_data in consolidated_structure.items():
        if "ids" not in category_data:
            continue
            
        category_ids = category_data["ids"]
        combined_ids = []
        
        for category_id in category_ids:
            if category_id.startswith("A_"):
                # Extract index: A_0 → 0, A_1 → 1, etc.
                index = int(category_id.split("_")[1])
                if index < len(taxonomy_a_categories):
                    source_category = taxonomy_a_categories[index]
                    category_info = taxonomy_a[source_category]
                    combined_ids.extend(category_info.get("ids", []))
                    
            elif category_id.startswith("B_"):
                # Extract index: B_0 → 0, B_1 → 1, etc.
                index = int(category_id.split("_")[1])
                if index < len(taxonomy_b_categories):
                    source_category = taxonomy_b_categories[index]
                    category_info = taxonomy_b[source_category]
                    combined_ids.extend(category_info.get("ids", []))
        
        consolidated_definition = category_data.get("definition", "")
        
        # Store the final mapping
        new_taxonomy[new_category_name] = {
            "definition": consolidated_definition,
            "ids": combined_ids
        }
    
    return new_taxonomy

async def consolidate_all_taxonomies(batch_taxonomies: List[Dict[str, Dict[str, Any]]], 
                                   aspect_type: str, aspect_context: str, product_categories: set) -> Dict[str, Dict[str, Any]]:
    """
    Consolidate multiple batch taxonomies into a single coherent taxonomy.
    
    Args:
        batch_taxonomies: List of taxonomies from different batches
        aspect_type: Type of aspects being consolidated
        aspect_context: Context description for the aspects
        product_categories: Set of product categories for context
    
    Returns:
        Single consolidated taxonomy combining all input taxonomies
    """
    print(f"Consolidating {len(batch_taxonomies)} {aspect_type} taxonomies...")
    
    if len(batch_taxonomies) == 0:
        return {}
    
    if len(batch_taxonomies) == 1:
        return batch_taxonomies[0]
    
    # Filter out OUT_OF_SCOPE if present and handle separately
    filtered_taxonomies = []
    out_of_scope_items = []
    
    for taxonomy in batch_taxonomies:
        taxonomy_copy = taxonomy.copy()
        out_of_scope = taxonomy_copy.pop("OUT_OF_SCOPE", None)
        if out_of_scope:
            out_of_scope_items.append(out_of_scope)
        if taxonomy_copy:  # Only add if not empty after removing OUT_OF_SCOPE
            filtered_taxonomies.append(taxonomy_copy)
    
    # If no non-OUT_OF_SCOPE categories, just combine OUT_OF_SCOPE items
    if not filtered_taxonomies:
        if out_of_scope_items:
            combined_out_of_scope = {
                "definition": "Aspects that are unclear, too generic, or don't fit into meaningful categories",
                "ids": []
            }
            for item in out_of_scope_items:
                combined_out_of_scope["ids"].extend(item.get("ids", []))
            return {"OUT_OF_SCOPE": combined_out_of_scope}
        return {}
    
    # Build consolidated taxonomy by merging taxonomies pairwise
    consolidated = filtered_taxonomies[0]
    
    for i in range(1, len(filtered_taxonomies)):
        next_taxonomy = filtered_taxonomies[i]
        print(f"Consolidating {aspect_type} taxonomy {i+1}/{len(filtered_taxonomies)}...")
        
        # Use consolidation function
        consolidated_structure = await consolidate_taxonomies(
            taxonomy_a=consolidated,
            taxonomy_b=next_taxonomy,
            aspect_type=aspect_type,
            aspect_context=aspect_context,
            product_categories=product_categories,
            max_tries=3
        )
        
        # Convert back to taxonomy format
        consolidated = resolve_consolidated_structure_to_taxonomy(
            consolidated_structure, consolidated, next_taxonomy
        )
    
    # Add back combined OUT_OF_SCOPE if exists
    if out_of_scope_items:
        combined_out_of_scope = {
            "definition": "Aspects that are unclear, too generic, or don't fit into meaningful categories",
            "ids": []
        }
        for item in out_of_scope_items:
            combined_out_of_scope["ids"].extend(item.get("ids", []))
        consolidated["OUT_OF_SCOPE"] = combined_out_of_scope
    
    print(f"✓ Final consolidated {aspect_type} taxonomy: {len(consolidated)} categories")
    return consolidated

# === FINAL CATEGORIZATION FUNCTIONS ===
async def final_categorize_aspects_batch(aspects: List[Tuple[str, str]], consolidated_categories: Dict[str, Dict[str, Any]],
                                       aspect_type: str, aspect_context: str, product_categories: set, 
                                       max_retries: int = 3) -> Dict[str, str]:
    """
    Final categorization of a batch of aspects into consolidated categories.
    
    Args:
        aspects: List of (aspect_id, description) tuples to categorize
        consolidated_categories: Consolidated category taxonomy from previous steps
        aspect_type: Type of aspects being categorized
        aspect_context: Context description for the aspects
        product_categories: Set of product categories
        max_retries: Maximum retry attempts
    
    Returns:
        Dict mapping aspect_id to final category name for this batch
    """
    if not aspects or not consolidated_categories:
        return {}
    
    print(f"Final categorization batch of {len(aspects)} {aspect_type} aspects...")
    
    # Build categories section (shared across all batches)
    categories_section = "**AVAILABLE CATEGORIES:**\n"
    category_to_id = {}
    id_to_category = {}
    
    for i, (category_name, category_info) in enumerate(consolidated_categories.items()):
        cat_id = f"C_{i}"
        category_to_id[category_name] = cat_id
        id_to_category[cat_id] = category_name
        definition = category_info.get("definition", "")
        categories_section += f"[{cat_id}] {category_name}: {definition}\n"
    
    # Add product context
    category_context = ""
    if product_categories:
        category_context += f"\n\n**PRODUCT CATEGORIES IN DATASET:** {', '.join(sorted(product_categories))}"
        category_context += f"\nConsider how {aspect_type} aspects relate to customer needs across these {len(product_categories)} product categories."
    
    # Format aspects for this batch
    formatted_aspects = format_aspects_for_prompt(aspects)
    
    # Build final categorization prompt using template
    base_prompt = FINAL_ASSIGN_PROMPT_TEMPLATE.format(
        aspect_type=aspect_type,
        aspect_context=aspect_context,
        categories_section=categories_section,
        product_context=category_context,
        formatted_aspects=formatted_aspects
    )
    
    # Expected IDs for validation
    expected_ids = set(aspect_id for aspect_id, _ in aspects)
    valid_category_ids = set(id_to_category.keys()) | {"OUT_OF_SCOPE"}
    
    # Create cache context
    cache_context = {
        "aspect_type": aspect_type,
        "aspect_count": len(aspects),
        "categories_count": len(consolidated_categories),
        "script_type": "final_aspect_categorization_batch",
        "model": config.MODEL_NAME
    }
    
    # Check cache first
    cached_response = cache_manager.load_llm_response(base_prompt, cache_context)
    if cached_response:
        print(f"✓ Using cached final categorization batch for {aspect_type}")
        try:
            json_text = extract_json_from_response(cached_response)
            result = json.loads(json_text)
            # Convert category IDs back to category names
            final_assignments = {}
            for aspect_id, cat_id in result.items():
                if cat_id == "OUT_OF_SCOPE":
                    final_assignments[aspect_id] = "OUT_OF_SCOPE"
                elif cat_id in id_to_category:
                    final_assignments[aspect_id] = id_to_category[cat_id]
            return final_assignments
        except Exception as e:
            print(f"⚠️ Error parsing cached final categorization batch: {e}, re-processing")
    
    # Process with validation and retry logic
    current_prompt = base_prompt
    
    for attempt in range(max_retries):
        try:
            print(f"   Final categorization attempt {attempt + 1}/{max_retries}")
            
            # Estimate tokens and acquire rate limit permission
            estimated_input_tokens = rate_limiter.estimate_tokens(current_prompt)
            await rate_limiter.acquire(estimated_input_tokens)
            
            try:
                response_text = await safe_llm_call(current_prompt)
                
                # Release rate limiter
                actual_output_tokens = rate_limiter.estimate_tokens(response_text)
                rate_limiter.release(estimated_input_tokens, actual_output_tokens)
                
            except Exception as e:
                # Always release on error
                rate_limiter.release()
                raise e
            
            # Save to cache
            cache_manager.save_llm_response(base_prompt, response_text, cache_context)
            
            # Validate final categorization response
            is_valid, result = parse_and_validate_final_categorization_response(
                response_text, expected_ids, valid_category_ids, aspect_type
            )
            
            if is_valid:
                assignments = result
                # Convert category IDs back to category names
                final_assignments = {}
                for aspect_id, cat_id in assignments.items():
                    if cat_id == "OUT_OF_SCOPE":
                        final_assignments[aspect_id] = "OUT_OF_SCOPE"
                    elif cat_id in id_to_category:
                        final_assignments[aspect_id] = id_to_category[cat_id]
                
                print(f"✓ Final {aspect_type} categorization batch complete")
                return final_assignments
            else:
                print(f"✗ Final categorization validation failed (attempt {attempt + 1}): {result['issues_summary']}")
                
                if attempt < max_retries - 1:
                    # Use unified retry prompt builder
                    retry_prompt = build_retry_prompt(
                        original_prompt=base_prompt,
                        retry_context=result,
                        aspect_type=aspect_type
                    )
                    
                    current_prompt = retry_prompt
                    print(f"Built final categorization retry prompt")
                
        except Exception as e:
            print(f"✗ Error during final {aspect_type} categorization (attempt {attempt + 1}): {e}")
    
    print(f"❌ Failed final {aspect_type} categorization batch after {max_retries} attempts")
    return {}

async def final_categorize_aspects(aspects: List[Tuple[str, str]], consolidated_categories: Dict[str, Dict[str, Any]],
                                 aspect_type: str, aspect_context: str, product_categories: set, 
                                 max_retries: int = 3) -> Dict[str, str]:
    """
    Final categorization step - categorize aspects into consolidated categories without showing original assignments.
    Processes in batches for efficiency.
    
    Args:
        aspects: List of (aspect_id, description) tuples to categorize
        consolidated_categories: Consolidated category taxonomy from previous steps
        aspect_type: Type of aspects being categorized
        aspect_context: Context description for the aspects
        product_categories: Set of product categories
        max_retries: Maximum retry attempts
    
    Returns:
        Dict mapping aspect_id to final category name
    """
    if not aspects or not consolidated_categories:
        return {}
    
    print(f"Final categorization of {len(aspects)} {aspect_type} aspects into {len(consolidated_categories)} categories in batches...")
    
    # Create optimal batches using batch creation utility
    batches = make_aspect_batches(aspects, CATEGORIZATION_BATCH_SIZE)
    
    # Process all batches concurrently
    batch_tasks = [
        final_categorize_aspects_batch(
            batch, consolidated_categories, aspect_type, aspect_context, 
            product_categories, max_retries
        )
        for batch in batches
    ]
    
    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
    
    # Combine results from all batches
    combined_assignments = {}
    successful_batches = 0
    
    for i, result in enumerate(batch_results):
        if isinstance(result, Exception):
            print(f"⚠️ Final categorization batch {i+1} failed: {result}")
            continue
        
        if result:
            # Merge batch result into combined assignments
            combined_assignments.update(result)
            successful_batches += 1
    
    print(f"✓ Successfully processed {successful_batches}/{len(batches)} final categorization batches for {aspect_type}")
    return combined_assignments

def parse_and_validate_final_categorization_response(response_text: str, expected_ids: set, 
                                                   valid_category_ids: set, aspect_type: str) -> Tuple[bool, Any]:
    """
    Parse and validate final categorization response.
    
    Args:
        response_text: Raw LLM response text
        expected_ids: Set of expected aspect IDs
        valid_category_ids: Set of valid category IDs (C_0, C_1, ..., OUT_OF_SCOPE)
        aspect_type: Type of aspects being categorized
    
    Returns:
        Tuple of (is_valid: bool, result: Dict or structured_retry_context)
    """
    try:
        json_text = extract_json_from_response(response_text)
        assignments = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        error_categories = {
            "format_errors": [f"Could not extract valid JSON: {e}"],
            "validation_errors": [],
            "completeness_errors": []
        }
        content_sections = {
            "previous_response": {
                "title": "YOUR PREVIOUS RESPONSE",
                "content": response_text[:500] + "..." if len(response_text) > 500 else response_text
            }
        }
        retry_context = create_retry_context(
            error_categories=error_categories,
            content_sections=content_sections
        )
        return False, retry_context
    
    if not isinstance(assignments, dict):
        error_categories = {
            "format_errors": ["Response must be a JSON object mapping aspect IDs to category IDs"],
            "validation_errors": [],
            "completeness_errors": []
        }
        content_sections = {
            "previous_json": {
                "title": "YOUR PREVIOUS JSON ATTEMPT",
                "content": json_text
            }
        }
        retry_context = create_retry_context(
            error_categories=error_categories,
            content_sections=content_sections
        )
        return False, retry_context
    
    # Validate assignments
    found_ids = set()
    validation_errors = []
    duplicate_ids = []
    
    for aspect_id, category_id in assignments.items():
        # Convert aspect_id to string for comparison
        aspect_id_str = str(aspect_id)
        
        if aspect_id_str not in expected_ids:
            validation_errors.append(f"Unexpected aspect ID '{aspect_id_str}' - must be one of {sorted(expected_ids)}")
            continue
            
        if aspect_id_str in found_ids:
            duplicate_ids.append(aspect_id_str)
        else:
            found_ids.add(aspect_id_str)
            
        if str(category_id) not in valid_category_ids:
            validation_errors.append(f"Invalid category ID '{category_id}' for aspect '{aspect_id_str}' - must be one of {sorted(valid_category_ids)}")
    
    # Check completeness
    missing_ids = expected_ids - found_ids
    
    # Categorize errors
    error_categories = {
        "format_errors": [],
        "validation_errors": validation_errors,
        "completeness_errors": []
    }
    
    if duplicate_ids:
        error_categories["completeness_errors"].append(f"Duplicate aspect IDs found: {sorted(duplicate_ids)}")
    if missing_ids:
        error_categories["completeness_errors"].append(f"Missing aspect IDs: {sorted(missing_ids)}")
    
    all_errors = error_categories["format_errors"] + error_categories["validation_errors"] + error_categories["completeness_errors"]
    
    if not all_errors:
        return True, assignments
    
    # Build content sections for retry
    content_sections = {}
    
    if json_text:
        content_sections["previous_json"] = {
            "title": "YOUR PREVIOUS JSON ATTEMPT",
            "content": json_text
        }
    
    content_sections["expected_aspect_ids"] = {
        "title": "EXPECTED ASPECT IDs",
        "content": str(sorted(expected_ids))
    }
    
    content_sections["valid_category_ids"] = {
        "title": "VALID CATEGORY IDs",
        "content": str(sorted(valid_category_ids))
    }
    
    if missing_ids:
        content_sections["missing_ids"] = {
            "title": "MISSING ASPECT IDs TO CATEGORIZE",
            "content": str(sorted(missing_ids))
        }
    
    retry_context = create_retry_context(
        error_categories=error_categories,
        content_sections=content_sections
    )
    
    return False, retry_context

def convert_assignments_to_categories(final_assignments: Dict[str, str], 
                                    consolidated_categories: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Convert final aspect assignments back to categorization format for mapping to products.
    
    Args:
        final_assignments: Dict mapping aspect_id to final category name
        consolidated_categories: Consolidated category taxonomy with definitions
    
    Returns:
        Categories in the expected format for map_categories_to_products
    """
    if not final_assignments:
        return {}
    
    # Group aspect IDs by their assigned category
    category_assignments = {}
    for aspect_id, category_name in final_assignments.items():
        if category_name not in category_assignments:
            category_assignments[category_name] = {
                "definition": consolidated_categories.get(category_name, {}).get("definition", "")
            }    
    return category_assignments

# === AGGREGATION AND DEDUPLICATION ===
def normalize_description_for_dedup(description: str, category: str) -> str:
    """Normalize description and category for deduplication using stemming"""
    import re
    
    # Combine category and description for normalization
    full_text = f"{category} {description}"
    
    # Convert to lowercase and clean, replacing underscores with spaces
    normalized = re.sub(r'[^\w\s]', ' ', full_text.lower())
    normalized = normalized.replace('_', ' ')  # Split on underscores too
    normalized = ' '.join(normalized.split())
    
    # Apply simple stemming to each word
    words = normalized.split()
    stemmed_words = [simple_stem(word) for word in words]
    
    return ' '.join(stemmed_words)

def deduplicate_aspects(all_aspects: List[Tuple[str, str, str, str]]) -> Tuple[List[Tuple[str, str]], Dict[str, List[str]], set, Dict[str, int], Dict[str, str]]:
    """
    Deduplicate aspects based on normalized descriptions and categories using stemming
    
    Args:
        all_aspects: List of (product_asin, aspect_id, category, description) tuples
    
    Returns:
        Tuple of (unique_aspects, aspect_mapping, unique_categories, category_distribution, original_to_unified_map)
        - unique_aspects: List of (unified_id, description) for categorization
        - aspect_mapping: Dict mapping unified_id to list of original (asin, aspect_id) pairs
        - unique_categories: Set of unique categories found
        - category_distribution: Dict mapping normalized categories to aspect counts
        - original_to_unified_map: Dict mapping original (asin, aspect_id) to unified_id
    """
    # Group aspects by normalized description and category
    description_groups = {}
    categories = set()
    normalized_categories = {}
    category_distribution = {}
    
    for asin, aspect_id, category, description in all_aspects:
        categories.add(category)
        
        # Track normalized categories
        normalized_category = simple_stem(category.lower().strip().replace('_', ' '))
        if normalized_category not in normalized_categories:
            normalized_categories[normalized_category] = set()
        normalized_categories[normalized_category].add(category)
        
        # Count aspects per normalized category
        if normalized_category not in category_distribution:
            category_distribution[normalized_category] = 0
        category_distribution[normalized_category] += 1
        
        normalized = normalize_description_for_dedup(description, category)
        if normalized not in description_groups:
            description_groups[normalized] = []
        description_groups[normalized].append((asin, aspect_id, category, description))
    
    # Create unique aspects and mapping
    unique_aspects = []
    aspect_mapping = {}
    original_to_unified_map = {}
    unified_counter = 0
    
    for normalized_desc, group in description_groups.items():
        unified_id = f"{unified_counter}"
        
        # Use the most comprehensive description from the group (longest one)
        best_description = max(group, key=lambda x: len(x[3]))[3]
        unique_aspects.append((unified_id, best_description))
        
        # Map unified ID to all original aspect IDs
        aspect_mapping[unified_id] = [(asin, aspect_id) for asin, aspect_id, _, _ in group]
        
        # Create reverse mapping from original to unified
        for asin, aspect_id, _, _ in group:
            original_to_unified_map[f"{asin}_{aspect_id}"] = unified_id
        
        unified_counter += 1
    
    print(f"Deduplicated {len(all_aspects)} aspects into {len(unique_aspects)} unique aspects")
    print(f"Found {len(categories)} unique original categories")
    print(f"Found {len(normalized_categories)} unique normalized categories")
    
    
    return unique_aspects, aspect_mapping, categories, category_distribution, original_to_unified_map

def collect_all_aspects_from_products(review_results: Dict[str, Any]) -> Tuple[List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]], List[Tuple[str, str, str, str]]]:
    """
    Collect all aspects from all products
    
    Returns:
        Tuple of (all_phy_aspects, all_perf_aspects, all_use_aspects)
        Each list contains (asin, aspect_id, category, description) tuples
    """
    all_phy_aspects = []
    all_perf_aspects = []
    all_use_aspects = []
    
    for asin, review_data in review_results.items():
        review_analysis = review_data.get('review_analysis', {})
        if not review_analysis:
            continue
        
        # Collect physical aspects
        if 'phy' in review_analysis:
            phy_aspects = extract_phy_aspects(review_analysis['phy'])
            for aspect_id, category, description in phy_aspects:
                all_phy_aspects.append((asin, aspect_id, category, description))
        
        # Collect performance aspects
        if 'perf' in review_analysis:
            perf_aspects = extract_perf_aspects(review_analysis['perf'])
            for aspect_id, category, description in perf_aspects:
                all_perf_aspects.append((asin, aspect_id, category, description))
        
        # Collect use case aspects
        if 'use' in review_analysis:
            use_aspects = extract_use_aspects(review_analysis['use'])
            for aspect_id, category, description in use_aspects:
                all_use_aspects.append((asin, aspect_id, category, description))
    
    print(f"Collected {len(all_phy_aspects)} physical, {len(all_perf_aspects)} performance, {len(all_use_aspects)} use case aspects across all products")
    return all_phy_aspects, all_perf_aspects, all_use_aspects

def expand_final_assignments_to_original_aspects(final_assignments: Dict[str, str], 
                                               original_to_unified_map: Dict[str, str],
                                               all_aspects: List[Tuple[str, str, str, str]]) -> Dict[str, str]:
    """
    Expand final assignments from unified aspects back to all original aspects
    
    Args:
        final_assignments: Dict mapping unified_id to category name
        original_to_unified_map: Dict mapping original (asin, aspect_id) to unified_id  
        all_aspects: List of all original (asin, aspect_id, category, description) tuples
    
    Returns:
        Dict mapping original (asin, aspect_id) to category name for all original aspects
    """
    original_assignments = {}
    
    for asin, aspect_id, original_category, description in all_aspects:
        original_key = f"{asin}_{aspect_id}"
        
        if original_key in original_to_unified_map:
            unified_id = original_to_unified_map[original_key]
            if unified_id in final_assignments:
                category_name = final_assignments[unified_id]
                original_assignments[original_key] = category_name
            else:
                # Fallback if unified aspect wasn't categorized
                original_assignments[original_key] = "UNCATEGORIZED"
        else:
            # Fallback if original aspect wasn't mapped
            original_assignments[original_key] = "UNMAPPED"
    
    return original_assignments

def map_categories_to_products(categorization_result: Dict[str, Any], aspect_mapping: Dict[str, List[str]], 
                              review_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Map categorization results back to individual products
    
    Args:
        categorization_result: Categorization result for unified aspects
        aspect_mapping: Mapping from unified_id to list of (asin, aspect_id) pairs
        review_results: Original review results
    
    Returns:
        Dict mapping asin to categorization results for that product
    """
    product_categories = {}
    
    # Initialize empty results for all products
    for asin in review_results.keys():
        product_categories[asin] = {}
    
    # Map categories back to products
    for category_name, category_data in categorization_result.items():
        category_definition = category_data.get('definition', '')
        unified_ids = category_data.get('ids', [])
        
        # For each unified ID in this category, map back to original products
        for unified_id in unified_ids:
            if unified_id in aspect_mapping:
                for asin, original_aspect_id in aspect_mapping[unified_id]:
                    if asin not in product_categories:
                        product_categories[asin] = {}
                    
                    if category_name not in product_categories[asin]:
                        product_categories[asin][category_name] = {
                            'definition': category_definition,
                            'aspects': []
                        }
                    
                    product_categories[asin][category_name]['aspects'].append(original_aspect_id)
    
    return product_categories

# === MAIN PROCESSING ===

async def process_all_products():
    """Process all products from consolidated review results with aggregation and deduplication"""
    print("Starting review aspect categorization with aggregation and deduplication...")
    
    # Load consolidated review results from the existing process_review output
    consolidated_path = config.get_data_path("result", "process_review", "20250609_01", "consolidated_review_results.json")
    
    if not consolidated_path.exists():
        print(f"Consolidated review results not found at {consolidated_path}")
        print("Please run process_reviews.py first to generate review hierarchies")
        return
    
    with open(consolidated_path, 'r', encoding='utf-8') as f:
        consolidated_data = json.load(f)
    
    review_results = consolidated_data.get('results', {})
    if not review_results:
        print("No review results found in consolidated data")
        return
    
    print(f"Processing aspect categorization for {len(review_results)} products...")
    
    # Step 1: Collect all aspects from all products
    all_phy_aspects, all_perf_aspects, all_use_aspects = collect_all_aspects_from_products(review_results)
    
    # Step 2: Deduplicate aspects for each type
    print("\nDeduplicating aspects...")
    print("\n--- Physical Aspects ---")
    unique_phy_aspects, phy_mapping, phy_categories, phy_distribution, phy_original_to_unified = deduplicate_aspects(all_phy_aspects)
    print("\n--- Performance Aspects ---")
    unique_perf_aspects, perf_mapping, perf_categories, perf_distribution, perf_original_to_unified = deduplicate_aspects(all_perf_aspects)
    print("\n--- Use Case Aspects ---")
    unique_use_aspects, use_mapping, use_categories, use_distribution, use_original_to_unified = deduplicate_aspects(all_use_aspects)
    
    # Load product categories from CSV category column
    product_categories = load_product_categories_from_csv()
    
    # Step 3: Initial categorization (batched, no validation)
    print("\nStep 3: Initial categorization of deduplicated aspects...")
    categorization_tasks = []
    
    if unique_phy_aspects:
        categorization_tasks.append(categorize_aspects(
            aspects=unique_phy_aspects,
            aspect_type="physical",
            aspect_context="physical product characteristics and attributes",
            input_description="Lines showing physical aspects in format: [ID] original theme: detail",
            product_categories=product_categories
        ))
    else:
        async def empty_result():
            return {}
        categorization_tasks.append(empty_result())
    
    if unique_perf_aspects:
        categorization_tasks.append(categorize_aspects(
            aspects=unique_perf_aspects,
            aspect_type="performance",
            aspect_context="product functionality and operational characteristics",
            input_description="Lines showing performance aspects in format: [ID] category: detail",
            product_categories=product_categories
        ))
    else:
        async def empty_result():
            return {}
        categorization_tasks.append(empty_result())
    
    if unique_use_aspects:
        categorization_tasks.append(categorize_aspects(
            aspects=unique_use_aspects,
            aspect_type="use case",
            aspect_context="product applications and usage scenarios",
            input_description="Lines following format: [ID] use case",
            product_categories=product_categories
        ))
    else:
        async def empty_result():
            return {}
        categorization_tasks.append(empty_result())
    
    # Wait for all initial categorizations to complete
    phy_batch_results, perf_batch_results, use_batch_results = await asyncio.gather(*categorization_tasks, return_exceptions=True)
    
    # Handle exceptions for initial categorization
    if isinstance(phy_batch_results, Exception):
        print(f"⚠️ Physical categorization failed: {phy_batch_results}")
        phy_batch_results = {}
    if isinstance(perf_batch_results, Exception):
        print(f"⚠️ Performance categorization failed: {perf_batch_results}")
        perf_batch_results = {}
    if isinstance(use_batch_results, Exception):
        print(f"⚠️ Use case categorization failed: {use_batch_results}")
        use_batch_results = {}
    
    # Step 4: Consolidation (if we had multiple batches, this would consolidate them)
    print("\nStep 4: Consolidating batch results...")
    # For now, we treat each result as a single "batch" to be consolidated if needed in the future
    # This step is designed for when we have multiple batches that need consolidation
    phy_consolidated = phy_batch_results if phy_batch_results else {}
    perf_consolidated = perf_batch_results if perf_batch_results else {}
    use_consolidated = use_batch_results if use_batch_results else {}
    
    print(f"✓ Consolidation complete:")
    print(f"   Physical: {len(phy_consolidated)} categories")
    print(f"   Performance: {len(perf_consolidated)} categories") 
    print(f"   Use cases: {len(use_consolidated)} categories")
    
    # Step 5: Final categorization (fresh categorization into consolidated categories)
    print("\nStep 5: Final categorization into consolidated categories...")
    final_categorization_tasks = []
    
    if unique_phy_aspects and phy_consolidated:
        final_categorization_tasks.append(final_categorize_aspects(
            aspects=unique_phy_aspects,
            consolidated_categories=phy_consolidated,
            aspect_type="physical",
            aspect_context="physical product characteristics and attributes",
            product_categories=product_categories
        ))
    else:
        async def empty_final_result():
            return {}
        final_categorization_tasks.append(empty_final_result())
    
    if unique_perf_aspects and perf_consolidated:
        final_categorization_tasks.append(final_categorize_aspects(
            aspects=unique_perf_aspects,
            consolidated_categories=perf_consolidated,
            aspect_type="performance",
            aspect_context="product functionality and operational characteristics",
            product_categories=product_categories
        ))
    else:
        async def empty_final_result():
            return {}
        final_categorization_tasks.append(empty_final_result())
    
    if unique_use_aspects and use_consolidated:
        final_categorization_tasks.append(final_categorize_aspects(
            aspects=unique_use_aspects,
            consolidated_categories=use_consolidated,
            aspect_type="use case",
            aspect_context="product applications and usage scenarios",
            product_categories=product_categories
        ))
    else:
        async def empty_final_result():
            return {}
        final_categorization_tasks.append(empty_final_result())
    
    # Wait for all final categorizations to complete
    phy_final_assignments, perf_final_assignments, use_final_assignments = await asyncio.gather(*final_categorization_tasks, return_exceptions=True)
    
    # Handle exceptions for final categorization
    if isinstance(phy_final_assignments, Exception):
        print(f"⚠️ Physical final categorization failed: {phy_final_assignments}")
        phy_final_assignments = {}
    if isinstance(perf_final_assignments, Exception):
        print(f"⚠️ Performance final categorization failed: {perf_final_assignments}")
        perf_final_assignments = {}
    if isinstance(use_final_assignments, Exception):
        print(f"⚠️ Use case final categorization failed: {use_final_assignments}")
        use_final_assignments = {}
    
    print(f"✓ Final categorization complete:")
    print(f"   Physical: {len(phy_final_assignments)} aspect assignments")
    print(f"   Performance: {len(perf_final_assignments)} aspect assignments")
    print(f"   Use cases: {len(use_final_assignments)} aspect assignments")
    
    # Expand final assignments back to all original aspects
    print("\nExpanding assignments to all original aspects...")
    phy_original_assignments = expand_final_assignments_to_original_aspects(
        phy_final_assignments, phy_original_to_unified, all_phy_aspects
    ) if phy_final_assignments else {}
    
    perf_original_assignments = expand_final_assignments_to_original_aspects(
        perf_final_assignments, perf_original_to_unified, all_perf_aspects
    ) if perf_final_assignments else {}
    
    use_original_assignments = expand_final_assignments_to_original_aspects(
        use_final_assignments, use_original_to_unified, all_use_aspects
    ) if use_final_assignments else {}
    
    print(f"✓ Expanded to original aspects:")
    print(f"   Physical: {len(phy_original_assignments)} original aspect assignments")
    print(f"   Performance: {len(perf_original_assignments)} original aspect assignments")
    print(f"   Use cases: {len(use_original_assignments)} original aspect assignments")
    
    # Convert final assignments back to categorization format for mapping
    phy_categories = convert_assignments_to_categories(phy_final_assignments, phy_consolidated)
    perf_categories = convert_assignments_to_categories(perf_final_assignments, perf_consolidated)
    use_categories = convert_assignments_to_categories(use_final_assignments, use_consolidated)
    
    # Step 6: Create simplified categorization results
    print("\nCreating simplified categorization results...")
    print(f"DEBUG: Processing {len(review_results)} products")
    print(f"DEBUG: phy_original_assignments has {len(phy_original_assignments)} entries")
    print(f"DEBUG: perf_original_assignments has {len(perf_original_assignments)} entries") 
    print(f"DEBUG: use_original_assignments has {len(use_original_assignments)} entries")
    
    # Show some sample keys to understand the format
    if phy_original_assignments:
        sample_phy_keys = list(phy_original_assignments.keys())[:5]
        print(f"DEBUG: Sample phy keys: {sample_phy_keys}")
    if perf_original_assignments:
        sample_perf_keys = list(perf_original_assignments.keys())[:5]
        print(f"DEBUG: Sample perf keys: {sample_perf_keys}")
    if use_original_assignments:
        sample_use_keys = list(use_original_assignments.keys())[:5]
        print(f"DEBUG: Sample use keys: {sample_use_keys}")
    
    final_results = {}
    processed_count = 0
    
    for asin in review_results.keys():
        review_analysis = review_results[asin].get('review_analysis', {})
        if not review_analysis:
            print(f"DEBUG: {asin} has no review_analysis")
            continue
            
        product_categorization = {
            'phy': {},
            'perf': {},
            'use': {}
        }
        
        # Map physical aspects to final categories
        if 'phy' in review_analysis and phy_original_assignments:
            print(f"DEBUG: {asin} has phy section with {len(review_analysis['phy'])} categories")
            for physical_category, details in review_analysis['phy'].items():
                if isinstance(details, dict):
                    detail_mappings = {}
                    for pid_detail, sentiments in details.items():
                        if '@' in pid_detail:
                            pid, detail = pid_detail.split('@', 1)
                            original_key = f"{asin}_{pid}"
                            print(f"DEBUG: Looking for key {original_key} in phy_original_assignments")
                            if original_key in phy_original_assignments:
                                final_category = phy_original_assignments[original_key]
                                detail_mappings[pid_detail] = final_category  # Keep PID@detail format
                                print(f"DEBUG: Found mapping {original_key} -> {final_category}")
                            else:
                                print(f"DEBUG: Key {original_key} not found in assignments")
                    
                    if detail_mappings:
                        product_categorization['phy'][physical_category] = detail_mappings
                        print(f"DEBUG: Added {len(detail_mappings)} mappings for {physical_category}")
                    else:
                        print(f"DEBUG: No mappings found for {physical_category}")
        
        # Map performance aspects to final categories  
        if 'perf' in review_analysis and perf_original_assignments:
            for perf_category, details in review_analysis['perf'].items():
                if isinstance(details, dict):
                    detail_mappings = {}
                    for perf_id_detail, sentiments in details.items():
                        if '@' in perf_id_detail:
                            perf_id, detail = perf_id_detail.split('@', 1)
                            original_key = f"{asin}_{perf_id}"
                            if original_key in perf_original_assignments:
                                final_category = perf_original_assignments[original_key]
                                detail_mappings[perf_id_detail] = final_category  # Keep perf_id@detail format
                    
                    if detail_mappings:
                        product_categorization['perf'][perf_category] = detail_mappings
        
        # Map use case aspects to final categories
        if 'use' in review_analysis and use_original_assignments:
            for use_case, sentiments in review_analysis['use'].items():
                original_key = f"{asin}_{use_case}"
                if original_key in use_original_assignments:
                    final_category = use_original_assignments[original_key]
                    product_categorization['use'][use_case] = final_category
        
        # Only include products that have at least some categorizations
        if (product_categorization['phy'] or 
            product_categorization['perf'] or 
            product_categorization['use']):
            final_results[asin] = {
                'aspect_categorization': product_categorization
            }
            processed_count += 1
    
    if final_results:
        # Save category definitions to separate file
        definitions_path = config.get_file_path("aspect_category_definitions.json")
        definitions_data = {
            'category_definitions': {
                'physical_categories': phy_categories,
                'performance_categories': perf_categories,
                'use_case_categories': use_categories
            },
            'generation_info': {
                'categorization_date': datetime.now().isoformat(),
                'model_used': config.MODEL_NAME,
                'total_products_processed': len(review_results),
            }
        }
        
        with open(definitions_path, 'w', encoding='utf-8') as f:
            json.dump(definitions_data, f, indent=2, ensure_ascii=False)
        
        # Save simplified consolidated categorized results
        categorized_path = config.get_file_path("consolidated_aspect_categorization.json")
        categorized_data = {
            'categorization_summary': {
                'total_products_categorized': processed_count,
                'total_products_attempted': len(review_results),
                'categorization_date': datetime.now().isoformat(),
                'model_used': config.MODEL_NAME,
                'configuration': config.to_dict()
            },
            'results': final_results
        }
        
        with open(categorized_path, 'w', encoding='utf-8') as f:
            json.dump(categorized_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Aspect categorization complete!")
        print(f"✓ Categorized {processed_count} products")
        print(f"✓ Deduplication efficiency:")
        print(f"   - Physical: {len(all_phy_aspects)} → {len(unique_phy_aspects)} aspects ({len(phy_categories)} categories)")
        print(f"   - Performance: {len(all_perf_aspects)} → {len(unique_perf_aspects)} aspects ({len(perf_categories)} categories)") 
        print(f"   - Use cases: {len(all_use_aspects)} → {len(unique_use_aspects)} aspects ({len(use_categories)} categories)")
        print(f"✓ Category definitions saved to: aspect_category_definitions.json")
        print(f"✓ Categorization results saved to: consolidated_aspect_categorization.json")
        print(f"✓ Results saved to {config.OUTPUT_ROOT_DIR}")
    else:
        print("\n❌ No categorization results generated")

# === MAIN EXECUTION ===
async def main():
    """Main execution function"""
    try:
        await process_all_products()
    except Exception as e:
        print(f"Error during categorization: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 