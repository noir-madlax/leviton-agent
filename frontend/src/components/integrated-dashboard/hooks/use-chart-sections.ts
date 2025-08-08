"use client"

import { useState, useEffect } from 'react'
import { ChartSectionConfig } from '../shared/types'
import { chatConfigService } from '../../../lib/services/chat-config-service'

export function useChartSections(tabKey: string, projectId: string) {
  const [chartSections, setChartSections] = useState<ChartSectionConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadChartSections = async () => {
      if (!projectId || !tabKey) {
        setChartSections([])
        return
      }

      try {
        setLoading(true)
        setError(null)
        
        // Get complete chat config
        const chatConfig = await chatConfigService.getChatConfig(projectId)
        
        // Extract chart sections for the specific tab
        const sections = chatConfig?.chart_sections?.[tabKey] || []
        setChartSections(sections)
        
      } catch (err) {
        console.error(`Error loading chart sections for ${tabKey}:`, err)
        setError(err instanceof Error ? err.message : 'Failed to load chart sections')
        
        // Fallback to empty array on error
        setChartSections([])
      } finally {
        setLoading(false)
      }
    }

    loadChartSections()
  }, [tabKey, projectId])

  // Helper function to check if a chart should be shown
  const shouldShowChart = (chartId: string): boolean => {
    const section = chartSections.find(s => s.chart_id === chartId)
    
    // If configuration is found, use it
    if (section) {
      return section.is_active
    }
    
    // If no configuration found, default to true for pricing analysis charts
    const pricingAnalysisCharts = [
      'price-distribution-overview',
      'price-vs-revenue', 
      'price-distribution-by-type',
      'price-distribution-by-brands'
    ]
    
    // Default to true for pricing analysis charts, false for others
    return pricingAnalysisCharts.includes(chartId)
  }

  return {
    chartSections,
    loading,
    error,
    shouldShowChart
  }
}