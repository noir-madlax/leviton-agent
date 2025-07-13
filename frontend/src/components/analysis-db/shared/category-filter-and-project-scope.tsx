"use client"

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Filter, RotateCcw, X, Database, Users, MessageSquare, BarChart3, Loader2 } from "lucide-react"
import { databaseService } from '@/components/analysis-db/data/database-service'

interface CategoryFilterAndProjectScopeProps {
  projectId: string | null
  onFiltersChange?: (filters: ProjectFilters) => void
  initialFilters?: ProjectFilters
  preloadedData?: ProjectOverviewData | null
  isDataLoading?: boolean
}

interface ProjectFilters {
  categories: string[]
  asins: string[]
}

interface ProjectOverviewData {
  project_name: string;
  created_at: string;
  stats: {
    total_products: number;
    total_brands: number;
    total_reviews: number;
    segment_count: number;
  };
  distributions: {
    sources: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    categories: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
  };
  available_categories: {
    flat_categories: string[];
    hierarchical_categories: Array<{
      parent_category: string;
      parent_count: number;
      children: Array<{
        category: string;
        count: number;
        percentage: number;
      }>;
    }>;
    total_products: number;
  };
}

export function CategoryFilterAndProjectScope({ 
  projectId, 
  onFiltersChange, 
  initialFilters = { categories: [], asins: [] },
  preloadedData,
  isDataLoading
}: CategoryFilterAndProjectScopeProps) {
  // Filter states
  const [availableCategories, setAvailableCategories] = useState<{
    flat_categories: string[];
    hierarchical_categories: Array<{
      parent_category: string;
      parent_count: number;
      children: Array<{
        category: string;
        count: number;
        percentage: number;
      }>;
    }>;
    total_products: number;
  }>({
    flat_categories: [],
    hierarchical_categories: [],
    total_products: 0
  })
  const [pendingCategories, setPendingCategories] = useState<string[]>(initialFilters.categories)
  const [appliedCategories, setAppliedCategories] = useState<string[]>(initialFilters.categories)
  const [filterLoading, setFilterLoading] = useState(false)

  // Project overview states - 优先使用预加载数据
  const [projectData, setProjectData] = useState<ProjectOverviewData | null>(preloadedData || null)
  const [overviewLoading, setOverviewLoading] = useState(isDataLoading || false)

  // 监听预加载数据变化
  useEffect(() => {
    if (preloadedData) {
      setProjectData(preloadedData)
      setAvailableCategories(preloadedData.available_categories)
    }
  }, [preloadedData])

  // 监听加载状态变化
  useEffect(() => {
    setOverviewLoading(isDataLoading || false)
  }, [isDataLoading])

  // Load data when projectId changes - 只在没有预加载数据时才加载
  useEffect(() => {
    if (!projectId) {
      setAvailableCategories({
        flat_categories: [],
        hierarchical_categories: [],
        total_products: 0
      })
      setPendingCategories([])
      setAppliedCategories([])
      if (!preloadedData) {
        setProjectData(null)
      }
      return
    }

    // 只在没有预加载数据时才进行数据加载
    if (!preloadedData && !projectData) {
      loadData()
    }
  }, [projectId, preloadedData, projectData])

  const loadData = async () => {
    if (!projectId) return

    setFilterLoading(true)
    try {
      const overview = await databaseService.getProjectOverview(projectId)
      setAvailableCategories(overview.available_categories)
      setProjectData(overview)
    } catch (error) {
      console.error('Failed to load project data:', error)
      setAvailableCategories({
        flat_categories: [],
        hierarchical_categories: [],
        total_products: 0
      })
      setProjectData(null)
    } finally {
      setFilterLoading(false)
    }
  }

  const loadProjectOverview = useCallback(async () => {
    if (!projectId) return

    setOverviewLoading(true)
    try {
      const categoryFilters = appliedCategories.length > 0 ? appliedCategories : undefined
      const overview = await databaseService.getProjectOverview(projectId, categoryFilters)
      setProjectData(overview)
    } catch (error) {
      console.error('Failed to load project overview:', error)
      setProjectData(null)
    } finally {
      setOverviewLoading(false)
    }
  }, [projectId, appliedCategories])

  // Load project overview when filters change - 重新加载项目概览数据
  useEffect(() => {
    if (!projectId) return
    // 当appliedCategories变化时总是重新加载数据（有过滤器或无过滤器）
    loadProjectOverview()
  }, [projectId, loadProjectOverview])

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
        asins: []
      })
    }
  }

  const handleReset = () => {
    setPendingCategories([])
    setAppliedCategories([])
    if (onFiltersChange) {
      onFiltersChange({
        categories: [],
        asins: []
      })
    }
  }

  const hasPendingChanges = JSON.stringify(pendingCategories) !== JSON.stringify(appliedCategories)
  const hasActiveFilters = appliedCategories.length > 0

  if (!projectId) {
    return null
  }

  // Format categories text
  const categoriesText = projectData?.distributions.categories
    ?.map(category => `${category.name} (${category.percentage}%)`)
    .join(', ') || ''

  return (
    <div className="mb-4">
      <Card className="border-gray-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filter Project Scope by Product Categories
          </CardTitle>
          <div className="text-sm text-gray-600 mt-1">
            Filters will <strong>apply to all</strong> charts and Xenith responses
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-0 space-y-4">
          {/* Category Filters Section */}
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              {/* Filter controls */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Category:</span>
                <Select onValueChange={handleCategorySelect} disabled={filterLoading}>
                  <SelectTrigger className="w-48 h-8">
                    <SelectValue placeholder="Select category..." />
                  </SelectTrigger>
                  <SelectContent className="max-h-80">
                    <SelectItem value="all">All Categories (No Filter)</SelectItem>
                    {availableCategories.hierarchical_categories?.map((parentGroup) => (
                      <div key={parentGroup.parent_category} className="mb-2">
                        {/* 父类别标题 */}
                        <div className="px-2 py-1.5 text-sm font-semibold text-gray-700 bg-gray-100 border-b sticky top-0 z-10">
                          📁 {parentGroup.parent_category} ({parentGroup.parent_count} products)
                        </div>
                        
                        {/* 子类别选项 */}
                        {parentGroup.children
                          .filter(child => !pendingCategories.includes(child.category))
                          .map((child) => (
                            <SelectItem 
                              key={child.category} 
                              value={child.category}
                              className="pl-6 py-2"
                            >
                              <div className="flex justify-between items-center w-full">
                                <span className="flex items-center gap-2">
                                  🏷️ {child.category}
                                </span>
                                <span className="text-sm text-gray-500">
                                  {child.count} ({child.percentage}%)
                                </span>
                              </div>
                            </SelectItem>
                          ))}
                      </div>
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
              <div className="pt-2 border-t border-gray-100">
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
              <div className="p-2 bg-green-50 border border-green-200 rounded text-xs text-green-700">
                <strong>✓ Filters Applied:</strong> Analysis data is now filtered by selected categories.
              </div>
            )}
            {hasPendingChanges && (
              <div className="p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-700">
                <strong>⏳ Pending Changes:</strong> Click &quot;Apply Filters&quot; to update the analysis data.
              </div>
            )}
          </div>

          {/* Project Data Scope Section */}
          <div className="pt-3 border-t border-gray-100">
            {overviewLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
                <span className="text-sm text-gray-600">Loading project data...</span>
              </div>
            ) : projectData ? (
              <>
                {/* Statistics Cards - Compact layout */}
                <div className="grid grid-cols-4 gap-3 mb-3">
                  <div className="flex items-center gap-2 p-2 bg-blue-50 rounded">
                    <Database className="w-4 h-4 text-blue-500" />
                    <div>
                      <p className="text-lg font-bold text-blue-900">{projectData.stats.total_products.toLocaleString()}</p>
                      <p className="text-xs text-blue-600">Products</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 p-2 bg-green-50 rounded">
                    <Users className="w-4 h-4 text-green-500" />
                    <div>
                      <p className="text-lg font-bold text-green-900">{projectData.stats.total_brands}</p>
                      <p className="text-xs text-green-600">Brands</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 p-2 bg-purple-50 rounded">
                    <MessageSquare className="w-4 h-4 text-purple-500" />
                    <div>
                      <p className="text-lg font-bold text-purple-900">{projectData.stats.total_reviews.toLocaleString()}</p>
                      <p className="text-xs text-purple-600">Reviews</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 p-2 bg-orange-50 rounded">
                    <BarChart3 className="w-4 h-4 text-orange-500" />
                    <div>
                      <p className="text-lg font-bold text-orange-900">{projectData.stats.segment_count}</p>
                      <p className="text-xs text-orange-600">Segments</p>
                    </div>
                  </div>
                </div>

                {/* Distribution information - Compact layout */}
                <div className="space-y-1 text-sm">
                  {projectData.distributions.categories.length > 0 && (
                    <div className="flex items-start gap-2">
                      <span className="font-medium text-gray-700 flex-shrink-0 text-xs">Categories:</span>
                      <span className="text-gray-600 flex-1 text-xs">
                        {categoriesText}
                      </span>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-red-600">
                  Failed to load project data. Please try again.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 