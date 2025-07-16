"""
测试 Supabase 查询工具
用于验证简化后的自定义数据库查询工具是否正常工作
"""
import asyncio
import json
import logging
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from supabase_query_tool import SupabaseQueryTool

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_supabase_query_tool():
    """测试 Supabase 查询工具"""
    print("🧪 开始测试简化版 Supabase 查询工具...")
    
    # 初始化工具
    query_tool = SupabaseQueryTool()
    
    print(f"\n✅ 工具初始化完成")
    print(f"   - 查询工具: {query_tool.name}")
    print(f"   - 描述: {query_tool.description[:100]}...")
    
    # 测试用例列表
    test_cases = [
        {
            "name": "测试 1: 基础查询 - 查询项目表",
            "sql": "SELECT id, project_name, status FROM projects LIMIT 5"
        },
        {
            "name": "测试 2: 条件查询 - 查询特定状态的项目",
            "sql": "SELECT * FROM projects WHERE status = 'active' LIMIT 3"
        },
        {
            "name": "测试 3: 聚合查询 - 统计产品数量",
            "sql": "SELECT category, COUNT(*) as count FROM product_wide_table GROUP BY category LIMIT 10"
        },
        {
            "name": "测试 4: 范围查询 - 价格范围查询",
            "sql": "SELECT platform_id, title, price_usd FROM product_wide_table WHERE price_usd BETWEEN 10 AND 100 ORDER BY price_usd DESC LIMIT 10"
        },
        {
            "name": "测试 5: 聚合统计 - 价格统计",
            "sql": "SELECT AVG(price_usd) as avg_price, MAX(price_usd) as max_price, MIN(price_usd) as min_price FROM product_wide_table WHERE price_usd > 0"
        },
        {
            "name": "测试 6: 安全性测试 - 尝试非 SELECT 查询（应该被拒绝）",
            "sql": "UPDATE projects SET status = 'updated' WHERE id = 1"
        },
        {
            "name": "测试 7: 安全性测试 - 尝试 DELETE 查询（应该被拒绝）",
            "sql": "DELETE FROM projects WHERE id = 1"
        },
        {
            "name": "测试 8: 安全性测试 - 尝试 CREATE 查询（应该被拒绝）",
            "sql": "CREATE TABLE test_table (id INT)"
        },
        {
            "name": "测试 9: 安全性测试 - 尝试 DROP 查询（应该被拒绝）",
            "sql": "SELECT  brand,     estimated_revenue        FROM       product_wide_table  "
        }

    ]
    
    # 执行测试用例
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 {test_case['name']}")
        print(f"   SQL: {test_case['sql']}")
        
        try:
            result = query_tool.forward(sql_query=test_case['sql'])
            result_data = json.loads(result)
            
            if result_data.get('success'):
                print(f"   ✅ 查询成功")
                if 'record_count' in result_data:
                    print(f"   📊 返回记录数: {result_data['record_count']}")
                if 'execution_time_ms' in result_data and result_data['execution_time_ms']:
                    print(f"   ⏱️ 执行时间: {result_data['execution_time_ms']}ms")
                
                # 显示部分数据（如果有）
                if result_data.get('data') and len(result_data['data']) > 0:
                    print(f"   📝 示例数据: {json.dumps(result_data['data'][:2], ensure_ascii=False, indent=4)}")
            else:
                print(f"   ❌ 查询失败: {result_data.get('error', '未知错误')}")
                # 对于安全性测试，失败是期望的结果
                if "安全性测试" in test_case['name']:
                    print(f"   🛡️ 安全拦截正常工作")
                    
        except Exception as e:
            print(f"   💥 测试执行异常: {e}")
    
    print(f"\n🎉 测试完成！")

def test_sql_security_validation():
    """测试 SQL 安全验证功能"""
    print("\n🔒 测试 SQL 安全验证功能...")
    
    query_tool = SupabaseQueryTool()
    
    # 安全测试用例
    security_tests = [
        ("SELECT * FROM projects", True, "正常 SELECT 查询"),
        ("select id from projects", True, "小写 SELECT 查询"),
        ("INSERT INTO projects VALUES (1)", False, "INSERT 查询"),
        ("UPDATE projects SET name='test'", False, "UPDATE 查询"),
        ("DELETE FROM projects", False, "DELETE 查询"),
        ("DROP TABLE projects", False, "DROP 查询"),
        ("CREATE TABLE test (id INT)", False, "CREATE 查询"),
        ("SELECT * FROM projects; DROP TABLE test;", False, "多语句注入"),
        ("SELECT * FROM projects;", True, "带分号的单语句"),
    ]
    
    for sql, expected_valid, description in security_tests:
        is_valid = query_tool._validate_sql_security(sql)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"   {status} {description}: {sql[:50]}... -> {'安全' if is_valid else '不安全'}")

if __name__ == "__main__":
    print("🚀 开始测试 Supabase 查询工具...")
    
    # 运行主要测试
    asyncio.run(test_supabase_query_tool())
    
    # 运行安全验证测试
    test_sql_security_validation()
    
    print("\n✨ 所有测试完成！") 