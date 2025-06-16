# LLM Response Caching System Implementation

## Overview
Implemented a comprehensive caching system for LLM responses to avoid redundant API calls and ensure deterministic results.

## Key Features

### 1. Deterministic Random Seeds
- Fixed all random operations to use `DEFAULT_SEED = 42`
- `add_random_groups()` now uses `DEFAULT_SEED` instead of hardcoded `seed=0`
- `make_batches()` uses `random_state=DEFAULT_SEED` for pandas sampling
- Ensures identical batch compositions across runs

### 2. Cache Storage Structure
```
OUTPUT_ROOT_DIR/
├── llm_cache/
│   ├── segmentation_cat_Electronics_batch1_a1b2c3d4_20241225_14.json
│   ├── consolidate_taxonomy_e5f6g7h8_20241225_14.json
│   └── refine_assignments_batch1_i9j0k1l2_20241225_14.json
└── result_cache/
    ├── segmentation_f1a2b3c4_20241225_14.json
    ├── segmentation_f1a2b3c4_20241225_14_results.csv
    └── segmentation_f1a2b3c4_20241225_14_taxonomies.json
```

### 3. Cache Key Generation

#### LLM Cache Keys
- Uses SHA256 hash of prompt + context for unique identification
- Context includes:
  - **Segmentation**: batch_size, product_category, batch_mapping, actual products
  - **Consolidation**: taxonomy categories, expected IDs, taxonomy structures
  - **Refinement**: product IDs, subcategory IDs, current assignments

#### Result Cache Keys
- Uses SHA256 hash of input file stats + processing parameters
- Context includes:
  - **File Stats**: modification time, file size (detects input changes)
  - **Processing Params**: columns, categories, model config, batch size, seed
  - **Model Config**: model name, temperature, retry settings

### 4. Cache File Format

#### LLM Cache Format
```json
{
  "timestamp": "2024-12-25T14:30:45.123456",
  "interaction_type": "segmentation|consolidate_taxonomy|refine_assignments",
  "cache_key": "a1b2c3d4e5f6g7h8",
  "context": { ... },
  "prompt": "...",
  "response": "...",
  "model_name": "claude-sonnet-4-20250514",
  "model_temperature": 0.15,
  "batch_id": 1,
  "category": "Electronics"
}
```

#### Result Cache Format
```json
{
  "timestamp": "2024-12-25T14:30:45.123456",
  "result_type": "segmentation",
  "cache_key": "f1a2b3c4d5e6f7g8",
  "input_file_path": "/path/to/input.csv",
  "processing_params": {
    "input_col": "cleaned_title",
    "output_col": "product_segment",
    "product_category": null,
    "total_products": 1500,
    "model_name": "claude-sonnet-4-20250514",
    "temperature": 0.15,
    "batch_size": 40,
    "seed": 42,
    "max_retries": 3
  },
  "model_config": { ... },
  "result_stats": {
    "total_products": 1500,
    "categories_found": 12,
    "products_with_segments": 1487
  }
}
```

### 5. Cache Lookup Logic
1. Generate cache key from prompt + context
2. Search for matching files by pattern: `{type}_*_{key}_*.json`
3. Verify exact match on key, type, model, prompt, and context
4. Parse cached response directly (no re-validation needed)
5. All cached responses are assumed to be pre-validated

### 6. Integration Points

#### LLM-Level Caching

**run_batch()**
- Caches successful segmentation responses after validation
- Context includes batch products and mappings
- Directly parses and applies cached responses (no re-validation)

**consolidate_taxonomies()**
- Caches successful taxonomy consolidations after validation
- Context includes both input taxonomies
- Directly parses and returns cached results (no re-validation)

**process_refinement_batch()**
- Caches successful refinement decisions after validation
- Context includes current assignments and available categories
- Directly parses and applies cached reassignments (no re-validation)

#### Result-Level Caching

**segment_products()**
- Checks for cached results before any processing
- Saves complete results (DataFrame + taxonomies) after successful processing
- Cache key based on input file stats + processing parameters
- Skips entire pipeline when valid cache exists

## Benefits

### LLM-Level Caching
1. **Performance**: Eliminates redundant LLM calls for identical inputs
2. **Reproducibility**: Deterministic batching ensures consistent cache hits
3. **Debugging**: Full context preservation enables cache inspection
4. **Cost Savings**: Reduces API usage for repeated experiments
5. **Reliability**: Only validated responses are cached, ensuring correctness
6. **Speed**: No re-validation overhead when loading cached responses

### Result-Level Caching
7. **Pipeline Skipping**: Bypasses entire processing pipeline for identical inputs
8. **File Change Detection**: Automatically detects input file modifications
9. **Parameter Tracking**: Ensures cache invalidation when processing parameters change
10. **Complete State Recovery**: Restores both results and taxonomies from cache
11. **Development Efficiency**: Instant results for repeated runs with same parameters

## Cache Management

- Organized by interaction type and category for easy navigation
- Includes timestamps for cache expiration if needed
- Human-readable filenames for debugging
- JSON format enables programmatic analysis
- Preserves full context for exact matching 