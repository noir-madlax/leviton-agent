"use client"

import { ProjectFilters } from '@/components/analysis-db/types/filters'

interface ChartDemoProps {
  projectId: string
}

export function ChartDemo({ projectId }: ChartDemoProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
      <div className="bg-white rounded-lg shadow-sm border">
        <MarketInsightsDemo projectId={projectId} />
      </div>

      <div className="bg-white rounded-lg shadow-sm border">
        <BrandAnalysisDemo projectId={projectId} />
      </div>
    </div>
  )
}

// 示例组件，展示如何接收filters prop
function MarketInsightsDemo({ filters, projectId }: { filters?: ProjectFilters; projectId?: string }) {
  return (
    <div className="h-96 bg-gray-50 rounded-lg flex items-center justify-center">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">Market Insights Chart</h3>
        <p className="text-gray-600">Project: {projectId}</p>
        <p className="text-sm text-gray-500 mt-2">Active filters: {JSON.stringify(filters || {})}</p>
      </div>
    </div>
  )
}

function BrandAnalysisDemo({ filters, projectId }: { filters?: ProjectFilters; projectId?: string }) {
  return (
    <div className="h-96 bg-gray-50 rounded-lg flex items-center justify-center">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">Brand Analysis Chart</h3>
        <p className="text-gray-600">Project: {projectId}</p>
        <p className="text-sm text-gray-500 mt-2">Active filters: {JSON.stringify(filters || {})}</p>
      </div>
    </div>
  )
} 