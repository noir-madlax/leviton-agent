# Product Segmentation Engine – Database-Integrated Version

## 1. Module Purpose
`backend/product_segmentation` provides an end-to-end service that:
1. Receives an explicit list of `product_id`s for segmentation
2. Uses LLM to intelligently categorize products into market segments
3. Stores raw LLM interactions as **files** (local disk with future S3 migration)
4. Writes only lightweight indexes and results into Supabase database
5. Supports batch processing with sophisticated retry logic and caching

## 2. Architecture Overview

### 2.1 Storage Strategy
- **LLM Interactions**: Stored as JSON files (local → S3 migration path)
- **Database**: Lightweight indexes, metadata, and final results only
- **Prompts**: Archived once per run for reproducibility

### 2.2 Processing Flow
```
Input: product_ids → 
Batch Processing → 
LLM Segmentation → 
Taxonomy Consolidation → 
Assignment Refinement → 
Database Results
```

### 2.3 Legacy Reference
The advanced prompt-engineering and retry logic were originally prototyped in the
stand-alone script:

`archive/backend-old/src/competitor/segment_products.py`

Whenever a **TODO** below references "original implementation", that file is the
authoritative source for behaviour.

## 3. Directory Structure
```
backend/product_segmentation/
├── __init__.py
├── services/
│   └── db_product_segmentation.py     # Main orchestration service
├── storage/
│   └── interaction_storage.py         # File storage abstraction
├── repositories/
│   ├── llm_interaction_repository.py  # LLM interaction indexing
│   ├── product_segment_repository.py  # Product segment assignments
│   ├── segmentation_run_repository.py # Run tracking and status
│   └── product_taxonomy_repository.py # Taxonomy management
├── prompts/
│   ├── extract_taxonomy_prompt_v0.txt      # Initial categorization
│   ├── consolidate_taxonomy_prompt_v0.txt  # Category merging
│   ├── refine_assignments_prompt_v0.txt    # Assignment refinement
│   └── shared_retry_prompt_v0.txt          # Error recovery
└── README_product_segmentation.md     # This file
```

## 4. LLM Logs Storage Layout
```
llm_logs/
└── RUN_<ISO_TIMESTAMP>_<hash>/
    ├── prompts/                        # Archived prompts (once per run)
    │   ├── extract_taxonomy_prompt.txt
    │   ├── consolidate_taxonomy_prompt.txt
    │   └── refine_assignments_prompt.txt
    ├── segmentation/                   # Initial batch categorization
    │   ├── <ts>_b1_a1_<hash>.json
    │   └── <ts>_b2_a1_<hash>.json
    ├── consolidate_taxonomy/           # Category consolidation
    │   └── <ts>_a1_<hash>.json
    └── refine_assignments/             # Assignment refinement
        ├── <ts>_b1_a1_<hash>.json
        └── <ts>_b2_a1_<hash>.json
```

### 4.1 File Naming Convention
- **Pattern**: `<ISO_timestamp>_<batch_or_category>_<attempt>_<hash>.json`
- **Example**: `20250618T120305Z_b1_a1_f4c2.json`
  - `20250618T120305Z`: ISO timestamp
  - `b1`: batch 1 (or category identifier)
  - `a1`: attempt 1
  - `f4c2`: short hash for uniqueness

### 4.2 JSON File Schema
```json
{
  "metadata": {
    "run_id": "RUN_20250618T120301Z_8d24",
    "interaction_type": "segmentation",
    "batch_id": 1,
    "attempt": 1,
    "model": "gpt-4o",
    "temperature": 0.2,
    "timestamp": "2025-06-18T12:03:05Z",
    "category": "Dimmer Switches",
    "cache_key": "f4c2e6ab",
    "duration_ms": 2345
  },
  "context": {
    "batch_size": 20,
    "expected_ids": [0, 1, 2, ...],
    "product_category": "Electronics",
    "batch_products": ["Product A", "Product B", ...]
  },
  "prompt": "<full prompt string>",
  "response": "<raw LLM response>"
}
```

## 5. Database Schema

