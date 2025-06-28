# LLM-Taxonomy Pipeline (shared core)

This package offers **re-usable orchestration mechanics** for any workflow that needs to:

1. extract provisional taxonomies from free-text,  
2. merge overlapping/duplicate taxonomies, and  
3. assign every original item to the final taxonomy.

Only _prompt templates_ and _response-validation logic_ differ per domain; all
batching, retry, and auto-split behaviour lives here.

```
backend/core/llm_taxonomy_pipeline/
├── pipeline_stage.py       # BaseStage, StageContext, StageResultBase
├── extraction_base.py      # abstract ExtractionStage
├── consolidation_base.py   # abstract ConsolidationStage
├── refinement_base.py      # abstract RefinementStage
└── prompts/                # shared prompt fragments (e.g. shared_retry_prompt_v0.txt)
```

Down-stream domains (e.g. `backend/product_segment/llm`, `backend/review_analysis/llm`)  
create **concrete** `extraction_stage.py`, `consolidation_stage.py`, `refinement_stage.py`
that subclass the corresponding base and implement:

* `_build_prompt`              – render prompt from templates & context.
* `_validate`                  – parse + rule-check raw LLM response.
* `_retry_prompt`              – append human-readable error diagnostics for 2nd attempt.
* `_produce_result`            – convert valid response → domain DTOs.

All constants (batch sizes, call budgets …) live in `backend/core/utils/config.py`.

## How retry / split works

```
┌ BaseStage.execute ──► attempt 1 ── validate ─┬─ ok  ⇒ produce_result
│                                              │
│                                              └─ fail ⇒ build_retry_prompt
│                                                               │
├──► attempt 2 ── validate ─┬─ ok ⇒ produce_result              │
│                           └─ fail & batch_len>1               │
│                                         │                     │
└── recursive split(left,right) ◄──────────┘                     │
      (runs execute() on both halves) ◄──────────────────────────┘
```

Validation & retry prompts are *stage-specific*; the control-flow is shared.

## Key guarantees

* No hard-coded numbers – every constant comes from config.
* No DB writes – stages return dataclasses, calling service decides persistence.
* Deterministic retries – at most two attempts per logical batch before split.
* Structured logs via `core.utils.llm_utils.safe_llm_call` for every LLM round-trip.

---
© Leviton Intelligence 2025