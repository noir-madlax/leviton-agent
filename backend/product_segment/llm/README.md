# Product-Segment LLM Pipeline

This package contains the **domain implementation** of the generic LLM-taxonomy
pipeline for the *Product-Segmentation* subsystem.  It plugs concrete prompt
logic and validation rules into the abstract bases from
`backend/core/llm_taxonomy_pipeline/`.

```
product_segment/llm/
├── __init__.py               # re-exports public API
├── prompts/                  # domain prompt templates
│   ├── taxonomy_extraction_prompt_v0.txt
│   ├── taxonomy_consolidation_prompt_v0.txt
│   └── taxonomy_refinement_prompt_v0.txt
├── product_extraction_stage.py       # concrete ProductExtractionStage
├── product_consolidation_stage.py    # concrete ProductConsolidationStage
├── product_refinement_stage.py       # concrete ProductRefinementStage
└── taxonomy_dedup_uitl.py    # stemming-based dedup helper
```

### Stage Classes

The pipeline consists of three main stages:

1. **ProductExtractionStage** (`product_extraction_stage.py`)
   - Converts raw product titles into provisional taxonomies
   - Returns `ProductExtractionStageResult` with taxonomies and initial assignments
   - Uses `ProductExtractionStageContext` for input configuration

2. **ProductConsolidationStage** (`product_consolidation_stage.py`) 
   - Consolidates overlapping taxonomies from multiple batches
   - Returns `ProductConsolidationStageResult` with consolidated taxonomies
   - Uses `ProductConsolidationStageContext` for consolidation parameters

3. **ProductRefinementStage** (`product_refinement_stage.py`)
   - Refines product assignments to better match taxonomy definitions
   - Returns `ProductRefinementStageResult` with reassignment mappings
   - Uses `ProductRefinementStageContext` for refinement configuration

## 4. Deduplication helper
`taxonomy_dedup_uitl.py` normalises names via Porter stemming and collapses
aliases before consolidation – used mainly inside the test-suite.

## 5. Tests
Extensive fixtures live under `product_segment/tests/llm/` covering:
* prompt building,
* validation error categorisation,
* retry prompt generation,
* split-and-merge logic.

Run a single suite:
```bash
pytest backend/product_segment/tests/llm -q
```

---
© Leviton Intelligence 2025 