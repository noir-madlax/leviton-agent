"use client"

import React from 'react'
import { ChartContainerState, ChartData } from '../shared/types'
import { AnalysisDbContainer } from '@/components/analysis-db'
import { DynamicChartRenderer } from './dynamic-chart-renderer'
import { ChevronRight } from 'lucide-react'
import { ProjectFilters } from '@/components/analysis-db/types/filters'

interface ChartContainerProps {
  state: ChartContainerState
  activeChartId: string | null
  dynamicCharts: ChartData[]
  navigationTab: string
  projectId: string
  filters: ProjectFilters
  onStateChange: (state: ChartContainerState) => void
}

export function ChartContainer({ 
  state, 
  activeChartId, 
  dynamicCharts, 
  navigationTab,
  projectId,
  filters,
  onStateChange
}: ChartContainerProps) {
  const renderContent = () => {
    switch (state) {
      case 'collapsed':
        return <CollapsedView onExpand={() => onStateChange('default')} />
      case 'default':
        return <DefaultView />
      case 'navigation':
        return (
          <AnalysisDbContainer 
            selectedProjectId={projectId}
            filters={filters}
            activeTab={navigationTab}
          />
        )
      case 'dynamic':
        return (
          <DynamicChartRenderer 
            chartId={activeChartId}
            charts={dynamicCharts}
          />
        )
      default:
        return <DefaultView />
    }
  }

  return (
    <div className={`chart-container ${state} h-full`}>
      {renderContent()}
    </div>
  )
}

function CollapsedView({ onExpand }: { onExpand: () => void }) {
  return (
    <div className="h-full flex items-center justify-center">
      <button
        onClick={onExpand}
        className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
      >
        <ChevronRight className="h-4 w-4" />
        Expand Charts
      </button>
    </div>
  )
}

function DefaultView() {
  return (
    <div className="h-full flex items-center justify-center text-gray-500">
      <div className="text-center">
        <p className="text-lg font-medium mb-2">Chart Analysis Panel</p>
        <p className="text-sm">Select a chart from the left to view detailed analysis</p>
      </div>
    </div>
  )
} 