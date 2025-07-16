"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Filter, RotateCcw, X } from "lucide-react"
import { ProjectFilters, FilterOptions, PACKAGING_TYPE_OPTIONS } from '../types/filters'
import { DynamicExtendFieldsFilter } from './dynamic-extend-fields-filter'
import { useFilterCache } from '../hooks/use-filter-cache'



interface UniversalFilterProps {
  level: 'project' | 'chart'
  chartId?: string
  projectId: string
  currentFilters: ProjectFilters
  appliedFilters?: ProjectFilters // 用于显示哪些来自project
  availableOptions?: FilterOptions // 现在是可选的，如果不提供则从缓存获取
  onFiltersChange: (filters: ProjectFilters) => void
  projectData?: {
    distributions?: {
      categories?: Array<{ name: string; count: number; percentage: number }>
      packaging_types?: Array<{ name: string; count: number; percentage: number }>
      segments?: Array<{ name: string; count: number; percentage: number }>
    }
  }
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
  const { filterOptions: cachedOptions, isLoading: cacheLoading } = useFilterCache(projectId)
  
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

  // 处理extend_fields的删除
  const handleRemoveExtendField = (fieldName: string) => {
    setPendingFilters(prev => {
      const newExtendFields = { ...prev.extend_fields }
      delete newExtendFields[fieldName]
      return {
        ...prev,
        extend_fields: newExtendFields
      }
    })
  }

  // 渲染筛选项标签，区分来源
  const renderFilterBadge = (filterType: keyof ProjectFilters, value: string, onRemove: () => void) => {
    const fromProject = isFromProject(filterType, value)
    
    // 添加对应的图标前缀
    const getPrefix = (filterType: keyof ProjectFilters) => {
      switch (filterType) {
        case 'categories': return '📁'
        case 'packaging_types': return '📦'
        case 'segments': return '🎯'
        default: return ''
      }
    }
    
    // 获取包装类型的显示标签
    const getDisplayValue = (filterType: keyof ProjectFilters, value: string) => {
      if (filterType === 'packaging_types') {
        const option = PACKAGING_TYPE_OPTIONS.find(opt => opt.value === value)
        return option?.label || value
      }
      return value
    }
    
    return (
      <Badge
        key={`${filterType}-${value}`}
        variant={fromProject ? "secondary" : "default"}
        className={`text-xs flex items-center gap-1 mr-2 mb-2 ${fromProject ? 'bg-blue-100 text-blue-800 border-blue-300' : ''}`}
      >
        {fromProject && <span className="mr-1">📌</span>}
        {getPrefix(filterType)} {getDisplayValue(filterType, value)}
        <X 
          className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto" 
          onClick={(e) => {
            console.log('[FILTER-REMOVE] Clicking X for filter:', filterType, value)
            e.stopPropagation()
            e.preventDefault()
            onRemove()
          }}
        />
      </Badge>
    )
  }

