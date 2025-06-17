#!/usr/bin/env python3
"""
OpenRouter智能切换脚本

这个脚本使用monkey patching技术，在运行时动态替换LLM调用，
无需修改任何原有代码即可切换到OpenRouter。

使用方法：
1. 设置环境变量：
   export OPENROUTER_API_KEY="your-key"
   export USE_OPENROUTER=true

2. 在任何脚本前导入这个模块：
   import switch_to_openrouter  # 这会自动执行切换

3. 或者直接运行：
   python3 -c "import switch_to_openrouter; import final_assign_aspects_only; import asyncio; asyncio.run(final_assign_aspects_only.main())"
"""

import os
import sys
import importlib
from typing import Optional, Dict, Any


def monkey_patch_llm_utils():
    """动态替换llm_utils模块的函数"""
    try:
        # 检查是否应该使用OpenRouter
        if not os.getenv("USE_OPENROUTER", "false").lower() in ("true", "1", "yes"):
            print("🔵 保持使用原始Claude API (设置 USE_OPENROUTER=true 以切换)")
            return False
        
        if not os.getenv("OPENROUTER_API_KEY"):
            print("⚠️  OPENROUTER_API_KEY未设置，无法切换到OpenRouter")
            return False
        
        print("🔀 正在切换到OpenRouter...")
        
        # 导入模块
        from utils import llm_utils
        from utils.openrouter_utils import CompatibleLLMManager, safe_llm_call_openrouter
        
        # 保存原始函数（以防需要还原）
        llm_utils._original_initialize_global_llm = llm_utils.initialize_global_llm
        llm_utils._original_safe_llm_call = llm_utils.safe_llm_call
        
        # 替换函数
        def patched_initialize_global_llm(model_name: str = "claude-sonnet-4-20250514",
                                        temperature: float = 0.15,
                                        max_tokens: int = 4096,
                                        rate_limiter: Optional[Any] = None):
            """替换的初始化函数"""
            print(f"🔀 使用OpenRouter初始化LLM: {model_name}")
            manager = CompatibleLLMManager(model_name, temperature, max_tokens, rate_limiter)
            llm_utils._global_llm_manager = manager
            return manager
        
        async def patched_safe_llm_call(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
            """替换的安全调用函数"""
            return await safe_llm_call_openrouter(prompt, context)
        
        # 执行替换
        llm_utils.initialize_global_llm = patched_initialize_global_llm
        llm_utils.safe_llm_call = patched_safe_llm_call
        
        # 同时替换全局管理器
        llm_utils._global_llm_manager = None  # 强制重新初始化
        
        print("✅ 成功切换到OpenRouter！")
        print(f"🎯 使用模型: {os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')}")
        return True
        
    except ImportError as e:
        print(f"❌ 导入OpenRouter模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 切换到OpenRouter失败: {e}")
        return False


def restore_original_llm():
    """还原到原始LLM配置"""
    try:
        from utils import llm_utils
        
        if hasattr(llm_utils, '_original_initialize_global_llm'):
            llm_utils.initialize_global_llm = llm_utils._original_initialize_global_llm
            llm_utils.safe_llm_call = llm_utils._original_safe_llm_call
            llm_utils._global_llm_manager = None
            print("✅ 已还原到原始Claude API")
            return True
        else:
            print("⚠️  没有找到原始函数，无法还原")
            return False
            
    except Exception as e:
        print(f"❌ 还原失败: {e}")
        return False


def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查OpenRouter配置
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    use_openrouter = os.getenv("USE_OPENROUTER", "false").lower() in ("true", "1", "yes")
    
    print(f"   OPENROUTER_API_KEY: {'✅ 已设置' if openrouter_key else '❌ 未设置'}")
    print(f"   USE_OPENROUTER: {'✅ true' if use_openrouter else '🔵 false'}")
    
    if use_openrouter and openrouter_key:
        print("✅ OpenRouter环境配置完整")
        return True
    elif use_openrouter and not openrouter_key:
        print("❌ 缺少OPENROUTER_API_KEY")
        return False
    else:
        print("🔵 将使用原始Claude API")
        return True


def print_usage_guide():
    """打印使用指南"""
    print("""
🚀 OpenRouter切换使用指南：

=== 方法1：环境变量切换（推荐） ===
export OPENROUTER_API_KEY="your-api-key"
export USE_OPENROUTER=true
python3 final_assign_aspects_only.py

=== 方法2：临时切换 ===
USE_OPENROUTER=true OPENROUTER_API_KEY="your-key" python3 final_assign_aspects_only.py

=== 方法3：在脚本中导入切换 ===
python3 -c "
import switch_to_openrouter
import final_assign_aspects_only
import asyncio
asyncio.run(final_assign_aspects_only.main())
"

=== 方法4：交互式切换 ===
python3 switch_to_openrouter.py

🎯 支持的模型：
- anthropic/claude-3.5-sonnet (推荐)
- anthropic/claude-3-opus (最高质量) 
- openai/gpt-4-turbo
- openai/gpt-4o
- meta-llama/llama-3.1-405b
- google/gemini-pro

💡 优势：
- 🌍 无地域限制
- 💰 通常更便宜
- 🔄 支持多个AI提供商
- 🚀 统一API接口
""")


def interactive_setup():
    """交互式设置"""
    print("🛠️  OpenRouter交互式设置")
    
    # 检查当前API key
    current_key = os.getenv("OPENROUTER_API_KEY")
    if current_key:
        print(f"✅ 检测到现有API密钥: {current_key[:10]}...")
        use_existing = input("是否使用现有密钥？(y/n): ").lower().startswith('y')
        if not use_existing:
            current_key = None
    
    # 设置API key
    if not current_key:
        api_key = input("请输入OpenRouter API密钥: ").strip()
        if api_key:
            os.environ["OPENROUTER_API_KEY"] = api_key
            print("✅ API密钥已设置")
        else:
            print("❌ 未提供API密钥，退出设置")
            return False
    
    # 选择模型
    from utils.openrouter_utils import get_recommended_models
    models = get_recommended_models()
    
    print("\n🎯 选择模型:")
    for i, (name, model_id) in enumerate(models.items(), 1):
        print(f"   {i}. {name} ({model_id})")
    
    try:
        choice = int(input(f"请选择模型 (1-{len(models)}): "))
        selected_model = list(models.values())[choice - 1]
        os.environ["OPENROUTER_MODEL"] = selected_model
        print(f"✅ 已选择模型: {selected_model}")
    except (ValueError, IndexError):
        print("🔵 使用默认模型: anthropic/claude-3.5-sonnet")
    
    # 启用OpenRouter
    os.environ["USE_OPENROUTER"] = "true"
    
    # 执行切换
    if monkey_patch_llm_utils():
        print("\n✅ OpenRouter设置完成！")
        
        # 询问是否运行测试
        run_test = input("是否运行第5.4步脚本？(y/n): ").lower().startswith('y')
        if run_test:
            try:
                import final_assign_aspects_only
                import asyncio
                print("🚀 开始运行脚本...")
                asyncio.run(final_assign_aspects_only.main())
            except Exception as e:
                print(f"❌ 运行脚本失败: {e}")
        
        return True
    else:
        return False


def main():
    """主函数"""
    print("🔄 OpenRouter LLM切换工具")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            check_environment()
        elif command == "setup":
            interactive_setup()
        elif command == "restore":
            restore_original_llm()
        elif command == "guide":
            print_usage_guide()
        else:
            print(f"❌ 未知命令: {command}")
            print("可用命令: check, setup, restore, guide")
    else:
        # 默认行为：检查环境并尝试切换
        if check_environment():
            monkey_patch_llm_utils()


# 自动执行切换（当模块被导入时）
if __name__ == "__main__":
    main()
else:
    # 当作为模块导入时，自动尝试切换
    check_environment()
    monkey_patch_llm_utils() 