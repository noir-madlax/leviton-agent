from fastapi import Depends
from supabase import Client
from .database.connection import get_supabase_client
from .repositories.product_prompt_repository import ProductPromptRepository
from .services.product_prompt_service import ProductPromptService

def get_product_prompt_repository(
    supabase_client: Client = Depends(get_supabase_client)
) -> ProductPromptRepository:
    """依赖注入：获取 ProductPrompt 仓库"""
    return ProductPromptRepository(supabase_client)

def get_product_prompt_service(
    repository: ProductPromptRepository = Depends(get_product_prompt_repository)
) -> ProductPromptService:
    """依赖注入：获取 ProductPrompt 服务"""
    return ProductPromptService(repository) 