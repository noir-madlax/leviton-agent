"""链式过滤器测试文件"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from backend.dashboard.charts.base_models import FiltersModel
from backend.dashboard.charts.filters.chain_filter import FilterChain, build_filtered_sql


def test_project_id_only():
    """测试只有project_id的情况"""
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"

    sql = build_filtered_sql(project_id)

    print("=== 测试1: 只有project_id ===")
    print("SQL:")
    print(sql)
    print("\n" + "="*50 + "\n")

    # 验证SQL包含必要的部分
    assert "select distinct pwt.platform_id" in sql
    assert "from product_wide_table pwt" in sql
    assert "project_extend_data ped" in sql
    assert project_id in sql


def test_all_filters():
    """测试所有过滤器都有值的情况"""
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    filters = FiltersModel(
        brands=["Leviton", "Lutron"],
        categories=["Dimmer Switches", "Light Switches"],
        extend_fields={
            "smart_capability": ["Smart", "Non-Smart"]
        }
    )

    sql = build_filtered_sql(project_id, filters)

    print("=== 测试2: 所有过滤器 ===")
    print("SQL:")
    print(sql)
    print("\n" + "="*50 + "\n")

    # 验证SQL包含所有过滤条件
    assert "pwt.brand = any" in sql
    assert "pwt.category = any" in sql
    assert "smart_capability" in sql
    assert "Leviton" in sql
    assert "Dimmer Switches" in sql


def test_partial_filters():
    """测试部分过滤器的情况"""
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    filters = FiltersModel(
        brands=["Leviton"],
        extend_fields={
            "smart_capability": "Smart",
            "energy_star": "true"
        }
    )

    sql = build_filtered_sql(project_id, filters)

    print("=== 测试3: 部分过滤器 ===")
    print("SQL:")
    print(sql)
    print("\n" + "="*50 + "\n")

    # 验证包含brand和extend_fields，但不包含category
    assert "pwt.brand = any" in sql
    assert "pwt.category = any" not in sql
    assert "smart_capability" in sql
    assert "energy_star" in sql


def test_empty_filters():
    """测试空过滤器的情况"""
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    filters = FiltersModel()  # 空的过滤器

    sql = build_filtered_sql(project_id, filters)

    print("=== 测试4: 空过滤器 ===")
    print("SQL:")
    print(sql)
    print("\n" + "="*50 + "\n")

    # 应该只包含project_id过滤
    assert "pwt.brand = any" not in sql
    assert "pwt.category = any" not in sql
    assert "smart_capability" not in sql


def test_no_filters():
    """测试没有filters参数的情况"""
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"

    sql = build_filtered_sql(project_id, None)

    print("=== 测试5: 无filters参数 ===")
    print("SQL:")
    print(sql)
    print("\n" + "="*50 + "\n")

    # 应该只包含project_id过滤
    assert "pwt.brand = any" not in sql
    assert "pwt.category = any" not in sql


def test_missing_project_id():
    """测试缺少project_id的情况"""
    try:
        sql = build_filtered_sql("", None)
        assert False, "Should raise ValueError"
    except ValueError as e:
        print("=== 测试6: 缺少project_id ===")
        print(f"正确抛出异常: {e}")
        print("\n" + "="*50 + "\n")


def run_all_tests():
    """运行所有测试"""
    print("开始运行链式过滤器测试...\n")
    
    test_project_id_only()
    test_all_filters()
    test_partial_filters()
    test_empty_filters()
    test_no_filters()
    test_missing_project_id()
    
    print("所有测试完成！")


if __name__ == "__main__":
    run_all_tests()