### 5.1 Core Tables
```sql
-- Segmentation run tracking
CREATE TABLE segmentation_runs (
    id              VARCHAR(50)  PRIMARY KEY,
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    status          VARCHAR(20)  DEFAULT 'running',  -- 'running'|'completed'|'failed'
    model_config    JSONB,
    processing_params JSONB,
    total_products  INT,
    processed_products INT DEFAULT 0,
    result_summary  JSONB
);

-- Explicit product input list
CREATE TABLE run_products (
    run_id        VARCHAR(50) REFERENCES segmentation_runs(id) ON DELETE CASCADE,
    product_id    BIGINT      REFERENCES amazon_products(id),
    PRIMARY KEY (run_id, product_id)
);

-- Generated taxonomies/categories
CREATE TABLE product_taxonomies (
    id           BIGSERIAL PRIMARY KEY,
    run_id       VARCHAR(50) REFERENCES segmentation_runs(id),
    category_name   VARCHAR(255),
    definition      TEXT,
    product_count   INT DEFAULT 0
);

-- Final product assignments (first-pass)
CREATE TABLE product_segments (
    run_id       VARCHAR(50) REFERENCES segmentation_runs(id),
    product_id   BIGINT      REFERENCES amazon_products(id),
    taxonomy_id  BIGINT      REFERENCES product_taxonomies(id),
    confidence   FLOAT,
    PRIMARY KEY (run_id, product_id)
);

-- *Refined* product assignments (post-LLM refinement)
CREATE TABLE refined_product_segments (
    run_id       VARCHAR(50) REFERENCES segmentation_runs(id),
    product_id   BIGINT      REFERENCES amazon_products(id),
    taxonomy_id  BIGINT      REFERENCES product_taxonomies(id),
    PRIMARY KEY (run_id, product_id)
);

-- LLM interaction file index
CREATE TABLE llm_interaction_index (
    id               BIGSERIAL PRIMARY KEY,
    run_id           VARCHAR(50) REFERENCES segmentation_runs(id),
    interaction_type VARCHAR(50),  -- 'segmentation'|'consolidate_taxonomy'|'refine_assignments'
    batch_id         INT,
    attempt          INT,
    file_path        TEXT,         -- local or S3 URI
    prompt_file      TEXT,         -- path to archived prompt
    cache_key        VARCHAR(32),
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 Data Relationships
- `segmentation_runs` is the root entity
- `run_products` defines input scope
- `product_taxonomies` contains generated categories
- `product_segments` maps products to taxonomies (initial pass)
- `refined_product_segments` stores the post-processing reassignment output
- `llm_interaction_index` points to file storage

## 6. Implementation Plan

### 6.1 Phase 1: Database Foundation  **(✅ Completed)**
- [x] Create database migration scripts for all tables *(001_create_segmentation_tables.sql)*
- [x] Implement repository classes with basic CRUD operations *(segmentation_run_repository.py, product_segment_repository.py, llm_interaction_repository.py)*
- [x] Add database indexes for performance *(completed via Supabase migration)*
- [x] Create basic data models with Pydantic validation *(models.py)*
- [x] Handle JSON field serialization for model_config and processing_params *(added in v4.1)*

### 6.2 Phase 2: File Storage System  **(✅ Completed – local backend)**
- [x] Implement `llm_storage.py` with local/S3 abstraction *(local backend finished; S3 stub ready)*
- [x] Create directory management utilities *(basic deterministic batching implemented)*
- [x] Implement prompt archiving logic *(LLMStorageService.store_prompt)*
- [x] Add file integrity verification *(checksum support completed)*

### 6.3 Phase 3: Core Segmentation Service **(✅ Completed)**
- [x] Implement baseline `DatabaseProductSegmentationService` *(services/db_product_segmentation.py)*
- [x] Implement batch processing with database input & progress tracking
- [x] Port advanced logic into dedicated LLM client *(llm/product_segmentation_client.py)*
- [x] Adapt LLM caching to use file + database hybrid *(file-layer via `utils/cache.py`; **database-indexed retrieval integrated in v3.1**)*
- [x] Add taxonomy consolidation and refinement *(LLM-driven consolidation **and** assignment refinement ported – see `utils.refinement` + updated LLM client)*
- [x] Supersede legacy helpers (`save_llm_cache`, `load_llm_cache`, `save_result_cache`) with unified `LLMCache`/`ResultCache` + DB index
- [x] Implement directory management utilities *(deterministic batching integrated into service)*
- [x] Port performance-oriented helpers (`calculate_optimal_batch_sizes`, async rate-limiter) *(completed in v4.1)*
- [x] Ensure proper order of taxonomy and segment creation *(fixed in v4.1)*

### 6.4 Phase 4: API Integration **(✅ Completed)**
- [x] Create REST endpoints for starting/monitoring runs *(api router added in v4.0)*
- [x] Add progress tracking and status reporting *(`/status` endpoint implemented)*
- [x] Implement result retrieval APIs *(`/results` endpoint implemented)*
- [x] Add error handling and recovery *(completed with database transaction support)*

### 6.5 Phase 5: Test & CI Stabilization  **(✅ Completed)**
The quality-gate phase is finished.  The entire **phase-ordered test-suite** now passes with a single command:

```bash
python -m pytest product_segmentation/tests/ -v -k "not test_db_integration_real"
```

Key accomplishments:

- [x] **Stub-LLM Fixtures** – Introduced deterministic `StubLLM` JSON fixtures removing all brittle free-form text matching.
- [x] **In-Memory Repository Parity** – In-memory fakes now fully mirror the production repositories (run-products, refined segments, taxonomies, progress updates).

CI pipelines can therefore rely on the test-suite as an authoritative regression gate.

## 7. Key Components Detail

### 7.1 DatabaseProductSegmentationService
**File**: `services/db_product_segmentation.py`

Main orchestration service that:
- Creates segmentation runs
- Manages product loading from database
- Coordinates LLM interactions
- Handles result persistence
- **Ensures proper order of taxonomy and segment creation**

### 7.2 InteractionStorage
**File**: `storage/interaction_storage.py`

Storage abstraction that:
- Supports local and S3 backends
- Manages directory structure
- Handles prompt archiving
- Provides migration utilities

### 7.3 Repository Layer
**Files**: `repositories/*.py`

Data access layer with:
- Type-safe database operations
- Error handling and logging
- Transaction management
- Query optimization

### 7.4 ProductSegmentationLLMClient
**File**: `llm/product_segmentation_client.py`

High-level wrapper around the OpenAI client that:
- Builds prompts for segmentation, taxonomy consolidation **and assignment refinement**
- Validates JSON responses with detailed error reporting
- Implements structured retry logic
- Exposes the `SegmentationLLMClient` protocol used by the service layer
- **Requires explicit prompt templates** for keys `extract_taxonomy`, `consolidate_taxonomy`, and `refine_assignments` – no built-in fallbacks.

### 7.5 Taxonomy Utilities
**File**: `utils/taxonomy.py`

Lightweight helpers for:
- Deterministic, name-based merging of batch-level taxonomies (fallback path)

### 7.6 LLMInteractionRepository
**File**: `repositories/llm_interaction_repository.py`

Database helper that:
- Inserts batches of LLM-interaction index rows in a single call
- Retrieves all interactions for a given run (future analytics/UI tooling)
- Mirrors coding style of other repository classes so it can be dependency-injected identically
- Keeps error handling non-throwing; logs and returns booleans/lists so the orchestration layer controls failure policy

### 7.7 Cache Utilities
**File**: `utils/cache.py`

Reusable helpers that:
- Provide `LLMCache` for prompt/response storage and `ResultCache` for generic results.
- Generate deterministic SHA-256 keys to prevent duplicate LLM calls.
- Offer simple factory functions for easy injection (`create_llm_cache`, `create_result_cache`).
- Are now consumed by `ProductSegmentationLLMClient` to skip redundant API calls and by the service layer to persist `cache_key`s in `llm_interaction_index`.

### 7.8 Refinement Utilities
**File**: `utils/refinement.py`

Light-weight helpers extracted from the legacy pipeline that are now used by the LLM client to perform the Phase-3 **assignment refinement** step:
- `build_subcategories_section` – renders consolidated taxonomy with stable `S_i` identifiers.
- `build_products_section` – formats products and their current assignments with `P_i` identifiers.
- `parse_and_validate_refinement_response` – strict JSON validation for reassignment payloads.

These utilities keep prompt-formatting and validation logic isolated from the client, enabling easier unit-testing and future extension.

## 8. Configuration

### 8.1 Environment Variables
```bash
# Storage configuration
STORAGE_BACKEND=local          # local | s3
STORAGE_ROOT=/opt/leviton/llm_logs
S3_BUCKET=leviton-llm-logs
S3_REGION=us-east-1

# LLM configuration
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.2

# Segmentation pipeline configuration
SEGMENTATION_PRODUCTS_PER_PROMPT=40     # Number of products per taxonomy extraction prompt
SEGMENTATION_TAXONOMIES_PER_CONSOLIDATION=20  # Number of taxonomies to consolidate at once
SEGMENTATION_PRODUCTS_PER_REFINEMENT=40  # Number of products per refinement prompt
SEGMENTATION_MAX_RETRIES=3              # Maximum retries for LLM calls
```

### 8.2 Runtime Configuration
Model parameters, processing options, and feature flags are stored in the database as part of each segmentation run for full reproducibility.

## 9. API Specification

### 9.1 Start Segmentation
```http
POST /api/segmentation/start
Content-Type: application/json

{
  "product_ids": [123, 456, 789],
  "category": "Dimmer Switches",
  "model": "gpt-4o",
  "temperature": 0.2
}

Response:
{
  "run_id": "RUN_20250618T120301Z_8d24",
  "status": "started",
  "total_products": 3
}
```

### 9.2 Get Run Status
```http
GET /api/segmentation/{run_id}/status

Response:
{
  "run_id": "RUN_20250618T120301Z_8d24",
  "status": "running",
  "total_products": 100,
  "processed_products": 45,
  "progress_percent": 45.0,
  "estimated_completion": "2025-06-18T12:15:00Z"
}
```

### 9.3 Get Results
```http
GET /api/segmentation/{run_id}/results

Response:
{
  "run_id": "RUN_20250618T120301Z_8d24",
  "status": "completed",
  "taxonomies": [
    {
      "id": 1,
      "category_name": "Smart Dimmer Switches",
      "definition": "WiFi-enabled dimmer switches...",
      "product_count": 25
    }
  ],
  "segments": [
    {
      "product_id": 123,
      "taxonomy_id": 1,
      "confidence": 0.95
    }
  ]
}
```

## 10. Migration Strategy

### 10.1 Local to S3 Migration
```python
# Example migration command
python -m product_segmentation.storage.migrate_to_s3 \
    --run-id RUN_20250618T120301Z_8d24 \
    --verify-integrity
```

Migration process:
1. Upload all files to S3 maintaining directory structure
2. Update `llm_interaction_index` with new S3 paths
3. Verify file integrity with checksums
4. Optionally remove local files after verification

### 10.2 Rollback Support
- Keep local files until S3 migration is verified
- Database rollback updates file paths back to local
- Integrity checks ensure no data loss

## 11. Performance Considerations

### 11.1 Optimization Strategies
- **Concurrent Processing**: Batch LLM calls run in parallel
- **Database Indexing**: Optimized queries for large product sets
- **File Compression**: Optional compression for LLM logs
- **Caching**: Smart cache key generation prevents duplicate work

### 11.2 Scalability
- Horizontal scaling through multiple workers
- S3 storage eliminates local disk constraints
- Database partitioning for large-scale deployments

## 12. Testing Strategy

### 12.1 Unit Tests
- [x] Repository layer with mock database
- [x] Storage abstraction with temporary directories
- [x] Service orchestrator with in-memory fakes *(tests/test_service.py)*
- [x] LLM response parsing and validation *(tests/test_llm_client.py)*
- [x] Error handling and recovery scenarios

### 12.2 Integration Tests
- [ ] End-to-end segmentation runs
- [ ] Database transaction integrity
- [ ] File storage consistency

### 12.3 Local Test Runner
The repository provides a stand-alone runner that executes **all unit tests** without external services:

```bash
python -m backend.product_segmentation.test_runner
```

The script orchestrates phase-ordered test suites:

1. Phase 1 – Model validation
2. Phase 2 – Storage subsystem
3. Phase 2b – Batching utilities
4. Phase 3 – Service orchestrator

Every suite prints a concise summary and the runner exits with a non-zero code on failure, making it suitable for CI pipelines.

## 13. Monitoring and Observability

### 13.1 Logging
- Structured logging for all operations
- Performance metrics collection
- Error tracking and alerting
- Audit trail for all changes

### 13.2 Metrics
- Run completion rates
- Processing time distributions
- LLM token usage
- Storage utilization

## 14. Development Guidelines

### 14.1 Code Standards
- Type hints for all functions
- Comprehensive docstrings
- Error handling with specific exceptions
- Async/await for I/O operations

### 14.2 Testing Requirements
- Minimum 80% code coverage
- Integration tests for all API endpoints
- Performance benchmarks for core operations
- Regression tests for bug fixes

---

This README serves as the implementation blueprint for the product_segmentation module. Keep it updated as the codebase evolves. 