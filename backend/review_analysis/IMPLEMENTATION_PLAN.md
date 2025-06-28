# Review Analysis Module Implementation Plan

## Overview
This plan implements a review analysis module that extracts fine-grained customer feedback from reviews and categorizes them using the existing `@backend/core/llm_taxonomy_pipeline/` architecture. The implementation will reuse existing patterns from `@backend/product_segment/` while adapting them for review analysis needs.

## Architecture Analysis

### Existing Components to Reuse
1. **Core LLM Taxonomy Pipeline** (`backend/core/llm_taxonomy_pipeline/`)
   - `pipeline_stage.py` - Base stage interface
   - `extraction_base.py` - Base extraction stage
   - `consolidation_base.py` - Base consolidation stage  
   - `refinement_base.py` - Base refinement stage

2. **Product Segment Implementation** (`backend/product_segment/llm/`)
   - `extraction_stage.py` - Product taxonomy extraction
   - `consolidation_stage.py` - Multi-batch consolidation
   - `refinement_stage.py` - Final assignment to categories
   - `taxonomy_dedup_util.py` - Deduplication utilities

3. **Validation and Retry System**
   - Unified retry context creation
   - Structured error categorization
   - Shared retry prompt templates

## Key Differences: Product Segment vs Review Analysis

| Aspect | Product Segment | Review Analysis |
|--------|----------------|-----------------|
| **Input** | Product titles | Product reviews (multiple per product) |
| **Extraction Target** | Product categories | Review aspects (phy/perf/use with sentiment) |
| **Validation** | Simple category assignment | Complex hierarchical structure validation |
| **ID Format** | Simple incremental IDs | Structured IDs (PID: A,B,C..., perf_id: a,b,c...) |
| **Deduplication** | Basic text similarity | Multi-level: aspects within products, across products |
| **Output Structure** | Flat category assignments | Hierarchical: phy/perf/use → categories → aspects → sentiments |

## Implementation Plan

### Phase 1: Core Review Analysis Stages

#### 1.1 Review Extraction Stage (`backend/review_analysis/llm/extraction_stage.py`)
- **Purpose**: Extract review aspects from raw review text
- **Input**: Product reviews (formatted as `{review_id}#{review_text}`)
- **Output**: Hierarchical structure (phy/perf/use sections)
- **Validation**: Complex structure validation with sentiment and ID format rules
- **Reuses**: `ExtractionBase` from core pipeline

#### 1.2 Review Categorization Stage (`backend/review_analysis/llm/categorization_stage.py`)
- **Purpose**: Categorize extracted aspects into meaningful groups
- **Input**: Deduplicated aspects from extraction
- **Output**: Aspect categories with definitions
- **Reuses**: Similar pattern to product segment extraction but for aspects

#### 1.3 Review Consolidation Stage (`backend/review_analysis/llm/consolidation_stage.py`)
- **Purpose**: Merge categories from multiple batches
- **Input**: Multiple category taxonomies
- **Output**: Unified category taxonomy
- **Reuses**: `ConsolidationBase` from core pipeline

#### 1.4 Review Refinement Stage (`backend/review_analysis/llm/refinement_stage.py`)
- **Purpose**: Final assignment of aspects to consolidated categories
- **Input**: Aspects + consolidated categories
- **Output**: Final aspect-to-category mappings
- **Reuses**: `RefinementBase` from core pipeline

### Phase 2: Review-Specific Utilities

#### 2.1 Review Validation System (`backend/review_analysis/llm/validation.py`)
- **Purpose**: Validate complex review analysis structures
- **Features**:
  - ID format validation (PID: A,B,C..., perf_id: a,b,c...)
  - Sentiment validation (+/-)
  - Review ID reference validation
  - Hierarchical structure validation
- **Reuses**: Retry context system from legacy code

#### 2.2 Review Deduplication Utilities (`backend/review_analysis/llm/dedup_util.py`)
- **Purpose**: Deduplicate aspects across products and within products
- **Features**:
  - Aspect similarity detection
  - Cross-product deduplication
  - Aspect mapping maintenance
- **Reuses**: Deduplication patterns from product segment

### Phase 3: Integration Components

#### 3.1 Review Analysis Service (`backend/review_analysis/services/review_analysis_service.py`)
- **Purpose**: Orchestrate the full review analysis pipeline
- **Features**:
  - Load review data
  - Execute pipeline stages
  - Handle cross-product aggregation
  - Save results

