"""Integration test runner for review analysis pipeline.

This module runs the review analysis pipeline stages in sequence:
1. Extraction stage - extracts aspects from reviews
2. Categorization stage - categorizes aspects into taxonomies  
3. Consolidation stage - consolidates taxonomies from multiple products

Each stage depends on the output of the previous stage, so they must run in order.
"""

import pytest
from pathlib import Path


class TestReviewAnalysisPipeline:
    """Integration test runner for the complete review analysis pipeline."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_pipeline_sequence(self):
        """Run the complete review analysis pipeline in sequence.
        
        This test orchestrates the execution of:
        1. Extraction stage tests (generates extraction results)
        2. Categorization stage tests (uses extraction results)
        3. Consolidation stage tests (uses categorization results)
        
        Each stage must complete successfully before the next stage runs.
        """
        import subprocess
        import sys
        from pathlib import Path
        
        # Get the backend directory
        backend_dir = Path(__file__).resolve().parents[3]
        
        print("\n" + "="*80)
        print("🚀 STARTING REVIEW ANALYSIS PIPELINE INTEGRATION TEST")
        print("="*80)
        
        # Stage 1: Run extraction tests
        print("\n📋 STAGE 1: Running extraction stage tests...")
        print("-" * 50)
        
        extraction_cmd = [
            sys.executable, "-m", "pytest", 
            "review_analysis/tests/llm/test_review_extraction_stage.py",
            "-v", "-s", "--tb=short"
        ]
        
        result = subprocess.run(
            extraction_cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode != 0:
            pytest.fail(f"Extraction stage tests failed with return code {result.returncode}")
        
        print("✅ Extraction stage completed successfully")
        
        # Stage 2: Run categorization tests
        print("\n🏷️  STAGE 2: Running categorization stage tests...")
        print("-" * 50)
        
        categorization_cmd = [
            sys.executable, "-m", "pytest",
            "review_analysis/tests/llm/test_review_categorization_stage.py", 
            "-v", "-s", "--tb=short"
        ]
        
        result = subprocess.run(
            categorization_cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode != 0:
            pytest.fail(f"Categorization stage tests failed with return code {result.returncode}")
            
        print("✅ Categorization stage completed successfully")
        
        # Stage 3: Run consolidation tests
        print("\n🔄 STAGE 3: Running consolidation stage tests...")
        print("-" * 50)
        
        consolidation_cmd = [
            sys.executable, "-m", "pytest",
            "review_analysis/tests/llm/test_review_consolidation_stage.py",
            "-v", "-s", "--tb=short"
        ]
        
        result = subprocess.run(
            consolidation_cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode != 0:
            pytest.fail(f"Consolidation stage tests failed with return code {result.returncode}")
            
        print("✅ Consolidation stage completed successfully")
        
        print("\n" + "="*80)
        print("🎉 REVIEW ANALYSIS PIPELINE INTEGRATION TEST COMPLETED SUCCESSFULLY")
        print("="*80)
        
        # Verify that all expected output files exist
        test_data_dir = Path(__file__).parent / "test_data"
        expected_files = [
            "real_amazon_extraction_results.json",
            "real_amazon_categorization_results.json", 
            "real_amazon_consolidation_results.json"
        ]
        
        print("\n📁 Verifying output files:")
        for filename in expected_files:
            filepath = test_data_dir / filename
            if filepath.exists():
                print(f"   ✅ {filename}")
            else:
                print(f"   ❌ {filename} (missing)")
                
        print("\n🔗 Pipeline stages completed in sequence:")
        print("   1. ✅ Extraction → Generated aspect taxonomies")
        print("   2. ✅ Categorization → Categorized aspects into groups") 
        print("   3. ✅ Consolidation → Consolidated taxonomies across products") 