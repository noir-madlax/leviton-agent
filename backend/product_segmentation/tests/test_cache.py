"""Unit tests for the file-based caching helpers."""

import tempfile
import shutil
from pathlib import Path

import pytest

from backend.product_segmentation.utils.cache import (
    create_llm_cache,
    create_result_cache,
)


@pytest.fixture(scope="function")
def _tmp_dir():
    path = Path(tempfile.mkdtemp(prefix="cache_tests_"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_llm_cache_roundtrip(_tmp_dir):
    cache = create_llm_cache(_tmp_dir)

    prompt = "Explain product differences"
    response = "Here are the differences..."
    context = {"model": "gpt-4o", "temperature": 0.2}

    assert cache.save_response(prompt, response, context)
    loaded = cache.load_response(prompt, context)
    assert loaded == response


def test_result_cache_roundtrip(_tmp_dir):
    cache = create_result_cache(_tmp_dir)

    input_data = {"numbers": [1, 2, 3]}
    result = sum(input_data["numbers"])
    params = {"method": "sum"}

    assert cache.save_result(input_data, result, params)
    loaded = cache.load_result(input_data, params)
    assert loaded == result


def test_cache_clear(_tmp_dir):
    cache = create_llm_cache(_tmp_dir)
    cache.save_response("p", "r")
    cache.save_response("p2", "r2")
    assert cache.clear() == 2
    # After clear nothing should be returned
    assert cache.load_response("p") is None 