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
      • detailed structured logging.

Concrete stage subclasses MUST implement five small hooks (see the *abstract
methods* further below); **no** direct LLM interaction is required in the
subclass – they only focus on domain prompts and validation logic.

All constants come from :pymod:`utils.config`; the helper never hardcodes
numbers.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, Sequence, Tuple, TypeVar
import asyncio

from core.utils import config as cfg
from core.utils.llm_utils import safe_llm_call, ValidationResult, LLMCallError  # Central semaphore + retry logic

logger = logging.getLogger(__name__)

__all__ = [
    "StageContext",
    "StageResultBase",
    "CallStorage",
    "BaseStage",
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



class StageProtocolError(RuntimeError):
    """Raised when an LLM response keeps failing validation even after splits."""


class StageCallBudgetExceeded(RuntimeError):
    """Total LLM call budget (cfg.MAX_LLM_CALLS_PER_EXECUTE) exhausted."""


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class StageResultBase:
    """Base class for stage execution results."""
    pass

@dataclass(slots=True, frozen=True)
class StageContext:
    """Immutable context object passed through stage execution.

    Parameters
    ----------
    input_seq
        The *sequence* of documents/items to process.
    product_category
        The product category being processed (e.g., "light switch", "electronics").
        Used for prompt template substitution and validation context.
    storage
        Optional persistence adapter; when supplied each prompt/response pair
        (including retries and recursive splits) is written through
        ``storage.write_json``.
    extracted_taxonomies, consolidated_taxonomies
        Upstream artefacts – preserved here so downstream stages may inspect
        them.  The base utilities never read these fields.
    """

    input_seq: Sequence[Any]
    product_category: str
    storage: CallStorage | None = None

    # Upstream artefacts (optional)
    extracted_taxonomies: list[Any] | None = None
    consolidated_taxonomies: list[Any] | None = None


# ---------------------------------------------------------------------------
# Internal helper for _llm_roundtrip
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class _RoundtripResult:
    ok: bool
    payload: str | None
    retry_ctx: Any | None = None


# ---------------------------------------------------------------------------
# BaseStage implementation
# ---------------------------------------------------------------------------

class BaseStage:
    """Abstract base-class that handles LLM calls, retries, splitting & metrics."""

    # ------------------------- abstract hooks ----------------------------------
    async def _build_prompt(self, seq: Sequence[Any], ctx: StageContext) -> str:  # noqa: D401 – abstract signature
        raise NotImplementedError

    def _validate(
        self, raw_response: str, seq: Sequence[Any], ctx: StageContext
    ) -> ValidationResult:
        """Synchronously validate the LLM response.

        Implementations should return a :class:`ValidationResult` instance.  The
        :pyattr:`ValidationResult.ok` flag decides whether the response is
        considered valid.  The *error_categories* payload will be forwarded to
        :pyfunc:`_retry_prompt` as-is when the call needs to be retried.
        """
        raise NotImplementedError

    def _retry_prompt(
        self, original_prompt: str, retry_ctx: Any, ctx: StageContext
    ) -> str:
        """Return a new prompt based on *retry_ctx* coming from *_validate*."""
        raise NotImplementedError

    async def _produce_result(
        self,
        seq: Sequence[Any],
        raw_response: str,
        ctx: StageContext,
        attempts: int,
    ) -> StageResultBase:
        raise NotImplementedError

    async def _merge_split_results(
        self,
        seq_left: Sequence[Any],
        seq_right: Sequence[Any],
        res_left: StageResultBase,
        res_right: StageResultBase,
        ctx: StageContext,
        depth: int,
    ) -> StageResultBase:
        raise NotImplementedError

    # Optional hooks ---------------------------------------------------------

    def _split_input(
        self, seq: Sequence[Any], depth: int
    ) -> tuple[Sequence[Any], Sequence[Any]]:  # noqa: D401 – overridable
        """Return a 2-way split of *seq* for recursive processing.

        Subclasses may override this to implement custom strategies (e.g. pair
        splitting for consolidation).  The default implementation halves the
        sequence (⌊n/2⌋ | ⌈n/2⌉).  The method **must** return exactly two
        non-empty sub-sequences; callers are responsible for guarding against
        *len(seq) == 1* before invoking it.
        """

        mid = len(seq) // 2
        return seq[:mid], seq[mid:]

    # ---------------------------------------------------------------------
    # Public entry-point
    # ---------------------------------------------------------------------

    async def execute(self, ctx: StageContext) -> StageResultBase:  # noqa: D401
        """Run the stage for *ctx.input_seq*.

        The retry logic is now fully delegated to :pyfunc:`safe_llm_call` –
        this helper handles validation-aware retries and only returns once the
        LLM response passes :pyfunc:`_validate` *or* raises
        :class:`core.utils.llm_utils.LLMCallError` after exhausting the global
        retry budget.

        The recursive helper is preserved solely so subclasses can override the
        split behaviour (e.g. consolidation stages may implement a custom
        splitting strategy).  The default implementation, however, **does not
        auto-split** – it processes the *seq* as a single batch.
        """

        async def _run_recursive(seq: Sequence[Any], depth: int = 0) -> StageResultBase:
            # NOTE: Depth is currently unused here but retained so specialised
            #       subclasses (e.g. consolidation) may leverage it.

            # Check recursive depth limit
            if depth >= cfg.MAX_RECURSIVE_DEPTH:
                raise StageProtocolError(
                    f"Maximum recursive depth ({cfg.MAX_RECURSIVE_DEPTH}) exceeded"
                )

            # 1) Build initial prompt -------------------------------------------------
            prompt = await self._build_prompt(seq, ctx)

            # 2) Adapter wrappers for the shared safe_llm_call -----------------------
            def _validator(raw: str):
                result = self._validate(raw, seq, ctx)
                return result  # Return ValidationResult directly

            def _retry_builder(original_prompt: str, retry_ctx: Any):
                return self._retry_prompt(original_prompt, retry_ctx, ctx)

            # 3) Fire the LLM – safe_llm_call handles its own retries ------------
            try:
                raw_response = await safe_llm_call(
                    prompt,
                    validate_response=_validator,
                    retry_prompt_builder=_retry_builder,
                    context={"stage": self.__class__.__name__, "depth": depth},
                )

                # 4) Successful – convert payload to stage-specific result -----------
                return await self._produce_result(seq, raw_response, ctx, attempts=1)

            except LLMCallError as exc:
                # After safe_llm_call exhausted its retries the response still failed
                # validation.  Apply *split-and-conquer* fallback if we have a batch
                # larger than one element; otherwise propagate as a protocol error.

                if len(seq) > 1:
                    left, right = self._split_input(seq, depth)

                    res_left, res_right = await asyncio.gather(
                        _run_recursive(left, depth + 1),
                        _run_recursive(right, depth + 1),
                    )

                    return await self._merge_split_results(
                        left, right, res_left, res_right, ctx, depth + 1
                    )

                # Single element still invalid → terminal failure
                raise StageProtocolError(
                    "Validation failed even for single-item batch after retries"
                ) from exc

        # Start recursion (single pass by default)
        return await _run_recursive(ctx.input_seq, depth=0)
