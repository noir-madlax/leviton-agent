"""LLM client for product segmentation.

This implementation translates the sophisticated prompt-engineering and 
validation logic from `archive/backend-old/src/competitor/segment_products.py`
into the typed interface expected by `DatabaseProductSegmentationService`.

The key features ported from the original:
- Structured JSON response parsing with comprehensive validation
- Retry logic with contextual error messages
- Taxonomy consolidation across multiple batches
- Configurable models and parameters
"""

import json
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from product_segmentation.utils.cache import LLMCache  # file-layer cache
from product_segmentation.repositories.llm_interaction_repository import (
    LLMInteractionRepository,
)
from product_segmentation.storage.llm_storage import LLMStorageService
from product_segmentation.utils import refinement as _rf
from utils.llm_utils import safe_llm_call  # shared util
from utils import config as llm_cfg
from product_segmentation import config as seg_cfg

logger = logging.getLogger(__name__)


class ProductSegmentationLLMClient:
    """Production LLM client implementing advanced segmentation workflows."""

    def __init__(
        self,
        llm_client: Any,  # OpenAI client or compatible interface
        prompts: Dict[str, str],  # Loaded prompt templates
        cache: Optional[LLMCache] = None,
        interaction_repo: Optional[LLMInteractionRepository] = None,
        storage_service: Optional[LLMStorageService] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """Create a new *ProductSegmentationLLMClient*.

        Parameters
        ----------
        llm_client
            The low-level LLM SDK (e.g. OpenAI client) or a stub in unit tests.
        prompts
            Mapping of prompt-template names to template strings.
        cache
            Optional *file* cache layer (:class:`LLMCache`).
        interaction_repo
            Optional repository that stores an **index** of earlier LLM
            interactions in the database.  When provided, the client can look
            up existing responses across *runs* by their deterministic
            ``cache_key``.
        storage_service
            Storage layer that can load the raw JSON files referenced by the
            interaction index.  Must be supplied whenever *interaction_repo*
            is passed.
        max_retries
            Maximum number of retries for LLM calls. If not provided, uses
            the value from config.
        """

        self._llm = llm_client
        self._prompts = prompts
        self._max_retries = max_retries if max_retries is not None else seg_cfg.MAX_RETRIES
        self._cache = cache
        self._interaction_repo = interaction_repo
        self._storage = storage_service

    async def segment_products(
        self,
        products: List[int],
        *,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Segment products into taxonomies.

        Parameters
        ----------
        products
            List of product IDs to segment.
        category
            Optional category to use for segmentation.

        Returns
        -------
        Dict[str, Any]
            Segmentation result with taxonomies and segments.
        """
        if not products:
            return {"taxonomies": [], "segments": []}

        # Build input for LLM (simulating product descriptions)
        batch_input = self._build_batch_input(products)
        
        # Create base prompt with category context
        base_prompt = self._prompts["extract_taxonomy"]
        if category:
            base_prompt = base_prompt.format(product_category=category)
        
        full_prompt = base_prompt + "\n\n" + batch_input

        # Call LLM to extract taxonomy
        response = await self._safe_llm_call(full_prompt)

        # Parse response
        result = self._parse_segmentation_response(response)

        # Convert to segments and taxonomies
        segments = []
        taxonomies = []
        for category_name, data in result.items():
            if category_name == "OUT_OF_SCOPE":
                continue

            # Create taxonomy
            taxonomies.append({
                "category_name": category_name,
                "definition": data["definition"],
                "product_count": len(data["ids"])
            })

            # Create segments
            for product_id in data["ids"]:
                segments.append({
                    "product_id": product_id,
                    "taxonomy_id": len(taxonomies)  # 1-based index
                })

        return {"taxonomies": taxonomies, "segments": segments}

    async def consolidate_taxonomy(
        self,
        taxonomies: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Consolidate taxonomies from multiple batches.

        Parameters
        ----------
        taxonomies
            List of taxonomies to consolidate.

        Returns
        -------
        Dict[str, Any]
            Consolidated taxonomy with segments.
        """
        if not taxonomies:
            return {"taxonomies": [], "segments": []}

        if len(taxonomies) == 1:
            # No need to consolidate a single taxonomy
            return {"taxonomies": taxonomies, "segments": []}

        # Convert to ID-based format for consolidation
        taxonomy_a, taxonomy_b = self._prepare_taxonomies_for_consolidation(taxonomies)

        # Create base prompt with taxonomies
        base_prompt = self._prompts["consolidate_taxonomy"].format(
            taxonomy_a=json.dumps(taxonomy_a, indent=2),
            taxonomy_b=json.dumps(taxonomy_b, indent=2),
        )

        # Call LLM to consolidate taxonomies
        response = await self._safe_llm_call(base_prompt)

        # Parse and validate response
        is_valid, result = self._parse_and_validate_consolidate_response(
            response,
            set(taxonomy_a.keys()),
            set(taxonomy_b.keys()),
            taxonomy_a,
            taxonomy_b,
        )

        if not is_valid:
            raise ValueError(f"Failed to consolidate taxonomies: {result}")

        # Convert back to original format
        taxonomies = []
        for category_name, data in result.items():
            taxonomies.append({
                "category_name": category_name,
                "definition": data["definition"],
                "product_count": len(data["ids"])
            })

        return {"taxonomies": taxonomies, "segments": []}

    async def refine_assignments(
        self,
        segments: List[Dict[str, Any]],
        taxonomies: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Refine product-to-taxonomy assignments.

        The *refinement* phase allows a follow-up LLM pass to
        reconsider earlier assignments once the full, consolidated
        taxonomy is known.  The sophisticated implementation from the
        legacy pipeline has **not** been ported yet – for now this
        method simply returns the input *segments* unchanged so that
        callers can already rely on the method being present without
        breaking the public contract.

        Parameters
        ----------
        segments
            The list of segment dictionaries coming out of the initial
            segmentation phase.  Each dict must contain at least the
            keys ``product_id`` and ``taxonomy_id``; additional keys are
            passed through verbatim.
        taxonomies
            The list of taxonomies that the segments are assigned to.
        """

        logger.info("Refining %d segment assignments (taxonomies=%s)", len(segments), bool(taxonomies))

        # ------------------------------------------------------------------
        # Fast-exit when we have *no* taxonomy context – callers can pass
        # *None* to keep the legacy "no-op" behaviour.
        # ------------------------------------------------------------------
        if taxonomies is None:
            logger.debug("No taxonomy context supplied -> pass-through")
            return {"segments": segments, "cache_key": None}

        # Build \*consolidated* taxonomy mapping used for prompt rendering
        consolidated: Dict[str, Any] = {
            t["category_name"]: {
                "definition": t.get("definition", "") or "",
            }
            for t in taxonomies
        }

        subcats_section, subcat_to_id, id_to_subcat = _rf.build_subcategories_section(consolidated)
        id_to_subcategory = id_to_subcat

        # Augment segments with *category_name* so helper can reference it.
        for s in segments:
            tax_id = s.get("taxonomy_id")
            # taxonomy_id is 1-based in our earlier conversion
            if isinstance(tax_id, int) and 1 <= tax_id <= len(taxonomies):
                s.setdefault("category_name", taxonomies[tax_id - 1]["category_name"])

        products_section, id_to_product = _rf.build_products_section(segments, subcat_to_id)

        base_prompt = self._prompts["refine_assignments"]

        full_prompt = base_prompt + "\n\n" + subcats_section + products_section

        # ----------------------------- caching -----------------------------
        cache_ctx = {
            "model": llm_cfg.LLM_MODEL_NAME,
            "temperature": llm_cfg.LLM_TEMPERATURE,
            "taxonomy_checksum": list(consolidated.keys()),
        }

        cache_key: Optional[str] = None
        if self._cache is not None:
            cache_key = self._cache.generate_key(full_prompt, cache_ctx)
            cached_text = self._cache.load_response(full_prompt, cache_ctx)
            if cached_text is not None:
                is_valid, result = _rf.parse_and_validate_refinement_response(
                    cached_text, set(id_to_product.keys()), set(id_to_subcategory.keys())
                )
                if is_valid:
                    updated_segments = self._apply_reassignments(segments, result, id_to_product, id_to_subcategory)
                    return {"segments": updated_segments, "cache_key": cache_key}

        # ------------------------------  LLM  ------------------------------
        for attempt in range(self._max_retries):
            try:
                response_text = await self._safe_llm_call(full_prompt)

                # Optionally persist raw response
                if self._cache is not None and cache_key is None:
                    cache_key = self._cache.generate_key(full_prompt, cache_ctx)
                if self._cache is not None:
                    self._cache.save_response(full_prompt, response_text, cache_ctx)

                is_valid, result = _rf.parse_and_validate_refinement_response(
                    response_text, set(id_to_product.keys()), set(id_to_subcategory.keys())
                )

                if is_valid:
                    updated_segments = self._apply_reassignments(segments, result, id_to_product, id_to_subcategory)
                    return {"segments": updated_segments, "cache_key": cache_key}

                # Retry build prompt with error info – simple append.
                if attempt < self._max_retries - 1:
                    full_prompt = (
                        base_prompt
                        + "\n\nPREVIOUS ATTEMPT HAD ISSUES:\n"
                        + json.dumps(result, indent=2)[:1000]
                        + "\n\n"
                        + subcats_section
                        + products_section
                    )
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Refinement LLM call failed: %s", exc)
                if attempt == self._max_retries - 1:
                    raise

        # If we reach this place all retries failed – return original assignments
        logger.warning("Refinement failed after %d attempts – returning original assignments", self._max_retries)
        return {"segments": segments, "cache_key": None}

    # -------------------------------------------------------------------------
    # Internal helpers (ported from original segment_products.py logic)
    # -------------------------------------------------------------------------

    def _build_batch_input(self, products: Sequence[int]) -> str:
        """Build product input section for LLM prompt."""
        from core.database.connection import get_supabase_service_client  # local import
        supa = get_supabase_service_client()
        if not products:
            return ""

        # Fetch titles in one query
        rows = (
            supa.table("amazon_products")
            .select("id,title")
            .in_("id", products)  # Pass list directly, no need for CSV string
            .execute()
        )
        title_map = {row["id"]: row.get("title", "") for row in rows.data} if rows.data else {}

        lines: List[str] = []
        for i, pid in enumerate(products):
            title = title_map.get(pid) or f"Product {pid}"
            lines.append(f"[{i}] {title}")

        return "\n".join(lines)

    def _parse_and_validate_response(
        self, response_text: str, expected_ids: set, products: Sequence[int]
    ) -> tuple[bool, Any]:
        """Parse LLM response and validate structure (from original logic)."""
        try:
            # Extract JSON from response
            json_text = self._extract_json_from_response(response_text)
            taxonomy = json.loads(json_text)
        except (json.JSONDecodeError, ValueError) as e:
            return False, {"error": f"Could not parse JSON: {e}", "response": response_text}
        
        if not isinstance(taxonomy, dict):
            return False, {"error": "Response must be JSON object", "response": response_text}
        
        # Validate taxonomy structure
        found_ids = set()
        validation_errors = []
        
        for category, category_data in taxonomy.items():
            if not isinstance(category_data, dict):
                validation_errors.append(f"Category '{category}' must be object")
                continue
            
            if "definition" not in category_data:
                validation_errors.append(f"Category '{category}' missing definition")
            
            if "ids" not in category_data:
                validation_errors.append(f"Category '{category}' missing ids")
                continue
            
            ids = category_data["ids"]
            if not isinstance(ids, list):
                validation_errors.append(f"Category '{category}' ids must be list")
                continue
            
            for id_val in ids:
                try:
                    id_int = int(id_val)
                    if id_int in found_ids:
                        validation_errors.append(f"Duplicate ID {id_int}")
                    else:
                        found_ids.add(id_int)
                except (ValueError, TypeError):
                    validation_errors.append(f"Invalid ID '{id_val}' must be integer")
        
        # Check completeness
        missing_ids = expected_ids - found_ids
        extra_ids = found_ids - expected_ids
        
        if validation_errors or missing_ids or extra_ids:
            error_info = {
                "validation_errors": validation_errors,
                "missing_ids": list(missing_ids),
                "extra_ids": list(extra_ids),
                "response": response_text
            }
            return False, error_info
        
        return True, taxonomy

    def _convert_to_service_format(
        self, taxonomy: Dict[str, Any], products: Sequence[int]
    ) -> Dict[str, Any]:
        """Convert parsed taxonomy to service expected format."""
        segments = []
        taxonomies = []
        
        taxonomy_id = 1
        for category_name, category_data in taxonomy.items():
            # Add taxonomy entry
            taxonomies.append({
                "category_name": category_name,
                "definition": category_data.get("definition", ""),
                "product_count": len(category_data.get("ids", []))
            })
            
            # Add segment entries
            for id_val in category_data.get("ids", []):
                product_id = products[int(id_val)]  # Map back to original product ID
                segments.append({
                    "product_id": product_id,
                    "taxonomy_id": taxonomy_id
                })
            
            taxonomy_id += 1
        
        return {
            "segments": segments,
            "taxonomies": taxonomies
        }

    def _prepare_taxonomies_for_consolidation(
        self,
        taxonomies: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Prepare taxonomies for consolidation by splitting them into two groups."""
        if not taxonomies:
            return {}, {}

        # Split taxonomies into two groups
        mid = len(taxonomies) // 2
        tax_a = taxonomies[:mid]
        tax_b = taxonomies[mid:]

        # Convert each group into the expected format
        def convert_group(group: List[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
            result = {}
            for i, tax in enumerate(group):
                result[tax["category_name"]] = {
                    "definition": tax["definition"],
                    "ids": [f"{prefix}_{i}"]
                }
            return result

        return convert_group(tax_a, "A"), convert_group(tax_b, "B")

    def _parse_consolidation_response(
        self,
        response: str,
    ) -> Dict[str, Any]:
        """Parse consolidation response from LLM.

        Parameters
        ----------
        response
            Raw response from LLM.

        Returns
        -------
        Dict[str, Any]
            Parsed response with category names, definitions, and IDs.
        """
        try:
            result = json.loads(response)
            if not isinstance(result, dict):
                raise ValueError("Response must be a dictionary")

            # Validate each category
            for category_name, data in result.items():
                if not isinstance(data, dict):
                    raise ValueError(f"Category {category_name} data must be a dictionary")
                if "definition" not in data:
                    raise ValueError(f"Category {category_name} missing definition")
                if "ids" not in data:
                    raise ValueError(f"Category {category_name} missing IDs")

            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e

    def _build_retry_prompt(
        self, base_prompt: str, error_info: Dict[str, Any], batch_input: str
    ) -> str:
        """Build retry prompt with error context."""
        retry_section = "\n\nPREVIOUS ATTEMPT FAILED:\n"
        
        if "validation_errors" in error_info:
            retry_section += "Validation errors:\n"
            for error in error_info["validation_errors"]:
                retry_section += f"- {error}\n"
        
        if "missing_ids" in error_info and error_info["missing_ids"]:
            retry_section += f"Missing IDs: {error_info['missing_ids']}\n"
        
        if "extra_ids" in error_info and error_info["extra_ids"]:
            retry_section += f"Extra IDs: {error_info['extra_ids']}\n"
        
        retry_section += "\nPlease fix these issues and provide valid JSON.\n"
        
        return base_prompt + retry_section + "\n\n" + batch_input

    def _build_consolidation_retry_prompt(
        self, base_prompt: str, error_info: Dict[str, Any]
    ) -> str:
        """Build retry prompt for consolidation failures."""
        retry_section = f"\n\nPREVIOUS ATTEMPT FAILED: {error_info.get('error', 'Unknown error')}\n"
        retry_section += "Please provide valid JSON for taxonomy consolidation.\n"
        return base_prompt + retry_section

    async def _safe_llm_call(self, prompt: str) -> str:
        """Delegate to the project-wide :pyfunc:`safe_llm_call`."""
        # The *model* and *temperature* parameters are preserved for API
        # compatibility but the actual selection happens inside the global
        # LLM manager (configured via environment variables).  We therefore
        # ignore them here.

        return await safe_llm_call(prompt)

    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from LLM response text."""
        # Simple extraction - look for content between { }
        start = response_text.find('{')
        if start == -1:
            raise ValueError("No JSON found in response")
        
        # Find matching closing brace
        brace_count = 0
        for i, char in enumerate(response_text[start:], start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return response_text[start:i+1]
        
        raise ValueError("Incomplete JSON in response")

    def _apply_reassignments(
        self,
        segments: List[Dict[str, Any]],
        reassignments: Dict[str, str],
        id_to_product: Dict[str, int],
        id_to_subcategory: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Return **new list** of segments with updated taxonomy_id values."""

        # Create mapping from category name back to taxonomy_id (1-based order)
        category_to_tax_id = {
            name: idx + 1 for idx, name in enumerate({seg["category_name"] for seg in segments})
        }

        updated: List[Dict[str, Any]] = []
        for seg in segments:
            prod_id = seg["product_id"]

            # Determine if product should be reassigned
            re_key = None
            for k, original_idx in id_to_product.items():
                if original_idx == prod_id:
                    re_key = k
                    break
            if re_key and re_key in reassignments:
                # New category name via sub_id mapping
                new_cat_name = id_to_subcategory[reassignments[re_key]]
                seg = dict(seg)  # shallow copy – we never mutate caller list in place
                seg["taxonomy_id"] = category_to_tax_id.get(new_cat_name, seg["taxonomy_id"])
                seg["category_name"] = new_cat_name
            updated.append(seg)

        return updated

    def _parse_segmentation_response(
        self,
        response: str,
    ) -> Dict[str, Any]:
        """Parse segmentation response from LLM.

        Parameters
        ----------
        response
            Raw response from LLM.

        Returns
        -------
        Dict[str, Any]
            Parsed response with category names, definitions, and IDs.
        """
        try:
            result = json.loads(response)
            if not isinstance(result, dict):
                raise ValueError("Response must be a dictionary")

            # Validate each category
            for category_name, data in result.items():
                if not isinstance(data, dict):
                    raise ValueError(f"Category {category_name} data must be a dictionary")
                if "definition" not in data:
                    raise ValueError(f"Category {category_name} missing definition")
                if "ids" not in data:
                    raise ValueError(f"Category {category_name} missing IDs")

            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e

    def _parse_and_validate_consolidate_response(
        self,
        response: str,
        taxonomy_a_keys: set,
        taxonomy_b_keys: set,
        taxonomy_a: Dict[str, Any],
        taxonomy_b: Dict[str, Any],
    ) -> tuple[bool, Dict[str, Any]]:
        """Parse consolidation response and validate it."""
        try:
            result = json.loads(response)
            if not isinstance(result, dict):
                raise ValueError("Response must be a dictionary")

            # Validate each category
            for category_name, data in result.items():
                if not isinstance(data, dict):
                    raise ValueError(f"Category {category_name} data must be a dictionary")
                if "definition" not in data:
                    raise ValueError(f"Category {category_name} missing definition")
                if "ids" not in data:
                    raise ValueError(f"Category {category_name} missing IDs")

            # Validate taxonomy structure
            found_ids = set()
            validation_errors = []
            
            for category, category_data in result.items():
                if not isinstance(category_data, dict):
                    validation_errors.append(f"Category '{category}' data must be a dictionary")
                    continue
                
                if "definition" not in category_data:
                    validation_errors.append(f"Category '{category}' missing definition")
                    continue
                
                if "ids" not in category_data:
                    validation_errors.append(f"Category '{category}' missing ids")
                    continue
                
                ids = category_data["ids"]
                if not isinstance(ids, list):
                    validation_errors.append(f"Category '{category}' ids must be list")
                    continue
                
                for id_val in ids:
                    if not isinstance(id_val, str):
                        validation_errors.append(f"Invalid ID '{id_val}' must be string")
                        continue
                    
                    if not (id_val.startswith("A_") or id_val.startswith("B_")):
                        validation_errors.append(f"Invalid ID '{id_val}' must start with A_ or B_")
                        continue
                    
                    if id_val in found_ids:
                        validation_errors.append(f"Duplicate ID {id_val}")
                    else:
                        found_ids.add(id_val)
            
            # Check completeness
            expected_ids = set()
            for tax_data in taxonomy_a.values():
                expected_ids.update(tax_data["ids"])
            for tax_data in taxonomy_b.values():
                expected_ids.update(tax_data["ids"])
            
            missing_ids = expected_ids - found_ids
            extra_ids = found_ids - expected_ids
            
            if validation_errors or missing_ids or extra_ids:
                error_info = {
                    "validation_errors": validation_errors,
                    "missing_ids": list(missing_ids),
                    "extra_ids": list(extra_ids),
                    "response": response
                }
                return False, error_info
            
            return True, result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e
 