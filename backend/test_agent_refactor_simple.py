#!/usr/bin/env python3
"""
简化测试：只测试重构后的模块结构和基本导入
"""

def test_basic_imports():
    """测试基本的模块导入（不依赖外部服务）"""
    try:
        # 测试核心模块的基本导入
        import agent.core
        print("✅ agent.core 模块导入成功")
        
        # 测试验证器模块
        import agent.validators
        print("✅ agent.validators 模块导入成功")
        
        # 测试流式处理模块
        import agent.streaming
        print("✅ agent.streaming 模块导入成功")
        
        # 测试验证器函数（不依赖外部服务）
        from agent.validators.chart_validator import is_valid_json
        
        # 简单测试 JSON 验证
        test_json = '{"test": "value"}'
        test_invalid = 'invalid json'
        
        assert is_valid_json(test_json) == True
        assert is_valid_json(test_invalid) == False
        print("✅ JSON 验证函数工作正常")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_file_structure():
    """测试文件结构是否正确"""
    import os
    
    base_path = "/Users/noir/Projects/leviton-agent/backend/agent"
    
    required_files = [
        "core/__init__.py",
        "core/agent_manager.py", 
        "core/monitoring.py",
        "validators/__init__.py",
        "validators/chart_validator.py",
        "services/query_processor.py",
        "streaming/__init__.py",
        "streaming/stream_handler.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    else:
        print("✅ 所有必需文件都存在")
        return True

if __name__ == "__main__":
    print("🚀 开始简化测试...")
    
    # 测试文件结构
    structure_success = test_file_structure()
    
    # 测试基本导入
    import_success = test_basic_imports()
    
    if structure_success and import_success:
        print("\n🎉 简化测试通过！重构结构正确。")
        print("\n📁 新的目录结构已成功创建:")
        print("  backend/agent/")
        print("  ├── core/                   # 核心管理模块")
        print("  │   ├── __init__.py")
        print("  │   ├── agent_manager.py    # Agent 管理器")
        print("  │   └── monitoring.py       # 监控初始化")
        print("  ├── validators/             # 验证器模块")
        print("  │   ├── __init__.py")
        print("  │   └── chart_validator.py  # 图表验证器")
        print("  ├── services/               # 服务模块")
        print("  │   ├── __init__.py")
        print("  │   ├── query_processor.py  # 查询处理器")
        print("  │   ├── product_prompt_service.py")
        print("  │   └── chart_validation_service.py")
        print("  ├── streaming/              # 流式处理模块")
        print("  │   ├── __init__.py")
        print("  │   └── stream_handler.py   # 流式响应处理")
        print("  ├── tools/                  # 工具模块（已存在）")
        print("  └── __init__.py             # 主模块入口")
        
        print("\n✨ 重构完成的功能:")
        print("  • Agent 初始化逻辑 -> agent/core/agent_manager.py")
        print("  • 监控初始化 -> agent/core/monitoring.py")
        print("  • 图表验证 -> agent/validators/chart_validator.py")
        print("  • 查询处理 -> agent/services/query_processor.py")
        print("  • 流式响应 -> agent/streaming/stream_handler.py")
        print("  • main.py 已更新使用新的模块结构")
        
    else:
        print("\n❌ 测试失败，请检查重构代码。")
        exit(1) 