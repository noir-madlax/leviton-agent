"use client"

import { UniversalFilterComponent } from '@/components/analysis-db/shared/universal-filter-component'
import { ProjectFilters } from '@/components/analysis-db/types/filters'
import { useFilterCache } from '@/components/analysis-db/hooks/use-filter-cache'
import { useCommonT, useProjectT } from '@/i18n/hooks'

interface ProjectFilterWrapperProps {
  projectId: string
  onFiltersChange: (filters: ProjectFilters) => void
  initialFilters: ProjectFilters
  preloadedData?: any
  isDataLoading?: boolean
}

export function ProjectFilterWrapper({
  projectId,
  onFiltersChange,
  initialFilters,
  preloadedData,
  isDataLoading
}: ProjectFilterWrapperProps) {
  // 国际化hooks
  const commonT = useCommonT()
  const projectT = useProjectT()
  
  // 使用缓存系统获取筛选器选项
  const { filterOptions, isLoading: cacheLoading, error: cacheError } = useFilterCache(projectId)

  // 如果缓存失败，显示错误状态
  if (cacheError) {
    return (
      <div className="p-4 text-center">
        <div className="text-red-500">
          {commonT('error')}: {cacheError}
        </div>
      </div>
    )
  }

  // 如果缓存还在加载中，显示加载状态
  if (!filterOptions) {
    return (
      <div className="p-4 text-center">
        <div className="flex items-center justify-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-gray-500">{projectT('loadingFilterOptions')}</span>
        </div>
      </div>
    )
  }

  return (
    <UniversalFilterComponent
      level="project"
      projectId={projectId}
      currentFilters={initialFilters}
      availableOptions={filterOptions}
      onFiltersChange={onFiltersChange}
      projectData={preloadedData}
      loading={cacheLoading || isDataLoading}
      useCachedData={false} // 我们已经从缓存获取了数据，所以不需要组件内部再次使用缓存
    />
  )
} 