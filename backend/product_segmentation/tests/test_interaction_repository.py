"""Unit-tests for :pyclass:`backend.product_segmentation.repositories.llm_interaction_repository.LLMInteractionRepository`.

The tests run entirely in-memory and therefore stub the *supabase* package so
that the repository implementation can be imported without the real SDK being
installed on the machine that executes the CI job.
"""

import sys
import types
import pytest

# ---------------------------------------------------------------------------
# 🧰  Minimal supabase stub – provides exactly the attributes used by the repo
# ---------------------------------------------------------------------------

class _FakeTable:  # pylint: disable=too-few-public-methods
    """Mimics the chainable *table/insert/execute* API."""

    def __init__(self) -> None:  # noqa: D401 – simple init
        self._data = []

    def insert(self, rows):  # noqa: D401 – keep signature compatible
        # NB: The real Supabase API allows method-chaining so we return *self*
        self._data.extend(rows)
        return self

    # The repository calls *.execute()* at the end of the chain.
    def execute(self):  # noqa: D401 – simple passthrough
        return types.SimpleNamespace(data=self._data)

class _FakeClient:  # pylint: disable=too-few-public-methods
    """Provides only the *table()* accessor."""

    def table(self, _name):  # noqa: D401 – signature mirrors SDK
        return _FakeTable()

try:
    import supabase as _supabase  # type: ignore

    # Replace the *Client* attribute with our fake while keeping the rest
    # of the module intact (important when other tests import supabase).
    _supabase.Client = _FakeClient  # type: ignore[attr-defined]
except ModuleNotFoundError:
    # When the real package is not installed, register a minimal stub
    supabase_stub = types.ModuleType("supabase")
    supabase_stub.Client = _FakeClient  # type: ignore[attr-defined]
    sys.modules["supabase"] = supabase_stub

# After the stub is in place, import the repository
from product_segmentation.repositories.llm_interaction_repository import (
    LLMInteractionRepository,
)
from product_segmentation.models import LLMInteractionIndexCreate, InteractionType


class TestLLMInteractionRepository:  # pylint: disable=too-few-public-methods
    """Simple happy-path tests verifying *insert* behaviour."""

    @pytest.fixture()
    def repo(self):
        from supabase import Client  # pylint: disable=import-error

        client = Client()  # type: ignore[call-arg] – fake client
        return LLMInteractionRepository(client)

    @pytest.mark.asyncio
    async def test_batch_create_interactions_success(self, repo):
        interactions = [
            LLMInteractionIndexCreate(
                run_id="RUN_TEST_1",
                interaction_type=InteractionType.SEGMENTATION,
                batch_id=0,
                attempt=1,
                file_path="RUN_TEST_1/interactions/foo.json",
            ),
            LLMInteractionIndexCreate(
                run_id="RUN_TEST_1",
                interaction_type=InteractionType.SEGMENTATION,
                batch_id=1,
                attempt=1,
                file_path="RUN_TEST_1/interactions/bar.json",
            ),
        ]

        ok = await repo.batch_create_interactions(interactions)
        assert ok  # should succeed with the fake client

    @pytest.mark.asyncio
    async def test_batch_create_empty_noop(self, repo):
        ok = await repo.batch_create_interactions([])
        assert ok  # inserting nothing should be a no-op and succeed 