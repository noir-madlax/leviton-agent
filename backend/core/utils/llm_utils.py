"""Shared LLM utilities (initialisation + safe async calls).

This module centralises *all* direct calls to the LLM so the rest of the
codebase – including unit-tests and higher-level LLM wrappers – can simply
import :pyfunc:`safe_llm_call` or grab the global manager via
:pyfunc:`get_global_llm`.

The helper re-uses the :class:`backend.utils.rate_limiter.RateLimiter`
implementation to enforce project-wide API-usage limits.
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional, Callable, Tuple, List
from dotenv import load_dotenv, find_dotenv
from langchain_anthropic import ChatAnthropic
import json  # still used elsewhere
import asyncio
import time

from utils.rate_limiter import RateLimiter
from utils import config as cfg

logger = logging.getLogger(__name__)
load_dotenv(find_dotenv())

# ---------------------------------------------------------------------------
# Global concurrency gate ----------------------------------------------------
# ---------------------------------------------------------------------------
_LLM_SEMAPHORE: Optional[asyncio.Semaphore] = None


def _get_semaphore() -> asyncio.Semaphore:
    """Return the global semaphore, creating it lazily inside an event loop."""
    global _LLM_SEMAPHORE  # noqa: PLW0603 – module-level singleton
    if _LLM_SEMAPHORE is None:
        _LLM_SEMAPHORE = asyncio.Semaphore(cfg.MAX_CONCURRENT_LLM_CALLS)
    return _LLM_SEMAPHORE

# ---------------------------------------------------------------------------
# Lightweight pub-sub event bus ----------------------------------------------
# ---------------------------------------------------------------------------
_EVENT_LISTENERS: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

def register_llm_listener(event: str, callback: Callable[[Dict[str, Any]], None]) -> None:
    """Register *callback* for *event* notifications (success/attempt_error/error)."""
    _EVENT_LISTENERS.setdefault(event, []).append(callback)


def _emit_event(event: str, payload: Dict[str, Any]) -> None:
    """Dispatch *payload* to all listeners subscribed to *event*."""
    for cb in _EVENT_LISTENERS.get(event, []):
        try:
            cb(payload)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("LLM listener %s raised: %s", cb, exc)


class LLMCallError(RuntimeError):
    """Raised after *MAX_ATTEMPTS_PER_CALL* unsuccessful attempts."""

class LLMManager:  # pylint: disable=too-few-public-methods
    """Manager for LLM model initialization and configuration.

    All runtime parameters default to the values exported by
    :pymod:`backend.utils.config`.  Passing explicit arguments at construction
    time overrides the global configuration – this is mainly useful in unit
    tests where environment variables are *not* set.
    """

    def __init__(
        self,
        *,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        """Initialize LLM manager.
        
        Args:
            rate_limiter: Optional custom :class:`RateLimiter` instance
        """
        self.model_name = cfg.LLM_MODEL_NAME
        self.temperature = cfg.LLM_TEMPERATURE
        self.max_tokens = cfg.LLM_MAX_TOKENS

        self.rate_limiter = rate_limiter or RateLimiter(
            max_requests_per_minute=cfg.MAX_REQUESTS_PER_MINUTE,
            max_input_tokens_per_minute=cfg.MAX_INPUT_TOKENS_PER_MINUTE,
            max_output_tokens_per_minute=cfg.MAX_OUTPUT_TOKENS_PER_MINUTE,
            max_concurrent_requests=cfg.MAX_CONCURRENT_REQUESTS,
            model_max_tokens=self.max_tokens,
        )
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> ChatAnthropic:
        """Initialize Claude model with configuration."""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY must be set for production and integration tests. "
                "Unit-tests should monkeypatch 'backend.utils.llm_utils.safe_llm_call' instead."
            )

        return ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            anthropic_api_key=api_key,
        )

    async def safe_call(
        self,
        prompt: str,
        *,
        validate_response: Optional[Callable[[str], Tuple[bool, Any]]] = None,
        retry_prompt_builder: Optional[Callable[[str, Any], str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call the LLM with built-in rate-limiting, retries and validation.

        Parameters
        ----------
        prompt
            Prompt to send to the model (first attempt).
        validate_response
            Optional callable that receives the *raw* response text and returns
            ``(is_valid, details)``.  When it reports *False* and a
            *retry_prompt_builder* is supplied we will rebuild the prompt and
            retry immediately.
        retry_prompt_builder
            Callable invoked as ``retry_prompt_builder(original_prompt,
            validation_ctx)`` to generate the next-attempt prompt.
        context
            Optional context dict propagated to event listeners.
        """
        original_prompt = prompt
        current_prompt = prompt
        attempts_exceptions: List[Exception] = []

        for attempt in range(1, cfg.MAX_ATTEMPTS_PER_CALL + 1):
            start_ts = time.time()
            est_in_tokens = self.rate_limiter.estimate_tokens(current_prompt)
            await self.rate_limiter.acquire(est_in_tokens)

            try:
                async with _get_semaphore():
                    response = await self.llm.ainvoke(current_prompt)

                latency = time.time() - start_ts
                response_text = response.content.strip()

                # Usage metadata correction ----------------------------------
                usage_metadata = getattr(response, "usage_metadata", {})
                act_in_tok = usage_metadata.get("input_tokens", est_in_tokens)
                act_out_tok = usage_metadata.get(
                    "output_tokens", len(response_text) // 4
                )
                self.rate_limiter.release(act_in_tok, act_out_tok)

                # ------------------------------------------------------------------
                # Optional validation step ----------------------------------------
                # ------------------------------------------------------------------
                if validate_response is not None:
                    try:
                        is_valid, val_ctx = validate_response(response_text)
                    except Exception as exc:  # pylint: disable=broad-except
                        # Treat validator crash as invalid response
                        logger.warning("Validator raised on attempt %d: %s", attempt, exc)
                        is_valid, val_ctx = False, {"validator_exception": str(exc)}

                    if not is_valid:
                        # Validation failure ------------------------------------
                        _emit_event(
                            "attempt_error",
                            {
                                "event": "attempt_error",
                                "type": "validation",
                                "attempt": attempt,
                                "prompt": current_prompt,
                                "exception": None,
                                "validation_ctx": val_ctx,
                                "context": context,
                            },
                        )
                        # Rebuild prompt or abort --------------------------------
                        if retry_prompt_builder is None or attempt == cfg.MAX_ATTEMPTS_PER_CALL:
                            # Exhausted retries or cannot build retry prompt
                            _emit_event(
                                "error",
                                {
                                    "event": "error",
                                    "attempts": attempt,
                                    "prompt": original_prompt,
                                    "exceptions": attempts_exceptions,
                                    "validation_ctx": val_ctx,
                                    "context": context,
                                },
                            )
                            raise LLMCallError("Validation failed after maximum attempts")

                        current_prompt = retry_prompt_builder(original_prompt, val_ctx)
                        continue  # Next retry immediately

                # Success ---------------------------------------------------------
                _emit_event(
                    "success",
                    {
                        "event": "success",
                        "attempt": attempt,
                        "prompt": current_prompt,
                        "latency": latency,
                        "input_tokens": act_in_tok,
                        "output_tokens": act_out_tok,
                        "context": context,
                    },
                )
                logger.debug("LLM call succeeded in %.2fs on attempt %d", latency, attempt)
                return response_text

            except Exception as exc:  # noqa: BLE001 – we re-raise later
                self.rate_limiter.release()
                attempts_exceptions.append(exc)
                logger.error("LLM call failed on attempt %d/%d: %s", attempt, cfg.MAX_ATTEMPTS_PER_CALL, exc)
                _emit_event(
                    "attempt_error",
                    {
                        "event": "attempt_error",
                        "type": "transport",
                        "attempt": attempt,
                        "prompt": current_prompt,
                        "exception": exc,
                        "context": context,
                    },
                )
                if attempt == cfg.MAX_ATTEMPTS_PER_CALL:
                    _emit_event(
                        "error",
                        {
                            "event": "error",
                            "attempts": attempt,
                            "prompt": original_prompt,
                            "exceptions": attempts_exceptions,
                            "context": context,
                        },
                    )
                    raise LLMCallError("LLM call failed after maximum attempts") from exc
                # Else: fallthrough to next loop iteration – new attempt.


