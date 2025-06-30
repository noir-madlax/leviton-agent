#!/usr/bin/env python3
"""
End-to-End Test: Scraping → Amazon Products → Data Transformation → Wide Table

测试完整的数据流程：
1. 使用Amazon URL爬取产品数据
2. 验证数据导入到amazon_products表
3. 验证数据转换到product_wide_table表  
4. 保存所有中间结果和日志用于调试

该测试模拟真实的生产环境工作流程。
"""

import asyncio
import logging
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from data_transformation.tests.utils.test_helpers import E2ETestRunner

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_leviton_product_url():
    """Test with Leviton product URL."""
    test_url = "https://www.amazon.com/Leviton-D26HD-2RW-Anywhere-Companions-Required/dp/B08RRM8VH5/"
    
    print("🚀 开始端到端测试...")
    print(f"URL: {test_url}")
    print(f"最大产品数: 3")
    print(f"最大评论数: 1")
    print("-" * 60)
    
    runner = E2ETestRunner(test_url, max_products=3, max_reviews=1)
    result = await runner.run_complete_test()
    
    print("\n" + "=" * 60)
    if result["status"] == "SUCCESS":
        print("🎉 测试完成！")
        print(f"状态: {result['status']}")
        print(f"批次ID: {result['batch_id']}")
        print(f"总耗时: {result['duration']:.1f}秒")
        print(f"结果保存在: {result['output_dir']}")
    else:
        print("❌ 测试失败！")
        print(f"状态: {result['status']}")
        print(f"原因: {result.get('reason', 'Unknown')}")
        print(f"详情: {result.get('details', {})}")
        print(f"结果保存在: {result['output_dir']}")
    print("=" * 60)
    
    return result


async def test_category_page_url():
    """Test with category page URL."""
    test_url = "https://www.amazon.com/b?node=166057011"
    
    print("🚀 开始分类页面测试...")
    print(f"URL: {test_url}")
    print(f"最大产品数: 5")
    print(f"最大评论数: 1")
    print("-" * 60)
    
    runner = E2ETestRunner(test_url, max_products=5, max_reviews=1)
    result = await runner.run_complete_test()
    
    print("\n" + "=" * 60)
    if result["status"] == "SUCCESS":
        print("🎉 测试完成！")
        print(f"状态: {result['status']}")
        print(f"批次ID: {result['batch_id']}")
        print(f"总耗时: {result['duration']:.1f}秒")
        print(f"结果保存在: {result['output_dir']}")
    else:
        print("❌ 测试失败！")
        print(f"状态: {result['status']}")
        print(f"原因: {result.get('reason', 'Unknown')}")
        print(f"详情: {result.get('details', {})}")
        print(f"结果保存在: {result['output_dir']}")
    print("=" * 60)
    
    return result


async def test_dimmer_switches_category():
    """Test with Dimmer Switches category URL."""
    test_url = "https://www.amazon.com/Dimmer-Switches/b/ref=dp_bc_5?ie=UTF8&node=507840"
    
    print("🚀 开始调光开关分类测试...")
    print(f"URL: {test_url}")
    print(f"最大产品数: 4")
    print(f"最大评论数: 1")
    print("-" * 60)
    
    runner = E2ETestRunner(test_url, max_products=4, max_reviews=1)
    result = await runner.run_complete_test()
    
    print("\n" + "=" * 60)
    if result["status"] == "SUCCESS":
        print("🎉 测试完成！")
        print(f"状态: {result['status']}")
        print(f"批次ID: {result['batch_id']}")
        print(f"总耗时: {result['duration']:.1f}秒")
        print(f"结果保存在: {result['output_dir']}")
    else:
        print("❌ 测试失败！")
        print(f"状态: {result['status']}")
        print(f"原因: {result.get('reason', 'Unknown')}")
        print(f"详情: {result.get('details', {})}")
        print(f"结果保存在: {result['output_dir']}")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run end-to-end tests")
    parser.add_argument(
        "--test", 
        choices=["leviton", "category", "dimmer", "all"], 
        default="leviton",
        help="Which test to run"
    )
    
    args = parser.parse_args()
    
    if args.test == "leviton":
        asyncio.run(test_leviton_product_url())
    elif args.test == "category":
        asyncio.run(test_category_page_url())
    elif args.test == "dimmer":
        asyncio.run(test_dimmer_switches_category())
    elif args.test == "all":
        print("运行所有测试...")
        asyncio.run(test_leviton_product_url())
        print("\n" + "="*60 + "\n")
        asyncio.run(test_category_page_url())
        print("\n" + "="*60 + "\n")
        asyncio.run(test_dimmer_switches_category()) 