"use client"

import { useState, useEffect, useMemo } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useProjectT, useFiltersT, useT } from '@/i18n/hooks'
import { CategoryFilterProps } from '../common/types'
import { useUnifiedFilter } from '@/components/analysis-db/contexts/unified-filter-context'

export function CategoryFilter({
  value,
  onChange,
  chartName,  // 🆕 只需要图表名称
  disabled = false,
  loading = false,
  className = ""
}: CategoryFilterProps) {
  const projectT = useProjectT()
  const filtersT = useFiltersT()
  const t = useT()
  const [selectKey, setSelectKey] = useState(0)
  
  // 🆕 从 context 获取统一过滤器数据
  const { getChartConfig } = useUnifiedFilter()
  const chartConfig = getChartConfig(chartName)
  
  // 🆕 从图表配置中提取categories数据
  const availableOptions = {
    categories: Array.isArray(chartConfig?.filters.categories?.options) 
      ? chartConfig.filters.categories.options 
      : [],
    hierarchical_categories: [] // TODO: 如果需要层级结构，可以后续添加
  }
  
  // 🆕 从图表配置中获取默认值（使用useMemo避免不必要的重新计算）
  const defaultValues = useMemo(() => {
    return Array.isArray(chartConfig?.filters.categories?.values) 
      ? chartConfig.filters.categories.values 
      : []
  }, [chartConfig?.filters.categories?.values])
  
  console.log(`🔍 [CategoryFilter] Chart: ${chartName}`, {
    availableOptions: availableOptions.categories.length,
    defaultValuesCount: defaultValues.length,
    currentValue: value.length,
    defaultValues
  })
  
  // 🆕 在组件初始化时设置默认值（仅在首次渲染时）
  useEffect(() => {
    // 只有当前 value 为空且有默认值时才设置
    if (value.length === 0 && defaultValues.length > 0) {
      console.log(`🆕 [CategoryFilter] Setting default values for ${chartName}:`, defaultValues)
      onChange(defaultValues)
    }
  }, [chartName, value.length, defaultValues, onChange]) // 📝 使用useMemo后可以安全地包含defaultValues

  const handleCategorySelect = (category: string) => {
    // 实现多选逻辑：如果没有选中则添加，如果已选中则移除
    if (value.includes(category)) {
      // 取消选中
      onChange(value.filter(c => c !== category))
    } else {
      // 添加选中
      onChange([...value, category])
    }
    // 重置Select组件的选择状态
    setSelectKey(prev => prev + 1)
  }

  // 🆕 获取所有可用的分类选项（简化版）
  const getAllCategories = () => {
    // 直接使用从 context 获取的 categories options
    return availableOptions.categories.map(category => ({
      category,
      count: undefined // 暂时不显示产品数量，可以后续添加
    }))
  }

  const allCategories = getAllCategories()

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-sm text-gray-600">{projectT('amazonCategory')}:</span>
      <Select
        key={selectKey}
        value=""
        onValueChange={handleCategorySelect}
        disabled={disabled || loading}
      >
        <SelectTrigger className="w-64 h-8">
          <SelectValue placeholder={
            value.length > 0 
              ? t('filters.selectedItems', { count: value.length })
              : filtersT('selectOption')
          } />
        </SelectTrigger>
        <SelectContent>
          {allCategories.map(({ category, count }) => {
            const isSelected = value.includes(category)
            const displayLabel = count 
              ? `${category} (${count} ${projectT('products')})`
              : category
            
            return (
              <SelectItem key={category} value={category}>
                <div className="flex items-center gap-2">
                  {isSelected && <span className="text-green-600">✅</span>}
                  {displayLabel}
                </div>
              </SelectItem>
            )
          })}
        </SelectContent>
      </Select>
    </div>
  )
}