# Global singleton – instantiated lazily on first access
_global_llm_manager: Optional[LLMManager] = None


def initialize_global_llm(
    *,
    rate_limiter: Optional[RateLimiter] = None,
) -> LLMManager:
    """Create/replace the global LLM manager instance.

    Explicit arguments override the environment‐driven defaults.  The helper
    is primarily intended for test-fixtures; application code should normally
    rely on the lazy :pyfunc:`get_global_llm` accessor instead.
    """
    global _global_llm_manager  # noqa: PLW0603 – singleton pattern
    _global_llm_manager = LLMManager(rate_limiter=rate_limiter)
    return _global_llm_manager


def get_global_llm() -> LLMManager:
    """Return the (lazily-created) global LLM manager instance."""
    global _global_llm_manager  # noqa: PLW0603 – singleton pattern
    if _global_llm_manager is None:
        _global_llm_manager = LLMManager()
    return _global_llm_manager


async def safe_llm_call(
    prompt: str,
    *,
    validate_response: Optional[Callable[[str], Tuple[bool, Any]]] = None,
    retry_prompt_builder: Optional[Callable[[str, Any], str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenient wrapper around the *global* LLM manager.

    The additional parameters are forwarded 1-to-1 to
    :pyfunc:`LLMManager.safe_call`.
    """
    llm_manager = get_global_llm()
    return await llm_manager.safe_call(
        prompt,
        validate_response=validate_response,
        retry_prompt_builder=retry_prompt_builder,
        context=context,
    ) 