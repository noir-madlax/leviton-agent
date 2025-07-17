"use client"

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Filter, RotateCcw, X, Database, Users, MessageSquare, BarChart3, Loader2 } from "lucide-react"
import { databaseService } from '@/components/analysis-db/data/database-service'
import { DynamicExtendFieldsFilter } from './dynamic-extend-fields-filter'
import { PACKAGING_TYPE_OPTIONS, ProjectFilters } from '@/components/analysis-db/types/filters'

interface CategoryFilterAndProjectScopeProps {
  projectId: string | null
  onFiltersChange?: (filters: ProjectFilters) => void
  initialFilters?: ProjectFilters
  preloadedData?: ProjectOverviewData | null
  isDataLoading?: boolean
}

// 添加项目概览数据接口
interface ProjectOverviewData {
  project_name: string;
  created_at: string;
  stats: {
    total_products: number;
    total_brands: number;
    total_reviews: number;
    segment_count: number;
  };
  distributions: {
    sources: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    categories: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    brands: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    segments: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    extend_fields: Record<string, Array<{
      name: string;
      count: number;
      percentage: number;
    }>>;
    packaging_types: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
  };
  available_categories: {
    flat_categories: string[];
    hierarchical_categories: Array<{
      parent_category: string;
      parent_count: number;
      children: Array<{
        category: string;
        count: number;
        percentage: number;
      }>;
    }>;
    total_products: number;
  };
}

