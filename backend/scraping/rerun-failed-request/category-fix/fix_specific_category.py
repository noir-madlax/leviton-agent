"""
修复特定JSON文件的类别信息
处理 amazon_category_cat_6478740011_20250712_231601.json 文件
"""
import asyncio
import logging
from pathlib import Path
from extract_categories_from_json import CategoryExtractor

async def fix_specific_category_json():
    """修复特定的JSON文件的类别信息"""
    logging.basicConfig(level=logging.INFO)
    
    # 指定要处理的JSON文件路径
    json_file_path = Path(__file__).parent.parent.parent / "data" / "scraped" / "amazon" / "amazon_category_cat_6478740011_20250712_231601.json"
    
    if not json_file_path.exists():
        print(f"❌ 文件不存在: {json_file_path}")
        print("请检查文件路径是否正确")
        return
    
    print(f"🎯 开始处理文件: {json_file_path}")
    print(f"📄 文件大小: {json_file_path.stat().st_size} bytes")
    
    try:
        extractor = CategoryExtractor()
        result = await extractor.process_json_file(str(json_file_path))
        
        print("\n" + "="*50)
        print("📋 处理结果:")
        print("="*50)
        print(f"✅ 状态: {result['status']}")
        print(f"💬 消息: {result['message']}")
        print(f"📊 提取的类别数: {result.get('categories_extracted', 0)}")
        print(f"💾 插入的类别数: {result.get('categories_inserted', 0)}")
        print("="*50)
        
        if result['status'] == 'success':
            print("🎉 类别信息已成功添加到数据库！")
            print("现在你应该可以创建项目了。")
        else:
            print("❌ 处理失败，请查看详细日志了解原因。")
            print("📁 查看日志文件: extract_categories_debug.log")
            
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")

if __name__ == "__main__":
    print("🚀 开始修复类别信息...")
    asyncio.run(fix_specific_category_json()) 