"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Filter, RotateCcw, X, Database, Users, Loader2 } from "lucide-react"
import { ProjectFilters, FilterOptions } from '../types/filters'
import { DynamicExtendFieldsFilter } from './dynamic-extend-fields-filter'
import { CategoryFilter } from '../filters'
import { useFilterCache } from '../hooks/use-filter-cache'
import { useUnifiedFilterData } from '../hooks/use-unified-filter-data'
import { useCommonT, useProjectT, useFiltersT } from '@/i18n/hooks'

// 新增：过滤器配置接口
interface FilterConfig {
  visible_filters: Record<string, boolean>
  default_values: Record<string, string[] | Record<string, string>>
  extend_fields: Array<{
    field_name: string
    display_name: string
    field_type: string
    filter_options: Record<string, string[] | string | boolean>
  }>
}


interface UniversalFilterProps {
  level: 'project' | 'chart'
  chartId?: string
  projectId: string
  currentFilters: ProjectFilters
  appliedFilters?: ProjectFilters // 用于显示哪些来自project
  availableOptions?: FilterOptions // 现在是可选的，如果不提供则从缓存获取
  onFiltersChange: (filters: ProjectFilters) => void
  projectData?: {
    stats?: {
      total_products: number;
      total_brands: number;
      total_reviews: number;
      segment_count: number;
    };
    distributions?: {
      categories?: Array<{ name: string; count: number; percentage: number }>
      brands?: Array<{ name: string; count: number; percentage: number }>
      segments?: Array<{ name: string; count: number; percentage: number }>
      packaging_types?: Array<{ name: string; count: number; percentage: number }> // 保留：包装类型分布数据（来自extend字段）
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
    brand: 0,  // 改：packaging -> brand
    segment: 0
  })
  const [applyingFilters, setApplyingFilters] = useState(false)

  // 新增：过滤器配置状态
  const [filterConfig, setFilterConfig] = useState<FilterConfig | null>(null)
  const [configLoading, setConfigLoading] = useState(false)
  
  // 国际化hooks
  const commonT = useCommonT()
  const projectT = useProjectT()
  const filtersT = useFiltersT()

  // 使用统一数据源，优先使用统一filter数据，fallback到原有逻辑
  const { filterData: unifiedFilterData, isLoading: unifiedLoading } = useUnifiedFilterData(projectId)
  const { filterOptions: cachedOptions, isLoading: cacheLoading } = useFilterCache(projectId)
  
  // 确定最终使用的筛选器选项：优先统一数据源，fallback到原有逻辑
  const finalAvailableOptions = useCachedData 
    ? (unifiedFilterData || cachedOptions || availableOptions)
    : availableOptions
  const finalLoading = useCachedData 
    ? (unifiedLoading || cacheLoading) 
    : loading

