"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Filter, RotateCcw, X, Database, Users, MessageSquare, BarChart3, Loader2 } from "lucide-react"
import { databaseService } from '@/components/analysis-db/data/database-service'
import { DynamicExtendFieldsFilter } from './dynamic-extend-fields-filter'
import { PACKAGING_TYPE_OPTIONS, ProjectFilters } from '@/components/analysis-db/types/filters'

// 新增：过滤器配置接口
interface FilterConfig {
  visible_filters: Record<string, boolean>
  default_values: Record<string, any>
  extend_fields: Array<{
    field_name: string
    display_name: string
    field_type: string
    filter_options: Record<string, any>
  }>
}

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
  initialFilters = { categories: [], asins: [], brands: [], segments: [], extend_fields: {}, time_period: "30 days" },  // 改：packaging_types -> brands
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

  // 🔧 修复：追踪用户手动操作，避免被系统重置覆盖
  const userModifiedExtendFields = useRef<boolean>(false)
  
  // 🔧 包装用户的 extend_fields 操作
  const handleExtendFieldsChange = useCallback((newFields: Record<string, any>) => {
    userModifiedExtendFields.current = true
    console.log('🔧 [USER-OPERATION] User modified extend_fields:', newFields)
    setPendingExtendFields(newFields)
  }, [])
  
  const [pendingTimePeriod, setPendingTimePeriod] = useState<string>(initialFilters.time_period)
  const [appliedTimePeriod, setAppliedTimePeriod] = useState<string>(initialFilters.time_period)
  const [filterLoading, setFilterLoading] = useState(false)
  const [applyingFilters, setApplyingFilters] = useState(false)

  // 添加Select状态控制
  const [brandSelectKey, setBrandSelectKey] = useState(0)  // 改：packaging -> brand
  const [segmentSelectKey, setSegmentSelectKey] = useState(0)

  // Project overview states - 优先使用预加载数据
  const [projectData, setProjectData] = useState<ProjectOverviewData | null>(preloadedData || null)
  const [overviewLoading, setOverviewLoading] = useState(isDataLoading || false)

  // 新增：过滤器配置状态
  const [filterConfig, setFilterConfig] = useState<FilterConfig | null>(null)
  const [configLoading, setConfigLoading] = useState(false)

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

  // 新增：加载过滤器配置
  const loadFilterConfig = async () => {
    if (!projectId) return

    setConfigLoading(true)
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/filter-config`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      setFilterConfig(result.config)
      
      console.log('🔧 [FILTER-CONFIG] Loaded filter configuration:', result.config)
    } catch (error) {
      console.error('Error loading filter config:', error)
      // 如果加载失败，使用默认配置（显示所有过滤器）
      setFilterConfig({
        visible_filters: {
          'categories': true,
          'brands': true,
          'Time Period': true,
          'segments': true,
          'Smart Capability': true,
          'Package Type': true
        },
        default_values: {},
        extend_fields: []
      })
    } finally {
      setConfigLoading(false)
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

  // 监听initialFilters的变化，同步内部状态
  useEffect(() => {
    if (initialFilters) {
      setPendingCategories(initialFilters.categories || [])
      setAppliedCategories(initialFilters.categories || [])
      setPendingBrands(initialFilters.brands || [])
      setAppliedBrands(initialFilters.brands || [])
      setPendingSegments(initialFilters.segments || [])
      setAppliedSegments(initialFilters.segments || [])
      
      // 🔧 修复：只有在用户没有手动修改时才同步 extend_fields
      if (!userModifiedExtendFields.current) {
        console.log('🔧 [FILTER-SYNC] Syncing extend_fields from initialFilters (user has not modified)')
        setPendingExtendFields(initialFilters.extend_fields || {})
      } else {
        console.log('🔧 [FILTER-SYNC] Skipping extend_fields sync - user has modified')
      }
      
      setAppliedExtendFields(initialFilters.extend_fields || {})
      setPendingTimePeriod(initialFilters.time_period || "30 days")
      setAppliedTimePeriod(initialFilters.time_period || "30 days")
      
      console.log('🔄 [FILTER-SYNC] Synced initialFilters to component state:', initialFilters)
    }
  }, [initialFilters])

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
      setFilterConfig(null)
      if (!preloadedData) {
        setProjectData(null)
      }
      return
    }

    // 总是加载过滤器配置
    loadFilterConfig()

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
  }

  const handleCategoryToggle = (category: string, checked: boolean) => {
    if (checked) {
      if (!pendingCategories.includes(category)) {
        setPendingCategories(prev => [...prev, category])
      }
    } else {
      setPendingCategories(prev => prev.filter(c => c !== category))
    }
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

  const handleTimePeriodSelect = (timePeriod: string) => {
    console.log('[TIME-PERIOD] Selecting time period:', timePeriod)
    setPendingTimePeriod(timePeriod)
  }

  const handleApplyFilters = async () => {
    setApplyingFilters(true)
    
    // 先更新状态
    setAppliedCategories(pendingCategories)
    setAppliedBrands(pendingBrands)
    setAppliedSegments(pendingSegments)
    setAppliedExtendFields(pendingExtendFields)
    setAppliedTimePeriod(pendingTimePeriod)
    
    // 立即触发数据重新加载
    try {
      // 检查 projectId 是否为 null
      if (!projectId) {
        console.warn('ProjectId is null, skipping data reload')
        setApplyingFilters(false)
        return
      }
      
      const categoryFilters = pendingCategories.length > 0 ? pendingCategories : undefined
      const brandFilters = pendingBrands.length > 0 ? pendingBrands : undefined
      const segmentFilters = pendingSegments.length > 0 ? pendingSegments : undefined
      const extendFields = Object.keys(pendingExtendFields).length > 0 ? pendingExtendFields : undefined
      
      // 使用当前的pending值立即重新加载数据
      const overview = await databaseService.getProjectOverview(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
      
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
      console.error('Failed to reload project data:', error)
    }
    
    if (onFiltersChange) {
      onFiltersChange({
        categories: pendingCategories,
        asins: [],
        brands: pendingBrands,
        segments: pendingSegments,
        extend_fields: pendingExtendFields,
        time_period: pendingTimePeriod
      })
    }
    
    setApplyingFilters(false)
  }

  const handleReset = async () => {
    // 重置所有状态
    setPendingCategories([])
    setAppliedCategories([])
    setPendingBrands([])
    setAppliedBrands([])
    setPendingSegments([])
    setAppliedSegments([])
    setPendingExtendFields({})
    setAppliedExtendFields({})
    // 🔧 重置用户修改标志
    userModifiedExtendFields.current = false
    setPendingTimePeriod("30 days")
    setAppliedTimePeriod("30 days")
    
    // 重置所有Select组件状态
    setBrandSelectKey(prev => prev + 1)
    setSegmentSelectKey(prev => prev + 1)
    
    // 重新加载原始项目数据（不带任何筛选条件），确保Smart Capability等选项恢复到原始状态
    if (projectId) {
      try {
        const overview = await databaseService.getProjectOverview(projectId)
        
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
        console.log('🔄 [RESET] Reloaded original project data with all extend_fields options')
      } catch (error) {
        console.error('Failed to reload original project data during reset:', error)
      }
    }
    
    if (onFiltersChange) {
      onFiltersChange({
        categories: [],
        asins: [],
        brands: [],
        segments: [],
        extend_fields: {},
        time_period: "30 days"
      })
    }
  }

  const hasPendingChanges = JSON.stringify(pendingCategories) !== JSON.stringify(appliedCategories) || 
                          JSON.stringify(pendingBrands) !== JSON.stringify(appliedBrands) ||
                          JSON.stringify(pendingSegments) !== JSON.stringify(appliedSegments) ||
                          JSON.stringify(pendingExtendFields) !== JSON.stringify(appliedExtendFields) ||
                          pendingTimePeriod !== appliedTimePeriod
  const hasActiveFilters = appliedCategories.length > 0 || appliedBrands.length > 0 || appliedSegments.length > 0 || Object.keys(appliedExtendFields).length > 0 || appliedTimePeriod !== "30 days"

  // 🔧 实时监控pendingExtendFields状态变化
  console.log('🔧 [PENDING-EXTEND-FIELDS-MONITOR]', {
    pendingExtendFields,
    pendingExtendFieldsKeys: Object.keys(pendingExtendFields),
    pendingExtendFieldsLength: Object.keys(pendingExtendFields).length,
    hasPendingChanges,
    hasActiveFilters,
    shouldShowAppliedFilters: (
      pendingCategories.length > 0 || 
      pendingBrands.length > 0 || 
      pendingSegments.length > 0 || 
      Object.keys(pendingExtendFields).length > 0 || 
      pendingTimePeriod !== "30 days"
    )
  })

  if (!projectId) {
    return null
  }

  // 如果配置还在加载中，显示加载状态
  if (configLoading && !filterConfig) {
    return (
      <div className="mb-4">
        <Card className="border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Loading Filter Configuration...
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-gray-500">Loading project filters...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
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
              {filterConfig?.visible_filters?.categories && (
                <div className="flex flex-col gap-2">
                  <span className="text-sm text-gray-600">Amazon Category:</span>
                  <div className="flex items-center gap-4 flex-wrap">
                    {availableCategories.hierarchical_categories && 
                     availableCategories.hierarchical_categories.length > 0 && 
                     availableCategories.hierarchical_categories.some(group => group.children.length > 0) ? (
                      // 显示层次结构的复选框
                      availableCategories.hierarchical_categories.map((parentGroup) =>
                        parentGroup.children.map((child) => {
                          const isSelected = pendingCategories.includes(child.category)
                          return (
                            <div key={child.category} className="flex items-center gap-2">
                              <Checkbox
                                checked={isSelected}
                                onCheckedChange={(checked) => handleCategoryToggle(child.category, checked as boolean)}
                                disabled={filterLoading || configLoading}
                              />
                              <label className="text-sm cursor-pointer">
                                {child.category} ({child.count} - {child.percentage}%)
                              </label>
                            </div>
                          )
                        })
                      ).flat()
                    ) : (
                      // Fallback: 显示扁平分类结构的复选框
                      availableCategories.flat_categories.map(category => {
                        const isSelected = pendingCategories.includes(category)
                        return (
                          <div key={category} className="flex items-center gap-2">
                            <Checkbox
                              checked={isSelected}
                              onCheckedChange={(checked) => handleCategoryToggle(category, checked as boolean)}
                              disabled={filterLoading || configLoading}
                            />
                            <label className="text-sm cursor-pointer">
                              {category}
                            </label>
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              )}

              {/* Brand Filter */}
              {filterConfig?.visible_filters?.brands && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Brand:</span>
                  <Select key={brandSelectKey} onValueChange={handleBrandSelect} disabled={filterLoading || configLoading}>
                                        <SelectTrigger className="w-48 h-8">
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
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
              )}

              {/* Time Period Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Time Period:</span>
                <Select value={pendingTimePeriod} onValueChange={handleTimePeriodSelect}>
                  <SelectTrigger className="w-48 h-8">
                    <SelectValue placeholder="Select time period" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7 days">Last 7 days</SelectItem>
                    <SelectItem value="30 days">Last 30 days</SelectItem>
                    <SelectItem value="90 days">Last 90 days</SelectItem>
                    <SelectItem value="6 months">Last 6 months</SelectItem>
                    <SelectItem value="1 year">Last 1 year</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Segments Filter */}
              {filterConfig?.visible_filters?.segments && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Product Segment:</span>
                  <Select key={segmentSelectKey} onValueChange={handleSegmentSelect} disabled={filterLoading || configLoading}>
                                        <SelectTrigger className="w-48 h-8">
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
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
              )}

              {/* Extend Fields Filter */}
              <DynamicExtendFieldsFilter
                projectId={projectId}
                extendFields={pendingExtendFields}
                onFilterChange={handleExtendFieldsChange}
                className="flex-wrap"
                projectData={projectData}
                filterConfig={filterConfig}
              />

              {/* Apply button */}
              <Button
                onClick={handleApplyFilters}
                disabled={!hasPendingChanges || applyingFilters}
                size="sm"
                className="h-8"
              >
                {applyingFilters ? (
                  <>
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    Applying...
                  </>
                ) : (
                  'Apply Filters'
                )}
              </Button>

              {/* Reset button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                disabled={!hasActiveFilters && pendingCategories.length === 0 && pendingBrands.length === 0 && pendingSegments.length === 0 && Object.keys(pendingExtendFields).length === 0 && pendingTimePeriod === "30 days"}
                className="h-8"
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                Reset
              </Button>

              {/* Status indicator */}
              {hasPendingChanges && (
                <div className="text-xs text-orange-600">
                  {pendingCategories.length + pendingBrands.length + pendingSegments.length + Object.keys(pendingExtendFields).length + (pendingTimePeriod !== "30 days" ? 1 : 0)} pending changes
                </div>
              )}
              {hasActiveFilters && !hasPendingChanges && (
                <div className="text-xs text-green-600">
                  {appliedCategories.length + appliedBrands.length + appliedSegments.length + Object.keys(appliedExtendFields).length + (appliedTimePeriod !== "30 days" ? 1 : 0)} filter{(appliedCategories.length + appliedBrands.length + appliedSegments.length + Object.keys(appliedExtendFields).length + (appliedTimePeriod !== "30 days" ? 1 : 0)) > 1 ? 's' : ''} applied
                </div>
              )}
            </div>

            {/* Pending filters display */}
            {(() => {
              // 🔧 调试：检查显示条件的详细状态
              const showCondition = (
                pendingCategories.length > 0 || 
                pendingBrands.length > 0 || 
                pendingSegments.length > 0 || 
                Object.keys(pendingExtendFields).length > 0 || 
                pendingTimePeriod !== "30 days"
              )
              
              console.log('🔧 [APPLIED-FILTER-DISPLAY] Display condition check:', {
                pendingCategories: pendingCategories.length,
                pendingBrands: pendingBrands.length,
                pendingSegments: pendingSegments.length,
                pendingExtendFields: Object.keys(pendingExtendFields),
                pendingExtendFieldsLength: Object.keys(pendingExtendFields).length,
                pendingTimePeriod,
                showCondition
              })
              
              return showCondition
            })() && (
              <div className="pt-2 border-t border-gray-100">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-gray-600">
                    {hasPendingChanges ? 'Pending filters:' : 'Applied filters:'}
                  </span>
                  {/* Time Period filter badge (always show) */}
                  <Badge
                    key="time-period"
                    variant={hasPendingChanges ? "outline" : "secondary"}
                    className={`text-xs flex items-center gap-1 ${
                      hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                    }`}
                  >
                    ⏰ Time Period: Last 30 days
                  </Badge>
                  {pendingCategories.map((category) => (
                    <Badge
                      key={`category-${category}`}
                      variant={hasPendingChanges ? "outline" : "secondary"}
                      className={`text-xs flex items-center gap-1 ${
                        hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                      }`}
                    >
                      📁 {category}
                     
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
                       {brand}
                     
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
                     
                    </Badge>
                  ))}
                  {Object.entries(pendingExtendFields).map(([fieldName, value]) => {
                    // 如果是数组类型（多选），为每个值创建单独的Badge
                    if (Array.isArray(value)) {
                      return value.map((item, index) => (
                        <Badge
                          key={`extend-${fieldName}-${index}`}
                          variant={hasPendingChanges ? "outline" : "secondary"}
                          className={`text-xs flex items-center gap-1 ${
                            hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                          }`}
                        >
                          ⚙️ {fieldName === 'smart_capability' ? 'Smart Capability' : fieldName}: {item}
                        
                        </Badge>
                      ))
                    } else {
                      // 单个值的情况
                      return (
                        <Badge
                          key={`extend-${fieldName}`}
                          variant={hasPendingChanges ? "outline" : "secondary"}
                          className={`text-xs flex items-center gap-1 ${
                            hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                          }`}
                        >
                          ⚙️ {fieldName === 'smart_capability' ? 'Smart Capability' : fieldName}: {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                         
                        </Badge>
                      )
                    }
                  }).flat()}
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
            {(overviewLoading || applyingFilters) ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
                <span className="text-sm text-gray-600">
                  {applyingFilters ? 'Updating project data...' : 'Loading project data...'}
                </span>
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