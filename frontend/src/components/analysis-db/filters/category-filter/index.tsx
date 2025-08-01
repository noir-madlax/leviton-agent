"use client"

import { useState } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useProjectT } from '@/i18n/hooks'
import { CategoryFilterProps } from '../common/types'

export function CategoryFilter({
  value,
  onChange,
  availableOptions,
  projectData,
  disabled = false,
  loading = false,
  className = ""
}: CategoryFilterProps) {
  const projectT = useProjectT()
  const [selectKey, setSelectKey] = useState(0)

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

  // 获取所有可用的分类选项
  const getAllCategories = () => {
    let categories: Array<{ category: string; count?: number }> = []
    
    if (availableOptions.hierarchical_categories && 
        availableOptions.hierarchical_categories.length > 0 && 
        availableOptions.hierarchical_categories.some(group => group.children.length > 0)) {
      // 使用层次结构数据
      availableOptions.hierarchical_categories.forEach((parentGroup) => {
        parentGroup.children.forEach((child) => {
          categories.push({ category: child.category, count: child.count })
        })
      })
    } else {
      // 使用扁平分类结构
      categories = availableOptions.categories.map(category => {
        const distributionData = projectData?.distributions?.categories?.find(
          item => item.name === category
        )
        return { category, count: distributionData?.count }
      })
    }
    
    return categories
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
              ? `已选择 ${value.length} 个分类` 
              : "选择分类"
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