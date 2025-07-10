from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime
import logging

from core.models.conversation import (
    ConversationSession,
    ConversationSessionCreate,
    ConversationSessionUpdate,
    ConversationMessage,
    ConversationMessageCreate,
    SessionWithMessages
)

logger = logging.getLogger(__name__)


class ConversationSessionRepository:
    """对话会话数据访问层"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.table_name = "conversation_sessions"
    
    async def get_by_id(self, session_id: str) -> Optional[ConversationSession]:
        """根据ID获取会话"""
        try:
            response = self.client.table(self.table_name).select("*").eq("id", session_id).execute()
            if response.data:
                return ConversationSession(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting session by id {session_id}: {str(e)}")
            return None
    
    async def get_by_user_id(self, user_id: str, limit: int = 50) -> List[ConversationSession]:
        """根据用户ID获取会话列表"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )
            return [ConversationSession(**session) for session in response.data]
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {str(e)}")
            return []
    
    async def create(self, session: ConversationSessionCreate) -> Optional[ConversationSession]:
        """创建新会话"""
        try:
            session_data = session.model_dump()
            logger.info(f"Creating session with data: {session_data}")
            
            # Log if we have a custom ID
            if session_data.get('id'):
                logger.info(f"Using custom session ID: {session_data['id']}")
            else:
                logger.info("No custom ID provided, database will auto-generate")
            
            response = (
                self.client.table(self.table_name)
                .insert(session_data)
                .execute()
            )
            
            logger.info(f"Database response: {response}")
            logger.info(f"Response data: {response.data}")
            
            if response.data:
                created_session = ConversationSession(**response.data[0])
                logger.info(f"Created session with ID: {created_session.id}")
                
                # Check if the returned ID matches the requested ID
                if session_data.get('id') and created_session.id != session_data.get('id'):
                    logger.warning(f"ID mismatch! Requested: {session_data.get('id')}, Got: {created_session.id}")
                
                return created_session
            return None
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            logger.error(f"Session data being inserted: {session.model_dump()}")
            return None
    
    async def update(self, session_id: str, session: ConversationSessionUpdate) -> Optional[ConversationSession]:
        """更新会话"""
        try:
            update_data = {k: v for k, v in session.model_dump().items() if v is not None}
            if not update_data:
                return await self.get_by_id(session_id)
            
            response = (
                self.client.table(self.table_name)
                .update(update_data)
                .eq("id", session_id)
                .execute()
            )
            if response.data:
                return ConversationSession(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            return None
    
    async def delete(self, session_id: str) -> bool:
        """删除会话"""
        try:
            response = (
                self.client.table(self.table_name)
                .delete()
                .eq("id", session_id)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    async def get_recent_sessions(self, user_id: str, limit: int = 10) -> List[ConversationSession]:
        """获取用户最近的会话"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )
            return [ConversationSession(**session) for session in response.data]
        except Exception as e:
            logger.error(f"Error getting recent sessions for user {user_id}: {str(e)}")
            return []


class ConversationMessageRepository:
    """对话消息数据访问层"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.table_name = "conversation_messages"
    
    async def get_by_id(self, message_id: str) -> Optional[ConversationMessage]:
        """根据ID获取消息"""
        try:
            response = self.client.table(self.table_name).select("*").eq("id", message_id).execute()
            if response.data:
                return ConversationMessage(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting message by id {message_id}: {str(e)}")
            return None
    
    async def get_session_messages(self, session_id: str, limit: int = None, offset: int = 0) -> List[ConversationMessage]:
        """获取会话的所有消息"""
        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("sequence_number", desc=False)
            )
            
            if offset > 0:
                query = query.range(offset, offset + limit - 1 if limit else None)
            elif limit:
                query = query.limit(limit)
            
            response = query.execute()
            return [ConversationMessage(**msg) for msg in response.data]
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {str(e)}")
            return []
    
    async def get_recent_messages(self, session_id: str, limit: int = 10) -> List[ConversationMessage]:
        """获取会话的最近消息"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("sequence_number", desc=True)
                .limit(limit)
                .execute()
            )
            # 返回时按正序排列
            messages = [ConversationMessage(**msg) for msg in response.data]
            return list(reversed(messages))
        except Exception as e:
            logger.error(f"Error getting recent messages for session {session_id}: {str(e)}")
            return []
    
    async def create(self, message: ConversationMessageCreate) -> Optional[ConversationMessage]:
        """创建新消息"""
        try:
            # 获取下一个序号
            sequence_number = await self._get_next_sequence_number(message.session_id)
            
            message_data = message.model_dump()
            message_data["sequence_number"] = sequence_number
            
            response = (
                self.client.table(self.table_name)
                .insert(message_data)
                .execute()
            )
            if response.data:
                return ConversationMessage(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            return None
    
    async def delete(self, message_id: str) -> bool:
        """删除消息"""
        try:
            response = (
                self.client.table(self.table_name)
                .delete()
                .eq("id", message_id)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {str(e)}")
            return False
    
    async def delete_session_messages(self, session_id: str) -> bool:
        """删除会话的所有消息"""
        try:
            response = (
                self.client.table(self.table_name)
                .delete()
                .eq("session_id", session_id)
                .execute()
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting messages for session {session_id}: {str(e)}")
            return False
    
    async def get_message_count(self, session_id: str) -> int:
        """获取会话消息数量"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("id", count="exact")
                .eq("session_id", session_id)
                .execute()
            )
            return response.count or 0
        except Exception as e:
            logger.error(f"Error getting message count for session {session_id}: {str(e)}")
            return 0
    
    async def _get_next_sequence_number(self, session_id: str) -> int:
        """获取下一个序号"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("sequence_number")
                .eq("session_id", session_id)
                .order("sequence_number", desc=True)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]["sequence_number"] + 1
            return 1
        except Exception as e:
            logger.error(f"Error getting next sequence number for session {session_id}: {str(e)}")
            return 1


class ConversationRepository:
    """对话复合数据访问层"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.session_repo = ConversationSessionRepository(supabase_client)
        self.message_repo = ConversationMessageRepository(supabase_client)
    
    async def get_session_with_messages(self, session_id: str, message_limit: int = 10) -> Optional[SessionWithMessages]:
        """获取包含消息的会话"""
        try:
            session = await self.session_repo.get_by_id(session_id)
            if not session:
                return None
            
            messages = await self.message_repo.get_recent_messages(session_id, message_limit)
            
            return SessionWithMessages(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                messages=messages
            )
        except Exception as e:
            logger.error(f"Error getting session with messages {session_id}: {str(e)}")
            return None
    
    async def delete_session_completely(self, session_id: str) -> bool:
        """完全删除会话（包括消息）"""
        try:
            # 先删除消息
            await self.message_repo.delete_session_messages(session_id)
            # 再删除会话
            return await self.session_repo.delete(session_id)
        except Exception as e:
            logger.error(f"Error deleting session completely {session_id}: {str(e)}")
            return False