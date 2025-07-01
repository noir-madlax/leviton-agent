#!/usr/bin/env python3
"""
修复category字段的数据修复脚本

这个脚本将：
1. 读取所有现有的product_wide_table记录
2. 将完整路径的category分解，只保留最下级类别
3. 将完整路径存储到categories_flat字段
4. 更新数据库记录

运行方式：
python backend/fix_category_fields.py --dry-run  # 试运行模式
python backend/fix_category_fields.py --execute  # 实际执行
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.connection import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CategoryFieldFixer:
    """修复category字段的工具类"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.supabase = get_supabase_client()
        
    def run(self) -> None:
        """执行修复过程"""
        logger.info("=" * 60)
        logger.info("Category字段修复工具")
        logger.info("=" * 60)
        
        if self.dry_run:
            logger.info("🔍 运行模式: 试运行 (不会修改数据)")
        else:
            logger.info("⚠️  运行模式: 实际修复 (将修改数据)")
        
        # 1. 获取需要修复的记录
        records_to_fix = self._get_records_to_fix()
        
        if not records_to_fix:
            logger.info("✅ 没有找到需要修复的记录")
            return
            
        logger.info(f"📊 找到 {len(records_to_fix)} 条需要修复的记录")
        
        # 2. 显示示例修复
        self._show_fix_examples(records_to_fix[:5])
        
        # 3. 执行修复
        if not self.dry_run:
            self._execute_fixes(records_to_fix)
        else:
            logger.info("💡 这是试运行模式，实际修复请使用 --execute 参数")
    
    def _get_records_to_fix(self) -> List[Dict[str, Any]]:
        """获取需要修复的记录"""
        try:
            # 查询包含 ' > ' 的category字段（即包含完整路径的记录）
            result = self.supabase.table('product_wide_table')\
                .select('id, platform_id, category, categories_flat')\
                .ilike('category', '%>%')\
                .execute()
            
            if result.data:
                logger.info(f"🔍 找到 {len(result.data)} 条包含完整路径的category记录")
                return result.data
            else:
                logger.info("🔍 没有找到包含完整路径的category记录")
                return []
                
        except Exception as e:
            logger.error(f"❌ 查询记录时出错: {e}")
            return []
    
    def _show_fix_examples(self, records: List[Dict[str, Any]]) -> None:
        """显示修复示例"""
        logger.info("\n📋 修复示例:")
        logger.info("-" * 80)
        
        for i, record in enumerate(records, 1):
            current_category = record.get('category', '')
            current_categories_flat = record.get('categories_flat')
            
            # 解析完整路径
            new_category, new_categories_flat = self._parse_category_path(current_category)
            
            logger.info(f"示例 {i}: ASIN {record.get('platform_id', 'Unknown')}")
            logger.info(f"  当前 category: {current_category}")
            logger.info(f"  修复后 category: {new_category}")
            logger.info(f"  当前 categories_flat: {current_categories_flat}")
            logger.info(f"  修复后 categories_flat: {new_categories_flat}")
            logger.info("")
    
    def _parse_category_path(self, category_path: str) -> tuple[str, str]:
        """解析类别路径，返回(最下级类别, 完整路径)"""
        if not category_path or ' > ' not in category_path:
            # 如果没有路径分隔符，保持原样
            return category_path, category_path
        
        # 分解路径
        parts = [part.strip() for part in category_path.split(' > ')]
        
        # 最下级类别是最后一个部分
        leaf_category = parts[-1] if parts else category_path
        
        # 完整路径就是原始字符串
        full_path = category_path
        
        return leaf_category, full_path
    
    def _execute_fixes(self, records: List[Dict[str, Any]]) -> None:
        """执行实际修复"""
        logger.info(f"\n🔧 开始修复 {len(records)} 条记录...")
        
        fixed_count = 0
        error_count = 0
        batch_size = 50
        
        # 分批处理
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_result = self._fix_batch(batch)
            fixed_count += batch_result['fixed']
            error_count += batch_result['errors']
            
            logger.info(f"📈 进度: {min(i + batch_size, len(records))}/{len(records)} "
                       f"(成功: {fixed_count}, 错误: {error_count})")
        
        logger.info(f"\n✅ 修复完成!")
        logger.info(f"📊 总结:")
        logger.info(f"  - 成功修复: {fixed_count} 条")
        logger.info(f"  - 修复失败: {error_count} 条")
        logger.info(f"  - 总计处理: {len(records)} 条")
    
    def _fix_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """修复一批记录"""
        fixed = 0
        errors = 0
        
        for record in batch:
            try:
                record_id = record['id']
                current_category = record.get('category', '')
                
                # 解析路径
                new_category, new_categories_flat = self._parse_category_path(current_category)
                
                # 更新记录
                update_data = {
                    'category': new_category,
                    'categories_flat': new_categories_flat
                }
                
                result = self.supabase.table('product_wide_table')\
                    .update(update_data)\
                    .eq('id', record_id)\
                    .execute()
                
                if result.data:
                    fixed += 1
                    logger.debug(f"✅ 成功修复记录 ID {record_id}")
                else:
                    errors += 1
                    logger.warning(f"⚠️  修复记录 ID {record_id} 时没有返回数据")
                    
            except Exception as e:
                errors += 1
                logger.error(f"❌ 修复记录 ID {record.get('id', 'Unknown')} 时出错: {e}")
        
        return {'fixed': fixed, 'errors': errors}

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='修复product_wide_table中的category字段')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='试运行模式，不会修改数据')
    group.add_argument('--execute', action='store_true', help='实际执行修复')
    
    args = parser.parse_args()
    
    # 创建修复器并运行
    fixer = CategoryFieldFixer(dry_run=args.dry_run)
    fixer.run()

if __name__ == '__main__':
    main() 