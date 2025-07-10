from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from core.database.connection import get_supabase_service_client
from core.repositories.conversation_repository import (
    ConversationRepository,
    ConversationSessionRepository,
    ConversationMessageRepository
)
from core.models.conversation import (
    ConversationSession,
    ConversationSessionCreate,
    ConversationSessionUpdate,
    ConversationSessionResponse,
    ConversationMessage,
    ConversationMessageCreate,
    ConversationMessageResponse,
    SessionWithMessages,
    ContextResponse
)

logger = logging.getLogger(__name__)


class ConversationService:
    """对话服务层"""
    
    def __init__(self):
        self.supabase_client = get_supabase_service_client()
        self.conversation_repo = ConversationRepository(self.supabase_client)
        self.session_repo = ConversationSessionRepository(self.supabase_client)
        self.message_repo = ConversationMessageRepository(self.supabase_client)
        self.context_window_size = 10
        self.max_context_length = 4000  # 最大上下文长度限制
    
    async def create_session(self, user_id: str, title: str = "New Conversation") -> Optional[ConversationSessionResponse]:
        """创建新会话"""
        try:
            session_create = ConversationSessionCreate(user_id=user_id, title=title)
            session = await self.session_repo.create(session_create)
            
            if session:
                return ConversationSessionResponse(
                    id=session.id,
                    user_id=session.user_id,
                    title=session.title,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    message_count=0
                )
            return None
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {str(e)}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[ConversationSessionResponse]:
        """获取会话"""
        try:
            session = await self.session_repo.get_by_id(session_id)
            if not session:
                return None
            
            message_count = await self.message_repo.get_message_count(session_id)
            
            return ConversationSessionResponse(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count
            )
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[ConversationSessionResponse]:
        """获取用户的所有会话"""
        try:
            sessions = await self.session_repo.get_by_user_id(user_id, limit)
            responses = []
            
            for session in sessions:
                message_count = await self.message_repo.get_message_count(session.id)
                responses.append(ConversationSessionResponse(
                    id=session.id,
                    user_id=session.user_id,
                    title=session.title,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    message_count=message_count
                ))
            
            return responses
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {str(e)}")
            return []
    
    async def update_session(self, session_id: str, title: str) -> Optional[ConversationSessionResponse]:
        """更新会话标题"""
        try:
            session_update = ConversationSessionUpdate(title=title)
            session = await self.session_repo.update(session_id, session_update)
            
            if session:
                message_count = await self.message_repo.get_message_count(session_id)
                return ConversationSessionResponse(
                    id=session.id,
                    user_id=session.user_id,
                    title=session.title,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    message_count=message_count
                )
            return None
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            return await self.conversation_repo.delete_session_completely(session_id)
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    async def create_or_get_session(self, user_id: str, session_id: Optional[str] = None) -> Optional[ConversationSession]:
        """获取或创建会话"""
        try:
            logger.info(f"🔄 [CREATE_OR_GET_SESSION] user_id={user_id}, session_id={session_id}")
            
            if session_id:
                # 尝试获取现有会话
                logger.info(f"🔍 Checking if session {session_id} exists")
                session = await self.session_repo.get_by_id(session_id)
                if session and session.user_id == user_id:
                    logger.info(f"✅ Found existing session: {session.id}")
                    return session
                
                if session:
                    logger.warning(f"⚠️ Session {session_id} exists but belongs to different user: {session.user_id} != {user_id}")
                else:
                    logger.info(f"❌ Session {session_id} not found")
                
                # 如果提供了 session_id 但会话不存在，使用提供的 session_id 创建新会话
                logger.info(f"🆕 Creating new session with provided session_id: {session_id}")
                session_create = ConversationSessionCreate(user_id=user_id, id=session_id)
                logger.info(f"📋 Session create object: {session_create.model_dump()}")
                
                created_session = await self.session_repo.create(session_create)
                if created_session:
                    logger.info(f"✅ Successfully created session with ID: {created_session.id}")
                    if created_session.id != session_id:
                        logger.error(f"🚨 CRITICAL: Session ID mismatch! Expected: {session_id}, Got: {created_session.id}")
                else:
                    logger.error(f"❌ Failed to create session")
                return created_session
            
            # 如果没有提供 session_id，创建新会话（让数据库自动生成 ID）
            logger.info(f"🆕 Creating new session with auto-generated ID for user: {user_id}")
            session_create = ConversationSessionCreate(user_id=user_id)
            logger.info(f"📋 Session create object: {session_create.model_dump()}")
            return await self.session_repo.create(session_create)
        except Exception as e:
            logger.error(f"Error creating or getting session for user {user_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_or_create_default_session(self, user_id: str) -> Optional[ConversationSession]:
        """获取或创建默认会话"""
        try:
            # 尝试获取用户最近的会话
            recent_sessions = await self.session_repo.get_recent_sessions(user_id, 1)
            
            if recent_sessions:
                # 检查最近会话是否在24小时内
                recent_session = recent_sessions[0]
                if datetime.now() - recent_session.updated_at < timedelta(hours=24):
                    return recent_session
            
            # 创建新会话
            session_create = ConversationSessionCreate(user_id=user_id)
            return await self.session_repo.create(session_create)
        except Exception as e:
            logger.error(f"Error getting or creating default session for user {user_id}: {str(e)}")
            return None
    
    async def add_user_message(self, session_id: str, content: str, metadata: Dict[str, Any] = None) -> Optional[ConversationMessageResponse]:
        """添加用户消息"""
        try:
            message_create = ConversationMessageCreate(
                session_id=session_id,
                message_type="user",
                content=content,
                metadata=metadata or {}
            )
            
            message = await self.message_repo.create(message_create)
            if message:
                return ConversationMessageResponse(
                    id=message.id,
                    session_id=message.session_id,
                    message_type=message.message_type,
                    content=message.content,
                    metadata=message.metadata,
                    sequence_number=message.sequence_number,
                    created_at=message.created_at
                )
            return None
        except Exception as e:
            logger.error(f"Error adding user message to session {session_id}: {str(e)}")
            return None
    
    async def add_agent_message(self, session_id: str, content: str, metadata: Dict[str, Any] = None) -> Optional[ConversationMessageResponse]:
        """添加Agent消息"""
        try:
            message_create = ConversationMessageCreate(
                session_id=session_id,
                message_type="agent",
                content=content,
                metadata=metadata or {}
            )
            
            message = await self.message_repo.create(message_create)
            if message:
                return ConversationMessageResponse(
                    id=message.id,
                    session_id=message.session_id,
                    message_type=message.message_type,
                    content=message.content,
                    metadata=message.metadata,
                    sequence_number=message.sequence_number,
                    created_at=message.created_at
                )
            return None
        except Exception as e:
            logger.error(f"Error adding agent message to session {session_id}: {str(e)}")
            return None
    
    async def get_context_for_agent(self, session_id: str, window_size: int = None) -> ContextResponse:
        """获取Agent上下文 - 核心功能"""
        try:
            window_size = window_size or self.context_window_size
            messages = await self.message_repo.get_recent_messages(session_id, window_size)
            
            # 格式化上下文
            context = await self.format_context_messages(messages)
            
            # 如果上下文过长，动态调整窗口大小
            if len(context) > self.max_context_length and len(messages) > 2:
                # 减少窗口大小，保留最近的消息
                reduced_window = max(2, window_size // 2)
                messages = await self.message_repo.get_recent_messages(session_id, reduced_window)
                context = await self.format_context_messages(messages)
            
            return ContextResponse(
                session_id=session_id,
                context=context,
                message_count=len(messages),
                window_size=window_size
            )
        except Exception as e:
            logger.error(f"Error getting context for session {session_id}: {str(e)}")
            return ContextResponse(
                session_id=session_id,
                context="",
                message_count=0,
                window_size=window_size or self.context_window_size
            )
    
    async def format_context_messages(self, messages: List[ConversationMessage]) -> str:
        """格式化消息为上下文文本"""
        if not messages:
            return ""
        
        context_parts = ["=== 对话历史 ==="]
        
        for msg in messages:
            if msg.message_type == "user":
                context_parts.append(f"用户: {msg.content}")
            else:
                context_parts.append(f"助手: {msg.content}")
                
                # 添加工具使用信息
                if msg.metadata.get("tools_used"):
                    tools = msg.metadata["tools_used"]
                    if isinstance(tools, list):
                        tools_str = ", ".join(tools)
                    else:
                        tools_str = str(tools)
                    context_parts.append(f"[使用工具: {tools_str}]")
                
                # 添加数据查询信息
                if msg.metadata.get("data_tables"):
                    tables = msg.metadata["data_tables"]
                    if isinstance(tables, list):
                        tables_str = ", ".join(tables)
                    else:
                        tables_str = str(tables)
                    context_parts.append(f"[查询数据表: {tables_str}]")
        
        context_parts.append("=== 当前问题 ===")
        return "\n".join(context_parts)
    
    async def get_session_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> List[ConversationMessageResponse]:
        """获取会话消息"""
        try:
            messages = await self.message_repo.get_session_messages(session_id, limit, offset)
            return [
                ConversationMessageResponse(
                    id=msg.id,
                    session_id=msg.session_id,
                    message_type=msg.message_type,
                    content=msg.content,
                    metadata=msg.metadata,
                    sequence_number=msg.sequence_number,
                    created_at=msg.created_at
                ) for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {str(e)}")
            return []
    
    async def get_session_with_messages(self, session_id: str, message_limit: int = 10) -> Optional[SessionWithMessages]:
        """获取包含消息的会话"""
        try:
            return await self.conversation_repo.get_session_with_messages(session_id, message_limit)
        except Exception as e:
            logger.error(f"Error getting session with messages {session_id}: {str(e)}")
            return None
    
    async def should_create_new_session(self, session_id: str, max_messages: int = 100) -> bool:
        """判断是否应该创建新会话"""
        try:
            message_count = await self.message_repo.get_message_count(session_id)
            return message_count >= max_messages
        except Exception as e:
            logger.error(f"Error checking if should create new session for {session_id}: {str(e)}")
            return False
    
    async def cleanup_old_sessions(self, user_id: str, keep_recent: int = 10) -> int:
        """清理旧会话"""
        try:
            sessions = await self.session_repo.get_by_user_id(user_id, limit=1000)
            
            if len(sessions) <= keep_recent:
                return 0
            
            # 保留最近的会话，删除其他的
            sessions_to_delete = sessions[keep_recent:]
            deleted_count = 0
            
            for session in sessions_to_delete:
                if await self.conversation_repo.delete_session_completely(session.id):
                    deleted_count += 1
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old sessions for user {user_id}: {str(e)}")
            return 0
    
    async def generate_session_title(self, session_id: str) -> str:
        """根据会话内容生成标题"""
        try:
            messages = await self.message_repo.get_recent_messages(session_id, 2)
            
            if not messages:
                return "New Conversation"
            
            # 查找第一个用户消息
            first_user_message = None
            for msg in messages:
                if msg.message_type == "user":
                    first_user_message = msg
                    break
            
            if first_user_message:
                # 截取前50个字符作为标题
                title = first_user_message.content[:50]
                if len(first_user_message.content) > 50:
                    title += "..."
                return title
            
            return "New Conversation"
        except Exception as e:
            logger.error(f"Error generating title for session {session_id}: {str(e)}")
            return "New Conversation"