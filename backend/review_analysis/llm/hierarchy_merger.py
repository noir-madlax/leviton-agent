"""Shared utilities for merging review analysis hierarchies.

This module provides common functionality for merging extraction hierarchies,
handling ID conflicts and maintaining referential integrity across merged results.
"""

import re
from typing import Dict, Any, List, Set, Tuple

try:
    import nltk
    from nltk.stem import PorterStemmer
    # Download required NLTK data if not already present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    _stemmer = PorterStemmer()
    _NLTK_AVAILABLE = True
except ImportError:
    _stemmer = None
    _NLTK_AVAILABLE = False


def extract_used_ids(hierarchy: Dict[str, Any]) -> Tuple[Set[str], Set[str]]:
    """Extract used PID and perf_id from hierarchy."""
    used_pids = set()
    used_perf_ids = set()
    
    # Extract PIDs from phy section
    if "phy" in hierarchy:
        for category, details in hierarchy["phy"].items():
            for pid_detail in details.keys():
                if "@" in pid_detail:
                    pid = pid_detail.split("@")[0]
                    used_pids.add(pid)
    
    # Extract perf_ids from perf section
    if "perf" in hierarchy:
        for category, details in hierarchy["perf"].items():
            for perf_id_detail in details.keys():
                if "@" in perf_id_detail:
                    perf_id = perf_id_detail.split("@")[0]
                    used_perf_ids.add(perf_id)
    
    return used_pids, used_perf_ids


def offset_id(original_id: str, used_ids: Set[str], is_perf: bool = False) -> str:
    """Calculate offset ID to continue sequence after used IDs."""
    if is_perf:
        # perf_ids: a, b, c, ..., z, aa, ab, ...
        base_chars = 'abcdefghijklmnopqrstuvwxyz'
    else:
        # PIDs: A, B, C, ..., Z, AA, AB, ...
        base_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    # Find the highest used ID
    max_id = ""
    for used_id in used_ids:
        if len(used_id) > len(max_id) or (len(used_id) == len(max_id) and used_id > max_id):
            max_id = used_id
    
    # Generate next ID in sequence
    if not max_id:
        return base_chars[0]  # Start with A or a
    
    # Convert to next ID
    if len(max_id) == 1:
        idx = base_chars.index(max_id)
        if idx < len(base_chars) - 1:
            return base_chars[idx + 1]
        else:
            return base_chars[0] + base_chars[0]  # AA or aa
    else:
        # Handle multi-character IDs (AA, AB, etc.)
        first_char = max_id[0]
        second_char = max_id[1]
        second_idx = base_chars.index(second_char)
        
        if second_idx < len(base_chars) - 1:
            return first_char + base_chars[second_idx + 1]
        else:
            first_idx = base_chars.index(first_char)
            if first_idx < len(base_chars) - 1:
                return base_chars[first_idx + 1] + base_chars[0]
            else:
                return base_chars[0] + base_chars[0] + base_chars[0]  # AAA or aaa


