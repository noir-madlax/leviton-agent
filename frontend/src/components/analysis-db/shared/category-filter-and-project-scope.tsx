"use client"

import { useState, useEffect } from 'react'
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
  available_categories: string[];
}

export function CategoryFilterAndProjectScope({ 
  projectId, 
  onFiltersChange, 
  initialFilters = { categories: [], asins: [] } 
}: CategoryFilterAndProjectScopeProps) {
  // Filter states
  const [availableCategories, setAvailableCategories] = useState<string[]>([])
  const [pendingCategories, setPendingCategories] = useState<string[]>(initialFilters.categories)
  const [appliedCategories, setAppliedCategories] = useState<string[]>(initialFilters.categories)
  const [filterLoading, setFilterLoading] = useState(false)

  // Project overview states
  const [projectData, setProjectData] = useState<ProjectOverviewData | null>(null)
  const [overviewLoading, setOverviewLoading] = useState(false)

  // Load data when projectId changes
  useEffect(() => {
    if (!projectId) {
      setAvailableCategories([])
      setPendingCategories([])
      setAppliedCategories([])
      setProjectData(null)
      return
    }

    loadData()
  }, [projectId])

  // Load project overview when filters change
  useEffect(() => {
    if (!projectId) return
    loadProjectOverview()
  }, [projectId, appliedCategories])

  const loadData = async () => {
    if (!projectId) return

    setFilterLoading(true)
    try {
      const overview = await databaseService.getProjectOverview(projectId)
      setAvailableCategories(overview.available_categories)
      setProjectData(overview)
    } catch (error) {
      console.error('Failed to load project data:', error)
      setAvailableCategories([])
      setProjectData(null)
    } finally {
      setFilterLoading(false)
    }
  }

  const loadProjectOverview = async () => {
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
  }

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

  // Format sources and categories text
  const sourcesText = projectData?.distributions.sources
    ?.map(source => `${source.name} (${source.percentage}%)`)
    .join(' • ') || ''

  const categoriesText = projectData?.distributions.categories
    ?.map(category => `${category.name} (${category.percentage}%)`)
    .join(', ') || ''

  return (
    <div className="mb-4">
      <Card className="border-gray-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Category Filter & Project Scope
          </CardTitle>
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
                        className="w-3 h-3 cursor-pointer hover:text-red-500"
                        onClick={() => handleCategoryRemove(category)}
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
                <strong>⏳ Pending Changes:</strong> Click "Apply Filters" to update the analysis data.
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
                  {projectData.distributions.sources.length > 0 && (
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-700 text-xs">Data Sources:</span>
                      <span className="text-gray-600 text-xs">{sourcesText}</span>
                    </div>
                  )}

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