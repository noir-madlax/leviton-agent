"""
监控初始化模块 - 保持原有逻辑不变
"""
import logging
from config import settings
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

logger = logging.getLogger(__name__)

def initialize_monitoring():
    """初始化 Phoenix 监控 - 保持原有逻辑不变"""
    if settings.PHOENIX_ENDPOINT:
        try:
            tracer_provider = register(
                project_name=settings.PROJECT_NAME,
                endpoint=settings.PHOENIX_ENDPOINT
            )
            SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info(f"Phoenix 监控已启动，项目: {settings.PROJECT_NAME}, 端点: {settings.PHOENIX_ENDPOINT}")
            return True
        except Exception as e:
            logger.error(f"Phoenix 监控初始化失败: {e}", exc_info=True)
            return False
    else:
        logger.warning("未配置 PHOENIX_ENDPOINT，Phoenix 监控未启动。")
        return False 