"""Batching utilities for deterministic directory / batch layout management.

This module centralises the logic that converts an arbitrary list or pandas DataFrame
into evenly-sized batches with stable, reproducible ordering.

The implementation is adapted from the legacy helper
`archive/backend-old/src/competitor/segment_products.py::make_batches`
but stripped of side effects and narrowed to a clear, testable API.

Data contracts:
1. Returned batches have **sequential integer indices starting from zero**.
2. `index_mappings[i][j]` gives the *original DataFrame index* for row *j* in batch *i*.
3. The exact batch composition is deterministic for a given seed and target batch size.
"""

from typing import List, Tuple, TypeVar, Union, Sequence, Any

import pandas as pd
import numpy as np

DEFAULT_SEED = 42

__all__ = [
    "calculate_optimal_batch_sizes",
    "make_batches",
]

T = TypeVar('T')

def calculate_optimal_batch_sizes(total_items: int, target_batch_size: int) -> List[int]:
    """Return a list of batch sizes that minimises the size variance.

    The algorithm chooses *n* such that `ceil(total_items / target_batch_size)` batches are
    produced and distributes the remainder as evenly as possible across the first bunches.

    Example
    -------
    >>> calculate_optimal_batch_sizes(7, 3)
    [3, 2, 2]
    """

    if total_items <= 0:
        raise ValueError("total_items must be positive")

    if total_items <= target_batch_size:
        return [total_items]

    num_batches: int = max(1, round(total_items / target_batch_size))

    base_size: int = total_items // num_batches
    remainder: int = total_items % num_batches

    sizes: List[int] = [base_size] * num_batches

    for i in range(remainder):
        sizes[i] += 1

    return sizes


def make_batches(
    data: Union[Sequence[T], pd.DataFrame],
    target_batch_size: int,
    seed: int = DEFAULT_SEED,
) -> Union[List[List[T]], List[pd.DataFrame]]:
    """Split data into evenly sized batches with deterministic ordering.

    Parameters
    ----------
    data : Union[Sequence[T], pd.DataFrame]
        Data to split. Can be a list, tuple, or DataFrame.
    target_batch_size : int
        Desired batch size. The function will attempt to distribute items evenly and
        avoid very small final batches.
    seed : int, optional
        Random seed for the internal shuffle that ensures even distribution across
        batches while keeping determinism.

    Returns
    -------
    Union[List[List[T]], List[pd.DataFrame]]
        List of batches. Each batch is either a list or DataFrame depending on input type.
    """
    if isinstance(data, pd.DataFrame):
        if data.empty:
            return []

        optimal_sizes = calculate_optimal_batch_sizes(len(data), target_batch_size)

        # Shuffle deterministically for balanced distribution
        shuffled_df = data.sample(frac=1, random_state=seed)
        shuffled_df = shuffled_df.reset_index(drop=True)

        batches: List[pd.DataFrame] = []
        cursor: int = 0
        
        for size in optimal_sizes:
            end = cursor + size
            if cursor >= len(shuffled_df):
                break

            batch_df = shuffled_df.iloc[cursor:end].copy()
            batch_df.index = range(len(batch_df))  # ensure sequential indices
            batches.append(batch_df)
            cursor = end

        return batches

    else:
        # Handle sequence types (list, tuple, etc.)
        if not data:
            return []

        optimal_sizes = calculate_optimal_batch_sizes(len(data), target_batch_size)
        
        # Convert to numpy array for efficient shuffling
        data_array = np.array(data)
        rng = np.random.RandomState(seed)
        rng.shuffle(data_array)

        batches: List[List[T]] = []
        cursor: int = 0

        for size in optimal_sizes:
            end = cursor + size
            if cursor >= len(data_array):
                break

            batch = data_array[cursor:end].tolist()
            batches.append(batch)
            cursor = end

        return batches 