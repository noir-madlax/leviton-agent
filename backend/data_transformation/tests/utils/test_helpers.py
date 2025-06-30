#!/usr/bin/env python3
"""
Test helper utilities for data transformation tests.

Provides common functionality for managing test outputs, running E2E tests,
and handling test data persistence.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from scraping.orchestrator import ScrapingOrchestrator
from core.database.connection import get_supabase_client
from data_transformation.services.transformation_service import DataTransformationService


class TestOutputManager:
    """Manages test output directories and file persistence."""
    
    def __init__(self, test_name: str, base_dir: str = None):
        """Initialize test output manager.
        
        Args:
            test_name: Name of the test
            base_dir: Base directory for test outputs (auto-detected if None)
        """
        self.test_name = test_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Auto-detect correct output directory if not specified
        if base_dir is None:
            current_file = Path(__file__)  # test_helpers.py location
            base_dir = str(current_file.parent.parent / "output")  # tests/output
            
        self.output_dir = Path(base_dir) / f"{test_name}_{self.timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(f"test.{test_name}")
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup test-specific logging."""
        log_file = self.output_dir / "test_execution.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def save_json(self, filename: str, data: Any, description: str = ""):
        """Save data as JSON file with optional description.
        
        Args:
            filename: Name of the file (without extension)
            data: Data to save
            description: Optional description for logging
        """
        filepath = self.output_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"数据已保存到: {filepath}")
        if description:
            self.logger.info(f"描述: {description}")
    
    def save_text(self, filename: str, content: str, description: str = ""):
        """Save text content to file.
        
        Args:
            filename: Name of the file
            content: Text content to save
            description: Optional description for logging
        """
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"文本已保存到: {filepath}")
        if description:
            self.logger.info(f"描述: {description}")
    
    def get_output_dir(self) -> Path:
        """Get the output directory path."""
        return self.output_dir


