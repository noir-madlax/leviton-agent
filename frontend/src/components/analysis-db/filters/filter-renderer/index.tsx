"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { RotateCcw, Loader2 } from "lucide-react"
import { ProjectFilters, FilterOptions } from '../../types/filters'
import { CategoryFilter } from '../category-filter'
import { ExtendFieldsFilter } from '../extend-fields-filter'
import { useCommonT, useProjectT, useFiltersT } from '@/i18n/hooks'

interface FilterRendererProps {
  // 数据和状态
  currentFilters: ProjectFilters
  onChange: (filters: ProjectFilters) => void
  availableOptions: FilterOptions
  
  // 上下文信息
  projectId: string
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
      packaging_types?: Array<{ name: string; count: number; percentage: number }>
      extend_fields?: Record<string, Array<{
        name: string
        count: number
        percentage: number
      }>>
    }
  }
  
  // 扩展字段配置
  filterConfig?: {
    visible_filters?: Record<string, boolean>
    default_values?: Record<string, string | boolean | number | string[] | number[]>
    extend_fields?: Array<{
      field_name: string
      display_name: string
      field_type: string
      filter_options: Record<string, string | boolean | number | string[] | number[]>
    }>
  } | null
  
  // UI状态
  loading?: boolean
  disabled?: boolean
  className?: string
  
  // 配置 - 暂时硬编码，后续会从 config 驱动
  visibleFilters?: {
    categories?: boolean
    brands?: boolean
    segments?: boolean
    extend_fields?: boolean
  }
}

export function FilterRenderer({
  currentFilters,
  onChange,
  availableOptions,
  projectId,
  projectData,
  filterConfig,
  loading = false,
  disabled = false,
  className = "",
  visibleFilters = { categories: true, extend_fields: true } // 默认显示 categories 和 extend_fields
}: FilterRendererProps) {
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
            availableOptions={availableOptions}
            projectData={projectData}
            disabled={disabled || loading}
            loading={loading}
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
            projectData={projectData}
            filterConfig={filterConfig}
            disabled={disabled || loading}
            loading={loading}
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
          disabled={disabled || loading}
          className="flex items-center gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          {filtersT('reset')}
        </Button>
        <Button 
          size="sm" 
          onClick={handleApplyFilters}
          disabled={!hasPendingChanges || disabled || loading || applyingFilters}
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
