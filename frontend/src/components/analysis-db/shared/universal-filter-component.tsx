"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Filter, RotateCcw, X, ChevronUp, ChevronDown } from "lucide-react"
import { ProjectFilters, FilterOptions } from '../types/filters'
import { DynamicExtendFieldsFilter } from './dynamic-extend-fields-filter'
import { useFilterCache } from '../hooks/use-filter-cache'

// 包装类型选项
const PACKAGING_TYPE_OPTIONS = [
  { value: 'individual', label: 'Individual/Unknown' },
  { value: 'package', label: 'Package (Multi-pack)' }
] as const

interface UniversalFilterProps {
  level: 'project' | 'chart'
  chartId?: string
  projectId: string
  currentFilters: ProjectFilters
  appliedFilters?: ProjectFilters // 用于显示哪些来自project
  availableOptions?: FilterOptions // 现在是可选的，如果不提供则从缓存获取
  onFiltersChange: (filters: ProjectFilters) => void
  projectData?: any
  loading?: boolean
  useCachedData?: boolean // 新增：是否使用缓存数据
}

export function UniversalFilterComponent({
  level,
  chartId,
  projectId,
  currentFilters,
  appliedFilters,
  availableOptions,
  onFiltersChange,
  projectData,
  loading = false,
  useCachedData = true // 默认使用缓存数据
}: UniversalFilterProps) {
  const [pendingFilters, setPendingFilters] = useState<ProjectFilters>(currentFilters)
  const [selectKeys, setSelectKeys] = useState({
    category: 0,
    packaging: 0,
    segment: 0
  })

  // 如果使用缓存数据，则从缓存获取筛选器选项
  const { filterOptions: cachedOptions, isLoading: cacheLoading, error: cacheError } = useFilterCache(projectId)
  
  // 确定最终使用的筛选器选项
  const finalAvailableOptions = useCachedData ? cachedOptions : availableOptions
  const finalLoading = useCachedData ? cacheLoading : loading

  // 同步外部传入的筛选器变化
  useEffect(() => {
    setPendingFilters(currentFilters)
  }, [currentFilters])

  // 判断某个筛选项是否来自project
  const isFromProject = (filterType: keyof ProjectFilters, value: string): boolean => {
    if (level === 'project' || !appliedFilters) return false
    
    const projectValues = appliedFilters[filterType] as string[]
    return projectValues?.includes(value) || false
  }

  // 渲染筛选项标签，区分来源
  const renderFilterBadge = (filterType: keyof ProjectFilters, value: string, onRemove: () => void) => {
    const fromProject = isFromProject(filterType, value)
    
    return (
      <Badge
        key={value}
        variant={fromProject ? "secondary" : "default"}
        className={`mr-2 mb-2 ${fromProject ? 'bg-blue-100 text-blue-800 border-blue-300' : ''}`}
      >
        {fromProject && <span className="mr-1">📌</span>}
        {value}
        <X 
          className="w-3 h-3 ml-1 cursor-pointer hover:text-red-500" 
          onClick={onRemove} 
        />
      </Badge>
    )
  }

  const handleCategorySelect = (category: string) => {
    if (category === 'all') {
      setPendingFilters(prev => ({ ...prev, categories: [] }))
    } else if (!pendingFilters.categories.includes(category)) {
      setPendingFilters(prev => ({ 
        ...prev, 
        categories: [...prev.categories, category] 
      }))
    }
    setSelectKeys(prev => ({ ...prev, category: prev.category + 1 }))
  }

  const handlePackagingTypeSelect = (packagingType: string) => {
    if (packagingType === 'all') {
      setPendingFilters(prev => ({ ...prev, packaging_types: [] }))
    } else if (!pendingFilters.packaging_types.includes(packagingType)) {
      setPendingFilters(prev => ({ 
        ...prev, 
        packaging_types: [...prev.packaging_types, packagingType] 
      }))
    }
    setSelectKeys(prev => ({ ...prev, packaging: prev.packaging + 1 }))
  }

  const handleSegmentSelect = (segment: string) => {
    if (segment === 'all') {
      setPendingFilters(prev => ({ ...prev, segments: [] }))
    } else if (!pendingFilters.segments.includes(segment)) {
      setPendingFilters(prev => ({ 
        ...prev, 
        segments: [...prev.segments, segment] 
      }))
    }
    setSelectKeys(prev => ({ ...prev, segment: prev.segment + 1 }))
  }

  const handleRemoveCategory = (category: string) => {
    setPendingFilters(prev => ({
      ...prev,
      categories: prev.categories.filter(c => c !== category)
    }))
  }

  const handleRemovePackagingType = (packagingType: string) => {
    setPendingFilters(prev => ({
      ...prev,
      packaging_types: prev.packaging_types.filter(pt => pt !== packagingType)
    }))
  }

  const handleRemoveSegment = (segment: string) => {
    setPendingFilters(prev => ({
      ...prev,
      segments: prev.segments.filter(s => s !== segment)
    }))
  }

  const handleApplyFilters = () => {
    onFiltersChange(pendingFilters)
  }

  const handleReset = () => {
    const resetFilters: ProjectFilters = level === 'project' 
      ? { categories: [], packaging_types: [], segments: [], extend_fields: {}, asins: [] }
      : { 
          categories: appliedFilters?.categories || [],
          packaging_types: appliedFilters?.packaging_types || [],
          segments: appliedFilters?.segments || [],
          extend_fields: {},
          asins: []
        } // chart级重置时保留来自project的筛选
    
    setPendingFilters(resetFilters)
    setSelectKeys(prev => ({ 
      category: prev.category + 1, 
      packaging: prev.packaging + 1, 
      segment: prev.segment + 1 
    }))
  }

  const hasPendingChanges = JSON.stringify(pendingFilters) !== JSON.stringify(currentFilters)
  const hasActiveFilters = pendingFilters.categories.length > 0 || 
                          pendingFilters.packaging_types.length > 0 || 
                          pendingFilters.segments.length > 0 ||
                          Object.keys(pendingFilters.extend_fields).length > 0

  // 如果没有筛选器选项，显示加载状态
  if (!finalAvailableOptions) {
    return (
      <div className="p-4 text-center">
        <div className="flex items-center justify-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-gray-500">Loading filter options...</span>
        </div>
      </div>
    )
  }

  return (
    <Card className="border-gray-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Filter className="w-5 h-5" />
          {level === 'project' ? 'Project Filters' : 'Chart Filters'}
          {level === 'chart' && chartId && (
            <Badge variant="outline" className="ml-2 text-xs">
              {chartId}
            </Badge>
          )}
        </CardTitle>
        <div className="text-sm text-gray-600">
          {level === 'project' 
            ? 'Filters will apply to all charts and responses' 
            : (
              <span>
                📌 indicates filters inherited from project level. 
                Chart-specific filters will be applied in addition to project filters.
              </span>
            )
          }
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0 space-y-4">
        {/* 筛选器控件 */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Category:</span>
            <Select 
              key={selectKeys.category}
              onValueChange={handleCategorySelect}
              disabled={finalLoading}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent className="max-h-80">
                <SelectItem value="all">All Categories</SelectItem>
                {finalAvailableOptions.categories
                  .filter(cat => !pendingFilters.categories.includes(cat))
                  .map(category => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          {/* Packaging Type Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Packaging:</span>
            <Select 
              key={selectKeys.packaging}
              onValueChange={handlePackagingTypeSelect}
              disabled={finalLoading}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="All Packaging Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Packaging Types</SelectItem>
                {PACKAGING_TYPE_OPTIONS
                  .filter(option => !pendingFilters.packaging_types.includes(option.value))
                  .map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          {/* Segments Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Segments:</span>
            <Select 
              key={selectKeys.segment}
              onValueChange={handleSegmentSelect}
              disabled={finalLoading}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="All Segments" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Segments</SelectItem>
                {finalAvailableOptions.segments
                  .filter(segment => !pendingFilters.segments.includes(segment))
                  .map(segment => (
                    <SelectItem key={segment} value={segment}>
                      {segment}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Extend Fields Filter */}
        <DynamicExtendFieldsFilter
          projectId={projectId}
          extendFields={pendingFilters.extend_fields}
          onFilterChange={(fields) => setPendingFilters(prev => ({ ...prev, extend_fields: fields }))}
          className="flex-wrap"
          projectData={projectData}
        />

        {/* 已选择的筛选器显示 */}
        {hasActiveFilters && (
          <div className="space-y-2">
            {pendingFilters.categories.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-700">Categories:</span>
                <div className="mt-1">
                  {pendingFilters.categories.map(category => 
                    renderFilterBadge('categories', category, () => handleRemoveCategory(category))
                  )}
                </div>
              </div>
            )}

            {pendingFilters.packaging_types.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-700">Packaging Types:</span>
                <div className="mt-1">
                  {pendingFilters.packaging_types.map(packagingType => 
                    renderFilterBadge('packaging_types', packagingType, () => handleRemovePackagingType(packagingType))
                  )}
                </div>
              </div>
            )}

            {pendingFilters.segments.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-700">Segments:</span>
                <div className="mt-1">
                  {pendingFilters.segments.map(segment => 
                    renderFilterBadge('segments', segment, () => handleRemoveSegment(segment))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex justify-between items-center pt-2 border-t">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleReset}
            disabled={finalLoading}
            className="flex items-center gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </Button>
          <Button 
            size="sm" 
            onClick={handleApplyFilters}
            disabled={!hasPendingChanges || finalLoading}
          >
            Apply Filters
          </Button>
        </div>
      </CardContent>
    </Card>
  )
} 