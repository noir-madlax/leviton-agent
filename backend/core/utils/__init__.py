__all__ = [
    "rate_limiter",
    "llm_utils",
    "config",
]

# ---------------------------------------------------------------------------
# Export this package as a top-level ``utils`` alias so legacy imports work
# ---------------------------------------------------------------------------
import sys as _sys
_sys.modules.setdefault("utils", _sys.modules[__name__])
for _sub in ("rate_limiter", "llm_utils", "config"):
    if f"{__name__}.{_sub}" in _sys.modules:
        _sys.modules.setdefault(f"utils.{_sub}", _sys.modules[f"{__name__}.{_sub}"])