  // 新增：加载过滤器配置（优化：使用统一数据源，避免重复请求）
  useEffect(() => {
    const loadFilterConfig = async () => {
      if (!projectId) return

      // 优先使用统一过滤器数据源，如果可用的话
      if (unifiedFilterData) {
        console.log('🔧 [UNIVERSAL-FILTER] Using unified filter data instead of separate config API')
        setFilterConfig({
          visible_filters: {
            'categories': true,
            'brands': true,
            'Time Period': true,
            'segments': true
          },
          default_values: {},
          extend_fields: []
        })
        setConfigLoading(false)
        return
      }

      setConfigLoading(true)
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
        const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/filter-config`)

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const result = await response.json()
        setFilterConfig(result.config)

        console.log('🔧 [UNIVERSAL-FILTER] Loaded filter configuration:', result.config)
      } catch (error) {
        console.error('Error loading filter config:', error)
        // 如果加载失败，使用默认配置（显示所有过滤器）
        setFilterConfig({
          visible_filters: {
            'categories': true,
            'brands': true,
            'Time Period': true,
            'segments': true
          },
          default_values: {},
          extend_fields: []
        })
      } finally {
        setConfigLoading(false)
      }
    }

    loadFilterConfig()
  }, [projectId, unifiedFilterData])

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

  // 新增：处理extend_fields数组中单个元素的删除
  const handleRemoveExtendFieldItem = (fieldName: string, item: string) => {
    setPendingFilters(prev => {
      const newExtendFields = { ...prev.extend_fields }
      const currentArray = Array.isArray(newExtendFields[fieldName]) ? newExtendFields[fieldName] : []
      const updatedArray = currentArray.filter((i: string) => i !== item)
      
      if (updatedArray.length === 0) {
        delete newExtendFields[fieldName]
      } else {
        newExtendFields[fieldName] = updatedArray
      }
      
      return { ...prev, extend_fields: newExtendFields }
    })
  }

  // 渲染筛选项标签，区分来源
  const renderFilterBadge = (filterType: keyof ProjectFilters, value: string, onRemove: () => void) => {
    const fromProject = isFromProject(filterType, value)
    
    // 添加对应的图标前缀和筛选器类型标识
    const getPrefix = (filterType: keyof ProjectFilters) => {
      switch (filterType) {
        case 'categories': return '📁 Amazon Category:'
        case 'brands': return '🏢 Brand:'  
        case 'segments': return '🎯 Product Segment:'
        default: return ''
      }
    }
    
    // 获取显示标签
    const getDisplayValue = (filterType: keyof ProjectFilters, value: string) => {
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
          className="w-3 h-3 hidden cursor-pointer hover:text-red-500 pointer-events-auto" 
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
          className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto ml-1" 
          onClick={(e) => {
            e.stopPropagation()
            e.preventDefault()
            onRemove()
          }}
        />
      </Badge>
    )
  }





  // Category filter logic moved to CategoryFilter component

  const handleBrandToggle = (brand: string, checked: boolean) => {
    if (checked) {
      if (!pendingFilters.brands.includes(brand)) {
        setPendingFilters(prev => ({ 
          ...prev, 
          brands: [...prev.brands, brand] 
        }))
      }
    } else {
      setPendingFilters(prev => ({
        ...prev,
        brands: prev.brands.filter(b => b !== brand)
      }))
    }
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

  // Category removal logic moved to CategoryFilter component

  const handleRemoveBrand = (brand: string) => {
    setPendingFilters(prev => ({
      ...prev,
      brands: prev.brands.filter(b => b !== brand)
    }))
  }

  const handleRemoveSegment = (segment: string) => {
    setPendingFilters(prev => ({
      ...prev,
      segments: prev.segments.filter(s => s !== segment)
    }))
  }

  const handleApplyFilters = async () => {
    setApplyingFilters(true)
    
    // 模拟短暂延迟，让用户看到loading效果
    await new Promise(resolve => setTimeout(resolve, 10))
    
    onFiltersChange(pendingFilters)
    
    setApplyingFilters(false)
  }

  // 检查是否有待处理的变化
  const hasPendingChanges = (
    JSON.stringify(pendingFilters.categories) !== JSON.stringify(currentFilters.categories) ||
    JSON.stringify(pendingFilters.brands) !== JSON.stringify(currentFilters.brands) ||  // 改：packaging_types -> brands
    JSON.stringify(pendingFilters.segments) !== JSON.stringify(currentFilters.segments) ||
    JSON.stringify(pendingFilters.extend_fields) !== JSON.stringify(currentFilters.extend_fields)
  )

  // 重置所有筛选器
  const handleReset = () => {
    const resetFilters = {
      categories: [],
      asins: [],
      brands: [],  // 改：packaging_types -> brands
      segments: [],
      extend_fields: {},
      time_period: "" // 🔧 不设置前端默认值
    }
    setPendingFilters(resetFilters)
    setSelectKeys(prev => ({
      ...prev,
      category: prev.category + 1,
      brand: prev.brand + 1,  // 改：packaging -> brand
      segment: prev.segment + 1
    }))
  }

  // 检查是否有活动的筛选器
  const hasActiveFilters = pendingFilters.categories.length > 0 || pendingFilters.brands.length > 0 || pendingFilters.segments.length > 0 || Object.keys(pendingFilters.extend_fields).length > 0

  // 如果配置还在加载中，显示加载状态
  if (configLoading && !filterConfig) {
    return (
      <div className="p-4 text-center">
        <div className="flex items-center justify-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-gray-500">{commonT('loading')}</span>
        </div>
      </div>
    )
  }

  // 如果没有筛选器选项，显示加载状态
  if (!finalAvailableOptions) {
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
          {level === 'project' ? projectT('projectScopeAndFilters') : projectT('chartFilters')}
          {level === 'chart' && chartId && (
            <Badge variant="outline" className="ml-2 text-xs">
              {chartId}
            </Badge>
          )}
        </CardTitle>
        <div className="text-sm text-gray-600">
          {level === 'project' 
            ? projectT('filtersApplyToWholeProject')
            : (
              <span>
                {projectT('chartFiltersDescription')}
              </span>
            )
          }
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0 space-y-4">
        {/* Project Data Preview - 4 color blocks */}
        {level === 'project' && projectData?.stats && (
          <div className="mb-4">
            <div className="mb-2">
              <h3 className="text-sm font-medium text-gray-700">{projectT('projectDataScope')}：</h3>
            </div>
            <div className="grid grid-cols-4 gap-3 mb-3">
              <div className="flex items-center gap-2 p-2 bg-blue-50 rounded">
                <Database className="w-4 h-4 text-blue-500" />
                <div>
                  <p className="text-lg font-bold text-blue-900">{projectData.stats.total_products.toLocaleString()}</p>
                  <p className="text-xs text-blue-600">{projectT('products')}</p>
                </div>
              </div>

              <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
                <Users className="w-4 h-4 text-green-500" />
                <div>
                  <p className="text-lg font-bold text-green-900">{projectData.stats.total_brands}</p>
                  <p className="text-xs text-green-600">{projectT('brands')}</p>
                </div>
              </div>
          {/* 暂时隐藏，project data scope 中的review数据 和 segment数据
              <div className="flex items-center gap-2 p-2 bg-purple-50 rounded">
                <MessageSquare className="w-4 h-4 text-purple-500" />
                <div>
                  <p className="text-lg font-bold text-purple-900">{projectData.stats.total_reviews.toLocaleString()}</p>
                  <p className="text-xs text-purple-600">Reviews</p>
                </div>
              </div>

              <div className="flex items-center gap-2 p-2 bg-orange-50 rounded">
                <BarChart3 className="w-4 h-4 text-orange-500" />
                <div>
                  <p className="text-lg font-bold text-orange-900">{projectData.stats.segment_count}</p>
                  <p className="text-xs text-orange-600">Segment</p>
                </div>
              </div>
              */}
            </div>
          </div>
        )}

        {/* Loading state for project data */}
        {level === 'project' && loading && !projectData?.stats && (
          <div className="mb-4">
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
              <span className="text-sm text-gray-600">{projectT('loadingProjectData')}</span>
            </div>
          </div>
        )}
  <h3 className="text-sm font-medium text-gray-700">{projectT('filters')}：</h3>
        {/* 筛选器控件 */}
        <div className="flex items-center gap-4 flex-wrap">
      
          {/* Category Filter - 使用新的独立组件 */}
          {filterConfig?.visible_filters?.categories && (
            <CategoryFilter
              value={pendingFilters.categories}
              onChange={(categories) => setPendingFilters(prev => ({ ...prev, categories }))}
              availableOptions={finalAvailableOptions}
              projectData={projectData}
              disabled={finalLoading || configLoading}
              loading={finalLoading || configLoading}
            />
          )}

          {/* Brand Filter */}
          {filterConfig?.visible_filters?.brands && (
            <div className="flex flex-col gap-2">
              <span className="text-sm text-gray-600">{filtersT('brand')}:</span>
              <div className="flex items-center gap-4 flex-wrap">
                {finalAvailableOptions?.brands && finalAvailableOptions.brands.length > 0 ? (
                  finalAvailableOptions.brands.map((brandName) => {
                    const isSelected = pendingFilters.brands.includes(brandName)
                    // 尝试从projectData获取计数信息（如果有的话）
                    const distributionData = projectData?.distributions?.brands?.find(
                      (item: { name: string; count: number; percentage: number }) => item.name === brandName
                    )
                    const displayLabel = distributionData 
                      ? `${brandName} (${distributionData.count} ${projectT('products')})`
                      : brandName
                    
                    return (
                      <div key={brandName} className="flex items-center gap-2">
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={(checked) => handleBrandToggle(brandName, checked as boolean)}
                          disabled={finalLoading || configLoading}
                        />
                        <label className="text-sm cursor-pointer">
                          {displayLabel}
                        </label>
                      </div>
                    )
                  })
                ) : (
                  // Fallback: 显示从available options获取的品牌复选框
                  finalAvailableOptions.brands.map((brand) => {
                    // 从distributions数据中查找对应的计数信息
                    const distributionData = projectData?.distributions?.brands?.find(
                      (item: { name: string; count: number; percentage: number }) => item.name === brand
                    )
                    
                    const displayLabel = distributionData 
                      ? `${brand} (${distributionData.count} ${projectT('products')})`
                      : brand
                    
                    const isSelected = pendingFilters.brands.includes(brand)
                    
                    return (
                      <div key={brand} className="flex items-center gap-2">
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={(checked) => handleBrandToggle(brand, checked as boolean)}
                          disabled={finalLoading || configLoading}
                        />
                        <label className="text-sm cursor-pointer">
                          {displayLabel}
                        </label>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          )}

         

          {/* Segments Filter */}
          {filterConfig?.visible_filters?.segments && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">{projectT('segments')}:</span>
              <Select 
                key={selectKeys.segment}
                onValueChange={handleSegmentSelect}
                disabled={finalLoading || configLoading}
              >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                {finalAvailableOptions.segments
                  .map((segment) => {
                    // 从distributions数据中查找对应的计数信息
                    const distributionData = projectData?.distributions?.segments?.find(
                      (item: { name: string; count: number; percentage: number }) => item.name === segment
                    )
                    
                    const displayLabel = distributionData 
                      ? `${segment} (${distributionData.count} ${projectT('products')})`
                      : segment
                    
                    const isSelected = pendingFilters.segments.includes(segment)
                    
                    return (
                      <SelectItem key={segment} value={segment} disabled={isSelected}>
                        <span className="flex items-center gap-2">
                          {isSelected && <span className="text-green-600">✅</span>}
                          {displayLabel}
                        </span>
                      </SelectItem>
                    )
                  })}
              </SelectContent>
            </Select>
          </div>
          )}
        </div>

        {/* Extend Fields Filter */}
        <DynamicExtendFieldsFilter
          projectId={projectId}
          extendFields={pendingFilters.extend_fields}
          onFilterChange={(fields) => setPendingFilters(prev => ({ ...prev, extend_fields: fields }))}
          className="flex-wrap"
          projectData={projectData as {
            distributions: {
              extend_fields: Record<string, Array<{
                name: string
                count: number
                percentage: number
              }>>
            }
          } | null}
          filterConfig={filterConfig}
        />

        {/* 已选择的筛选器显示 - 横向排列 */}
        {hasActiveFilters && (
          <div className="pt-2 border-t border-gray-100">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-600">{projectT('appliedFilters')}:</span>
              {/* Category badges moved to CategoryFilter component */}
              {pendingFilters.brands.map(brand => 
                renderFilterBadge('brands', brand, () => handleRemoveBrand(brand))
              )}
              {pendingFilters.segments.map(segment => 
                renderFilterBadge('segments', segment, () => handleRemoveSegment(segment))
              )}
              {/* 添加extend_fields的Badge显示 */}
              {Object.entries(pendingFilters.extend_fields).map(([fieldName, value]) => {
                if (value === undefined || value === null || value === '') return null
                
                // 获取字段的显示名称
                const displayName = fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                
                // 如果是数组，为每个值创建单独的Badge
                if (Array.isArray(value)) {
                  return value.map((item, index) => 
                    renderExtendFieldBadge(
                      `${fieldName}-${index}`,  // 唯一key
                      item,  // 传递单个item而不是整个数组
                      displayName, 
                      () => handleRemoveExtendFieldItem(fieldName, item)  // 删除单个元素
                    )
                  )
                }
                
                // 单个值的情况
                return renderExtendFieldBadge(
                  fieldName, 
                  value, 
                  displayName, 
                  () => handleRemoveExtendField(fieldName)
                )
              }).flat()}
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
            {filtersT('reset')}
          </Button>
          <Button 
            size="sm" 
            onClick={handleApplyFilters}
            disabled={!hasPendingChanges || finalLoading || applyingFilters}
          >
            {applyingFilters ? (
              <>
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                {commonT('loading')}
              </>
            ) : (
              filtersT('applyFilters')
            )}
          </Button>
        </div>


      </CardContent>
    </Card>
  )
} 