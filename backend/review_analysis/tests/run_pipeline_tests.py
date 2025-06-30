#!/usr/bin/env python3
"""Standalone test runner for review analysis pipeline.

This script runs the review analysis pipeline tests in the correct sequence:
1. Extraction stage
2. Categorization stage  
3. Consolidation stage

Usage:
    python review_analysis/tests/run_pipeline_tests.py
    
Or from the backend directory:
    python -m review_analysis.tests.run_pipeline_tests
"""

import subprocess
import sys
from pathlib import Path


def run_stage_tests(stage_name: str, test_file: str, backend_dir: Path) -> bool:
    """Run tests for a specific pipeline stage.
    
    Args:
        stage_name: Human-readable name of the stage
        test_file: Path to the test file relative to backend_dir
        backend_dir: Path to the backend directory
        
    Returns:
        True if tests passed, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"🧪 RUNNING {stage_name.upper()} STAGE TESTS")
    print(f"{'='*80}")
    print(f"📁 Test file: {test_file}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v", "-s", "--tb=short",
        "-m", "integration"  # Only run integration tests
    ]
    
    print(f"🚀 Command: {' '.join(cmd)}")
    print("-" * 80)
    
    result = subprocess.run(
        cmd,
        cwd=backend_dir,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ {stage_name} stage tests PASSED")
        return True
    else:
        print(f"❌ {stage_name} stage tests FAILED (exit code: {result.returncode})")
        return False


def main():
    """Run the complete review analysis pipeline test suite."""
    print("🚀 REVIEW ANALYSIS PIPELINE TEST RUNNER")
    print("="*80)
    
    # Get the backend directory
    backend_dir = Path(__file__).resolve().parents[2]
    print(f"📁 Backend directory: {backend_dir}")
    
    # Define the test stages in order
    stages = [
        ("Extraction", "review_analysis/tests/llm/test_review_extraction_stage.py"),
        ("Categorization", "review_analysis/tests/llm/test_review_categorization_stage.py"),
        ("Consolidation", "review_analysis/tests/llm/test_review_consolidation_stage.py"),
    ]
    
    print(f"\n📋 Pipeline stages to run:")
    for i, (stage_name, _) in enumerate(stages, 1):
        print(f"   {i}. {stage_name}")
    
    # Run each stage in sequence
    all_passed = True
    for stage_name, test_file in stages:
        success = run_stage_tests(stage_name, test_file, backend_dir)
        if not success:
            all_passed = False
            print(f"\n💥 PIPELINE FAILED at {stage_name} stage")
            print("❌ Stopping execution - fix the failing stage before continuing")
            break
    
    # Final summary
    print(f"\n{'='*80}")
    if all_passed:
        print("🎉 REVIEW ANALYSIS PIPELINE TESTS COMPLETED SUCCESSFULLY")
        print("✅ All stages passed:")
        for i, (stage_name, _) in enumerate(stages, 1):
            print(f"   {i}. ✅ {stage_name}")
    else:
        print("💥 REVIEW ANALYSIS PIPELINE TESTS FAILED")
        print("❌ Some stages failed - check the output above")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main()) 