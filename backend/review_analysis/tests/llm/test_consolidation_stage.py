"""Tests for review analysis consolidation stage.

This module tests the consolidation stage with sample extraction results
and includes real LLM integration testing for comprehensive workflow validation.

Test Coverage:
--------------

1. **test_template_loading**: Tests prompt template loading functionality
2. **test_additional_template_vars**: Tests review-specific template variables
3. **test_build_prompt**: Tests prompt building with A_*/B_* taxonomy formatting
4. **test_validation_***: Tests validation logic with various response formats
5. **test_produce_result**: Tests result production from valid LLM responses
6. **test_real_llm_consolidation**: Real LLM integration test with orchestration
7. **test_orchestration_workflow**: End-to-end workflow similar to product_segment service

Configuration:
--------------
- Uses extraction results from test_data/sample_extraction_results.json
- Aspect types: physical, performance, use case
- Real LLM calls for integration testing
"""

import pytest
from unittest.mock import Mock, patch
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO
from core.llm_taxonomy_pipeline.consolidation_base import ConsolidationStageContext
from core.utils.llm_utils import ValidationResult
from review_analysis.llm.consolidation_stage import ConsolidationStage

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"
SAMPLE_EXTRACTION_PATH = TEST_DATA_DIR / "sample_extraction_results.json"
PRODUCT_CATEGORY = "Kids Art and Craft Tool"


