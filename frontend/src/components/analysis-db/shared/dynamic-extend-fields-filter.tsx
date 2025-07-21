'use client'

import { useState, useEffect } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { ExtendFieldDefinition } from '../types/filters'
import { useUnifiedFilterData } from '../hooks/use-unified-filter-data'

interface DynamicExtendFieldsFilterProps {
  projectId: string
  extendFields: Record<string, any>
  onFilterChange: (filters: Record<string, any>) => void
  className?: string
  projectData?: {
    distributions: {
      extend_fields: Record<string, Array<{
        name: string
        count: number
        percentage: number
      }>>
    }
  } | null
  // 新增：过滤器配置，用于控制显示哪些扩展字段
  filterConfig?: {
    visible_filters: Record<string, boolean>
    default_values: Record<string, any>
    extend_fields: Array<{
      field_name: string
      display_name: string
      field_type: string
      filter_options: Record<string, any>
    }>
  } | null
}

export function DynamicExtendFieldsFilter({
  projectId,
  extendFields,
  onFilterChange,
  className = '',
  projectData,
  filterConfig
}: DynamicExtendFieldsFilterProps) {
  const [fieldDefinitions, setFieldDefinitions] = useState<ExtendFieldDefinition[]>([])
  const [loading, setLoading] = useState(false)
  const [selectKeys, setSelectKeys] = useState<Record<string, number>>({})

  // 使用统一筛选器数据源获取原始extend_fields选项（不受当前筛选条件影响）
  const { filterData: unifiedFilterData, isLoading: unifiedLoading } = useUnifiedFilterData(projectId)

  useEffect(() => {
    const loadExtendFields = async () => {
      if (!projectId) return
      
      // 如果有过滤器配置，优先使用配置中的extend_fields
      if (filterConfig?.extend_fields) {
        const fields = filterConfig.extend_fields.map(field => ({
          ...field,
          sort_order: 1, // 添加必需的 sort_order 字段
          field_type: field.field_type as 'boolean' | 'select' | 'multi_select' | 'range'
        })) as ExtendFieldDefinition[]
        setFieldDefinitions(fields)
        
        // 初始化selectKeys
        const initialKeys: Record<string, number> = {}
        fields.forEach((field: any) => {
          initialKeys[field.field_name] = 0
        })
        setSelectKeys(initialKeys)
        
        console.log('🔧 [EXTEND-FIELDS] Using filterConfig extend_fields:', fields.map(f => f.field_name))
        return
      }
      
      // Fallback: 从API获取
      setLoading(true)
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
        
        console.log('🔧 [EXTEND-FIELDS] Loaded from API:', fields.map((f: any) => f.field_name))
      } catch (error) {
        console.error('Error loading extend fields:', error)
        setFieldDefinitions([])
      } finally {
        setLoading(false)
      }
    }

    loadExtendFields()
  }, [projectId, filterConfig])

  const handleFieldChange = (fieldName: string, value: string | boolean | number | string[] | number[] | undefined) => {
    const newFilters = { ...extendFields }
    
    if (value === undefined || value === null || value === '') {
      delete newFilters[fieldName]
    } else {
      newFilters[fieldName] = value
    }
    
    onFilterChange(newFilters)
    
    // 重置选择器
    setSelectKeys(prev => ({ ...prev, [fieldName]: prev[fieldName] + 1 }))
  }

  const renderFieldComponent = (field: ExtendFieldDefinition) => {
    const currentValue = extendFields[field.field_name]

    switch (field.field_type) {
      case 'select':
        // Select类型支持多选（和Amazon Category一样的逻辑）
        const selectCurrentValue = Array.isArray(currentValue) ? currentValue : (
          typeof currentValue === 'string' ? [currentValue] :
          currentValue ? [String(currentValue)] :
          []
        )
        
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </label>
            <Select
              key={selectKeys[field.field_name] || 0}
              value=""
              onValueChange={(value) => {
                // 实现和Amazon Category一样的多选逻辑
                let newValue: string[]
                if (!selectCurrentValue.includes(value)) {
                  newValue = [...selectCurrentValue, value]
                  console.log(`✅ [${field.field_name.toUpperCase()}] Multi-select working! Added "${value}" to array:`, newValue)
                } else {
                  return // 如果已经选中了，不做任何操作
                }
                
                handleFieldChange(field.field_name, newValue.length > 0 ? newValue : undefined)
              }}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                {/* 优先使用统一数据源中的原始选项（不受当前筛选条件影响），并尝试获取count信息 */}
                {(() => {
                  // 获取稳定的选项列表（从统一数据源）
                  const stableOptions = unifiedFilterData?.extend_fields?.[field.field_name] || []
                  
                  if (stableOptions.length > 0) {
                    return stableOptions.map((optionName) => {
                      const isSelected = selectCurrentValue.includes(optionName)
                      
                      // 尝试从projectData获取count信息（如果可用）
                      const countInfo = projectData?.distributions?.extend_fields?.[field.field_name]?.find(
                        (item: any) => item.name === optionName
                      )
                      
                      const displayLabel = countInfo 
                        ? `${optionName} (${countInfo.count} products)`
                        : optionName
                      
                      return (
                        <SelectItem key={optionName} value={optionName} disabled={isSelected}>
                          <div className="flex items-center gap-2">
                            {isSelected && <span className="text-green-600">✅</span>}
                            {displayLabel}
                          </div>
                        </SelectItem>
                      )
                    })
                  }
                  
                  // Fallback: 如果统一数据源没有数据，使用定义中的选项
                  if (field.filter_options.options) {
                    return Object.keys(field.filter_options.options).map((option) => {
                      const isSelected = selectCurrentValue.includes(option)
                      return (
                        <SelectItem key={option} value={option} disabled={isSelected}>
                          <div className="flex items-center gap-2">
                            {isSelected && <span className="text-green-600">✅</span>}
                            {option}
                          </div>
                        </SelectItem>
                      )
                    })
                  }
                  
                  return null
                })()}
              </SelectContent>
            </Select>
          </div>
        )

      case 'multi_select':
        // Multi-select类型支持多选（和Amazon Category一样的逻辑）
        const multiSelectValues = Array.isArray(currentValue) ? currentValue : (
          typeof currentValue === 'string' ? [currentValue] :
          currentValue ? [String(currentValue)] :
          []
        )
        
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </label>
            <Select
              key={selectKeys[field.field_name] || 0}
              value=""
              onValueChange={(value) => {
                // 实现和Amazon Category一样的多选逻辑
                let newValue: string[]
                if (!multiSelectValues.includes(value)) {
                  newValue = [...multiSelectValues, value]
                  console.log(`✅ [${field.field_name.toUpperCase()}] Multi-select working! Added "${value}" to array:`, newValue)
                } else {
                  return // 如果已经选中了，不做任何操作
                }
                
                handleFieldChange(field.field_name, newValue.length > 0 ? newValue : undefined)
              }}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                {field.filter_options.options && Object.keys(field.filter_options.options)
                  .map((option) => {
                    const isSelected = multiSelectValues.includes(option)
                    return (
                      <SelectItem key={option} value={option} disabled={isSelected}>
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
        // 将boolean类型按select类型处理，支持多选（和Amazon Category一样的逻辑）
        const booleanSelectValues = Array.isArray(currentValue) ? currentValue : (
          typeof currentValue === 'string' ? [currentValue] :
          currentValue ? [String(currentValue)] :
          []
        )
        
        // 获取所有可用选项（从统一数据源中获取，不受当前筛选条件影响）
        const stableOptions = unifiedFilterData?.extend_fields?.[field.field_name] || []
        
        // 构建可用选项列表，尝试包含count信息
        let availableOptions = stableOptions.map(optionName => {
          // 尝试从projectData获取count信息（如果可用）
          const countInfo = projectData?.distributions?.extend_fields?.[field.field_name]?.find(
            (item: any) => item.name === optionName
          )
          
          return {
            name: optionName,
            count: countInfo?.count || 0
          }
        })
        
        // 如果统一数据源也没有数据，fallback到projectData
        if (availableOptions.length === 0) {
          availableOptions = projectData?.distributions?.extend_fields?.[field.field_name] || []
        }
        
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </label>
            <Select
              key={selectKeys[field.field_name] || 0}
              value=""
              onValueChange={(value) => {
                // 实现和Amazon Category一样的多选逻辑
                let newValue: string[]
                if (!booleanSelectValues.includes(value)) {
                  newValue = [...booleanSelectValues, value]
                  console.log(`✅ [${field.field_name.toUpperCase()}] Multi-select working! Added "${value}" to array:`, newValue)
                } else {
                  return // 如果已经选中了，不做任何操作
                }
                
                handleFieldChange(field.field_name, newValue.length > 0 ? newValue : undefined)
              }}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                {availableOptions.map((item) => {
                  const isSelected = booleanSelectValues.includes(item.name)
                  return (
                    <SelectItem key={item.name} value={item.name} disabled={isSelected}>
                      <div className="flex items-center gap-2">
                        {isSelected && <span className="text-green-600">✅</span>}
                        {item.name} ({item.count} products)
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
              {field.display_name}:
            </label>
            <div className="flex items-center gap-2 w-48">
              <Slider
                value={currentRange as number[]}
                onValueChange={(value) => {
                  const newValue = value[0] === min && value[1] === max ? undefined : value
                  handleFieldChange(field.field_name, newValue)
                }}
                min={min}
                max={max}
                step={step}
                className="flex-1"
              />
              <span className="text-xs text-gray-500 min-w-fit">
                {currentRange[0]} - {currentRange[1]}
              </span>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className={`text-sm text-gray-500 ${className}`}>
        Loading extend fields...
      </div>
    )
  }

  if (fieldDefinitions.length === 0) {
    return null
  }

  // 根据filterConfig.visible_filters过滤要显示的字段
  const visibleFields = fieldDefinitions.filter(field => {
    // 如果没有filterConfig或visible_filters，显示所有字段（向后兼容）
    if (!filterConfig?.visible_filters) {
      return true
    }
    
    // 检查字段是否在visible_filters中被标记为true
    const fieldVisible = filterConfig.visible_filters[field.display_name] || 
                        filterConfig.visible_filters[field.field_name]
    
    console.log(`🔧 [DYNAMIC-EXTEND] Field visibility check:`, {
      field_name: field.field_name,
      display_name: field.display_name,
      visible: fieldVisible,
      visible_filters: filterConfig.visible_filters
    })
    
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