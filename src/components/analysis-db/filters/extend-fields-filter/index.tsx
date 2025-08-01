"use client"

import { useState, useEffect } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Checkbox } from '@/components/ui/checkbox'
import { useUnifiedFilterData } from '../../hooks/use-unified-filter-data'
import { useCommonT, useProjectT } from '@/i18n/hooks'
import { ExtendFieldDefinition, ExtendFieldsFilterProps, ExtendFieldValue } from './types'

export function ExtendFieldsFilter({
  value,
  onChange,
  projectId,
  projectData,
  filterConfig,
  loading = false,
  disabled = false,
  className = ""
}: ExtendFieldsFilterProps) {
  const [fieldDefinitions, setFieldDefinitions] = useState<ExtendFieldDefinition[]>([])
  const [internalLoading, setInternalLoading] = useState(false)
  const [selectKeys, setSelectKeys] = useState<Record<string, number>>({})

  // 国际化hooks
  const commonT = useCommonT()
  const projectT = useProjectT()
  
  // 翻译字段显示名称
  const translateFieldName = (displayName: string) => {
    switch (displayName) {
      case 'Smart Capability':
        return projectT('smartCapability')
      default:
        return displayName
    }
  }

  // 使用统一筛选器数据源获取原始extend_fields选项
  const { filterData: unifiedFilterData } = useUnifiedFilterData(projectId)

  useEffect(() => {
    const loadExtendFields = async () => {
      if (!projectId) return
      
      // 如果有过滤器配置，优先使用配置中的extend_fields
      if (filterConfig?.extend_fields) {
        const fields = filterConfig.extend_fields.map(field => ({
          ...field,
          sort_order: 1,
          field_type: field.field_type as 'boolean' | 'select' | 'multi_select' | 'range'
        })) as ExtendFieldDefinition[]
        setFieldDefinitions(fields)
        
        // 初始化selectKeys
        const initialKeys: Record<string, number> = {}
        fields.forEach((field) => {
          initialKeys[field.field_name] = 0
        })
        setSelectKeys(initialKeys)
        
        console.log('🔧 [EXTEND-FIELDS] Using filterConfig extend_fields:', fields.map(f => f.field_name))
        return
      }
      
      // Fallback: 从API获取
      setInternalLoading(true)
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
        const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/extend-fields`)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const result = await response.json()
        const fields = result.extend_fields || []
        setFieldDefinitions(fields)
        
        // 初始化selectKeys
        const initialKeys: Record<string, number> = {}
        fields.forEach((field: ExtendFieldDefinition) => {
          initialKeys[field.field_name] = 0
        })
        setSelectKeys(initialKeys)
        
        console.log('🔧 [EXTEND-FIELDS] Loaded from API:', fields.map((f: ExtendFieldDefinition) => f.field_name))
      } catch (error) {
        console.error('Error loading extend fields:', error)
        setFieldDefinitions([])
      } finally {
        setInternalLoading(false)
      }
    }

    loadExtendFields()
  }, [projectId, filterConfig])

  const handleFieldChange = (fieldName: string, newValue: ExtendFieldValue) => {
    const newFilters = { ...value }
    
    if (newValue === undefined || newValue === null || newValue === '') {
      delete newFilters[fieldName]
    } else {
      newFilters[fieldName] = newValue
    }
    
    console.log('🔧 [EXTEND-FIELDS] Field change:', {
      fieldName,
      value: newValue,
      oldFilters: value,
      newFilters,
      hasKeys: Object.keys(newFilters).length > 0
    })
    
    onChange(newFilters)
    
    // 重置选择器
    setSelectKeys(prev => ({ ...prev, [fieldName]: prev[fieldName] + 1 }))
  }

  const renderFieldComponent = (field: ExtendFieldDefinition) => {
    const currentValue = value[field.field_name]

    switch (field.field_type) {
      case 'select':
        // Select类型改为复选框形式
        let selectCurrentValue: string[] = []
        if (Array.isArray(currentValue)) {
          selectCurrentValue = currentValue.map(v => String(v))
        } else if (typeof currentValue === 'string') {
          selectCurrentValue = [currentValue]
        } else if (currentValue) {
          selectCurrentValue = [String(currentValue)]
        }
        
        // 获取可用选项列表，优先使用统一数据源
        const selectStableOptions = unifiedFilterData?.extend_fields?.[field.field_name] || []
        let availableSelectOptions: Array<{ name: string; count: number }> = selectStableOptions.map(optionName => {
          const countInfo = projectData?.distributions?.extend_fields?.[field.field_name]?.find(
            (item) => item.name === optionName
          )
          
          return {
            name: optionName,
            count: countInfo?.count || 0
          }
        })
        
        // 如果统一数据源没有数据，fallback到定义中的选项
        if (availableSelectOptions.length === 0 && field.filter_options.options) {
          availableSelectOptions = Object.keys(field.filter_options.options).map(option => ({
            name: option,
            count: 0
          }))
        }
        
        // 最后fallback到projectData
        if (availableSelectOptions.length === 0) {
          availableSelectOptions = projectData?.distributions?.extend_fields?.[field.field_name] || []
        }
        
        return (
          <div key={field.field_name} className="flex flex-col gap-2">
            <label className="text-sm text-gray-600">
              {translateFieldName(field.display_name)}:
            </label>
            <div className="flex items-center gap-4 flex-wrap">
              {(availableSelectOptions as Array<{ name: string; count: number }>).map((item) => {
                const isSelected = selectCurrentValue.includes(item.name)
                return (
                  <div key={item.name} className="flex items-center gap-2">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={(checked) => {
                        let newValue: string[]
                        if (checked && !selectCurrentValue.includes(item.name)) {
                          newValue = [...selectCurrentValue, item.name]
                        } else if (!checked) {
                          newValue = selectCurrentValue.filter(v => v !== item.name)
                        } else {
                          return
                        }
                        handleFieldChange(field.field_name, newValue.length > 0 ? newValue : undefined)
                      }}
                      disabled={disabled || loading || internalLoading}
                    />
                    <label className="text-sm cursor-pointer">
                      {item.name}
                    </label>
                  </div>
                )
              })}
            </div>
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
        
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <label className="text-sm text-gray-600 min-w-fit">
              {translateFieldName(field.display_name)}:
            </label>
            <Select
              key={selectKeys[field.field_name] || 0}
              value=""
              onValueChange={(newValue) => {
                if (multiSelectValues.includes(newValue)) {
                  // 取消选中
                  const updatedValues = multiSelectValues.filter(v => v !== newValue)
                  handleFieldChange(field.field_name, updatedValues.length > 0 ? updatedValues : undefined)
                } else {
                  // 添加选中
                  const updatedValues = [...multiSelectValues, newValue]
                  handleFieldChange(field.field_name, updatedValues)
                }
              }}
              disabled={disabled || loading || internalLoading}
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
        // Boolean类型按select类型处理
        let booleanSelectValues: string[] = []
        if (Array.isArray(currentValue)) {
          booleanSelectValues = currentValue.map(v => String(v))
        } else if (typeof currentValue === 'string') {
          booleanSelectValues = [currentValue]
        } else if (currentValue) {
          booleanSelectValues = [String(currentValue)]
        }
        
        // 获取所有可用选项
        const stableOptions = unifiedFilterData?.extend_fields?.[field.field_name] || []
        
        let availableOptions: Array<{ name: string; count: number }> = stableOptions.map(optionName => {
          const countInfo = projectData?.distributions?.extend_fields?.[field.field_name]?.find(
            (item) => item.name === optionName
          )
          
          return {
            name: optionName,
            count: countInfo?.count || 0
          }
        })
        
        // Fallback到projectData
        if (availableOptions.length === 0) {
          availableOptions = projectData?.distributions?.extend_fields?.[field.field_name] || []
        }
        
        return (
          <div key={field.field_name} className="flex flex-col gap-2">
            <label className="text-sm text-gray-600">
              {translateFieldName(field.display_name)}:
            </label>
            <div className="flex items-center gap-4 flex-wrap">
              {(availableOptions as Array<{ name: string; count: number }>).map((item) => {
                const isSelected = booleanSelectValues.includes(item.name)
                return (
                  <div key={item.name} className="flex items-center gap-2">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={(checked) => {
                        let newValue: string[]
                        if (checked && !booleanSelectValues.includes(item.name)) {
                          newValue = [...booleanSelectValues, item.name]
                        } else if (!checked) {
                          newValue = booleanSelectValues.filter(v => v !== item.name)
                        } else {
                          return
                        }
                        handleFieldChange(field.field_name, newValue.length > 0 ? newValue : undefined)
                      }}
                      disabled={disabled || loading || internalLoading}
                    />
                    <label className="text-sm cursor-pointer">
                      {item.name}
                    </label>
                  </div>
                )
              })}
            </div>
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
                disabled={disabled || loading || internalLoading}
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

  if (internalLoading) {
    return (
      <div className={`text-sm text-gray-500 ${className}`}>
        {commonT('loading')}
      </div>
    )
  }

  if (fieldDefinitions.length === 0) {
    return null
  }

  // 根据filterConfig.visible_filters过滤要显示的字段
  const visibleFields = fieldDefinitions.filter(field => {
    // 如果没有filterConfig或visible_filters，显示所有字段
    if (!filterConfig?.visible_filters) {
      return true
    }
    
    // 检查字段是否在visible_filters中被标记为true
    const fieldVisible = filterConfig.visible_filters[field.display_name] || 
                        filterConfig.visible_filters[field.field_name]
    
    return fieldVisible === true
  })

  if (visibleFields.length === 0) {
    return null
  }

  return (
    <div className={`flex flex-wrap gap-4 ${className}`}>
      {visibleFields.map(field => renderFieldComponent(field))}
    </div>
  )
}