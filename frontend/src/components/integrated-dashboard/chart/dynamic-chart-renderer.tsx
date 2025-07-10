"use client"

import React, { useState, useEffect } from 'react'
import { ChartData } from '../shared/types'
import { Loader2 } from 'lucide-react'
import { compileChartCode, validateChartCode } from '@/lib/chart-compiler'

interface DynamicChartRendererProps {
  chartId: string | null
  charts: ChartData[]
}

export function DynamicChartRenderer({ chartId, charts }: DynamicChartRendererProps) {
  const activeChart = charts.find(c => c.id === chartId)
  
  if (!activeChart) {
    return <NoChartSelectedView />
  }

  return (
    <div className="dynamic-chart-renderer h-full flex flex-col">
      <ChartHeader chart={activeChart} />
      <div className="flex-1 overflow-hidden">
        <ChartContent code={activeChart.code} />
      </div>
    </div>
  )
}

function NoChartSelectedView() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center text-gray-500">
        <div className="text-lg mb-2">🔍</div>
        <div className="text-sm">No chart selected</div>
      </div>
    </div>
  )
}

function ChartHeader({ chart }: { chart: ChartData }) {
  return (
    <div className="border-b bg-white p-4">
      <h3 className="font-medium text-gray-900">{chart.explanation}</h3>
      <p className="text-sm text-gray-600 mt-1">{chart.insights}</p>
      <div className="text-xs text-gray-500 mt-2">
        Generated {new Date(chart.timestamp).toLocaleString()}
      </div>
    </div>
  )
}

function ChartContent({ code }: { code: string }) {
  const [CompiledChart, setCompiledChart] = useState<React.ComponentType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    renderChart()
  }, [code])

  const renderChart = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      // 验证代码安全性
      const validation = validateChartCode(code)
      if (!validation.valid) {
        throw new Error(validation.error)
      }

      // 编译代码
      const result = compileChartCode(code)
      if (!result.success) {
        throw new Error(result.error)
      }

      // 设置组件
      setCompiledChart(() => result.component!)
      
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
        <span className="ml-2 text-gray-600">Generating chart...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <div className="text-red-500 mb-2">Chart generation failed</div>
        <div className="text-sm text-gray-500">{error}</div>
      </div>
    )
  }

  if (!CompiledChart) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">No chart to render</div>
      </div>
    )
  }

  return (
    <div className="w-full h-full p-4">
      <CompiledChart />
    </div>
  )
} 