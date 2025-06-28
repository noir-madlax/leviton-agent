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
├── extraction_stage.py       # concrete ExtractionStage
├── consolidation_stage.py    # concrete ConsolidationStage
├── refinement_stage.py       # concrete RefinementStage
└── taxonomy_dedup_uitl.py    # stemming-based dedup helper
```

## 1. ExtractionStage
* Converts *product titles* into provisional taxonomies.
* Validation ensures every `[ID]` appears exactly once across the response.
* Uses prompt `prompts/taxonomy_extraction_prompt_v0.txt`.

## 2. ConsolidationStage
* Merges two taxonomy lists at a time; recursion handles >2 lists.
* Validation guarantees unique names after consolidation.
* Prompt: `prompts/taxonomy_consolidation_prompt_v0.txt`.

## 3. RefinementStage
* Re-assigns products to the final consolidated taxonomy.
* Accepts JSON `{"P_1": "S_0", ...}` where `P_*` are product indices and
  `S_*` are sub-category IDs rendered in the prompt.
* Prompt: `prompts/taxonomy_refinement_prompt_v0.txt`.

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