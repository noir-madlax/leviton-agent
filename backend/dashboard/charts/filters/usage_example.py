"""链式过滤器使用示例"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from backend.dashboard.charts.base_models import FiltersModel
from backend.dashboard.charts.filters.chain_filter import FilterChain, build_filtered_sql
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)


def example_1_basic_usage():
    """示例1: 基础用法 - 只有project_id"""
    print("=" * 60)
    print("示例1: 基础用法 - 只有project_id")
    print("=" * 60)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    
    sql, params = build_filtered_sql(project_id)
    
    print("生成的SQL:")
    print(sql)
    print("\n参数:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()


def example_2_full_filters():
    """示例2: 完整过滤器 - 所有参数都传递"""
    print("=" * 60)
    print("示例2: 完整过滤器 - 所有参数都传递")
    print("=" * 60)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    filters = FiltersModel(
        brands=["Leviton", "Lutron"],
        categories=["Dimmer Switches", "Light Switches"],
        extend_fields={
            "smart_capability": ["Smart", "Non-Smart"]
        }
    )
    
    sql, params = build_filtered_sql(project_id, filters)
    
    print("生成的SQL:")
    print(sql)
    print("\n参数:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()


def example_3_partial_filters():
    """示例3: 部分过滤器"""
    print("=" * 60)
    print("示例3: 部分过滤器 - 只有brand和extend_fields")
    print("=" * 60)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    filters = FiltersModel(
        brands=["Leviton"],
        extend_fields={
            "smart_capability": "Smart",
            "energy_star": "true"
        }
    )
    
    sql, params = build_filtered_sql(project_id, filters)
    
    print("生成的SQL:")
    print(sql)
    print("\n参数:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()


def example_4_custom_chain():
    """示例4: 自定义过滤器链"""
    print("=" * 60)
    print("示例4: 自定义过滤器链")
    print("=" * 60)
    
    # 创建自定义过滤器链
    chain = FilterChain()
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    filters = FiltersModel(
        categories=["Light Switches"],
        extend_fields={
            "smart_capability": "Smart"
        }
    )
    
    sql, params = chain.build_sql(project_id, filters)
    
    print("生成的SQL:")
    print(sql)
    print("\n参数:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()


def example_5_in_service():
    """示例5: 在服务中使用"""
    print("=" * 60)
    print("示例5: 在服务中使用")
    print("=" * 60)
    
    class BrandAnalysisService:
        def __init__(self, project_id: str):
            self.project_id = project_id
        
        def get_filtered_asins(self, filters: FiltersModel = None):
            """获取过滤后的ASIN列表"""
            # 使用链式过滤器构建SQL
            sql, params = build_filtered_sql(self.project_id, filters)
            
            # 这里可以执行SQL查询
            print("在服务中执行的SQL:")
            print(sql)
            print("\n参数:")
            for key, value in params.items():
                print(f"  {key}: {value}")
            
            # 模拟返回结果
            return ["B001", "B002", "B003"]
    
    # 使用服务
    service = BrandAnalysisService("d2c02b80-4c82-44cc-8093-56708a7883f7")
    filters = FiltersModel(
        brands=["Leviton"],
        categories=["Dimmer Switches"]
    )
    
    asins = service.get_filtered_asins(filters)
    print(f"\n返回的ASINs: {asins}")
    print()


def example_6_supabase_integration():
    """示例6: 与Supabase集成"""
    print("=" * 60)
    print("示例6: 与Supabase集成示例")
    print("=" * 60)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    filters = FiltersModel(
        brands=["Leviton", "Lutron"],
        extend_fields={
            "smart_capability": "Smart"
        }
    )
    
    sql, params = build_filtered_sql(project_id, filters)
    
    print("Supabase RPC调用示例:")
    print("```python")
    print("# 使用链式过滤器生成的SQL和参数")
    print("result = supabase.rpc('execute_safe_query', {")
    print(f"    'query_text': '''{sql}'''")
    print("}).execute()")
    print("```")
    print()
    
    print("或者使用参数化查询:")
    print("```python")
    print("result = supabase.rpc('execute_parameterized_query', {")
    print(f"    'query_text': '''{sql}''',")
    print(f"    'params': {params}")
    print("}).execute()")
    print("```")
    print()


def run_all_examples():
    """运行所有示例"""
    print("链式过滤器使用示例")
    print("=" * 60)
    print()
    
    example_1_basic_usage()
    example_2_full_filters()
    example_3_partial_filters()
    example_4_custom_chain()
    example_5_in_service()
    example_6_supabase_integration()
    
    print("所有示例运行完成！")


if __name__ == "__main__":
    run_all_examples()
