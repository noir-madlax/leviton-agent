#!/usr/bin/env python3
"""Debug script for DataFrame batching logic."""

import pandas as pd
from core.utils.batching import make_batches

def debug_dataframe_batching():
    """Debug the DataFrame batching logic."""
    test_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6],
        'title': ['short', 'medium length', 'very long text that exceeds the limit', 'another short', 'medium', 'longer text here'],
        'text': ['a', 'bb', 'ccc', 'dddd', 'eeeee', 'ffffff']
    })
    
    def char_count_func(row: pd.Series) -> int:
        return len(str(row['title'])) + len(str(row['text']))
    
    print("🔍 Debug DataFrame batching:")
    print(f"   Input: {len(test_data)} rows")
    print(f"   Original IDs: {list(test_data['id'])}")
    print(f"   Char counts: {[char_count_func(row) for _, row in test_data.iterrows()]}")
    
    # Show shuffled data
    shuffled_df = test_data.sample(frac=1, random_state=42)
    shuffled_df = shuffled_df.reset_index(drop=True)
    print(f"   Shuffled IDs: {list(shuffled_df['id'])}")
    
    batches = make_batches(
        test_data, 
        target_batch_size=2, 
        max_chars=25, 
        char_count_func=char_count_func
    )
    
    print(f"   Result: {len(batches)} batches")
    for i, batch in enumerate(batches):
        batch_chars = sum(char_count_func(row) for _, row in batch.iterrows())
        print(f"   Batch {i+1}: {len(batch)} rows, {batch_chars} chars")
        print(f"      IDs: {list(batch['id'])}")
    
    # Check total rows
    all_rows = pd.concat(batches, ignore_index=True)
    print(f"   Total rows in batches: {len(all_rows)}, Original: {len(test_data)}")
    print(f"   Missing IDs: {set(test_data['id']) - set(all_rows['id'])}")

if __name__ == "__main__":
    debug_dataframe_batching() 