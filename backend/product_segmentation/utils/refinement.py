"""Helper utilities for *assignment refinement* (Phase 3.2).

The original implementation lives in
`archive/backend-old/src/competitor/segment_products.py::refine_product_assignments`.
This module ports **only the reusable building-blocks** so that
`ProductSegmentationLLMClient.refine_assignments` can rely on a focused,
unit-testable API while keeping the heavy prompt/validation logic contained in
one place.

Key differences to the legacy code
----------------------------------
1. **No file I/O** – caching, logging and prompt archiving is handled at a
   higher abstraction level (see :pymod:`backend.product_segmentation.utils.cache` and
   :pymod:`backend.product_segmentation.storage.llm_storage`).
2. **Stable interfaces** – instead of full dataframes we operate on simple
   lists/Dicts that already contain the *current* taxonomy assignment.  The
   public helpers therefore return *new* assignment mappings that callers can
   apply to their own data structures.
3. **Strict typing** – the helpers are fully typed and raise explicit
   exceptions when the provided data contract is violated.

The subset we port (for now):
* :func:`build_subcategories_section` – stringify consolidated taxonomy with
  deterministic ``S_i`` identifiers.
* :func:`build_products_section` – render products with their "current"
  assignments using deterministic ``P_i`` identifiers.
* :func:`parse_and_validate_refinement_response` – validate the JSON payload
  containing potential re-assignments returned by the LLM.

The validation rules follow the legacy contract closely so the same prompt
templates remain compatible.
"""

from typing import Dict, List, Tuple, Set, Any

__all__ = [
    "build_subcategories_section",
    "build_products_section",
    "parse_and_validate_refinement_response",
]


# ---------------------------------------------------------------------------
# Prompt rendering helpers
# ---------------------------------------------------------------------------

def build_subcategories_section(
    consolidated_taxonomy: Dict[str, Dict[str, Any]],
) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """Return text section plus *bidirectional* mapping dicts.

    Parameters
    ----------
    consolidated_taxonomy
        Mapping ``{category_name: {"definition": str, ...}}`` as produced by
        the consolidation phase.
    """

    subcategory_to_id: Dict[str, str] = {}
    id_to_subcategory: Dict[str, str] = {}

    lines: List[str] = ["**SUBCATEGORIES:**"]

    for idx, (category_name, category_info) in enumerate(consolidated_taxonomy.items()):
        sub_id = f"S_{idx}"
        subcategory_to_id[category_name] = sub_id
        id_to_subcategory[sub_id] = category_name

        definition = category_info.get("definition", "")
        lines.append(f"[{sub_id}] {category_name}: {definition}")

    return "\n".join(lines) + "\n", subcategory_to_id, id_to_subcategory


def build_products_section(
    products: List[Dict[str, Any]],
    subcategory_to_id: Dict[str, str],
    start_idx: int = 0,
) -> Tuple[str, Dict[str, int]]:
    """Return text section enumerating products with their current assignment.

    The *products* list must contain ``product_id`` and ``category_name`` keys.
    Additional keys are ignored for prompt generation.
    """

    id_to_product_index: Dict[str, int] = {}
    lines = ["\n**PRODUCTS WITH CURRENT ASSIGNMENTS:**"]

    counter = start_idx
    for prod in products:
        prod_id = f"P_{counter}"
        counter += 1

        cat_name = prod.get("category_name")
        if cat_name is None or cat_name not in subcategory_to_id:
            raise ValueError(
                f"Product {prod.get('product_id')} references unknown category '{cat_name}'"
            )
        sub_id = subcategory_to_id[cat_name]

        title = prod.get("title", "<no title>")
        lines.append(f"[{prod_id}] {title} → {sub_id} ({cat_name})")

        # Map back so we can update callers later
        id_to_product_index[prod_id] = prod["product_id"]

    return "\n".join(lines) + "\n", id_to_product_index


# ---------------------------------------------------------------------------
# Response JSON validation helper
# ---------------------------------------------------------------------------

def parse_and_validate_refinement_response(
    response_text: str,
    batch_product_ids: Set[str],
    valid_subcategory_ids: Set[str],
) -> Tuple[bool, Any]:
    """Return *(is_valid, result_or_error)* tuple for re-assignment payload.

    The expected JSON schema is a simple mapping ``{"P_i": "S_j", ...}``.
    Empty mapping (``{}``) means *no changes required* and is considered valid.
    """

    import json  # local import to avoid unnecessary startup overhead

    def _extract_json(raw: str) -> str:
        """Naïve brace matching – same as other helpers in the codebase."""
        start = raw.find("{")
        if start == -1:
            raise ValueError("No JSON object found")
        brace = 0
        for pos, ch in enumerate(raw[start:], start):
            if ch == "{":
                brace += 1
            elif ch == "}":
                brace -= 1
                if brace == 0:
                    return raw[start : pos + 1]
        raise ValueError("Unterminated JSON object")

    try:
        json_snippet = _extract_json(response_text)
        mapping = json.loads(json_snippet)
    except Exception as exc:  # pylint: disable=broad-except
        # We return *structured* error info so the caller can create retry prompt
        return False, {"error": f"Failed to parse JSON: {exc}", "response": response_text[:500]}

    if not isinstance(mapping, dict):
        return False, {
            "error": "JSON root must be an object mapping P_i → S_j",
            "response": response_text[:500],
        }

    # Empty mapping is explicitly allowed (means *no* reassignment)
    if not mapping:
        return True, {}

    validation_errs: List[str] = []
    seen_products: Set[str] = set()

    # Convert the new format to the old format
    if "segments" in mapping:
        segments = mapping["segments"]
        if not isinstance(segments, list):
            return False, {
                "error": "segments must be a list",
                "response": response_text[:500],
            }
        
        # Convert list of segments to P_i → S_j mapping
        result = {}
        for i, segment in enumerate(segments):
            prod_id = f"P_{i}"
            sub_id = f"S_{segment['taxonomy_id'] - 1}"  # Convert taxonomy_id to S_j format
            result[prod_id] = sub_id
        return True, result

    # Handle old format
    for prod_id, sub_id in mapping.items():
        if prod_id in seen_products:
            validation_errs.append(f"Duplicate product ID '{prod_id}'")
        else:
            seen_products.add(prod_id)

        if prod_id not in batch_product_ids:
            validation_errs.append(f"Unknown product ID '{prod_id}' not in batch")
        if sub_id not in valid_subcategory_ids:
            validation_errs.append(f"Unknown subcategory ID '{sub_id}'")

    missing = batch_product_ids - seen_products
    if missing:
        # The spec *allows* missing products (they keep current assignment)
        # We therefore do *not* treat as error – this differs from segmentation
        # validation where completeness is required.
        pass

    if validation_errs:
        return False, {"validation_errors": validation_errs, "response": response_text[:500]}

    return True, mapping 