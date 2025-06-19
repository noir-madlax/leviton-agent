"""File-based caching helpers for LLM interactions and expensive computations.

The implementation is ported from the *archive/backend-old* prototype but
streamlined for modern typing and our packaging guidelines.  It purposefully
avoids any external dependencies so it can run in constrained environments
(e.g. unit-test CI) while still supporting migration to S3 later (by mounting
an S3-backed filesystem or overlay driver).

The module provides two specialised wrappers:

* :class:`LLMCache` – stores raw prompt/response pairs keyed by a stable hash.
* :class:`ResultCache` – generic helper for expensive post-processing results.

Both subclasses inherit from :class:`CacheManager`, which encapsulates the
common JSON-file read/write logic and SHA-256 key generation.
"""

from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "CacheManager",
    "LLMCache",
    "ResultCache",
    "create_llm_cache",
    "create_result_cache",
]


class CacheManager:  # pylint: disable=too-few-public-methods
    """Light-weight file-based cache backend (JSON serialisation)."""

    def __init__(self, cache_dir: Path | str, cache_type: str = "generic") -> None:  # noqa: D401 – simple init
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._type = cache_type

    # ------------------------------------------------------------------
    # Public convenience helpers
    # ------------------------------------------------------------------

    def generate_key(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Return *stable* 16-char SHA-256 key for *content* + *context*."""
        payload = content if context is None else f"{content}|||{json.dumps(context, sort_keys=True)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def save(self, key: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Serialise *data* plus bookkeeping info into ``cache_dir``."""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_type": self._type,
            "metadata": metadata or {},
            "data": data,
        }
        path = self._dir / self._filename(key)
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(record, fh, indent=2, ensure_ascii=False, default=str)
            logger.debug("Saved cache entry %%s to %%s", key, path)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to save cache entry %s: %s", key, exc)
            return False

    def load(self, key: str) -> Optional[Any]:
        """Return cached payload or *None* when key not present."""
        path = self._dir / self._filename(key)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                record = json.load(fh)
            return record.get("data")
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to load cache entry %s: %s", key, exc)
            return None

    def clear(self) -> int:
        """Delete **all** cache files for this cache type. Returns number removed."""
        count = 0
        for file in self._dir.glob(f"{self._type}_*.json"):
            try:
                file.unlink()
                count += 1
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Error deleting cache file %s: %s", file, exc)
        return count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _filename(self, key: str, ext: str = ".json") -> str:  # noqa: D401 – small helper
        return f"{self._type}_{key}{ext}"


class LLMCache(CacheManager):
    """Cache wrapper specifically for raw LLM prompt/response pairs."""

    def __init__(self, cache_dir: Path | str):  # noqa: D401 – thin wrapper
        super().__init__(cache_dir, cache_type="llm")

    # Public convenience wrappers ------------------------------------------------

    def save_response(self, prompt: str, response: str, context: Optional[Dict[str, Any]] = None) -> bool:
        key = self.generate_key(prompt, context)
        payload = {
            "prompt": prompt,
            "response": response,
            "prompt_length": len(prompt),
            "response_length": len(response),
        }
        return self.save(key, payload, context)

    def load_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        key = self.generate_key(prompt, context)
        cached = self.load(key)
        if isinstance(cached, dict):
            return cached.get("response")
        return None


class ResultCache(CacheManager):
    """Generic helper for expensive deterministic computations."""

    def __init__(self, cache_dir: Path | str):  # noqa: D401 – thin wrapper
        super().__init__(cache_dir, cache_type="result")

    def save_result(self, input_data: Any, result: Any, params: Optional[Dict[str, Any]] = None) -> bool:
        key = self.generate_key(json.dumps(input_data, sort_keys=True), params)
        return self.save(key, {"input": input_data, "result": result}, params)

    def load_result(self, input_data: Any, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        key = self.generate_key(json.dumps(input_data, sort_keys=True), params)
        cached = self.load(key)
        if isinstance(cached, dict):
            return cached.get("result")
        return None


# Factory helpers ----------------------------------------------------------------

def create_llm_cache(cache_dir: Path | str) -> LLMCache:  # noqa: D401 – one-liner factory
    return LLMCache(cache_dir)


def create_result_cache(cache_dir: Path | str) -> ResultCache:  # noqa: D401
    return ResultCache(cache_dir) 