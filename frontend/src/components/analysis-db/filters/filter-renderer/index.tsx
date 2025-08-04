"use client"

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { RotateCcw, Loader2 } from "lucide-react"
import { ProjectFilters } from '../../types/filters'
import { CategoryFilter } from '../category-filter'
import { ExtendFieldsFilter } from '../extend-fields-filter'
import { useCommonT, useProjectT, useFiltersT } from '@/i18n/hooks'
import { useUnifiedFilter } from '../../contexts/unified-filter-context' // 🆕 从 context 获取数据
import { useChartFilters } from '../../hooks/use-filter-state-manager' // 🆕 使用过滤器状态管理器

// 🆕 简化后的 FilterRenderer 接口 - 只需要最少参数
interface FilterRendererProps {
  // 🔥 核心参数
  projectId: string
  chartName: string  // 图表名称，用于从 context 获取配置
  currentFilters: ProjectFilters  // 当前过滤器值
  onChange: (filters: ProjectFilters) => void  // 变化回调
  
  // 🌟 可选参数
  disabled?: boolean
  className?: string
}

export function FilterRenderer({
  projectId,
  chartName,
  currentFilters,
  onChange,
  disabled = false,
  className = ""
}: FilterRendererProps) {
  // 🆕 从 context 获取统一过滤器数据
  const { getChartConfig, isLoading: contextLoading } = useUnifiedFilter()
  const chartConfig = getChartConfig(chartName)

  // 🔧 调试：输出图表配置信息
  console.log('🔧 [FILTER-RENDERER] Chart config debug:', {
    chartName,
    chartConfig,
    hasExtendFields: !!chartConfig?.filters.extend_fields,
    extendFieldsVisible: chartConfig?.filters.extend_fields?.isVisible,
    allFilters: chartConfig?.filters
  })

  // 🆕 从图表配置中提取可见性配置
  const visibleFilters = {
    categories: chartConfig?.filters.categories?.isVisible === true,
    brands: chartConfig?.filters.brands?.isVisible === true,
    segments: chartConfig?.filters.product_segments?.isVisible === true,
    // 🔧 修复：如果没有配置 extend_fields，默认显示为 true
    extend_fields: chartConfig?.filters.extend_fields?.isVisible !== false
  }

  // 🔧 调试：输出可见性配置
  console.log('🔧 [FILTER-RENDERER] Visible filters:', visibleFilters)

  // 移除了未使用的 filterConfig，ExtendFieldsFilter 现在自己获取配置

  console.log(`🔍 [FilterRenderer] Chart: ${chartName}, Config:`, {
    visibleFilters,
    hasChartConfig: !!chartConfig,
    contextLoading
  })

  // 🆕 使用过滤器状态管理器
  const {
    filters: chartFilters,
    updateCategories,
    updateExtendFields,
    resetFilters
  } = useChartFilters(chartName)

  const [pendingFilters, setPendingFilters] = useState<ProjectFilters>(currentFilters)
  const [applyingFilters, setApplyingFilters] = useState(false)
  // 🔧 新增：用于强制重置 ExtendFieldsFilter 的 key
  const [extendFieldsKey, setExtendFieldsKey] = useState(0)

  // 国际化hooks
  const commonT = useCommonT()
  const projectT = useProjectT()
  const filtersT = useFiltersT()

  // 🔄 同步状态管理器的变化到 pendingFilters
  useEffect(() => {
    if (chartFilters) {
      const newPendingFilters: ProjectFilters = {
        categories: chartFilters.filters.categories || [],
        asins: [],
        brands: chartFilters.filters.brands || [],
        segments: chartFilters.filters.segments || [],
        extend_fields: chartFilters.filters.extend_fields || {},
        time_period: chartFilters.timeframe?.period || "30 days"
      }

      console.log(`🔄 [FILTER-RENDERER] Syncing chart filters to pending filters for ${chartName}:`, newPendingFilters)
      setPendingFilters(newPendingFilters)
    }
  }, [chartFilters, chartName])

  // 应用过滤器
  const handleApplyFilters = async () => {
    setApplyingFilters(true)

    // 模拟短暂延迟，让用户看到loading效果
    await new Promise(resolve => setTimeout(resolve, 10))

    // 🆕 同时更新状态管理器和外部回调
    const chartState = {
      filters: {
        categories: pendingFilters.categories || [],
        brands: pendingFilters.brands || [],
        segments: pendingFilters.segments || [],
        extend_fields: pendingFilters.extend_fields || {}
      },
      timeframe: {
        period: pendingFilters.time_period || 'year'
      }
    }

    // 更新状态管理器
    updateCategories(chartState.filters.categories)
    updateExtendFields(chartState.filters.extend_fields)

    // 调用外部回调
    onChange(pendingFilters)

    setApplyingFilters(false)
  }

  // 重置过滤器
  const handleReset = () => {
    // 🆕 使用状态管理器的重置方法
    resetFilters()

    // 重置本地状态
    const resetFiltersData = {
      categories: [],
      asins: [],
      brands: [],
      segments: [],
      extend_fields: {},
      time_period: "30 days"
    }
    setPendingFilters(resetFiltersData)

    // 🔧 强制重置 ExtendFieldsFilter 组件
    setExtendFieldsKey(prev => prev + 1)
    console.log('🔧 [FILTER-RENDERER] Reset triggered, new extend fields key:', extendFieldsKey + 1)
  }

  // 检查是否有待处理的变化
  const hasPendingChanges = (
    JSON.stringify(pendingFilters.categories) !== JSON.stringify(currentFilters.categories) ||
    JSON.stringify(pendingFilters.brands) !== JSON.stringify(currentFilters.brands) ||
    JSON.stringify(pendingFilters.segments) !== JSON.stringify(currentFilters.segments) ||
    JSON.stringify(pendingFilters.extend_fields) !== JSON.stringify(currentFilters.extend_fields)
  )

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 过滤器标题 */}
      <h3 className="text-sm font-medium text-gray-700">{projectT('filters')}：</h3>
      
      {/* 第一行：基础过滤器控件 */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* Category Filter */}
        {visibleFilters?.categories && (
          <CategoryFilter
            value={pendingFilters.categories}
            onChange={(categories) => {
              setPendingFilters(prev => ({ ...prev, categories }))
              // 🆕 同时更新状态管理器
              updateCategories(categories)
            }}
            chartName={chartName} // 🆕 使用 chartName
            disabled={disabled || contextLoading} // 🆕 使用 context 的 loading 状态
            loading={contextLoading}
          />
        )}
        
        {/* 其他基础过滤器组件将在后续添加 */}
      </div>

      {/* 第二行：扩展字段过滤器（单独占用一行） */}
      {visibleFilters?.extend_fields && (
        <div className="w-full">
          <ExtendFieldsFilter
            key={extendFieldsKey} // 🔧 添加 key 属性，当 reset 时强制重新渲染
            onChange={(extendFields) => {
              setPendingFilters(prev => ({ ...prev, extend_fields: extendFields }))
              // 🆕 同时更新状态管理器
              updateExtendFields(extendFields)
            }}
            projectId={projectId}
            disabled={disabled || contextLoading}
            loading={contextLoading}
            className="w-full"
          />
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex justify-between items-center pt-2 border-t">
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handleReset}
          disabled={disabled || contextLoading} // 🆕 使用 context 的 loading 状态
          className="flex items-center gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          {filtersT('reset')}
        </Button>
        <Button 
          size="sm" 
          onClick={handleApplyFilters}
          disabled={!hasPendingChanges || disabled || contextLoading || applyingFilters} // 🆕 使用 context 的 loading 状态
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
    </div>
  )
}
