"""Generic LLM-powered taxonomy / categorisation pipeline utilities.

This module provides **all** cross-cutting mechanics required by multi-stage
workflows that rely on large-language-model calls.  It is deliberately kept
backend-agnostic: there are **no** imports from database layers, storage back
ends, or segmentation-specific helpers.  Any application can implement concrete
stage classes on top of :class:`BaseStage` and plug them into its own
orchestrator.

Main building blocks
--------------------
1. ``StageContext``   – immutable dataclass carrying the input sequence, optional
   LLM configuration, a (pluggable) storage adapter, and arbitrary ``context_vars``.
2. ``StageResultBase`` – common metrics payload returned by every stage.  Concrete
   stages should inherit from this dataclass to expose their domain-specific
   data.
3. ``BaseStage``      – abstract base class that implements:
      • two LLM attempts per *logical batch* (original + retry prompt),
      • automatic **split-and-conquer** fallback: when both attempts fail
        validation and the batch length > 1, the input is halved and processed
        recursively; this continues until either validation succeeds or a
        single-element batch still fails (protocol error).
      • global call budget enforcement via ``cfg.MAX_LLM_CALLS_PER_EXECUTE``.
      • automatic prompt / response persistence through an optional
        ``CallStorage`` adapter on the context.
      • detailed structured logging and latency measurement.

Concrete stage subclasses MUST implement five small hooks (see the *abstract
methods* further below); **no** direct LLM interaction is required in the
subclass – they only focus on domain prompts and validation logic.

All constants come from :pymod:`utils.config`; the helper never hardcodes
numbers.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence, Tuple, TypeVar

from utils import config as cfg
from utils.llm_utils import safe_llm_call  # Central semaphore + retry logic

logger = logging.getLogger(__name__)

__all__ = [
    "StageContext",
    "StageResultBase",
    "CallStorage",
    "BaseStage",
    "chunked",
    "pairwise",
    "StageProtocolError",
    "StageCallBudgetExceeded",
]

# ---------------------------------------------------------------------------
# Helper type-aliases / protocols
# ---------------------------------------------------------------------------

class CallStorage(Protocol):
    """Minimal adapter interface used to persist each prompt/response pair."""

    async def write_json(self, record: dict[str, Any]) -> str:  # noqa: D401 – protocol
        """Persist *record* and return the file-path/identifier."""


T = TypeVar("T", bound="StageResultBase")


class StageProtocolError(RuntimeError):
    """Raised when an LLM response keeps failing validation even after splits."""


class StageCallBudgetExceeded(RuntimeError):
    """Total LLM call budget (cfg.MAX_LLM_CALLS_PER_EXECUTE) exhausted."""


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class StageContext:
    """Immutable context object passed through stage execution.

    Parameters
    ----------
    input_seq
        The *sequence* of documents/items to process.
    llm_cfg
        Optional override for LLM configuration.  When *None* the stage will
        rely on the defaults in :pymod:`utils.config`.
    storage
        Optional persistence adapter; when supplied each prompt/response pair
        (including retries and recursive splits) is written through
        ``storage.write_json``.
    context_vars
        Arbitrary key→value mapping that concrete stages can consult in their
        prompt rendering / validation logic.  E.g. ``{"doc_category": "Books"}``.
    extracted_taxonomies, consolidated_taxonomies
        Upstream artefacts – preserved here so downstream stages may inspect
        them.  The base utilities never read these fields.
    """

    input_seq: Sequence[Any]
    llm_cfg: Any | None = None
    storage: CallStorage | None = None
    context_vars: dict[str, Any] = field(default_factory=dict)

    # Upstream artefacts (optional)
    extracted_taxonomies: list[Any] | None = None
    consolidated_taxonomies: list[Any] | None = None


@dataclass(slots=True)
class StageResultBase:  # pylint: disable=too-many-instance-attributes
    """Base result object – concrete stages should subclass this."""

    calls_made: int
    latency_ms: int

    # Split-merge helpers may accumulate further metrics; subclasses should
    # override/extend as needed but must call *super().__init__*.


# ---------------------------------------------------------------------------
# Internal helper for _llm_roundtrip
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class _RoundtripResult:
    ok: bool
    payload: str | None
    latency_ms: int = 0
    retry_ctx: Any | None = None


# ---------------------------------------------------------------------------
# BaseStage implementation
# ---------------------------------------------------------------------------

class BaseStage:
    """Abstract base-class that handles LLM calls, retries, splitting & metrics."""

    # ------------------------- abstract hooks ----------------------------------
    async def _build_prompt(self, seq: Sequence[Any], ctx: StageContext) -> str:  # noqa: D401 – abstract signature
        raise NotImplementedError

    async def _validate(
        self, raw_response: str, seq: Sequence[Any], ctx: StageContext
    ) -> Tuple[bool, Any]:
        """Return (is_valid, retry_ctx).  retry_ctx fed back into _retry_prompt."""

    async def _retry_prompt(
        self, original_prompt: str, retry_ctx: Any, ctx: StageContext
    ) -> str:
        raise NotImplementedError

    async def _produce_result(
        self,
        seq: Sequence[Any],
        raw_response: str,
        ctx: StageContext,
        total_latency_ms: int,
        attempts: int,
    ) -> T:
        raise NotImplementedError

    async def _merge_split_results(
        self,
        seq_left: Sequence[Any],
        seq_right: Sequence[Any],
        res_left: T,
        res_right: T,
        ctx: StageContext,
        depth: int,
        cumulative_latency_ms: int,
    ) -> T:
        raise NotImplementedError

    # ---------------------------------------------------------------------
    # Public entry-point
    # ---------------------------------------------------------------------

    async def execute(self, ctx: StageContext) -> StageResultBase:  # noqa: D401
        """Process *ctx.input_seq* and return a :class:`StageResultBase`.

        The helper enforces:
        • Two validation attempts per batch (original + retry).
        • Automatic split-and-conquer when validation keeps failing.
        • Cumulated LLM call ceiling specified by
          ``cfg.MAX_LLM_CALLS_PER_EXECUTE``.
        """

        call_budget = cfg.MAX_LLM_CALLS_PER_EXECUTE
        calls_made = 0

        async def _run_recursive(seq: Sequence[Any], depth: int = 0) -> StageResultBase:
            nonlocal calls_made, call_budget  # modify outer scope

            if calls_made >= call_budget:
                raise StageCallBudgetExceeded(
                    f"Exceeded maximum of {cfg.MAX_LLM_CALLS_PER_EXECUTE} LLM calls"
                )

            # ---------------- attempt-1 ------------------------------------
            prompt1 = await self._build_prompt(seq, ctx)
            raw1, lat1 = await _call_and_persist(prompt1, ctx, attempt=1)
            calls_made += 1

            ok1, retry_ctx1 = await self._validate(raw1, seq, ctx)
            if ok1:
                return await self._produce_result(seq, raw1, ctx, lat1, attempts=1)

            # ---------------- attempt-2 (retry prompt) ---------------------
            if calls_made >= call_budget:
                raise StageCallBudgetExceeded(
                    f"Exceeded maximum of {cfg.MAX_LLM_CALLS_PER_EXECUTE} LLM calls"
                )

            prompt2 = await self._retry_prompt(prompt1, retry_ctx1, ctx)
            raw2, lat2 = await _call_and_persist(prompt2, ctx, attempt=2)
            calls_made += 1

            ok2, retry_ctx2 = await self._validate(raw2, seq, ctx)
            if ok2:
                return await self._produce_result(
                    seq, raw2, ctx, lat1 + lat2, attempts=2
                )

            # ---------------- auto-split -----------------------------------
            if len(seq) > 1:
                mid = len(seq) // 2
                left, right = seq[:mid], seq[mid:]
                res_left, res_right = await asyncio.gather(
                    _run_recursive(left, depth + 1),
                    _run_recursive(right, depth + 1),
                )
                return await self._merge_split_results(
                    left, right, res_left, res_right, ctx, depth + 1, lat1 + lat2
                )

            # single item still invalid → give up
            raise StageProtocolError(
                "Validation failed even for single-item batch after two attempts"
            )

        return await _run_recursive(ctx.input_seq, depth=0)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _call_and_persist(
    prompt: str,
    ctx: StageContext,
    *,
    attempt: int,
) -> Tuple[str, int]:
    """Invoke the LLM, persist artefact (if storage set) and return raw text + latency."""

    start_ts = time.time()
    raw_response = await safe_llm_call(prompt, context={**ctx.context_vars, "attempt": attempt})
    latency_ms = int((time.time() - start_ts) * 1000)

    if ctx.storage is not None:
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "attempt": attempt,
            "llm_config": ctx.llm_cfg or {
                "model": cfg.LLM_MODEL_NAME,
                "temperature": cfg.LLM_TEMPERATURE,
                "max_tokens": cfg.LLM_MAX_TOKENS,
            },
            "context_vars": ctx.context_vars,
            "prompt": prompt,
            "response": raw_response,
            "latency_ms": latency_ms,
        }
        try:
            await ctx.storage.write_json(record)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("CallStorage.write_json failed: %s", exc)

    return raw_response, latency_ms
