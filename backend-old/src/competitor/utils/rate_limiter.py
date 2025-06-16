"""
Rate limiting utilities for LLM API calls.

Provides token-aware rate limiting for Claude API calls with:
- Request count limiting
- Input/output token limiting
- Concurrent request limiting
- Token estimation
"""

import asyncio
import time
import tiktoken
from collections import deque
from typing import Optional


class RateLimiter:
    """Rate limiter for LLM API calls with token tracking"""
    
    def __init__(self, 
                 max_requests_per_minute: int = 1900,
                 max_input_tokens_per_minute: int = 75000,
                 max_output_tokens_per_minute: int = 30000,
                 max_concurrent_requests: int = 20,
                 model_max_tokens: int = 4096):
        """
        Initialize rate limiter with Claude Sonnet 4 defaults
        
        Args:
            max_requests_per_minute: Maximum requests per minute
            max_input_tokens_per_minute: Maximum input tokens per minute
            max_output_tokens_per_minute: Maximum output tokens per minute
            max_concurrent_requests: Maximum concurrent requests
            model_max_tokens: Maximum tokens per model call
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.max_input_tokens_per_minute = max_input_tokens_per_minute
        self.max_output_tokens_per_minute = max_output_tokens_per_minute
        self.max_concurrent_requests = max_concurrent_requests
        self.model_max_tokens = model_max_tokens
        
        self.request_times = deque()
        self.input_token_times = deque()
        self.output_token_times = deque()
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: roughly 4 characters per token
            return len(text) // 4
    
    def _clean_old_entries(self, deque_obj: deque, window_seconds: int = 60):
        """Remove entries older than window_seconds"""
        current_time = time.time()
        while deque_obj and deque_obj[0][0] < current_time - window_seconds:
            deque_obj.popleft()
    
    def _get_current_usage(self, deque_obj: deque, window_seconds: int = 60) -> int:
        """Get current usage count within window"""
        self._clean_old_entries(deque_obj, window_seconds)
        return sum(entry[1] for entry in deque_obj)
    
    async def acquire(self, estimated_input_tokens: int, estimated_output_tokens: Optional[int] = None) -> None:
        """Acquire rate limit permission before making request"""
        if estimated_output_tokens is None:
            estimated_output_tokens = self.model_max_tokens // 2  # Conservative estimate
        
        # First acquire semaphore for concurrency control
        await self.semaphore.acquire()
        
        # Then check rate limits in a loop
        while True:
            current_time = time.time()
            
            # Check current usage within the rate limit window
            current_requests = self._get_current_usage(self.request_times)
            current_input_tokens = self._get_current_usage(self.input_token_times)
            current_output_tokens = self._get_current_usage(self.output_token_times)
            
            # Calculate remaining capacity
            requests_remaining = self.max_requests_per_minute - current_requests
            input_tokens_remaining = self.max_input_tokens_per_minute - current_input_tokens
            output_tokens_remaining = self.max_output_tokens_per_minute - current_output_tokens
            
            # Check if we can make the request without exceeding any limit
            can_request = (
                requests_remaining >= 1 and
                input_tokens_remaining >= estimated_input_tokens and
                output_tokens_remaining >= estimated_output_tokens
            )
            
            if can_request:
                # Record the request immediately to prevent race conditions
                self.request_times.append((current_time, 1))
                self.input_token_times.append((current_time, estimated_input_tokens))
                self.output_token_times.append((current_time, estimated_output_tokens))
                break
            else:
                # Calculate wait time based on most constraining limit
                request_wait = 60.0 / self.max_requests_per_minute if requests_remaining < 1 else 0
                token_wait = 2.0 if (input_tokens_remaining < estimated_input_tokens or 
                                   output_tokens_remaining < estimated_output_tokens) else 0
                wait_time = max(request_wait, token_wait, 1.0)  # Minimum 1 second
                await asyncio.sleep(wait_time)
    
    def release(self, actual_input_tokens: Optional[int] = None, actual_output_tokens: Optional[int] = None):
        """Release semaphore and optionally update token counts"""
        self.semaphore.release()
        
        # Update with actual token counts if available
        if actual_input_tokens is not None or actual_output_tokens is not None:
            current_time = time.time()
            # Update the most recent entry with actual values
            if actual_input_tokens and self.input_token_times:
                self.input_token_times[-1] = (current_time, actual_input_tokens)
            if actual_output_tokens and self.output_token_times:
                self.output_token_times[-1] = (current_time, actual_output_tokens)


class SimpleRateLimiter:
    """Simple rate limiter for non-LLM async operations"""
    
    def __init__(self, max_concurrent: int = 32, delay_seconds: float = 0.1):
        """
        Initialize simple rate limiter
        
        Args:
            max_concurrent: Maximum concurrent operations
            delay_seconds: Delay between operations
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.delay_seconds = delay_seconds
    
    async def acquire(self):
        """Acquire permission for operation"""
        await self.semaphore.acquire()
        await asyncio.sleep(self.delay_seconds)
    
    def release(self):
        """Release semaphore"""
        self.semaphore.release() 