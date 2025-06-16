import json
import random
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import os
from pathlib import Path
from datetime import datetime
import hashlib
import asyncio
import time
from collections import deque

# Import shared utilities
from utils.config import get_segment_config
from utils.rate_limiter import RateLimiter
from utils.llm_utils import initialize_global_llm, get_global_llm
from utils.prompt_utils import PromptManager
from utils.json_utils import extract_json_from_response

# === CONFIGURATION ===
config = get_segment_config()

# Legacy compatibility - expose configuration as module-level variables
ROOT_DIR = config.ROOT_DIR
PROMPT_DIR = config.get_prompt_path("", "product_segment")
DATA_DIR = config.DATA_DIR
LOG_DIR = config.LOG_DIR

MODEL_NAME = config.MODEL_NAME
MODEL_TEMPERATURE = config.MODEL_TEMPERATURE
MODEL_MAX_TOKENS = config.MODEL_MAX_TOKENS

MAX_REQUESTS_PER_MINUTE = config.MAX_REQUESTS_PER_MINUTE
MAX_INPUT_TOKENS_PER_MINUTE = config.MAX_INPUT_TOKENS_PER_MINUTE
MAX_OUTPUT_TOKENS_PER_MINUTE = config.MAX_OUTPUT_TOKENS_PER_MINUTE
MAX_CONCURRENT_REQUESTS = config.MAX_CONCURRENT_REQUESTS

DEFAULT_BATCH_SIZE = config.DEFAULT_BATCH_SIZE
DEFAULT_SEED = config.DEFAULT_SEED
DEFAULT_MAX_RETRIES = config.DEFAULT_MAX_RETRIES
DEFAULT_CLUSTERS_PER_BATCH_RATIO = 80  # Products per cluster for initial clustering

# File paths
DEFAULT_CSV_PATH = config.get_data_path("processed", "combined_products_cleaned.csv")
OUTPUT_ROOT_DIR = config.OUTPUT_ROOT_DIR
DEFAULT_OUTPUT_PATH = OUTPUT_ROOT_DIR / "combined_products_with_categories.csv"
ORIGINAL_CONSOLIDATED_OUTPUT_PATH = OUTPUT_ROOT_DIR / "combined_products_with_original_consolidated_categories.csv"
FINAL_OUTPUT_PATH = OUTPUT_ROOT_DIR / "combined_products_with_final_categories.csv"
CACHE_DIR = config.CACHE_DIR
RESULT_CACHE_DIR = config.RESULT_CACHE_DIR

# Initialize shared utilities
rate_limiter = RateLimiter(
    max_requests_per_minute=MAX_REQUESTS_PER_MINUTE,
    max_input_tokens_per_minute=MAX_INPUT_TOKENS_PER_MINUTE,
    max_output_tokens_per_minute=MAX_OUTPUT_TOKENS_PER_MINUTE,
    max_concurrent_requests=MAX_CONCURRENT_REQUESTS,
    model_max_tokens=MODEL_MAX_TOKENS
)

# Initialize LLM manager
llm_manager = initialize_global_llm(
    model_name=MODEL_NAME,
    temperature=MODEL_TEMPERATURE,
    max_tokens=MODEL_MAX_TOKENS,
    rate_limiter=rate_limiter
)

# Initialize prompt manager
prompt_manager = PromptManager(PROMPT_DIR.parent, "product_segment")

# === RATE LIMITING SYSTEM (using shared utility) ===
# Rate limiter instance initialized above with configuration

# === PROMPT MANAGEMENT (using shared utility) ===
# Load prompts from files using shared prompt manager
TAXONOMY_EXTRACTION_PROMPT = prompt_manager.load_prompt("extract_taxonomy_prompt_v0.txt")
CONSOLIDATE_TAXONOMY_PROMPT = prompt_manager.load_prompt("consolidate_taxonomy_prompt_v0.txt")
REFINE_ASSIGNMENTS_PROMPT = prompt_manager.load_prompt("refine_assignments_prompt_v0.txt")
SHARED_RETRY_PROMPT_TEMPLATE = prompt_manager.load_prompt("shared_retry_prompt_v0.txt")

# === MODEL INITIALIZATION (using shared utility) ===
# LLM manager initialized above with configuration
llm = llm_manager.llm  # For backward compatibility with existing code

# === ASYNC LLM WRAPPER (using shared utility) ===
async def safe_llm_call(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Safe async LLM call with rate limiting and error handling
    Uses the shared LLM utility for consistency.
    """
    return await llm_manager.safe_call(prompt, context)

# Legacy compatibility for direct access
def safe_llm_call_legacy(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Legacy function signature - kept for backward compatibility"""
    estimated_input_tokens = rate_limiter.estimate_tokens(prompt)
    
    try:
        # The shared utilities handle this automatically
        pass
    except Exception as e:
        rate_limiter.release()  # Always release semaphore
        print(f"❌ LLM call failed: {e}")
        raise

# === CACHING SYSTEM ===

def generate_cache_key(base_prompt: str, context: Dict[str, Any]) -> str:
    """Generate a unique cache key based on base prompt and context"""
    # Create a deterministic string from base prompt and context
    context_str = json.dumps(context, sort_keys=True, ensure_ascii=False)
    combined = f"{base_prompt}\n---CONTEXT---\n{context_str}"
    
    # Generate SHA256 hash
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return hash_obj.hexdigest()[:16]  # Use first 16 characters for readability

def create_cache_filename(interaction_type: str, cache_key: str, 
                         batch_id: Optional[int] = None, category: Optional[str] = None) -> str:
    """Create interpretable cache filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    
    parts = [interaction_type]
    if category:
        parts.append(f"cat_{category.replace(':', '_').replace(' ', '_')}")
    if batch_id is not None:
        parts.append(f"batch{batch_id}")
    parts.extend([cache_key, timestamp])
    
    return "_".join(parts) + ".json"

def save_llm_cache(prompt: str, response: str, interaction_type: str, context: Dict[str, Any],
                   batch_id: Optional[int] = None, category: Optional[str] = None,
                   base_prompt: Optional[str] = None) -> str:
    """Save successful LLM response to cache with context"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Use base_prompt for cache key if provided, otherwise use full prompt
    cache_key_prompt = base_prompt if base_prompt is not None else prompt
    cache_key = generate_cache_key(cache_key_prompt, context)
    filename = create_cache_filename(interaction_type, cache_key, batch_id, category)
    
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "interaction_type": interaction_type,
        "cache_key": cache_key,
        "context": context,
        "base_prompt": cache_key_prompt,  # Store the base prompt used for caching
        "prompt": prompt,
        "response": response,
        "model_name": MODEL_NAME,
        "model_temperature": MODEL_TEMPERATURE,
        "batch_id": batch_id,
        "category": category
    }
    
    cache_path = CACHE_DIR / filename
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Cached LLM response: {filename}")
    return str(cache_path)

