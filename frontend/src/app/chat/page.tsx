'use client'

import React, { useState } from 'react'
import { ChartRenderer } from './components/chart-renderer'
import type { SalesTrendFilters } from './charts/sales_trend/types/sales-trend.types'

// 模拟项目ID - 实际使用时应该从路由参数或上下文获取
const DEMO_PROJECT_ID = 'd2c02b80-4c82-44cc-8093-56708a7883f7'

export default function ChatPage() {
  const [currentChart, setCurrentChart] = useState<string>('sales_trend')
  const [chartFilters, setChartFilters] = useState<SalesTrendFilters>({
    categories: [],
    brands: [],
    segments: [],
    extend_fields: {}
  })

  const handleChartRequest = (chartType: string, filters: SalesTrendFilters) => {
    setCurrentChart(chartType)
    setChartFilters(filters)
  }

  const handleFilterChange = (newFilters: Partial<SalesTrendFilters>) => {
    setChartFilters(prev => ({
      ...prev,
      ...newFilters
    }))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            📊 Sales Analytics Chat
          </h1>
          <p className="text-gray-600">
            Interactive sales data analysis and visualization
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* 左侧控制面板 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">
                Chart Controls
              </h2>
              
              {/* 图表类型选择 */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Chart Type
                </label>
                <select
                  value={currentChart}
                  onChange={(e) => setCurrentChart(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="sales_trend">Sales Trend</option>
                  <option value="market_insights" disabled>Market Insights (Coming Soon)</option>
                  <option value="competitor_analysis" disabled>Competitor Analysis (Coming Soon)</option>
                </select>
              </div>

              {/* 过滤器控制 */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Categories
                  </label>
                  <input
                    type="text"
                    placeholder="Light Switches, Dimmer Switches"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onChange={(e) => {
                      const categories = e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                      handleFilterChange({ categories })
                    }}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Brands
                  </label>
                  <input
                    type="text"
                    placeholder="Leviton, Lutron"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onChange={(e) => {
                      const brands = e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                      handleFilterChange({ brands })
                    }}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Segments
                  </label>
                  <input
                    type="text"
                    placeholder="Combination Switches"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onChange={(e) => {
                      const segments = e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                      handleFilterChange({ segments })
                    }}
                  />
                </div>
              </div>

              {/* 快速操作按钮 */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Quick Actions</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => handleFilterChange({ categories: ['Light Switches'] })}
                    className="w-full text-left px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 transition-colors"
                  >
                    Light Switches Only
                  </button>
                  <button
                    onClick={() => handleFilterChange({ brands: ['Leviton', 'Lutron'] })}
                    className="w-full text-left px-3 py-2 text-sm bg-green-50 text-green-700 rounded-md hover:bg-green-100 transition-colors"
                  >
                    Top 2 Brands
                  </button>
                  <button
                    onClick={() => setChartFilters({ categories: [], brands: [], segments: [], extend_fields: {} })}
                    className="w-full text-left px-3 py-2 text-sm bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100 transition-colors"
                  >
                    Clear All Filters
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {/* 右侧图表展示区域 */}
          <div className="lg:col-span-3">
            {currentChart ? (
              <ChartRenderer
                chartType={currentChart}
                projectId={DEMO_PROJECT_ID}
                filters={chartFilters}
                dateRange={{
                  start_date: "2025-01-01",
                  end_date: "2025-06-30"
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-96 bg-white rounded-lg shadow-sm">
                <div className="text-center text-gray-500">
                  <div className="text-gray-400 mb-4">
                    <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <p className="text-lg font-medium">Select a chart type to begin</p>
                  <p className="text-sm mt-2">Choose from the available chart options on the left</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 