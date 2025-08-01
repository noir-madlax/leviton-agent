"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Filter, Database, Users, Loader2 } from "lucide-react"
import { FilterRenderer } from '@/components/analysis-db/filters'
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
    <Card className="border-gray-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Filter className="w-5 h-5" />
          {projectT('projectScopeAndFilters')}
        </CardTitle>
        <div className="text-sm text-gray-600">
          {projectT('filtersApplyToWholeProject')}
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0 space-y-4">
        {/* Project Data Preview - 保留原有的项目数据展示 */}
        {preloadedData?.stats && (
          <div className="mb-4">
            <div className="mb-2">
              <h3 className="text-sm font-medium text-gray-700">{projectT('projectDataScope')}：</h3>
            </div>
            <div className="grid grid-cols-4 gap-3 mb-3">
              <div className="flex items-center gap-2 p-2 bg-blue-50 rounded">
                <Database className="w-4 h-4 text-blue-500" />
                <div>
                  <p className="text-lg font-bold text-blue-900">{preloadedData.stats.total_products.toLocaleString()}</p>
                  <p className="text-xs text-blue-600">{projectT('products')}</p>
                </div>
              </div>

              <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
                <Users className="w-4 h-4 text-green-500" />
                <div>
                  <p className="text-lg font-bold text-green-900">{preloadedData.stats.total_brands}</p>
                  <p className="text-xs text-green-600">{projectT('brands')}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading state for project data */}
        {(cacheLoading || isDataLoading) && !preloadedData?.stats && (
          <div className="mb-4">
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
              <span className="text-sm text-gray-600">{projectT('loadingProjectData')}</span>
            </div>
          </div>
        )}

        {/* 使用新的 FilterRenderer 组件 */}
        <FilterRenderer
          currentFilters={initialFilters}
          onChange={onFiltersChange}
          availableOptions={filterOptions}
          projectId={projectId}
          projectData={preloadedData}
          filterConfig={null} // 暂时为 null，后续会从配置中获取
          loading={cacheLoading || isDataLoading}
          visibleFilters={{ categories: true, extend_fields: true }}
        />
      </CardContent>
    </Card>
  )
} 