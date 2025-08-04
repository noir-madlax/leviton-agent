"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { RotateCcw, Loader2 } from "lucide-react"
import { ProjectFilters } from '../../types/filters'
import { CategoryFilter } from '../category-filter'
import { ExtendFieldsFilter } from '../extend-fields-filter'
import { useCommonT, useProjectT, useFiltersT } from '@/i18n/hooks'
import { useUnifiedFilter } from '../../contexts/unified-filter-context' // 🆕 从 context 获取数据

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
  
  // 🆕 从图表配置中提取可见性配置
  const visibleFilters = {
    categories: chartConfig?.filters.categories?.isVisible === true,
    brands: chartConfig?.filters.brands?.isVisible === true,
    segments: chartConfig?.filters.product_segments?.isVisible === true,
    extend_fields: chartConfig?.filters.extend_fields?.isVisible === true
  }
  
  // 🆕 从图表配置中提取扩展字段配置
  const filterConfig = chartConfig ? {
    visible_filters: {
      categories: chartConfig.filters.categories?.isVisible === true,
      brands: chartConfig.filters.brands?.isVisible === true,
      segments: chartConfig.filters.product_segments?.isVisible === true,
      extend_fields: chartConfig.filters.extend_fields?.isVisible === true
    },
    default_values: {},
    extend_fields: [] // TODO: 从 chartConfig 中提取扩展字段配置
  } : null
  
  console.log(`🔍 [FilterRenderer] Chart: ${chartName}, Config:`, {
    visibleFilters,
    hasChartConfig: !!chartConfig,
    contextLoading
  })
  const [pendingFilters, setPendingFilters] = useState<ProjectFilters>(currentFilters)
  const [applyingFilters, setApplyingFilters] = useState(false)

  // 国际化hooks
  const commonT = useCommonT()
  const projectT = useProjectT()
  const filtersT = useFiltersT()

  // 应用过滤器
  const handleApplyFilters = async () => {
    setApplyingFilters(true)
    
    // 模拟短暂延迟，让用户看到loading效果
    await new Promise(resolve => setTimeout(resolve, 10))
    
    onChange(pendingFilters)
    
    setApplyingFilters(false)
  }

  // 重置过滤器
  const handleReset = () => {
    const resetFilters = {
      categories: [],
      asins: [],
      brands: [],
      segments: [],
      extend_fields: {},
      time_period: "30 days"
    }
    setPendingFilters(resetFilters)
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
            onChange={(categories) => setPendingFilters(prev => ({ ...prev, categories }))}
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
            value={pendingFilters.extend_fields}
            onChange={(extendFields) => setPendingFilters(prev => ({ ...prev, extend_fields: extendFields }))}
            projectId={projectId}
            projectData={undefined} // 🆕 不传递 projectData，让组件内部处理
            filterConfig={filterConfig}
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
