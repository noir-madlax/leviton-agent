"""
LLM Interaction Storage Service
Handles file-based storage of LLM interactions with future S3 migration support
"""
import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from abc import ABC, abstractmethod
import hashlib

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def write_interaction(self, file_path: str, data: Dict[str, Any]) -> bool:
        """Write LLM interaction data to storage"""
        pass
    
    @abstractmethod
    async def read_interaction(self, file_path: str) -> Dict[str, Any]:
        """Read LLM interaction data from storage"""
        pass
    
    @abstractmethod
    async def write_prompt(self, file_path: str, prompt: str) -> bool:
        """Write prompt text to storage"""
        pass
    
    @abstractmethod
    async def read_prompt(self, file_path: str) -> str:
        """Read prompt text from storage"""
        pass
    
    @abstractmethod
    async def list_files(self, directory: str) -> List[str]:
        """List files in a directory"""
        pass

    @abstractmethod
    async def compute_checksum(self, file_path: str) -> str:
        """Return SHA256 checksum (hex) for the given file path"""
        pass

    @abstractmethod
    async def verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """Verify that file's SHA256 matches expected_checksum"""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
    
    async def write_interaction(self, file_path: str, data: Dict[str, Any]) -> bool:
        """Write LLM interaction data as JSON"""
        try:
            full_path = self.storage_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Wrote interaction to {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write interaction to {file_path}: {e}")
            return False
    
    async def read_interaction(self, file_path: str) -> Dict[str, Any]:
        """Read LLM interaction data from JSON"""
        try:
            full_path = self.storage_root / file_path
            
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Read interaction from {full_path}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to read interaction from {file_path}: {e}")
            raise
    
    async def write_prompt(self, file_path: str, prompt: str) -> bool:
        """Write prompt text to file"""
        try:
            full_path = self.storage_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            logger.info(f"Wrote prompt to {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write prompt to {file_path}: {e}")
            return False
    
    async def read_prompt(self, file_path: str) -> str:
        """Read prompt text from file"""
        try:
            full_path = self.storage_root / file_path
            
            with open(full_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            
            logger.debug(f"Read prompt from {full_path}")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to read prompt from {file_path}: {e}")
            raise
    
    async def list_files(self, directory: str) -> List[str]:
        """List files in a directory"""
        try:
            dir_path = self.storage_root / directory
            if not dir_path.exists():
                return []
            
            files = []
            for item in dir_path.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(self.storage_root)
                    files.append(str(rel_path))
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []

    async def compute_checksum(self, file_path: str) -> str:
        """Compute SHA256 checksum for a file on local filesystem"""
        full_path = self.storage_root / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"Cannot compute checksum; file not found: {full_path}")

        sha256 = hashlib.sha256()
        try:
            with open(full_path, "rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    sha256.update(chunk)
            checksum = sha256.hexdigest()
            logger.debug(f"Computed checksum for {full_path}: {checksum}")
            return checksum
        except Exception as exc:
            logger.error(f"Failed to compute checksum for {file_path}: {exc}")
            raise

    async def verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """Verify file's checksum against expected value"""
        actual = await self.compute_checksum(file_path)
        is_valid = actual == expected_checksum
        if not is_valid:
            logger.warning(
                "Checksum mismatch for %s. Expected %s but got %s", file_path, expected_checksum, actual
            )
        return is_valid


class S3StorageBackend(StorageBackend):
    """S3 storage backend (placeholder for future implementation)"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        # TODO: Initialize boto3 client
        raise NotImplementedError("S3 backend not yet implemented")
    
    async def write_interaction(self, file_path: str, data: Dict[str, Any]) -> bool:
        # TODO: Implement S3 upload
        raise NotImplementedError("S3 backend not yet implemented")
    
    async def read_interaction(self, file_path: str) -> Dict[str, Any]:
        # TODO: Implement S3 download
        raise NotImplementedError("S3 backend not yet implemented")
    
    async def write_prompt(self, file_path: str, prompt: str) -> bool:
        # TODO: Implement S3 upload
        raise NotImplementedError("S3 backend not yet implemented")
    
    async def read_prompt(self, file_path: str) -> str:
        # TODO: Implement S3 download
        raise NotImplementedError("S3 backend not yet implemented")
    
    async def list_files(self, directory: str) -> List[str]:
        # TODO: Implement S3 list
        raise NotImplementedError("S3 backend not yet implemented")

    async def compute_checksum(self, file_path: str) -> str:
        # TODO: Implement checksum calculation for S3 objects
        raise NotImplementedError("S3 backend not yet implemented")

    async def verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        # TODO: Implement checksum verification for S3 objects
        raise NotImplementedError("S3 backend not yet implemented")


class LLMStorageService:
    """High-level LLM interaction storage service"""
    
    def __init__(self, storage_backend: StorageBackend):
        self.backend = storage_backend
    
    @classmethod
    def create_local(cls, storage_root: str) -> 'LLMStorageService':
        """Create service with local storage backend"""
        backend = LocalStorageBackend(storage_root)
        return cls(backend)
    
    @classmethod
    def create_s3(cls, bucket_name: str, region: str = "us-east-1") -> 'LLMStorageService':
        """Create service with S3 storage backend"""
        backend = S3StorageBackend(bucket_name, region)
        return cls(backend)
    
    def generate_interaction_path(self, run_id: str, interaction_type: str, 
                                batch_id: Optional[int] = None, attempt: int = 1) -> str:
        """Generate standardized path for interaction file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        filename = f"{interaction_type}"
        if batch_id is not None:
            filename += f"_batch_{batch_id}"
        filename += f"_attempt_{attempt}_{timestamp}_{unique_id}.json"
        
        return f"{run_id}/interactions/{filename}"
    
    def generate_prompt_path(self, run_id: str, prompt_type: str) -> str:
        """Generate standardized path for prompt file"""
        return f"{run_id}/prompts/{prompt_type}_prompt.txt"
    
    async def store_interaction(self, run_id: str, interaction_type: str,
                              request_data: Dict[str, Any], response_data: Dict[str, Any],
                              batch_id: Optional[int] = None, attempt: int = 1,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store complete LLM interaction
        
        Returns:
            File path where the interaction was stored
        """
        file_path = self.generate_interaction_path(run_id, interaction_type, batch_id, attempt)
        
        interaction_data = {
            "run_id": run_id,
            "interaction_type": interaction_type,
            "batch_id": batch_id,
            "attempt": attempt,
            "timestamp": datetime.now().isoformat(),
            "request": request_data,
            "response": response_data,
            "metadata": metadata or {}
        }
        
        success = await self.backend.write_interaction(file_path, interaction_data)
        if not success:
            raise RuntimeError(f"Failed to store interaction at {file_path}")
        
        return file_path
    
    async def store_prompt(self, run_id: str, prompt_type: str, prompt_content: str) -> str:
        """
        Store prompt template for the run
        
        Returns:
            File path where the prompt was stored
        """
        file_path = self.generate_prompt_path(run_id, prompt_type)
        
        success = await self.backend.write_prompt(file_path, prompt_content)
        if not success:
            raise RuntimeError(f"Failed to store prompt at {file_path}")
        
        return file_path
    
    async def load_interaction(self, file_path: str) -> Dict[str, Any]:
        """Load LLM interaction from storage"""
        return await self.backend.read_interaction(file_path)
    
    async def load_prompt(self, file_path: str) -> str:
        """Load prompt from storage"""
        return await self.backend.read_prompt(file_path)
    
    async def list_run_interactions(self, run_id: str) -> List[str]:
        """List all interaction files for a run"""
        return await self.backend.list_files(f"{run_id}/interactions")
    
    async def list_run_prompts(self, run_id: str) -> List[str]:
        """List all prompt files for a run"""
        return await self.backend.list_files(f"{run_id}/prompts")

    # ---------------------------------------------------------------------
    # Integrity helpers
    # ---------------------------------------------------------------------

    async def compute_checksum(self, file_path: str) -> str:
        """Compute SHA256 checksum (hex) for a stored file"""
        return await self.backend.compute_checksum(file_path)

    async def verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """Verify that stored file matches provided checksum"""
        return await self.backend.verify_checksum(file_path, expected_checksum) 