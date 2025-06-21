# Product-Segmentation Engine ‑ v6.0  
*Backend subsystem: `backend/product_segmentation`*

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
└── product_segmentation
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

    -- detailed progress -------------------------------------------------
    seg_batches_done      INT DEFAULT 0,
    seg_batches_total     INT,

    con_batches_done      INT DEFAULT 0,
    con_batches_total     INT,      -- pair-wise consolidation levels

    ref_batches_done      INT DEFAULT 0,
    ref_batches_total     INT,

    total_products        INT,
    processed_products    INT DEFAULT 0,

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

-- llm interactions ------------------------------------------------------
CREATE TABLE product_segment_llm_interactions (
    id         BIGSERIAL PRIMARY KEY,
    run_id     VARCHAR(50) REFERENCES product_segment_runs(id),
    file_path  TEXT UNIQUE,
    cache_key  VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

*The generic `progress_batches / total_batches / progress_percent` columns have
been replaced by stage-specific counters so UIs can render three independent
progress bars.*

### 4.0.a Consolidation batch math
Given `N₀ = ceil(total_taxonomies / TAXONOMIES_PER_PROMPT)` initial taxonomy batches, we compute
```
levels = ceil(log2(N₀))     -- always an integer
con_batches_total = levels  -- written to run header before consolidation starts
```

The service then merges **pair-wise**:
1. `[1,2] → 101`  (where *101* is a new taxonomy batch id)
2. `[3,4] → 102`
3. `[101,102] → final`

At each merge the service increments `con_batches_done`.  When it equals
`con_batches_total` the `stage` flips to `refinement`.

### 4.1 Assignment lifecycle
1. **Run creation** inserts one `product_segment_taxonomies` row with `segment_name='__UNASSIGNED__'` and stores its ID (`u_id`).
2. Service bulk-inserts one row per product into `product_segment_assignments` with `taxonomy_id_initial = u_id` and `taxonomy_id_refined = NULL`.
3. Segmentation batches `UPDATE … SET taxonomy_id_initial = <extracted>`.
4. Refinement `UPDATE … SET taxonomy_id_refined = <refined>`.

This design keeps referential integrity while allowing "not yet assigned" rows without a null foreign-key.

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

### 5.2 Progress delivery
*The backend now **pushes** progress events instead of relying on client polling.*

```
GET /product-segmentation/{run_id}/stream   # text/event-stream

# sample server-sent events (SSE)
progress: {"run_id":"RUN_…","percent":12.5}
progress: {"run_id":"RUN_…","percent":37.5}
…
```

The UI simply listens to the stream and animates **one** progress bar using the
`percent` field.

#### 5.3 Retrieve final segments

```http
GET /product-segmentation/{run_id}/segments
```

Response schema

```
{
  "run_id": "RUN_…",
  "taxonomies": [
    {"id": 1, "segment_name": "Premium Switches", "definition": "High-end smart dimmers", "product_count": 42},
    …
  ],
  "segments": [
    {"product_id": 123, "taxonomy_id": 1},
    …
  ]
}
```

### 5.4 How `percent` is calculated
Progress is proportional to the **number of LLM calls** still outstanding.
For each stage we pre-compute:

| Stage            | Calls per run |
|------------------|--------------|
| Segmentation     | seg_batches_total |
| Consolidation    | `2^x − 1` where `x = ceil(log2(seg_batches_total))` |
| Refinement       | ref_batches_total |

Total expected calls  
`C_total = seg_batches_total + (2^x − 1) + ref_batches_total`

After every LLM response we increment `calls_done` and broadcast:  
`percent = round((calls_done / C_total) * 100, 1)`

Because consolidation merges batches **pair-wise** the call sequence is:
```
level 0  : [1,2] [3,4] [5,6] [7,8]         →  2^(x-1)  calls
level 1  : [9,10] [11,12] …                 →  2^(x-2)
…
level x-1: final                             →  1        call
```
Sum = `2^(x) − 1` calls.

The result is a smooth, monotonic single bar with no sudden jumps between
stages, while still reflecting true LLM throughput.

## 6. Configuration (env / cfg)
```
```
