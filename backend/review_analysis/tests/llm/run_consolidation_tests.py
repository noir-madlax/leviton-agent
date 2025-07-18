#!/usr/bin/env python3
"""
Test runner for review analysis consolidation tests.

This script runs the consolidation tests in the correct order to ensure
that all required test data is available from previous stages.

Usage:
    python run_consolidation_tests.py [--generate-data] [--test-names TEST_NAMES]

Options:
    --generate-data: Run previous stages to generate test data
    --test-names: Comma-separated list of specific test names to run
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "test_data"
EXTRACTION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_extraction_results.json"
CATEGORIZATION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_categorization_results.json"
CONSOLIDATION_RESULTS_PATH = TEST_DATA_DIR / "real_amazon_consolidation_results.json"

# Test data requirements
REQUIRED_TEST_DATA = {
    "extraction": EXTRACTION_RESULTS_PATH,
    "categorization": CATEGORIZATION_RESULTS_PATH,
    "consolidation": CONSOLIDATION_RESULTS_PATH
}

def check_test_data() -> dict:
    """Check which test data files exist."""
    status = {}
    for stage, path in REQUIRED_TEST_DATA.items():
        status[stage] = path.exists()
    return status

def run_pytest_command(test_path: str, test_names: Optional[List[str]] = None, markers: Optional[List[str]] = None) -> bool:
    """Run pytest with specified parameters."""
    cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
    
    if test_names:
        for test_name in test_names:
            cmd.extend(["-k", test_name])
    
    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
    return result.returncode == 0

def generate_test_data() -> bool:
    """Generate test data by running previous stages."""
    print("🔄 Generating test data...")
    
    # Run extraction tests first
    print("\n📝 Running extraction tests...")
    if not run_pytest_command("tests/llm/test_review_extraction_stage.py", markers=["integration"]):
        print("❌ Extraction tests failed")
        return False
    
    # Run categorization tests
    print("\n🏷️ Running categorization tests...")
    if not run_pytest_command("tests/llm/test_review_categorization_stage.py", markers=["integration"]):
        print("❌ Categorization tests failed")
        return False
    
    print("✅ Test data generation completed")
    return True

def run_consolidation_tests(test_names: Optional[List[str]] = None) -> bool:
    """Run consolidation tests."""
    print("\n🔗 Running consolidation tests...")
    
    # Check if test data exists
    data_status = check_test_data()
    missing_data = [stage for stage, exists in data_status.items() if not exists]
    
    if missing_data:
        print(f"⚠️  Missing test data: {missing_data}")
        print("Run with --generate-data to create test data first")
        return False
    
    print("✅ All required test data found")
    
    # Run consolidation tests
    success = run_pytest_command(
        "tests/llm/test_review_consolidation_stage.py",
        test_names=test_names,
        markers=["integration"]
    )
    
    if success:
        print("✅ Consolidation tests completed successfully")
    else:
        print("❌ Consolidation tests failed")
    
    return success

def run_unit_tests() -> bool:
    """Run unit tests (no LLM calls)."""
    print("\n🧪 Running unit tests...")
    
    success = run_pytest_command(
        "tests/llm/test_review_consolidation_stage.py",
        markers=["not integration"]
    )
    
    if success:
        print("✅ Unit tests completed successfully")
    else:
        print("❌ Unit tests failed")
    
    return success

def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run review analysis consolidation tests")
    parser.add_argument("--generate-data", action="store_true", 
                       help="Generate test data by running previous stages")
    parser.add_argument("--test-names", type=str,
                       help="Comma-separated list of specific test names to run")
    parser.add_argument("--unit-only", action="store_true",
                       help="Run only unit tests (no LLM calls)")
    parser.add_argument("--integration-only", action="store_true",
                       help="Run only integration tests (with LLM calls)")
    
    args = parser.parse_args()
    
    print("🚀 Review Analysis Consolidation Test Runner")
    print("=" * 50)
    
    # Parse test names if provided
    test_names = None
    if args.test_names:
        test_names = [name.strip() for name in args.test_names.split(",")]
        print(f"📋 Running specific tests: {test_names}")
    
    # Check test data status
    data_status = check_test_data()
    print("\n📊 Test data status:")
    for stage, exists in data_status.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {stage}: {REQUIRED_TEST_DATA[stage].name}")
    
    # Generate data if requested or missing
    if args.generate_data or (not all(data_status.values()) and not args.unit_only):
        if not generate_test_data():
            print("❌ Failed to generate test data")
            sys.exit(1)
    
    # Run tests
    all_success = True
    
    if not args.integration_only:
        if not run_unit_tests():
            all_success = False
    
    if not args.unit_only:
        if not run_consolidation_tests(test_names):
            all_success = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("💥 Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 