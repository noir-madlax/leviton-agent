"use client"

import { useState, useEffect } from 'react'
import { ChatWithNavigation } from './chat-with-navigation'
import { AnalysisDbContainer } from '@/components/analysis-db'
import { useDashboardNavigation } from './hooks/use-dashboard-navigation'
import { Button } from '@/components/ui/button'
import { ArrowLeft, MessageSquare } from 'lucide-react'
import Link from 'next/link'
import { CategoryFilterAndProjectScope } from '@/components/analysis-db/shared/category-filter-and-project-scope'

// 使用现有的Project接口
interface Project {
  id: string
  project_name: string
  description?: string
  created_at: string
  updated_at: string
  status: string
}

// 添加项目概览数据接口
interface ProjectOverviewData {
  project_name: string
  created_at: string
  stats: {
    total_products: number
    total_brands: number
    total_reviews: number
    segment_count: number
  }
  distributions: {
    sources: Array<{
      name: string
      count: number
      percentage: number
    }>
    categories: Array<{
      name: string
      count: number
      percentage: number
    }>
  }
  available_categories: string[]
}

interface IntegratedLayoutProps {
  projectId: string
  project: Project
  projectOverviewData?: ProjectOverviewData | null
  overviewLoading?: boolean
  onFiltersChange?: (filters: { categories: string[]; asins: string[] }) => void
  filters?: { categories: string[]; asins: string[] }
  isFilterExpanded?: boolean
  onToggleFilter?: () => void
}

export function IntegratedLayout({ 
  projectId, 
  project,
  projectOverviewData,
  overviewLoading,
  onFiltersChange,
  filters = { categories: [], asins: [] },
  isFilterExpanded = false,
  onToggleFilter
}: IntegratedLayoutProps) {
  const { activeTab, setActiveTab } = useDashboardNavigation()

  // Tab映射：将图表导航的tab key映射到dashboard的实际tab
  const tabMapping: Record<string, string> = {
    'brand-analysis': 'brand-analysis',
    'product-analysis': 'product-analysis', 
    'pricing-analysis': 'pricing-analysis',
    'market-insights': 'market-insights',
    'package-preference': 'package-preference',
    'review-insights': 'review-insights',
    'competitor-analysis': 'competitor-analysis'
  }

  const handleTabChange = (tabKey: string) => {
    const mappedTab = tabMapping[tabKey] || tabKey
    setActiveTab(mappedTab)
  }

  return (
    <div className="h-screen bg-gray-50/50 flex flex-col">
      {/* Header */}
      <header className="flex-shrink-0 border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Projects
                </Button>
              </Link>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-semibold">{project.project_name}</h1>
                {/* Filter toggle button */}
                {onToggleFilter && (
                  <button
                    onClick={onToggleFilter}
                    className="text-xs text-blue-600 hover:text-blue-800 cursor-pointer transition-colors"
                  >
                    {isFilterExpanded ? 'Hide filters' : 'Click to adjust product category scope'}
                  </button>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Chat Button - 导航到独立chat页面 */}
              <Link href={`/project/${projectId}/chat?from=dashboard`}>
                <Button variant="outline">
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Full Chat
                </Button>
              </Link>
            </div>
          </div>
          
          {/* 动态展开的过滤器区域 */}
          {isFilterExpanded && onFiltersChange && (
            <div className="pb-4 pt-2 mt-4">
              <CategoryFilterAndProjectScope 
                projectId={projectId}
                onFiltersChange={onFiltersChange}
                initialFilters={filters}
                preloadedData={projectOverviewData}
                isDataLoading={overviewLoading || false}
              />
            </div>
          )}
        </div>
      </header>

      {/* 主要内容区域 */}
      <div className="flex flex-1 h-80">
        {/* 左侧Chat Panel - 1/3 */}
        <div className="w-1/3 border-r bg-white overflow-y-auto">
          <ChatWithNavigation 
            projectId={projectId}
            onTabChange={handleTabChange}
            activeTab={activeTab}
          />
        </div>
        
        {/* 右侧Dashboard Panel - 2/3 */}
        <div className="w-2/3 overflow-y-auto">
          <AnalysisDbContainer 
            selectedProjectId={projectId}
            filters={filters}
            activeTab={activeTab}
          />
        </div>
      </div>
    </div>
  )
} 