  // 渲染extend_fields的Badge
  const renderExtendFieldBadge = (fieldName: string, value: string | boolean | number | string[] | number[] | undefined, displayName: string, onRemove: () => void) => {
    let displayValue = value
    
    // 对于数组值，显示第一个元素
    if (Array.isArray(value)) {
      displayValue = value[0] || ''
    }
    
    // 对于boolean值，转换为Yes/No
    if (typeof value === 'boolean') {
      displayValue = value ? 'Yes' : 'No'
    }
    
    // 对于range值，显示范围
    if (Array.isArray(value) && value.length === 2) {
      displayValue = `${value[0]}-${value[1]}`
    }
    
    return (
      <Badge
        key={`extend-${fieldName}`}
        variant="default"
        className="text-xs flex items-center gap-1 mr-2 mb-2"
      >
        🔧 {displayName}: {displayValue}
        <X 
          className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto" 
          onClick={(e) => {
            console.log('[FILTER-REMOVE] Clicking X for extend field:', fieldName, value)
            e.stopPropagation()
            e.preventDefault()
            onRemove()
          }}
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
                {/* 调试日志 */}
                {(() => {
                  console.log('🔍 [UNIVERSAL-FILTER] Available category options:', {
                    flat_categories: finalAvailableOptions.categories?.length || 0,
                    hierarchical_categories: finalAvailableOptions.hierarchical_categories?.length || 0,
                    hierarchical_with_children: finalAvailableOptions.hierarchical_categories?.filter(g => g.children.length > 0).length || 0,
                    project_id: projectId,
                    level: level
                  })
                  return null
                })()}
                {finalAvailableOptions.hierarchical_categories && 
                 finalAvailableOptions.hierarchical_categories.length > 0 && 
                 finalAvailableOptions.hierarchical_categories.some(group => group.children.length > 0) ? (
                  // 显示层次结构
                  finalAvailableOptions.hierarchical_categories.map((parentGroup) => (
                    <div key={parentGroup.parent_category} className="mb-2">
                      {/* 父类别标题 */}
                      <div className="px-2 py-1.5 text-sm font-semibold text-gray-700 bg-gray-100 border-b sticky top-0 z-10">
                        📁 {parentGroup.parent_category} ({parentGroup.parent_count} products)
                      </div>
                      
                      {/* 子类别选项 */}
                      {parentGroup.children
                        .filter(child => !pendingFilters.categories.includes(child.category))
                        .map((child) => (
                          <SelectItem 
                            key={child.category} 
                            value={child.category}
                            className="pl-6 py-2"
                          >
                            <div className="flex justify-between items-center w-full">
                              <span className="flex items-center gap-2">
                                🏷️ {child.category}
                              </span>
                              <span className="text-sm text-gray-500">
                                {child.count} ({child.percentage}%)
                              </span>
                            </div>
                          </SelectItem>
                        ))}
                    </div>
                  ))
                ) : (
                  // Fallback: 显示扁平分类结构
                  finalAvailableOptions.categories
                    .filter(cat => !pendingFilters.categories.includes(cat))
                    .map(category => {
                      // 从projectData中查找对应的计数信息
                      const distributionData = projectData?.distributions?.categories?.find(
                        (item: { name: string; count: number; percentage: number }) => item.name === category
                      )
                      
                      const displayLabel = distributionData 
                        ? `${category} (${distributionData.count} - ${distributionData.percentage}%)`
                        : category
                      
                      return (
                        <SelectItem key={category} value={category}>
                          {displayLabel}
                        </SelectItem>
                      )
                    })
                )}
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
                {/* 优先显示实际数据中的包装类型 */}
                {projectData?.distributions?.packaging_types && projectData.distributions.packaging_types.length > 0 ? (
                  projectData.distributions.packaging_types
                    .filter(item => !pendingFilters.packaging_types.includes(item.name.toLowerCase()))
                    .map((item) => {
                      // 标准化名称映射
                      const standardizedName = item.name.toLowerCase().includes('individual') ? 'individual' : 
                                              item.name.toLowerCase().includes('package') ? 'package' : 
                                              item.name.toLowerCase()
                      
                      return (
                        <SelectItem key={standardizedName} value={standardizedName}>
                          {item.name} ({item.count} - {item.percentage}%)
                        </SelectItem>
                      )
                    })
                ) : (
                  // Fallback: 使用固定选项
                  PACKAGING_TYPE_OPTIONS
                    .filter(option => !pendingFilters.packaging_types.includes(option.value))
                    .map((option) => {
                      // 从distributions数据中查找对应的计数信息
                      const distributionData = projectData?.distributions?.packaging_types?.find(
                        (item: { name: string; count: number; percentage: number }) => item.name.toLowerCase() === option.value || 
                                (option.value === 'individual' && item.name.toLowerCase() === 'individual') ||
                                (option.value === 'package' && item.name.toLowerCase() === 'package')
                      )
                      
                      const displayLabel = distributionData 
                        ? `${option.label} (${distributionData.count} - ${distributionData.percentage}%)`
                        : option.label
                      
                      return (
                        <SelectItem key={option.value} value={option.value}>
                          {displayLabel}
                        </SelectItem>
                      )
                    })
                )}
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
                  .map((segment) => {
                    // 从distributions数据中查找对应的计数信息
                    const distributionData = projectData?.distributions?.segments?.find(
                      (item: { name: string; count: number; percentage: number }) => item.name === segment
                    )
                    
                    const displayLabel = distributionData 
                      ? `${segment} (${distributionData.count} - ${distributionData.percentage}%)`
                      : segment
                    
                    return (
                      <SelectItem key={segment} value={segment}>
                        {displayLabel}
                      </SelectItem>
                    )
                  })}
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
          projectData={projectData as any}
        />

        {/* 已选择的筛选器显示 - 横向排列 */}
        {hasActiveFilters && (
          <div className="pt-2 border-t border-gray-100">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-600">Applied filters:</span>
              {pendingFilters.categories.map(category => 
                renderFilterBadge('categories', category, () => handleRemoveCategory(category))
              )}
              {pendingFilters.packaging_types.map(packagingType => 
                renderFilterBadge('packaging_types', packagingType, () => handleRemovePackagingType(packagingType))
              )}
              {pendingFilters.segments.map(segment => 
                renderFilterBadge('segments', segment, () => handleRemoveSegment(segment))
              )}
              {/* 添加extend_fields的Badge显示 */}
              {Object.entries(pendingFilters.extend_fields).map(([fieldName, value]) => {
                if (value === undefined || value === null || value === '') return null
                
                // 获取字段的显示名称
                const displayName = fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                
                return renderExtendFieldBadge(
                  fieldName, 
                  value, 
                  displayName, 
                  () => handleRemoveExtendField(fieldName)
                )
              })}
            </div>
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