def load_llm_cache(prompt: str, context: Dict[str, Any], interaction_type: str,
                   base_prompt: Optional[str] = None) -> Optional[str]:
    """Load cached LLM response if it exists and matches"""
    if not CACHE_DIR.exists():
        return None
        
    # Use base_prompt for cache key if provided, otherwise use full prompt
    cache_key_prompt = base_prompt if base_prompt is not None else prompt
    cache_key = generate_cache_key(cache_key_prompt, context)
    
    # Search for matching cache files
    for cache_file in CACHE_DIR.glob(f"{interaction_type}_*_{cache_key}_*.json"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verify the cache matches our request
            if (cache_data.get("cache_key") == cache_key and 
                cache_data.get("interaction_type") == interaction_type and
                cache_data.get("model_name") == MODEL_NAME and
                cache_data.get("base_prompt") == cache_key_prompt and
                cache_data.get("context") == context):
                
                print(f"🔄 Using cached response: {cache_file.name}")
                return cache_data["response"]
                
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            continue
    
    return None

# === RESULT CACHING SYSTEM ===
def generate_result_cache_key(input_file_path: str, processing_params: Dict[str, Any]) -> str:
    """Generate cache key for result files based on input file and processing parameters"""
    # Include file modification time and size for change detection
    file_path = Path(input_file_path)
    if file_path.exists():
        file_stats = {
            "mtime": file_path.stat().st_mtime,
            "size": file_path.stat().st_size
        }
    else:
        file_stats = {"mtime": 0, "size": 0}
    
    # Combine file stats with processing parameters
    cache_context = {
        "input_file": str(file_path),
        "file_stats": file_stats,
        "processing_params": processing_params
    }
    
    context_str = json.dumps(cache_context, sort_keys=True, ensure_ascii=False)
    hash_obj = hashlib.sha256(context_str.encode('utf-8'))
    return hash_obj.hexdigest()[:16]

def save_result_cache(result_df: pd.DataFrame, taxonomies: Dict[str, Dict[str, Any]], 
                     input_file_path: str, processing_params: Dict[str, Any],
                     result_type: str = "segmentation") -> str:
    """Save processing results with context metadata"""
    RESULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    cache_key = generate_result_cache_key(input_file_path, processing_params)
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    
    # Create cache data
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "result_type": result_type,
        "cache_key": cache_key,
        "input_file_path": input_file_path,
        "processing_params": processing_params,
        "model_config": {
            "model_name": MODEL_NAME,
            "temperature": MODEL_TEMPERATURE,
            "batch_size": DEFAULT_BATCH_SIZE,
            "seed": DEFAULT_SEED
        },
        "result_stats": {
            "total_products": len(result_df),
            "categories_found": len(taxonomies),
            "products_with_segments": len(result_df[result_df[processing_params["output_col"]].notna()])
        }
    }
    
    # Save cache metadata
    cache_filename = f"{result_type}_{cache_key}_{timestamp}.json"
    cache_path = RESULT_CACHE_DIR / cache_filename
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    # Save result files with cache key prefix
    result_prefix = f"{result_type}_{cache_key}_{timestamp}"
    
    # Save main result DataFrame
    result_csv_path = RESULT_CACHE_DIR / f"{result_prefix}_results.csv"
    result_df.to_csv(result_csv_path, index=False)
    
    # Save taxonomies
    taxonomy_path = RESULT_CACHE_DIR / f"{result_prefix}_taxonomies.json"
    with open(taxonomy_path, 'w', encoding='utf-8') as f:
        json.dump(taxonomies, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Cached results: {cache_filename}")
    return str(cache_path)

def load_result_cache(input_file_path: str, processing_params: Dict[str, Any], 
                     result_type: str = "segmentation") -> Optional[Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]]:
    """Load cached results if they exist and match current context"""
    if not RESULT_CACHE_DIR.exists():
        return None
    
    cache_key = generate_result_cache_key(input_file_path, processing_params)
    
    # Search for matching cache files
    for cache_file in RESULT_CACHE_DIR.glob(f"{result_type}_{cache_key}_*.json"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verify cache matches current context
            if (cache_data.get("cache_key") == cache_key and
                cache_data.get("result_type") == result_type and
                cache_data.get("input_file_path") == input_file_path and
                cache_data.get("processing_params") == processing_params and
                cache_data.get("model_config", {}).get("model_name") == MODEL_NAME):
                
                # Load result files
                cache_prefix = cache_file.stem  # Remove .json extension
                
                result_csv_path = RESULT_CACHE_DIR / f"{cache_prefix}_results.csv"
                taxonomy_path = RESULT_CACHE_DIR / f"{cache_prefix}_taxonomies.json"
                
                if result_csv_path.exists() and taxonomy_path.exists():
                    # Load DataFrame
                    result_df = pd.read_csv(result_csv_path)
                    
                    # Load taxonomies
                    with open(taxonomy_path, 'r', encoding='utf-8') as f:
                        taxonomies = json.load(f)
                    
                    print(f"🔄 Using cached results: {cache_file.name}")
                    return result_df, taxonomies
                
        except (json.JSONDecodeError, KeyError, FileNotFoundError, pd.errors.EmptyDataError):
            continue
    
    return None

# === LOGGING FUNCTIONS (kept for backward compatibility) ===
def create_log_filename(interaction_type: str, batch_id: Optional[int] = None, 
                       attempt: Optional[int] = None) -> str:
    """Create consistent log filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if batch_id is not None and attempt is not None:
        return f"{interaction_type}_batch{batch_id}_attempt{attempt}_{timestamp}"
    elif batch_id is not None:
        return f"{interaction_type}_batch{batch_id}_{timestamp}"
    else:
        return f"{interaction_type}_{timestamp}"

def save_llm_interaction(prompt: str, response: str, interaction_type: str, 
                        batch_id: Optional[int] = None, attempt: Optional[int] = None) -> None:
    """Save LLM input and response to files with metadata"""
    LOG_DIR.mkdir(exist_ok=True)
    filename_base = create_log_filename(interaction_type, batch_id, attempt)
    
    # Save files
    files_created = {}
    for suffix, content in [("input.txt", prompt), ("response.txt", response)]:
        file_path = LOG_DIR / f"{filename_base}_{suffix}"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        files_created[suffix.split('.')[0]] = str(file_path)
    
    
    print(f"📝 Saved LLM interaction: {filename_base}")

# === DATA PROCESSING ===
def load_data(csv_path: str) -> pd.DataFrame:
    """Load and validate product data from CSV file"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} products from {csv_path}")
    return df

def get_unique_categories(df: pd.DataFrame, category_col: str = 'category') -> List[str]:
    """Extract unique categories from dataframe"""
    if category_col in df.columns:
        categories = df[category_col].dropna().unique().tolist()
        print(f"Found {len(categories)} unique categories: {categories}")
        return categories
    else:
        print(f"No '{category_col}' column found, using default category 'Products'")
        return ["Products"]

def filter_data_by_category(df: pd.DataFrame, category: str, 
                          category_col: str = 'category') -> pd.DataFrame:
    """Filter dataframe to only include products from specific category"""
    if category_col in df.columns:
        filtered_df = df[df[category_col] == category].copy()
    else:
        filtered_df = df.copy()
    
    print(f"Filtered to {len(filtered_df)} products for category '{category}'")
    return filtered_df

