"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Filter, RotateCcw, X } from "lucide-react"
import { databaseService } from '@/components/analysis-db/data/database-service'

interface ProjectFiltersProps {
  projectId: string | null
  onFiltersChange?: (filters: ProjectFilters) => void
  initialFilters?: ProjectFilters
}

interface ProjectFilters {
  categories: string[]
  asins: string[]
  brands: string[]  // 新增: 品牌筛选
  segments: string[]  // 新增: 产品段筛选
  is_bestseller?: string  // 新增: 畅销书状态筛选
  extend_fields: Record<string, any>  // 新增: 扩展字段筛选
}

export function ProjectFilters({ 
  projectId, 
  onFiltersChange, 
  initialFilters = { categories: [], asins: [], brands: [], segments: [], is_bestseller: undefined, extend_fields: {} }
}: ProjectFiltersProps) {
  const [availableCategories, setAvailableCategories] = useState<string[]>([])
  const [pendingCategories, setPendingCategories] = useState<string[]>(initialFilters.categories)
  const [appliedCategories, setAppliedCategories] = useState<string[]>(initialFilters.categories)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!projectId) {
      setAvailableCategories([])
      setPendingCategories([])
      setAppliedCategories([])
      return
    }

    const loadFilterOptions = async () => {
      setLoading(true)
      try {
        const overview = await databaseService.getProjectOverview(projectId)
        setAvailableCategories(overview.available_categories.flat_categories)
      } catch (error) {
        console.error('Failed to load filter options:', error)
        setAvailableCategories([])
      } finally {
        setLoading(false)
      }
    }

    loadFilterOptions()
  }, [projectId])

  // 监听initialFilters的变化，同步内部状态
  useEffect(() => {
    if (initialFilters) {
      setPendingCategories(initialFilters.categories)
      setAppliedCategories(initialFilters.categories)
    }
  }, [initialFilters])

  const handleCategorySelect = (category: string) => {
    if (category === 'all') {
      setPendingCategories([])
    } else if (!pendingCategories.includes(category)) {
      setPendingCategories(prev => [...prev, category])
    }
  }

  const handleCategoryRemove = (category: string) => {
    setPendingCategories(prev => prev.filter(c => c !== category))
  }

  const handleApplyFilters = () => {
    setAppliedCategories(pendingCategories)
    if (onFiltersChange) {
      onFiltersChange({
        categories: pendingCategories,
        asins: [],
        brands: [],
        segments: [],
        is_bestseller: undefined,
        extend_fields: {}
      })
    }
  }

  const handleReset = () => {
    setPendingCategories([])
    setAppliedCategories([])
    if (onFiltersChange) {
      onFiltersChange({
        categories: [],
        asins: [],
        brands: [],
        segments: [],
        is_bestseller: undefined,
        extend_fields: {}
      })
    }
  }

  const hasPendingChanges = JSON.stringify(pendingCategories) !== JSON.stringify(appliedCategories)
  const hasActiveFilters = appliedCategories.length > 0

  if (!projectId) {
    return null
  }

  return (
    <div className="mb-6">
      <Card className="border-gray-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Category Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 pt-0">
          <div className="flex items-center gap-4">
            {/* Filter controls */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Category:</span>
              <Select onValueChange={handleCategorySelect} disabled={loading}>
                <SelectTrigger className="w-48 h-8">
                  <SelectValue placeholder="Select category..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories (No Filter)</SelectItem>
                  {availableCategories
                    .filter(category => !pendingCategories.includes(category))
                    .map((category) => (
                      <SelectItem key={category} value={category}>
                        {category}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            {/* Apply button */}
            <Button
              onClick={handleApplyFilters}
              disabled={!hasPendingChanges}
              size="sm"
              className="h-8"
            >
              Apply Filters
            </Button>

            {/* Reset button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={!hasActiveFilters && pendingCategories.length === 0}
              className="h-8"
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              Reset
            </Button>

            {/* Status indicator */}
            {hasPendingChanges && (
              <div className="text-xs text-orange-600">
                {pendingCategories.length} pending changes
              </div>
            )}
            {hasActiveFilters && !hasPendingChanges && (
              <div className="text-xs text-green-600">
                {appliedCategories.length} filter{appliedCategories.length > 1 ? 's' : ''} applied
              </div>
            )}
          </div>

          {/* Pending filters display */}
          {pendingCategories.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-gray-600">
                  {hasPendingChanges ? 'Pending filters:' : 'Applied filters:'}
                </span>
                {pendingCategories.map((category) => (
                  <Badge
                    key={category}
                    variant={hasPendingChanges ? "outline" : "secondary"}
                    className={`text-xs flex items-center gap-1 ${
                      hasPendingChanges ? 'border-orange-300 text-orange-700' : ''
                    }`}
                  >
                    {category}
                    <X
                      className="w-3 h-3 cursor-pointer hover:text-red-500 pointer-events-auto"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleCategoryRemove(category)
                      }}
                    />
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Status message */}
          {hasActiveFilters && !hasPendingChanges && (
            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs text-green-700">
              <strong>✓ Filters Applied:</strong> Analysis data is now filtered by selected categories.
            </div>
          )}
          {hasPendingChanges && (
            <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-700">
              <strong>⏳ Pending Changes:</strong> Click &quot;Apply Filters&quot; to update the analysis data.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 