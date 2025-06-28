# Review-Analysis Engine ‑ v1.0  
*Backend subsystem: `backend/review_analysis`*

---

## 1. Purpose
Extract **hierarchical customer insights** from Amazon reviews, then transform them into **business-ready aspect categories** that can be queried by downstream analytics dashboards.  
Compared with the product-segmentation engine, this module adds an **initial extraction phase** that produces a rich three-level JSON structure (`phy`, `perf`, `use`).  The later *categorize → consolidate → refine* stages re-use the same AI-assisted workflow pattern.

## 2. High-Level Flow
1. **Client/UI** calls `POST /review-analysis` with a list of `asin` identifiers.  
2. The **Service layer** orchestrates four LLM stages per product:
   1. **Extraction** – run `review_aspects_extraction_prompt_v0.txt` on *all* reviews to produce the hierarchy.
   2. **Categorization** – batch-group raw aspects into provisional business categories.
   3. **Consolidation** – iteratively merge batch taxonomies into a global taxonomy.
   4. **Refinement** – re-assign *all* aspects against the consolidated taxonomy for perfect mutual exclusivity.
3. After every LLM call the engine writes:
   * a JSON file to `llm_logs/review_analysis/RUN_*` via `LLMStorageService` (see §3)
   * an index row to `review_aspect_llm_interactions` for traceability.
4. The orchestrator updates **run progress** so dashboards can render a live progress bar.

```
┌ client ──► REST API ──► Service  ──► LLM client ──► Claude/OpenAI
│                                   │                   ▲
│                                   ├──► Storage (JSON) │
└───────── progress / results ◄─────┴── DB repositories ┘
```

## 3. Storage Layout (local → S3-ready)
```
llm_logs/
└── review_analysis
    ├── RUN_<ISO>_<hash>/
    │   ├── prompts/
    │   │   ├── extract_aspects_prompt.txt
    │   │   ├── categorize_aspects_prompt.txt
    │   │   ├── consolidate_aspects_prompt.txt
    │   │   └── refine_aspects_prompt.txt
    │   ├── extraction/              # per-product
    │   │   └── <ASIN>_extract.json
    │   ├── categorization/          # batch-level
    │   │   └── 20250618T120625Z_batch0.json
    │   ├── consolidation/
    │   │   └── 20250618T120830Z_round1.json
    │   └── refinement/
    │       └── 20250618T121200Z_final_assign.json
```
*Filename pattern*  `<ISO>_batch<i|all>_a<attempt>_<hash>.json` unless `extraction` which is one-file-per-ASIN.  
Each file contains **full prompt**, **raw LLM response** and **metadata** identical to the product-segmentation log schema.

## 4. LLM I/O Schemas
1. **Extraction** – see [`prompts/review_aspects_extraction_prompt_v0.txt`](./prompts/review_aspects_extraction_prompt_v0.txt) for the nested JSON spec ↓
```
{
  "phy": { "<PHYSICAL>": { "<PID>@<DETAIL>": { "+": [ID,…], "-": [ID,…] } } },
  "perf": { "<PERF>": { "<perf_id>@<DETAIL>": { "+": {<REASON>: [ID,…]}, "-": {...} } } },
  "use":  { "<USE>":  { "+": {<REASON>: [ID,…]}, "-": {...} } }
}
```
2. **Categorization** – input = list of `[ID] description`; output = JSON mapping **new subcategory → {definition, ids}` (prompt v0).
3. **Consolidation** – input = Taxonomy A + Taxonomy B; output = JSON mapping **consolidated-name → {definition, ids}` where `ids` are `A_i` / `B_j`.
4. **Refinement** – input = consolidated taxonomy & `[ID] description`; output = JSON mapping **aspect ID → C_k / OUT_OF_SCOPE**.

All validation & retry logic lives in `process_reviews.py` and `categorize_review_aspects.py`.

## 5. Database Schema (draft v1.0)
```sql
-- run header ------------------------------------------------------------
CREATE TABLE review_aspect_runs (
    id              VARCHAR(50)  PRIMARY KEY,
    created_at      TIMESTAMPTZ  DEFAULT now(),
    stage           VARCHAR(20)  DEFAULT 'init',

    llm_config       JSONB,
    processing_params JSONB,
    result_summary   JSONB
);

-- taxonomy / category definitions --------------------------------------
CREATE TABLE review_aspect_taxonomies (
    id              BIGSERIAL PRIMARY KEY,
    run_id          VARCHAR(50) REFERENCES review_aspect_runs(id),
    category_name   VARCHAR(255),
    definition      TEXT,
    stage           VARCHAR(30) DEFAULT 'categorization' -- or consolidation_l0 … final
);

-- placeholder row so UI has a bucket before first extraction
INSERT INTO review_aspect_taxonomies (run_id, category_name, definition, stage)
VALUES (:run_id, '__OUT_OF_SCOPE__', 'Uncategorizable or generic aspects', 'system');

-- unified assignment table ---------------------------------------------
CREATE TABLE review_aspect_assignments (
    run_id          VARCHAR(50) REFERENCES review_aspect_runs(id),
    asin            VARCHAR(20),
    aspect_raw_id   VARCHAR(40),   -- PID / perf_id / use key
    taxonomy_id_initial BIGINT,    -- first categorization
    taxonomy_id_refined BIGINT,    -- after final refinement
    PRIMARY KEY (run_id, asin, aspect_raw_id)
);
```

## 6. Public API (v1.0)
### 6.1 Create & run (single call)
```http
POST /review-analysis
{
  "asins": ["B0C123", "B084XYZ"],
  "product_category_fallback": "Light Switches"
}

HTTP/1.1 202 Accepted
Location: /review-analysis/RUN_20250618T120301Z_8d24/stream
```
`/stream` returns SSE with progress events identical to product-segmentation.

### 6.2 Fetch results
```http
GET /review-analysis/{run_id}/results
```
Returns the **extraction JSON** plus **category mapping** for each ASIN.

## 7. Configuration
All env vars mirror `backend/product_segment/config.py` with additional knobs:
* `REVIEW_ANALYSIS_BATCH_SIZE` – #aspects per categorization LLM call (default 150)
* `REVIEW_ANALYSIS_EXTRACT_MODEL` – model for extraction phase (can differ from categorization model)
* `REVIEW_ANALYSIS_CACHE_DIR` – separate sub-folder under `llm_logs`

## 8. Validation & Retry Strategy
Validation rules for IDs, sentiment, hierarchy depth, duplicate coverage, etc. are implemented in `process_reviews.py` (`validate_hierarchy_structure`).  On any failure the **shared retry template** is appended to the original prompt, supplying:
* **Error breakdown** *(format / validation / completeness)*
* **Excerpt of previous attempt (JSON or raw)*
* **Context sections** (product info, missing IDs, …)

This yields deterministic convergence within ≤3 attempts by design.

## 9. Roadmap
* v1.1 – incremental processing that streams extraction & categorization per product for lower latency.
* v1.2 – surfacing aspect importance metrics (frequency × sentiment) during categorization.
* v2.0 – merge aspect data with product-segmentation segments for combined dashboards.

---
© 2025 Leviton Intelligence