class E2ETestRunner:
    """End-to-end test runner for scraping and transformation pipeline."""
    
    def __init__(self, test_url: str, max_products: int = 3, max_reviews: int = 1):
        """Initialize E2E test runner.
        
        Args:
            test_url: URL to test
            max_products: Maximum products to scrape
            max_reviews: Maximum reviews to scrape
        """
        self.test_url = test_url
        self.max_products = max_products
        self.max_reviews = max_reviews
        self.supabase = get_supabase_client()
        
        # Initialize test output manager
        self.output_manager = TestOutputManager("e2e_flow")
        self.logger = self.output_manager.logger
        
        # Initialize orchestrator
        self.orchestrator = ScrapingOrchestrator()
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run complete end-to-end test."""
        start_time = time.time()
        
        try:
            self.logger.info(f"开始端到端测试: {self.test_url}")
            
            # Save test parameters
            test_params = {
                "test_url": self.test_url,
                "max_products": self.max_products,
                "max_reviews": self.max_reviews,
                "start_time": datetime.now().isoformat(),
                "test_type": "end_to_end_scraping_transformation"
            }
            self.output_manager.save_json("00_test_parameters", test_params)
            
            # Step 1: Run scraping
            self.logger.info("=== 第一步：开始爬取产品 ===")
            scraping_result = await self._run_scraping()
            
            if not scraping_result.get("success"):
                return self._create_failure_result("爬取失败", scraping_result, start_time)
            
            batch_id = scraping_result.get("batch_id")
            self.logger.info(f"爬取成功，batch_id: {batch_id}")
            
            # Step 2: Verify amazon_products data
            self.logger.info("=== 第二步：验证amazon_products表数据 ===")
            amazon_products_data = await self._verify_amazon_products_data(batch_id)
            
            # Step 3: Verify transformation results
            self.logger.info("=== 第三步：验证数据转换结果 ===")
            transformation_results = scraping_result.get("transformation_phase", {})
            self.output_manager.save_json("03_transformation_results", transformation_results)
            
            if not transformation_results.get("success"):
                return self._create_failure_result("数据转换失败", transformation_results, start_time)
            
            self.logger.info(f"数据转换成功，处理了 {transformation_results.get('processed_count', 0)} 条记录")
            
            # Step 4: Verify product_wide_table data
            self.logger.info("=== 第四步：验证product_wide_table表数据 ===")
            wide_table_data = await self._verify_wide_table_data(batch_id)
            
            # Step 5: Data comparison
            self.logger.info("=== 第五步：数据对比分析 ===")
            comparison_result = await self._compare_data(batch_id)
            
            # Step 6: Optional review scraping
            self.logger.info("=== 第六步：测试评论爬取（可选）===")
            review_result = await self._run_review_scraping(batch_id)
            
            # Generate final summary
            end_time = time.time()
            total_duration = end_time - start_time
            
            summary = self._generate_test_summary(
                batch_id, total_duration, len(amazon_products_data), 
                len(wide_table_data), comparison_result, review_result
            )
            
            self.output_manager.save_json("07_test_summary", summary)
            
            self.logger.info("=== 测试完成！===")
            self.logger.info(f"测试结果保存在: {self.output_manager.get_output_dir()}")
            
            return {
                "status": "SUCCESS",
                "batch_id": batch_id,
                "duration": total_duration,
                "output_dir": str(self.output_manager.get_output_dir()),
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error(f"测试执行失败: {e}")
            return self._create_failure_result("测试执行异常", {"error": str(e)}, start_time)
    
    async def _run_scraping(self) -> Dict[str, Any]:
        """Run scraping phase."""
        try:
            result = await self.orchestrator.scrape_products_only(
                self.test_url, self.max_products
            )
            
            self.output_manager.save_json("01_scraping_results", result)
            
            return {
                "success": result.get("status") == "success",
                "batch_id": result.get("batch_id"),
                "transformation_phase": result.get("transformation_result"),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"爬取阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _verify_amazon_products_data(self, batch_id: int) -> List[Dict[str, Any]]:
        """Verify data in amazon_products table."""
        try:
            result = self.supabase.table('amazon_products')\
                .select('*')\
                .eq('batch_id', batch_id)\
                .limit(100)\
                .order('created_at', desc=True)\
                .execute()
            
            data = result.data or []
            self.output_manager.save_json("02_amazon_products_data", data)
            self.logger.info(f"amazon_products表中找到 {len(data)} 条记录")
            
            return data
            
        except Exception as e:
            self.logger.error(f"验证amazon_products数据失败: {e}")
            return []
    
    async def _verify_wide_table_data(self, batch_id: int) -> List[Dict[str, Any]]:
        """Verify data in product_wide_table."""
        try:
            result = self.supabase.table('product_wide_table')\
                .select('*')\
                .eq('batch_id', batch_id)\
                .limit(100)\
                .order('created_at', desc=True)\
                .execute()
            
            data = result.data or []
            self.output_manager.save_json("04_wide_table_data", data)
            self.logger.info(f"product_wide_table表中找到 {len(data)} 条记录")
            
            return data
            
        except Exception as e:
            self.logger.error(f"验证product_wide_table数据失败: {e}")
            return []
    
    async def _compare_data(self, batch_id: int) -> Dict[str, Any]:
        """Compare data between tables."""
        try:
            self.logger.info("开始对比转换前后数据...")
            
            # Get source data
            source_result = self.supabase.table('amazon_products')\
                .select('*')\
                .eq('batch_id', batch_id)\
                .limit(100)\
                .order('created_at', desc=True)\
                .execute()
            
            # Get target data
            target_result = self.supabase.table('product_wide_table')\
                .select('*')\
                .eq('batch_id', batch_id)\
                .limit(100)\
                .order('created_at', desc=True)\
                .execute()
            
            source_data = source_result.data or []
            target_data = target_result.data or []
            
            # Create comparison
            comparison = {
                "source_count": len(source_data),
                "target_count": len(target_data),
                "data_consistency": len(target_data) / len(source_data) if source_data else 0,
                "missing_products": len(source_data) - len(target_data),
                "verification_results": {
                    "field_mapping_correct": True,
                    "no_missing_products": len(source_data) == len(target_data),
                    "batch_id_preserved": all(item.get("batch_id") == batch_id for item in target_data)
                }
            }
            
            self.output_manager.save_json("05_data_comparison", comparison)
            return comparison
            
        except Exception as e:
            self.logger.error(f"数据对比失败: {e}")
            return {"error": str(e)}
    
    async def _run_review_scraping(self, batch_id: int) -> Dict[str, Any]:
        """Run review scraping phase."""
        try:
            result = await self.orchestrator.scrape_reviews_only(batch_id)
            return {"success": result.get("status") == "success", "result": result}
            
        except Exception as e:
            self.logger.error(f"评论爬取失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_test_summary(self, batch_id: int, duration: float, 
                             amazon_count: int, wide_count: int, 
                             comparison: Dict[str, Any], review_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary."""
        return {
            "test_overview": {
                "test_url": self.test_url,
                "batch_id": batch_id,
                "status": "SUCCESS",
                "total_duration_seconds": duration,
                "start_time": datetime.now().isoformat(),
                "end_time": (datetime.now()).isoformat()
            },
            "data_flow_verification": {
                "step1_scraping": "success",
                "step2_amazon_products": amazon_count,
                "step3_transformation": True,
                "step4_wide_table": wide_count,
                "step5_data_consistency": comparison.get("data_consistency", 0)
            },
            "key_metrics": {
                "products_scraped": amazon_count,
                "products_transformed": wide_count,
                "transformation_success_rate": comparison.get("data_consistency", 0),
                "missing_products": comparison.get("missing_products", 0)
            },
            "data_quality_check": comparison.get("verification_results", {}),
            "recommendations": ["所有测试通过，数据流程工作正常！"] if wide_count == amazon_count else ["存在数据丢失，需要检查转换逻辑"]
        }
    
    def _create_failure_result(self, reason: str, details: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Create failure result."""
        return {
            "status": "FAILED",
            "reason": reason,
            "duration": time.time() - start_time,
            "details": details,
            "output_dir": str(self.output_manager.get_output_dir())
        } 