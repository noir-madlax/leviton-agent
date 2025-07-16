"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Filter, RotateCcw, X, Database, Users, MessageSquare, BarChart3, Loader2 } from "lucide-react"
import { ProjectFilters, FilterOptions } from '../types/filters'
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
    segment: 0,
    is_bestseller: 0
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
        case 'brands': return '🏢'  // 改：packaging_types -> brands，使用品牌图标
        case 'segments': return '🎯'
        case 'is_bestseller': return '⭐'
        default: return ''
      }
    }
    
    // 获取显示标签
    const getDisplayValue = (filterType: keyof ProjectFilters, value: string) => {
      // 移除包装类型的特殊处理，brand直接显示原值
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

  const handleBrandSelect = (brand: string) => {
    if (brand === 'all') {
      setPendingFilters(prev => ({ ...prev, brands: [] }))
    } else if (!pendingFilters.brands.includes(brand)) {
      setPendingFilters(prev => ({ 
        ...prev, 
        brands: [...prev.brands, brand] 
      }))
    }
    setSelectKeys(prev => ({ ...prev, brand: prev.brand + 1 }))
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

  const handleIsBestsellerSelect = (value: string) => {
    if (value === 'all') {
      setPendingFilters(prev => ({ ...prev, is_bestseller: undefined }))
    } else {
      setPendingFilters(prev => ({ ...prev, is_bestseller: value }))
    }
    setSelectKeys(prev => ({ ...prev, is_bestseller: prev.is_bestseller + 1 }))
  }

  const handleRemoveCategory = (category: string) => {
    setPendingFilters(prev => ({
      ...prev,
      categories: prev.categories.filter(c => c !== category)
    }))
  }

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

  const handleRemoveIsBestseller = () => {
    setPendingFilters(prev => ({
      ...prev,
      is_bestseller: undefined
    }))
  }

  const handleApplyFilters = () => {
    onFiltersChange(pendingFilters)
  }

  // 检查是否有待处理的变化
  const hasPendingChanges = (
    JSON.stringify(pendingFilters.categories) !== JSON.stringify(currentFilters.categories) ||
    JSON.stringify(pendingFilters.brands) !== JSON.stringify(currentFilters.brands) ||  // 改：packaging_types -> brands
    JSON.stringify(pendingFilters.segments) !== JSON.stringify(currentFilters.segments) ||
    pendingFilters.is_bestseller !== currentFilters.is_bestseller ||
    JSON.stringify(pendingFilters.extend_fields) !== JSON.stringify(currentFilters.extend_fields)
  )

  // 重置所有筛选器
  const handleReset = () => {
    const resetFilters = {
      categories: [],
      asins: [],
      brands: [],  // 改：packaging_types -> brands
      segments: [],
      is_bestseller: undefined,
      extend_fields: {}
    }
    setPendingFilters(resetFilters)
    setSelectKeys(prev => ({
      ...prev,
      category: prev.category + 1,
      brand: prev.brand + 1,  // 改：packaging -> brand
      segment: prev.segment + 1,
      is_bestseller: prev.is_bestseller + 1
    }))
  }

  // 检查是否有活动的筛选器
  const hasActiveFilters = pendingFilters.categories.length > 0 || pendingFilters.brands.length > 0 || pendingFilters.segments.length > 0 || pendingFilters.is_bestseller

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
          {level === 'project' ? 'Project Scope & Filters' : 'Chart Filters'}
          {level === 'chart' && chartId && (
            <Badge variant="outline" className="ml-2 text-xs">
              {chartId}
            </Badge>
          )}
        </CardTitle>
        <div className="text-sm text-gray-600">
          {level === 'project' 
            ? 'Filters will apply to the whole project' 
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
        {/* Project Data Preview - 4 color blocks */}
        {level === 'project' && projectData?.stats && (
          <div className="mb-4">
            <div className="mb-2">
              <h3 className="text-sm font-medium text-gray-700">Project Data Scope：</h3>
            </div>
            <div className="grid grid-cols-4 gap-3 mb-3">
              <div className="flex items-center gap-2 p-2 bg-blue-50 rounded">
                <Database className="w-4 h-4 text-blue-500" />
                <div>
                  <p className="text-lg font-bold text-blue-900">{projectData.stats.total_products.toLocaleString()}</p>
                  <p className="text-xs text-blue-600">Products</p>
                </div>
              </div>

              <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
                <Users className="w-4 h-4 text-green-500" />
                <div>
                  <p className="text-lg font-bold text-green-900">{projectData.stats.total_brands}</p>
                  <p className="text-xs text-green-600">Brands</p>
                </div>
              </div>

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
                  <p className="text-xs text-orange-600">Segments</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading state for project data */}
        {level === 'project' && loading && !projectData?.stats && (
          <div className="mb-4">
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
              <span className="text-sm text-gray-600">Loading project data...</span>
            </div>
          </div>
        )}
  <h3 className="text-sm font-medium text-gray-700">Filters：</h3>
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

          {/* Brand Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Brand:</span>  {/* 改：Packaging -> Brand */}
            <Select 
              key={selectKeys.brand}
              onValueChange={handleBrandSelect}
              disabled={finalLoading}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="All Brands" />  {/* 改：All Packaging Types -> All Brands */}
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Brands</SelectItem>  {/* 改：All Packaging Types -> All Brands */}
                {/* 显示实际数据中的品牌 */}
                {projectData?.distributions?.brands && projectData.distributions.brands.length > 0 ? (
                  projectData.distributions.brands
                    .filter(item => !pendingFilters.brands.includes(item.name))
                    .map((item) => (
                      <SelectItem key={item.name} value={item.name}>
                        {item.name} ({item.count} - {item.percentage}%)
                      </SelectItem>
                    ))
                ) : (
                  // Fallback: 显示从available options获取的品牌
                  finalAvailableOptions.brands
                    .filter(brand => !pendingFilters.brands.includes(brand))
                    .map((brand) => {
                      // 从distributions数据中查找对应的计数信息
                      const distributionData = projectData?.distributions?.brands?.find(
                        (item: { name: string; count: number; percentage: number }) => item.name === brand
                      )
                      
                      const displayLabel = distributionData 
                        ? `${brand} (${distributionData.count} - ${distributionData.percentage}%)`
                        : brand
                      
                      return (
                        <SelectItem key={brand} value={brand}>
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

          {/* Is Bestseller Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Bestseller:</span>
            <Select
              key={selectKeys.is_bestseller}
              onValueChange={handleIsBestsellerSelect}
              disabled={finalLoading}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="All Products" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Products</SelectItem>
                {finalAvailableOptions.is_bestseller_options?.includes("true") && (
                  <SelectItem value="true">Bestsellers Only</SelectItem>
                )}
                {finalAvailableOptions.is_bestseller_options?.includes("false") && (
                  <SelectItem value="false">Non-Bestsellers Only</SelectItem>
                )}
                {finalAvailableOptions.is_bestseller_options?.includes("null") && (
                  <SelectItem value="null">Unknown Status</SelectItem>
                )}
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
              {pendingFilters.brands.map(brand => 
                renderFilterBadge('brands', brand, () => handleRemoveBrand(brand))
              )}
              {pendingFilters.segments.map(segment =>
                renderFilterBadge('segments', segment, () => handleRemoveSegment(segment))
              )}
              {/* 添加is_bestseller的Badge显示 */}
              {pendingFilters.is_bestseller && (
                <Badge
                  variant="default"
                  className="text-xs flex items-center gap-1 mr-2 mb-2"
                >
                  ⭐ Bestseller: {
                    pendingFilters.is_bestseller === 'true' ? 'Yes' :
                    pendingFilters.is_bestseller === 'false' ? 'No' : 'Unknown'
                  }
                  <X
                    className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto"
                    onClick={(e) => {
                      e.stopPropagation()
                      e.preventDefault()
                      handleRemoveIsBestseller()
                    }}
                  />
                </Badge>
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