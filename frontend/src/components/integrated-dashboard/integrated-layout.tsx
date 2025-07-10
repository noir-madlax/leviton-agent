"use client"

import { useState } from 'react'
import { ChatWithNavigation } from './chat-with-navigation'
import { ChartContainer } from './chart/chart-container'
import { useChartManagement } from './hooks/use-chart-management'
import { useDashboardNavigation } from './hooks/use-dashboard-navigation'
import { Button } from '@/components/ui/button'
import { ArrowLeft, MessageSquare, ChevronLeft, ChevronRight } from 'lucide-react'
import Link from 'next/link'
import { CategoryFilterAndProjectScope } from '@/components/analysis-db/shared/category-filter-and-project-scope'
import { ChartData } from './shared/types'

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
  const [isChartPanelExpanded, setIsChartPanelExpanded] = useState(false) // 默认为折叠状态
  
  const {
    chartContainerState,
    activeChartId,
    dynamicCharts,
    allCards,
    setChartContainerState,
    addDynamicChart,
    selectChart
  } = useChartManagement()

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

  const handleChartSelect = (chartId: string) => {
    selectChart(chartId)
    // 当选择图表时，自动展开chart面板
    setIsChartPanelExpanded(true)
    const card = allCards.find(c => c.id === chartId)
    if (card && card.type === 'preset' && card.tabKey) {
      handleTabChange(card.tabKey)
    }
  }

  const handleAddDynamicChart = (chart: ChartData) => {
    addDynamicChart(chart)
    // 当添加动态图表时，自动展开chart面板
    setIsChartPanelExpanded(true)
  }

  const toggleChartPanel = () => {
    setIsChartPanelExpanded(!isChartPanelExpanded)
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
        {/* 左侧Chat Panel - 根据chart面板状态调整宽度 */}
        <div className={`bg-white overflow-y-auto transition-all duration-300 ${
          isChartPanelExpanded ? 'w-1/3 border-r' : 'w-full mx-[20%] max-w-none'
        }`}>
          <div className={`${isChartPanelExpanded ? '' : 'max-w-4xl mx-auto'}`}>
            <ChatWithNavigation 
              projectId={projectId}
              chartCards={allCards}
              activeChartId={activeChartId}
              onChartSelect={handleChartSelect}
              onAddDynamicChart={handleAddDynamicChart}
            />
          </div>
        </div>
        
        {/* Chart面板切换按钮 - 仅在展开状态显示 */}
        {isChartPanelExpanded && (
          <button
            onClick={toggleChartPanel}
            className="w-6 bg-gray-200 hover:bg-gray-300 border-r border-gray-300 flex items-center justify-center transition-colors"
            title="Hide Charts"
          >
            <ChevronRight className="h-4 w-4 text-gray-600" />
          </button>
        )}
        
        {/* 右侧Chart Panel - 仅在展开状态显示 */}
        {isChartPanelExpanded && (
          <div className="w-2/3 overflow-y-auto">
            <ChartContainer
              state={chartContainerState}
              activeChartId={activeChartId}
              dynamicCharts={dynamicCharts}
              navigationTab={activeTab}
              projectId={projectId}
              filters={filters}
              onStateChange={setChartContainerState}
            />
          </div>
        )}
        
        {/* 展开Chart面板的按钮 - 仅在收起状态显示 */}
        {!isChartPanelExpanded && (
          <button
            onClick={toggleChartPanel}
            className="fixed bottom-6 right-6 w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-colors z-10"
            title="Show Charts"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  )
} 