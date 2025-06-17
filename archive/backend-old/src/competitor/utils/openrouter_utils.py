"""
OpenRouter LLM utilities - 与现有LLM接口完全兼容的OpenRouter实现

这个文件提供了一个替代的LLM实现，可以无缝替换原有的Claude调用。
使用方法：设置环境变量 USE_OPENROUTER=true 即可自动切换。

支持的模型：
- anthropic/claude-3.5-sonnet
- openai/gpt-4-turbo
- openai/gpt-4o
- meta-llama/llama-3.1-405b
等等...
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from .rate_limiter import RateLimiter


class OpenRouterManager:
    """OpenRouter LLM管理器，与现有LLMManager接口完全兼容"""
    
    def __init__(self, 
                 model_name: str = "anthropic/claude-3.5-sonnet",
                 temperature: float = 0.15,
                 max_tokens: int = 4096,
                 rate_limiter: Optional[RateLimiter] = None):
        """
        初始化OpenRouter管理器
        
        Args:
            model_name: 模型名称 (OpenRouter格式，如 anthropic/claude-3.5-sonnet)
            temperature: 温度设置
            max_tokens: 最大token数
            rate_limiter: 可选的速率限制器
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limiter = rate_limiter or RateLimiter(model_max_tokens=max_tokens)
        
        # OpenRouter API配置
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY环境变量未设置")
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/leviton-switch-demo",  # 可选：用于analytics
            "X-Title": "Leviton Switch Competitor Analysis",  # 可选：用于analytics
            "Content-Type": "application/json"
        }
    
    async def safe_call(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        安全的异步LLM调用，与现有接口完全兼容
        
        Args:
            prompt: 发送给LLM的提示
            context: 可选的上下文信息
        
        Returns:
            LLM响应文本
        """
        estimated_input_tokens = self.rate_limiter.estimate_tokens(prompt)
        
        try:
            # 获取速率限制许可
            await self.rate_limiter.acquire(estimated_input_tokens)
            
            # 准备OpenRouter API请求
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False
            }
            
            # 发送异步请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API错误 {response.status}: {error_text}")
                    
                    result = await response.json()
            
            # 提取响应内容
            response_text = result["choices"][0]["message"]["content"].strip()
            
            # 更新速率限制器的实际使用量
            actual_input_tokens = result.get("usage", {}).get("prompt_tokens", estimated_input_tokens)
            actual_output_tokens = result.get("usage", {}).get("completion_tokens", len(response_text) // 4)
            
            self.rate_limiter.release(actual_input_tokens, actual_output_tokens)
            
            return response_text
            
        except Exception as e:
            self.rate_limiter.release()
            print(f"❌ OpenRouter LLM调用失败: {e}")
            raise


class OpenRouterResponse:
    """模拟LangChain响应对象，确保兼容性"""
    
    def __init__(self, content: str, usage_metadata: Dict[str, int] = None):
        self.content = content
        self.usage_metadata = usage_metadata or {}


class OpenRouterLLM:
    """模拟LangChain ChatAnthropic接口的OpenRouter实现"""
    
    def __init__(self, model: str, temperature: float, max_tokens: int):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.manager = OpenRouterManager(model, temperature, max_tokens)
    
    async def ainvoke(self, prompt: str) -> OpenRouterResponse:
        """异步调用，模拟LangChain的ainvoke接口"""
        try:
            # 如果传入的是string，直接使用；如果是其他格式，提取content
            if hasattr(prompt, 'content'):
                prompt_text = prompt.content
            elif isinstance(prompt, str):
                prompt_text = prompt
            else:
                prompt_text = str(prompt)
            
            response_text = await self.manager.safe_call(prompt_text)
            
            # 创建兼容的响应对象
            return OpenRouterResponse(
                content=response_text,
                usage_metadata={
                    'input_tokens': self.manager.rate_limiter.estimate_tokens(prompt_text),
                    'output_tokens': self.manager.rate_limiter.estimate_tokens(response_text)
                }
            )
            
        except Exception as e:
            print(f"❌ OpenRouter ainvoke失败: {e}")
            raise


# === 智能切换机制 ===

def should_use_openrouter() -> bool:
    """检查是否应该使用OpenRouter"""
    return os.getenv("USE_OPENROUTER", "false").lower() in ("true", "1", "yes")


def get_openrouter_model_mapping(claude_model: str) -> str:
    """将Claude模型名称映射到OpenRouter模型名称"""
    mapping = {
        "claude-sonnet-4-20250514": "anthropic/claude-3.5-sonnet",
        "claude-3-sonnet": "anthropic/claude-3-sonnet",
        "claude-3-opus": "anthropic/claude-3-opus",
        "claude-3-haiku": "anthropic/claude-3-haiku",
    }
    return mapping.get(claude_model, "anthropic/claude-3.5-sonnet")


# === 兼容性包装器 ===

class CompatibleLLMManager:
    """兼容的LLM管理器，自动选择OpenRouter或原始Claude"""
    
    def __init__(self, 
                 model_name: str = "claude-sonnet-4-20250514",
                 temperature: float = 0.15,
                 max_tokens: int = 4096,
                 rate_limiter: Optional[RateLimiter] = None):
        
        if should_use_openrouter():
            print("🔀 使用OpenRouter作为LLM提供商")
            openrouter_model = get_openrouter_model_mapping(model_name)
            self.manager = OpenRouterManager(openrouter_model, temperature, max_tokens, rate_limiter)
            self.is_openrouter = True
        else:
            print("🔵 使用原始Claude API")
            # 导入原始的LLMManager
            from .llm_utils import LLMManager
            self.manager = LLMManager(model_name, temperature, max_tokens, rate_limiter)
            self.is_openrouter = False
    
    async def safe_call(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """统一的安全调用接口"""
        return await self.manager.safe_call(prompt, context)
    
    @property
    def llm(self):
        """获取底层LLM对象"""
        if self.is_openrouter:
            return OpenRouterLLM(self.manager.model_name, self.manager.temperature, self.manager.max_tokens)
        else:
            return self.manager.llm


# === 全局管理器替换函数 ===

def create_compatible_llm_manager(model_name: str = "claude-sonnet-4-20250514",
                                temperature: float = 0.15,
                                max_tokens: int = 4096,
                                rate_limiter: Optional[RateLimiter] = None):
    """创建兼容的LLM管理器"""
    return CompatibleLLMManager(model_name, temperature, max_tokens, rate_limiter)


# === 便捷的切换函数 ===

async def safe_llm_call_openrouter(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    使用OpenRouter的安全LLM调用
    这是一个独立的函数，可以直接替换原有的safe_llm_call
    """
    manager = CompatibleLLMManager()
    return await manager.safe_call(prompt, context)


# === 模型选择指南 ===

def get_recommended_models() -> Dict[str, str]:
    """获取推荐的OpenRouter模型"""
    return {
        "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",  # 推荐：平衡性能和成本
        "claude-3-opus": "anthropic/claude-3-opus",  # 最高质量，较贵
        "gpt-4-turbo": "openai/gpt-4-turbo",  # OpenAI最新模型
        "gpt-4o": "openai/gpt-4o",  # 多模态支持
        "llama-3.1-405b": "meta-llama/llama-3.1-405b",  # 开源高性能
        "gemini-pro": "google/gemini-pro",  # Google模型
    }


def print_setup_instructions():
    """打印设置说明"""
    print("""
🚀 OpenRouter设置说明：

1. 获取API Key：
   - 访问 https://openrouter.ai/
   - 注册账户并获取API密钥

2. 设置环境变量：
   export OPENROUTER_API_KEY="your-api-key"
   export USE_OPENROUTER=true

3. 选择模型（可选）：
   export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"

4. 运行脚本：
   python3 final_assign_aspects_only.py

💡 优势：
   - 支持多个AI提供商
   - 统一的API接口
   - 通常更便宜
   - 无地域限制
   - 支持更多模型选择
""")


if __name__ == "__main__":
    print_setup_instructions() 