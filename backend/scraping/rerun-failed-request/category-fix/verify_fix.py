"""
验证类别修复效果
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from core.database.connection import get_supabase_client

async def verify_category_fix():
    """验证类别修复效果"""
    logging.basicConfig(level=logging.INFO)
    
    supabase = get_supabase_client()
    
    print("=== 验证类别修复效果 ===")
    
    # 1. 检查23883894011类别是否存在
    print("\n1. 检查类别23883894011是否存在:")
    try:
        result = supabase.table('amazon_categories').select('*').eq('category_id', '23883894011').execute()
        if result.data:
            category = result.data[0]
            print(f"✅ 类别存在: {category['name']} (层级: {category['level']})")
            print(f"   完整路径: {category['full_path']}")
        else:
            print("❌ 类别不存在")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    
    # 2. 检查该类别下的产品数量
    print("\n2. 检查类别23883894011下的产品数量:")
    try:
        result = supabase.table('product_wide_table')\
            .select('platform_id', count='exact')\
            .eq('category_l6_id', '23883894011')\
            .execute()
        
        product_count = result.count or 0
        print(f"✅ 找到 {product_count} 个产品")
        
        # 显示几个产品示例
        if product_count > 0:
            sample_result = supabase.table('product_wide_table')\
                .select('platform_id, title, category')\
                .eq('category_l6_id', '23883894011')\
                .limit(3)\
                .execute()
            
            print("   产品示例:")
            for product in sample_result.data:
                print(f"   - {product['platform_id']}: {product['title'][:50]}...")
                
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    
    # 3. 模拟前端查询逻辑
    print("\n3. 模拟前端查询逻辑:")
    try:
        # 模拟 get_data_confirmation_data_by_category_id 的查询
        category_result = supabase.table('amazon_categories')\
            .select('level')\
            .eq('category_id', '23883894011')\
            .single()\
            .execute()
        
        if category_result.data:
            category_level = category_result.data['level']
            print(f"✅ 找到类别层级: {category_level}")
            
            # 使用对应的层级字段查询产品
            category_field = f'category_l{category_level}_id'
            products_result = supabase.table('product_wide_table')\
                .select('platform_id', count='exact')\
                .eq(category_field, '23883894011')\
                .execute()
            
            products_count = products_result.count or 0
            print(f"✅ 通过 {category_field} 字段查询到 {products_count} 个产品")
            
            if products_count > 0:
                print("🎉 修复成功！前端应该能正确显示产品数量了")
            else:
                print("❌ 仍然查询不到产品")
        else:
            print("❌ 类别查询失败")
            
    except Exception as e:
        print(f"❌ 模拟查询失败: {e}")
    
    print("\n=== 验证完成 ===")

if __name__ == "__main__":
    asyncio.run(verify_category_fix()) 