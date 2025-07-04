"""Server-Sent Events manager for real-time project progress updates."""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class SSEConnectionManager:
    """Manages SSE connections for project progress updates."""
    
    def __init__(self):
        # project_id -> set of connection queues
        self._connections: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
    
    async def add_connection(self, project_id: str) -> asyncio.Queue:
        """Add a new SSE connection for a project."""
        async with self._lock:
            if project_id not in self._connections:
                self._connections[project_id] = set()
            
            connection_queue = asyncio.Queue()
            self._connections[project_id].add(connection_queue)
            logger.info(f"Added SSE connection for project {project_id}. Total connections: {len(self._connections[project_id])}")
            return connection_queue
    
    async def remove_connection(self, project_id: str, connection_queue: asyncio.Queue):
        """Remove an SSE connection."""
        async with self._lock:
            if project_id in self._connections:
                self._connections[project_id].discard(connection_queue)
                if not self._connections[project_id]:
                    del self._connections[project_id]
                logger.info(f"Removed SSE connection for project {project_id}")
    
    async def broadcast_to_project(self, project_id: str, data: dict):
        """Broadcast progress data to all connections for a project."""
        async with self._lock:
            if project_id not in self._connections:
                logger.debug(f"No SSE connections for project {project_id}")
                return
            
            connections = self._connections[project_id].copy()
        
        if not connections:
            return
            
        logger.info(f"Broadcasting progress update to {len(connections)} connections for project {project_id}")
        
        # Send to all connections
        dead_connections = set()
        for connection_queue in connections:
            try:
                await connection_queue.put(data)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                dead_connections.add(connection_queue)
        
        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                if project_id in self._connections:
                    self._connections[project_id] -= dead_connections
    
    async def stream_for_project(
        self, project_id: str, request: Request, initial_progress_data: dict
    ):
        """
        Yields messages for a specific project's SSE stream.
        An initial message with the current progress is sent immediately.
        """
        response_queue = await self.add_connection(project_id)
        
        # Immediately send the initial state to the newly connected client.
        logger.info(f"📬 Sending initial state to new connection for project {project_id}")
        yield f"data: {json.dumps(initial_progress_data)}\n\n"
        
        try:
            while True:
                # Check for disconnection before waiting for a message
                if await request.is_disconnected():
                    logger.info(f"Client for project {project_id} disconnected.")
                    break
                
                try:
                    # Wait for a message from the broadcast queue
                    message = await asyncio.wait_for(response_queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send a heartbeat comment to keep the connection alive
                    yield ": heartbeat\n\n"

        finally:
            await self.remove_connection(project_id, response_queue)
    
    def _is_project_completed(self, data: dict) -> bool:
        """Check if project is completed based on progress data."""
        segmentation_status = data.get('segmentation_status')
        review_analysis_status = data.get('review_analysis_status')
        
        return (segmentation_status == 'completed' and 
                review_analysis_status == 'completed')


# Global SSE manager instance
sse_manager = SSEConnectionManager() 