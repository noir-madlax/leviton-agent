"""Configuration for review analysis LLM tests.

This module configures pytest to run the review analysis pipeline tests in the correct order:
1. Extraction stage tests first (generates data)
2. Categorization stage tests second (uses extraction data)
3. Consolidation stage tests third (uses categorization data)
4. Integration pipeline test last (orchestrates all stages)
"""

import pytest


def pytest_collection_modifyitems(config, items):
    """Modify test collection to ensure proper execution order.
    
    This function reorders tests so that:
    1. Extraction tests run first
    2. Categorization tests run second  
    3. Consolidation tests run third
    4. Integration pipeline test runs last
    """
    # Define the desired order of test modules
    module_order = [
        "test_review_extraction_stage.py",
        "test_review_categorization_stage.py", 
        "test_review_consolidation_stage.py",
        "test_pipeline_integration.py"
    ]
    
    # Group tests by module
    tests_by_module = {}
    for item in items:
        module_name = item.fspath.basename
        if module_name not in tests_by_module:
            tests_by_module[module_name] = []
        tests_by_module[module_name].append(item)
    
    # Reorder items according to module order
    ordered_items = []
    
    # Add tests in the specified order
    for module_name in module_order:
        if module_name in tests_by_module:
            ordered_items.extend(tests_by_module[module_name])
    
    # Add any remaining tests that weren't in the order list
    for module_name, module_tests in tests_by_module.items():
        if module_name not in module_order:
            ordered_items.extend(module_tests)
    
    # Replace the original items list
    items[:] = ordered_items


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment for review analysis pipeline tests."""
    print("\n" + "="*80)
    print("🔧 SETTING UP REVIEW ANALYSIS TEST ENVIRONMENT")
    print("="*80)
    print("📋 Test execution order:")
    print("   1. Extraction stage tests")
    print("   2. Categorization stage tests")
    print("   3. Consolidation stage tests") 
    print("   4. Integration pipeline test")
    print("="*80)
    
    yield
    
    print("\n" + "="*80)
    print("🧹 CLEANING UP REVIEW ANALYSIS TEST ENVIRONMENT")
    print("="*80) 