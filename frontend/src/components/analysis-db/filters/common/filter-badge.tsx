"use client"

import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"
import { ProjectFilters } from '../../types/filters'

interface FilterBadgeProps {
  filterType: keyof ProjectFilters
  value: string
  onRemove: () => void
  fromProject?: boolean
  className?: string
}

export function FilterBadge({
  filterType,
  value,
  onRemove,
  fromProject = false,
  className = ""
}: FilterBadgeProps) {
  // 添加对应的图标前缀和筛选器类型标识
  const getPrefix = (filterType: keyof ProjectFilters) => {
    switch (filterType) {
      case 'categories': return '📁 Amazon Category:'
      case 'brands': return '🏢 Brand:'  
      case 'segments': return '🎯 Product Segment:'
      default: return ''
    }
  }

  return (
    <Badge
      variant={fromProject ? "secondary" : "default"}
      className={`text-xs flex items-center gap-1 mr-2 mb-2 ${
        fromProject ? 'bg-blue-100 text-blue-800 border-blue-300' : ''
      } ${className}`}
    >
      {fromProject && <span className="mr-1">📌</span>}
      {getPrefix(filterType)} {value}
      <X 
        className="w-3 h-3 hidden cursor-pointer hover:text-red-500 pointer-events-auto" 
        onClick={(e) => {
          console.log('[FILTER-REMOVE] Clicking X for filter:', filterType, value)
          e.stopPropagation()
          e.preventDefault()
          onRemove()
        }}
      />
    </Badge>
  )
}