"""Progress Tracker - Real-time Progress Monitoring"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import asdict

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
import sys
sys.path.insert(0, str(current_dir))

from category_config import CategoryFetcherConfig
from models import (
    FetchRun, CategoryInfo, ProgressSnapshot, CategoryFetchStatus, 
    RunStatus, FetchStatistics, CategoryHierarchy
)


logger = logging.getLogger(__name__)


class ProgressTracker:
    """进度跟踪器 - 管理执行进度和状态文件"""
    
    def __init__(self, run_id: str):
        """
        初始化进度跟踪器
        
        Args:
            run_id: 运行ID
        """
        self.run_id = run_id
        self.run_dir = CategoryFetcherConfig.get_run_directory(run_id)
        self.progress_file = CategoryFetcherConfig.get_progress_file_path(run_id)
        self.config_file = CategoryFetcherConfig.get_config_file_path(run_id)
        
        # 确保目录存在
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化状态
        self.fetch_run: Optional[FetchRun] = None
        self.hierarchy: CategoryHierarchy = CategoryHierarchy(root_categories=[])
        self.statistics = FetchStatistics()
        self.recent_activities: List[str] = []
        
        logger.info(f"Initialized progress tracker for run: {run_id}")
    
    def initialize_run(self, fetch_run: FetchRun):
        """
        初始化运行记录
        
        Args:
            fetch_run: 获取运行对象
        """
        self.fetch_run = fetch_run
        self._save_config()
        self.update_progress("Run initialized")
        logger.info(f"Initialized run: {self.run_id}")
    
    def update_progress(self, activity: str, current_category: Optional[str] = None):
        """
        更新进度信息
        
        Args:
            activity: 当前活动描述
            current_category: 当前处理的类别
        """
        if not self.fetch_run:
            return
        
        # 更新运行状态
        if current_category:
            self.fetch_run.current_category = current_category
        
        # 添加活动记录
        timestamp = datetime.now().strftime("%H:%M:%S")
        activity_with_time = f"[{timestamp}] {activity}"
        self.recent_activities.append(activity_with_time)
        
        # 保持最近20条活动记录
        if len(self.recent_activities) > 20:
            self.recent_activities = self.recent_activities[-20:]
        
        # 生成进度文件
        self._generate_progress_file()
        
        logger.debug(f"Progress updated: {activity}")
    
    def update_category_status(self, category_id: str, status: CategoryFetchStatus, 
                             error_message: Optional[str] = None):
        """
        更新类别状态
        
        Args:
            category_id: 类别ID
            status: 新状态
            error_message: 错误消息（如果失败）
        """
        if category_id in self.hierarchy.category_map:
            category = self.hierarchy.category_map[category_id]
            category.status = status
            category.last_attempt = datetime.now()
            
            if error_message:
                category.error_message = error_message
                category.retry_count += 1
            
            self._generate_progress_file()
    
    def add_categories(self, categories: List[CategoryInfo]):
        """
        添加类别到层级结构
        
        Args:
            categories: 类别列表
        """
        for category in categories:
            self.hierarchy.add_category(category)
        
        # 更新总数
        if self.fetch_run:
            self.fetch_run.total_categories = len(self.hierarchy.category_map)
        
        self._generate_progress_file()
    
    def increment_processed_count(self):
        """增加已处理类别数量"""
        if self.fetch_run:
            self.fetch_run.processed_categories += 1
        self._generate_progress_file()
    
    def increment_failed_count(self):
        """增加失败类别数量"""
        if self.fetch_run:
            self.fetch_run.failed_categories += 1
        self._generate_progress_file()
    
    def increment_api_calls(self):
        """增加API调用数量"""
        if self.fetch_run:
            self.fetch_run.api_calls_made += 1
        self.statistics.total_api_calls += 1
        self._generate_progress_file()
    
    def update_run_status(self, status: RunStatus):
        """
        更新运行状态
        
        Args:
            status: 新状态
        """
        if self.fetch_run:
            self.fetch_run.status = status
            
            if status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
                self.fetch_run.completed_at = datetime.now()
                duration = (self.fetch_run.completed_at - self.fetch_run.started_at).total_seconds()
                self.fetch_run.duration_seconds = int(duration)
        
        self._generate_progress_file()
        self.update_runs_summary()
    
    def _generate_progress_file(self):
        """生成进度文件"""
        try:
            if not self.fetch_run:
                return
            
            # 计算统计信息
            stats = self._calculate_statistics()
            
            # 生成进度内容
            content = self._build_progress_content(stats)
            
            # 写入文件
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新当前运行链接
            self._update_current_run_link()
            
        except Exception as e:
            logger.error(f"Error generating progress file: {e}")
    
    def _build_progress_content(self, stats: Dict[str, Any]) -> str:
        """
        构建进度文件内容
        
        Args:
            stats: 统计信息
            
        Returns:
            str: 进度文件内容
        """
        if not self.fetch_run:
            return "No run data available"
        
        lines = []
        
        # 标题和基本信息
        lines.append("=" * 50)
        lines.append("  Amazon Category Fetch Progress")
        lines.append("=" * 50)
        lines.append(f"Run ID: {self.run_id}")
        lines.append(f"Domain: {self.fetch_run.domain}")
        lines.append(f"Started: {self.fetch_run.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Status: {self.fetch_run.status.value.upper()}")
        
        if self.fetch_run.completed_at:
            lines.append(f"Completed: {self.fetch_run.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Duration: {self.fetch_run.duration_seconds} seconds")
        
        lines.append("")
        
        # 总体进度
        lines.append("=" * 30)
        lines.append("  Overall Progress")
        lines.append("=" * 30)
        progress_percentage = self._calculate_progress_percentage()
        lines.append(f"Progress: {progress_percentage:.1f}%")
        lines.append(f"Total Categories: {self.fetch_run.total_categories}")
        lines.append(f"Processed: {self.fetch_run.processed_categories}")
        lines.append(f"Failed: {self.fetch_run.failed_categories}")
        lines.append(f"API Calls: {self.fetch_run.api_calls_made}")
        lines.append("")
        
        # 当前处理状态
        if self.fetch_run.current_category:
            lines.append("=" * 30)
            lines.append("  Current Processing")
            lines.append("=" * 30)
            current_cat = self.hierarchy.category_map.get(self.fetch_run.current_category)
            if current_cat:
                lines.append(f"Category: {current_cat.name}")
                lines.append(f"Category ID: {current_cat.category_id}")
                lines.append(f"Level: {current_cat.level}")
                if current_cat.parent_id:
                    path = self.hierarchy.get_category_path(current_cat.category_id)
                    lines.append(f"Path: {' > '.join(path)}")
            lines.append("")
        
        # 根级别类别状态
        lines.append("=" * 30)
        lines.append("  Top Level Categories")
        lines.append("=" * 30)
        for category in self.hierarchy.root_categories:
            status_symbol = self._get_status_symbol(category.status)
            lines.append(f"{status_symbol} {category.name} (ID: {category.category_id})")
            if category.status == CategoryFetchStatus.FAILED and category.error_message:
                lines.append(f"    └─ Error: {category.error_message}")
            elif category.status == CategoryFetchStatus.PROCESSING:
                children_info = f"Children: {category.children_processed}/{category.children_count}"
                lines.append(f"    └─ {children_info}")
        lines.append("")
        
        # 按级别统计
        if stats['categories_by_level']:
            lines.append("=" * 30)
            lines.append("  Categories by Level")
            lines.append("=" * 30)
            for level in sorted(stats['categories_by_level'].keys()):
                count = stats['categories_by_level'][level]
                lines.append(f"Level {level}: {count} categories")
            lines.append("")
        
        # 按状态统计
        status_stats = stats['categories_by_status']
        if status_stats:
            lines.append("=" * 30)
            lines.append("  Categories by Status")
            lines.append("=" * 30)
            for status, count in status_stats.items():
                lines.append(f"{status.value.replace('_', ' ').title()}: {count}")
            lines.append("")
        
        # 最近活动
        if self.recent_activities:
            lines.append("=" * 30)
            lines.append("  Recent Activity")
            lines.append("=" * 30)
            for activity in self.recent_activities[-10:]:  # 显示最近10条
                lines.append(f"  {activity}")
            lines.append("")
        
        # 错误信息
        if self.fetch_run.errors:
            lines.append("=" * 30)
            lines.append("  Errors")
            lines.append("=" * 30)
            for error in self.fetch_run.errors[-5:]:  # 显示最近5个错误
                lines.append(f"  • {error}")
            lines.append("")
        
        # 估计剩余时间
        estimated_time = self._estimate_remaining_time()
        if estimated_time:
            lines.append("=" * 30)
            lines.append("  Estimates")
            lines.append("=" * 30)
            lines.append(f"Estimated remaining time: {estimated_time}")
            lines.append("")
        
        # 配置信息
        if self.fetch_run.config:
            lines.append("=" * 30)
            lines.append("  Configuration")
            lines.append("=" * 30)
            lines.append(f"API Delay: {self.fetch_run.config.api_delay_seconds}s")
            lines.append(f"Max Retries: {self.fetch_run.config.max_retries}")
            lines.append(f"Max Depth: {self.fetch_run.config.max_depth}")
            lines.append(f"Skip Existing: {self.fetch_run.config.skip_existing}")
            if self.fetch_run.config.target_category:
                lines.append(f"Target Category: {self.fetch_run.config.target_category}")
        
        lines.append("=" * 50)
        lines.append(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        
        return '\n'.join(lines)
    
    def _get_status_symbol(self, status: CategoryFetchStatus) -> str:
        """获取状态符号"""
        symbols = {
            CategoryFetchStatus.COMPLETED: "✓",
            CategoryFetchStatus.PROCESSING: "→",
            CategoryFetchStatus.FAILED: "✗",
            CategoryFetchStatus.PENDING: "○",
            CategoryFetchStatus.NOT_STARTED: "○",
            CategoryFetchStatus.SKIPPED: "◦"
        }
        return symbols.get(status, "?")
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        categories_by_level = {}
        categories_by_status = {}
        
        for category in self.hierarchy.category_map.values():
            # 按级别统计
            level = category.level
            categories_by_level[level] = categories_by_level.get(level, 0) + 1
            
            # 按状态统计
            status = category.status
            categories_by_status[status] = categories_by_status.get(status, 0) + 1
        
        return {
            'categories_by_level': categories_by_level,
            'categories_by_status': categories_by_status
        }
    
    def _calculate_progress_percentage(self) -> float:
        """计算进度百分比"""
        if not self.fetch_run or self.fetch_run.total_categories == 0:
            return 0.0
        
        return (self.fetch_run.processed_categories / self.fetch_run.total_categories) * 100
    
    def _estimate_remaining_time(self) -> Optional[str]:
        """估计剩余时间"""
        if not self.fetch_run or self.fetch_run.processed_categories == 0:
            return None
        
        elapsed_seconds = (datetime.now() - self.fetch_run.started_at).total_seconds()
        rate = self.fetch_run.processed_categories / elapsed_seconds  # 每秒处理数量
        
        remaining_categories = self.fetch_run.total_categories - self.fetch_run.processed_categories
        if remaining_categories <= 0 or rate <= 0:
            return None
        
        estimated_seconds = remaining_categories / rate
        
        if estimated_seconds < 60:
            return f"{int(estimated_seconds)} seconds"
        elif estimated_seconds < 3600:
            return f"{int(estimated_seconds / 60)} minutes"
        else:
            return f"{int(estimated_seconds / 3600)} hours {int((estimated_seconds % 3600) / 60)} minutes"
    
    def _save_config(self):
        """保存配置到文件"""
        if not self.fetch_run:
            return
        
        try:
            config_data = {
                "run_id": self.run_id,
                "fetch_run": asdict(self.fetch_run),
                "saved_at": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _update_current_run_link(self):
        """更新当前运行的软链接"""
        try:
            current_link = CategoryFetcherConfig.CURRENT_RUN_LINK
            
            # 删除现有链接
            if current_link.exists() or current_link.is_symlink():
                current_link.unlink()
            
            # 创建新链接
            current_link.symlink_to(self.run_dir.name)
            
        except Exception as e:
            logger.debug(f"Error updating current run link: {e}")
    
    def update_runs_summary(self):
        """更新运行摘要文件"""
        try:
            summary_file = CategoryFetcherConfig.RUNS_SUMMARY_FILE
            
            # 读取现有摘要
            existing_runs = []
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        lines = content.strip().split('\n')
                        existing_runs = [line for line in lines if line.strip() and not line.startswith('=')]
            
            # 创建当前运行的摘要行
            if self.fetch_run:
                status = self.fetch_run.status.value.upper()
                started = self.fetch_run.started_at.strftime('%Y-%m-%d %H:%M')
                domain = self.fetch_run.domain
                progress = f"{self.fetch_run.processed_categories}/{self.fetch_run.total_categories}"
                
                current_summary = f"{self.run_id} | {status} | {started} | {domain} | {progress}"
                
                # 更新或添加当前运行
                updated = False
                for i, line in enumerate(existing_runs):
                    if line.startswith(self.run_id):
                        existing_runs[i] = current_summary
                        updated = True
                        break
                
                if not updated:
                    existing_runs.append(current_summary)
                
                # 保持最近50个运行
                existing_runs = existing_runs[-50:]
                
                # 写入摘要文件
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + '\n')
                    f.write("Amazon Category Fetch Runs Summary\n")
                    f.write("=" * 80 + '\n')
                    f.write("Format: RUN_ID | STATUS | STARTED | DOMAIN | PROGRESS\n")
                    f.write("-" * 80 + '\n')
                    
                    for run_line in existing_runs:
                        f.write(run_line + '\n')
                    
                    f.write("-" * 80 + '\n')
                    f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + '\n')
                
        except Exception as e:
            logger.error(f"Error updating runs summary: {e}")
    
    def load_existing_run(self) -> bool:
        """
        加载现有运行状态
        
        Returns:
            bool: 是否成功加载
        """
        try:
            if not self.config_file.exists():
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 重建FetchRun对象
            run_data = config_data['fetch_run']
            self.fetch_run = FetchRun(**run_data)
            
            logger.info(f"Loaded existing run: {self.run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading existing run: {e}")
            return False 