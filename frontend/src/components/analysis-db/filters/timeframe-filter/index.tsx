"use client"

import { useState, useEffect, useMemo } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useCommonT } from '@/i18n/hooks'
import { TimeframeFilterProps } from '../common/types'
import { useUnifiedFilter } from '@/components/analysis-db/contexts/unified-filter-context'

export function TimeframeFilter({
  value,
  onChange,
  chartName,
  disabled = false,
  loading = false,
  className = ""
}: TimeframeFilterProps) {
  const commonT = useCommonT()
  
  // 🆕 从 context 获取统一过滤器数据
  const { getChartConfig } = useUnifiedFilter()
  const chartConfig = getChartConfig(chartName)
  
  // 🆕 从图表配置中提取 time_period 数据
  const availableOptions = useMemo(() => {
    return Array.isArray(chartConfig?.filters.time_period?.options)
      ? chartConfig.filters.time_period.options
      : []
  }, [chartConfig?.filters.time_period?.options])

  // 🆕 从图表配置中获取默认值（不提供前端默认值）
  const defaultValue = useMemo(() => {
    const configValue = chartConfig?.filters.time_period?.values
    // 如果是字符串，直接返回；如果是数组，取第一个；否则返回空字符串
    if (typeof configValue === 'string') {
      return configValue
    } else if (Array.isArray(configValue) && configValue.length > 0) {
      return configValue[0]
    } else {
      return "" // 🔧 不提供前端默认值
    }
  }, [chartConfig?.filters.time_period?.values])
  
  console.log(`🔍 [TimeframeFilter] Chart: ${chartName}`, {
    availableOptions: availableOptions.length,
    defaultValue,
    currentValue: value,
    chartConfig: chartConfig?.filters.time_period
  })
  
  // 🆕 在组件初始化时设置默认值（仅在首次渲染时）
  useEffect(() => {
    // 只有当前 value 为空且有默认值时才设置
    if (!value && defaultValue) {
      console.log(`🆕 [TimeframeFilter] Setting default value for ${chartName}:`, defaultValue)
      onChange(defaultValue)
    }
  }, [chartName, value, defaultValue, onChange])

  const handleTimeframeSelect = (period: string) => {
    console.log(`🔄 [TimeframeFilter] Selected period for ${chartName}:`, period)
    onChange(period)
  }

  // 时间范围选项的显示标签映射
  const getTimeframeLabel = (period: string): string => {
    const labelMap: Record<string, string> = {
      'month': '最近1个月',
      '3months': '最近3个月',
      '6months': '最近6个月',
      'year': '最近1年',
      '2years': '最近2年',
      'all': '全部时间'
    }
    return labelMap[period] || period
  }

  // 🔧 只显示后端提供的选项，不提供前端默认选项
  const displayOptions = availableOptions

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-sm text-gray-600">时间范围:</span>
      <Select
        value={value || defaultValue}
        onValueChange={handleTimeframeSelect}
        disabled={disabled || loading}
      >
        <SelectTrigger className="w-40 h-8">
          <SelectValue placeholder="选择时间范围" />
        </SelectTrigger>
        <SelectContent>
          {displayOptions.map((period) => (
            <SelectItem key={period} value={period}>
              <div className="flex items-center gap-2">
                {value === period && <span className="text-green-600">✅</span>}
                {getTimeframeLabel(period)}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
