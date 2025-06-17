"""
LLM utilities for model management and safe API calls.

Provides:
- LLM model initialization and management
- Safe async API calls with error handling
- Token usage tracking
"""

from typing import Dict, Any, Optional
from langchain_anthropic import ChatAnthropic
from .rate_limiter import RateLimiter


class LLMManager:
    """Manager for LLM model initialization and configuration"""
    
    def __init__(self, 
                 model_name: str = "claude-sonnet-4-20250514",
                 temperature: float = 0.15,
                 max_tokens: int = 4096,
                 rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize LLM manager
        
        Args:
            model_name: Name of the model to use
            temperature: Model temperature setting
            max_tokens: Maximum tokens per response
            rate_limiter: Optional rate limiter instance
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limiter = rate_limiter or RateLimiter(model_max_tokens=max_tokens)
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self) -> ChatAnthropic:
        """Initialize Claude model with configuration"""
        return ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
    
    async def safe_call(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Safe async LLM call with rate limiting and error handling
        
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
            actual_input_tokens = getattr(response, 'usage_metadata', {}).get('input_tokens', estimated_input_tokens)
            actual_output_tokens = getattr(response, 'usage_metadata', {}).get('output_tokens', len(response_text) // 4)
            
            self.rate_limiter.release(actual_input_tokens, actual_output_tokens)
            
            return response_text
            
        except Exception as e:
            self.rate_limiter.release()
            print(f"❌ LLM call failed: {e}")
            raise


# Global LLM manager instance
_global_llm_manager: Optional[LLMManager] = None


def initialize_global_llm(model_name: str = "claude-sonnet-4-20250514",
                         temperature: float = 0.15,
                         max_tokens: int = 4096,
                         rate_limiter: Optional[RateLimiter] = None) -> LLMManager:
    """Initialize global LLM manager"""
    global _global_llm_manager
    _global_llm_manager = LLMManager(model_name, temperature, max_tokens, rate_limiter)
    return _global_llm_manager


def get_global_llm() -> LLMManager:
    """Get global LLM manager, initializing if needed"""
    global _global_llm_manager
    if _global_llm_manager is None:
        _global_llm_manager = LLMManager()
    return _global_llm_manager


async def safe_llm_call(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Convenient function for safe LLM calls using global manager
    
    Args:
        prompt: The prompt to send to LLM
        context: Optional context for logging/caching
    
    Returns:
        LLM response text
    """
    llm_manager = get_global_llm()
    return await llm_manager.safe_call(prompt, context) 