"""Centralised runtime configuration for backend utilities.

This module replaces scattered *default constants* with a single source of
truth that derives its values from environment variables (with safe fallbacks
for local development).

The design purposefully avoids external dependencies (e.g. *pydantic* settings)
so it can be imported very early during interpreter start‐up without risk of
heavy import graphs.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Centralised constants – *only* the Anthropic API token is read from the
# environment inside :pyclass:`backend.utils.llm_utils.LLMManager`.  Every other
# parameter is defined **statically** here for deterministic behaviour across
# environments and test runs.
# ---------------------------------------------------------------------------

# LLM model configuration ----------------------------------------------------
LLM_MODEL_NAME: str = "claude-sonnet-4-20250514"  # Anthropic Claude Sonnet v3
LLM_TEMPERATURE: float = 0.15
LLM_MAX_TOKENS: int = 8192

# Rate-limit parameters – aligned with Anthropic enterprise quota ------------
MAX_REQUESTS_PER_MINUTE: int = 1_900 # Slightly below 2_000 limit
MAX_INPUT_TOKENS_PER_MINUTE: int = 75_000 # Slightly below 80_000 limit
MAX_OUTPUT_TOKENS_PER_MINUTE: int = 30_000 # Slightly below 32_000 limit
MAX_CONCURRENT_REQUESTS: int = 20 # Concurrent request limit

__all__ = [
    "LLM_MODEL_NAME",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "MAX_REQUESTS_PER_MINUTE",
    "MAX_INPUT_TOKENS_PER_MINUTE",
    "MAX_OUTPUT_TOKENS_PER_MINUTE",
    "MAX_CONCURRENT_REQUESTS",
] 