class TestConsolidationStage:
    """Test consolidation stage functionality."""

    @pytest.fixture
    def stage(self):
        """Create consolidation stage with test context."""
        return ConsolidationStage(
            aspect_type="physical",
            product_categories={"Electronics", "Home & Garden"}
        )

    @pytest.fixture
    def real_extraction_data(self) -> Dict[str, Any]:
        """Load real extraction results for consolidation testing."""
        results_path = TEST_DATA_DIR / "real_amazon_extraction_results.json"
        if not results_path.exists():
            pytest.skip(f"Real extraction results not found: {results_path}")
        
        with open(results_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📁 Loaded real extraction data from {results_path}")
        print(f"   - Aspects extracted: {data['extraction_result']['aspects_extracted']}")
        print(f"   - Reviews processed: {data['test_metadata']['reviews_count']}")
        
        return data

    @pytest.fixture
    def sample_context(self):
        """Create sample consolidation context."""
        taxonomy_a = [
            TaxonomyDTO(name="Color", definition="Product color aspects"),
            TaxonomyDTO(name="Size", definition="Product size aspects")
        ]
        taxonomy_b = [
            TaxonomyDTO(name="Material", definition="Product material aspects"),
            TaxonomyDTO(name="Weight", definition="Product weight aspects")
        ]
        return ConsolidationStageContext(
            product_category="test_category",
            taxonomy_a=taxonomy_a, 
            taxonomy_b=taxonomy_b
        )

    @pytest.mark.asyncio
    async def test_prompt_templates_and_build(self, stage, sample_context):
        """Combined test for template loading, additional vars, and prompt building."""

        # ------------------------------------------------------------------
        # 1. Template loading assertions
        # ------------------------------------------------------------------
        print("\n🔍 [1/3] Testing template loading functionality (real templates)")

        assert stage._consolidate_prompt_template, (
            "Consolidate prompt template should not be empty"
        )
        assert "{{taxonomy_a}}" in stage._consolidate_prompt_template
        assert "{{taxonomy_b}}" in stage._consolidate_prompt_template
        assert "{{aspect_definition}}" in stage._consolidate_prompt_template

        assert stage._retry_prompt_template, (
            "Retry prompt template should not be empty"
        )
        assert "{error_details}" in stage._retry_prompt_template
        print("✅ Template loading validated")

        # ------------------------------------------------------------------
        # 2. Additional template variables assertions
        # ------------------------------------------------------------------
        print("\n🔍 [2/3] Testing additional template variables")
        vars = stage._get_additional_template_vars(sample_context)

        print("📋 Template variables:")
        for k, v in vars.items():
            preview = v if len(v) < 120 else v[:117] + "..."
            print(f"   - {k}: {preview}")

        assert vars["aspect_type"] == "physical"
        assert "Electronics" in vars["product_context"]
        assert "Home & Garden" in vars["product_context"]
        assert vars.get("aspect_definition"), "aspect_definition should not be empty"
        print("✅ Additional template variables validated")

        # ------------------------------------------------------------------
        # 3. Prompt building assertions
        # ------------------------------------------------------------------
        print("\n🔍 [3/3] Testing prompt building with A_*/B_* taxonomy formatting")

        prompt = await stage._build_prompt(sample_context)

        print("=" * 40 + " GENERATED PROMPT " + "=" * 40)
        print(prompt)
        print("=" * 100)

        # Check for IDs and expected content in the prompt
        assert "A_0" in prompt
        assert "A_1" in prompt
        assert "B_0" in prompt
        assert "B_1" in prompt
        assert "Color" in prompt
        assert "physical" in prompt
        assert "Components or inherent physical properties" in prompt
        print("✅ Prompt built and validated successfully")

    def test_validation_success(self, stage, sample_context):
        """Test successful validation."""
        print(f"\n🔍 Testing successful validation")
        valid_response = '''
        {
            "Appearance": {
                "definition": "Visual aspects",
                "ids": ["A_0", "B_0"]
            },
            "Physical Properties": {
                "definition": "Physical characteristics", 
                "ids": ["A_1", "B_1"]
            }
        }
        '''
        
        result = stage._validate(valid_response, sample_context)
        print(f"📊 Validation result: {result.ok}")
        print(f"📋 Error categories: {result.error_categories}")
        assert result.ok == True
        assert len(result.error_categories["format_errors"]) == 0
        print(f"✅ Successful validation test passed")

    def test_validation_missing_ids(self, stage, sample_context):
        """Test validation with missing IDs."""
        print(f"\n🔍 Testing validation with missing IDs")
        invalid_response = '''
        {
            "Appearance": {
                "definition": "Visual aspects",
                "ids": ["A_0"]
            }
        }
        '''
        
        result = stage._validate(invalid_response, sample_context)
        print(f"📊 Validation result: {result.ok}")
        print(f"📋 Error categories: {result.error_categories}")
        assert result.ok == False
        assert any("Missing assignments" in error 
                  for error in result.error_categories["completeness_errors"])
        print(f"✅ Missing IDs validation test passed")

    def test_validation_duplicate_ids(self, stage, sample_context):
        """Test validation with duplicate IDs."""
        invalid_response = '''
        {
            "Category1": {
                "definition": "Test",
                "ids": ["A_0", "A_1"]
            },
            "Category2": {
                "definition": "Test", 
                "ids": ["A_0", "B_0", "B_1"]
            }
        }
        '''
        
        result = stage._validate(invalid_response, sample_context)
        assert result.ok == False
        assert any("appears in multiple categories" in error
                  for error in result.error_categories["completeness_errors"])

    @pytest.mark.asyncio
    async def test_produce_result(self, stage, sample_context):
        """Test result production."""
        print(f"\n🔍 Testing result production")
        valid_response = '''
        {
            "Appearance": {
                "definition": "Visual aspects", 
                "ids": ["A_0", "B_0"]
            },
            "Physical Properties": {
                "definition": "Physical characteristics",
                "ids": ["A_1", "B_1"] 
            }
        }
        '''
        
        with patch('core.utils.llm_utils.extract_json', return_value=valid_response.strip()):
            result = await stage._produce_result(valid_response, sample_context, 1)
            
            print(f"📊 Result produced:")
            print(f"   - Consolidated taxonomies: {len(result.taxonomies_consolidated)}")
            for i, tax in enumerate(result.taxonomies_consolidated):
                print(f"   - [{i}] {tax.taxonomy.name}: {len(tax.original_taxonomies)} original taxonomies")
            
            assert len(result.taxonomies_consolidated) == 2
            assert result.taxonomies_consolidated[0].taxonomy.name == "Appearance"
            assert len(result.taxonomies_consolidated[0].original_taxonomies) == 2
            print(f"✅ Result production test passed")

    @pytest.mark.asyncio
    async def test_real_llm_consolidation_with_amazon_data(
        self,
        real_extraction_data: Dict[str, Any]
    ) -> None:
        """Real LLM consolidation test using extracted Amazon review aspects."""
        
        print(f"\n" + "="*80)
        print(f"🤖 REAL LLM CONSOLIDATION WITH AMAZON EXTRACTION DATA")
        print(f"="*80)
        
        extraction_result = real_extraction_data["extraction_result"]["review_hierarchy"]
        
        # Convert extraction result to taxonomies for consolidation testing
        # We'll create two "batches" from the extracted aspects to test consolidation
        
        # Extract physical aspects
        phy_aspects = []
        if "phy" in extraction_result and extraction_result["phy"]:
            for category, aspects in extraction_result["phy"].items():
                for aspect_key, sentiments in aspects.items():
                    # Convert aspect_key format (e.g., "A@colorful") to taxonomy
                    aspect_name = aspect_key.split('@')[1] if '@' in aspect_key else aspect_key
                    phy_aspects.append(TaxonomyDTO(
                        name=f"{category}_{aspect_name}",
                        definition=f"Physical aspect: {aspect_name} in {category}"
                    ))
        
        if len(phy_aspects) < 2:
            # Create mock taxonomies that can be consolidated (similar aspects)
            phy_aspects = [
                TaxonomyDTO(name="Red Color", definition="Red coloring and appearance characteristics"),
                TaxonomyDTO(name="Blue Color", definition="Blue coloring and appearance characteristics"), 
                TaxonomyDTO(name="Bright Colors", definition="Vibrant and bright color schemes"),
                TaxonomyDTO(name="Small Size", definition="Compact and small dimensions"),
                TaxonomyDTO(name="Portable Size", definition="Easy to carry and transport"),
                TaxonomyDTO(name="Mini Format", definition="Miniature and tiny form factor")
            ]
            print(f"📊 Using mock physical aspects designed for consolidation testing")
        else:
            print(f"📊 Using {len(phy_aspects)} real physical aspects from extraction")
        
        # Split into two batches for consolidation testing
        mid_point = len(phy_aspects) // 2
        taxonomy_a = phy_aspects[:mid_point] if mid_point > 0 else phy_aspects[:2]
        taxonomy_b = phy_aspects[mid_point:] if mid_point > 0 else phy_aspects[2:4]
        
        # Ensure we have at least 1 taxonomy in each batch
        if not taxonomy_a:
            taxonomy_a = [phy_aspects[0]]
        if not taxonomy_b:
            taxonomy_b = [phy_aspects[-1]] if len(phy_aspects) > 1 else [TaxonomyDTO(name="Test", definition="Test")]
        
        print(f"📦 Batch A taxonomies: {[t.name for t in taxonomy_a]}")
        print(f"📦 Batch B taxonomies: {[t.name for t in taxonomy_b]}")
        print(f"="*80)
        
        # Create consolidation stage for physical aspects
        consolidation_stage = ConsolidationStage(
            aspect_type="physical",
            product_categories={"Kids Arts & Crafts"}
        )
        
        # Create consolidation context
        context = ConsolidationStageContext(
            product_category="Kids Arts & Crafts",
            taxonomy_a=taxonomy_a,
            taxonomy_b=taxonomy_b
        )
        
        # Execute real LLM consolidation
        print(f"🚀 Executing real LLM consolidation...")
        result = await consolidation_stage.execute(context)
        
        print(f"📊 REAL LLM CONSOLIDATION RESULTS:")
        print(f"   - Consolidated taxonomies: {len(result.taxonomies_consolidated)}")
        
        for i, consolidated in enumerate(result.taxonomies_consolidated):
            print(f"   📁 [{i}] {consolidated.taxonomy.name}")
            print(f"       Definition: {consolidated.taxonomy.definition}")
            print(f"       Original taxonomies: {[t.name for t in consolidated.original_taxonomies]}")
        print(f"="*80)
        
        # Save consolidation results
        save_path = TEST_DATA_DIR / "real_amazon_consolidation_results.json"
        consolidation_data = {
            "test_metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "source": "real_amazon_extraction_consolidation",
                "aspect_type": "physical",
                "input_taxonomies_a": len(taxonomy_a),
                "input_taxonomies_b": len(taxonomy_b),
                "output_taxonomies": len(result.taxonomies_consolidated)
            },
            "consolidation_result": {
                "taxonomies_consolidated": [
                    {
                        "name": cons.taxonomy.name,
                        "definition": cons.taxonomy.definition,
                        "original_count": len(cons.original_taxonomies),
                        "original_names": [t.name for t in cons.original_taxonomies]
                    }
                    for cons in result.taxonomies_consolidated
                ]
            },
            "input_context": {
                "product_category": context.product_category,
                "taxonomy_a_names": [t.name for t in taxonomy_a],
                "taxonomy_b_names": [t.name for t in taxonomy_b]
            }
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(consolidation_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved real consolidation results to: {save_path}")
        print(f"📊 Consolidation summary:")
        print(f"   - Input: {len(taxonomy_a)} + {len(taxonomy_b)} = {len(taxonomy_a) + len(taxonomy_b)} taxonomies")
        print(f"   - Output: {len(result.taxonomies_consolidated)} consolidated taxonomies")
        print(f"   - Reduction: {((len(taxonomy_a) + len(taxonomy_b) - len(result.taxonomies_consolidated)) / (len(taxonomy_a) + len(taxonomy_b)) * 100):.1f}%")
        print(f"="*80)
        
        # Verify result structure
        assert len(result.taxonomies_consolidated) > 0
        assert len(result.taxonomies_consolidated) <= len(taxonomy_a) + len(taxonomy_b)
        
        # Verify all original taxonomies are accounted for
        total_originals = sum(len(cons.original_taxonomies) for cons in result.taxonomies_consolidated)
        expected_total = len(taxonomy_a) + len(taxonomy_b)
        assert total_originals == expected_total, f"Expected {expected_total} original taxonomies, got {total_originals}"
        
        print(f"\n✅ Real LLM consolidation completed successfully!")
        print(f"   - Consolidated {len(taxonomy_a) + len(taxonomy_b)} taxonomies into {len(result.taxonomies_consolidated)}")
        print(f"   - All original taxonomies properly mapped")
        print(f"   - Results saved for further testing")

