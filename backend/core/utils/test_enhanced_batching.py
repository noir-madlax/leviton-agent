"""Unit tests for enhanced batching functionality with character count limits."""

import pytest
import pandas as pd
from typing import List, Dict, Any

from core.utils.batching import make_batches


class TestEnhancedBatching:
    """Test suite for enhanced batching with character count limits."""

    def test_make_batches_with_char_limit_list(self):
        """Test batching with character count limits for lists."""
        # Create test data with varying character counts
        test_data = [
            "short",           # 5 chars
            "medium length",   # 13 chars
            "very long text that exceeds the limit",  # 35 chars
            "another short",   # 14 chars
            "medium",          # 6 chars
            "longer text here",  # 16 chars
        ]
        
        def char_count_func(item: str) -> int:
            return len(item)
        
        # Test with max_chars=20 and target_batch_size=3
        batches = make_batches(
            test_data, 
            target_batch_size=3, 
            max_chars=20, 
            char_count_func=char_count_func
        )
        
        print(f"\n🔍 Character-based batching test:")
        print(f"   Input: {len(test_data)} items")
        print(f"   Max chars per batch: 20")
        print(f"   Target batch size: 3")
        print(f"   Result: {len(batches)} batches")
        
        # Validate batches
        for i, batch in enumerate(batches):
            batch_chars = sum(len(item) for item in batch)
            print(f"   Batch {i+1}: {len(batch)} items, {batch_chars} chars")
            # Allow oversized items to be in their own batch (single item)
            if len(batch) == 1 and batch_chars > 20:
                print(f"   ✅ Oversized item in single-item batch: {batch[0]}")
            else:
                assert batch_chars <= 20, f"Batch {i+1} exceeds char limit: {batch_chars} > 20"
            assert len(batch) <= 3, f"Batch {i+1} exceeds size limit: {len(batch)} > 3"
        
        # Verify all items are included
        all_items = [item for batch in batches for item in batch]
        assert len(all_items) == len(test_data)
        assert set(all_items) == set(test_data)
        
        print(f"✅ Character-based batching test passed")

    def test_make_batches_with_char_limit_dataframe(self):
        """Test batching with character count limits for DataFrames."""
        # Create test DataFrame
        test_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5, 6],
            'title': ['short', 'medium length', 'very long text that exceeds the limit', 'another short', 'medium', 'longer text here'],
            'text': ['a', 'bb', 'ccc', 'dddd', 'eeeee', 'ffffff']
        })
        
        def char_count_func(row: pd.Series) -> int:
            return len(str(row['title'])) + len(str(row['text']))
        
        # Test with max_chars=25 and target_batch_size=2
        batches = make_batches(
            test_data, 
            target_batch_size=2, 
            max_chars=25, 
            char_count_func=char_count_func
        )
        
        print(f"\n🔍 DataFrame character-based batching test:")
        print(f"   Input: {len(test_data)} rows")
        print(f"   Max chars per batch: 25")
        print(f"   Target batch size: 2")
        print(f"   Result: {len(batches)} batches")
        
        # Validate batches
        for i, batch in enumerate(batches):
            batch_chars = sum(char_count_func(row) for _, row in batch.iterrows())
            print(f"   Batch {i+1}: {len(batch)} rows, {batch_chars} chars")
            # Allow oversized items to be in their own batch (single item)
            if len(batch) == 1 and batch_chars > 25:
                print(f"   ✅ Oversized item in single-item batch")
            else:
                assert batch_chars <= 25, f"Batch {i+1} exceeds char limit: {batch_chars} > 25"
            assert len(batch) <= 2, f"Batch {i+1} exceeds size limit: {len(batch)} > 2"
        
        # Verify all rows are included
        all_rows = pd.concat(batches, ignore_index=True)
        print(f"   Total rows in batches: {len(all_rows)}, Original: {len(test_data)}")
        assert len(all_rows) == len(test_data), f"Row count mismatch: {len(all_rows)} != {len(test_data)}"
        
        print(f"✅ DataFrame character-based batching test passed")

    def test_make_batches_fallback_to_size_only(self):
        """Test that batching falls back to size-only when max_chars is not provided."""
        test_data = ["item1", "item2", "item3", "item4", "item5"]
        
        # Test without max_chars (should use original behavior)
        batches = make_batches(test_data, target_batch_size=2)
        
        print(f"\n🔍 Fallback to size-only batching test:")
        print(f"   Input: {len(test_data)} items")
        print(f"   Target batch size: 2")
        print(f"   Result: {len(batches)} batches")
        
        # Should create batches of size 2 (with remainder)
        # Note: Due to shuffling, the exact batch count may vary, but should be reasonable
        # For 5 items with batch size 2, we expect 2-3 batches
        assert 2 <= len(batches) <= 3, f"Expected 2-3 batches, got {len(batches)}"
        
        # Verify all items are included
        all_items = [item for batch in batches for item in batch]
        assert len(all_items) == len(test_data)
        assert set(all_items) == set(test_data)
        
        print(f"✅ Fallback to size-only batching test passed")

    def test_make_batches_with_large_items(self):
        """Test batching when individual items exceed the character limit."""
        test_data = [
            "short",  # 5 chars
            "this is a very long item that exceeds the character limit by itself",  # 67 chars
            "medium",  # 6 chars
            "another very long item that also exceeds the limit individually",  # 58 chars
        ]
        
        def char_count_func(item: str) -> int:
            return len(item)
        
        # Test with max_chars=20 (smaller than some individual items)
        batches = make_batches(
            test_data, 
            target_batch_size=3, 
            max_chars=20, 
            char_count_func=char_count_func
        )
        
        print(f"\n🔍 Large items batching test:")
        print(f"   Input: {len(test_data)} items")
        print(f"   Max chars per batch: 20")
        print(f"   Target batch size: 3")
        print(f"   Result: {len(batches)} batches")
        
        # Each large item should be in its own batch
        for i, batch in enumerate(batches):
            batch_chars = sum(len(item) for item in batch)
            print(f"   Batch {i+1}: {len(batch)} items, {batch_chars} chars")
            # Allow oversized items to be in their own batch (single item)
            if len(batch) == 1 and batch_chars > 20:
                print(f"   ✅ Oversized item in single-item batch: {batch[0]}")
            else:
                assert batch_chars <= 20, f"Batch {i+1} exceeds char limit: {batch_chars} > 20"
        
        # Verify all items are included
        all_items = [item for batch in batches for item in batch]
        assert len(all_items) == len(test_data)
        assert set(all_items) == set(test_data)
        
        print(f"✅ Large items batching test passed")

    def test_make_batches_edge_cases(self):
        """Test edge cases for enhanced batching."""
        # Empty data
        empty_batches = make_batches([], target_batch_size=5, max_chars=100, char_count_func=len)
        assert empty_batches == []
        
        # Single item
        single_batches = make_batches(["test"], target_batch_size=5, max_chars=100, char_count_func=len)
        assert len(single_batches) == 1
        assert single_batches[0] == ["test"]
        
        # All items fit in one batch
        small_batches = make_batches(["a", "b", "c"], target_batch_size=5, max_chars=100, char_count_func=len)
        assert len(small_batches) == 1
        assert len(small_batches[0]) == 3
        
        print(f"✅ Edge cases test passed")

    def test_review_batching_simulation(self):
        """Simulate the review batching scenario from db_review_analysis.py."""
        # Simulate review data structure
        reviews = [
            {"review_title": "Great product", "review_text": "I love this light switch. It works perfectly and was easy to install."},
            {"review_title": "Easy setup", "review_text": "Simple installation process. Took only 10 minutes."},
            {"review_title": "Quality build", "review_text": "Well constructed with good materials. Feels solid and reliable."},
            {"review_title": "Good value", "review_text": "Reasonable price for the quality. Would recommend to others."},
            {"review_title": "Perfect fit", "review_text": "Fits perfectly in my existing electrical box. No modifications needed."},
            {"review_title": "Bright lights", "review_text": "The LED indicator is bright and easy to see in the dark."},
        ]
        
        def review_char_count(review: Dict[str, Any]) -> int:
            """Calculate character count for a review (same as in db_review_analysis.py)."""
            title = review.get("review_title", "") or ""
            text = review.get("review_text", "") or ""
            return len(title) + len(text)
        
        # Test with 4000 chars limit and batch size of 3
        batches = make_batches(
            reviews, 
            target_batch_size=3, 
            max_chars=4000, 
            char_count_func=review_char_count
        )
        
        print(f"\n🔍 Review batching simulation:")
        print(f"   Input: {len(reviews)} reviews")
        print(f"   Max chars per batch: 4000")
        print(f"   Target batch size: 3")
        print(f"   Result: {len(batches)} batches")
        
        # Validate batches
        for i, batch in enumerate(batches):
            batch_chars = sum(review_char_count(review) for review in batch)
            print(f"   Batch {i+1}: {len(batch)} reviews, {batch_chars} chars")
            assert batch_chars <= 4000, f"Batch {i+1} exceeds char limit: {batch_chars} > 4000"
            assert len(batch) <= 3, f"Batch {i+1} exceeds size limit: {len(batch)} > 3"
        
        # Verify all reviews are included
        all_reviews = [review for batch in batches for review in batch]
        assert len(all_reviews) == len(reviews)
        
        print(f"✅ Review batching simulation passed")


def run_enhanced_batching_tests() -> bool:
    """Execute all enhanced batching tests without pytest."""
    print("🧪 Running Enhanced Batching Tests")
    print("=" * 50)
    
    test_instance = TestEnhancedBatching()
    
    tests = [
        ("make_batches_with_char_limit_list", test_instance.test_make_batches_with_char_limit_list),
        ("make_batches_with_char_limit_dataframe", test_instance.test_make_batches_with_char_limit_dataframe),
        ("make_batches_fallback_to_size_only", test_instance.test_make_batches_fallback_to_size_only),
        ("make_batches_with_large_items", test_instance.test_make_batches_with_large_items),
        ("make_batches_edge_cases", test_instance.test_make_batches_edge_cases),
        ("review_batching_simulation", test_instance.test_review_batching_simulation),
    ]
    
    passed = 0
    for name, test_method in tests:
        try:
            test_method()
            passed += 1
            print(f"✅ PASS: {name}")
        except Exception as e:
            print(f"❌ FAIL: {name}")
            print(f"   → {e}")
    
    print(f"\n🎉 Enhanced batching tests completed: {passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == "__main__":
    run_enhanced_batching_tests() 