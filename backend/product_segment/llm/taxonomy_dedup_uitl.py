"""Taxonomy deduplication utilities using NLP word stemming.

This module provides functions to deduplicate taxonomies by converting names to
sorted lowercase word stems and keeping only unique entries.
"""

# Copy of previous taxonomy_deduplication.py content
import re
from typing import List, Dict, Set
from dataclasses import dataclass
from nltk.stem import PorterStemmer

from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO

# Constants for deduplication
STEMMER_LANGUAGE = 'english'
MIN_WORD_LENGTH = 2  # Minimum word length to consider for stemming


@dataclass
class DeduplicationResult:
    """Result of taxonomy deduplication process."""
    unique_taxonomies: List[TaxonomyDTO]
    duplicate_groups: Dict[str, List[TaxonomyDTO]]
    stem_mapping: Dict[str, str]  # original_name -> stemmed_key

    """Download required NLTK data for stemming."""
    


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _get_word_stems(text: str) -> List[str]:
    normalized = _normalize_text(text)
    words = normalized.split()

    stemmer = PorterStemmer()
    return [stemmer.stem(w) for w in words if len(w) >= MIN_WORD_LENGTH]


def _create_stemmed_key(name: str) -> str:
    return ' '.join(sorted(_get_word_stems(name)))


def deduplicate_taxonomies(taxonomies: List[TaxonomyDTO]) -> DeduplicationResult:
    """Return unique list by *stemmed key* and concatenate definitions.

    For each group of duplicates determined by the stemmed key, the *name* of
    the first entry is kept as the representative, while the *definition*
    fields of **all** items in the group are concatenated (in their original
    order).  This preserves every semantic hint for downstream stages such as
    consolidation while still removing duplicate categories.
    """

    if not taxonomies:
        return DeduplicationResult([], {}, {})
    stem_map: Dict[str, str] = {}
    bucket: Dict[str, List[TaxonomyDTO]] = {}
    for tax in taxonomies:
        key = _create_stemmed_key(tax.name)
        stem_map[tax.name] = key
        bucket.setdefault(key, []).append(tax)
    uniques: List[TaxonomyDTO] = []
    dup_groups: Dict[str, List[TaxonomyDTO]] = {}

    for key, lst in bucket.items():
        # Concatenate definitions from all duplicates (if present) and clean up
        # whitespace.  This keeps the first item's *name* as representative but
        # ensures the semantic information from every duplicate definition is
        # preserved for downstream stages.
        concatenated_def = " - ".join(filter(None, (t.definition for t in lst))).strip()
        rep = lst[0]
        merged_dto = TaxonomyDTO(name=rep.name, definition=concatenated_def or rep.definition)

        uniques.append(merged_dto)

        # Store duplicates (original objects) under the key for transparency
        if len(lst) > 1:
            dup_groups[key] = lst
    return DeduplicationResult(uniques, dup_groups, stem_map)


def deduplicate_taxonomy_batches(batches: List[List[TaxonomyDTO]]) -> List[List[TaxonomyDTO]]:
    if not batches:
        return []
    # within batch
    deduped = [deduplicate_taxonomies(b).unique_taxonomies for b in batches]
    # global
    seen: Set[str] = set()
    final_batches: List[List[TaxonomyDTO]] = []
    for batch in deduped:
        new_batch: List[TaxonomyDTO] = []
        for tax in batch:
            key = _create_stemmed_key(tax.name)
            if key not in seen:
                seen.add(key)
                new_batch.append(tax)
        if new_batch:
            final_batches.append(new_batch)
    return final_batches


def print_deduplication_summary(result: DeduplicationResult) -> None:
    """Print summary and show which taxonomy names were merged.

    Args:
        original: full list of original taxonomies (possibly with duplicates)
        result: deduplication result containing unique list & duplicate mapping
    """
    unique_count = len(result.unique_taxonomies)
    merged_total = sum(len(group) - 1 for group in result.duplicate_groups.values())
    original_total = unique_count + merged_total
    print(f"\n🔍 Deduplication Summary: {original_total} ⇒ {unique_count} unique (merged {merged_total})")

    if result.duplicate_groups:
        print("\n📦 Merged Groups:")
        for stem_key, duplicates in result.duplicate_groups.items():
            rep_name = duplicates[0].name
            merged_names = [d.name for d in duplicates[1:]]
            if merged_names:
                print(f"  • '{rep_name}' ← merged: {merged_names}")
    else:
        print("\n✅ No duplicates detected.")
