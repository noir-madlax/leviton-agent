"""Token-aware async rate limiter for LLM calls.

This is a **minimal** extraction of the production‐grade implementation that
lived in ``archive/backend-old/src/competitor/utils/rate_limiter.py``.  The
objective here is not to replicate every bell and whistle but to provide a
robust, dependency-free rate-limiter that:

1.  Caps *requests/minute* and *concurrent* requests.
2.  Optionally caps estimated *tokens/minute* (input+output).  The token
    estimation uses ``tiktoken`` when available and otherwise falls back to a
    4-chars-per-token heuristic so the module never hard-depends on it.
3.  Is entirely **async** so it can be used from any coroutine without
    blocking the event-loop.

Keeping the implementation in ``backend.product_segmentation.utils`` ensures
that *all* LLM clients in the backend (present and future) can share the same
logic.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Deque, Tuple, Optional

import logging

logger = logging.getLogger(__name__)

try:  # Lazy optional import – do **not** hard-require tiktoken at runtime.
    import tiktoken  # type: ignore

    _TOKENIZER = tiktoken.get_encoding("cl100k_base")
except Exception:  # pylint: disable=broad-except
    _TOKENIZER = None  # type: ignore


class RateLimiter:  # pylint: disable=too-few-public-methods
    """Asynchronous rate-limiter with token accounting."""

    def __init__(
        self,
        max_requests_per_minute: int = 3_000,
        max_input_tokens_per_minute: int = 120_000,
        max_output_tokens_per_minute: int = 120_000,
        max_concurrent_requests: int = 100,
        model_max_tokens: int = 4_096,
    ) -> None:
        # Hard caps ------------------------------------------------------------------
        self._max_rpm = max_requests_per_minute
        self._max_in_tok = max_input_tokens_per_minute
        self._max_out_tok = max_output_tokens_per_minute
        self._max_concurrent = max_concurrent_requests
        self._model_max_tokens = model_max_tokens

        # Sliding-window usage trackers ----------------------------------------------
        # Each deque entry is ``(timestamp, amount)``
        self._req_times: Deque[Tuple[float, int]] = deque()
        self._in_tok_times: Deque[Tuple[float, int]] = deque()
        self._out_tok_times: Deque[Tuple[float, int]] = deque()

        # Concurrency gate -----------------------------------------------------------
        self._sem = asyncio.Semaphore(self._max_concurrent)

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Return rough token count without external dependencies."""
        if _TOKENIZER is not None:
            try:
                return len(_TOKENIZER.encode(text))
            except Exception:  # pylint: disable=broad-except
                pass
        # Fallback – 4 chars ≈ 1 token (OpenAI heuristic)
        return max(1, len(text) // 4)

    def estimate_tokens(self, text: str) -> int:  # noqa: D401 – tiny shim
        return self._estimate_tokens(text)

    async def acquire(self, est_input_tokens: int, est_output_tokens: Optional[int] = None) -> None:
        """Block until both token- and request-level budgets allow a new call."""
        if est_output_tokens is None:
            est_output_tokens = self._model_max_tokens // 2

        await self._sem.acquire()
        while True:
            now = time.time()
            self._purge_old(now)

            if (
                self._within(self._req_times, self._max_rpm, 1)
                and self._within(self._in_tok_times, self._max_in_tok, est_input_tokens)
                and self._within(self._out_tok_times, self._max_out_tok, est_output_tokens)
            ):
                # Reserve slots ---------------------------------------------------
                self._req_times.append((now, 1))
                self._in_tok_times.append((now, est_input_tokens))
                self._out_tok_times.append((now, est_output_tokens))
                return  # Permit granted

            # Otherwise wait a bit and re-check ----------------------------------
            await asyncio.sleep(0.25)

    def release(self, act_input_tokens: Optional[int] = None, act_output_tokens: Optional[int] = None) -> None:
        """Release semaphore and optionally correct token counts."""
        self._sem.release()
        # Token corrections are **best-effort** – failures are non-fatal.
        if act_input_tokens is not None and self._in_tok_times:
            ts, _ = self._in_tok_times.pop()
            self._in_tok_times.append((ts, act_input_tokens))
        if act_output_tokens is not None and self._out_tok_times:
            ts, _ = self._out_tok_times.pop()
            self._out_tok_times.append((ts, act_output_tokens))

    # ---------------------------------------------------------------------
    # Internals
    # ---------------------------------------------------------------------

    @staticmethod
    def _within(deq: Deque[Tuple[float, int]], limit: int, add: int) -> bool:
        """Return *True* if ``sum(deq) + add`` stays below ``limit``."""
        return sum(v for _, v in deq) + add <= limit

    def _purge_old(self, now: float) -> None:
        """Drop deque entries that fall outside the 60-sec window."""
        for dq in (self._req_times, self._in_tok_times, self._out_tok_times):
            while dq and dq[0][0] < now - 60.0:
                dq.popleft() 