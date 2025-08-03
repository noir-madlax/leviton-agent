#!/usr/bin/env python3
"""Test script to validate the request model."""

import json
from dashboard.charts.reviewAnalysis.models import TopCategoriesRequest

def test_request_model():
    """Test the TopCategoriesRequest model."""
    print("🧪 Testing TopCategoriesRequest model validation")
    print("=" * 50)
    
    # Test data from the HTTP request
    test_data = {
        "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
        "filters": {},
        "date_range": None,
        "options": {
            "aspect_type": "phy_perf",
            "sort_by": "mentions",
            "sort_direction": "desc",
            "max_categories": 3,
            "min_mentions": 3
        }
    }
    
    try:
        print("📝 Test data:")
        print(json.dumps(test_data, indent=2))
        print()
        
        # Validate the request model
        print("🔍 Validating request model...")
        request = TopCategoriesRequest(**test_data)
        print("✅ Request model validation successful!")
        
        print("\n📊 Validated request:")
        print(f"   Project ID: {request.project_id}")
        print(f"   Filters: {request.filters}")
        print(f"   Date Range: {request.date_range}")
        print(f"   Options: {request.options}")
        
        # Test serialization
        print("\n🔄 Testing serialization...")
        request_dict = request.model_dump()
        print("✅ Serialization successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_request_model()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!") 