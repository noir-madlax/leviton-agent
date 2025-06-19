from supabase import create_client, Client
import logging
from backend.config import settings

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Supabase 连接管理器"""
    
    def __init__(self):
        self._client: Client = None
        
    def get_client(self) -> Client:
        """获取 Supabase 客户端（用户级别的操作）"""
        if self._client is None:
            try:
                self._client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("Supabase 客户端初始化成功")
            except Exception as e:
                logger.error(f"Supabase 客户端初始化失败: {e}")
                raise
        
        return self._client
    
    def get_service_client(self) -> Client:
        """获取具有服务密钥的 Supabase 客户端（用于服务端操作）"""
        try:
            # 使用 service key 以获得更高权限
            service_key = settings.SUPABASE_SERVICE_KEY if hasattr(settings, 'SUPABASE_SERVICE_KEY') and settings.SUPABASE_SERVICE_KEY else settings.SUPABASE_KEY
            
            client = create_client(
                settings.SUPABASE_URL,
                service_key
            )
            
            logger.info(f"Supabase 服务客户端初始化成功，使用的KEY类型: {'SERVICE_KEY' if service_key != settings.SUPABASE_KEY else 'ANON_KEY'}")
            return client
            
        except Exception as e:
            logger.error(f"Supabase 服务客户端初始化失败: {e}")
            raise

# 全局 Supabase 管理器实例
supabase_manager = SupabaseManager()

def get_supabase_client() -> Client:
    """获取 Supabase 客户端（用于依赖注入）"""
    return supabase_manager.get_client()

def get_supabase_service_client() -> Client:
    """获取 Supabase 服务客户端（用于依赖注入）"""
    return supabase_manager.get_service_client() 