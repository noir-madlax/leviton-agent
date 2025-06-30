#!/usr/bin/env python3
"""
Data Transformation Testing Script

This script runs comprehensive tests for the data transformation module.
It's designed to be run from the backend directory.

Usage:
    cd backend
    python data_transformation/run_tests.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import test functions
from data_transformation.tests.test_small_batch import main as run_tests

def main():
    """Run all data transformation tests."""
    print("🚀 Data Transformation Testing Suite")
    print("=" * 50)
    print("📍 Working directory:", os.getcwd())
    print("📁 Backend path:", backend_path)
    print("🐍 Python path:", sys.path[0])
    print()
    
    try:
        # Run the comprehensive test suite
        run_tests()
        print("\n🎉 All tests completed!")
        return 0
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 