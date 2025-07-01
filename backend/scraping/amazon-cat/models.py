"""Amazon Category Fetching Data Models"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CategoryFetchStatus(Enum):
    """类别获取状态枚举"""
    NOT_STARTED = "not_started"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RunStatus(Enum):
    """运行状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CategoryInfo:
    """类别信息"""
    category_id: str
    name: str
    level: int
    parent_id: Optional[str] = None
    link: Optional[str] = None
    status: CategoryFetchStatus = CategoryFetchStatus.NOT_STARTED
    children_count: int = 0
    children_processed: int = 0
    error_message: Optional[str] = None
    last_attempt: Optional[datetime] = None
    retry_count: int = 0


@dataclass
class FetchConfig:
    """获取配置"""
    amazon_domain: str = "amazon.com"
    api_delay_seconds: float = 1.0
    max_retries: int = 3
    max_depth: int = 10
    skip_existing: bool = True
    target_category: Optional[str] = None  # 指定获取的顶级类别
    concurrent_requests: int = 1  # 并发请求数，暂时保持为1


@dataclass
class FetchRun:
    """获取运行记录"""
    run_id: str
    domain: str
    status: RunStatus
    started_at: datetime
    config: FetchConfig
    current_category: Optional[str] = None
    current_level: int = 0
    total_categories: int = 0
    processed_categories: int = 0
    failed_categories: int = 0
    api_calls_made: int = 0
    errors: List[str] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


@dataclass
class ProgressSnapshot:
    """进度快照"""
    run_id: str
    timestamp: datetime
    status: RunStatus
    current_category: Optional[str]
    current_level: int
    progress_percentage: float
    categories_by_status: Dict[CategoryFetchStatus, int]
    recent_activity: List[str]
    estimated_remaining_time: Optional[int] = None


@dataclass
class APIResponse:
    """API响应记录"""
    category_id: str
    timestamp: datetime
    success: bool
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None  # 保存的文件路径


@dataclass
class CategoryHierarchy:
    """类别层级结构"""
    root_categories: List[CategoryInfo]
    category_map: Dict[str, CategoryInfo] = field(default_factory=dict)
    parent_child_map: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_category(self, category: CategoryInfo):
        """添加类别到层级结构"""
        self.category_map[category.category_id] = category
        
        if category.parent_id:
            if category.parent_id not in self.parent_child_map:
                self.parent_child_map[category.parent_id] = []
            if category.category_id not in self.parent_child_map[category.parent_id]:
                self.parent_child_map[category.parent_id].append(category.category_id)
        else:
            # 顶级类别
            if category not in self.root_categories:
                self.root_categories.append(category)
    
    def get_children(self, category_id: str) -> List[CategoryInfo]:
        """获取指定类别的子类别"""
        child_ids = self.parent_child_map.get(category_id, [])
        return [self.category_map[child_id] for child_id in child_ids if child_id in self.category_map]
    
    def get_category_path(self, category_id: str) -> List[str]:
        """获取类别的完整路径"""
        path = []
        current = self.category_map.get(category_id)
        
        while current:
            path.insert(0, current.name)
            if current.parent_id:
                current = self.category_map.get(current.parent_id)
            else:
                break
                
        return path


@dataclass
class FetchStatistics:
    """获取统计信息"""
    total_api_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_categories_found: int = 0
    total_categories_saved: int = 0
    categories_by_level: Dict[int, int] = field(default_factory=dict)
    average_response_time: float = 0.0
    total_data_size_mb: float = 0.0 