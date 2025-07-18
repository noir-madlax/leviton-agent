"use client"

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Filter, ChevronUp, ChevronDown, BarChart3, DollarSign, Target } from "lucide-react"
import { ProjectFilters, DEFAULT_FILTERS } from '../types/filters'
import { UniversalFilterComponent } from './universal-filter-component'
import { useFilterState } from '../hooks/use-filter-state'
import { useFilterCache } from '../hooks/use-filter-cache'

interface ChartWithFiltersProps {
  chartId: string
  chartType: string
  projectId: string
  title: string
  children: React.ReactNode
  projectFilters?: ProjectFilters
  onFilterChange?: (filters: ProjectFilters) => void
}

export function ChartWithFilters({ 
  chartId, 
  chartType, // eslint-disable-line @typescript-eslint/no-unused-vars
  projectId, 
  title, 
  children,
  projectFilters,
  onFilterChange
}: ChartWithFiltersProps) {
  const filterState = useFilterState(projectId, projectFilters)
  const [showFilters, setShowFilters] = useState(false)
  
  // 使用缓存hook获取loading状态
  const { isLoading: cacheLoading } = useFilterCache(projectId)

  // 初始化chart筛选器
  useEffect(() => {
    filterState.initializeChartFilter(chartId)
  }, [chartId, filterState])

  const currentChartFilters = filterState.getChartFilters(chartId) || { ...DEFAULT_FILTERS }
  const finalFilters = filterState.getFinalFilters(chartId) || { ...DEFAULT_FILTERS }

  const handleChartFiltersChange = (newFilters: ProjectFilters) => {
    filterState.updateChartFilters(chartId, newFilters)
    onFilterChange?.(newFilters)
  }

  // 计算活跃筛选器数量
  const activeFiltersCount = finalFilters.categories.length + 
                           finalFilters.brands.length + 
                           finalFilters.segments.length +
                           Object.keys(finalFilters.extend_fields).length

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          {title}
        </h3>
        <div className="flex items-center gap-2">
          {activeFiltersCount > 0 && (
            <Badge variant="outline" className="text-xs">
              {activeFiltersCount} filters
            </Badge>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            disabled={cacheLoading}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            {cacheLoading ? 'Loading...' : 'Filters'}
            {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {showFilters && (
        <UniversalFilterComponent
          level="chart"
          chartId={chartId}
          projectId={projectId}
          currentFilters={currentChartFilters}
          appliedFilters={projectFilters}
          onFiltersChange={handleChartFiltersChange}
          useCachedData={true}
        />
      )}

      <div className="chart-content">
        {children}
      </div>
    </div>
  )
} 

interface ChartHeaderProps {
  title: string
  icon?: React.ComponentType<{ className?: string }>
}

export function ChartHeader({ title, icon: Icon = BarChart3 }: ChartHeaderProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <Icon className="w-5 h-5" />
          {title}
        </h3>
      </div>
    </div>
  )
} 