'use client'

import { useState, useEffect } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { ExtendFieldDefinition } from '../types/filters'

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
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </label>
            <Select
              key={selectKeys[field.field_name] || 0}
              onValueChange={(value) => {
                if (value === 'All' || value === String(field.filter_options.default)) {
                  handleFieldChange(field.field_name, undefined)
                } else {
                  handleFieldChange(field.field_name, value)
                }
              }}
              defaultValue="All"
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All</SelectItem>
                {/* 优先显示实际数据中的选项，并过滤已选择的项目 */}
                {projectData?.distributions?.extend_fields?.[field.field_name] ? (
                  projectData.distributions.extend_fields[field.field_name]
                    .filter(item => currentValue !== item.name)
                    .map((item) => (
                      <SelectItem key={item.name} value={item.name}>
                        {item.name} ({item.count} products)
                      </SelectItem>
                    ))
                ) : (
                  // Fallback: 如果没有实际数据，才使用定义中的选项（但不显示占比）
                  field.filter_options.options && Object.keys(field.filter_options.options)
                    .filter(option => currentValue !== option)
                    .map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))
                )}
              </SelectContent>
            </Select>
          </div>
        )

      case 'multi_select':
        // For multi-select, we'll use a simplified approach with multiple Select components
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </label>
            <Select
              key={selectKeys[field.field_name] || 0}
              onValueChange={(value) => {
                if (value === '' || value === 'all' || value === 'none') {
                  handleFieldChange(field.field_name, undefined)
                } else {
                  handleFieldChange(field.field_name, [value])
                }
              }}
              defaultValue="all"
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {field.filter_options.options && Object.keys(field.filter_options.options)
                  .filter(option => !currentValue || !currentValue.includes(option))
                  .map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        )

      case 'boolean':
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </label>
            <Select
              key={selectKeys[field.field_name] || 0}
              onValueChange={(value) => {
                let newValue: boolean | undefined
                if (value === 'true') {
                  newValue = true
                } else if (value === 'false') {
                  newValue = false
                } else {
                  newValue = undefined
                }
                handleFieldChange(field.field_name, newValue)
              }}
              defaultValue="all"
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {/* 过滤已选择的项目 */}
                {currentValue !== true && (
                  <SelectItem value="true">
                    {(() => {
                      const fieldDistribution = projectData?.distributions?.extend_fields?.[field.field_name]
                      const trueLabel = field.filter_options.true_label || 'Yes'
                      const distributionData = fieldDistribution?.find(item => item.name === trueLabel)
                      
                      return distributionData 
                        ? `${trueLabel} (${distributionData.count} products)`
                        : trueLabel
                    })()}
                  </SelectItem>
                )}
                {currentValue !== false && (
                  <SelectItem value="false">
                    {(() => {
                      const fieldDistribution = projectData?.distributions?.extend_fields?.[field.field_name]
                      const falseLabel = field.filter_options.false_label || 'No'
                      const distributionData = fieldDistribution?.find(item => item.name === falseLabel)
                      
                      return distributionData 
                        ? `${falseLabel} (${distributionData.count} products)`
                        : falseLabel
                    })()}
                  </SelectItem>
                )}
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