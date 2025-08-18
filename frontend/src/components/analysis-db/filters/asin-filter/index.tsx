"use client"

import { useEffect, useMemo, useState } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useT } from '@/i18n/hooks'
import { BaseFilterProps } from '../common/types'
import { useUnifiedFilter } from '@/components/analysis-db/contexts/unified-filter-context'

interface AsinFilterProps extends BaseFilterProps {
  // 受控值：选中的 ASIN 列表
  value: string[]
  // 变化回调
  onChange: (asins: string[]) => void
  // 图表名称，用于从统一过滤配置中取 options/values
  chartName: string
}

/**
 * ASIN 多选组件（与 CategoryFilter 模式一致）
 * - 选项来源：chartConfig.filters.asins.options
 * - 默认值来源：chartConfig.filters.asins.values
 */
export function AsinFilter({ value, onChange, chartName, disabled = false, loading = false, className = "" }: AsinFilterProps) {
  const t = useT()
  const { getChartConfig } = useUnifiedFilter()
  const chartConfig = getChartConfig(chartName)

  // 可选 ASIN 列表
  const allAsins = useMemo<string[]>(() => {
    const opts = chartConfig?.filters?.asins?.options
    return Array.isArray(opts) ? (opts as string[]) : []
  }, [chartConfig?.filters?.asins?.options])

  // 默认选中值（初次渲染时应用）
  const defaultValues = useMemo<string[]>(() => {
    const vals = chartConfig?.filters?.asins?.values
    return Array.isArray(vals) ? (vals as string[]) : []
  }, [chartConfig?.filters?.asins?.values])

  useEffect(() => {
    if (value.length === 0 && defaultValues.length > 0) {
      onChange(defaultValues)
    }
  }, [value.length, defaultValues, onChange])

  const [selectKey, setSelectKey] = useState(0)

  const handleSelect = (asin: string) => {
    if (value.includes(asin)) {
      onChange(value.filter(a => a !== asin))
    } else {
      onChange([...value, asin])
    }
    setSelectKey(prev => prev + 1)
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-sm text-gray-600">ASIN:</span>
      <Select
        key={selectKey}
        value=""
        onValueChange={handleSelect}
        disabled={disabled || loading}
      >
        <SelectTrigger className="w-64 h-8">
          <SelectValue placeholder={
            value.length > 0
              ? t('filters.selectedItems', { count: value.length })
              : t('filters.selectOption')
          } />
        </SelectTrigger>
        <SelectContent>
          {allAsins.map(asin => {
            const isSelected = value.includes(asin)
            return (
              <SelectItem key={asin} value={asin}>
                <div className="flex items-center gap-2">
                  {isSelected && <span className="text-green-600">✅</span>}
                  <span className="font-mono text-xs">{asin}</span>
                </div>
              </SelectItem>
            )
          })}
        </SelectContent>
      </Select>
    </div>
  )
}

