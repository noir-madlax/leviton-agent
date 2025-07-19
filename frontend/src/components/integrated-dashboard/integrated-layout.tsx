"use client"

import { useState, useEffect } from 'react'
import './styles.css'
import { ArrowLeft, Filter, MessageSquare, ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { ChartContainer } from './chart/chart-container'
import { ChatWithNavigation } from './chat-with-navigation'
import { ProjectFilterWrapper } from './components/project-filter-wrapper'
import { AnalysisDbContainer } from '@/components/analysis-db'
import { DynamicChartRenderer } from './chart/dynamic-chart-renderer'
import { useDashboardNavigation } from './hooks/use-dashboard-navigation'
import { useChartManagement } from './hooks/use-chart-management'
import { ProjectFilters, DEFAULT_FILTERS } from '@/components/analysis-db/types/filters'
import { useFilterCache } from '@/components/analysis-db/hooks/use-filter-cache'
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
    brands: Array<{
      name: string
      count: number
      percentage: number
    }>
    segments: Array<{
      name: string
      count: number
      percentage: number
    }>
    extend_fields: Record<string, Array<{
      name: string
      count: number
      percentage: number
    }>>
  }
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
  }
}

interface IntegratedLayoutProps {
  projectId: string
  project: Project
  projectOverviewData?: ProjectOverviewData | null
  overviewLoading?: boolean
  onFiltersChange?: (filters: ProjectFilters) => void
  filters?: ProjectFilters
  isFilterExpanded?: boolean
  onToggleFilter?: () => void
}

export function IntegratedLayout({ 
  projectId, 
  project,
  projectOverviewData,
  overviewLoading,
  onFiltersChange,
  filters = DEFAULT_FILTERS,
  isFilterExpanded = false,
  onToggleFilter
}: IntegratedLayoutProps) {
  const { activeTab, setActiveTab } = useDashboardNavigation()
  const [isChartPanelExpanded, setIsChartPanelExpanded] = useState(true) // 默认展开状态
  
  // 获取缓存loading状态
  const { isLoading: cacheLoading } = useFilterCache(projectId)
  
  const {
    chartContainerState,
    activeChartId,
    dynamicCharts,
    allCards,
    setChartContainerState,
    addDynamicChart,
    selectChart
  } = useChartManagement()

  // 设置默认选中市场分析chart card
  useEffect(() => {
    if (!activeChartId && allCards.length > 0) {
      // 选择第一个chart card (brand-analysis - 市场分析)
      const marketAnalysisCard = allCards.find(card => card.id === 'brand-analysis')
      if (marketAnalysisCard) {
        selectChart(marketAnalysisCard.id)
        setActiveTab('brand-analysis')
      }
    }
  }, [activeChartId, allCards, selectChart, setActiveTab])

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

  const getFilterButtonText = () => {
    if (cacheLoading) {
      return 'Loading filter options...'
    }
    return isFilterExpanded ? 'Hide filters' : 'View Project Data Scope'
  }

  const getFilterButtonIcon = () => {
    if (cacheLoading) {
      return <Loader2 className="h-3.5 w-3.5 animate-spin" />
    }
    return <Filter className="h-3.5 w-3.5" />
  }

  // 计算活跃筛选器数量
  const activeFiltersCount = filters.categories.length + 
                           filters.brands.length + 
                           filters.segments.length +
                           Object.keys(filters.extend_fields).length;

  return (
    <div className="integrated-dashboard h-screen bg-gray-50/50 flex flex-col">
      {/* Header */}
      <header className="flex-shrink-0 border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Home
                </Button>
              </Link>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-semibold">{project.project_name}</h1>
                {/* Filter toggle button */}
                {onToggleFilter && (
                  <button
                    onClick={onToggleFilter}
                    disabled={cacheLoading}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border shadow-sm hover:shadow-md ${
                      cacheLoading 
                        ? 'bg-gray-100 text-gray-500 border-gray-300 cursor-not-allowed' 
                        : 'bg-blue-100 hover:bg-blue-200 text-blue-700 hover:text-blue-800 border-blue-200 hover:border-blue-300'
                    }`}
                  >
                    {getFilterButtonIcon()}
                    {getFilterButtonText()}
                  </button>
                )}
                {/* Filter count badge */}
                {activeFiltersCount > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {activeFiltersCount} filter{activeFiltersCount > 1 ? 's' : ''} applied
                  </Badge>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 hidden">
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
              <ProjectFilterWrapper
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
            className="hidden w-6 bg-gray-200 hover:bg-gray-300 border-r border-gray-300 flex items-center justify-center transition-colors"
            title="Hide Charts"
          >
            <ChevronRight className="h-4 w-4 text-gray-600" />
          </button>
        )}
        
        {/* 右侧Chart Panel - 仅在展开状态显示 */}
        {isChartPanelExpanded && (
          <div className="w-2/3 bg-white overflow-y-auto">
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
      </div>
    </div>
  )
} 