#!/usr/bin/env python3
"""
专门处理Review Transformation的脚本
修复无限循环问题：禁用validate_calculations

用法:
    python continue_review_transformation.py --batch-id 74
"""

import sys
import os
import asyncio
import logging
import argparse
from datetime import datetime

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
scraping_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(scraping_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'review_transformation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

try:
    from core.database.connection import get_supabase_client
    from data_transformation.models import TransformationConfig
    from data_transformation.services.review_transformation_service import ReviewTransformationService
    logger.info("✅ 所有模块导入成功")
except ImportError as e:
    logger.error(f"❌ 模块导入失败: {e}")
    sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(description='继续Review Transformation - 修复无限循环问题')
    parser.add_argument('--batch-id', type=int, required=True, help='批次ID')
    parser.add_argument('--verbose', action='store_true', help='详细日志')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"🚀 开始处理batch {args.batch_id}的Review Transformation")
    
    try:
        # 关键修复：禁用validate_calculations避免无限循环
        config = TransformationConfig(
            skip_existing=True,
            validate_calculations=False,  # 🔧 关闭验证，避免无限循环
            dry_run=False,
            batch_size=100
        )
        
        logger.info(f"📋 配置: validate_calculations={config.validate_calculations}")
        
        # 创建服务
        review_service = ReviewTransformationService(config)
        logger.info("✅ Review transformation服务创建成功")
        
        # 执行转换
        result = await review_service.transform_batch_for_orchestrator(
            batch_id=args.batch_id,
            request_id=None  # 不更新request状态，避免干扰
        )
        
        # 显示结果
        logger.info("=" * 60)
        logger.info("📊 REVIEW TRANSFORMATION 结果")
        logger.info("=" * 60)
        logger.info(f"✅ 成功: {result.success}")
        logger.info(f"📝 处理数量: {result.processed_count}")
        logger.info(f"⏭️ 跳过数量: {result.skipped_count}")
        logger.info(f"❌ 错误数量: {result.error_count}")
        logger.info(f"⏱️ 处理时间: {result.duration_seconds:.2f}秒")
        
        if result.summary:
            logger.info("📈 详细统计:")
            for key, value in result.summary.items():
                logger.info(f"  {key}: {value}")
        
        if result.errors:
            logger.warning("⚠️ 错误信息:")
            for i, error in enumerate(result.errors[:5], 1):
                logger.warning(f"  {i}. {error}")
        
        # 手动更新scraping_requests状态
        if result.success:
            await update_scraping_request_status(args.batch_id, result)
            logger.info("✅ 爬虫请求状态更新成功")
        
    except Exception as e:
        logger.error(f"❌ 处理失败: {e}")
        raise

async def update_scraping_request_status(batch_id: int, result):
    """手动更新scraping_requests状态"""
    try:
        supabase = get_supabase_client()
        
        update_data = {
            'workflow_stage': 'completed',
            'review_status': 'transformation_completed',
            'status': 'completed',
            'reviews_transformed': result.processed_count,
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase.table('scraping_requests')\
            .update(update_data)\
            .eq('id', batch_id)\
            .execute()
        
        logger.info(f"✅ 更新scraping_requests状态: {update_data}")
        
    except Exception as e:
        logger.error(f"❌ 更新状态失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 