from datetime import datetime
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field
from uuid import UUID


class ConversationSession(BaseModel):
    """对话会话模型"""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationSessionCreate(BaseModel):
    """创建对话会话请求模型"""
    user_id: str
    title: str = Field(default="New Conversation", description="会话标题")
    id: Optional[str] = Field(None, description="可选的会话ID，如果不提供则自动生成")
    
    def model_dump(self, **kwargs):
        """Override model_dump method to ensure id field is included when set"""
        data = super().model_dump(**kwargs)
        # Only include id if it's not None
        if self.id is not None:
            data['id'] = self.id
        elif 'id' in data and data['id'] is None:
            # Remove None id to let database auto-generate
            del data['id']
        return data


class ConversationSessionUpdate(BaseModel):
    """更新对话会话请求模型"""
    title: Optional[str] = Field(None, description="会话标题")


class ConversationSessionResponse(BaseModel):
    """对话会话响应模型"""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = Field(None, description="消息数量")
    
    class Config:
        from_attributes = True


class ConversationMessage(BaseModel):
    """对话消息模型"""
    id: str
    session_id: str
    message_type: Literal["user", "agent"]
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sequence_number: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationMessageCreate(BaseModel):
    """创建对话消息请求模型"""
    session_id: str
    message_type: Literal["user", "agent"]
    content: str = Field(..., description="消息内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ConversationMessageResponse(BaseModel):
    """对话消息响应模型"""
    id: str
    session_id: str
    message_type: Literal["user", "agent"]
    content: str
    metadata: Dict[str, Any]
    sequence_number: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionWithMessages(BaseModel):
    """包含消息的会话模型"""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ConversationMessage] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class ContextRequest(BaseModel):
    """获取上下文请求模型"""
    session_id: str
    window_size: Optional[int] = Field(10, description="上下文窗口大小")


class ContextResponse(BaseModel):
    """上下文响应模型"""
    session_id: str
    context: str
    message_count: int
    window_size: int