def create_id_mapping(hierarchy: Dict[str, Any], used_pids: Set[str], used_perf_ids: Set[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Create mapping from original IDs to offset IDs."""
    pid_mapping = {}
    perf_id_mapping = {}
    
    # Create PID mapping
    current_pids = set()
    if "phy" in hierarchy:
        for category, details in hierarchy["phy"].items():
            for pid_detail in details.keys():
                if "@" in pid_detail:
                    original_pid = pid_detail.split("@")[0]
                    current_pids.add(original_pid)
    
    for original_pid in sorted(current_pids):
        new_pid = offset_id(original_pid, used_pids, is_perf=False)
        pid_mapping[original_pid] = new_pid
        used_pids.add(new_pid)
    
    # Create perf_id mapping
    current_perf_ids = set()
    if "perf" in hierarchy:
        for category, details in hierarchy["perf"].items():
            for perf_id_detail in details.keys():
                if "@" in perf_id_detail:
                    original_perf_id = perf_id_detail.split("@")[0]
                    current_perf_ids.add(original_perf_id)
    
    for original_perf_id in sorted(current_perf_ids):
        new_perf_id = offset_id(original_perf_id, used_perf_ids, is_perf=True)
        perf_id_mapping[original_perf_id] = new_perf_id
        used_perf_ids.add(new_perf_id)
    
    return pid_mapping, perf_id_mapping


def remap_compound_reason(reason: str, pid_mapping: Dict[str, str], perf_id_mapping: Dict[str, str]) -> str:
    """Remap compound reasons like 'A,C' to 'AE,AG' using mappings."""
    if ',' in reason:
        # Split compound reason and remap each part
        parts = [part.strip() for part in reason.split(',')]
        remapped_parts = []
        for part in parts:
            if part in pid_mapping:
                remapped_parts.append(pid_mapping[part])
            elif part in perf_id_mapping:
                remapped_parts.append(perf_id_mapping[part])
            else:
                remapped_parts.append(part)  # Keep as-is if not found
        return ','.join(remapped_parts)
    else:
        # Single reason
        if reason in pid_mapping:
            return pid_mapping[reason]
        elif reason in perf_id_mapping:
            return perf_id_mapping[reason]
        else:
            return reason  # Keep as-is if not found





def _merge_hierarchy_with_semantic_matching(
    base: Dict[str, Any], 
    additional: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge hierarchies by matching same category+detail, only creating new IDs for different aspects."""
    
    # Initialize sections if not present
    for section in ["phy", "perf", "use"]:
        if section not in base:
            base[section] = {}
    
    # Merge physical section with semantic matching
    if "phy" in additional:
        for category, details in additional["phy"].items():
            # Look for matching category using normalized comparison
            matching_category = _find_matching_category(base["phy"], category)
            target_category = matching_category if matching_category else category
            
            if target_category not in base["phy"]:
                base["phy"][target_category] = {}
            
            for pid_detail, sentiments in details.items():
                if isinstance(sentiments, dict) and "@" in pid_detail:
                    original_pid, detail = pid_detail.split("@", 1)
                    
                    # Look for existing aspect with same detail in the target category
                    existing_pid_detail = _find_matching_aspect(base["phy"][target_category], detail)
                    
                    if existing_pid_detail:
                        # Merge with existing aspect
                        for sentiment, rid_list in sentiments.items():
                            if isinstance(rid_list, list):
                                if sentiment in base["phy"][target_category][existing_pid_detail]:
                                    base["phy"][target_category][existing_pid_detail][sentiment].extend(rid_list)
                                else:
                                    base["phy"][target_category][existing_pid_detail][sentiment] = rid_list
                    else:
                        # Create new aspect with unique ID
                        used_pids, _ = extract_used_ids(base)
                        new_pid = _generate_next_id(used_pids, is_perf=False)
                        new_pid_detail = f"{new_pid}@{detail}"
                        base["phy"][target_category][new_pid_detail] = sentiments.copy()
    
    # Merge performance section with semantic matching
    if "perf" in additional:
        for category, details in additional["perf"].items():
            # Look for matching category using normalized comparison
            matching_category = _find_matching_category(base["perf"], category)
            target_category = matching_category if matching_category else category
            
            if target_category not in base["perf"]:
                base["perf"][target_category] = {}
            
            for perf_detail, sentiments in details.items():
                if isinstance(sentiments, dict) and "@" in perf_detail:
                    original_perf_id, detail = perf_detail.split("@", 1)
                    
                    # Look for existing performance with same detail in the target category
                    existing_perf_detail = _find_matching_aspect(base["perf"][target_category], detail)
                    
                    if existing_perf_detail:
                        # Merge with existing performance
                        for sentiment, reasons in sentiments.items():
                            if isinstance(reasons, dict):
                                if sentiment in base["perf"][target_category][existing_perf_detail]:
                                    for reason, rid_list in reasons.items():
                                        # Need to remap reason IDs to match base hierarchy
                                        mapped_reason = _map_reason_to_base(reason, base)
                                        if isinstance(rid_list, list):
                                            if mapped_reason in base["perf"][target_category][existing_perf_detail][sentiment]:
                                                base["perf"][target_category][existing_perf_detail][sentiment][mapped_reason].extend(rid_list)
                                            else:
                                                base["perf"][target_category][existing_perf_detail][sentiment][mapped_reason] = rid_list
                                else:
                                    # Map all reasons in this sentiment
                                    mapped_reasons = {}
                                    for reason, rid_list in reasons.items():
                                        mapped_reason = _map_reason_to_base(reason, base)
                                        mapped_reasons[mapped_reason] = rid_list
                                    base["perf"][target_category][existing_perf_detail][sentiment] = mapped_reasons
                    else:
                        # Create new performance with unique ID
                        _, used_perf_ids = extract_used_ids(base)
                        new_perf_id = _generate_next_id(used_perf_ids, is_perf=True)
                        new_perf_detail = f"{new_perf_id}@{detail}"
                        
                        # Map reasons to base hierarchy IDs
                        mapped_sentiments = {}
                        for sentiment, reasons in sentiments.items():
                            if isinstance(reasons, dict):
                                mapped_reasons = {}
                                for reason, rid_list in reasons.items():
                                    mapped_reason = _map_reason_to_base(reason, base)
                                    mapped_reasons[mapped_reason] = rid_list
                                mapped_sentiments[sentiment] = mapped_reasons
                        
                        base["perf"][target_category][new_perf_detail] = mapped_sentiments
    
    # Merge use section - use cases are matched by normalized name
    if "use" in additional:
        for use_case, sentiments in additional["use"].items():
            if isinstance(sentiments, dict):
                # Look for matching use case using normalized comparison
                matching_use_case = _find_matching_use_case(base["use"], use_case)
                target_use_case = matching_use_case if matching_use_case else use_case
                
                if target_use_case in base["use"]:
                    # Merge with existing use case - combine reasons properly
                    for sentiment, reasons in sentiments.items():
                        if isinstance(reasons, dict):
                            if sentiment in base["use"][target_use_case]:
                                # Sentiment exists - combine the reasons by adding new ones
                                existing_reasons = base["use"][target_use_case][sentiment]
                                for reason, rid_list in reasons.items():
                                    mapped_reason = _map_reason_to_base(reason, base)
                                    if isinstance(rid_list, list):
                                        if mapped_reason in existing_reasons:
                                            # Extend existing reason's review list
                                            existing_reasons[mapped_reason].extend(rid_list)
                                        else:
                                            # Add new reason to existing sentiment
                                            existing_reasons[mapped_reason] = rid_list
                            else:
                                # New sentiment for existing use case
                                mapped_reasons = {}
                                for reason, rid_list in reasons.items():
                                    mapped_reason = _map_reason_to_base(reason, base)
                                    mapped_reasons[mapped_reason] = rid_list
                                base["use"][target_use_case][sentiment] = mapped_reasons
                else:
                    # New use case - map reasons to base hierarchy
                    mapped_sentiments = {}
                    for sentiment, reasons in sentiments.items():
                        if isinstance(reasons, dict):
                            mapped_reasons = {}
                            for reason, rid_list in reasons.items():
                                mapped_reason = _map_reason_to_base(reason, base)
                                mapped_reasons[mapped_reason] = rid_list
                            mapped_sentiments[sentiment] = mapped_reasons
                    base["use"][target_use_case] = mapped_sentiments
    
    return base


def _normalize_text(text: str) -> str:
    """Normalize text for semantic matching using lowercase and stemming."""
    if not text:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = text.strip().lower()
    
    # Remove punctuation and split into words
    words = re.findall(r'\b\w+\b', normalized)
    
    if _NLTK_AVAILABLE and _stemmer:
        # Apply stemming to each word
        stemmed_words = [_stemmer.stem(word) for word in words]
        return ' '.join(stemmed_words)
    else:
        # Fallback to just lowercase without stemming
        return ' '.join(words)


def _find_matching_aspect(category_details: Dict[str, Any], target_detail: str) -> str:
    """Find existing aspect with matching detail text using normalized comparison.
    
    Returns the full 'ID@detail' key in original format if match found.
    """
    target_normalized = _normalize_text(target_detail)
    
    for id_detail in category_details.keys():
        if "@" in id_detail:
            _, existing_detail = id_detail.split("@", 1)
            existing_normalized = _normalize_text(existing_detail)
            
            if existing_normalized == target_normalized:
                return id_detail  # Return original format
    return ""


def _find_matching_category(base_section: Dict[str, Any], target_category: str) -> str:
    """Find existing category with matching name using normalized comparison.
    
    Returns the original category name if match found.
    """
    target_normalized = _normalize_text(target_category)
    
    for existing_category in base_section.keys():
        existing_normalized = _normalize_text(existing_category)
        if existing_normalized == target_normalized:
            return existing_category  # Return original format
    return ""


def _find_matching_use_case(base_use_section: Dict[str, Any], target_use_case: str) -> str:
    """Find existing use case with matching name using normalized comparison.
    
    Returns the original use case name if match found.
    """
    target_normalized = _normalize_text(target_use_case)
    
    for existing_use_case in base_use_section.keys():
        existing_normalized = _normalize_text(existing_use_case)
        if existing_normalized == target_normalized:
            return existing_use_case  # Return original format
    return ""


def _generate_next_id(used_ids: Set[str], is_perf: bool = False) -> str:
    """Generate the next available ID in sequence."""
    if is_perf:
        base_chars = 'abcdefghijklmnopqrstuvwxyz'
    else:
        base_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    # Start with single characters
    for char in base_chars:
        if char not in used_ids:
            return char
    
    # Move to double characters
    for first in base_chars:
        for second in base_chars:
            double_char = first + second
            if double_char not in used_ids:
                return double_char
    
    # Fallback to triple characters (should rarely be needed)
    for first in base_chars:
        for second in base_chars:
            for third in base_chars:
                triple_char = first + second + third
                if triple_char not in used_ids:
                    return triple_char
    
    # Ultimate fallback
    return base_chars[0]


def _map_reason_to_base(reason: str, base_hierarchy: Dict[str, Any]) -> str:
    """Map reason IDs from additional hierarchy to matching aspects in base hierarchy."""
    if reason == "?":
        return "?"
    
    # Handle compound reasons (e.g., "A,C")
    if ',' in reason:
        parts = [part.strip() for part in reason.split(',')]
        mapped_parts = []
        for part in parts:
            mapped_part = _map_single_reason_to_base(part, base_hierarchy)
            mapped_parts.append(mapped_part)
        return ','.join(mapped_parts)
    else:
        return _map_single_reason_to_base(reason, base_hierarchy)


def _map_single_reason_to_base(reason_id: str, base_hierarchy: Dict[str, Any]) -> str:
    """Map a single reason ID to base hierarchy, finding semantically matching aspects."""
    # Check if reason_id already exists in base (no mapping needed)
    if _reason_exists_in_base(reason_id, base_hierarchy):
        return reason_id
    
    # Try to find semantically matching aspect in base hierarchy
    # First check if it's a physical aspect (uppercase) or performance aspect (lowercase)
    if reason_id.isupper():
        # Physical aspect - search in phy section
        matching_id = _find_matching_physical_aspect(reason_id, base_hierarchy)
        return matching_id if matching_id else reason_id
    elif reason_id.islower():
        # Performance aspect - search in perf section  
        matching_id = _find_matching_performance_aspect(reason_id, base_hierarchy)
        return matching_id if matching_id else reason_id
    else:
        # Unknown format, keep as-is
        return reason_id


def _reason_exists_in_base(reason_id: str, base_hierarchy: Dict[str, Any]) -> bool:
    """Check if a reason ID already exists in the base hierarchy."""
    # Check physical aspects
    if "phy" in base_hierarchy:
        for category, details in base_hierarchy["phy"].items():
            for pid_detail in details.keys():
                if "@" in pid_detail:
                    pid = pid_detail.split("@")[0]
                    if pid == reason_id:
                        return True
    
    # Check performance aspects  
    if "perf" in base_hierarchy:
        for category, details in base_hierarchy["perf"].items():
            for perf_detail in details.keys():
                if "@" in perf_detail:
                    perf_id = perf_detail.split("@")[0]
                    if perf_id == reason_id:
                        return True
    
    return False


def _find_matching_physical_aspect(reason_id: str, base_hierarchy: Dict[str, Any]) -> str:
    """Find physical aspect in base hierarchy that matches semantically."""
    if "phy" not in base_hierarchy:
        return reason_id
    
    # We don't have the original hierarchy to compare details, so keep original ID
    # In a more sophisticated version, we'd need access to the original hierarchy
    # to compare the detail text of reason_id with aspects in base_hierarchy
    return reason_id


def _find_matching_performance_aspect(reason_id: str, base_hierarchy: Dict[str, Any]) -> str:
    """Find performance aspect in base hierarchy that matches semantically."""
    if "perf" not in base_hierarchy:
        return reason_id
    
    # We don't have the original hierarchy to compare details, so keep original ID
    # In a more sophisticated version, we'd need access to the original hierarchy
    # to compare the detail text of reason_id with aspects in base_hierarchy
    return reason_id





def _merge_hierarchy_preserving_indices(
    base: Dict[str, Any], 
    additional: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge hierarchies while preserving offset indices and handling ID collisions.
    
    Unlike semantic merging, this function treats each hierarchy as independent
    and handles ID collisions by remapping IDs in the additional hierarchy.
    Review indices are preserved exactly as they were offset.
    """
    
    # Initialize sections if not present
    for section in ["phy", "perf", "use"]:
        if section not in base:
            base[section] = {}
    
    # Get used IDs from base hierarchy to avoid collisions
    used_pids, used_perf_ids = extract_used_ids(base)
    
    # Create ID mappings for additional hierarchy to avoid collisions
    pid_mapping, perf_id_mapping = create_id_mapping(additional, used_pids, used_perf_ids)
    
    # Merge physical section with ID remapping
    if "phy" in additional:
        for category, details in additional["phy"].items():
            if category not in base["phy"]:
                base["phy"][category] = {}
            
            for pid_detail, sentiments in details.items():
                if isinstance(sentiments, dict) and "@" in pid_detail:
                    # Remap PID to avoid collisions
                    original_pid, detail = pid_detail.split("@", 1)
                    new_pid = pid_mapping.get(original_pid, original_pid)
                    new_pid_detail = f"{new_pid}@{detail}"
                    
                    # Add to base with preserved indices (no merging of review lists)
                    base["phy"][category][new_pid_detail] = sentiments.copy()
    
    # Merge performance section with ID remapping
    if "perf" in additional:
        for category, details in additional["perf"].items():
            if category not in base["perf"]:
                base["perf"][category] = {}
            
            for perf_detail, sentiments in details.items():
                if isinstance(sentiments, dict) and "@" in perf_detail:
                    # Remap perf_id to avoid collisions
                    original_perf_id, detail = perf_detail.split("@", 1)
                    new_perf_id = perf_id_mapping.get(original_perf_id, original_perf_id)
                    new_perf_detail = f"{new_perf_id}@{detail}"
                    
                    # Remap reason IDs in sentiments to match remapped physical IDs
                    remapped_sentiments = {}
                    for sentiment, reasons in sentiments.items():
                        if isinstance(reasons, dict):
                            remapped_reasons = {}
                            for reason, rid_list in reasons.items():
                                # Remap reason IDs using the mappings
                                new_reason = remap_compound_reason(reason, pid_mapping, perf_id_mapping)
                                remapped_reasons[new_reason] = rid_list
                            remapped_sentiments[sentiment] = remapped_reasons
                    
                    # Add to base with preserved indices
                    base["perf"][category][new_perf_detail] = remapped_sentiments
    
    # Merge use section with ID remapping
    if "use" in additional:
        for use_case, sentiments in additional["use"].items():
            if isinstance(sentiments, dict):
                # Remap reason IDs in use case sentiments
                remapped_sentiments = {}
                for sentiment, reasons in sentiments.items():
                    if isinstance(reasons, dict):
                        remapped_reasons = {}
                        for reason, rid_list in reasons.items():
                            # Remap reason IDs using the mappings
                            new_reason = remap_compound_reason(reason, pid_mapping, perf_id_mapping)
                            remapped_reasons[new_reason] = rid_list
                        remapped_sentiments[sentiment] = remapped_reasons
                
                # Add to base (may create duplicate use case names, but that's ok)
                if use_case in base["use"]:
                    # If use case exists, create a unique name to avoid merging
                    counter = 1
                    unique_use_case = f"{use_case} (batch {counter})"
                    while unique_use_case in base["use"]:
                        counter += 1
                        unique_use_case = f"{use_case} (batch {counter})"
                    base["use"][unique_use_case] = remapped_sentiments
                else:
                    base["use"][use_case] = remapped_sentiments
    
    return base


def merge_hierarchies_batch_with_mappings(
    hierarchies: List[Dict[str, Any]], 
    review_mappings: List[Dict[int, str]]
) -> Tuple[Dict[str, Any], Dict[int, str]]:
    """Merge multiple extraction hierarchies with review ID mappings.
    
    Args:
        hierarchies: List of batch hierarchies (each using indices 0,1,2,...)
        review_mappings: List of mappings from batch indices to actual review IDs
        
    Returns:
        Tuple of (merged_hierarchy, global_review_mapping)
        
    The function offsets indices in each batch to prevent collisions:
    - Batch 1: 0,1,2 → 0,1,2
    - Batch 2: 0,1,2 → 3,4,5  
    - Batch 3: 0,1,2 → 6,7,8
    etc.
    """
    if not hierarchies:
        return {}, {}
    
    if len(hierarchies) == 1:
        return hierarchies[0], review_mappings[0] if review_mappings else {}
    
    # Calculate index offsets for each batch
    global_review_mapping = {}
    offset_hierarchies = []
    current_offset = 0
    
    for i, (hierarchy, mapping) in enumerate(zip(hierarchies, review_mappings)):
        if not hierarchy:
            continue
            
        # Create offset hierarchy with adjusted indices
        offset_hierarchy = _offset_hierarchy_indices(hierarchy, current_offset)
        offset_hierarchies.append(offset_hierarchy)
        
        # Create global review mapping with offset indices
        for batch_index, actual_review_id in mapping.items():
            global_index = batch_index + current_offset
            global_review_mapping[global_index] = actual_review_id
        
        # Calculate next offset based on max index in this batch's mapping
        if mapping:
            max_batch_index = max(mapping.keys())
            current_offset += max_batch_index + 1
    
    # Merge offset hierarchies while preserving indices (no semantic merging for batches)
    merged = offset_hierarchies[0].copy()
    for hierarchy in offset_hierarchies[1:]:
        if hierarchy:
            merged = _merge_hierarchy_preserving_indices(merged, hierarchy)
    
    return merged, global_review_mapping


def _offset_hierarchy_indices(hierarchy: Dict[str, Any], offset: int) -> Dict[str, Any]:
    """Offset all review indices in a hierarchy by the given amount.
    
    Args:
        hierarchy: Hierarchy with indices starting from 0
        offset: Amount to add to each index
        
    Returns:
        New hierarchy with offset indices
    """
    if offset == 0:
        return hierarchy  # No offset needed
    
    offset_hierarchy = {}
    
    # Process physical section
    if "phy" in hierarchy:
        offset_hierarchy["phy"] = {}
        for category, details in hierarchy["phy"].items():
            offset_hierarchy["phy"][category] = {}
            for pid_detail, sentiments in details.items():
                offset_sentiments = {}
                for sentiment, rid_list in sentiments.items():
                    if isinstance(rid_list, list):
                        offset_sentiments[sentiment] = [rid + offset for rid in rid_list]
                    else:
                        offset_sentiments[sentiment] = rid_list
                offset_hierarchy["phy"][category][pid_detail] = offset_sentiments
    
    # Process performance section
    if "perf" in hierarchy:
        offset_hierarchy["perf"] = {}
        for category, details in hierarchy["perf"].items():
            offset_hierarchy["perf"][category] = {}
            for perf_detail, sentiments in details.items():
                offset_sentiments = {}
                for sentiment, reasons in sentiments.items():
                    if isinstance(reasons, dict):
                        offset_reasons = {}
                        for reason, rid_list in reasons.items():
                            if isinstance(rid_list, list):
                                offset_reasons[reason] = [rid + offset for rid in rid_list]
                            else:
                                offset_reasons[reason] = rid_list
                        offset_sentiments[sentiment] = offset_reasons
                    else:
                        offset_sentiments[sentiment] = reasons
                offset_hierarchy["perf"][category][perf_detail] = offset_sentiments
    
    # Process use section
    if "use" in hierarchy:
        offset_hierarchy["use"] = {}
        for use_case, sentiments in hierarchy["use"].items():
            offset_sentiments = {}
            for sentiment, reasons in sentiments.items():
                if isinstance(reasons, dict):
                    offset_reasons = {}
                    for reason, rid_list in reasons.items():
                        if isinstance(rid_list, list):
                            offset_reasons[reason] = [rid + offset for rid in rid_list]
                        else:
                            offset_reasons[reason] = rid_list
                    offset_sentiments[sentiment] = offset_reasons
                else:
                    offset_sentiments[sentiment] = reasons
            offset_hierarchy["use"][use_case] = offset_sentiments
    
    return offset_hierarchy 