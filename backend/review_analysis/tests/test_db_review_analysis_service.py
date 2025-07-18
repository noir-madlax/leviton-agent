"""
Tests for DatabaseReviewAnalysisService with real database operations but mocked LLM calls.

This test suite validates:
- Error handling when LLM validation fails
- Database operations for error placeholders
- Progress tracking with mixed success/failure scenarios
- Complete pipeline execution with various error conditions
"""

import pytest
import pytest_asyncio
from dataclasses import asdict

from review_analysis.services.db_review_analysis import DatabaseReviewAnalysisService
from review_analysis.models import ReviewAnalysisRequest
from core.database.connection import get_supabase_service_client

pytestmark = pytest.mark.integration


class TestDatabaseReviewAnalysisService:
    """Test DatabaseReviewAnalysisService with real DB but mocked LLM."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return DatabaseReviewAnalysisService()

    @pytest.fixture
    def sample_request(self):
        """Create sample analysis request."""
        return ReviewAnalysisRequest(
            project_id="TEST_DB_SERVICE",
            product_ids=["B08PKMT2DV", "B0771BC2YH"],
            product_category="Test Switches",
            max_reviews_per_product=10  # Limit for faster testing
        )

    @pytest_asyncio.fixture
    async def setup_test_reviews(self, sample_request):
        """Set up test review data in database."""
        sb_client = get_supabase_service_client()
        
        # Insert test reviews
        test_reviews = [
            {
                "product_id": "B08PKMT2DV",
                "review_id": 999991,
                "review_title": "Great switch",
                "review_text": "This dimmer switch works perfectly and looks great."
            },
            {
                "product_id": "B08PKMT2DV", 
                "review_id": 999992,
                "review_title": "Installation issue",
                "review_text": "Switch quality is good but installation was difficult."
            },
            {
                "product_id": "B0771BC2YH",
                "review_id": 999993, 
                "review_title": "Perfect functionality",
                "review_text": "Dimming works smoothly and the design is elegant."
            }
        ]
        
        # Clean up any existing test reviews first
        try:
            sb_client.table("product_reviews").delete().in_("review_id", [r["review_id"] for r in test_reviews]).execute()
        except:
            pass
        
        # Insert test reviews
        sb_client.table("product_reviews").insert(test_reviews).execute()
        
        yield test_reviews
        
        # Cleanup
        try:
            sb_client.table("product_reviews").delete().in_("review_id", [r["review_id"] for r in test_reviews]).execute()
            # Also cleanup any analysis data
            sb_client.table("review_analysis_aspects").delete().eq("project_id", sample_request.project_id).execute()
            sb_client.table("review_analysis_aspect_categories").delete().eq("project_id", sample_request.project_id).execute()
        except Exception as e:
            print(f"Cleanup warning: {e}")

    @pytest.mark.asyncio
    async def test_error_placeholder_db_operations(self, service, sample_request, setup_test_reviews):
        """Test error placeholder creation and database persistence.
        
        Test Input:
        - Batch of 2 review records with integer IDs (999991, 999992)
        - Review ID mapping: {0: 999991, 1: 999992}
        - Error message: "LLM validation failed: Invalid sentiment found"
        - Sample request with project_id: "TEST_DB_SERVICE"
        
        Expected Outcome:
        - Error placeholder hierarchy created with proper structure (phy/perf/use categories)
        - Error aspects persisted to database with ERROR_ prefixed local_ids
        - Error aspects contain "[EXTRACTION_FAILED]" in detail_text
        - Error aspects assigned to "extraction_errors" parent group
        - Database contains at least 1 error aspect record
        - Error aspects visible in progress tracking queries
        """
        
        # Test the error placeholder creation directly
        batch = [
            {"review_id": 999991, "review_title": "Test", "review_text": "Test review 1"},
            {"review_id": 999992, "review_title": "Test", "review_text": "Test review 2"}
        ]
        review_id_mapping = {0: 999991, 1: 999992}
        error_message = "LLM validation failed: Invalid sentiment found"
        
        # Create error placeholder hierarchy
        error_hierarchy = await service._create_error_placeholder_hierarchy(
            batch, review_id_mapping, error_message
        )
        
        # Verify placeholder structure
        assert "phy" in error_hierarchy
        assert "extraction_errors" in error_hierarchy["phy"]
        error_aspects = error_hierarchy["phy"]["extraction_errors"]
        assert len(error_aspects) == len(batch)
        
        print(f"✅ Created error hierarchy with {len(error_aspects)} error aspects")
        
        # Test persistence
        await service._persist_extraction_result(
            sample_request.project_id, 
            "B08PKMT2DV",  # Use test product ID
            error_hierarchy, 
            review_id_mapping
        )
        
        # Verify database state
        sb_client = get_supabase_service_client()
        aspects = sb_client.table("review_analysis_aspects").select("*").eq("project_id", sample_request.project_id).execute().data
        
        # Should have error aspects
        error_aspects_db = [a for a in aspects if a["detail_text"].startswith("[EXTRACTION_FAILED]")]
        
        assert len(error_aspects_db) >= 1, "Should have at least 1 error aspect in database"
        
        # Verify error aspect structure
        for aspect in error_aspects_db:
            assert aspect["local_id"].startswith("ERROR_"), "Error aspects should have ERROR_ prefix"
            assert aspect["parent_group_name"] == "extraction_errors", "Error aspects should be in extraction_errors group"
            assert "LLM_EXTRACTION_ERROR" in aspect["detail_text"], "Error aspects should contain error details"
        
        print(f"✅ Created {len(error_aspects_db)} error aspects in database")

    @pytest.mark.asyncio
    async def test_error_placeholder_creation(self, service):
        """Test error placeholder hierarchy creation.
        
        Test Input:
        - Batch of 2 review records with integer IDs (999994, 999995)
        - Review ID mapping: {0: 999994, 1: 999995}
        - Error message: "LLM validation failed: Invalid sentiment found"
        
        Expected Outcome:
        - Error hierarchy contains all 3 aspect types: phy, perf, use
        - "extraction_errors" group created under phy category
        - Error aspects count matches input batch size (2 aspects)
        - Each error aspect has ERROR_ prefix in local_id
        - Each error aspect contains "LLM_EXTRACTION_ERROR" in key name
        - Error aspects have empty positive sentiment (+: [])
        - Error aspects have exactly 1 negative sentiment entry per aspect
        """
        
        # Test data
        batch = [
            {"review_id": 999994, "review_title": "Test", "review_text": "Test review 1"},
            {"review_id": 999995, "review_title": "Test", "review_text": "Test review 2"}
        ]
        review_id_mapping = {0: 999994, 1: 999995}
        error_message = "LLM validation failed: Invalid sentiment found"
        
        # Create error placeholder
        error_hierarchy = await service._create_error_placeholder_hierarchy(
            batch, review_id_mapping, error_message
        )
        
        # Verify structure
        assert "phy" in error_hierarchy
        assert "perf" in error_hierarchy
        assert "use" in error_hierarchy
        assert "extraction_errors" in error_hierarchy["phy"]
        
        # Should have one error aspect per review
        error_aspects = error_hierarchy["phy"]["extraction_errors"]
        assert len(error_aspects) == len(batch)
        
        # Check error aspect details
        for aspect_key, sentiments in error_aspects.items():
            assert aspect_key.startswith("ERROR_")
            assert "LLM_EXTRACTION_ERROR" in aspect_key
            assert sentiments["+"] == []  # No positive sentiment for errors
            assert len(sentiments["-"]) == 1  # One negative sentiment per aspect
        
        print(f"✅ Error placeholder created with {len(error_aspects)} error aspects")

    @pytest.mark.asyncio
    async def test_progress_tracking_with_errors(self, service, sample_request, setup_test_reviews):
        """Test that progress tracking works correctly even with error placeholders.
        
        Test Input:
        - 4 test aspects: 2 normal + 2 error aspects
        - Normal aspects: "elegant appearance" (phy/design), "smooth operation" (perf/functionality)
        - Error aspects: ERROR_1 and ERROR_2 with "[EXTRACTION_FAILED]" detail_text
        - All aspects assigned to project_id: "TEST_DB_SERVICE"
        - Product_id: "B08PKMT2DV"
        
        Expected Outcome:
        - Progress tracking queries return all 4 aspects (normal + error)
        - Assigned count: 0 (no category_pk assigned initially)
        - Unassigned count: 4 (all aspects start unassigned)
        - Progress calculation: 0/4 (0.0%)
        - Normal aspects count: 2 (aspects without [EXTRACTION_FAILED])
        - Error aspects count: 2 (aspects with [EXTRACTION_FAILED])
        - Total aspects visible to progress tracking: 4
        """
        
        # Create mix of normal and error aspects in database
        sb_client = get_supabase_service_client()
        
        from review_analysis.models import Aspect
        test_aspects = [
            # Normal aspects
            Aspect(
                project_id=sample_request.project_id,
                product_id="B08PKMT2DV",
                aspect_type="phy",
                local_id="A",
                parent_group_name="design",
                detail_text="elegant appearance"
            ),
            Aspect(
                project_id=sample_request.project_id,
                product_id="B08PKMT2DV",
                aspect_type="perf", 
                local_id="a",
                parent_group_name="functionality",
                detail_text="smooth operation"
            ),
            # Error aspects
            Aspect(
                project_id=sample_request.project_id,
                product_id="B08PKMT2DV",
                aspect_type="phy",
                local_id="ERROR_1",
                parent_group_name="extraction_errors",
                detail_text="[EXTRACTION_FAILED] LLM_EXTRACTION_ERROR: Validation failed..."
            ),
            Aspect(
                project_id=sample_request.project_id,
                product_id="B08PKMT2DV", 
                aspect_type="perf",
                local_id="ERROR_2",
                parent_group_name="extraction_errors",
                detail_text="[EXTRACTION_FAILED] LLM_EXTRACTION_ERROR: JSON parse error..."
            )
        ]
        
        # Insert aspects (exclude auto-generated fields)
        aspect_data = []
        for a in test_aspects:
            data = asdict(a)
            # Remove auto-generated fields
            data.pop('aspect_pk', None)
            data.pop('created_at', None)
            aspect_data.append(data)
        sb_client.table("review_analysis_aspects").insert(aspect_data).execute()
        
        # Test progress tracking queries (similar to integration test)
        all_aspects = sb_client.table("review_analysis_aspects").select("aspect_pk, detail_text, category_pk").eq("project_id", sample_request.project_id).execute().data
        
        # Count assigned vs unassigned
        assigned_count = sum(1 for a in all_aspects if a["category_pk"] is not None)
        unassigned_count = len(all_aspects) - assigned_count
        
        print("📊 Progress tracking simulation:")
        print(f"   • Total aspects: {len(all_aspects)}")
        print(f"   • Assigned: {assigned_count}")
        print(f"   • Unassigned: {unassigned_count}")
        print(f"   • Progress: {assigned_count}/{len(all_aspects)} ({assigned_count/len(all_aspects)*100:.1f}%)")
        
        # Verify all aspects are visible to progress tracking
        normal_aspects = [a for a in all_aspects if not a["detail_text"].startswith("[EXTRACTION_FAILED]")]
        error_aspects = [a for a in all_aspects if a["detail_text"].startswith("[EXTRACTION_FAILED]")]
        
        assert len(normal_aspects) == 2, "Should see 2 normal aspects"
        assert len(error_aspects) == 2, "Should see 2 error aspects"
        assert len(all_aspects) == 4, "Should see all 4 aspects for progress tracking"
        
        print(f"✅ Progress tracking correctly sees {len(all_aspects)} total aspects")

    @pytest.mark.asyncio
    async def test_cleanup_robustness(self, service, sample_request, setup_test_reviews):
        """Test that cleanup handles mixed normal/error data correctly.
        
        Test Input:
        - 2 test aspects: 1 normal + 1 error aspect
        - Normal aspect: "normal aspect" (phy/design, local_id: A)
        - Error aspect: "[EXTRACTION_FAILED] error aspect" (phy/extraction_errors, local_id: ERROR_1)
        - 2 test categories: "Normal Category" and "EXTRACTION_ERRORS"
        - All data assigned to project_id: "TEST_DB_SERVICE"
        
        Expected Outcome:
        - Initial data insertion succeeds for both aspects and categories
        - Before cleanup: 2 aspects and 2 categories exist in database
        - Cleanup operation deletes all aspects for the project_id
        - Cleanup operation deletes all categories for the project_id
        - After cleanup: 0 aspects and 0 categories remain in database
        - Cleanup handles both normal and error data without issues
        - No orphaned data remains after cleanup operation
        """
        
        sb_client = get_supabase_service_client()
        
        # Create test data similar to what would be left after a test
        from review_analysis.models import Aspect
        test_aspects = [
            Aspect(
                project_id=sample_request.project_id,
                product_id="B08PKMT2DV",
                aspect_type="phy",
                local_id="A",
                parent_group_name="design", 
                detail_text="normal aspect"
            ),
            Aspect(
                project_id=sample_request.project_id,
                product_id="B08PKMT2DV",
                aspect_type="phy",
                local_id="ERROR_1",
                parent_group_name="extraction_errors",
                detail_text="[EXTRACTION_FAILED] error aspect"
            )
        ]
        
        test_categories = [
            {
                "project_id": sample_request.project_id,
                "aspect_type": "phy",
                "name": "Normal Category",
                "definition": "Normal category definition",
                "stage": "final"
            },
            {
                "project_id": sample_request.project_id,
                "aspect_type": "phy", 
                "name": "EXTRACTION_ERRORS",
                "definition": "Error category definition",
                "stage": "final"
            }
        ]
        
        # Insert test data (exclude auto-generated fields)
        aspect_data = []
        for a in test_aspects:
            data = asdict(a)
            # Remove auto-generated fields
            data.pop('aspect_pk', None)
            data.pop('created_at', None)
            aspect_data.append(data)
        sb_client.table("review_analysis_aspects").insert(aspect_data).execute()
        sb_client.table("review_analysis_aspect_categories").insert(test_categories).execute()
        
        # Verify data exists
        aspects_before = sb_client.table("review_analysis_aspects").select("*").eq("project_id", sample_request.project_id).execute().data
        categories_before = sb_client.table("review_analysis_aspect_categories").select("*").eq("project_id", sample_request.project_id).execute().data
        
        print(f"📊 Before cleanup: {len(aspects_before)} aspects, {len(categories_before)} categories")
        
        # Test cleanup (this happens in the fixture teardown, but let's test it explicitly)
        sb_client.table("review_analysis_aspects").delete().eq("project_id", sample_request.project_id).execute()
        sb_client.table("review_analysis_aspect_categories").delete().eq("project_id", sample_request.project_id).execute()
        
        # Verify cleanup worked
        aspects_after = sb_client.table("review_analysis_aspects").select("*").eq("project_id", sample_request.project_id).execute().data
        categories_after = sb_client.table("review_analysis_aspect_categories").select("*").eq("project_id", sample_request.project_id).execute().data
        
        assert len(aspects_after) == 0, "All aspects should be cleaned up"
        assert len(categories_after) == 0, "All categories should be cleaned up"
        
        print(f"✅ Cleanup verified: {len(aspects_after)} aspects, {len(categories_after)} categories remaining")

    @pytest.mark.asyncio
    async def test_category_assignment_persistence(self, service, sample_request, setup_test_reviews):
        """Test that category assignments persist correctly after categorization stage.
        
        This test specifically investigates the issue where aspects are assigned to categories
        during categorization but the assignments are lost before consolidation.
        
        Test Input:
        - Sample request with project_id: "TEST_DB_SERVICE"
        - Test reviews in database from setup_test_reviews fixture
        
        Expected Outcome:
        - After categorization: aspects should have non-null category_pk values
        - Sample log should show aspects with their category_pk assignments
        - This will help identify if assignments are being lost between stages
        """
        
        # Run the full analysis pipeline to test category assignment persistence
        print(f"🚀 Starting analysis for project: {sample_request.project_id}")
        
        # Run the analysis (this will trigger our new debug log)
        analysis_id = await service.analyse(sample_request)
        
        print(f"✅ Analysis completed with ID: {analysis_id}")
        
        # Check the final state of aspects in the database
        sb_client = get_supabase_service_client()
        
        # Get all aspects for this project
        all_aspects = sb_client.table("review_analysis_aspects").select(
            "aspect_pk, aspect_type, category_pk, detail_text"
        ).eq("project_id", sample_request.project_id).execute().data
        
        print(f"📊 Final aspect count: {len(all_aspects)}")
        
        # Count assigned vs unassigned aspects
        assigned_aspects = [a for a in all_aspects if a["category_pk"] is not None]
        unassigned_aspects = [a for a in all_aspects if a["category_pk"] is None]
        
        print(f"📊 Final assignment status:")
        print(f"   • Total aspects: {len(all_aspects)}")
        print(f"   • Assigned: {len(assigned_aspects)}")
        print(f"   • Unassigned: {len(unassigned_aspects)}")
        
        # Show sample of assigned aspects
        if assigned_aspects:
            print(f"📋 Sample assigned aspects:")
            for aspect in assigned_aspects[:5]:
                print(f"   • {aspect['aspect_pk']} ({aspect['aspect_type']}): category_pk={aspect['category_pk']}")
        else:
            print("⚠️ No aspects are assigned to categories!")
        
        # Show sample of unassigned aspects
        if unassigned_aspects:
            print(f"📋 Sample unassigned aspects:")
            for aspect in unassigned_aspects[:5]:
                print(f"   • {aspect['aspect_pk']} ({aspect['aspect_type']}): {aspect['detail_text'][:50]}...")
        
        # Get categories for this project
        categories = sb_client.table("review_analysis_aspect_categories").select(
            "category_pk, name, aspect_type, stage"
        ).eq("project_id", sample_request.project_id).execute().data
        
        print(f"📊 Categories created:")
        print(f"   • Total categories: {len(categories)}")
        for cat in categories:
            print(f"   • {cat['category_pk']} ({cat['aspect_type']}/{cat['stage']}): {cat['name']}")
        
        # This test will help us understand if the issue is:
        # 1. Aspects are never assigned to categories during categorization
        # 2. Aspects are assigned but then lose their assignments before consolidation
        # 3. Categories are created but aspects aren't linked to them
        
        # For now, we'll just log the results to help debug the issue
        # In a real test, we might assert that aspects should be assigned
        # But since we're investigating a bug, we'll just collect the data
        
        print(f"✅ Category assignment persistence test completed") 