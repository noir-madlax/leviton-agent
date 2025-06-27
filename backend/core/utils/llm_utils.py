"""Shared LLM utilities (initialisation + safe async calls).

This module centralises *all* direct calls to the LLM so the rest of the
codebase – including unit-tests and higher-level LLM wrappers – can simply
import :pyfunc:`safe_llm_call` or grab the global manager via
:pyfunc:`get_global_llm`.

The helper re-uses the :class:`backend.utils.rate_limiter.RateLimiter`
implementation to enforce project-wide API-usage limits.
"""
import os
import logging
import json
from typing import Any, Dict, Optional, Callable, List
from dotenv import load_dotenv, find_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import re
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any

from core.utils.rate_limiter import RateLimiter
from core.utils import config as cfg

logger = logging.getLogger(__name__)
load_dotenv(find_dotenv())

# ---------------------------------------------------------------------------
# Global rate-limiter (shared across all LLM calls) --------------------------
# ---------------------------------------------------------------------------

_global_rate_limiter: Optional[RateLimiter] = None


def get_global_rate_limiter() -> RateLimiter:
    """Return a singleton :class:`RateLimiter` configured from :pymod:`config`."""
    global _global_rate_limiter  # noqa: PLW0603 – singleton pattern
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(
            max_requests_per_minute=cfg.MAX_REQUESTS_PER_MINUTE,
            max_input_tokens_per_minute=cfg.MAX_INPUT_TOKENS_PER_MINUTE,
            max_output_tokens_per_minute=cfg.MAX_OUTPUT_TOKENS_PER_MINUTE,
            max_concurrent_requests=cfg.MAX_CONCURRENT_REQUESTS,
            model_max_tokens=cfg.LLM_MAX_TOKENS,
        )
    return _global_rate_limiter


def initialize_global_rate_limiter(rate_limiter: RateLimiter) -> None:
    """Override the process-wide rate-limiter (mainly for test fixtures)."""
    global _global_rate_limiter  # noqa: PLW0603 – singleton pattern
    _global_rate_limiter = rate_limiter


@dataclass(slots=True)
class ValidationResult:
    """Validation result for LLM response."""
    ok: bool
    error_categories: Dict[str, List[str]]

def create_retry_error_details(error_categories: Dict[str, List[str]]) -> str:
    """Build the minimal context consumed by *_retry_prompt*."""
    error_details_lines: List[str] = []
    for cat, errs in error_categories.items():
        if errs:
            error_details_lines.append(f"{cat}:")
            error_details_lines.extend([f"  – {e}" for e in errs])
    error_details = "\n".join(error_details_lines)
    return error_details

class LLMCallError(RuntimeError):
    """Raised after *MAX_ATTEMPTS_PER_CALL* unsuccessful attempts."""