# === RANDOM BATCH SAMPLING ===
def add_random_groups(df: pd.DataFrame, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Add random group assignments for batch sampling"""
    df_with_groups = df.copy()
    rng = random.Random(seed)
    
    # Create random group assignments (simulating clusters for batch diversity)
    n_groups = max(2, len(df) // DEFAULT_CLUSTERS_PER_BATCH_RATIO)
    print(f"Creating {n_groups} random groups for {len(df)} products...")
    
    group_assignments = [rng.randint(0, n_groups - 1) for _ in range(len(df))]
    df_with_groups["cluster"] = group_assignments
    
    return df_with_groups

# === BATCH PROCESSING ===


def calculate_optimal_batch_sizes(total_items: int, target_batch_size: int) -> List[int]:
    """Calculate optimal batch sizes to avoid small remainders"""
    if total_items <= target_batch_size:
        return [total_items]
    
    # Calculate number of batches needed
    num_batches = max(1, round(total_items / target_batch_size))
    
    # Calculate base size and remainder
    base_size = total_items // num_batches
    remainder = total_items % num_batches
    
    # Distribute remainder across batches
    batch_sizes = [base_size] * num_batches
    for i in range(remainder):
        batch_sizes[i] += 1
    
    return batch_sizes

def make_batches(df: pd.DataFrame) -> Tuple[List[pd.DataFrame], List[List[int]]]:
    """Create evenly-sized batches from dataframe with index mapping
    
    Returns:
        Tuple of (batches, index_mappings) where:
        - batches: List of DataFrames with sequential indices (0, 1, 2...)
        - index_mappings: List of lists, where index_mappings[i][j] gives the original 
          DataFrame index for position j in batch i
    """
    # Calculate optimal batch sizes
    optimal_sizes = calculate_optimal_batch_sizes(len(df), DEFAULT_BATCH_SIZE)
    print(f"Creating {len(optimal_sizes)} batches with sizes: {optimal_sizes}")
    
    # Shuffle the dataframe for random distribution using fixed seed
    shuffled_df = df.sample(frac=1, random_state=DEFAULT_SEED)
    original_indices = shuffled_df.index.tolist()  # Capture original indices before reset
    shuffled_df = shuffled_df.reset_index(drop=True)
    
    batches = []
    index_mappings = []
    start_idx = 0
    
    for target_size in optimal_sizes:
        end_idx = start_idx + target_size
        if start_idx < len(shuffled_df):
            batch = shuffled_df.iloc[start_idx:end_idx].copy()
            # Keep sequential indices (0, 1, 2, 3...)
            batch.index = range(len(batch))
            
            # Create mapping from batch position to original DataFrame index
            batch_mapping = original_indices[start_idx:end_idx]
            
            batches.append(batch)
            index_mappings.append(batch_mapping)
            start_idx = end_idx
        else:
            break
    
    actual_sizes = [len(batch) for batch in batches]
    print(f"Created {len(batches)} batches with actual sizes: {actual_sizes}")
    return batches, index_mappings

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
        **additional_kwargs: Additional template variables (e.g., product_category)
    
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
    
    # Combine template variables (removed redundant count variables)
    template_vars = {
        "error_details": error_details,
        "content_sections": "\n".join(content_sections_text),
        **additional_kwargs
    }
    
    # Format the shared retry template
    retry_instructions = SHARED_RETRY_PROMPT_TEMPLATE.format(**template_vars)
    
    # Append retry instructions to original prompt
    return original_prompt + retry_instructions

# === PROMPT BUILDING AND VALIDATION ===
def build_batch_input(batch: pd.DataFrame, input_col: str) -> str:
    """Build input string for LLM from batch data"""
    return "\n".join(f"[{i}] {text}" for i, text in enumerate(batch[input_col]))

# extract_json_from_response function is now imported from utils.json_utils

def parse_and_validate_response(response_text: str, expected_ids: set, 
                               batch: pd.DataFrame, input_col: str) -> Tuple[bool, Any]:
    """
    Parse LLM response and validate completeness for product segmentation.
    
    Args:
        response_text: Raw LLM response text
        expected_ids: Set of expected product IDs (0, 1, 2, ...)
        batch: DataFrame containing batch products for context
        input_col: Column name containing product descriptions
    
    Returns:
        Tuple of (is_valid: bool, result: Dict or structured_retry_context)
        
    Data Contract:
        - On success: returns (True, parsed_taxonomy_dict)
        - On failure: returns (False, standardized_retry_context)
        - expected_ids must be consecutive integers starting from 0
        - parsed_taxonomy_dict has schema: {"category": {"definition": "...", "ids": [...]}}
        - retry_context follows create_retry_context() format
    """
    
    # Try to extract JSON from response
    json_text = ""
    taxonomy = {}
    json_error = ""
    
    try:
        json_text = extract_json_from_response(response_text)
        taxonomy = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        json_error = f"Could not extract valid JSON: {e}"
    
    # Validate JSON structure
    structure_errors = []
    if not isinstance(taxonomy, dict):
        structure_errors.append("Response must be a JSON object")
    
    # Collect all IDs and validation errors
    found_ids = set()
    duplicate_ids = []
    validation_errors = []
    
    if isinstance(taxonomy, dict):
        for category, category_data in taxonomy.items():
            # Handle new schema: {"category": {"definition": "...", "ids": [...]}}
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
                try:
                    id_int = int(id_val)
                    if id_int in found_ids:
                        duplicate_ids.append(id_int)
                    else:
                        found_ids.add(id_int)
                except (ValueError, TypeError):
                    validation_errors.append(f"Invalid ID '{id_val}' in category '{category}' - must be an integer")
    
    # Check for missing/extra IDs
    missing_ids = expected_ids - found_ids
    extra_ids = found_ids - expected_ids
    
    # Categorize errors logically
    error_categories = {
        "format_errors": [],
        "validation_errors": [],
        "completeness_errors": []
    }
    
    if json_error:
        error_categories["format_errors"].append(json_error)
    if structure_errors:
        error_categories["format_errors"].extend(structure_errors)
    if validation_errors:
        error_categories["validation_errors"].extend(validation_errors)
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
        return True, taxonomy
    
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
            "content": json_text
        }
    
    # Missing products section
    if missing_ids:
        missing_lines = "\n".join(f"[{i}] {batch[input_col].iloc[i]}" for i in sorted(missing_ids))
        content_sections["missing_products"] = {
            "title": "MISSING PRODUCTS TO CATEGORIZE",
            "content": missing_lines
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

def process_batch_taxonomy(taxonomy: Dict[str, Dict[str, Any]], batch: pd.DataFrame, batch_mapping: List[int],
                          product_category: str, input_col: str) -> Dict[str, Dict[str, Any]]:
    """Process taxonomy results, preserving all categories including OUT_OF_SCOPE, with definitions and inputs"""
    global_taxonomy = {}
    out_of_scope_count = 0
    
    for category, category_data in taxonomy.items():
        # Extract IDs from new schema: {"definition": "...", "ids": [...]}
        if not isinstance(category_data, dict):
            raise ValueError(f"Category '{category}' must be an object with 'definition' and 'ids' fields, got {type(category_data)}")
        
        if "ids" not in category_data:
            raise ValueError(f"Category '{category}' missing required 'ids' field")
            
        product_ids = category_data["ids"]
        
        if category == "OUT_OF_SCOPE":
            out_of_scope_count = len(product_ids)
            print(f"Found {out_of_scope_count} products marked as OUT_OF_SCOPE (not belonging to {product_category})")
        # Map local IDs to original row numbers and collect product inputs
        mapped_product_ids = [batch_mapping[i] for i in product_ids]
        product_inputs = []
        
        for i in product_ids:
            if i < len(batch):
                product_inputs.append(batch.iloc[i][input_col])
        
        global_taxonomy[category] = {
            "definition": category_data["definition"],
            "product_ids": mapped_product_ids,
            "product_inputs": product_inputs
        }
    
    valid_categories = len(global_taxonomy)
    print(f"✓ Processed successfully with {valid_categories} valid categories")
    
    return global_taxonomy

# === BATCH EXECUTION ===
async def run_batch(batch: pd.DataFrame, batch_mapping: List[int], batch_id: int, input_col: str, product_category: str, 
              max_tries: int = DEFAULT_MAX_RETRIES) -> Dict[str, Dict[str, Any]]:
    """
    Process a single batch of products to generate initial taxonomy with unified retry logic.
    
    Args:
        batch: DataFrame with sequential indices (0, 1, 2...) containing products to process
        batch_mapping: List mapping batch positions to original DataFrame indices  
        batch_id: Batch identifier for logging
        input_col: Column name containing product descriptions
        product_category: Category context for AI segmentation
        max_tries: Maximum retry attempts per batch
        
    Returns:
        Dictionary containing processed taxonomy: {category_name: {"definition": "...", "product_ids": [...], "product_inputs": [...]}}
        
    Data Contract:
        - batch indices must be sequential starting from 0
        - batch_mapping[i] gives original DataFrame index for batch position i
        - Returns taxonomy with clean category names (no prefixes)
        - All product_ids are mapped to original DataFrame indices
        - Uses unified retry system on validation failures
        
    Raises:
        RuntimeError: If LLM fails to process all products after max_tries
    """
    expected_ids = set(range(len(batch)))
    batch_input = build_batch_input(batch, input_col)
    formatted_prompt = TAXONOMY_EXTRACTION_PROMPT.format(product_category=product_category)
    full_prompt = formatted_prompt + "\n\n" + batch_input
    
    # Create cache context for this specific batch
    cache_context = {
        "batch_size": len(batch),
        "expected_ids": sorted(list(expected_ids)),
        "product_category": product_category,
        "input_col": input_col,
        "batch_mapping": batch_mapping,
        "batch_products": batch[input_col].tolist()  # Include actual products for cache validation
    }
    
    # Check cache first using base prompt
    cached_response = load_llm_cache(full_prompt, cache_context, "segmentation", base_prompt=formatted_prompt)
    if cached_response:
        print(f"✓ Using cached result for batch {batch_id}")
        # Cached responses are already validated, parse directly
        json_text = extract_json_from_response(cached_response)
        result = json.loads(json_text)
        return process_batch_taxonomy(result, batch, batch_mapping, product_category, input_col)
    
    print(f"Processing batch {batch_id} with {len(batch)} products...")
    
    for attempt in range(max_tries):
        print(f"Debug - Sending prompt to LLM: {full_prompt}")
        
        response_text = await safe_llm_call(full_prompt)
        
        print(f"Debug - LLM response (first 200 chars): {response_text[:200]}...")
        print(f"Debug - Full LLM response: {repr(response_text)}")
        
        # Save LLM interaction (legacy logging)
        save_llm_interaction(
            prompt=full_prompt,
            response=response_text,
            interaction_type="segmentation",
            batch_id=batch_id,
            attempt=attempt + 1
        )
        
        is_valid, result = parse_and_validate_response(response_text, expected_ids, batch, input_col)
        if is_valid:
            # Save successful response to cache using base prompt
            save_llm_cache(
                prompt=full_prompt,
                response=response_text,
                interaction_type="segmentation",
                context=cache_context,
                batch_id=batch_id,
                category=product_category,
                base_prompt=formatted_prompt
            )
            return process_batch_taxonomy(result, batch, batch_mapping, product_category, input_col)
        
        print(f"✗ Attempt {attempt + 1} failed, retrying...")
        print(f"  Issues: {result['issues_summary']}")
        
        # Use unified retry prompt builder
        retry_prompt = build_retry_prompt(
            original_prompt=formatted_prompt,
            retry_context=result,
            product_category=product_category
        )
        
        # Replace prompt with focused retry + batch input
        full_prompt = retry_prompt + "\n\n" + batch_input
        print(f"Debug - Retry prompt created: {retry_prompt[:200]}...")
    
    raise RuntimeError("LLM failed to process all IDs after maximum retries.")

# === TAXONOMY MERGING ===
def create_taxonomy_with_ids(taxonomy: Dict[str, Dict[str, Any]], prefix: str) -> Dict[str, Dict[str, Any]]:
    """Create taxonomy with prefixed category IDs and preserve structure for merging"""
    taxonomy_with_ids = {}
    categories = list(taxonomy.keys())
    
    for i, category in enumerate(categories):
        category_id = f"{prefix}_{i}"
        category_info = taxonomy[category]
        taxonomy_with_ids[category] = {
            "definition": category_info.get("definition", f"Products from {category} category"),
            "ids": [category_id]
        }
    
    return taxonomy_with_ids

def parse_and_validate_consolidate_response(response_text: str, expected_a_ids: set, 
                                     expected_b_ids: set, taxonomy_a: Dict[str, Dict[str, Any]], 
                                     taxonomy_b: Dict[str, Dict[str, Any]]) -> Tuple[bool, Any]:
    """
    Parse and validate consolidate response for taxonomy merging.
    
    Args:
        response_text: Raw LLM response text
        expected_a_ids: Set of expected category IDs from taxonomy A (A_0, A_1, ...)
        expected_b_ids: Set of expected category IDs from taxonomy B (B_0, B_1, ...)
        taxonomy_a: Source taxonomy A for context
        taxonomy_b: Source taxonomy B for context
    
    Returns:
        Tuple of (is_valid: bool, result: Dict or structured_retry_context)
        
    Data Contract:
        - On success: returns (True, consolidated_structure_dict)
        - On failure: returns (False, standardized_retry_context)
        - expected_a_ids format: {"A_0", "A_1", ...}, expected_b_ids format: {"B_0", "B_1", ...}
        - consolidated_structure_dict has schema: {"category": {"definition": "...", "ids": [...]}}
        - retry_context follows create_retry_context() format
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
            content_sections=content_sections,
            expected_count=len(expected_a_ids | expected_b_ids),
            found_count=0
        )
        return False, retry_context
    
    # Collect all IDs from the consolidated structure (new schema)
    found_ids = set()
    found_a_ids = set()
    found_b_ids = set()
    validation_errors = []
    duplicate_ids = []
    
    for category, category_data in consolidated_structure.items():
        # Handle new schema: {"category": {"definition": "...", "ids": [...]}}
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
    missing_a_ids = expected_a_ids - found_a_ids
    missing_b_ids = expected_b_ids - found_b_ids
    
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
    if missing_a_ids:
        error_categories["completeness_errors"].append(f"Missing from Taxonomy A: {sorted(missing_a_ids)}")
    if missing_b_ids:
        error_categories["completeness_errors"].append(f"Missing from Taxonomy B: {sorted(missing_b_ids)}")
    
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
    
    # Create readable summaries for retry
    taxonomy_a_summary = ", ".join([f"A_{i} = '{cat}'" for i, cat in enumerate(taxonomy_a.keys())])
    taxonomy_b_summary = ", ".join([f"B_{i} = '{cat}'" for i, cat in enumerate(taxonomy_b.keys())])
    
    content_sections["taxonomy_mappings"] = {
        "title": "CATEGORY ID MAPPINGS",
        "content": f"Taxonomy A: {taxonomy_a_summary}\nTaxonomy B: {taxonomy_b_summary}"
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

async def consolidate_taxonomies(taxonomy_a: Dict[str, Dict[str, Any]], taxonomy_b: Dict[str, Dict[str, Any]], 
                          category_id_map: Dict[str, str], max_tries: int = DEFAULT_MAX_RETRIES) -> Dict[str, Dict[str, Any]]:
    """
    Consolidate two taxonomies into one coherent structure using AI-guided merging with unified retry logic.
    
    Args:
        taxonomy_a: Existing consolidated taxonomy {category_name: {"definition": "...", "product_ids": [...], "product_inputs": [...]}}
        taxonomy_b: New batch taxonomy to merge in
        category_id_map: Mapping dictionary for category ID resolution (updated in-place)
        max_tries: Maximum retry attempts for consolidation
        
    Returns:
        Consolidated taxonomy structure with same schema as inputs
        
    Data Contract:
        - Input taxonomies must have schema: {category_name: {"definition": str, "product_ids": List[int], "product_inputs": List[str]}}
        - OUT_OF_SCOPE categories are filtered out before consolidation and restored after
        - Returns consolidated taxonomy with same schema
        - category_id_map is updated with A_i → category_a mappings and B_i → category_b mappings  
        - Uses unified retry system on validation failures
        
    Raises:
        RuntimeError: If LLM fails to consolidate taxonomies after max_tries
    """
    # Note: OUT_OF_SCOPE categories are filtered out before calling this function and added back after
    taxonomy_a_with_ids = create_taxonomy_with_ids(taxonomy_a, "A")
    taxonomy_b_with_ids = create_taxonomy_with_ids(taxonomy_b, "B")
    
    # Update category ID map
    for i, category in enumerate(taxonomy_a.keys()):
        category_id_map[f"A_{i}"] = category
    for i, category in enumerate(taxonomy_b.keys()):
        category_id_map[f"B_{i}"] = category
    
    base_prompt = CONSOLIDATE_TAXONOMY_PROMPT.format(
        taxonomy_a=json.dumps(taxonomy_a_with_ids, indent=2),
        taxonomy_b=json.dumps(taxonomy_b_with_ids, indent=2)
    )
    prompt = base_prompt
    
    # Expected IDs for validation
    expected_a_ids = {f"A_{i}" for i in range(len(taxonomy_a))}
    expected_b_ids = {f"B_{i}" for i in range(len(taxonomy_b))}
    
    # Create cache context for consolidation
    cache_context = {
        "taxonomy_a_categories": sorted(list(taxonomy_a.keys())),
        "taxonomy_b_categories": sorted(list(taxonomy_b.keys())),
        "expected_a_ids": sorted(list(expected_a_ids)),
        "expected_b_ids": sorted(list(expected_b_ids)),
        "taxonomy_a_with_ids": taxonomy_a_with_ids,
        "taxonomy_b_with_ids": taxonomy_b_with_ids
    }
    
    # Check cache first using base prompt
    cached_response = load_llm_cache(prompt, cache_context, "consolidate_taxonomy", base_prompt=base_prompt)
    if cached_response:
        print("✓ Using cached consolidation result")
        # Cached responses are already validated, parse directly
        json_text = extract_json_from_response(cached_response)
        result = json.loads(json_text)
        return result
    
    print(f"Merging taxonomies - A: {sorted(expected_a_ids)}, B: {sorted(expected_b_ids)}")
    
    # Show what categories are being consolidated
    print("\nCategories to consolidate:")
    print(f"  Taxonomy A: {list(taxonomy_a.keys())}")
    print(f"  Taxonomy B: {list(taxonomy_b.keys())}")
    
    for attempt in range(max_tries):
        print(f"Debug - Consolidate attempt {attempt + 1}, prompt length: {len(prompt)}")
        
        response_text = await safe_llm_call(prompt)
        
        save_llm_interaction(
            prompt=prompt,
            response=response_text,
            interaction_type="consolidate_taxonomy",
            attempt=attempt + 1
        )
        
        is_valid, result = parse_and_validate_consolidate_response(
            response_text, expected_a_ids, expected_b_ids, taxonomy_a, taxonomy_b
        )
        
        if is_valid:
            consolidated_structure = result
            
            # Save successful response to cache using base prompt
            save_llm_cache(
                prompt=prompt,
                response=response_text,
                interaction_type="consolidate_taxonomy",
                context=cache_context,
                base_prompt=base_prompt
            )
            
            print(f"✓ Taxonomies consolidated successfully into {len(consolidated_structure)} categories")
            
            # Print the consolidated category structure
            print("\nConsolidated categories:")
            for new_category, category_data in consolidated_structure.items():
                category_ids = category_data["ids"]
                # Show which original categories were consolidated
                a_categories = []
                b_categories = []
                for cat_id in category_ids:
                    if cat_id.startswith("A_"):
                        idx = int(cat_id.split("_")[1])
                        if idx < len(list(taxonomy_a.keys())):
                            a_categories.append(list(taxonomy_a.keys())[idx])
                    elif cat_id.startswith("B_"):
                        idx = int(cat_id.split("_")[1])
                        if idx < len(list(taxonomy_b.keys())):
                            b_categories.append(list(taxonomy_b.keys())[idx])
                
                consolidated_from = []
                if a_categories:
                    consolidated_from.extend([f"A:{cat}" for cat in a_categories])
                if b_categories:
                    consolidated_from.extend([f"B:{cat}" for cat in b_categories])
                
                print(f"  '{new_category}' ← {' + '.join(consolidated_from)}")
            
            return consolidated_structure
        else:
            print(f"✗ Consolidate attempt {attempt + 1} failed, retrying...")
            print(f"  Issues: {result['issues_summary']}")
            
            # Use unified retry prompt builder
            retry_prompt = build_retry_prompt(
                original_prompt=base_prompt,
                retry_context=result
            )
            
            prompt = retry_prompt  # Replace prompt with retry
            print(f"Debug - Consolidation retry prompt created (first 300 chars): {retry_prompt[:300]}...")

    raise RuntimeError("LLM failed to consolidate taxonomies after maximum retries.")

# === REPORTING FUNCTIONS ===
def print_category_summary(category: str, num_products: int) -> None:
    """Print summary for processing a category"""
    print(f"\n{'='*60}")
    print(f"Processing category: {category}")
    print(f"{'='*60}")
    print(f"Processing {num_products} products in category '{category}'...")

def print_final_summary(result_df: pd.DataFrame, output_col: str) -> None:
    """Print final processing summary"""
    segment_counts = result_df[output_col].value_counts()
    products_with_segments = len(result_df[result_df[output_col].notna()])
    products_without_segments = len(result_df) - products_with_segments
    out_of_scope_count = segment_counts.get("OUT_OF_SCOPE", 0)
    
    print(f"\n{'='*60}")
    print("✓ Segmentation complete!")
    print(f"Total products processed: {len(result_df)}")
    print(f"Products with segments: {products_with_segments}")
    print(f"Products without segments: {products_without_segments}")
    if out_of_scope_count > 0:
        print(f"Products categorized as OUT_OF_SCOPE: {out_of_scope_count}")
    print(f"Final segments created: {len(segment_counts)}")
    
    print("\nFinal segment distribution:")
    for segment, count in segment_counts.head(10).items():  # Show top 10
        if segment is not None:
            print(f"  {segment}: {count} products")
    
    if len(segment_counts) > 10:
        print(f"  ... and {len(segment_counts) - 10} more segments")

def update_result_dataframe(result_df: pd.DataFrame, category_result: pd.DataFrame, 
                           category: str, output_col: str) -> None:
    """
    Update main result dataframe with category-specific results.
    
    Args:
        result_df: Main DataFrame to update
        category_result: Category-specific results DataFrame
        category: Category name being processed (for logging only)
        output_col: Column name for category assignments
        
    Data Contract:
        - category_result[output_col] contains clean category names (no prefixes)
        - Updates result_df[output_col] with the same clean category names
    """
    for idx, row in category_result.iterrows():
        if output_col in row and row[output_col] is not None:
            result_df.loc[idx, output_col] = row[output_col]

# === CORE SEGMENTATION FUNCTIONS ===
async def process_single_category(category_df: pd.DataFrame, category: str, 
                          input_col: str, output_col: str) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """
    Process segmentation for a single category using batch processing and taxonomy consolidation.
    
    Args:
        category_df: DataFrame containing products from a single category
        category: Category name for context and logging
        input_col: Column name containing product descriptions
        output_col: Column name for storing category assignments
    
    Returns:
        Tuple of (DataFrame with assignments, refined consolidated taxonomy)
        
    Data Contract:
        - Output DataFrame[output_col] contains clean category names (no prefixes)
        - Refined taxonomy contains only non-empty categories
        - All assignments are guaranteed to be valid category names
    """
    if len(category_df) == 0:
        print(f"No products found for category '{category}', skipping...")
        return category_df, {}
    
    print_category_summary(category, len(category_df))
    
    # Create working dataframe
    work_df = category_df.copy()
    
    # Add random groups for batch sampling
    df_with_groups = add_random_groups(work_df, seed=DEFAULT_SEED)
    
    # Create batches
    batches, index_mappings = make_batches(df_with_groups)
    
    # Phase 1: Extract taxonomies from all batches concurrently
    print(f"\n🔍 Phase 1: Extracting taxonomies from {len(batches)} batches concurrently...")
    start_time = time.time()
    
    batch_tasks = []
    for seed, (batch, batch_mapping) in enumerate(zip(batches, index_mappings)):
        batch_id = seed + 1
        task = run_batch(batch, batch_mapping, batch_id, input_col, product_category=category, max_tries=DEFAULT_MAX_RETRIES)
        batch_tasks.append(task)
    
    # Wait for all batch taxonomy extraction to complete
    batch_taxonomies = await asyncio.gather(*batch_tasks)
    extraction_time = time.time() - start_time
    print(f"✓ All {len(batches)} taxonomies extracted concurrently in {extraction_time:.1f}s")
    
    # Phase 2: Consolidate all taxonomies at once
    print(f"\n🔄 Phase 2: Consolidating {len(batch_taxonomies)} taxonomies...")
    consolidation_start = time.time()
    
    if len(batch_taxonomies) == 1:
        # Single batch case
        consolidated_taxonomy = batch_taxonomies[0]
        all_product_assignments = {}
        for category_name, category_info in consolidated_taxonomy.items():
            for product_id in category_info["product_ids"]:
                all_product_assignments[product_id] = category_name
    else:
        # Multiple batches - consolidate all at once
        consolidated_taxonomy = await consolidate_all_taxonomies(batch_taxonomies, category)
        
        # Create product assignments from final consolidated taxonomy
        all_product_assignments = {}
        for category_name, category_info in consolidated_taxonomy.items():
            for product_id in category_info["product_ids"]:
                all_product_assignments[product_id] = category_name
    
    consolidation_time = time.time() - consolidation_start
    print(f"✓ Consolidation complete in {consolidation_time:.1f}s - {len(consolidated_taxonomy)} final categories")
    
    # Create result dataframe for this category
    category_result = category_df.copy()
    category_result[output_col] = None
    
    # Map products to their final consolidated categories
    for product_id, final_category in all_product_assignments.items():
        category_result.loc[product_id, output_col] = final_category
    
    # Phase 3: Refinement
    if consolidated_taxonomy:
        print(f"\n🎯 Phase 3: Refining assignments for category '{category}' with {len(consolidated_taxonomy)} subcategories...")
        refinement_start = time.time()
        
        # Perform refinement on this category's results
        refined_category_result, refined_taxonomy = await refine_product_assignments(
            df=category_result,
            consolidated_taxonomy=consolidated_taxonomy,
            input_col=input_col,
            output_col=output_col,
            category_prefix=category,
            max_tries=DEFAULT_MAX_RETRIES
        )
        
        refinement_time = time.time() - refinement_start
        print(f"✓ Refinement complete in {refinement_time:.1f}s")
        
        # Print phase summary
        total_time = extraction_time + consolidation_time + refinement_time
        print(f"\n📊 Category '{category}' processing summary:")
        print(f"   Phase 1 (Extraction): {extraction_time:.1f}s")
        print(f"   Phase 2 (Consolidation): {consolidation_time:.1f}s") 
        print(f"   Phase 3 (Refinement): {refinement_time:.1f}s")
        print(f"   Total: {total_time:.1f}s")
        
        return refined_category_result, refined_taxonomy
    else:
        print(f"No subcategories found for category '{category}', skipping refinement")
        return category_result, consolidated_taxonomy

async def segment_products(df: pd.DataFrame, input_col: str, output_col: str, 
                    product_category: Optional[str] = None, input_file_path: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """
    Segment products in a dataframe into categories using AI-powered taxonomy generation and refinement.
    
    Args:
        df: Input dataframe containing products to segment
        input_col: Column name containing product titles/descriptions to segment
        output_col: Column name where assigned categories will be stored
        product_category: Category context for segmentation (auto-detected if None)
        input_file_path: Path to input file for caching (optional)
    
    Returns:
        Tuple of (dataframe with category assignments, consolidated taxonomy dictionary)
        
    Data Contract:
        - Input df[input_col] must contain product descriptions/titles
        - Output df[output_col] will contain clean category names (no prefixes)
        - Consolidated taxonomy maps category names to product lists and definitions
        - All category assignments are guaranteed to be valid (no null/unknown values)
    """
    print(f"Segmenting {len(df)} products from column '{input_col}'...")
    
    # Validate input
    if input_col not in df.columns:
        raise ValueError(f"Input column '{input_col}' not found in dataframe")
    
    # Create processing parameters for caching
    processing_params = {
        "input_col": input_col,
        "output_col": output_col,
        "product_category": product_category,
        "total_products": len(df),
        "model_name": MODEL_NAME,
        "temperature": MODEL_TEMPERATURE,
        "batch_size": DEFAULT_BATCH_SIZE,
        "seed": DEFAULT_SEED,
        "max_retries": DEFAULT_MAX_RETRIES
    }
    
    # Check for cached results if input file path provided
    if input_file_path:
        cached_results = load_result_cache(input_file_path, processing_params, "segmentation")
        if cached_results:
            print("✓ Using cached segmentation results")
            return cached_results
    
    # Get unique categories to process
    if product_category is None:
        unique_categories = get_unique_categories(df)
    else:
        unique_categories = [product_category]
        print(f"Using specified product category: {product_category}")
    
    # Initialize result dataframe
    result_df = df.copy()
    result_df[output_col] = None
    
    # Track all consolidated taxonomies
    all_consolidated_taxonomies = {}
    
    # Process each category separately
    for category in unique_categories:
        # Filter data for this category
        category_df = filter_data_by_category(df, category)
        
        if len(category_df) == 0:
            continue
        
        # Process this category
        category_result, category_taxonomy = await process_single_category(   
            category_df, category, input_col, output_col
        )
        
        # Store the consolidated taxonomy for this category
        all_consolidated_taxonomies[category] = category_taxonomy
        
        # Update the main result dataframe with this category's results
        update_result_dataframe(result_df, category_result, category, output_col)
    
    # Print final summary
    print_final_summary(result_df, output_col)
    
    # Save results to cache if input file path provided
    if input_file_path:
        save_result_cache(result_df, all_consolidated_taxonomies, input_file_path, processing_params, "segmentation")
    
    return result_df, all_consolidated_taxonomies

# === PRODUCT ID RESOLUTION ===
def resolve_category_ids_to_products(consolidated_category_mapping: Dict[str, Dict[str, Any]], 
                                    taxonomy_a: Dict[str, Dict[str, Any]], 
                                    taxonomy_b: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Dict[int, str]]:
    """
    Convert consolidated category ID mapping back to product IDs
    
    Args:
        consolidated_category_mapping: {new_category: {"definition": "...", "ids": [A_0, A_1, B_0, ...]}}
        taxonomy_a: {category_name: {"definition": "...", "product_ids": [...], "product_inputs": [...]}} - existing consolidated taxonomy
        taxonomy_b: {category_name: {"definition": "...", "product_ids": [...], "product_inputs": [...]}} - new batch taxonomy
    
    Returns:
        new_taxonomy: {new_category: {"definition": "...", "product_ids": [...], "product_inputs": [...]}}
        product_assignments: {product_id: new_category}
    """
    # Create ordered lists for deterministic ID→category mapping
    taxonomy_a_categories = list(taxonomy_a.keys())
    taxonomy_b_categories = list(taxonomy_b.keys())
    
    new_taxonomy = {}
    product_assignments = {}
    
    for new_category_name, category_data in consolidated_category_mapping.items():
        # Extract IDs from new schema
        if not isinstance(category_data, dict):
            raise ValueError(f"Consolidated category '{new_category_name}' must be an object with 'definition' and 'ids' fields, got {type(category_data)}")
        
        if "ids" not in category_data:
            raise ValueError(f"Consolidated category '{new_category_name}' missing required 'ids' field")
            
        category_ids = category_data["ids"]
        combined_product_ids = []
        combined_product_inputs = []
        
        for category_id in category_ids:
            if category_id.startswith("A_"):
                # Extract index: A_0 → 0, A_1 → 1, etc.
                index = int(category_id.split("_")[1])
                if index < len(taxonomy_a_categories):
                    source_category = taxonomy_a_categories[index]
                    category_info = taxonomy_a[source_category]
                    combined_product_ids.extend(category_info["product_ids"])
                    combined_product_inputs.extend(category_info["product_inputs"])
                    
            elif category_id.startswith("B_"):
                # Extract index: B_0 → 0, B_1 → 1, etc.
                index = int(category_id.split("_")[1])
                if index < len(taxonomy_b_categories):
                    source_category = taxonomy_b_categories[index]
                    category_info = taxonomy_b[source_category]
                    combined_product_ids.extend(category_info["product_ids"])
                    combined_product_inputs.extend(category_info["product_inputs"])
        
        consolidated_definition = category_data["definition"]
        
        # Store the final mapping
        new_taxonomy[new_category_name] = {
            "definition": consolidated_definition,
            "product_ids": combined_product_ids,
            "product_inputs": combined_product_inputs
        }
        
        # Track where each product ended up
        for product_id in combined_product_ids:
            product_assignments[product_id] = new_category_name
    
    return new_taxonomy, product_assignments
# === MULTI-TAXONOMY CONSOLIDATION ===
async def consolidate_all_taxonomies(batch_taxonomies: List[Dict[str, Dict[str, Any]]], 
                                   category_context: str) -> Dict[str, Dict[str, Any]]:
    """
    Consolidate multiple batch taxonomies into a single coherent taxonomy.
    
    Args:
        batch_taxonomies: List of taxonomies from different batches
        category_context: Category context for logging
    
    Returns:
        Single consolidated taxonomy combining all input taxonomies
        
    Data Contract:
        - Input taxonomies have schema: {category_name: {"definition": str, "product_ids": List[int], "product_inputs": List[str]}}
        - Returns consolidated taxonomy with same schema
        - OUT_OF_SCOPE categories are handled separately and combined at the end
    """
    print(f"Consolidating {len(batch_taxonomies)} taxonomies for category '{category_context}'...")
    
    if len(batch_taxonomies) == 0:
        return {}
    
    if len(batch_taxonomies) == 1:
        return batch_taxonomies[0]
    
    # Extract OUT_OF_SCOPE from all taxonomies
    out_of_scope_items = []
    filtered_taxonomies = []
    
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
            combined_out_of_scope = combine_out_of_scope_items(out_of_scope_items)
            return {"OUT_OF_SCOPE": combined_out_of_scope}
        return {}
    
    # Build consolidated taxonomy by merging taxonomies pairwise
    consolidated = filtered_taxonomies[0]
    
    for i in range(1, len(filtered_taxonomies)):
        next_taxonomy = filtered_taxonomies[i]
        print(f"Consolidating taxonomy {i+1}/{len(filtered_taxonomies)}...")
        
        # Use existing pairwise consolidation function
        local_category_id_map = {}
        consolidated_structure = await consolidate_taxonomies(
            taxonomy_a=consolidated,
            taxonomy_b=next_taxonomy,
            category_id_map=local_category_id_map,
            max_tries=DEFAULT_MAX_RETRIES
        )
        
        # Convert back to product assignments
        consolidated = resolve_consolidated_structure_to_taxonomy(
            consolidated_structure, consolidated, next_taxonomy
        )
    
    # Add back combined OUT_OF_SCOPE if exists
    if out_of_scope_items:
        combined_out_of_scope = combine_out_of_scope_items(out_of_scope_items)
        consolidated["OUT_OF_SCOPE"] = combined_out_of_scope
    
    print(f"✓ Final consolidated taxonomy: {len(consolidated)} categories")
    return consolidated

def combine_out_of_scope_items(out_of_scope_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine multiple OUT_OF_SCOPE category items into one"""
    combined_product_ids = []
    combined_product_inputs = []
    
    for item in out_of_scope_items:
        combined_product_ids.extend(item["product_ids"])
        combined_product_inputs.extend(item["product_inputs"])
    
    return {
        "definition": "Products that do not belong to the specified product category",
        "product_ids": combined_product_ids,
        "product_inputs": combined_product_inputs
    }

def resolve_consolidated_structure_to_taxonomy(consolidated_structure: Dict[str, Dict[str, Any]], 
                                             taxonomy_a: Dict[str, Dict[str, Any]], 
                                             taxonomy_b: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Convert consolidated category structure back to taxonomy format"""
    new_taxonomy, _ = resolve_category_ids_to_products(
        consolidated_structure, taxonomy_a, taxonomy_b
    )
    return new_taxonomy

# === REFINEMENT FUNCTIONS ===
def parse_and_validate_refinement_response(response_text: str, batch_product_ids: set,
                                         valid_subcategory_ids: set) -> Tuple[bool, Any]:
    """
    Parse and validate refinement response for product reassignments.
    
    Args:
        response_text: Raw LLM response text
        batch_product_ids: Set of valid product IDs in current batch (P_0, P_1, ...)
        valid_subcategory_ids: Set of valid subcategory IDs (S_0, S_1, ...)
    
    Returns:
        Tuple of (is_valid: bool, result: Dict or structured_retry_context)
        
    Data Contract:
        - On success: returns (True, reassignments_dict) where reassignments_dict = {"P_0": "S_1", ...}
        - On failure: returns (False, standardized_retry_context)
        - Empty reassignments_dict ({}) is valid (means no changes needed)
        - batch_product_ids format: {"P_0", "P_1", ...}, valid_subcategory_ids format: {"S_0", "S_1", ...}
        - retry_context follows create_retry_context() format
    """
    try:
        json_text = extract_json_from_response(response_text)
        reassignments = json.loads(json_text)
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
    
    if not isinstance(reassignments, dict):
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
    
    # Empty JSON is valid - means no products need reassignment
    if len(reassignments) == 0:
        print("  No products need reassignment in this batch")
        return True, {}
    
    validation_errors = []
    found_product_ids = set()
    duplicate_products = []
    
    for product_id, subcategory_id in reassignments.items():
        if not isinstance(product_id, str) or not product_id.startswith("P_"):
            validation_errors.append(f"Invalid product ID format '{product_id}' - must be P_0, P_1, etc.")
            continue
            
        if product_id not in batch_product_ids:
            validation_errors.append(f"Product ID '{product_id}' not in current batch")
            continue
            
        if not isinstance(subcategory_id, str) or not subcategory_id.startswith("S_"):
            validation_errors.append(f"Invalid subcategory ID format '{subcategory_id}' - must be S_0, S_1, etc.")
            continue
            
        if subcategory_id not in valid_subcategory_ids:
            validation_errors.append(f"Unknown subcategory ID '{subcategory_id}' - must be one of {sorted(valid_subcategory_ids)}")
            
        if product_id in found_product_ids:
            duplicate_products.append(product_id)
        else:
            found_product_ids.add(product_id)
    
    # Check for extra products
    extra_products = found_product_ids - batch_product_ids
    
    # Categorize errors
    error_categories = {
        "format_errors": [],
        "validation_errors": validation_errors,
        "completeness_errors": []
    }
    
    if duplicate_products:
        error_categories["completeness_errors"].append(f"Duplicate product IDs found: {sorted(duplicate_products)}")
    if extra_products:
        error_categories["completeness_errors"].append(f"Extra product IDs not in current batch: {sorted(extra_products)}")
    
    all_errors = error_categories["format_errors"] + error_categories["validation_errors"] + error_categories["completeness_errors"]
    
    if not all_errors:
        return True, reassignments
    
    # Build content sections for retry
    content_sections = {}
    
    if json_text:
        content_sections["previous_json"] = {
            "title": "YOUR PREVIOUS JSON ATTEMPT",
            "content": json_text
        }
    
    content_sections["valid_product_ids"] = {
        "title": "VALID PRODUCT IDs FOR THIS BATCH",
        "content": str(sorted(batch_product_ids))
    }
    
    content_sections["valid_subcategory_ids"] = {
        "title": "VALID SUBCATEGORY IDs",
        "content": str(sorted(valid_subcategory_ids))
    }
    
    retry_context = create_retry_context(
        error_categories=error_categories,
        content_sections=content_sections
    )
    
    return False, retry_context

def build_subcategories_section(consolidated_taxonomy: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """Build reusable subcategories section with mappings"""
    
    # Create subcategory mapping with IDs
    subcategory_to_id = {}
    id_to_subcategory = {}
    subcategory_definitions = {}
    
    subcategory_counter = 0
    for category_name, category_info in consolidated_taxonomy.items():
        subcategory_id = f"S_{subcategory_counter}"
        subcategory_to_id[category_name] = subcategory_id
        id_to_subcategory[subcategory_id] = category_name
        subcategory_counter += 1
        
        # Use stored definition and sample products
        definition = category_info["definition"]
        
        subcategory_definitions[subcategory_id] = {
            "name": category_name,
            "definition": definition
        }
    
    # Build subcategories section
    subcategories_section = "**SUBCATEGORIES:**\n"
    for subcat_id in sorted(subcategory_definitions.keys()):
        subcat_info = subcategory_definitions[subcat_id]
        subcategories_section += f"[{subcat_id}] {subcat_info['name']}: {subcat_info['definition']}\n"
    
    return subcategories_section, subcategory_to_id, id_to_subcategory

def build_products_batch_section(batch_df: pd.DataFrame, batch_mapping: List[int], input_col: str, output_col: str, 
                                subcategory_to_id: Dict[str, str], start_idx: int = 0) -> Tuple[str, Dict[str, int]]:
    """
    Build products section for refinement batch with current assignments.
    
    Args:
        batch_df: DataFrame containing products to process (with sequential indices 0, 1, 2...)
        batch_mapping: List mapping batch positions to original DataFrame indices
        input_col: Column name containing product descriptions
        output_col: Column name containing current category assignments (must be valid category names)
        subcategory_to_id: Mapping from category names to subcategory IDs (S_0, S_1, etc.)
        start_idx: Starting index for product IDs
    
    Returns:
        Tuple of (formatted products section string, mapping from product_id to original dataframe index)
        
    Data Contract:
        - All products in batch_df[output_col] must have valid category assignments
        - Category names must exist in subcategory_to_id mapping
        - No UNKNOWN or invalid assignments allowed
    """
    products_section = "\n**PRODUCTS WITH CURRENT ASSIGNMENTS:**\n"
    id_to_product = {}
    
    product_counter = start_idx
    for batch_pos, row in batch_df.iterrows():
        if pd.notna(row[output_col]):
            product_id = f"P_{product_counter}"
            current_category = row[output_col]
            current_subcategory_id = subcategory_to_id[current_category]
            # Map to original DataFrame index
            original_idx = batch_mapping[batch_pos]
            id_to_product[product_id] = original_idx
            
            products_section += f"[{product_id}] {row[input_col]} → {current_subcategory_id} ({current_category})\n"
            product_counter += 1
    
    return products_section, id_to_product

async def refine_product_assignments(df: pd.DataFrame, consolidated_taxonomy: Dict[str, Dict[str, Any]], 
                              input_col: str, output_col: str, category_prefix: str = "", max_tries: int = DEFAULT_MAX_RETRIES) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """
    Refine product assignments by allowing reassignment to better-matching subcategories using batched processing.
    
    Args:
        df: DataFrame containing products with current assignments
        consolidated_taxonomy: Taxonomy structure with category definitions and product assignments
        input_col: Column name containing product descriptions
        output_col: Column name containing current category assignments (clean category names only)
        category_prefix: Prefix for file naming (e.g., "Electronics", "Dimmer_Switches") 
        max_tries: Maximum retry attempts per batch
    
    Returns:
        Tuple of (refined DataFrame, updated taxonomy with empty categories removed)
        
    Data Contract:
        - Input df[output_col] must contain only clean category names (no prefixes)
        - All category names must exist in consolidated_taxonomy keys
        - Output df[output_col] will contain clean category names
        - Returned taxonomy contains only categories with assigned products
    """
    print(f"\n{'='*60}")
    print("Starting assignment refinement...")
    print(f"{'='*60}")
    
    # Save original taxonomy
    original_taxonomy_path = OUTPUT_ROOT_DIR / f"original_taxonomy_{category_prefix.replace(':', '_')}.json"
    original_taxonomy_path.parent.mkdir(parents=True, exist_ok=True)
    with open(original_taxonomy_path, 'w', encoding='utf-8') as f:
        json.dump(consolidated_taxonomy, f, indent=2, ensure_ascii=False)
    print(f"📝 Saved original taxonomy to {original_taxonomy_path}")
    
    # Build reusable subcategories section
    subcategories_section, subcategory_to_id, id_to_subcategory = build_subcategories_section(consolidated_taxonomy)
    valid_subcategory_ids = set(id_to_subcategory.keys())
    
    print(f"Refining assignments for {len(df)} products across {len(valid_subcategory_ids)} subcategories...")
    
    # Create batches for processing (sample products to reduce LLM load)
    products_with_assignments = df[df[output_col].notna()].copy()
      
    batches, index_mappings = make_batches(products_with_assignments)
    
    refined_df = df.copy()
    refined_taxonomy = {k: {"definition": v["definition"], "product_ids": [], "product_inputs": []} 
                       for k, v in consolidated_taxonomy.items()}
    
    print(f"Processing {len(batches)} refinement batches concurrently...")
    
    # Prepare batch tasks with all necessary data
    refinement_tasks = []
    product_counter = 0
    
    for batch_idx, (batch_df, batch_mapping) in enumerate(zip(batches, index_mappings)):
        if len(batch_df) == 0:
            continue
            
        # Build products section for this batch with unique IDs
        products_section, id_to_product = build_products_batch_section(
            batch_df, batch_mapping, input_col, output_col, subcategory_to_id, start_idx=product_counter
        )
        
        product_counter += len([idx for idx, row in batch_df.iterrows() if pd.notna(row[output_col])])
        
        batch_product_ids = set(id_to_product.keys())
        full_prompt = REFINE_ASSIGNMENTS_PROMPT + "\n\n" + subcategories_section + products_section
        
        # Create task for this batch
        task = process_refinement_batch(
            full_prompt, batch_product_ids, valid_subcategory_ids, id_to_product, 
            id_to_subcategory, refined_df, output_col, batch_idx, max_tries,
            subcategories_section, products_section
        )
        refinement_tasks.append(task)
    
    # Process all refinement batches concurrently
    if refinement_tasks:
        batch_changes_list = await asyncio.gather(*refinement_tasks)
        total_changes = sum(batch_changes_list)
        print(f"✓ All {len(refinement_tasks)} refinement batches processed concurrently")
    else:
        total_changes = 0
    
    # Rebuild the refined taxonomy based on final assignments
    print("Rebuilding taxonomy based on refined assignments...")
    for idx, row in refined_df.iterrows():
        if pd.notna(row[output_col]):
            category_name = row[output_col]
            
            if category_name not in refined_taxonomy:
                raise ValueError(f"Invalid category assignment '{category_name}' found at index {idx}. "
                               f"Valid categories: {list(refined_taxonomy.keys())}")
            
            product_input = row[input_col]
            refined_taxonomy[category_name]["product_ids"].append(idx)
            refined_taxonomy[category_name]["product_inputs"].append(product_input)
    
    # Remove empty categories
    non_empty_taxonomy = {k: v for k, v in refined_taxonomy.items() if len(v["product_ids"]) > 0}
    empty_categories = set(refined_taxonomy.keys()) - set(non_empty_taxonomy.keys())
    
    if empty_categories:
        print(f"Removed {len(empty_categories)} empty categories: {list(empty_categories)}")
    
    # Save refined taxonomy
    refined_taxonomy_path = OUTPUT_ROOT_DIR / f"refined_taxonomy_{category_prefix.replace(':', '_')}.json"
    with open(refined_taxonomy_path, 'w', encoding='utf-8') as f:
        json.dump(non_empty_taxonomy, f, indent=2, ensure_ascii=False)
    print(f"📝 Saved refined taxonomy to {refined_taxonomy_path}")
    
    print(f"✓ Refinement complete: {total_changes} products reassigned across all batches")
    print(f"✓ Final taxonomy: {len(non_empty_taxonomy)} categories (removed {len(empty_categories)} empty)")
    
    return refined_df, non_empty_taxonomy

async def process_refinement_batch(full_prompt: str, batch_product_ids: set, valid_subcategory_ids: set,
                           id_to_product: Dict[str, int], id_to_subcategory: Dict[str, str],
                           refined_df: pd.DataFrame, output_col: str, batch_idx: int, max_tries: int,
                           subcategories_section: str, products_section: str) -> int:
    """
    Process a single refinement batch with unified retry logic and return number of changes made.
    
    Args:
        full_prompt: Complete prompt for LLM refinement
        batch_product_ids: Set of valid product IDs in this batch (P_0, P_1, ...)
        valid_subcategory_ids: Set of valid subcategory IDs (S_0, S_1, ...)
        id_to_product: Mapping from product IDs to original DataFrame indices
        id_to_subcategory: Mapping from subcategory IDs to clean category names
        refined_df: DataFrame to update with refined assignments
        output_col: Column name for category assignments
        batch_idx: Batch index for logging
        max_tries: Maximum retry attempts
        subcategories_section: Section with subcategory definitions
        products_section: Section with product listings
    
    Returns:
        Number of product reassignments made
        
    Data Contract:
        - batch_product_ids format: {"P_0", "P_1", ...}
        - valid_subcategory_ids format: {"S_0", "S_1", ...}
        - id_to_subcategory values must be clean category names (no prefixes)
        - Updates refined_df[output_col] with clean category names only
        - Uses unified retry system on validation failures
        - Empty reassignments ({}) are valid (no changes needed)
        
    Raises:
        RuntimeError: If LLM fails to process refinements after max_tries
    """
    # Create base prompt for caching
    base_prompt = REFINE_ASSIGNMENTS_PROMPT + "\n\n" + subcategories_section + products_section
    prompt = full_prompt
    
    # Create cache context for refinement
    current_assignments = {}
    for product_id in batch_product_ids:
        original_idx = id_to_product[product_id]
        current_assignments[product_id] = refined_df.loc[original_idx, output_col]
    
    cache_context = {
        "batch_product_ids": sorted(list(batch_product_ids)),
        "valid_subcategory_ids": sorted(list(valid_subcategory_ids)),
        "current_assignments": current_assignments,
        "id_to_subcategory": id_to_subcategory,
        "batch_idx": batch_idx
    }
    
    # Check cache first using base prompt
    cached_response = load_llm_cache(prompt, cache_context, "refine_assignments", base_prompt=base_prompt)
    if cached_response:
        print(f"✓ Using cached refinement result for batch {batch_idx + 1}")
        # Cached responses are already validated, parse directly
        json_text = extract_json_from_response(cached_response)
        reassignments = json.loads(json_text)
        changes_made = 0
        
        # Apply cached reassignments to dataframe
        for product_id, new_subcategory_id in reassignments.items():
            original_idx = id_to_product[product_id]
            new_category_name = id_to_subcategory[new_subcategory_id]
            old_category_name = refined_df.loc[original_idx, output_col]
            
            if old_category_name != new_category_name:
                refined_df.loc[original_idx, output_col] = new_category_name
                changes_made += 1
                print(f"    Reassigned {product_id} from '{old_category_name}' to '{new_category_name}'")
        
        return changes_made
    
    for attempt in range(max_tries):
        print(f"  Refinement attempt {attempt + 1}...")
        
        response_text = await safe_llm_call(prompt)
        
        save_llm_interaction(
            prompt=prompt,
            response=response_text,
            interaction_type="refine_assignments",
            batch_id=batch_idx + 1,
            attempt=attempt + 1
        )
        
        is_valid, result = parse_and_validate_refinement_response(
            response_text, batch_product_ids, valid_subcategory_ids
        )
        
        if is_valid:
            reassignments = result
            
            # Save successful response to cache using base prompt
            save_llm_cache(
                prompt=prompt,
                response=response_text,
                interaction_type="refine_assignments",
                context=cache_context,
                batch_id=batch_idx + 1,
                base_prompt=base_prompt
            )
            
            changes_made = 0
            
            # Apply reassignments to dataframe
            for product_id, new_subcategory_id in reassignments.items():
                original_idx = id_to_product[product_id]
                new_category_name = id_to_subcategory[new_subcategory_id]
                old_category_name = refined_df.loc[original_idx, output_col]
                
                if old_category_name != new_category_name:
                    refined_df.loc[original_idx, output_col] = new_category_name
                    changes_made += 1
                    print(f"    Reassigned {product_id} from '{old_category_name}' to '{new_category_name}'")
            
            print(f"  ✓ Batch {batch_idx + 1} complete: {changes_made} products reassigned")
            return changes_made
        
        print(f"  ✗ Batch {batch_idx + 1} attempt {attempt + 1} failed, retrying...")
        print(f"    Issues: {result['issues_summary']}")
        
        # Use unified retry prompt builder  
        retry_prompt = build_retry_prompt(
            original_prompt=base_prompt,
            retry_context=result
        )
        
        prompt = retry_prompt


    
    print(f"  ⚠ Batch {batch_idx + 1} failed after maximum retries")
    return 0

# === MAIN EXECUTION ===
async def main() -> None:
    """Main execution function with async optimization tracking"""    
    try:
        print(f"Loading data from {DEFAULT_CSV_PATH}...")
        df = load_data(DEFAULT_CSV_PATH)
        
        # Run segmentation with async optimization and result caching
        result_df, all_consolidated_taxonomies = await segment_products(
            df=df,
            input_col="cleaned_title",  # Column containing product titles/descriptions
            output_col="product_segment",  # Column where categories will be assigned
            product_category=None,  # Process all categories
            input_file_path=str(DEFAULT_CSV_PATH)  # Enable result caching
        )
        
        # Save final results (refinement already performed within each category)
        print(f"\nSaving final results to {FINAL_OUTPUT_PATH}...")
        FINAL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(FINAL_OUTPUT_PATH, index=False)
        print("✓ Final refined taxonomy saved!")
        
        print("✓ Processing complete!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please make sure the file exists and the path is correct.")
        exit(1)
    except Exception as e:
        print(f"Error during segmentation: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
