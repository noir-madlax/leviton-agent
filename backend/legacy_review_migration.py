#!/usr/bin/env python3
"""
存量Amazon Reviews数据批量转换脚本
将amazon_reviews表中的存量数据转换到product_reviews表

功能:
1. 测试模式 - 转换少量数据验证
2. 批量模式 - 全量转换所有存量数据
3. 验证模式 - 检查转换结果
4. 回滚模式 - 清理转换数据（如需要）
"""

import sys
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.connection import get_supabase_client
from data_transformation.services.review_transformation_service import ReviewTransformationService
from data_transformation.models import TransformationConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('legacy_review_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LegacyReviewMigration:
    """存量review数据迁移工具"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.review_service = ReviewTransformationService()
        
    async def analyze_data(self) -> Dict[str, Any]:
        """分析存量数据状况"""
        logger.info("🔍 开始分析存量数据...")
        
        try:
            # 1. Amazon reviews统计 - 使用count查询避免limit限制
            amazon_count_result = self.supabase.table('amazon_reviews').select('*', count='exact').execute()
            amazon_count = amazon_count_result.count
            
            # 获取少量数据用于分析
            amazon_result = self.supabase.table('amazon_reviews').select(
                'scrape_batch_id, asin, review_id, created_at'
            ).limit(5000).execute()  # 增加limit来获取更多样本
            
            if not amazon_result.data:
                logger.warning("❌ 没有找到amazon_reviews数据")
                return {"error": "No amazon_reviews data found"}
            
            amazon_data = amazon_result.data
            unique_batches = len(set(row['scrape_batch_id'] for row in amazon_data))
            unique_asins = len(set(row['asin'] for row in amazon_data))
            
            # 2. Product reviews统计 - 使用count查询
            product_count_result = self.supabase.table('product_reviews').select('*', count='exact').execute()
            product_count = product_count_result.count
            
            # 获取少量product_reviews数据用于重叠分析
            product_result = self.supabase.table('product_reviews').select(
                'product_id, review_id, created_at'
            ).limit(5000).execute()
            
            product_data = product_result.data if product_result.data else []
            
            # 3. 检查重叠数据
            overlap_count = 0
            if product_data:
                product_review_ids = set(str(row['review_id']) for row in product_data)
                amazon_review_ids = set(row['review_id'] for row in amazon_data)
                overlap_count = len(amazon_review_ids.intersection(product_review_ids))
            
            # 4. 批次分析 - 获取唯一批次信息（简化版）
            batch_ids = list(set(row['scrape_batch_id'] for row in amazon_data))
            batch_summary = [
                {
                    'batch_id': batch_id,
                    'note': 'Sample from limited data'
                }
                for batch_id in sorted(batch_ids, reverse=True)[:10]
            ]
            
            analysis = {
                "amazon_reviews": {
                    "total_count": amazon_count,
                    "unique_batches": unique_batches,
                    "unique_asins": unique_asins,
                    "batch_range": f"{min(batch_ids)}-{max(batch_ids)}" if batch_ids else "N/A"
                },
                "product_reviews": {
                    "current_count": product_count
                },
                "migration_analysis": {
                    "overlap_count": overlap_count,
                    "new_records_to_migrate": amazon_count - overlap_count,
                    "overlap_percentage": round((overlap_count / amazon_count) * 100, 2) if amazon_count > 0 else 0
                },
                "batch_summary": batch_summary[:10],  # 显示最新10个批次
                "recommendation": self._get_migration_recommendation(amazon_count, overlap_count)
            }
            
            logger.info(f"✅ 数据分析完成:")
            logger.info(f"   📊 Amazon Reviews: {amazon_count:,} 条")
            logger.info(f"   📊 Product Reviews: {product_count:,} 条")
            logger.info(f"   🔄 需要迁移: {analysis['migration_analysis']['new_records_to_migrate']:,} 条")
            logger.info(f"   📈 重叠率: {analysis['migration_analysis']['overlap_percentage']}%")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ 数据分析失败: {e}")
            raise
    
    def _get_migration_recommendation(self, total_count: int, overlap_count: int) -> str:
        """生成迁移建议"""
        if overlap_count == 0:
            return "建议: 可以安全执行全量迁移，没有重复数据风险"
        elif overlap_count < total_count * 0.1:
            return f"建议: 有少量重复数据({overlap_count}条)，建议先测试小批量迁移"
        else:
            return f"建议: 有大量重复数据({overlap_count}条)，需要仔细检查去重策略"
    
    async def test_migration(self, test_batch_ids: List[int], limit: int = 50) -> Dict[str, Any]:
        """测试迁移 - 转换指定批次的少量数据"""
        logger.info(f"🧪 开始测试迁移 - 批次: {test_batch_ids}, 限制: {limit}条")
        
        try:
            # 配置测试模式
            config = TransformationConfig(
                skip_existing=True,
                validate_calculations=False,
                dry_run=False,  # 实际执行，但数量有限
                batch_size=20
            )
            
            total_processed = 0
            total_errors = 0
            results = []
            
            for batch_id in test_batch_ids:
                logger.info(f"🔄 处理测试批次: {batch_id}")
                
                # 使用ReviewTransformationService转换数据
                result = await self.review_service.transform_batch_reviews(
                    batch_id=batch_id,
                    config=config,
                    limit=limit  # 限制测试数量
                )
                
                batch_result = {
                    "batch_id": batch_id,
                    "success": result.success,
                    "processed_count": result.processed_count,
                    "error_count": result.error_count,
                    "duration_seconds": result.duration_seconds,
                    "errors": result.errors[:3] if result.errors else []  # 只显示前3个错误
                }
                
                results.append(batch_result)
                total_processed += result.processed_count
                total_errors += result.error_count
                
                logger.info(f"   ✅ 批次 {batch_id}: {result.processed_count}条成功, {result.error_count}条失败")
            
            test_summary = {
                "test_batches": test_batch_ids,
                "total_processed": total_processed,
                "total_errors": total_errors,
                "success_rate": round((total_processed / (total_processed + total_errors)) * 100, 2) if (total_processed + total_errors) > 0 else 0,
                "batch_results": results,
                "recommendation": "测试成功，可以继续全量迁移" if total_errors == 0 else f"发现{total_errors}个错误，建议检查后再执行全量迁移"
            }
            
            logger.info(f"🧪 测试完成: {total_processed}条成功, {total_errors}条错误")
            return test_summary
            
        except Exception as e:
            logger.error(f"❌ 测试迁移失败: {e}")
            raise
    
    async def full_migration(self, batch_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """全量迁移所有存量数据"""
        logger.info("🚀 开始全量迁移存量数据...")
        
        try:
            # 如果没有指定批次，获取所有批次
            if not batch_ids:
                result = self.supabase.table('amazon_reviews').select('scrape_batch_id').execute()
                if not result.data:
                    return {"error": "No amazon_reviews data found"}
                
                batch_ids = sorted(list(set(row['scrape_batch_id'] for row in result.data)))
                logger.info(f"📋 发现 {len(batch_ids)} 个批次: {batch_ids}")
            
            # 配置全量模式
            config = TransformationConfig(
                skip_existing=True,  # 跳过已存在的，避免重复
                validate_calculations=False,
                dry_run=False,
                batch_size=100  # 增大批次大小提高效率
            )
            
            start_time = datetime.now()
            total_processed = 0
            total_errors = 0
            failed_batches = []
            successful_batches = []
            
            for i, batch_id in enumerate(batch_ids, 1):
                logger.info(f"🔄 处理批次 {batch_id} ({i}/{len(batch_ids)})")
                
                try:
                    result = await self.review_service.transform_batch_reviews(
                        batch_id=batch_id,
                        config=config
                    )
                    
                    if result.success:
                        successful_batches.append({
                            "batch_id": batch_id,
                            "processed_count": result.processed_count,
                            "error_count": result.error_count,
                            "duration_seconds": result.duration_seconds
                        })
                        logger.info(f"   ✅ 批次 {batch_id}: {result.processed_count}条成功")
                    else:
                        failed_batches.append({
                            "batch_id": batch_id,
                            "error": result.errors[0] if result.errors else "Unknown error"
                        })
                        logger.error(f"   ❌ 批次 {batch_id}: 转换失败")
                    
                    total_processed += result.processed_count
                    total_errors += result.error_count
                    
                except Exception as e:
                    logger.error(f"   ❌ 批次 {batch_id} 处理异常: {e}")
                    failed_batches.append({
                        "batch_id": batch_id,
                        "error": str(e)
                    })
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            migration_summary = {
                "migration_type": "full",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": round(duration, 2),
                "batches_processed": len(batch_ids),
                "successful_batches": len(successful_batches),
                "failed_batches": len(failed_batches),
                "total_records_processed": total_processed,
                "total_errors": total_errors,
                "success_rate": round((total_processed / (total_processed + total_errors)) * 100, 2) if (total_processed + total_errors) > 0 else 0,
                "throughput_per_second": round(total_processed / duration, 2) if duration > 0 else 0,
                "successful_batch_details": successful_batches,
                "failed_batch_details": failed_batches,
                "status": "completed" if len(failed_batches) == 0 else "completed_with_errors"
            }
            
            logger.info(f"🎉 全量迁移完成!")
            logger.info(f"   📊 处理: {total_processed:,} 条记录")
            logger.info(f"   ⏱️  用时: {duration:.1f} 秒")
            logger.info(f"   🚀 速度: {migration_summary['throughput_per_second']:.1f} 条/秒")
            logger.info(f"   ✅ 成功率: {migration_summary['success_rate']}%")
            
            return migration_summary
            
        except Exception as e:
            logger.error(f"❌ 全量迁移失败: {e}")
            raise
    
    async def verify_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        logger.info("🔍 开始验证迁移结果...")
        
        try:
            # 1. 统计对比
            amazon_result = self.supabase.table('amazon_reviews').select('*', count='exact').execute()
            product_result = self.supabase.table('product_reviews').select('*', count='exact').execute()
            
            amazon_count = amazon_result.count
            product_count = product_result.count
            
            # 2. 抽样验证 - 检查最新5条记录
            amazon_sample = self.supabase.table('amazon_reviews').select(
                'asin, review_id, review_text, rating, verified'
            ).order('created_at', desc=True).limit(5).execute()
            
            verification_details = []
            for amazon_row in amazon_sample.data:
                # 查找对应的product_reviews记录
                # 转换review_id：如果是数字字符串则转为int，否则使用hash
                amazon_review_id = amazon_row['review_id']
                try:
                    product_review_id = int(amazon_review_id) if str(amazon_review_id).isdigit() else hash(amazon_review_id) % 2147483647
                except (ValueError, TypeError):
                    product_review_id = hash(str(amazon_review_id)) % 2147483647
                
                product_match = self.supabase.table('product_reviews').select(
                    'product_id, review_id, review_text, rating, verified'
                ).eq('product_id', amazon_row['asin']).eq('review_id', product_review_id).execute()
                
                verification_details.append({
                    "amazon_review_id": amazon_row['review_id'],
                    "amazon_asin": amazon_row['asin'],
                    "found_in_product_reviews": len(product_match.data) > 0,
                    "data_matches": len(product_match.data) > 0 and self._compare_review_data(amazon_row, product_match.data[0])
                })
            
            # 3. 计算转换率
            successfully_migrated = sum(1 for detail in verification_details if detail['found_in_product_reviews'])
            migration_rate = round((successfully_migrated / len(verification_details)) * 100, 2) if verification_details else 0
            
            verification_summary = {
                "verification_time": datetime.now().isoformat(),
                "amazon_reviews_total": amazon_count,
                "product_reviews_total": product_count,
                "sample_verification": {
                    "sample_size": len(verification_details),
                    "successfully_migrated": successfully_migrated,
                    "migration_rate": migration_rate,
                    "details": verification_details
                },
                "overall_status": "success" if migration_rate >= 80 else "needs_attention",
                "recommendation": self._get_verification_recommendation(migration_rate, amazon_count, product_count)
            }
            
            logger.info(f"🔍 验证完成:")
            logger.info(f"   📊 Amazon Reviews: {amazon_count:,} 条")
            logger.info(f"   📊 Product Reviews: {product_count:,} 条") 
            logger.info(f"   🎯 抽样迁移率: {migration_rate}%")
            
            return verification_summary
            
        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            raise
    
    def _compare_review_data(self, amazon_row: Dict, product_row: Dict) -> bool:
        """比较两条记录是否匹配"""
        try:
            return (
                amazon_row['asin'] == product_row['product_id'] and
                amazon_row['review_id'] == str(product_row['review_id']) and
                amazon_row['review_text'] == product_row['review_text'] and
                amazon_row['rating'] == product_row['rating'] and
                amazon_row['verified'] == product_row['verified']
            )
        except Exception:
            return False
    
    def _get_verification_recommendation(self, migration_rate: float, amazon_count: int, product_count: int) -> str:
        """生成验证建议"""
        if migration_rate >= 95:
            return f"✅ 迁移成功! 抽样验证率{migration_rate}%，数据质量优秀"
        elif migration_rate >= 80:
            return f"⚠️ 迁移基本成功，但有{100-migration_rate}%的数据可能有问题，建议进一步检查"
        else:
            return f"❌ 迁移存在问题，验证率仅{migration_rate}%，需要排查失败原因"


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='存量Review数据迁移工具')
    parser.add_argument('action', choices=['analyze', 'test', 'migrate', 'verify'], 
                       help='执行的操作')
    parser.add_argument('--batch-ids', type=str, 
                       help='指定批次ID，用逗号分隔 (例: 65,67,70)')
    parser.add_argument('--limit', type=int, default=50,
                       help='测试模式的记录限制 (默认: 50)')
    
    args = parser.parse_args()
    
    migration = LegacyReviewMigration()
    
    try:
        if args.action == 'analyze':
            print("🔍 分析存量数据...")
            result = await migration.analyze_data()
            print("\n📊 分析结果:")
            print(f"Amazon Reviews: {result['amazon_reviews']['total_count']:,} 条")
            print(f"Product Reviews: {result['product_reviews']['current_count']:,} 条")
            print(f"需要迁移: {result['migration_analysis']['new_records_to_migrate']:,} 条")
            print(f"建议: {result['recommendation']}")
            
        elif args.action == 'test':
            batch_ids = [65, 67, 70]  # 默认测试批次
            if args.batch_ids:
                batch_ids = [int(x.strip()) for x in args.batch_ids.split(',')]
            
            print(f"🧪 测试迁移批次: {batch_ids} (限制: {args.limit}条)")
            result = await migration.test_migration(batch_ids, args.limit)
            print(f"\n🧪 测试结果: {result['total_processed']}条成功, {result['total_errors']}条错误")
            print(f"成功率: {result['success_rate']}%")
            print(f"建议: {result['recommendation']}")
            
        elif args.action == 'migrate':
            batch_ids = None
            if args.batch_ids:
                batch_ids = [int(x.strip()) for x in args.batch_ids.split(',')]
                
            print("🚀 开始全量迁移...")
            result = await migration.full_migration(batch_ids)
            print(f"\n🎉 迁移完成!")
            print(f"处理: {result['total_records_processed']:,} 条记录")
            print(f"用时: {result['duration_seconds']:.1f} 秒")
            print(f"成功率: {result['success_rate']}%")
            
        elif args.action == 'verify':
            print("🔍 验证迁移结果...")
            result = await migration.verify_migration()
            print(f"\n🔍 验证结果:")
            print(f"Amazon Reviews: {result['amazon_reviews_total']:,} 条")
            print(f"Product Reviews: {result['product_reviews_total']:,} 条")
            print(f"抽样迁移率: {result['sample_verification']['migration_rate']}%")
            print(f"建议: {result['recommendation']}")
            
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 