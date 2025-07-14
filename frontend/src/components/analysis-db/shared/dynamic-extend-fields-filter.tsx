'use client'

import { useState, useEffect } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
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
}

export function DynamicExtendFieldsFilter({
  projectId,
  extendFields,
  onFilterChange,
  className = '',
  projectData
}: DynamicExtendFieldsFilterProps) {
  const [fieldDefinitions, setFieldDefinitions] = useState<ExtendFieldDefinition[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const loadExtendFields = async () => {
      if (!projectId) return
      
      setLoading(true)
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
        const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/extend-fields`)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const result = await response.json()
        setFieldDefinitions(result.extend_fields || [])
      } catch (error) {
        console.error('Error loading extend fields:', error)
        setFieldDefinitions([])
      } finally {
        setLoading(false)
      }
    }

    loadExtendFields()
  }, [projectId])

  const handleFieldChange = (fieldName: string, value: any) => {
    const newFilters = { ...extendFields, [fieldName]: value }
    onFilterChange(newFilters)
  }

  const renderFieldComponent = (field: ExtendFieldDefinition) => {
    const currentValue = extendFields[field.field_name]

    switch (field.field_type) {
      case 'select':
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <Label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </Label>
            <Select
              value={currentValue || String(field.filter_options.default || '')}
                              onValueChange={(value) => {
                  const finalValue = value === String(field.filter_options.default) ? undefined : value
                  handleFieldChange(field.field_name, finalValue)
                }}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder={field.filter_options.placeholder || field.display_name} />
              </SelectTrigger>
              <SelectContent>
                {field.filter_options.default && (
                  <SelectItem value={String(field.filter_options.default)}>
                    {String(field.filter_options.default)}
                  </SelectItem>
                )}
                {field.filter_options.options?.map((option) => {
                  // 从project data中查找对应的计数信息
                  const fieldDistribution = projectData?.distributions?.extend_fields?.[field.field_name]
                  const distributionData = fieldDistribution?.find(item => item.name === option)
                  
                  const displayLabel = distributionData 
                    ? `${option} (${distributionData.count} - ${distributionData.percentage}%)`
                    : option
                  
                  return (
                    <SelectItem key={option} value={option}>
                      {displayLabel}
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
          </div>
        )

      case 'multi_select':
        // For multi-select, we'll use a simplified approach with multiple Select components
        return (
          <div key={field.field_name} className="flex items-center gap-2">
            <Label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </Label>
            <Select
              value={currentValue?.[0] || ''}
              onValueChange={(value) => {
                const newValue = value ? [value] : []
                handleFieldChange(field.field_name, newValue.length > 0 ? newValue : undefined)
              }}
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder={field.filter_options.placeholder || field.display_name} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">None</SelectItem>
                {field.filter_options.options?.map((option) => (
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
            <Label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </Label>
            <Select
              value={currentValue === true ? 'true' : currentValue === false ? 'false' : 'all'}
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
            >
              <SelectTrigger className="w-48 h-8">
                <SelectValue placeholder={field.filter_options.placeholder || field.display_name} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="true">
                  {(() => {
                    const fieldDistribution = projectData?.distributions?.extend_fields?.[field.field_name]
                    const trueLabel = field.filter_options.true_label || 'Yes'
                    const distributionData = fieldDistribution?.find(item => item.name === trueLabel)
                    
                    return distributionData 
                      ? `${trueLabel} (${distributionData.count} - ${distributionData.percentage}%)`
                      : trueLabel
                  })()}
                </SelectItem>
                <SelectItem value="false">
                  {(() => {
                    const fieldDistribution = projectData?.distributions?.extend_fields?.[field.field_name]
                    const falseLabel = field.filter_options.false_label || 'No'
                    const distributionData = fieldDistribution?.find(item => item.name === falseLabel)
                    
                    return distributionData 
                      ? `${falseLabel} (${distributionData.count} - ${distributionData.percentage}%)`
                      : falseLabel
                  })()}
                </SelectItem>
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
            <Label className="text-sm text-gray-600 min-w-fit">
              {field.display_name}:
            </Label>
            <div className="flex items-center gap-2 w-48">
              <Slider
                value={currentRange}
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

  return (
    <div className={`flex flex-wrap gap-4 ${className}`}>
      {fieldDefinitions.map(field => renderFieldComponent(field))}
    </div>
  )
} 