# 抽象LLM客户端接口
class LLMClient(ABC):
    """抽象LLM客户端接口，支持不同的LLM提供商"""
    
    @abstractmethod
    async def ainvoke(self, prompt: str) -> Any:
        """异步调用LLM"""
        pass
        
    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称"""
        pass


class AnthropicLLMClient(LLMClient):
    """Anthropic Claude客户端实现"""
    
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self.client = ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=api_key,
        )
        self._model_name = model
    
    async def ainvoke(self, prompt: str) -> Any:
        return await self.client.ainvoke(prompt)
        
    @property
    def model_name(self) -> str:
        return self._model_name


class OpenRouterLLMClient(LLMClient):
    """OpenRouter客户端实现，使用OpenAI兼容接口"""
    
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float, max_tokens: int):
        # OpenRouter使用OpenAI兼容接口
        self.client = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=api_key,
            openai_api_base=base_url,
        )
        self._model_name = model
    
    async def ainvoke(self, prompt: str) -> Any:
        return await self.client.ainvoke(prompt)
        
    @property  
    def model_name(self) -> str:
        return self._model_name


class LLMClientFactory:
    """LLM客户端工厂，根据环境变量创建合适的客户端"""
    
    @staticmethod
    def create_client(region: str, model: str, temperature: float, max_tokens: int) -> LLMClient:
        if region.lower() == 'cn':
            # CN环境使用OpenRouter
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            if not api_key:
                raise EnvironmentError(
                    "OPENROUTER_API_KEY must be set for CN region. "
                    "Please set OPENROUTER_API_KEY in your environment variables."
                )
            
            # OpenRouter中Claude模型名称映射
            # claude-sonnet-4-20250514 -> anthropic/claude-sonnet-4
            if model.startswith("claude-sonnet-4"):
                openrouter_model = "anthropic/claude-sonnet-4"
            elif model.startswith("claude-opus-4"):
                openrouter_model = "anthropic/claude-opus-4"
            elif model.startswith("claude-3-7-sonnet"):
                openrouter_model = "anthropic/claude-3.7-sonnet"
            elif model.startswith("claude-3-5-sonnet"):
                openrouter_model = "anthropic/claude-3.5-sonnet"
            else:
                # 默认映射为anthropic前缀
                openrouter_model = f"anthropic/{model}"
            
            logger.info(f"CN region: Using OpenRouter with model {openrouter_model}")
            return OpenRouterLLMClient(api_key, base_url, openrouter_model, temperature, max_tokens)
        else:
            # US环境或默认使用Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise EnvironmentError(
                    "ANTHROPIC_API_KEY must be set for US region. "
                    "Unit-tests should monkeypatch 'backend.utils.llm_utils.safe_llm_call' instead."
                )
            
            logger.info(f"US region: Using Anthropic with model {model}")
            return AnthropicLLMClient(api_key, model, temperature, max_tokens)

class LLMManager:  # pylint: disable=too-few-public-methods
    """Manager for LLM model initialization and configuration.

    All runtime parameters default to the values exported by
    :pymod:`backend.utils.config`.  Passing explicit arguments at construction
    time overrides the global configuration – this is mainly useful in unit
    tests where environment variables are *not* set.
    """

    def __init__(
        self
    ) -> None:
        """Initialize LLM manager.
        
        Args:
            rate_limiter: Optional custom :class:`RateLimiter` instance
        """
        self.model_name = cfg.LLM_MODEL_NAME
        self.temperature = cfg.LLM_TEMPERATURE
        self.max_tokens = cfg.LLM_MAX_TOKENS

        # Re-use the **global** rate-limiter unless an explicit override is provided.
        self.rate_limiter = get_global_rate_limiter()
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> LLMClient:
        """Initialize LLM client based on region configuration."""
        region = os.getenv("REGION", "us")  # 默认为us
        
        return LLMClientFactory.create_client(
            region=region,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

    async def safe_call(
        self,
        prompt: str,
        *,
        validate_response: Optional[Callable[[str], ValidationResult]] = None,
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

        # Log initial prompt and context
        logger.info("LLM call starting - Full Prompt: %s", prompt)
        if context:
            logger.info("LLM call context: %s", json.dumps(context, indent=2))

        for attempt in range(1, cfg.MAX_ATTEMPTS_PER_CALL + 1):
            await self.rate_limiter.acquire(current_prompt)

            try:
                # Concurrency is already enforced by the global *RateLimiter*; no
                # additional semaphore is required here.
                response = await self.llm.ainvoke(current_prompt)

                response_text = response.content.strip()
                # Pass raw prompt and response to rate-limiter for correction.
                self.rate_limiter.release(current_prompt, response_text)

                # Log the response
                logger.info("LLM full response (attempt %d): %s", attempt, response_text)

                # ------------------------------------------------------------------
                # Optional validation step ----------------------------------------
                # ------------------------------------------------------------------
                if validate_response is not None:
                    try:
                        validation_result = validate_response(response_text)
                    except Exception as exc:  # pylint: disable=broad-except
                        # Treat validator crash as invalid response
                        logger.warning("Validator raised on attempt %d: %s", attempt, exc)
                        validation_result = ValidationResult(ok=False, error_categories={"validator_exception": [str(exc)]})

                    if not validation_result.ok:
                        # Validation failure ------------------------------------
                        logger.warning("LLM validation failed on attempt %d: %s", attempt, json.dumps(validation_result.error_categories, indent=2))
                        
                        # Rebuild prompt or abort --------------------------------
                        if retry_prompt_builder is None or attempt == cfg.MAX_ATTEMPTS_PER_CALL:
                            # Exhausted retries or cannot build retry prompt
                            logger.error("LLM call failed after %d attempts with validation errors: %s", attempt, json.dumps(validation_result.error_categories, indent=2))
                            raise LLMCallError("Validation failed after maximum attempts")

                        current_prompt = retry_prompt_builder(original_prompt, validation_result.error_categories)
                        logger.info("Retrying with full updated prompt (attempt %d): %s", attempt + 1, current_prompt)
                        continue  # Next retry immediately

                # Success ---------------------------------------------------------
                logger.info("LLM call succeeded on attempt %d", attempt)
                return response_text

            except Exception as exc:  # noqa: BLE001 – we re-raise later
                self.rate_limiter.release()
                attempts_exceptions.append(exc)
                logger.error("LLM call failed on attempt %d/%d: %s", attempt, cfg.MAX_ATTEMPTS_PER_CALL, exc)
                
                if attempt == cfg.MAX_ATTEMPTS_PER_CALL:
                    logger.error("LLM call failed after maximum attempts. All exceptions: %s", [str(e) for e in attempts_exceptions])
                    raise LLMCallError("LLM call failed after maximum attempts") from exc
                # Else: fallthrough to next loop iteration – new attempt.


# Global singleton – instantiated lazily on first access
_global_llm_manager: Optional[LLMManager] = None


def initialize_global_llm(
    *,
    rate_limiter: Optional[RateLimiter] = None,
) -> LLMManager:
    """Create/replace the global LLM manager instance.

    If a *rate_limiter* is supplied we first register it as the process-wide
    limiter via :pyfunc:`initialize_global_rate_limiter` so that subsequent
    LLMManager instances reuse it automatically.
    """
    if rate_limiter is not None:
        initialize_global_rate_limiter(rate_limiter)

    global _global_llm_manager  # noqa: PLW0603 – singleton pattern
    _global_llm_manager = LLMManager()
    return _global_llm_manager


def get_global_llm() -> LLMManager:
    """Return the (lazily-created) global LLM manager instance."""
    global _global_llm_manager  # noqa: PLW0603 – singleton pattern
    if _global_llm_manager is None:
        _global_llm_manager = LLMManager()
    return _global_llm_manager

def extract_json(raw: str) -> str:
    """Attempt to extract the first JSON object from *raw* text."""

    # Fast-path – already valid JSON
    raw = raw.strip()
    if raw.startswith("{") and raw.endswith("}"):
        return raw

    # Otherwise try to locate a {...} block via a naive regex (balanced braces
    # would be nice but overkill here as the stage gets auto-splitting retries).
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return match.group(0)
    raise ValueError("No JSON object found in LLM response")

async def safe_llm_call(
    prompt: str,
    *,
    validate_response: Optional[Callable[[str], ValidationResult]] = None,
    retry_prompt_builder: Optional[Callable[[str, Dict[str, List[str]]], str]] = None,
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