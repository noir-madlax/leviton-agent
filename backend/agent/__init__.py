"""
Agent module for AI-powered chat and tool calling functionality
"""

from .services.product_prompt_service import ProductPromptService
from .dependencies import get_product_prompt_service, get_product_prompt_repository

__all__ = [
    'ProductPromptService',
    'get_product_prompt_service',
    'get_product_prompt_repository'
] 