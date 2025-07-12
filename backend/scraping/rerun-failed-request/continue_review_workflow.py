#!/usr/bin/env python3
"""
继续完成爬虫任务的剩余步骤 - Review Scraping、Import、Transformation

用法:
    python continue_review_workflow.py --batch-id 74 --review-months 6
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
        logging.FileHandler(f'continue_review_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='继续完成爬虫任务的评论相关步骤')
    parser.add_argument('--batch-id', type=int, required=True, help='批次ID')
    parser.add_argument('--review-months', type=int, default=6, help='评论覆盖月数 (默认: 6)')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"🚀 开始继续处理批次 {args.batch_id} 的评论工作流程")
    logger.info(f"📅 评论覆盖月数: {args.review_months}")
    
    try:
        # 导入并初始化 orchestrator
        from backend.scraping.orchestrator import ScrapingOrchestrator
        
        orchestrator = ScrapingOrchestrator()
        logger.info(f"✅ Orchestrator 初始化成功")
        
        # 调用 scrape_reviews_only 方法完成所有剩余步骤
        logger.info(f"🔄 开始执行评论工作流程...")
        start_time = datetime.now()
        
        result = await orchestrator.scrape_reviews_only(
            batch_id=args.batch_id,
            review_coverage_months=args.review_months
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"⏱️  工作流程完成，耗时: {duration:.2f}秒")
        
        # 输出结果
        if result.get("status") == "success":
            logger.info(f"🎉 批次 {args.batch_id} 的评论工作流程完成成功!")
            
            # 显示详细结果
            scraping_result = result.get("scraping_result", {})
            importing_result = result.get("importing_result", {})
            transformation_result = result.get("transformation_result", {})
            
            logger.info("📊 详细结果:")
            logger.info(f"  📥 Review Scraping: {scraping_result.get('status', 'unknown')}")
            if scraping_result.get("total_reviews_scraped"):
                logger.info(f"     - 总评论数: {scraping_result['total_reviews_scraped']}")
            if scraping_result.get("products_processed"):
                logger.info(f"     - 处理产品数: {scraping_result['products_processed']}")
            
            logger.info(f"  📤 Review Import: {importing_result.get('status', 'unknown')}")
            if importing_result.get("reviews_imported"):
                logger.info(f"     - 导入评论数: {importing_result['reviews_imported']}")
            
            logger.info(f"  🔄 Review Transformation: {'success' if transformation_result.get('success') else 'failed'}")
            if transformation_result.get("processed_count"):
                logger.info(f"     - 转换记录数: {transformation_result['processed_count']}")
            if transformation_result.get("duration_seconds"):
                logger.info(f"     - 转换耗时: {transformation_result['duration_seconds']:.2f}秒")
            
        else:
            logger.error(f"❌ 批次 {args.batch_id} 的评论工作流程失败:")
            logger.error(f"   状态: {result.get('status')}")
            
            if result.get("error"):
                logger.error(f"   错误: {result['error']}")
            
            # 显示各阶段的详细错误
            if "scraping_result" in result:
                scraping_result = result["scraping_result"]
                if scraping_result.get("status") not in ["success", "partial_success"]:
                    logger.error(f"   Scraping 错误: {scraping_result.get('message', 'Unknown')}")
            
            if "importing_result" in result:
                importing_result = result["importing_result"]
                if importing_result.get("status") != "success":
                    logger.error(f"   Import 错误: {importing_result.get('message', 'Unknown')}")
            
            if "transformation_result" in result:
                transformation_result = result["transformation_result"]
                if not transformation_result.get("success"):
                    logger.error(f"   Transformation 错误: {transformation_result.get('error', 'Unknown')}")
                    if transformation_result.get("errors"):
                        logger.error(f"   详细错误: {transformation_result['errors'][:3]}")
        
        # 始终显示完整的结果数据供调试
        logger.info("🔍 完整结果数据:")
        logger.info(f"{result}")
        
    except ImportError as e:
        logger.error(f"❌ 导入错误: {e}")
        logger.error("请确保项目依赖已正确安装")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 执行过程中发生异常: {e}")
        logger.error("详细错误信息:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 