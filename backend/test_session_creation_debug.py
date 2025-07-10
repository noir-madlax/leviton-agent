#!/usr/bin/env python3
"""
Test script to debug session creation issues
"""
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pydantic_model():
    """Test the Pydantic model behavior"""
    from core.models.conversation import ConversationSessionCreate
    
    logger.info("=== Testing Pydantic Model Behavior ===")
    
    # Test with custom ID
    session_with_id = ConversationSessionCreate(user_id="test_user", id="custom_session_123")
    data_with_id = session_with_id.model_dump()
    logger.info(f"With custom ID - model_dump(): {data_with_id}")
    
    # Test without custom ID
    session_without_id = ConversationSessionCreate(user_id="test_user")
    data_without_id = session_without_id.model_dump()
    logger.info(f"Without custom ID - model_dump(): {data_without_id}")
    
    # Test with None ID explicitly
    session_none_id = ConversationSessionCreate(user_id="test_user", id=None)
    data_none_id = session_none_id.model_dump()
    logger.info(f"With None ID - model_dump(): {data_none_id}")

async def test_session_creation():
    """Test actual session creation"""
    try:
        from core.database.connection import get_supabase_service_client
        from core.services.conversation_service import ConversationService
        
        logger.info("=== Testing Session Creation ===")
        
        conversation_service = ConversationService()
        
        # Test 1: Create session with custom ID
        custom_session_id = "debug_test_session_" + str(int(time.time()))
        logger.info(f"Creating session with custom ID: {custom_session_id}")
        
        session = await conversation_service.create_or_get_session(
            user_id="debug_test_user",
            session_id=custom_session_id
        )
        
        if session:
            logger.info(f"Created session: {session.id}")
            if session.id == custom_session_id:
                logger.info("✅ SUCCESS: Custom ID preserved!")
            else:
                logger.error(f"❌ FAILURE: Custom ID not preserved. Expected: {custom_session_id}, Got: {session.id}")
            
            # Clean up
            await conversation_service.delete_session(session.id)
        else:
            logger.error("❌ FAILURE: Session creation returned None")
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    import time
    import asyncio
    
    # Run the tests
    test_pydantic_model()
    
    # Only run database test if dependencies are available
    try:
        asyncio.run(test_session_creation())
    except ImportError as e:
        logger.warning(f"Skipping database test due to missing dependencies: {e}")
    except Exception as e:
        logger.error(f"Database test failed: {e}")