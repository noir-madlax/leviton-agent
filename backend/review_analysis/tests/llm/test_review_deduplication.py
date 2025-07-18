"""Tests for review analysis deduplication utilities."""

import pytest
from typing import List

from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO
from review_analysis.llm.review_dedup_util import (
    deduplicate_review_categories,
    deduplicate_review_category_batches,
    print_review_deduplication_summary,
    _create_category_stemmed_key,
    ReviewDeduplicationResult,
)


class TestReviewDeduplication:
    """Test cases for review analysis deduplication utilities."""

    def test_stemmed_key_creation(self):
        """Test that stemmed keys are created correctly for different category patterns."""
        # Test basic words (NLTK PorterStemmer results)
        assert _create_category_stemmed_key("Brightness Control") == "bright_control"
        assert _create_category_stemmed_key("Device Connectivity") == "connect_devic"
        
        # Test plurals and suffixes (NLTK PorterStemmer results)
        assert _create_category_stemmed_key("Smart Features") == "featur_smart"
        assert _create_category_stemmed_key("Connection Capabilities") == "capabl_connect"
        
        # Test word ordering (should be sorted)
        assert _create_category_stemmed_key("Smart Control") == _create_category_stemmed_key("Control Smart")
        
        # Test stop words removal
        assert _create_category_stemmed_key("Control of the Device") == "control_devic"
        assert _create_category_stemmed_key("Features and Functions") == "featur_function"
        
        # Test NLTK stemming patterns (actual NLTK behavior)
        assert _create_category_stemmed_key("Dimming Capabilities") == "capabl_dim"
        assert _create_category_stemmed_key("Dimmer Capability") == "capabl_dimmer"  # NLTK keeps "dimmer" as-is
        
        # Test Wi-Fi handling
        assert _create_category_stemmed_key("WiFi Connectivity") == "connect_wifi"
        assert _create_category_stemmed_key("Wi-Fi Connection") == "connect_wifi"  # Should normalize to same

    def test_basic_deduplication(self):
        """Test basic deduplication functionality."""
        categories = [
            TaxonomyDTO(name="Brightness Control", definition="Controls brightness levels"),
            TaxonomyDTO(name="Control Brightness", definition="Manages light brightness"),  # Should merge
            TaxonomyDTO(name="Device Connectivity", definition="Network connection features"),
            TaxonomyDTO(name="Smart Features", definition="Advanced smart capabilities"),
        ]
        
        result = deduplicate_review_categories(categories)
        
        # Should have 3 unique categories (2 brightness ones merged)
        assert len(result.unique_categories) == 3
        assert len(result.duplicate_groups) == 1
        
        # Check name mapping
        assert result.name_mapping["Brightness Control"] == "Brightness Control"  # Representative
        assert result.name_mapping["Control Brightness"] == "Brightness Control"  # Mapped to representative
        assert result.name_mapping["Device Connectivity"] == "Device Connectivity"  # Unchanged
        
        # Check that definitions are merged
        brightness_category = next(cat for cat in result.unique_categories if cat.name == "Brightness Control")
        assert "Controls brightness levels" in brightness_category.definition
        assert "Manages light brightness" in brightness_category.definition

    def test_no_duplicates(self):
        """Test deduplication when there are no duplicates."""
        categories = [
            TaxonomyDTO(name="Installation Process", definition="How to install"),
            TaxonomyDTO(name="Battery Life", definition="Power duration"),
            TaxonomyDTO(name="Build Quality", definition="Construction quality"),
        ]
        
        result = deduplicate_review_categories(categories)
        
        assert len(result.unique_categories) == 3
        assert len(result.duplicate_groups) == 0
        
        # All mappings should be identity
        for category in categories:
            assert result.name_mapping[category.name] == category.name

    def test_empty_input(self):
        """Test deduplication with empty input."""
        result = deduplicate_review_categories([])
        
        assert len(result.unique_categories) == 0
        assert len(result.duplicate_groups) == 0
        assert len(result.name_mapping) == 0

    def test_batch_deduplication(self):
        """Test deduplication across multiple batches."""
        batch1 = [
            TaxonomyDTO(name="Smart Control", definition="Smart controlling"),
            TaxonomyDTO(name="Device Setup", definition="Setup process"),
        ]
        
        batch2 = [
            TaxonomyDTO(name="Control Smart", definition="Smart control features"),  # Should merge with batch1
            TaxonomyDTO(name="Installation Guide", definition="Installation process"),
        ]
        
        batch3 = [
            TaxonomyDTO(name="Smart Control", definition="Smart control duplicate"),  # Exact duplicate
            TaxonomyDTO(name="Battery Performance", definition="Battery performance"),
        ]
        
        batches = [batch1, batch2, batch3]
        deduped_batches, global_mapping = deduplicate_review_category_batches(batches)
        
        # Should have fewer total categories due to deduplication
        total_deduped = sum(len(batch) for batch in deduped_batches)
        assert total_deduped < 6  # Original total was 6
        
        # Check global mapping includes all original names
        assert "Smart Control" in global_mapping
        assert "Control Smart" in global_mapping
        assert global_mapping["Smart Control"] == global_mapping["Control Smart"]  # Should map to same representative

    def test_complex_category_patterns(self):
        """Test deduplication with complex review category patterns."""
        categories = [
            TaxonomyDTO(name="Dimming Capabilities", definition="Ability to dim lights"),
            TaxonomyDTO(name="Dimmer Capability", definition="Dimming functionality"),  # Won't merge with NLTK stemming
            TaxonomyDTO(name="WiFi Connectivity", definition="WiFi connection features"),
            TaxonomyDTO(name="Wi-Fi Connection", definition="Wireless network connection"),  # Should merge
            TaxonomyDTO(name="Installation Difficulty", definition="How hard to install"),
            TaxonomyDTO(name="Setup Complexity", definition="Installation complexity"),  # Different enough to not merge
        ]
        
        result = deduplicate_review_categories(categories)
        
        # Should merge wifi categories, but not dimming vs dimmer (NLTK keeps them separate)
        assert len(result.unique_categories) < len(categories)
        
        # Verify specific merges - only wifi categories should merge
        wifi_names = {name for name in result.name_mapping.keys() if "wifi" in name.lower() or "wi-fi" in name.lower()}
        if len(wifi_names) > 1:
            representatives = {result.name_mapping[name] for name in wifi_names}
            assert len(representatives) == 1  # All wifi categories should map to same representative

    def test_print_summary_no_error(self):
        """Test that print summary doesn't raise errors."""
        categories = [
            TaxonomyDTO(name="Test Category 1", definition="Test def 1"),
            TaxonomyDTO(name="Category Test 1", definition="Test def 2"),  # Should merge
            TaxonomyDTO(name="Different Category", definition="Different def"),
        ]
        
        result = deduplicate_review_categories(categories)
        
        # Should not raise any exceptions
        print_review_deduplication_summary(result)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with single category
        single_result = deduplicate_review_categories([
            TaxonomyDTO(name="Single Category", definition="Only one")
        ])
        assert len(single_result.unique_categories) == 1
        assert len(single_result.duplicate_groups) == 0
        
        # Test with identical categories
        identical_categories = [
            TaxonomyDTO(name="Same Name", definition="First definition"),
            TaxonomyDTO(name="Same Name", definition="Second definition"),
        ]
        identical_result = deduplicate_review_categories(identical_categories)
        assert len(identical_result.unique_categories) == 1
        assert "First definition" in identical_result.unique_categories[0].definition
        assert "Second definition" in identical_result.unique_categories[0].definition
        
        # Test with empty definitions
        empty_def_categories = [
            TaxonomyDTO(name="Category A", definition=""),
            TaxonomyDTO(name="Category B", definition=""),
        ]
        empty_result = deduplicate_review_categories(empty_def_categories)
        assert len(empty_result.unique_categories) == 2  # Different names, should not merge


if __name__ == "__main__":
    pytest.main([__file__]) 