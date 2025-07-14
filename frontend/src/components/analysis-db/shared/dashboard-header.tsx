'use client';

interface DashboardHeaderProps {
  onProjectChange?: (projectId: string) => void;
  selectedProjectId?: string | null;
  onFiltersChange?: (filters: { categories: string[]; asins: string[] }) => void;
}

export function DashboardHeader({}: DashboardHeaderProps) {
  // 过滤器功能已移至页面标题区域，这里保留接口以备将来扩展

  return (
    <div className="mb-2">
      {/* 过滤器功能已集成到页面标题区域 */}
      {/* 这里可以添加其他dashboard header内容 */}
    </div>
  );
}
