from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ProductPrompt(BaseModel):
    """ProductPrompt 数据模型（对应数据库表结构）"""
    id: int
    created_at: datetime
    prompt: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProductPromptCreate(BaseModel):
    """创建 ProductPrompt 的请求模型"""
    prompt: Optional[str] = Field(None, description="提示词内容")
    description: Optional[str] = Field(None, description="描述信息")

class ProductPromptUpdate(BaseModel):
    """更新 ProductPrompt 的请求模型"""
    prompt: Optional[str] = Field(None, description="提示词内容")
    description: Optional[str] = Field(None, description="描述信息")

class ProductPromptResponse(BaseModel):
    """ProductPrompt 响应模型"""
    id: int
    created_at: datetime
    prompt: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True 