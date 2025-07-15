"use client"

import { Badge } from "@/components/ui/badge"
import { Filter, ChevronUp, ChevronDown, Loader2 } from "lucide-react"

interface ChartFilterButtonProps {
  chartId?: string
  title: string
  activeFiltersCount?: number
  isExpanded?: boolean
  isLoading?: boolean
  onToggle: (expanded: boolean) => void
  className?: string
}

export function ChartFilterButton({
  chartId,
  title,
  activeFiltersCount = 0,
  isExpanded = false,
  isLoading = false,
  onToggle,
  className = ""
}: ChartFilterButtonProps) {
  const handleClick = () => {
    if (!isLoading) {
      onToggle(!isExpanded)
    }
  }

  const getButtonText = () => {
    if (isLoading) {
      return 'Loading filter options...'
    }
    return isExpanded ? 'Hide filters' : `Click to filter ${title}`
  }

  const getButtonIcon = () => {
    if (isLoading) {
      return <Loader2 className="h-3.5 w-3.5 animate-spin" />
    }
    if (isExpanded) {
      return <ChevronUp className="h-3.5 w-3.5" />
    }
    return <ChevronDown className="h-3.5 w-3.5" />
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* 活跃筛选器数量显示 */}
      {activeFiltersCount > 0 && (
        <Badge variant="outline" className="text-xs">
          {activeFiltersCount} filters
        </Badge>
      )}
      
      {/* 筛选器按钮 */}
      <button
        onClick={handleClick}
        disabled={isLoading}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border shadow-sm hover:shadow-md ${
          isLoading 
            ? 'bg-gray-100 text-gray-500 border-gray-300 cursor-not-allowed' 
            : 'bg-blue-100 hover:bg-blue-200 text-blue-700 hover:text-blue-800 border-blue-200 hover:border-blue-300'
        }`}
      >
        <Filter className="h-3.5 w-3.5" />
        {getButtonText()}
        {getButtonIcon()}
      </button>
    </div>
  )
} 