"""
测试类别修复功能
"""
import asyncio
import logging
from pathlib import Path
from extract_categories_from_json import CategoryExtractor

async def test_fix_specific_json():
    """测试修复特定的JSON文件"""
    logging.basicConfig(level=logging.INFO)
    
    # 指定要测试的JSON文件路径
    json_file_path = Path(__file__).parent.parent.parent / "data" / "scraped" / "amazon" / "amazon_product_cat_23883894011_20250712_162609.json"
    
    if not json_file_path.exists():
        print(f"测试文件不存在: {json_file_path}")
        return
    
    print(f"测试文件: {json_file_path}")
    
    extractor = CategoryExtractor()
    result = await extractor.process_json_file(str(json_file_path))
    
    print("测试结果:")
    print(f"- 状态: {result['status']}")
    print(f"- 消息: {result['message']}")
    print(f"- 提取的类别数: {result.get('categories_extracted', 0)}")
    print(f"- 插入的类别数: {result.get('categories_inserted', 0)}")

if __name__ == "__main__":
    asyncio.run(test_fix_specific_json()) 