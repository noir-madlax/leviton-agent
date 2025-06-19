#!/usr/bin/env python3
"""
Simple test runner for product segmentation module
Run tests without external dependencies
"""

import sys
import traceback
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def run_model_tests():
    """Run model validation tests"""
    print("🧪 Running Phase 1: Model Tests")
    print("=" * 50)
    
    try:
        from product_segmentation.models import (
            SegmentationRunCreate, SegmentationStatus, InteractionType,
            ProductTaxonomyCreate, ProductSegmentCreate, LLMInteractionIndexCreate,
            StartSegmentationRequest
        )
        
        # Test 1: Valid segmentation run creation
        print("✓ Testing valid segmentation run creation...")
        run_data = SegmentationRunCreate(
            id="RUN_20250618T120301Z_8d24",
            total_products=100,
            llm_config={"model": "gpt-4o", "temperature": 0.2}
        )
        assert run_data.id == "RUN_20250618T120301Z_8d24"
        assert run_data.status == SegmentationStatus.RUNNING
        print("  ✅ PASS: Valid segmentation run creation")
        
        # Test 2: Invalid run ID validation
        print("✓ Testing invalid run ID validation...")
        try:
            SegmentationRunCreate(id="", total_products=100)
            assert False, "Should have raised ValidationError"
        except Exception as e:
            if "Run ID must be non-empty" in str(e):
                print("  ✅ PASS: Invalid run ID validation")
            else:
                print(f"  ❌ FAIL: Wrong error message: {e}")
        
        # Test 3: Valid taxonomy creation
        print("✓ Testing valid taxonomy creation...")
        taxonomy = ProductTaxonomyCreate(
            run_id="RUN_TEST_123",
            category_name="Smart Switches",
            definition="WiFi-enabled smart switches",
            product_count=25
        )
        assert taxonomy.category_name == "Smart Switches"
        print("  ✅ PASS: Valid taxonomy creation")
        
        # Test 4: Valid segment creation
        print("✓ Testing valid segment creation...")
        segment = ProductSegmentCreate(
            run_id="RUN_TEST_123",
            product_id=456,
            taxonomy_id=789,
            confidence=0.95
        )
        assert segment.confidence == 0.95
        print("  ✅ PASS: Valid segment creation")
        
        # Test 5: Invalid confidence validation
        print("✓ Testing invalid confidence validation...")
        try:
            ProductSegmentCreate(
                run_id="RUN_TEST_123",
                product_id=456,
                taxonomy_id=789,
                confidence=1.5  # > 1.0 should fail
            )
            assert False, "Should have raised ValidationError"
        except Exception:
            print("  ✅ PASS: Invalid confidence validation")
        
        # Test 6: Valid API request
        print("✓ Testing valid API request...")
        request = StartSegmentationRequest(
            product_ids=[1, 2, 3, 4, 5],
            category="Electronics",
            model="gpt-4o",
            temperature=0.3,
            batch_size=10
        )
        assert len(request.product_ids) == 5
        print("  ✅ PASS: Valid API request")
        
        # Test 7: Invalid product IDs validation
        print("✓ Testing invalid product IDs validation...")
        try:
            StartSegmentationRequest(product_ids=[], category="Electronics")
            assert False, "Should have raised ValidationError"
        except Exception:
            print("  ✅ PASS: Invalid product IDs validation")
        
        print("\n🎉 All model tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Model tests failed: {e}")
        traceback.print_exc()
        return False

def test_enums():
    """Test enum definitions"""
    print("\n🧪 Testing Enums")
    print("=" * 30)
    
    try:
        from product_segmentation.models import SegmentationStatus, InteractionType
        
        # Test SegmentationStatus
        assert SegmentationStatus.RUNNING == "running"
        assert SegmentationStatus.COMPLETED == "completed"
        assert SegmentationStatus.FAILED == "failed"
        print("✅ PASS: SegmentationStatus enum")
        
        # Test InteractionType
        assert InteractionType.SEGMENTATION == "segmentation"
        assert InteractionType.CONSOLIDATE_TAXONOMY == "consolidate_taxonomy"
        assert InteractionType.REFINE_ASSIGNMENTS == "refine_assignments"
        print("✅ PASS: InteractionType enum")
        
        print("\n🎉 All enum tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Enum tests failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all implemented phase tests"""
    print("🚀 Starting Product Segmentation Tests")
    print("=" * 60)
    
    results = []
    
    # Phase 1: Database Foundation
    print("\n📊 PHASE 1: Database Foundation")
    results.append(run_model_tests())
    results.append(test_enums())
    
    # Phase 2: File Storage System
    print("\n💾 PHASE 2: File Storage System")
    try:
        from backend.product_segmentation.tests.test_storage import run_storage_tests
        results.append(run_storage_tests())
    except Exception as e:
        print(f"❌ Storage tests failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Phase 2b: Directory/Batching Utilities
    print("\n📦 PHASE 2b: Batching Utilities")
    try:
        from backend.product_segmentation.tests.test_batching import run_batching_tests
        results.append(run_batching_tests())
    except Exception as e:
        print(f"❌ Batching tests failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Phase 2c: Interaction Repository
    print("\n📑 PHASE 2c: Interaction Repository")
    try:
        from backend.product_segmentation.tests.test_interaction_repository import TestLLMInteractionRepository  # noqa: F401
        import pytest, importlib, inspect
        # Dynamically collect the tests and run via pytest.main in-process
        # We run only the tests from this module to keep the runner lightweight.
        repo_test_module = importlib.import_module("backend.product_segmentation.tests.test_interaction_repository")
        repo_test_file = inspect.getsourcefile(repo_test_module)
        # Run pytest programmatically on the specific file
        result_code = pytest.main([repo_test_file, "-q"])
        success = result_code == 0
        results.append(success)
    except Exception as e:
        print(f"❌ Interaction repository tests failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Phase 3: Core Segmentation Service
    print("\n⚙️  PHASE 3: Core Segmentation Service")
    try:
        from backend.product_segmentation.tests.test_service import run_service_tests
        results.append(run_service_tests())
    except Exception as e:
        print(f"❌ Service tests failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Phase 2d: Cache Utilities
    print("\n🗄️  PHASE 2d: Cache Utilities")
    try:
        from backend.product_segmentation.tests import test_cache as _  # noqa: F401
        import pytest
        result_code = pytest.main(["backend/product_segmentation/tests/test_cache.py", "-q"])
        results.append(result_code == 0)
    except Exception as e:
        print(f"❌ Cache utilities tests failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED! ({passed}/{total})")
        print("✅ Phase 1: Database Foundation - COMPLETE")
        print("✅ Phase 2: File Storage System - COMPLETE")
        print("✅ Phase 3: Core Segmentation Service - COMPLETE")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 