export function CategoryFilterAndProjectScope({ 
  projectId, 
  onFiltersChange, 
  initialFilters = { categories: [], asins: [], brands: [], segments: [], extend_fields: {} },  // 改：packaging_types -> brands
  preloadedData,
  isDataLoading
}: CategoryFilterAndProjectScopeProps) {
  // Filter states
  const [availableCategories, setAvailableCategories] = useState<{
    flat_categories: string[];
    hierarchical_categories: Array<{
      parent_category: string;
      parent_count: number;
      children: Array<{
        category: string;
        count: number;
        percentage: number;
      }>;
    }>;
    total_products: number;
  }>({
    flat_categories: [],
    hierarchical_categories: [],
    total_products: 0
  })
  const [availableSegments, setAvailableSegments] = useState<string[]>([])
  const [pendingCategories, setPendingCategories] = useState<string[]>(initialFilters.categories)
  const [appliedCategories, setAppliedCategories] = useState<string[]>(initialFilters.categories)
  const [pendingBrands, setPendingBrands] = useState<string[]>(initialFilters.brands)  // 改：packaging_types -> brands
  const [appliedBrands, setAppliedBrands] = useState<string[]>(initialFilters.brands)  // 改：packaging_types -> brands
  const [pendingSegments, setPendingSegments] = useState<string[]>(initialFilters.segments)
  const [appliedSegments, setAppliedSegments] = useState<string[]>(initialFilters.segments)
  const [pendingExtendFields, setPendingExtendFields] = useState<Record<string, any>>(initialFilters.extend_fields)
  const [appliedExtendFields, setAppliedExtendFields] = useState<Record<string, any>>(initialFilters.extend_fields)
  const [filterLoading, setFilterLoading] = useState(false)

  // 添加Select状态控制
  const [categorySelectKey, setCategorySelectKey] = useState(0)
  const [brandSelectKey, setBrandSelectKey] = useState(0)  // 改：packaging -> brand
  const [segmentSelectKey, setSegmentSelectKey] = useState(0)

  // Project overview states - 优先使用预加载数据
  const [projectData, setProjectData] = useState<ProjectOverviewData | null>(preloadedData || null)
  const [overviewLoading, setOverviewLoading] = useState(isDataLoading || false)

  const loadData = async () => {
    if (!projectId) return

    setFilterLoading(true)
    try {
      const overview = await databaseService.getProjectOverview(projectId)
      
      // 确保包含所有必需字段，提供默认值
      const completeOverview: ProjectOverviewData = {
        ...overview,
        distributions: {
          ...overview.distributions,
          brands: (overview.distributions as any).brands || [],
          segments: (overview.distributions as any).segments || [],
          extend_fields: (overview.distributions as any).extend_fields || {},
          packaging_types: (overview.distributions as any).packaging_types || []
        }
      }
      
      setAvailableCategories(overview.available_categories)
      setProjectData(completeOverview)
      
      // 获取项目segments
      const segments = await databaseService.getProjectSegments(projectId)
      setAvailableSegments(segments)
    } catch (error) {
      console.error('Failed to load project data:', error)
      setAvailableCategories({
        flat_categories: [],
        hierarchical_categories: [],
        total_products: 0
      })
      setAvailableSegments([])
      setProjectData(null)
    } finally {
      setFilterLoading(false)
    }
  }

  // 单独的segments加载函数
  const loadSegments = async () => {
    if (!projectId) return

    try {
      const segments = await databaseService.getProjectSegments(projectId)
      setAvailableSegments(segments)
    } catch (error) {
      console.error('Failed to load project segments:', error)
      setAvailableSegments([])
    }
  }

  // 监听预加载数据变化
  useEffect(() => {
    if (preloadedData) {
      setProjectData(preloadedData)
      setAvailableCategories(preloadedData.available_categories)
      // 即使有预加载数据，也要获取segments数据
      loadSegments()
    }
  }, [preloadedData, projectId])

  // 监听加载状态变化
  useEffect(() => {
    setOverviewLoading(isDataLoading || false)
  }, [isDataLoading])

  // Load data when projectId changes - 只在没有预加载数据时才加载
  useEffect(() => {
    if (!projectId) {
      setAvailableCategories({
        flat_categories: [],
        hierarchical_categories: [],
        total_products: 0
      })
      setAvailableSegments([])
      setPendingCategories([])
      setAppliedCategories([])
      setPendingBrands([])
      setAppliedBrands([])
      setPendingSegments([])
      setAppliedSegments([])
      if (!preloadedData) {
        setProjectData(null)
      }
      return
    }

    // 只在没有预加载数据时才进行数据加载
    if (!preloadedData && !projectData) {
      loadData()
    } else if (!preloadedData) {
      // 如果没有预加载数据但有projectData，仍然需要加载segments
      loadSegments()
    }
  }, [projectId, preloadedData, projectData])

  const loadProjectOverview = useCallback(async () => {
    if (!projectId) return

    setOverviewLoading(true)
    try {
      const categoryFilters = appliedCategories.length > 0 ? appliedCategories : undefined
      const packagingFilters = appliedBrands.length > 0 ? appliedBrands : undefined
      const segmentFilters = appliedSegments.length > 0 ? appliedSegments : undefined
      const extendFields = Object.keys(appliedExtendFields).length > 0 ? appliedExtendFields : undefined
      const overview = await databaseService.getProjectOverview(projectId, categoryFilters, packagingFilters, segmentFilters, extendFields)
      
      // 确保包含所有必需字段，提供默认值
      const completeOverview: ProjectOverviewData = {
        ...overview,
        distributions: {
          ...overview.distributions,
          brands: (overview.distributions as any).brands || [],
          segments: (overview.distributions as any).segments || [],
          extend_fields: (overview.distributions as any).extend_fields || {},
          packaging_types: (overview.distributions as any).packaging_types || []
        }
      }
      
      setProjectData(completeOverview)
    } catch (error) {
      console.error('Failed to load project overview:', error)
      setProjectData(null)
    } finally {
      setOverviewLoading(false)
    }
  }, [projectId, appliedCategories, appliedBrands, appliedSegments, appliedExtendFields])

  // Load project overview when filters change - 重新加载项目概览数据
  useEffect(() => {
    if (!projectId) return
    // 当appliedFilters变化时总是重新加载数据（有过滤器或无过滤器）
    loadProjectOverview()
  }, [projectId, loadProjectOverview])

  const handleCategorySelect = (category: string) => {
    if (category === 'all') {
      setPendingCategories([])
    } else if (!pendingCategories.includes(category)) {
      setPendingCategories(prev => [...prev, category])
    }
    // 重置Select状态
    setCategorySelectKey(prev => prev + 1)
  }

  const handleCategoryRemove = (category: string) => {
    console.log('[FILTER-REMOVE] Clicking X for category:', category)
    console.log('[FILTER-REMOVE] Before removal:', pendingCategories)
    setPendingCategories(prev => prev.filter(c => c !== category))
    console.log('[FILTER-REMOVE] After removal should be triggered')
  }

  const handleBrandSelect = (brand: string) => {
    if (brand === 'all') {
      setPendingBrands([])
    } else if (!pendingBrands.includes(brand)) {
      setPendingBrands(prev => [...prev, brand])
    }
    // 重置Select状态
    setBrandSelectKey(prev => prev + 1)
  }

  const handleBrandRemove = (brand: string) => {
    console.log('[FILTER-REMOVE] Clicking X for brand:', brand)
    console.log('[FILTER-REMOVE] Before removal:', pendingBrands)
    setPendingBrands(prev => prev.filter(b => b !== brand))
    console.log('[FILTER-REMOVE] After removal should be triggered')
  }

  const handleSegmentSelect = (segment: string) => {
    if (segment === 'all') {
      setPendingSegments([])
    } else if (!pendingSegments.includes(segment)) {
      setPendingSegments(prev => [...prev, segment])
    }
    // 重置Select状态
    setSegmentSelectKey(prev => prev + 1)
  }

  const handleSegmentRemove = (segment: string) => {
    console.log('[FILTER-REMOVE] Clicking X for segment:', segment)
    console.log('[FILTER-REMOVE] Before removal:', pendingSegments)
    setPendingSegments(prev => prev.filter(s => s !== segment))
    console.log('[FILTER-REMOVE] After removal should be triggered')
  }

  const handleApplyFilters = () => {
    setAppliedCategories(pendingCategories)
    setAppliedBrands(pendingBrands)
    setAppliedSegments(pendingSegments)
    setAppliedExtendFields(pendingExtendFields)
    if (onFiltersChange) {
      onFiltersChange({
        categories: pendingCategories,
        asins: [],
        brands: pendingBrands,
        segments: pendingSegments,
        extend_fields: pendingExtendFields
      })
    }
  }

  const handleReset = () => {
    setPendingCategories([])
    setAppliedCategories([])
    setPendingBrands([])
    setAppliedBrands([])
    setPendingSegments([])
    setAppliedSegments([])
    setPendingExtendFields({})
    setAppliedExtendFields({})
    // 重置所有Select组件状态
    setCategorySelectKey(prev => prev + 1)
    setBrandSelectKey(prev => prev + 1)
    setSegmentSelectKey(prev => prev + 1)
    if (onFiltersChange) {
      onFiltersChange({
        categories: [],
        asins: [],
        brands: [],
        segments: [],
        extend_fields: {}
      })
    }
  }

  const hasPendingChanges = JSON.stringify(pendingCategories) !== JSON.stringify(appliedCategories) || 
                          JSON.stringify(pendingBrands) !== JSON.stringify(appliedBrands) ||
                          JSON.stringify(pendingSegments) !== JSON.stringify(appliedSegments) ||
                          JSON.stringify(pendingExtendFields) !== JSON.stringify(appliedExtendFields)
  const hasActiveFilters = appliedCategories.length > 0 || appliedBrands.length > 0 || appliedSegments.length > 0 || Object.keys(appliedExtendFields).length > 0

  if (!projectId) {
    return null
  }



  return (
    <div className="mb-4">
      <Card className="border-gray-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filter Project Scope by Product Properties
          </CardTitle>
          <div className="text-sm text-gray-600 mt-1">
            Filters will <strong>apply to all</strong> charts and Xenith responses. Filter by category, packaging type, and segments.
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-0 space-y-4">
          {/* Category Filters Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-4 flex-wrap">
              {/* Category Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Amazon Category:</span>
                <Select key={categorySelectKey} onValueChange={handleCategorySelect} disabled={filterLoading}>
                  <SelectTrigger className="w-48 h-8">
                    <SelectValue placeholder="All Amazon Categories (No Filter)" />
                  </SelectTrigger>
                  <SelectContent className="max-h-80">
                    <SelectItem value="all">All Amazon Categories (No Filter)</SelectItem>
                    {/* 调试日志 */}
                    {(() => {
                      console.log('🔍 [CATEGORY-FILTER-SCOPE] Available category options:', {
                        flat_categories: availableCategories.flat_categories?.length || 0,
                        hierarchical_categories: availableCategories.hierarchical_categories?.length || 0,
                        hierarchical_with_children: availableCategories.hierarchical_categories?.filter(g => g.children.length > 0).length || 0,
                        project_id: projectId
                      })
                      return null
                    })()}
                    {availableCategories.hierarchical_categories && 
                     availableCategories.hierarchical_categories.length > 0 && 
                     availableCategories.hierarchical_categories.some(group => group.children.length > 0) ? (
                      // 显示层次结构
                      availableCategories.hierarchical_categories.map((parentGroup) => (
                        <div key={parentGroup.parent_category} className="mb-2">
                          {/* 父类别标题 */}
                          <div className="px-2 py-1.5 text-sm font-semibold text-gray-700 bg-gray-100 border-b sticky top-0 z-10">
                            📁 {parentGroup.parent_category} ({parentGroup.parent_count} products)
                          </div>
                          
                          {/* 子类别选项 */}
                          {parentGroup.children
                            .map((child) => {
                              const isSelected = pendingCategories.includes(child.category)
                              return (
                                <SelectItem 
                                  key={child.category} 
                                  value={child.category}
                                  className="pl-6 py-2"
                                  disabled={isSelected}
                                >
                                  <div className="flex justify-between items-center w-full">
                                    <span className="flex items-center gap-2">
                                      {isSelected && <span className="text-green-600">✅</span>}
                                      🏷️ {child.category}
                                    </span>
                                    <span className="text-sm text-gray-500">
                                      {child.count} ({child.percentage}%)
                                    </span>
                                  </div>
                                </SelectItem>
                              )
                            })}
                        </div>
                      ))
                    ) : (
                      // Fallback: 显示扁平分类结构
                      availableCategories.flat_categories
                        .map(category => {
                          const isSelected = pendingCategories.includes(category)
                          return (
                            <SelectItem key={category} value={category} disabled={isSelected}>
                              <span className="flex items-center gap-2">
                                {isSelected && <span className="text-green-600">✅</span>}
                                {category}
                              </span>
                            </SelectItem>
                          )
                        })
                    )}
                  </SelectContent>
                </Select>
              </div>

              {/* Brand Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Brand:</span>
                <Select key={brandSelectKey} onValueChange={handleBrandSelect} disabled={filterLoading}>
                  <SelectTrigger className="w-48 h-8">
                    <SelectValue placeholder="All Brands" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Brands</SelectItem>
                    {/* 显示从project数据中获取的brands */}
                    {projectData?.distributions?.brands && projectData.distributions.brands.length > 0 ? (
                      projectData.distributions.brands
                        .map((brand) => {
                          const isSelected = pendingBrands.includes(brand.name)
                          return (
                            <SelectItem key={brand.name} value={brand.name} disabled={isSelected}>
                              <span className="flex items-center gap-2">
                                {isSelected && <span className="text-green-600">✅</span>}
                                {brand.name} ({brand.count} - {brand.percentage}%)
                              </span>
                            </SelectItem>
                          )
                        })
                    ) : (
                      // Fallback: 如果没有brands分布数据，显示空状态
                      <SelectItem value="" disabled>
                        No brands available
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>

              {/* Time Period Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Time Period:</span>
                <Select defaultValue="recent-month" disabled>
                  <SelectTrigger className="w-48 h-8">
                    <SelectValue placeholder="Select time period" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="recent-month">最近一个月</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Segments Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Product Segments:</span>
                <Select key={segmentSelectKey} onValueChange={handleSegmentSelect} disabled={filterLoading}>
                  <SelectTrigger className="w-48 h-8">
                    <SelectValue placeholder="All Segments" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Segments</SelectItem>
                    {availableSegments
                      .map((segment) => {
                        // 从distributions数据中查找对应的计数信息
                        const distributionData = projectData?.distributions.segments?.find(
                          item => item.name === segment
                        )
                        
                        const displayLabel = distributionData 
                          ? `${segment} (${distributionData.count} - ${distributionData.percentage}%)`
                          : segment
                        
                        const isSelected = pendingSegments.includes(segment)
                        
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

              {/* Extend Fields Filter */}
              <DynamicExtendFieldsFilter
                projectId={projectId}
                extendFields={pendingExtendFields}
                onFilterChange={setPendingExtendFields}
                className="flex-wrap"
                projectData={projectData}
              />

              {/* Apply button */}
              <Button
                onClick={handleApplyFilters}
                disabled={!hasPendingChanges}
                size="sm"
                className="h-8"
              >
                Apply Filters
              </Button>

              {/* Reset button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                disabled={!hasActiveFilters && pendingCategories.length === 0 && pendingBrands.length === 0 && pendingSegments.length === 0 && Object.keys(pendingExtendFields).length === 0}
                className="h-8"
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                Reset
              </Button>

              {/* Status indicator */}
              {hasPendingChanges && (
                <div className="text-xs text-orange-600">
                  {pendingCategories.length + pendingBrands.length + pendingSegments.length + Object.keys(pendingExtendFields).length} pending changes
                </div>
              )}
              {hasActiveFilters && !hasPendingChanges && (
                <div className="text-xs text-green-600">
                  {appliedCategories.length + appliedBrands.length + appliedSegments.length + Object.keys(appliedExtendFields).length} filter{(appliedCategories.length + appliedBrands.length + appliedSegments.length + Object.keys(appliedExtendFields).length) > 1 ? 's' : ''} applied
                </div>
              )}
            </div>

            {/* Pending filters display */}
            {(pendingCategories.length > 0 || pendingBrands.length > 0 || pendingSegments.length > 0 || Object.keys(pendingExtendFields).length > 0) && (
              <div className="pt-2 border-t border-gray-100">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-gray-600">
                    {hasPendingChanges ? 'Pending filters:' : 'Applied filters:'}
                  </span>
                  {pendingCategories.map((category) => (
                    <Badge
                      key={`category-${category}`}
                      variant={hasPendingChanges ? "outline" : "secondary"}
                      className={`text-xs flex items-center gap-1 ${
                        hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                      }`}
                    >
                      📁 {category}
                      <X
                        className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto"
                        onClick={(e) => {
                          console.log('[FILTER-REMOVE] Clicking X for category badge:', category)
                          e.stopPropagation()
                          e.preventDefault()
                          handleCategoryRemove(category)
                        }}
                      />
                    </Badge>
                  ))}
                  {pendingBrands.map((brand) => (
                    <Badge
                      key={`brand-${brand}`}
                      variant={hasPendingChanges ? "outline" : "secondary"}
                      className={`text-xs flex items-center gap-1 ${
                        hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                      }`}
                    >
                      🏷️ {brand}
                      <X
                        className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto"
                        onClick={(e) => {
                          console.log('[FILTER-REMOVE] Clicking X for brand badge:', brand)
                          e.stopPropagation()
                          e.preventDefault()
                          handleBrandRemove(brand)
                        }}
                      />
                    </Badge>
                  ))}
                  {pendingSegments.map((segment) => (
                    <Badge
                      key={`segment-${segment}`}
                      variant={hasPendingChanges ? "outline" : "secondary"}
                      className={`text-xs flex items-center gap-1 ${
                        hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                      }`}
                    >
                      🎯 {segment}
                      <X
                        className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto"
                        onClick={(e) => {
                          console.log('[FILTER-REMOVE] Clicking X for segment badge:', segment)
                          e.stopPropagation()
                          e.preventDefault()
                          handleSegmentRemove(segment)
                        }}
                      />
                    </Badge>
                  ))}
                  {Object.entries(pendingExtendFields).map(([fieldName, value]) => (
                    <Badge
                      key={`extend-${fieldName}`}
                      variant={hasPendingChanges ? "outline" : "secondary"}
                      className={`text-xs flex items-center gap-1 ${
                        hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                      }`}
                    >
                      ⚙️ {fieldName}: {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                      <X
                        className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto"
                        onClick={(e) => {
                          console.log('[FILTER-REMOVE] Clicking X for extend field badge:', fieldName)
                          e.stopPropagation()
                          e.preventDefault()
                          const newFields = { ...pendingExtendFields }
                          delete newFields[fieldName]
                          setPendingExtendFields(newFields)
                        }}
                      />
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Status message */}
            {hasActiveFilters && !hasPendingChanges && (
              <div className="p-2 bg-green-50 border border-green-200 rounded text-xs text-green-700">
                <strong>✓ Filters Applied:</strong> Analysis data is now filtered by selected categories.
              </div>
            )}
            {hasPendingChanges && (
              <div className="p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-700">
                <strong>⏳ Pending Changes:</strong> Click &quot;Apply Filters&quot; to update the analysis data.
              </div>
            )}
          </div>

          {/* Project Data Scope Section */}
          <div className="pt-3 border-t border-gray-100">
            {overviewLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
                <span className="text-sm text-gray-600">Loading project data...</span>
              </div>
            ) : projectData ? (
              <>
                {/* Statistics Cards - Compact layout */}
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



              </>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-red-600">
                  Failed to load project data. Please try again.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 