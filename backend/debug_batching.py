#!/usr/bin/env python3
"""Debug script for batching logic."""

from core.utils.batching import make_batches

def debug_batching():
    """Debug the batching logic."""
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
    
    print("🔍 Debug batching:")
    print(f"   Input: {test_data}")
    print(f"   Char counts: {[char_count_func(item) for item in test_data]}")
    
    batches = make_batches(
        test_data, 
        target_batch_size=3, 
        max_chars=20, 
        char_count_func=char_count_func
    )
    
    print(f"   Result: {len(batches)} batches")
    for i, batch in enumerate(batches):
        batch_chars = sum(char_count_func(item) for item in batch)
        print(f"   Batch {i+1}: {batch} ({batch_chars} chars)")

if __name__ == "__main__":
    debug_batching() 