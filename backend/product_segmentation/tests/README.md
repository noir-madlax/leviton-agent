# Product-Segmentation Test-Suite Overview

This document complements `README_product_segmentation.md` by mapping **each test module** to the corresponding processing phase of the Product-Segmentation Engine and explaining the kind of behaviour it safeguards.

---

## 0  End-to-End Flow (recap)

```
Input product_ids
      │
      ▼
Phase 1 – Batching helpers (utils.batching)
      │
      ▼
Phase 2 – LLM Segmentation  ← caching / storage layer
      │
      ▼
Phase 3 – Taxonomy Consolidation
      │
      ▼
Phase 3b – Assignment Refinement
      │
      ▼
Phase 4 – Result Persistence & API exposure
```

The unit & integration tests target those layers from **pure functions** up to **FastAPI endpoints**.  External services (Supabase, S3, OpenAI) are replaced with deterministic fakes where necessary, but the orchestration / validation / persistence logic is always the *real* production code.

---

## 1  Module-by-Module Coverage

| Test file | Engine phase(s) | Focus | Notes |
|-----------|-----------------|-------|-------|
| **`test_models.py`** | _All phases (data-contract)_ | Pydantic schema validation, edge cases, id length, enum values | Pure model layer, no fakes |
| **`test_batching.py`** | Phase 1 | Optimal batch sizing & determinism of helper functions | Pure Python logic |
| **`test_cache.py`** | Phase 2 (caching sub-layer) | File-based `LLMCache` round-trip, eviction & clearing | tmp paths only |
| **`test_storage.py`** | Phase 2 (storage sub-layer) | `LLMStorageService` path generation, store/load integrity, checksum verification | tmp dirs, no mocks |
| **`test_interaction_repository.py`** | Phase 2 ↔ DB | SQL payload generation & insert success; uses fake Supabase client | Validates DB contract without real DB |
| **`test_service.py`** | Phases 1-4 | `DatabaseProductSegmentationService` control-flow: run creation, batching, LLM calls (stub), progress tracking, completion & failure | In-memory repos + `StubLLM`, but real orchestrator code |
| **`test_api.py`** | Phase 4 | FastAPI router contract, request/response schema, 500-path handling | Uses same in-memory service wired by the router |
| **`test_db_cache_integration.py`** | Phase 2 (cache lookup across **DB index + storage**) | Ensures pre-existing interaction is replayed without hitting LLM | Fake interaction repo + storage, real client logic |
| **`test_db_integration_real.py`** | Full stack (opt-in) | Executes a segmentation run against a **real Supabase instance** for smoke/regression | Marked separately, skipped in CI unless credentials provided |

> **Removed tests**:  `test_llm_client.py` was deleted because it exercised only stub interactions and several now-private helpers, duplicating more realistic coverage provided by the modules above.

---

## 2  Running the Suite

From the`backend/`:

```bash
python -m pytest product_segmentation/tests/ -v -k "not test_db_integration_real"
```

The heavy *real-DB* integration test is deselected by default; run it explicitly when Supabase credentials are configured.

A one-shot helper is also available:

```bash
python -m backend.product_segmentation.test_runner
```

which executes all **phase-ordered** suites and returns a non-zero exit-code on the first failure – useful for CI pipelines.

---

## 3  Coverage Goals

| Layer | Target coverage |
|-------|-----------------|
| Pure helpers / utils | ≥ 95 % |
| Service orchestrator | ≥ 85 % |
| Storage / Cache | ≥ 85 % |
| FastAPI router | ≥ 80 % |

The current suite meets those thresholds once run without the optional Supabase test (CI baseline).  Please keep this README in sync when adding new tests or restructuring existing ones. 