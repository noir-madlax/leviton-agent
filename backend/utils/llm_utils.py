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
from typing import Any, Dict, Optional
from dotenv import load_dotenv, find_dotenv
from langchain_anthropic import ChatAnthropic
import json  # still used elsewhere

from utils.rate_limiter import RateLimiter
from utils import config as cfg

logger = logging.getLogger(__name__)
load_dotenv(find_dotenv())

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
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Safe async LLM call with rate limiting and error handling.
        
        Args:
            prompt: The prompt to send to LLM
            context: Optional context for logging/caching
        
        Returns:
            LLM response text
        """
        estimated_input_tokens = self.rate_limiter.estimate_tokens(prompt)

        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire(estimated_input_tokens)

            # Make async LLM call
            response = await self.llm.ainvoke(prompt)
            response_text = response.content.strip()

            # Update rate limiter with actual usage if available
            usage_metadata = getattr(response, "usage_metadata", {})
            actual_input_tokens = usage_metadata.get(
                "input_tokens", estimated_input_tokens
            )
            actual_output_tokens = usage_metadata.get(
                "output_tokens", len(response_text) // 4
            )

            self.rate_limiter.release(actual_input_tokens, actual_output_tokens)

            logger.debug(
                "LLM call successful: %d input tokens, %d output tokens",
                actual_input_tokens,
                actual_output_tokens,
            )

            return response_text

        except Exception as e:
            self.rate_limiter.release()
            logger.error("LLM call failed: %s", e)
            raise


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
    prompt: str, context: Optional[Dict[str, Any]] = None
) -> str:
    """Convenient function for safe LLM calls using global manager.
    
    Args:
        prompt: The prompt to send to LLM
        context: Optional context for logging/caching
    
    Returns:
        LLM response text
    """
    llm_manager = get_global_llm()
    return await llm_manager.safe_call(prompt, context) 