"""Unit tests for batching utilities"""

from typing import List

import pandas as pd
import numpy as np

from backend.product_segmentation.utils.batching import (
    calculate_optimal_batch_sizes,
    make_batches,
    DEFAULT_SEED,
)


def test_calculate_optimal_batch_sizes_simple() -> None:
    assert calculate_optimal_batch_sizes(3, 5) == [3]
    assert calculate_optimal_batch_sizes(6, 4) == [3, 3]
    assert calculate_optimal_batch_sizes(7, 3) == [4, 3]


def test_make_batches_dataframe() -> None:
    # Create dummy DataFrame with 25 rows
    df = pd.DataFrame({"value": list(range(25))})

    batches = make_batches(df, target_batch_size=10, seed=DEFAULT_SEED)

    # Ensure total rows match
    total_rows = sum(len(b) for b in batches)
    assert total_rows == len(df)

    # Ensure batch indices sequential
    for batch in batches:
        assert list(batch.index) == list(range(len(batch)))

    # Ensure all values are present (just in different order)
    all_values = pd.concat(batches)["value"].sort_values().reset_index(drop=True)
    assert all_values.equals(pd.Series(range(25)))


def test_make_batches_list() -> None:
    # Create list of 25 items
    items = list(range(25))

    batches = make_batches(items, target_batch_size=10, seed=DEFAULT_SEED)

    # Ensure total items match
    total_items = sum(len(b) for b in batches)
    assert total_items == len(items)

    # Ensure all values are present (just in different order)
    all_values = sorted([x for batch in batches for x in batch])
    assert all_values == list(range(25))


def test_determinism_dataframe() -> None:
    df = pd.DataFrame({"value": list(range(30))})

    b1 = make_batches(df, target_batch_size=10, seed=DEFAULT_SEED)
    b2 = make_batches(df, target_batch_size=10, seed=DEFAULT_SEED)

    # DataFrames equality
    for d1, d2 in zip(b1, b2):
        assert d1.equals(d2)


def test_determinism_list() -> None:
    items = list(range(30))

    b1 = make_batches(items, target_batch_size=10, seed=DEFAULT_SEED)
    b2 = make_batches(items, target_batch_size=10, seed=DEFAULT_SEED)

    # List equality
    assert b1 == b2


# -----------------------------------------------------------------------------
# Manual test runner (allows `python -m backend.product_segmentation.tests.test_batching`)
# -----------------------------------------------------------------------------

def _run_test(fn):
    try:
        fn()
        return True, None
    except Exception as exc:  # pylint: disable=broad-except
        return False, exc


def run_batching_tests() -> bool:  # pragma: no cover
    """Execute all tests in this module without pytest."""
    print("🧪 Running Batching Utility Tests")
    print("=" * 50)

    tests = [
        ("calculate_optimal_batch_sizes", test_calculate_optimal_batch_sizes_simple),
        ("make_batches_dataframe", test_make_batches_dataframe),
        ("make_batches_list", test_make_batches_list),
        ("determinism_dataframe", test_determinism_dataframe),
        ("determinism_list", test_determinism_list),
    ]

    passed = 0
    for name, fn in tests:
        success, err = _run_test(fn)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if success:
            passed += 1
        else:
            print(f"   → {err}")
    print(f"\n🎉 Batching tests completed: {passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == "__main__":  # pragma: no cover
    run_batching_tests() 