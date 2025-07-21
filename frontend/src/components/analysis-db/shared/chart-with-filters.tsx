"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Filter, ChevronUp, ChevronDown, BarChart3 } from "lucide-react"
import { ProjectFilters, DEFAULT_FILTERS } from '../types/filters'
import { UniversalFilterComponent } from './universal-filter-component'
import { useFilterState } from '../hooks/use-filter-state'
import { useFilterCache } from '../hooks/use-filter-cache'
import { useUnifiedFilterData } from '../hooks/use-unified-filter-data'

interface ChartFilterConfig {
  visible_filters: Record<string, boolean>
  default_values: Record<string, string[] | Record<string, string>>
  extend_fields: Array<{
    field_name: string
    display_name: string
    field_type: string
    filter_options: Record<string, string[] | string | boolean>
  }>
  chart_type: string
}

interface ChartWithFiltersProps {
  chartId: string
  projectId: string
  title: string
  children: React.ReactNode
  projectFilters?: ProjectFilters
  onFilterChange?: (filters: ProjectFilters) => void
  chartType?: string // eslint-disable-line @typescript-eslint/no-unused-vars
}

export function ChartWithFilters({ 
  chartId, 
  projectId, 
  title, 
  children,
  projectFilters,
  onFilterChange,
  chartType // eslint-disable-line @typescript-eslint/no-unused-vars
}: ChartWithFiltersProps) {
  const filterState = useFilterState(projectId, projectFilters)
  const [showFilters, setShowFilters] = useState(false)
  const [chartFilterConfig, setChartFilterConfig] = useState<ChartFilterConfig | null>(null)
  const [configLoading, setConfigLoading] = useState(true)
  const [defaultsApplied, setDefaultsApplied] = useState(false)
  
  // 使用统一数据源hook获取筛选器选项，fallback到原有缓存逻辑
  const { filterData: unifiedFilterData, isLoading: unifiedLoading } = useUnifiedFilterData(projectId)
  const { isLoading: cacheLoading, filterOptions: cachedOptions } = useFilterCache(projectId)
  
  // 优先使用统一数据源，fallback到原有缓存
  const filterOptions = unifiedFilterData || cachedOptions
  const dataLoading = unifiedLoading || cacheLoading

  // 加载chart专用筛选器配置
  useEffect(() => {
    const loadChartFilterConfig = async () => {
      if (!projectId || !chartId) return

      setConfigLoading(true)
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
        // 使用chartId而不是chartType，因为chartId对应数据库中的chart_name
        const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/charts/${chartId}/filter-config`)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const result = await response.json()
        setChartFilterConfig(result.config)
        
        console.log('🔧 [CHART-FILTER] Loaded chart filter configuration:', chartId, result.config)
      } catch (error) {
        console.error('Error loading chart filter config:', error)
        // 如果加载失败，使用空配置
        setChartFilterConfig({
          visible_filters: {},
          default_values: {},
          extend_fields: [],
          chart_type: chartId // 使用chartId作为chart_type
        })
      } finally {
        setConfigLoading(false)
      }
    }

    loadChartFilterConfig()
  }, [projectId, chartId])

  // 初始化chart筛选器
  useEffect(() => {
    filterState.initializeChartFilter(chartId)
  }, [chartId, filterState])

  // 应用chart配置的默认值和预载数据的默认值 - 移除filterState依赖，添加防重复应用标志
  useEffect(() => {
    if (!chartFilterConfig || configLoading || dataLoading || !filterOptions || defaultsApplied) return

    const defaultExtendFields: Record<string, string> = {}
    let hasDefaults = false

    // 处理配置的默认值
    const configuredDefaults = chartFilterConfig.default_values.extend_fields as Record<string, string> || {}
    Object.entries(configuredDefaults).forEach(([fieldName, value]) => {
      if (value && value !== 'all') {
        defaultExtendFields[fieldName] = value
        hasDefaults = true
      }
    })

    // 处理预载数据中boolean字段的默认值 (如Smart Capability)
    if (chartFilterConfig.extend_fields) {
      chartFilterConfig.extend_fields.forEach((fieldDef) => {
        const fieldName = fieldDef.field_name
        
        // 如果还没有设置默认值，且是boolean类型字段
        if (!defaultExtendFields[fieldName] && fieldDef.field_type === 'boolean') {
          const preloadedOptions = filterOptions.extend_fields?.[fieldName]
          if (preloadedOptions && preloadedOptions.length > 0) {
            // 使用第一个预载选项作为默认值
            defaultExtendFields[fieldName] = preloadedOptions[0]
            hasDefaults = true
          }
        }
      })
    }

    // 如果有默认值需要应用，更新chart filter
    if (hasDefaults) {
      const currentChartFilters = filterState.getChartFilters(chartId) || { ...DEFAULT_FILTERS }
      
      // 检查是否需要更新 - 避免不必要的状态更新
      const needsUpdate = Object.entries(defaultExtendFields).some(([key, value]) => 
        currentChartFilters.extend_fields[key] !== value
      )
      
      if (needsUpdate) {
        const updatedFilters = {
          ...currentChartFilters,
          extend_fields: {
            ...currentChartFilters.extend_fields,
            ...defaultExtendFields
          }
        }
        filterState.updateChartFilters(chartId, updatedFilters)
      }
      
      setDefaultsApplied(true)
    }
  }, [chartFilterConfig, configLoading, dataLoading, filterOptions, chartId, defaultsApplied]) // 移除filterState依赖

  const currentChartFilters = filterState.getChartFilters(chartId) || { ...DEFAULT_FILTERS }
  const finalFilters = filterState.getFinalFilters(chartId) || { ...DEFAULT_FILTERS }

  const handleChartFiltersChange = useCallback((newFilters: ProjectFilters) => {
    filterState.updateChartFilters(chartId, newFilters)
    onFilterChange?.(newFilters)
  }, [filterState, chartId, onFilterChange])

  // 处理单个筛选器变化
  const handleFilterChange = useCallback((filterType: 'categories' | 'brands' | 'segments', value: string) => {
    const newFilters = { ...currentChartFilters }
    
    if (value === 'all' || value === '') {
      // 清空该类型的筛选器
      newFilters[filterType] = []
    } else {
      // 设置单个值（替换现有的）
      newFilters[filterType] = [value]
    }
    
    handleChartFiltersChange(newFilters)
  }, [currentChartFilters, handleChartFiltersChange])

  // 处理extend_fields变化
  const handleExtendFieldChange = useCallback((fieldName: string, value: string) => {
    const newFilters = { ...currentChartFilters }
    const newExtendFields = { ...newFilters.extend_fields }
    
    if (value === '' || value === 'all') {
      delete newExtendFields[fieldName]
    } else {
      newExtendFields[fieldName] = value
    }
    
    newFilters.extend_fields = newExtendFields
    handleChartFiltersChange(newFilters)
  }, [currentChartFilters, handleChartFiltersChange])

  // 渲染inline筛选器选择框 - 使用useMemo优化性能
  const inlineFilters = useMemo(() => {
    if (configLoading || dataLoading || !chartFilterConfig || !filterOptions) {
      return null
    }

    const filters = []

    // Brand筛选器
    if (chartFilterConfig.visible_filters.brands && filterOptions.brands?.length > 0) {
      const currentValue = finalFilters.brands?.[0] || ''
      const brandsDefault = chartFilterConfig.default_values.brands as string[]
      const defaultValue = brandsDefault?.[0] || ''
      const displayValue = currentValue || defaultValue || 'all'
      
      filters.push(
        <div key="brands" className="flex flex-col items-end">
          <label className="text-xs text-gray-500 mb-1">Brand</label>
          <Select value={displayValue} onValueChange={(value) => handleFilterChange('brands', value)}>
            <SelectTrigger className="w-32 h-8 text-xs">
              <SelectValue placeholder="All Brands" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Brands</SelectItem>
              {filterOptions.brands.map((brand) => (
                <SelectItem key={brand} value={brand}>
                  {brand}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )
    }

    // Segments筛选器
    if (chartFilterConfig.visible_filters.segments && filterOptions.segments?.length > 0) {
      const currentValue = finalFilters.segments?.[0] || ''
      const segmentsDefault = chartFilterConfig.default_values.segments as string[]
      const defaultValue = segmentsDefault?.[0] || ''
      const displayValue = currentValue || defaultValue || 'all'
      
      filters.push(
        <div key="segments" className="flex flex-col items-end">
          <label className="text-xs text-gray-500 mb-1">Segment</label>
          <Select value={displayValue} onValueChange={(value) => handleFilterChange('segments', value)}>
            <SelectTrigger className="w-36 h-8 text-xs">
              <SelectValue placeholder="All Segments" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Segments</SelectItem>
              {filterOptions.segments.map((segment) => (
                <SelectItem key={segment} value={segment}>
                  {segment}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )
    }

    // Time Period筛选器
    if (chartFilterConfig.visible_filters.time_period) {
      const timeOptions = ['Last 30 days']
      const currentValue = finalFilters.extend_fields.time_period || ''
      const defaultValue = 'Last 30 days'
      const displayValue = currentValue || defaultValue
      
      filters.push(
        <div key="time_period" className="flex flex-col items-end">
          <label className="text-xs text-gray-500 mb-1">Time Period</label>
          <Select value={displayValue} onValueChange={(value) => handleExtendFieldChange('time_period', value)}>
            <SelectTrigger className="w-32 h-8 text-xs">
              <SelectValue placeholder="Last 30 days" />
            </SelectTrigger>
            <SelectContent>
              {timeOptions.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )
    }

    // Extend Fields筛选器（从配置的extend_fields中读取）
    if (chartFilterConfig.visible_filters.extend_fields && chartFilterConfig.extend_fields) {
      chartFilterConfig.extend_fields.forEach((fieldDef) => {
        const fieldName = fieldDef.field_name
        const displayName = fieldDef.display_name
        
        // 检查该字段是否有可用的数据选项 - 关键修复！
        const preloadedOptions = filterOptions?.extend_fields?.[fieldName]
        let hasValidOptions = false
        
        if (fieldDef.field_type === 'boolean') {
          // boolean类型：检查是否有预载数据，或者允许使用默认的boolean值
          hasValidOptions = (preloadedOptions && preloadedOptions.length > 0) || true
        } else {
          // select类型：必须有预载数据选项才显示
          hasValidOptions = preloadedOptions && preloadedOptions.length > 0
        }
        
        // 如果该字段没有可用选项，跳过不显示
        if (!hasValidOptions) {
          return
        }
        
        // 从chart配置的default_values中获取默认值
        const configuredDefaultValues = chartFilterConfig.default_values.extend_fields as Record<string, string> || {}
        const currentValue = finalFilters.extend_fields[fieldName] || ''
        
        // 优先级：当前值 > chart配置默认值 > field定义默认值 > 'all'
        let defaultValue = configuredDefaultValues[fieldName] || String(fieldDef.filter_options?.default || 'all')
        
        // 如果没有当前值且没有配置默认值，对于boolean类型尝试从预载的filterOptions获取默认值
        if (!currentValue && !configuredDefaultValues[fieldName] && fieldDef.field_type === 'boolean') {
          // 对于Smart Capability等boolean字段，如果预载数据中有值，使用第一个值作为默认值
          if (preloadedOptions && preloadedOptions.length > 0) {
            defaultValue = preloadedOptions[0]
          }
        }
        
        const displayValue = currentValue || defaultValue || 'all'

        if (fieldDef.field_type === 'select' || fieldDef.field_type === 'boolean') {
          let options: string[] = []
          
          if (fieldDef.field_type === 'boolean') {
            // 沿用Project Filter的逻辑：优先使用统一数据源的extend_fields数据
            if (preloadedOptions && preloadedOptions.length > 0) {
              options = preloadedOptions
            } else {
              // 如果统一数据源没有数据，使用默认的boolean值
              options = ['true', 'false']
            }
          } else {
            // 优先使用统一数据源的extend_fields数据，如果没有则fallback到chart配置
            const filterValues = preloadedOptions || fieldDef.filter_options?.values
            const rawOptions = Array.isArray(filterValues) ? filterValues : []
            
            // 对package_type字段进行特殊处理：合并Multiple选项
            if (fieldName === 'package_type') {
              const processedOptions: string[] = []
              let hasMultiple = false
              
              rawOptions.forEach(option => {
                if (option.startsWith('Multiple-')) {
                  if (!hasMultiple) {
                    processedOptions.push('Multiple')
                    hasMultiple = true
                  }
                } else {
                  processedOptions.push(option)
                }
              })
              
              options = processedOptions
            } else {
              options = rawOptions
            }
          }
          
          filters.push(
            <div key={fieldName} className="flex flex-col items-end">
              <label className="text-xs text-gray-500 mb-1">{displayName}</label>
              <Select 
                value={displayValue} 
                onValueChange={(value) => handleExtendFieldChange(fieldName, value)}
              >
                <SelectTrigger className="w-32 h-8 text-xs">
                  <SelectValue placeholder={`All ${displayName}`} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All {displayName}</SelectItem>
                  {options.map((option) => (
                    <SelectItem key={option} value={option}>
                      {fieldName === 'smart_capability' 
                        ? (option === 'Smart' ? 'Smart' : 
                           option === 'Non-Smart' ? 'Non-Smart' : 
                           option === 'true' ? 'Smart' : 
                           option === 'false' ? 'Non-Smart' : 
                           option)
                        : option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )
        }
      })
    }

    return filters.reverse() // 从右向左排列
  }, [chartFilterConfig, configLoading, dataLoading, filterOptions, finalFilters, handleFilterChange, handleExtendFieldChange])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          {title}
        </h3>
        <div className="flex items-center gap-2 hidden">
          {/* 保留原有的详细筛选器按钮 */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            disabled={dataLoading || configLoading}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            {(dataLoading || configLoading) ? 'Loading...' : 'More Filters'}
            {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Inline筛选器 - 放在按钮下方一行 */}
      <div className="flex items-center justify-end gap-3 hidden">
        {inlineFilters}
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