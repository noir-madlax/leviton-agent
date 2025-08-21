"""ASIN过滤器相关模型"""

from typing import List
from pydantic import BaseModel, Field

from ..base_models import BaseRequestModel, BaseResponseModel


class AsinFilterRequest(BaseRequestModel):
    """ASIN过滤器请求模型 - 继承基础请求模型"""

    # 无需额外字段，使用基础模型的 project_id 和 filters

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "filters": {
                    "categories": ["Dimmer Switches", "Light Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "segments": ["Premium"],
                    "extend_fields": {"smart_capability": "Smart"}
                }
            }
        }


class AsinFilterResponse(BaseResponseModel[List[str]]):
    """ASIN过滤器响应模型 - 继承基础响应模型，返回ASIN列表"""

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": None,
                "timestamp": "2024-01-15T10:30:00Z",
                "data": [
                    "B001ABC123",
                    "B002DEF456", 
                    "B003GHI789"
                ]
            }
        }
