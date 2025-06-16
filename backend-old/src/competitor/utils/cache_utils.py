"""
Caching utilities for LLM responses and processing results.

Provides:
- Simple file-based caching for LLM responses
- Result caching for expensive computations
- Cache key generation
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


class CacheManager:
    """Simple file-based cache manager for LLM responses and results"""
    
    def __init__(self, cache_dir: Path, cache_type: str = "llm"):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for cache files
            cache_type: Type of cache ("llm" or "result")
        """
        self.cache_dir = cache_dir
        self.cache_type = cache_type
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_cache_key(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate cache key from content and context
        
        Args:
            content: Primary content to hash
            context: Optional context data
            
        Returns:
            Cache key string
        """
        # Combine content with sorted context for consistent hashing
        cache_input = content
        if context:
            sorted_context = json.dumps(context, sort_keys=True)
            cache_input = f"{content}|||{sorted_context}"
        
        return hashlib.sha256(cache_input.encode('utf-8')).hexdigest()[:16]
    
    def get_cache_filename(self, cache_key: str, extension: str = ".json") -> str:
        """
        Generate cache filename from key
        
        Args:
            cache_key: Cache key
            extension: File extension
            
        Returns:
            Cache filename
        """
        return f"{self.cache_type}_{cache_key}{extension}"
    
    def save_to_cache(self, key: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save data to cache
        
        Args:
            key: Cache key
            data: Data to cache
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "cache_type": self.cache_type,
                "data": data,
                "metadata": metadata or {}
            }
            
            filename = self.get_cache_filename(key)
            filepath = self.cache_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Failed to save to cache: {e}")
            return False
    
    def load_from_cache(self, key: str) -> Optional[Any]:
        """
        Load data from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        try:
            filename = self.get_cache_filename(key)
            filepath = self.cache_dir / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            return cache_data.get("data")
            
        except Exception as e:
            print(f"Failed to load from cache: {e}")
            return None
    
    def clear_cache(self) -> int:
        """
        Clear all cache files
        
        Returns:
            Number of files removed
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob(f"{self.cache_type}_*.json"):
                cache_file.unlink()
                count += 1
        except Exception as e:
            print(f"Error clearing cache: {e}")
        
        return count


class LLMCache(CacheManager):
    """Specialized cache for LLM responses"""
    
    def __init__(self, cache_dir: Path):
        super().__init__(cache_dir, "llm")
    
    def save_llm_response(self, prompt: str, response: str, 
                         context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save LLM response to cache
        
        Args:
            prompt: Input prompt
            response: LLM response
            context: Optional context data
            
        Returns:
            True if successful
        """
        cache_key = self.generate_cache_key(prompt, context)
        
        llm_data = {
            "prompt": prompt,
            "response": response,
            "prompt_length": len(prompt),
            "response_length": len(response)
        }
        
        return self.save_to_cache(cache_key, llm_data, context)
    
    def load_llm_response(self, prompt: str, 
                         context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Load LLM response from cache
        
        Args:
            prompt: Input prompt
            context: Optional context data
            
        Returns:
            Cached response or None if not found
        """
        cache_key = self.generate_cache_key(prompt, context)
        cached_data = self.load_from_cache(cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get("response")
        
        return None


class ResultCache(CacheManager):
    """Specialized cache for processing results"""
    
    def __init__(self, cache_dir: Path):
        super().__init__(cache_dir, "result")
    
    def save_processing_result(self, input_data: Any, result: Any, 
                             processing_params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save processing result to cache
        
        Args:
            input_data: Input data for processing
            result: Processing result
            processing_params: Processing parameters used
            
        Returns:
            True if successful
        """
        # Create cache key from input and parameters
        input_str = json.dumps(input_data, sort_keys=True) if not isinstance(input_data, str) else input_data
        cache_key = self.generate_cache_key(input_str, processing_params)
        
        result_data = {
            "input_data": input_data,
            "result": result,
            "processing_params": processing_params or {}
        }
        
        return self.save_to_cache(cache_key, result_data)
    
    def load_processing_result(self, input_data: Any, 
                             processing_params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Load processing result from cache
        
        Args:
            input_data: Input data for processing
            processing_params: Processing parameters used
            
        Returns:
            Cached result or None if not found
        """
        input_str = json.dumps(input_data, sort_keys=True) if not isinstance(input_data, str) else input_data
        cache_key = self.generate_cache_key(input_str, processing_params)
        cached_data = self.load_from_cache(cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get("result")
        
        return None


# Convenience functions
def create_llm_cache(cache_dir: Path) -> LLMCache:
    """Create LLM cache instance"""
    return LLMCache(cache_dir)


def create_result_cache(cache_dir: Path) -> ResultCache:
    """Create result cache instance"""
    return ResultCache(cache_dir) 