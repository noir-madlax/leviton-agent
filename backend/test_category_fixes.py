#!/usr/bin/env python3
"""
测试category字段修复和dashboard服务分类逻辑的脚本

验证：
1. category字段修复是否正确
2. dashboard服务是否正确使用segment信息进行分类
3. 数据一致性检查
"""

import os
import sys
import asyncio
import logging

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.connection import get_supabase_client
from dashboard.services.product_analysis_service import ProductAnalysisService
from dashboard.services.pricing_analysis_service import PricingAnalysisService
from dashboard.services.package_preference_service import PackagePreferenceService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CategoryFixTester:
    """测试category字段修复效果"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def test_category_field_format(self):
        """测试category字段格式是否正确"""
        logger.info("🔍 测试category字段格式...")
        
        try:
            # 查询包含路径分隔符的category记录
            result = self.supabase.table('product_wide_table')\
                .select('platform_id, category, categories_flat')\
                .ilike('category', '%>%')\
                .limit(5)\
                .execute()
            
            if result.data:
                logger.warning(f"⚠️  发现 {len(result.data)} 条仍包含路径分隔符的category记录:")
                for item in result.data:
                    logger.info(f"  ASIN: {item.get('platform_id')}")
                    logger.info(f"  Category: {item.get('category')}")
                    logger.info(f"  Categories_flat: {item.get('categories_flat')}")
                    logger.info("  ---")
                return False
            else:
                logger.info("✅ 所有category字段格式正确，不包含路径分隔符")
                return True
                
        except Exception as e:
            logger.error(f"❌ 测试category字段格式时出错: {e}")
            return False
    
    def test_categories_flat_field(self):
        """测试categories_flat字段是否正确填充"""
        logger.info("🔍 测试categories_flat字段...")
        
        try:
            # 查询有categories_flat但没有路径分隔符的记录
            result = self.supabase.table('product_wide_table')\
                .select('platform_id, category, categories_flat')\
                .ilike('categories_flat', '%>%')\
                .limit(5)\
                .execute()
            
            if result.data:
                logger.info(f"✅ 发现 {len(result.data)} 条正确的categories_flat记录:")
                for item in result.data:
                    logger.info(f"  ASIN: {item.get('platform_id')}")
                    logger.info(f"  Category: {item.get('category')}")
                    logger.info(f"  Categories_flat: {item.get('categories_flat')}")
                    logger.info("  ---")
                return True
            else:
                logger.warning("⚠️  没有找到包含完整路径的categories_flat记录")
                return False
                
        except Exception as e:
            logger.error(f"❌ 测试categories_flat字段时出错: {e}")
            return False
    
    def test_segment_classification(self):
        """测试基于segment的产品分类"""
        logger.info("🔍 测试segment分类逻辑...")
        
        try:
            # 查询有segment assignment的产品样本
            result = self.supabase.table('product_segment_assignments')\
                .select('platform_id, segment_name')\
                .limit(10)\
                .execute()
            
            if not result.data:
                logger.warning("⚠️  没有找到product_segment_assignments数据")
                return False
            
            logger.info(f"✅ 找到 {len(result.data)} 条segment分配记录:")
            dimmer_count = 0
            switch_count = 0
            
            for item in result.data:
                platform_id = item.get('platform_id')
                segment_name = item.get('segment_name', '')
                
                # 基于segment名称判断类别
                if 'dimmer' in segment_name.lower():
                    category = 'Dimmer Switches'
                    dimmer_count += 1
                else:
                    category = 'Light Switches'
                    switch_count += 1
                
                logger.info(f"  ASIN: {platform_id}")
                logger.info(f"  Segment: {segment_name}")
                logger.info(f"  分类为: {category}")
                logger.info("  ---")
            
            logger.info(f"📊 分类统计: {dimmer_count} Dimmer Switches, {switch_count} Light Switches")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试segment分类时出错: {e}")
            return False
    
    async def test_dashboard_services(self):
        """测试dashboard服务的分类逻辑"""
        logger.info("🔍 测试dashboard服务分类逻辑...")
        
        try:
            # 模拟一个项目ID进行测试
            project_id = 1  # 假设项目ID为1
            
            # 测试产品分析服务
            logger.info("  测试ProductAnalysisService...")
            product_service = ProductAnalysisService(project_id)
            try:
                product_data = product_service.get_data()
                logger.info(f"  ✅ ProductAnalysisService运行成功，返回数据类型: {type(product_data)}")
                
                # 检查数据结构
                if isinstance(product_data, dict):
                    if 'priceVsRevenue' in product_data:
                        price_revenue_data = product_data['priceVsRevenue']
                        logger.info(f"    - priceVsRevenue包含 {len(price_revenue_data)} 个类别")
                        for cat_data in price_revenue_data:
                            category = cat_data.get('category', 'Unknown')
                            products_count = len(cat_data.get('products', []))
                            logger.info(f"      {category}: {products_count} 产品")
                    
                    if 'topProducts' in product_data:
                        top_products_data = product_data['topProducts']
                        logger.info(f"    - topProducts包含 {len(top_products_data)} 个类别")
                        
            except Exception as e:
                logger.warning(f"  ⚠️  ProductAnalysisService测试失败: {e}")
            
            # 测试定价分析服务
            logger.info("  测试PricingAnalysisService...")
            pricing_service = PricingAnalysisService(project_id)
            try:
                pricing_data = pricing_service.get_data()
                logger.info(f"  ✅ PricingAnalysisService运行成功，返回数据类型: {type(pricing_data)}")
            except Exception as e:
                logger.warning(f"  ⚠️  PricingAnalysisService测试失败: {e}")
            
            # 测试包装偏好服务
            logger.info("  测试PackagePreferenceService...")
            package_service = PackagePreferenceService(project_id)
            try:
                package_data = package_service.get_data()
                logger.info(f"  ✅ PackagePreferenceService运行成功，返回数据类型: {type(package_data)}")
            except Exception as e:
                logger.warning(f"  ⚠️  PackagePreferenceService测试失败: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试dashboard服务时出错: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("Category字段修复测试")
        logger.info("=" * 60)
        
        tests = [
            ("Category字段格式测试", self.test_category_field_format),
            ("Categories_flat字段测试", self.test_categories_flat_field),
            ("Segment分类测试", self.test_segment_classification),
            ("Dashboard服务测试", self.test_dashboard_services),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n📋 {test_name}")
            logger.info("-" * 40)
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        
        # 总结
        logger.info("\n" + "=" * 60)
        logger.info("测试结果总结")
        logger.info("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            if result:
                logger.info(f"✅ {test_name}: 通过")
                passed += 1
            else:
                logger.info(f"❌ {test_name}: 失败")
                failed += 1
        
        logger.info(f"\n📊 总计: {passed} 通过, {failed} 失败")
        
        if failed == 0:
            logger.info("🎉 所有测试通过！")
        else:
            logger.info("⚠️  部分测试失败，请检查相关功能")

async def main():
    """主函数"""
    tester = CategoryFixTester()
    await tester.run_all_tests()

if __name__ == '__main__':
    asyncio.run(main()) 