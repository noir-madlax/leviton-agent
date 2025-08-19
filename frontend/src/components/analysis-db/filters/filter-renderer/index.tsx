"use client"

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"
import { ProjectFilters } from '../../types/filters'
import { CategoryFilter } from '../category-filter'
import { AsinFilter } from '../asin-filter'

import { TimeframeFilter } from '../timeframe-filter'
import { ExtendFieldsFilter } from '../extend-fields-filter'
import { useCommonT, useFiltersT } from '@/i18n/hooks'
import { useUnifiedFilter } from '../../contexts/unified-filter-context' // 🆕 从 context 获取数据
import { useChartFilters } from '../../hooks/use-filter-state-manager' // 🆕 使用过滤器状态管理器
import { filterStateManager } from '../../stores' // 🆕 导入状态管理器
import { CHART_NAMES } from '../../constants' // 🆕 导入图表名称常量

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
  // 🆕 过滤器就绪状态回调
  onFiltersReady?: (isReady: boolean) => void
}

export function FilterRenderer({
  projectId,
  chartName,
  currentFilters,
  onChange,
  disabled = false,
  className = "",
  onFiltersReady
}: FilterRendererProps) {
  // 🆕 从 context 获取统一过滤器数据
  const { getChartConfig, isLoading: contextLoading, extendFieldsVersion } = useUnifiedFilter()
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
    asins: chartConfig?.filters.asins?.isVisible === true,
    brands: chartConfig?.filters.brands?.isVisible === true,
    segments: chartConfig?.filters.product_segments?.isVisible === true,
    timeframe: chartConfig?.filters.time_period?.isVisible === true,
    // 🔧 修复：如果没有配置 extend_fields，默认不显示（仅当 isVisible === true 时显示）
    extend_fields: chartConfig?.filters.extend_fields?.isVisible === true
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
    updateTimeframe,
    resetFilters,
    updateFilter
  } = useChartFilters(chartName)

  const [pendingFilters, setPendingFilters] = useState<ProjectFilters>(currentFilters)
  const [applyingFilters, setApplyingFilters] = useState(false)
  // 🔧 新增：用于强制重置 ExtendFieldsFilter 的 key
  const [extendFieldsKey, setExtendFieldsKey] = useState(0)
  // 🆕 过滤器就绪状态
  const [filtersReady, setFiltersReady] = useState(false)

  // 🆕 检测是否为项目级过滤器
  const isProjectFilter = chartName === CHART_NAMES.PROJECT

  // 国际化hooks
  const commonT = useCommonT()
  const filtersT = useFiltersT()

  // 🔄 同步 currentFilters 的变化到 pendingFilters（优先级最高）
  useEffect(() => {
    console.log(`🔄 [FILTER-RENDERER] Syncing currentFilters to pendingFilters for ${chartName}:`, currentFilters)
    setPendingFilters(currentFilters)
  }, [currentFilters, chartName])

  // 🔄 同步状态管理器的变化到 pendingFilters（仅在没有 currentFilters 时使用）
  useEffect(() => {
    if (
      chartFilters &&
      !currentFilters.time_period &&
      (!currentFilters.categories || currentFilters.categories.length === 0) &&
      (!currentFilters.asins || currentFilters.asins.length === 0) &&
      (!currentFilters.brands || currentFilters.brands.length === 0) &&
      (!currentFilters.segments || currentFilters.segments.length === 0)
    ) {
      const newPendingFilters: ProjectFilters = {
        categories: chartFilters.filters.categories || [],
        asins: (chartFilters as any).selected_asins || [],
        brands: chartFilters.filters.brands || [],
        segments: chartFilters.filters.segments || [],
        extend_fields: chartFilters.filters.extend_fields || {},
        time_period: chartFilters.timeframe?.period || "" // 🔧 不设置前端默认值
      }

      // 避免无差异更新导致的重复渲染
      const isSame = JSON.stringify(newPendingFilters) === JSON.stringify(pendingFilters)
      if (!isSame) {
        console.log(`🔄 [FILTER-RENDERER] Syncing chart filters to pending filters for ${chartName}:`, newPendingFilters)
        setPendingFilters(newPendingFilters)
      }
    }
  }, [chartFilters, chartName, currentFilters, pendingFilters])

  // 🆕 监听 extend-fields 版本变化，触发重渲染
  useEffect(() => {
    if (extendFieldsVersion > 0) {
      console.log(`🔄 [FILTER-RENDERER] ExtendFields version changed for ${chartName}, triggering rerender:`, extendFieldsVersion)
      setExtendFieldsKey(prev => prev + 1)
    }
  }, [extendFieldsVersion, chartName])

  // 🆕 检测过滤器是否就绪 - 简化版本
  useEffect(() => {
    const checkFiltersReady = () => {
      // 简化的检查条件：
      // 1. context 数据已加载
      // 2. 图表配置可能不存在（无配置也应视为就绪）
      // 3. 如果需要扩展字段且有值或默认值，则就绪；否则在无配置或不需要扩展字段时也就绪
      const isContextReady = !contextLoading
      const hasChartConfig = !!chartConfig
      const noConfig = !chartConfig

      // 🔧 简化的扩展字段检查逻辑
      const hasExtendFields = visibleFilters?.extend_fields ?
        (
          // 方案1：状态管理器中已有扩展字段值
          (chartFilters?.filters.extend_fields && Object.keys(chartFilters.filters.extend_fields).length > 0) ||
          // 方案2：图表配置中有默认的扩展字段值（避免竞态条件）
          (chartConfig?.filters.extend_fields?.values && Object.keys(chartConfig.filters.extend_fields.values).length > 0) ||
          // 方案3：如果以上都没有，但图表配置存在，也认为就绪（让数据加载流程继续）
          !!chartConfig
        ) :
        true // 如果不需要扩展字段，则认为已就绪

      // 无配置时，只要 context 加载完成即就绪；有配置时遵循扩展字段的就绪规则
      const isReady = Boolean(isContextReady && (noConfig || hasExtendFields))

      console.log(`🔍 [FILTER-RENDERER] Checking filters ready for ${chartName}:`, {
        isContextReady,
        hasChartConfig,
        noConfig,
        hasExtendFields,
        chartConfigExtendFields: chartConfig?.filters.extend_fields?.values,
        chartFiltersExtendFields: chartFilters?.filters.extend_fields,
        isReady,
        previousState: filtersReady
      })

      if (isReady !== filtersReady) {
        setFiltersReady(isReady)
        onFiltersReady?.(isReady)
        console.log(`🎯 [FILTER-RENDERER] Filters ready state changed for ${chartName}: ${filtersReady} → ${isReady}`)
      }
    }

    checkFiltersReady()
  }, [contextLoading, chartConfig, chartFilters, visibleFilters, chartName, filtersReady, onFiltersReady])

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
      // 🆕 将 ASIN 选择存入 selected_asins（与 filters 平级）
      selected_asins: (pendingFilters.asins as string[] | undefined) || [],
      timeframe: {
        period: pendingFilters.time_period || ''
      },
      metadata: {
        lastUpdated: Date.now(),
        appliedAt: Date.now()
      }
    }

    // 更新状态管理器
    updateCategories(chartState.filters.categories)
    updateExtendFields(chartState.filters.extend_fields)
    updateTimeframe(chartState.timeframe)

    // 🆕 项目级过滤器的特殊处理
    if (isProjectFilter) {
      console.log('🌍 [FILTER-RENDERER] Project filter detected, syncing to all charts')

      // 同步到所有其他图表
      filterStateManager.syncProjectFiltersToAllCharts(chartState)

      // 触发全局刷新信号
      triggerGlobalRefresh()
    }

    // 调用外部回调
    onChange(pendingFilters)

    setApplyingFilters(false)
  }

  // 🆕 触发全局刷新
  const triggerGlobalRefresh = () => {
    console.log('🚀 [FILTER-RENDERER] Triggering global refresh')
    // 通过重置和重新设置就绪状态来触发所有图表刷新
    onFiltersReady?.(false)
    setTimeout(() => {
      onFiltersReady?.(true)
    }, 100)
  }

  // 重置过滤器
  const handleReset = () => {
    // 先重置状态管理器
    resetFilters()

    // 从图表配置读取默认 ASIN（filter_values）
    const defaultAsins: string[] = Array.isArray(chartConfig?.filters?.asins?.values)
      ? (chartConfig!.filters!.asins!.values as string[])
      : []

    // 重置本地 pendingFilters，ASIN 回到默认值，其它保持清空策略（与原逻辑一致）
    const resetFiltersData = {
      categories: [],
      asins: defaultAsins,
      brands: [],
      segments: [],
      extend_fields: {},
      time_period: "" // 🔧 重置时不设置前端默认值
    }
    setPendingFilters(resetFiltersData)

    // 同步默认 ASIN 到状态管理器（selected_asins 与 filters 平级）
    updateFilter('selected_asins', defaultAsins)

    // 🔧 强制重置 ExtendFieldsFilter 组件
    setExtendFieldsKey(prev => prev + 1)
    console.log('🔧 [FILTER-RENDERER] Reset triggered (ASIN restored to defaults), new key:', extendFieldsKey + 1)
  }

  // 检查是否有待处理的变化
  const hasPendingChanges = (
    JSON.stringify(pendingFilters.categories) !== JSON.stringify(currentFilters.categories) ||
    JSON.stringify(pendingFilters.asins) !== JSON.stringify(currentFilters.asins) ||
    JSON.stringify(pendingFilters.brands) !== JSON.stringify(currentFilters.brands) ||
    JSON.stringify(pendingFilters.segments) !== JSON.stringify(currentFilters.segments) ||
    JSON.stringify(pendingFilters.extend_fields) !== JSON.stringify(currentFilters.extend_fields) ||
    pendingFilters.time_period !== currentFilters.time_period
  )

  return (
    <div className={`space-y-2 ${className}`}> {/* FILTER_STACK_GAP: reduce vertical gap between filter blocks */}
      {/* 过滤器标题和操作按钮 */}
      <div className="flex justify-between items-center ">
        <h3 className="text-sm font-medium text-gray-700">{projectT('filters')}：</h3>
        <div className="flex items-center gap-2">
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

      {/* 第一行：基础过滤器控件 */}
      <div className="flex items-center gap-2 flex-wrap "> {/* FILTER_ROW_GAP: tighten inline filter controls spacing */}
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


          {/* Timeframe Filter */}
          {visibleFilters?.timeframe && (
            <TimeframeFilter
              value={pendingFilters.time_period || ""}
              onChange={(period) => {
                setPendingFilters(prev => ({ ...prev, time_period: period }))
                // 🆕 同时更新状态管理器
                updateTimeframe({ period })
              }}
              chartName={chartName}
              disabled={disabled || contextLoading}
              loading={contextLoading}
            />
          )}

          {/* 其他基础过滤器组件将在后续添加 */}
        </div>
        <div className="ml-auto"> {/* Right: Apply button */}
          <Button
            size="sm"
            onClick={handleApplyFilters}
            disabled={!hasPendingChanges || disabled || contextLoading || applyingFilters}
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

      {/* 第二行：扩展字段过滤器（单独占用一行） */}
      {visibleFilters?.extend_fields && (
        <div className="w-full pt-1"> {/* compact spacing */}
          <ExtendFieldsFilter
            key={extendFieldsKey} // 🔧 添加 key 属性，当 reset 时强制重新渲染
            chartName={chartName} // 🆕 传递 chartName
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

      {/* ASIN Filter */}
      {visibleFilters?.asins && (
        <AsinFilter
          value={pendingFilters.asins}
          onChange={(asins) => {
            // 与其他组件一致：先写入 pendingFilters，再同步状态管理器
            setPendingFilters(prev => ({ ...prev, asins }))
            updateFilter('selected_asins', asins)
          }}
          chartName={chartName}
          disabled={disabled || contextLoading}
          loading={contextLoading}
        />
      )}

    </div>
  )
}
