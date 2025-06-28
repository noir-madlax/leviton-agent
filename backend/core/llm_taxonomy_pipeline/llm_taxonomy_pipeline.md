The focus is on responsibilities, data structures, control-flow, inputs/outputs, and observability for each stage – independent of any domain-specific storage layer or database schema.

────────────────────────────────────────────────────────
A. Shared Building Blocks
────────────────────────────────────────────────────────
All stage processors use the same supporting abstractions provided by
`backend/core/utils/llm_taxonomy_pipeline.py`:

1. StageContext (immutable dataclass)
   • run_id (optional str) – correlation identifier for logs/metrics
   • input_seq (Sequence[Any]) – the **only mandatory** input: raw texts or
     lightweight documents to be categorised.
   • storage (CallStorage | None) – adapter that can persist every prompt /
     response pair; irrelevant stages simply pass `None`.
   • context_vars (dict[str, Any]) – free-form values accessible by prompts.
   • artefacts (dict[str, Any]) – downstream-read-only map populated by stages
     to expose intermediate results (e.g. `{"taxonomies_extracted": [...]}`).

2. BaseStage (ABC)
   • `async execute(ctx: StageContext) → StageResultBase`
   • wraps five abstract hooks in common mechanics:
     – **two attempts** per logical batch (original + retry prompt)
     – automatic *split-and-conquer* fallback when validation fails
     – global call-budget ceiling (`cfg.MAX_LLM_CALLS_PER_EXECUTE`)
     – optional persistence via `ctx.storage.write_json(record)`
     – structured logging of attempt / batch details

3. StageResultBase (dataclass)
   • `calls_made` – number of LLM round-trips consumed
   • concrete subclasses extend this with domain-specific payload

4. PromptRenderer / ResponseParser helpers live **next to the concrete stage
   implementation**, not in the core utilities.

5. **No hard-coded numbers**: every constant resides in `utils.config` or a
   Pydantic `Settings` object.

────────────────────────────────────────────────────────
B. ExtractionStage
────────────────────────────────────────────────────────
Goal Convert raw input texts → *provisional* taxonomies + initial assignments.

Inputs
• `ctx.input_seq`: `Sequence[str]` – texts to analyse (e.g. product reviews,
  support tickets, blog posts …)

Outputs (StageResult subclass)
• `taxonomies_extracted: list[TaxonomyDTO]`
• `assignments_initial: dict[int, str]` # idx → taxonomy_name
• `batches_done: int`
• `calls_made: int`

Algorithm
1. **Batching** – split `input_seq` into chunks of
   `cfg.MAX_BATCH_SIZE_TEXTS` using a helper.
2. **Parallel processing** (bounded by internal semaphore):
   a. Render *extraction* prompt with `{texts_json}` and optional context
      (`ctx.context_vars`).
   b. LLM call executed through `BaseStage.execute`.
   c. Validate JSON: every text index appears exactly once; each taxonomy has
      `name` + `definition`.
   d. Persist prompt / response via `ctx.storage` (if set).
3. Gather per-batch results and return aggregated StageResult.

Observability & Validation
• Structured log for each batch: `{run_id, batch_id, new_taxonomies_n}`.
• On validation failure → automatic retry, then auto-split; final failure raises
  `StageProtocolError`.

────────────────────────────────────────────────────────
C. ConsolidationStage
────────────────────────────────────────────────────────
Goal Merge overlapping or duplicate taxonomies into a coherent, unique set.

Inputs
• `ctx.artefacts["taxonomies_extracted"]`

Outputs
• `taxonomies_final: list[TaxonomyDTO]`
• `batches_done: int`
• `calls_made: int`

Algorithm
1. **Overview – two-input batches**
   Each batch consumed by the ConsolidationStage contains **two separate
   sequences** – the *left* and *right* taxonomy lists.  They are passed to the
   LLM together so it can decide how to merge overlapping categories.

2. **Level-wise pair consolidation**
   a. Start with `current_sets = taxonomies_extracted` (list[list[TaxonomyDTO]]).
   b. While `len(current_sets) > 1`:
      i.  Build `pairs = pairwise(current_sets)` → `[(S1,S2), (S3,S4), …]`.
      ii. For every pair **in parallel** (bounded by the internal semaphore):
          • Render *consolidation* prompt with JSON of **two input sequences**.
          • Call LLM via `BaseStage.execute` (inherits retry / split logic).
          • Validate that the returned `merged_set` contains *unique* names and
            preserves `name` + `definition` for each entry.
          • Persist artefacts with `ctx.storage` (if provided) and collect
            calls metrics.
      iii. Gather every `merged_set` into `merged_sets` and assign
           `current_sets = merged_sets` for the next iteration.
      iv. Increment `level` and continue; depth ≤ ⌈log₂ N⌉.
   c. When the loop terminates, `current_sets` holds either one list or a very
      small duplicate-free list → this becomes `taxonomies_final`.

3. **Split-and-retry logic (per pair)**
   The _pair_ itself is treated as a batch and therefore enjoys the full
   BaseStage safety net:
   • **Attempt 1** – build prompt, call LLM, validate.
   • **Attempt 2** – on failure, build _retry prompt_, call LLM again, validate.
   • **Auto-split** – if both attempts fail _and_ the combined pair length > 1,
     each of the two input lists is halved, producing four sub-lists.  The stage
     recursively processes *(left_a + right_a)* and *(left_b + right_b)* in
     parallel and then merges the two partial results via `_merge_split_results`.
   • **Terminal failure** – if a single-entry list still fails validation after
     two attempts, `StageProtocolError` is raised.

4. **Metrics & artefacts**
   • `calls_made` aggregated across **all levels**.
   • `batches_done` counts every LLM round-trip (including recursive splits).
   • `taxonomies_final` is returned via StageResult **and** stored in
     `ctx.artefacts` for the downstream AssignmentStage.

Validation
• Duplicate names must collapse into one canonical entry; synonyms recorded in a
  `lineage` field for audit.

────────────────────────────────────────────────────────
D. AssignmentStage
────────────────────────────────────────────────────────
Goal Assign every input text to one of the *final* taxonomy entries.

Inputs
• `ctx.input_seq`
• `ctx.artefacts["taxonomies_final"]`

Outputs
• `assignments_final: dict[int, str]`
• `batches_done: int`
• `calls_made: int`

Algorithm
1. Precompute `taxonomy_lookup = {name.lower(): taxonomy_obj}`.
2. Reuse the same batching + parallelism strategy as ExtractionStage.
3. Validate that every text index appears exactly once; raise on duplicates /
   omissions.

────────────────────────────────────────────────────────
E. Cross-Cutting Concerns Recap
────────────────────────────────────────────────────────
• **No direct database writes** – the pipeline only returns dataclasses; the
  caller decides how/where to persist artefacts.
• **Observability** – stages log structured records; higher-level orchestrators
  can forward these to Prometheus / OpenTelemetry.
• **Retry & split logic** centralised in `BaseStage`; concrete stages remain
  thin wrappers over domain prompts + validation.
• **Constants** centralised; no magic numbers inside stage code.
• All exceptions are propagated unless explicitly whitelisted (e.g.
  `asyncio.CancelledError`).

This design yields a deterministic, testable flow for generic taxonomy
extraction and categorisation tasks while staying agnostic of any downstream
persistence or application-specific schemas.