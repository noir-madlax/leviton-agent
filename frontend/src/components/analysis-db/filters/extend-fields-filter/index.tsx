"use client"

import { useState, useEffect, useMemo } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { useCommonT, useProjectT, useFiltersT, useT } from '@/i18n/hooks'
import { ExtendFieldDefinition, ExtendFieldsFilterProps, ExtendFieldValue } from './types'
import { useExtendFieldsData, registerExtendFieldsRerenderCallback } from './hooks/useExtendFieldsData'
import { useUnifiedFilter } from '../../contexts/unified-filter-context'

export function ExtendFieldsFilter({
  onChange,
  projectId,
  chartName,
  loading = false,
  disabled = false,
  className = ""
}: ExtendFieldsFilterProps) {
  const [selectKeys, setSelectKeys] = useState<Record<string, number>>({})
  const [currentValues, setCurrentValues] = useState<Record<string, ExtendFieldValue>>({})

  // 国际化hooks
  const commonT = useCommonT()
  const projectT = useProjectT()
  const filtersT = useFiltersT()
  const t = useT()

  // 翻译字段显示名称
  const translateFieldName = (displayName: string) => {
    switch (displayName) {
      case 'Smart Capability':
        return projectT('smartCapability')
      default:
        return displayName
    }
  }

  // 使用新的 hook 获取 extend fields 数据，确保只调用一次接口
  const { fieldDefinitions, projectData, loading: fieldsLoading, error } = useExtendFieldsData(projectId)

  // 🆕 获取配置
  const { getChartConfig, triggerExtendFieldsRerender } = useUnifiedFilter()
  const chartConfig = getChartConfig(chartName)
  const extendFieldsConfig = chartConfig?.filters?.extend_fields

  // 🆕 注册重渲染回调
  useEffect(() => {
    console.log(`🔄 [EXTEND-FIELDS] Registering rerender callback for chart: ${chartName}`)
    const unregister = registerExtendFieldsRerenderCallback(() => {
      console.log(`🔄 [EXTEND-FIELDS] Received rerender signal for chart: ${chartName}, triggering context rerender`)
      triggerExtendFieldsRerender()
    })

    return () => {
      console.log(`🔄 [EXTEND-FIELDS] Unregistering rerender callback for chart: ${chartName}`)
      unregister()
    }
  }, [triggerExtendFieldsRerender, chartName])

  // 🆕 根据配置过滤要显示的字段
  const visibleFields = useMemo(() => {
    if (!fieldDefinitions.length) return []

    // 获取配置中允许显示的字段名列表
    let allowedFieldNames: string[] = []

    if (extendFieldsConfig?.options) {
      // 如果统一过滤器有配置，使用它
      allowedFieldNames = extendFieldsConfig.options as string[] || []
      console.log('🔧 [EXTEND-FIELDS] Using unified filter config:', allowedFieldNames)
    } 

    // 如果仍然没有配置或不是数组，返回空数组
    if (!Array.isArray(allowedFieldNames)) {
      console.warn('🔧 [EXTEND-FIELDS] allowedFieldNames is not an array:', typeof allowedFieldNames, allowedFieldNames)
      return []
    }

    if (allowedFieldNames.length === 0) {
      // 如果没有配置，则不显示任何字段
      return []
    }

    // 过滤出配置中指定的字段，保持原有排序
    return fieldDefinitions.filter(field =>
      allowedFieldNames.includes(field.field_name)
    ).sort((a, b) => a.sort_order - b.sort_order)
  }, [fieldDefinitions, extendFieldsConfig?.options])

  // 调试日志
  console.log('🔧 [EXTEND-FIELDS] Component render:', {
    chartName,
    projectId,
    fieldDefinitionsCount: fieldDefinitions.length,
    configuredFields: extendFieldsConfig?.options || [],
    visibleFieldsCount: visibleFields.length,
    visibleFields: visibleFields.map(f => f.field_name),
    fieldsLoading,
    error,
    currentValuesCount: Object.keys(currentValues).length,
    hasProjectData: !!projectData,
    hasConfig: !!extendFieldsConfig
  })

  // 初始化 selectKeys - 基于可见字段
  useEffect(() => {
    if (visibleFields.length > 0) {
      const initialKeys: Record<string, number> = {}
      visibleFields.forEach((field) => {
        initialKeys[field.field_name] = 0
      })
      setSelectKeys(initialKeys)
    }
  }, [visibleFields])

  // 初始化默认值 - 基于可见字段，分离到独立的 useEffect 避免循环依赖
  useEffect(() => {
    if (visibleFields.length > 0 && Object.keys(currentValues).length === 0) {
      console.log('🔧 [EXTEND-FIELDS] Initializing default selections for visible fields (all options selected)')
      const defaultSelections: Record<string, ExtendFieldValue> = {}

      visibleFields.forEach(field => {
        if (field.field_type === 'select' || field.field_type === 'multi_select' || field.field_type === 'boolean') {
          // 获取所有可用选项
          const availableOptions = getAvailableOptions(field)
          if (availableOptions.length > 0) {
            defaultSelections[field.field_name] = availableOptions.map(option => option.name)
          }
        } else if (field.field_type === 'range') {
          // 对于范围类型，使用最大范围
          const min = field.filter_options.min || 0
          const max = field.filter_options.max || 100
          defaultSelections[field.field_name] = [min, max]
        }
      })

      if (Object.keys(defaultSelections).length > 0) {
        setCurrentValues(defaultSelections)
        onChange(defaultSelections)
      }
    }
  }, [visibleFields, projectData]) // 依赖 visibleFields 和 projectData

  // 获取字段的可用选项
  const getAvailableOptions = (field: ExtendFieldDefinition) => {
    let availableOptions: Array<{ name: string; count: number }> = []

    // 优先使用定义中的选项（按照API返回的顺序）
    if (field.filter_options.options) {
      availableOptions = Object.keys(field.filter_options.options).map(option => {
        const countInfo = projectData?.distributions?.extend_fields?.[field.field_name]?.find(
          (item: any) => item.name === option
        )

        return {
          name: option,
          count: countInfo?.count || 0
        }
      })
    }

    // 如果定义中没有选项，fallback到projectData
    if (availableOptions.length === 0) {
      const projectDataOptions = projectData?.distributions?.extend_fields?.[field.field_name] || []
      availableOptions = projectDataOptions.map((item: any) => ({
        name: item.name,
        count: item.count || 0
      }))
    }

    return availableOptions
  }

  const handleFieldChange = (fieldName: string, newValue: ExtendFieldValue) => {
    const newFilters = { ...currentValues }

    if (newValue === undefined || newValue === null || newValue === '') {
      delete newFilters[fieldName]
    } else {
      newFilters[fieldName] = newValue
    }

    console.log('🔧 [EXTEND-FIELDS] Field change:', {
      fieldName,
      value: newValue,
      oldFilters: currentValues,
      newFilters,
      hasKeys: Object.keys(newFilters).length > 0
    })

    setCurrentValues(newFilters)
    onChange(newFilters)

    // 重置选择器
    setSelectKeys(prev => ({ ...prev, [fieldName]: prev[fieldName] + 1 }))
  }

  const renderFieldComponent = (field: ExtendFieldDefinition) => {
    const currentValue = currentValues[field.field_name]

    switch (field.field_type) {
      case 'select':
        // Select类型改为下拉框形式
        let selectCurrentValue: string[] = []
        if (Array.isArray(currentValue)) {
          selectCurrentValue = currentValue.map(v => String(v))
        } else if (typeof currentValue === 'string') {
          selectCurrentValue = [currentValue]
        } else if (currentValue) {
          selectCurrentValue = [String(currentValue)]
        }
        
        // 获取可用选项列表
        const availableSelectOptions = getAvailableOptions(field)
        
        const handleSelectChange = (optionName: string) => {
          if (selectCurrentValue.includes(optionName)) {
            // 取消选中
            const newValue = selectCurrentValue.filter(v => v !== optionName)
            handleFieldChange(field.field_name, newValue.length > 0 ? newValue : undefined)
          } else {
            // 添加选中
            const newValue = [...selectCurrentValue, optionName]
            handleFieldChange(field.field_name, newValue)
          }
        }
        
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <span className="text-sm text-gray-600">{translateFieldName(field.display_name)}:</span>
            <Select
              key={selectKeys[field.field_name] || 0}
              value=""
              onValueChange={handleSelectChange}
              disabled={disabled || loading || fieldsLoading}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder={
                  selectCurrentValue.length > 0 
                    ? t('filters.selectedItems', { count: selectCurrentValue.length })
                    : filtersT('selectOption')
                } />
              </SelectTrigger>
              <SelectContent>
                {availableSelectOptions.map((item) => {
                  const isSelected = selectCurrentValue.includes(item.name)
                  const displayLabel = item.count > 0 
                    ? `${item.name} (${item.count})`
                    : item.name
                  
                  return (
                    <SelectItem key={item.name} value={item.name}>
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

      case 'multi_select':
        // Multi-select类型支持多选
        let multiSelectValues: string[] = []
        if (Array.isArray(currentValue)) {
          multiSelectValues = currentValue.map(v => String(v))
        } else if (typeof currentValue === 'string') {
          multiSelectValues = [currentValue]
        } else if (currentValue) {
          multiSelectValues = [String(currentValue)]
        }
        
        const handleMultiSelectChange = (newValue: string) => {
          if (multiSelectValues.includes(newValue)) {
            // 取消选中
            const updatedValues = multiSelectValues.filter(v => v !== newValue)
            handleFieldChange(field.field_name, updatedValues.length > 0 ? updatedValues : undefined)
          } else {
            // 添加选中
            const updatedValues = [...multiSelectValues, newValue]
            handleFieldChange(field.field_name, updatedValues)
          }
        }
        
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <span className="text-sm text-gray-600">{translateFieldName(field.display_name)}:</span>
            <Select
              key={selectKeys[field.field_name] || 0}
              value=""
              onValueChange={handleMultiSelectChange}
              disabled={disabled || loading || fieldsLoading}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder={
                  multiSelectValues.length > 0 
                    ? `已选择 ${multiSelectValues.length} 项`
                    : "选择选项"
                } />
              </SelectTrigger>
              <SelectContent>
                {field.filter_options.options && Object.keys(field.filter_options.options)
                  .map((option) => {
                    const isSelected = multiSelectValues.includes(option)
                    return (
                      <SelectItem key={option} value={option}>
                        <div className="flex items-center gap-2">
                          {isSelected && <span className="text-green-600">✅</span>}
                          {option}
                        </div>
                      </SelectItem>
                    )
                  })}
              </SelectContent>
            </Select>
          </div>
        )

      case 'boolean':
        // Boolean类型改为下拉框形式
        let booleanSelectValues: string[] = []
        if (Array.isArray(currentValue)) {
          booleanSelectValues = currentValue.map(v => String(v))
        } else if (typeof currentValue === 'string') {
          booleanSelectValues = [currentValue]
        } else if (currentValue) {
          booleanSelectValues = [String(currentValue)]
        }
        
        // 获取所有可用选项
        const availableOptions = getAvailableOptions(field)
        
        const handleBooleanChange = (optionName: string) => {
          if (booleanSelectValues.includes(optionName)) {
            // 取消选中
            const newValue = booleanSelectValues.filter(v => v !== optionName)
            handleFieldChange(field.field_name, newValue.length > 0 ? newValue : undefined)
          } else {
            // 添加选中
            const newValue = [...booleanSelectValues, optionName]
            handleFieldChange(field.field_name, newValue)
          }
        }
        
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <span className="text-sm text-gray-600">{translateFieldName(field.display_name)}:</span>
            <Select
              key={selectKeys[field.field_name] || 0}
              value=""
              onValueChange={handleBooleanChange}
              disabled={disabled || loading || fieldsLoading}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder={
                  booleanSelectValues.length > 0 
                    ? `已选择 ${booleanSelectValues.length} 项` 
                    : "选择选项"
                } />
              </SelectTrigger>
              <SelectContent>
                {availableOptions.map((item) => {
                  const isSelected = booleanSelectValues.includes(item.name)
                  const displayLabel = item.count > 0 
                    ? `${item.name} (${item.count})`
                    : item.name
                  
                  return (
                    <SelectItem key={item.name} value={item.name}>
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

      case 'range':
        const min = field.filter_options.min || 0
        const max = field.filter_options.max || 100
        const step = field.filter_options.step || 1
        const currentRange = currentValue || [min, max]

        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <label className="text-sm text-gray-600 min-w-fit">
              {translateFieldName(field.display_name)}:
            </label>
            <div className="flex items-center gap-2 w-48">
              <Slider
                value={currentRange as number[]}
                onValueChange={(sliderValue) => {
                  const newValue = sliderValue[0] === min && sliderValue[1] === max ? undefined : sliderValue
                  handleFieldChange(field.field_name, newValue)
                }}
                min={min}
                max={max}
                step={step}
                className="flex-1"
                disabled={disabled || loading || fieldsLoading}
              />
              <span className="text-xs text-gray-500 min-w-fit">
                {(currentRange as number[])[0]} - {(currentRange as number[])[1]}
              </span>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  if (fieldsLoading) {
    return (
      <div className={`text-sm text-gray-500 ${className}`}>
        {commonT('loading')}
      </div>
    )
  }

  if (error) {
    return (
      <div className={`text-sm text-red-500 ${className}`}>
        {error}
      </div>
    )
  }

  if (fieldDefinitions.length === 0) {
    return null
  }

  console.log('🔧 [EXTEND-FIELDS] Final rendering fields:', {
    chartName,
    fieldDefinitions: fieldDefinitions.length,
    visibleFields: visibleFields.length,
    fields: visibleFields.map(f => f.field_name)
  })

  if (visibleFields.length === 0) {
    return null
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}>
      {visibleFields.map(field => renderFieldComponent(field))}
    </div>
  )
}
