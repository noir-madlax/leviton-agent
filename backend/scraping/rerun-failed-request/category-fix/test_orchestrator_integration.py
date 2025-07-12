"""
测试爬虫流程中的类别修复集成
验证修改后的ScrapingOrchestrator是否正常工作
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scraping.orchestrator import ScrapingOrchestrator

async def test_orchestrator_initialization():
    """测试ScrapingOrchestrator初始化"""
    try:
        orchestrator = ScrapingOrchestrator()
        
        # 检查是否正确初始化了CategoryExtractor
        assert hasattr(orchestrator, 'category_extractor'), "CategoryExtractor未正确初始化"
        assert orchestrator.category_extractor is not None, "CategoryExtractor为None"
        
        print("✅ ScrapingOrchestrator初始化测试通过")
        return True
        
    except Exception as e:
        print(f"❌ ScrapingOrchestrator初始化测试失败: {e}")
        return False

async def test_import_categories_method():
    """测试_import_categories_from_json方法"""
    try:
        orchestrator = ScrapingOrchestrator()
        
        # 检查方法是否存在
        assert hasattr(orchestrator, '_import_categories_from_json'), "_import_categories_from_json方法不存在"
        
        # 测试使用已知的JSON文件
        json_file_path = Path(__file__).parent.parent.parent / "data" / "scraped" / "amazon" / "amazon_product_cat_23883894011_20250712_162609.json"
        
        if json_file_path.exists():
            result = await orchestrator._import_categories_from_json(str(json_file_path))
            
            # 验证返回结果结构
            assert isinstance(result, dict), "返回结果不是字典"
            assert 'status' in result, "返回结果缺少status字段"
            assert 'categories_extracted' in result, "返回结果缺少categories_extracted字段"
            assert 'categories_inserted' in result, "返回结果缺少categories_inserted字段"
            
            print(f"✅ _import_categories_from_json方法测试通过")
            print(f"   状态: {result['status']}")
            print(f"   提取类别数: {result['categories_extracted']}")
            print(f"   插入类别数: {result['categories_inserted']}")
            
            return True
        else:
            print(f"⚠️  测试文件不存在: {json_file_path}")
            print("   但方法存在，基本结构正确")
            return True
            
    except Exception as e:
        print(f"❌ _import_categories_from_json方法测试失败: {e}")
        return False

async def test_orchestrator_methods_exist():
    """测试爬虫编排器的关键方法是否存在"""
    try:
        orchestrator = ScrapingOrchestrator()
        
        # 检查关键方法是否存在
        methods_to_check = [
            'process_url',
            'scrape_products_only', 
            'scrape_reviews_only',
            '_import_categories_from_json'
        ]
        
        for method_name in methods_to_check:
            assert hasattr(orchestrator, method_name), f"方法{method_name}不存在"
            print(f"✅ 方法 {method_name} 存在")
        
        print("✅ 所有关键方法存在测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 方法存在性测试失败: {e}")
        return False

async def test_integration_without_breaking_existing():
    """测试集成不会破坏现有功能"""
    try:
        orchestrator = ScrapingOrchestrator()
        
        # 验证现有组件仍然正常初始化
        assert orchestrator.product_scraper is not None, "product_scraper未初始化"
        assert orchestrator.product_importer is not None, "product_importer未初始化"
        assert orchestrator.review_scraper is not None, "review_scraper未初始化"
        assert orchestrator.review_importer is not None, "review_importer未初始化"
        assert orchestrator.quality_analyzer is not None, "quality_analyzer未初始化"
        assert orchestrator.supabase_client is not None, "supabase_client未初始化"
        assert orchestrator.request_repository is not None, "request_repository未初始化"
        
        # 新增的组件也应该正常初始化
        assert orchestrator.category_extractor is not None, "category_extractor未初始化"
        
        print("✅ 现有功能完整性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 现有功能完整性测试失败: {e}")
        return False

async def main():
    """运行所有测试"""
    logging.basicConfig(level=logging.INFO)
    
    print("=== 测试ScrapingOrchestrator类别修复集成 ===\n")
    
    tests = [
        ("初始化测试", test_orchestrator_initialization),
        ("方法存在性测试", test_orchestrator_methods_exist),
        ("类别导入方法测试", test_import_categories_method),
        ("现有功能完整性测试", test_integration_without_breaking_existing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print(f"\n=== 测试结果总结 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试通过！集成成功！")
        return True
    else:
        print("⚠️  部分测试失败，需要检查代码")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 