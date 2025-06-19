"""
Tests for LLM storage system
"""
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from backend.product_segmentation.storage.llm_storage import (
    LLMStorageService,
    LocalStorageBackend,
)


class TestLLMStorage:
    """Test cases for LLM storage functionality"""
    
    def setup_method(self):
        """Setup temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_service = LLMStorageService.create_local(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup temporary directory after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_path_generation(self):
        """Test path generation for interactions and prompts"""
        # Test interaction path generation
        interaction_path = self.storage_service.generate_interaction_path(
            "RUN_TEST_123", "segmentation", batch_id=1, attempt=1
        )
        
        assert interaction_path.startswith("RUN_TEST_123/interactions/")
        assert "segmentation_batch_1_attempt_1" in interaction_path
        assert interaction_path.endswith(".json")
        
        # Test prompt path generation
        prompt_path = self.storage_service.generate_prompt_path(
            "RUN_TEST_123", "taxonomy_extraction"
        )
        
        assert prompt_path == "RUN_TEST_123/prompts/taxonomy_extraction_prompt.txt"
    
    def test_store_and_load_interaction(self):
        """Test storing and loading LLM interactions"""
        async def run_test():
            # Test data
            run_id = "RUN_TEST_123"
            interaction_type = "segmentation"
            request_data = {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Test prompt"}],
                "temperature": 0.2
            }
            response_data = {
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {"total_tokens": 50}
            }
            metadata = {"batch_size": 10, "product_count": 5}
            
            # Store interaction
            file_path = await self.storage_service.store_interaction(
                run_id, interaction_type, request_data, response_data,
                batch_id=1, attempt=1, metadata=metadata
            )
            
            assert file_path.startswith("RUN_TEST_123/interactions/")
            
            # Verify file exists
            full_path = Path(self.temp_dir) / file_path
            assert full_path.exists()
            
            # Load interaction back
            loaded_data = await self.storage_service.load_interaction(file_path)
            
            # Verify data integrity
            assert loaded_data["run_id"] == run_id
            assert loaded_data["interaction_type"] == interaction_type
            assert loaded_data["batch_id"] == 1
            assert loaded_data["attempt"] == 1
            assert loaded_data["request"] == request_data
            assert loaded_data["response"] == response_data
            assert loaded_data["metadata"] == metadata
            assert "timestamp" in loaded_data
        
        # Run async test
        asyncio.run(run_test())
    
    def test_store_and_load_prompt(self):
        """Test storing and loading prompt templates"""
        async def run_test():
            # Test data
            run_id = "RUN_TEST_123"
            prompt_type = "taxonomy_extraction"
            prompt_content = """
            Please analyze the following products and create a taxonomy:
            
            Products: {products}
            
            Instructions:
            1. Group similar products
            2. Create category names
            3. Provide definitions
            """
            
            # Store prompt
            file_path = await self.storage_service.store_prompt(
                run_id, prompt_type, prompt_content
            )
            
            assert file_path == "RUN_TEST_123/prompts/taxonomy_extraction_prompt.txt"
            
            # Verify file exists
            full_path = Path(self.temp_dir) / file_path
            assert full_path.exists()
            
            # Load prompt back
            loaded_prompt = await self.storage_service.load_prompt(file_path)
            
            # Verify content matches
            assert loaded_prompt.strip() == prompt_content.strip()
        
        # Run async test
        asyncio.run(run_test())
    
    def test_list_run_files(self):
        """Test listing files for a run"""
        async def run_test():
            run_id = "RUN_TEST_123"
            
            # Store multiple interactions
            for i in range(3):
                await self.storage_service.store_interaction(
                    run_id, "segmentation", 
                    {"test": f"request_{i}"}, {"test": f"response_{i}"},
                    batch_id=i
                )
            
            # Store multiple prompts
            for prompt_type in ["taxonomy_extraction", "consolidate_taxonomy"]:
                await self.storage_service.store_prompt(
                    run_id, prompt_type, f"Test prompt for {prompt_type}"
                )
            
            # List interactions
            interactions = await self.storage_service.list_run_interactions(run_id)
            assert len(interactions) == 3
            for interaction in interactions:
                assert interaction.startswith(f"{run_id}/interactions/")
                assert interaction.endswith(".json")
            
            # List prompts
            prompts = await self.storage_service.list_run_prompts(run_id)
            assert len(prompts) == 2
            for prompt in prompts:
                assert prompt.startswith(f"{run_id}/prompts/")
                assert prompt.endswith("_prompt.txt")
        
        # Run async test
        asyncio.run(run_test())
    
    def test_local_backend_directly(self):
        """Test local storage backend directly"""
        async def run_test():
            backend = LocalStorageBackend(self.temp_dir)
            
            # Test writing and reading JSON data
            test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
            file_path = "test/data.json"
            
            success = await backend.write_interaction(file_path, test_data)
            assert success
            
            loaded_data = await backend.read_interaction(file_path)
            assert loaded_data == test_data
            
            # Test writing and reading text data
            text_content = "This is a test prompt\nWith multiple lines"
            text_path = "test/prompt.txt"
            
            success = await backend.write_prompt(text_path, text_content)
            assert success
            
            loaded_text = await backend.read_prompt(text_path)
            assert loaded_text == text_content
            
            # Test listing files
            files = await backend.list_files("test")
            assert len(files) == 2
            assert "test/data.json" in files
            assert "test/prompt.txt" in files
        
        # Run async test
        asyncio.run(run_test())
    
    def test_error_handling(self):
        """Test error handling for storage operations"""
        async def run_test():
            # Test reading non-existent file
            try:
                await self.storage_service.load_interaction("nonexistent/file.json")
                assert False, "Should have raised an exception"
            except Exception:
                pass  # Expected
            
            try:
                await self.storage_service.load_prompt("nonexistent/prompt.txt")
                assert False, "Should have raised an exception"
            except Exception:
                pass  # Expected
        
        # Run async test
        asyncio.run(run_test())

    def test_file_integrity(self):
        """Test checksum computation and verification"""
        async def run_test():
            run_id = "RUN_TEST_123"
            # Store an interaction
            file_path = await self.storage_service.store_interaction(
                run_id,
                "segmentation",
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
                batch_id=0,
            )

            # Compute checksum
            checksum = await self.storage_service.compute_checksum(file_path)
            assert len(checksum) == 64  # sha256 hex length

            # Verify returns True
            assert await self.storage_service.verify_checksum(file_path, checksum)

            # Tamper with file
            full_path = Path(self.temp_dir) / file_path
            with open(full_path, "a", encoding="utf-8") as fh:
                fh.write("tamper")

            # Verification should now fail
            assert not await self.storage_service.verify_checksum(file_path, checksum)

        asyncio.run(run_test())


def run_storage_tests():
    """Run all storage tests without pytest"""
    print("🧪 Running Phase 2: Storage Tests")
    print("=" * 50)
    
    tests = [
        ("path generation", "test_path_generation"),
        ("store and load interaction", "test_store_and_load_interaction"),
        ("store and load prompt", "test_store_and_load_prompt"),
        ("list run files", "test_list_run_files"),
        ("local backend directly", "test_local_backend_directly"),
        ("error handling", "test_error_handling"),
        ("file integrity", "test_file_integrity"),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, method_name in tests:
        try:
            print(f"✓ Testing {test_name}...")
            
            # Create test instance
            test_instance = TestLLMStorage()
            test_instance.setup_method()
            
            try:
                # Run test method
                method = getattr(test_instance, method_name)
                method()
                print(f"  ✅ PASS: {test_name}")
                passed += 1
            finally:
                test_instance.teardown_method()
                
        except Exception as e:
            print(f"  ❌ FAIL: {test_name} - {e}")
    
    print(f"\n🎉 Storage tests completed: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    run_storage_tests() 