#### 3.2 Review Analysis API (`backend/review_analysis/api.py`)
- **Purpose**: HTTP endpoints for review analysis
- **Endpoints**:
  - `POST /review-analysis/extract` - Extract aspects from reviews
  - `POST /review-analysis/categorize` - Categorize aspects  
  - `GET /review-analysis/results/{run_id}` - Get results
- **Reuses**: API patterns from product segment module

#### 3.3 Database Models (`backend/review_analysis/models.py`)
- **Purpose**: Store review analysis results
- **Tables**:
  - `review_analysis_runs` - Track analysis runs
  - `review_aspect_extractions` - Store extracted aspects
  - `review_aspect_categories` - Store category definitions
  - `review_aspect_assignments` - Store final assignments

## Critical Uncertainties & Questions

### 1. Data Flow Architecture
**Question**: Should we process reviews per-product individually then aggregate, or aggregate all reviews first then process?

**Legacy Approach**: Per-product processing with aggregation
**Considerations**: 
- Per-product: Better for incremental processing, product-specific context
- Aggregated: Better for cross-product pattern detection, more efficient deduplication

**Recommendation**: Start with per-product like legacy, add aggregation option later

### 2. Validation Strategy
**Question**: How strict should validation be for the complex hierarchical review structure?

**Legacy Approach**: Very strict validation with detailed error categorization
**Considerations**:
- Strict: Higher quality, more retries, slower processing
- Lenient: Faster processing, potential quality issues

**Recommendation**: Start strict like legacy, add configurable validation levels

### 3. Deduplication Scope
**Question**: Should we deduplicate aspects within products, across products, or both?

**Legacy Approach**: Across all products globally
**Considerations**:
- Within-product: Simpler, maintains product context
- Cross-product: Better pattern detection, more efficient
- Both: Most comprehensive but complex

**Recommendation**: Implement both with configuration options

### 4. Caching Strategy
**Question**: How should we handle caching for the multi-stage review analysis pipeline?

**Legacy Approach**: Per-LLM-call caching with context-based keys
**Considerations**:
- Stage-level caching: Cache each pipeline stage result
- Call-level caching: Cache individual LLM calls
- Hybrid: Both approaches

**Recommendation**: Start with call-level like legacy, add stage-level for efficiency

### 5. Error Handling
**Question**: How should we handle partial failures in the multi-stage pipeline?

**Legacy Approach**: Fail entire product if any stage fails
**Considerations**:
- Fail-fast: Stop on first error, cleaner but less robust
- Partial success: Continue with available data, more complex but robust
- Retry-all: Retry entire pipeline on any failure

**Recommendation**: Implement partial success with retry options

## Implementation Timeline

### Week 1: Foundation
- [ ] Create base review analysis stages inheriting from core pipeline
- [ ] Implement review-specific validation system
- [ ] Create basic deduplication utilities

### Week 2: Core Functionality  
- [ ] Implement extraction stage with hierarchical validation
- [ ] Implement categorization stage for aspects
- [ ] Add consolidation and refinement stages

### Week 3: Integration
- [ ] Create review analysis service
- [ ] Add database models and repositories
- [ ] Implement API endpoints

### Week 4: Testing & Refinement
- [ ] Test with legacy data formats
- [ ] Performance optimization
- [ ] Documentation and examples

## Success Criteria
1. **Compatibility**: Can process legacy review data formats
2. **Reusability**: Reuses ≥80% of core pipeline patterns
3. **Quality**: Maintains validation strictness of legacy system  
4. **Performance**: Processes reviews efficiently with proper rate limiting
5. **Extensibility**: Easy to add new aspect types or validation rules

## File Structure
```
backend/review_analysis/
├── llm/
│   ├── extraction_stage.py      # Review aspect extraction
│   ├── categorization_stage.py  # Aspect categorization  
│   ├── consolidation_stage.py   # Category consolidation
│   ├── refinement_stage.py      # Final aspect assignment
│   ├── validation.py            # Review-specific validation
│   └── dedup_util.py            # Review deduplication
├── services/
│   └── review_analysis_service.py
├── repositories/
│   ├── review_analysis_run_repository.py
│   ├── review_aspect_extraction_repository.py
│   └── review_aspect_category_repository.py
├── models.py
├── api.py
└── config.py
```