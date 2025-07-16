#!/usr/bin/env python3
"""
测试 SupabaseQueryTool 的新 RPC 实现
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from supabase_query_tool import SupabaseQueryTool
import json

def test_supabase_query_tool():
    """测试 SupabaseQueryTool 的基本功能"""
    
    print("🔧 初始化 SupabaseQueryTool...")
    tool = SupabaseQueryTool()
    
    if not tool.supabase_client:
        print("❌ 无法初始化 Supabase 客户端")
        return
    
    print("✅ SupabaseQueryTool 初始化成功")
    
    # 测试用例
    test_cases = [
        {
            "name": "基础查询测试",
            "sql": "SELECT 1 as test_number, 'hello' as test_string",
            "should_pass": True
        },
        {
            "name": "简单表查询（如果表存在）",
            "sql": "SELECT * FROM projects LIMIT 5",
            "should_pass": True
        },
        {
            "name": "聚合查询测试",
            "sql": "SELECT COUNT(*) as total_count FROM projects",
            "should_pass": True
        },
        {
            "name": "安全测试 - INSERT 语句",
            "sql": "INSERT INTO projects (name) VALUES ('test')",
            "should_pass": False
        },
        {
            "name": "安全测试 - UPDATE 语句",
            "sql": "UPDATE projects SET name = 'test' WHERE id = 1",
            "should_pass": False
        },
        {
            "name": "安全测试 - DELETE 语句",
            "sql": "DELETE FROM projects WHERE id = 1",
            "should_pass": False
        },
        {
            "name": "安全测试 - 多语句",
            "sql": "SELECT * FROM projects; DROP TABLE projects;",
            "should_pass": False
        }
    ]
    
    print("\n🧪 开始运行测试用例...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        print(f"SQL: {test_case['sql']}")
        
        try:
            result = tool.forward(test_case['sql'])
            result_data = json.loads(result)
            
            success = result_data.get('success', False)
            
            if test_case['should_pass']:
                if success:
                    print(f"✅ 通过 - 查询成功，返回 {result_data.get('record_count', 0)} 条记录")
                    if result_data.get('data'):
                        print(f"   数据示例: {str(result_data['data'][:2])[:100]}...")
                else:
                    print(f"❌ 失败 - 预期成功但查询失败: {result_data.get('error', 'Unknown error')}")
            else:
                if not success:
                    print(f"✅ 通过 - 正确拒绝不安全查询: {result_data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ 失败 - 应该拒绝但查询成功了")
                    
        except Exception as e:
            print(f"❌ 异常 - 测试执行出错: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")

if __name__ == "__main__":
    test_supabase_query_tool()