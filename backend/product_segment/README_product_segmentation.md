# Product-Segmentation Engine ‑ v6.0  
*Backend subsystem: `backend/product_segment`*

---

## 1. Purpose
Transforms an **explicit list of Amazon product-IDs** into **market segments** using an LLM pipeline.  
Raw LLM interactions are archived as files; only lightweight indexes & final results reach Postgres (Supabase).

## 2. High-Level Flow
1. **Client/UI** calls `POST /product-segmentation` with `product_ids` and a `product_category`.
2. The **Service layer** (`DatabaseProductSegmentationService`) creates a *run*, splits products into batches and orchestrates three LLM phases:
   1. Extraction ─ extract per-batch taxonomies.
   2. Consolidation ─ merge batch taxonomies into a global set.
   3. Refinement    ─ re-assign products with full taxonomy context.
3. After each LLM call the engine writes:
   * a JSON file to `llm_logs/RUN_*` via `LLMStorageService`.
   * an index row to `product_segment_llm_interactions`.
4. The orchestrator inserts/updates **run progress** so dashboards can render a live progress bar.

```
┌ client ──► REST API ──► Service  ──► LLM client ──► Claude/OpenAI
│                              │                   ▲
│                              ├──► Storage (JSON) │
└──────── progress / results ◄─┴── DB repositories ┘
```

## 3. Storage Layout (local → S3-ready)
```
llm_logs/
└── product_segment
    ├── RUN_<ISO>_<hash>/
    │   ├── prompts/
    │   │   ├── extract_taxonomy_prompt.txt
    │   │   ├── consolidate_taxonomy_prompt.txt
    │   │   └── refine_assignments_prompt.txt
    │   ├── extraction/              # batch-level
    │   │   ├── 20250618T120305Z_b1_a1_f4c2.json
    │   │   └── …
    │   ├── consolidation/
    │   │   └── 20250618T120625Z_all_a1_9ab1.json
    │   └── refinement/
    │       ├── 20250618T120900Z_b1_a1_c1d2.json
    │       └── …
```
*Filename pattern*  `<ISO>_<b{batch}|all>_<a{attempt}>_<hash>.json`.
*JSON schema*  (excerpt)
```json
{
  "metadata": {
    "run_id": "RUN_…",
    "llm_interaction_id": 1111,
    "batch_id": 1,
    "attempt": 1,
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.15,
    "timestamp": "2025-06-18T12:03:05Z",
    "cache_key": "f4c2e6ab",
    "duration_ms": 2345,
    "batch_size": 40, 
    "product_ids": [0,1,…]
  },
  "prompt": "<full prompt>",
  "response": "<raw LLM response>"
}

### 4.2 JSON File Schema


## 4. Database Schema (v6.4)
```sql
-- run header ------------------------------------------------------------
CREATE TABLE product_segment_runs (
    id                   VARCHAR(50)  PRIMARY KEY,
    created_at           TIMESTAMPTZ  DEFAULT now(),
    stage                VARCHAR(20)  DEFAULT 'init',

    llm_config            JSONB,
    processing_params     JSONB,
    result_summary        JSONB
);

-- taxonomy / segment definitions ---------------------------------------
CREATE TABLE product_segment_taxonomies (
    id           BIGSERIAL PRIMARY KEY,
    run_id       VARCHAR(50) REFERENCES product_segment_runs(id),
    segment_name VARCHAR(255),
    definition   TEXT,
    stage        VARCHAR(30)   DEFAULT 'extraction'  -- e.g. extraction, consolidation_l0, consolidation_l1, ..., final
);

-- placeholder row created at run start
INSERT INTO product_segment_taxonomies (run_id, segment_name, definition, stage)
VALUES (:run_id, '__UNASSIGNED__', 'Auto-generated placeholder', 'init');

-- special bucket for products filtered out by the extraction prompt
INSERT INTO product_segment_taxonomies (run_id, segment_name, definition, stage)
VALUES (:run_id, '__OUT_OF_SCOPE__', 'Products totally irrelevant to the current category', 'system');

-- unified assignment table ---------------------------------------------
CREATE TABLE product_segment_assignments (
    run_id               VARCHAR(50) REFERENCES product_segment_runs(id),
    product_id           BIGINT      REFERENCES amazon_products(id),
    taxonomy_id_initial  BIGINT      REFERENCES product_segment_taxonomies(id),
    taxonomy_id_refined  BIGINT      REFERENCES product_segment_taxonomies(id),
    PRIMARY KEY (run_id, product_id)
);
```


## 5. Public API (v6.2)
### 5.1 Create & run (single call)
```http
POST /product-segmentation
{
  "product_ids": [123,456,789],
  "product_category": "Dimmer Switches"
}

HTTP/1.1 202 Accepted
Location: /product-segmentation/RUN_20250618T120301Z_8d24/stream
```

## 6. Configuration (env / cfg)
```
```
