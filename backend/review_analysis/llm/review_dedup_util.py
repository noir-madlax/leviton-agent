"""Review analysis category deduplication utilities.

This module provides deduplication functionality for review aspect categories,
adapted from product segmentation's deduplication utilities but tailored for
the specific needs of review analysis workflows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Set

from nltk.stem import PorterStemmer

from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO


@dataclass
class ReviewDeduplicationResult:
    """Result of deduplicating review aspect categories."""
    unique_categories: List[TaxonomyDTO]
    duplicate_groups: Dict[str, List[TaxonomyDTO]]
    name_mapping: Dict[str, str]  # original_name -> representative_name


# Initialize NLTK stemmer
_stemmer = PorterStemmer()


def _create_category_stemmed_key(category_name: str) -> str:
    """Create a stemmed key for category deduplication using NLTK PorterStemmer.
    
    Adapted from product segmentation but optimized for review aspect categories.
    """
    # Convert to lowercase and remove common punctuation/symbols
    key = category_name.lower()
    key = re.sub(r'[-_]', ' ', key)  # Convert dashes/underscores to spaces
    
    # Handle special wifi pattern
    key = re.sub(r'\bwi\s+fi\b', 'wifi', key)  # "wi fi" -> "wifi"
    
    # Remove common connecting words and articles
    stop_words = {'and', 'or', 'the', 'a', 'an', 'of', 'for', 'with', 'to', 'in', 'on', 'at', 'by'}
    words = re.findall(r'\b\w+\b', key)
    filtered_words = [w for w in words if w not in stop_words]
    
    # Use NLTK PorterStemmer for proper linguistic stemming
    stemmed_words = [_stemmer.stem(word) for word in filtered_words]
    
    # Sort words to handle different orderings (e.g., "Smart Control" vs "Control Smart")
    stemmed_words.sort()
    
    return '_'.join(stemmed_words)


def deduplicate_review_categories(categories: List[TaxonomyDTO]) -> ReviewDeduplicationResult:
    """Deduplicate review aspect categories using stemmed key matching.
    
    For each group of duplicates, keeps the first entry's name as representative
    and concatenates all definitions to preserve semantic information.
    
    Args:
        categories: List of category DTOs to deduplicate
        
    Returns:
        ReviewDeduplicationResult with unique categories and mapping information
    """
    if not categories:
        return ReviewDeduplicationResult([], {}, {})
    
    # Group categories by stemmed key
    stem_map: Dict[str, str] = {}
    category_groups: Dict[str, List[TaxonomyDTO]] = {}
    
    for category in categories:
        stemmed_key = _create_category_stemmed_key(category.name)
        stem_map[category.name] = stemmed_key
        category_groups.setdefault(stemmed_key, []).append(category)
    
    # Create unique categories and track duplicates
    unique_categories: List[TaxonomyDTO] = []
    duplicate_groups: Dict[str, List[TaxonomyDTO]] = {}
    name_mapping: Dict[str, str] = {}
    
    for stemmed_key, group in category_groups.items():
        # Use first category as representative
        representative = group[0]
        
        # Concatenate definitions from all duplicates
        all_definitions = [cat.definition for cat in group if cat.definition]
        merged_definition = " | ".join(all_definitions) if all_definitions else representative.definition
        
        # Create merged category
        merged_category = TaxonomyDTO(
            name=representative.name,
            definition=merged_definition
        )
        unique_categories.append(merged_category)
        
        # Track name mapping for all categories in this group
        for category in group:
            name_mapping[category.name] = representative.name
        
        # Store duplicate groups (only if there are actual duplicates)
        if len(group) > 1:
            duplicate_groups[stemmed_key] = group
    
    return ReviewDeduplicationResult(
        unique_categories=unique_categories,
        duplicate_groups=duplicate_groups,
        name_mapping=name_mapping
    )


def deduplicate_review_category_batches(category_batches: List[List[TaxonomyDTO]]) -> tuple[List[List[TaxonomyDTO]], Dict[str, str]]:
    """Deduplicate review categories within and across batches.
    
    First deduplicates within each batch, then deduplicates across batches
    to ensure global uniqueness.
    
    Args:
        category_batches: List of category batches to deduplicate
        
    Returns:
        Tuple of (deduplicated_batches, global_name_mapping)
    """
    if not category_batches:
        return [], {}
    
    # Step 1: Deduplicate within each batch
    deduped_batches = []
    batch_mappings = []
    
    for batch in category_batches:
        result = deduplicate_review_categories(batch)
        deduped_batches.append(result.unique_categories)
        batch_mappings.append(result.name_mapping)
    
    # Step 2: Deduplicate across batches
    seen_keys: Set[str] = set()
    final_batches: List[List[TaxonomyDTO]] = []
    global_name_mapping: Dict[str, str] = {}
    
    # Merge all batch mappings into global mapping first
    for batch_mapping in batch_mappings:
        global_name_mapping.update(batch_mapping)
    
    # Now deduplicate across batches
    cross_batch_mapping: Dict[str, str] = {}
    
    for batch in deduped_batches:
        final_batch: List[TaxonomyDTO] = []
        
        for category in batch:
            stemmed_key = _create_category_stemmed_key(category.name)
            
            if stemmed_key not in seen_keys:
                # First time seeing this key, add to final batch
                seen_keys.add(stemmed_key)
                final_batch.append(category)
                cross_batch_mapping[category.name] = category.name  # Identity mapping
            else:
                # Find the representative name for this key
                for prev_batch in final_batches:
                    for prev_category in prev_batch:
                        if _create_category_stemmed_key(prev_category.name) == stemmed_key:
                            cross_batch_mapping[category.name] = prev_category.name
                            break
                    if category.name in cross_batch_mapping:
                        break
        
        if final_batch:  # Only add non-empty batches
            final_batches.append(final_batch)
    
    # Update global mapping with cross-batch deduplication
    final_mapping = {}
    for original_name, batch_mapped_name in global_name_mapping.items():
        final_name = cross_batch_mapping.get(batch_mapped_name, batch_mapped_name)
        final_mapping[original_name] = final_name
    
    return final_batches, final_mapping


def print_review_deduplication_summary(result: ReviewDeduplicationResult) -> None:
    """Print summary of review category deduplication results."""
    unique_count = len(result.unique_categories)
    merged_total = sum(len(group) - 1 for group in result.duplicate_groups.values())
    original_total = unique_count + merged_total
    
    print(f"\n🔍 Review Category Deduplication: {original_total} → {unique_count} unique (merged {merged_total})")
    
    if result.duplicate_groups:
        print("\n📦 Merged Category Groups:")
        for stem_key, duplicates in result.duplicate_groups.items():
            representative = duplicates[0].name
            merged_names = [cat.name for cat in duplicates[1:]]
            if merged_names:
                print(f"  • '{representative}' ← merged: {merged_names}")
    else:
        print("\n✅ No duplicate categories detected.") 