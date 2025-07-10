"use client"

import { useState, useCallback } from 'react'
import { UnifiedChartCard, ChartData, ChartContainerState } from '../shared/types'
import { 
  TrendingUp, 
  PieChart, 
  Building, 
  Package, 
  MessageCircle, 
  Target,
  Zap
} from 'lucide-react'

export function useChartManagement() {
  const [chartContainerState, setChartContainerState] = useState<ChartContainerState>('default')
  const [activeChartId, setActiveChartId] = useState<string | null>(null)
  const [dynamicCharts, setDynamicCharts] = useState<ChartData[]>([])
  
  // 预设图表卡片 - 补充完整的7个图表
  const presetCards: UnifiedChartCard[] = [
    {
      id: 'brand-analysis',
      type: 'preset',
      title: 'Brand Performance',
      description: 'Market share and brand positioning analysis',
      icon: Building,
      tabKey: 'brand-analysis',
      isActive: false,
      aiIntroduction: 'Below is the brand performance analysis across different product segments to understand revenue and volume dynamics:'
    },
    {
      id: 'market-insights',
      type: 'preset',
      title: 'Market Trends',
      description: 'Growth opportunities and market dynamics',
      icon: TrendingUp,
      tabKey: 'market-insights',
      isActive: false,
      aiIntroduction: 'Here is the revenue distribution analysis across product segments to identify high-growth opportunities:'
    },
    {
      id: 'product-analysis',
      type: 'preset',
      title: 'Product Deep Dive',
      description: 'Pricing, volume and revenue relationships',
      icon: Package,
      tabKey: 'product-analysis',
      isActive: false,
      aiIntroduction: 'Deep analysis of product pricing, volume, and revenue relationships across different market segments:'
    },
    {
      id: 'pricing-analysis',
      type: 'preset',
      title: 'Pricing Strategy',
      description: 'Competitive pricing and distribution analysis',
      icon: Target,
      tabKey: 'pricing-analysis',
      isActive: false,
      aiIntroduction: 'Analysis of pricing strategy distribution across brands to understand competitive landscape:'
    },
    {
      id: 'review-insights',
      type: 'preset',
      title: 'Customer Reviews',
      description: 'Pain points and satisfaction analysis',
      icon: MessageCircle,
      tabKey: 'review-insights',
      isActive: false,
      aiIntroduction: 'Customer pain points and satisfaction analysis based on reviews to identify product improvement opportunities:'
    },
    {
      id: 'package-preference',
      type: 'preset',
      title: 'Package Preference',
      description: 'Customer buying patterns and preferences',
      icon: PieChart,
      tabKey: 'package-preference',
      isActive: false,
      aiIntroduction: 'Customer preferences and buying patterns analysis for different package sizes:'
    },
    {
      id: 'competitor-analysis',
      type: 'preset',
      title: 'Competitive Analysis',
      description: 'Market positioning and competitive landscape',
      icon: Zap,
      tabKey: 'competitor-analysis',
      isActive: false,
      aiIntroduction: 'Competitive performance analysis across different dimensions to identify differentiation opportunities:'
    }
  ]

  // 动态图表卡片
  const dynamicCards: UnifiedChartCard[] = dynamicCharts.map(chart => ({
    id: chart.id,
    type: 'dynamic',
    title: chart.title || `Chart ${dynamicCharts.indexOf(chart) + 1}`,
    description: chart.explanation,
    chartCode: chart.code,
    timestamp: new Date(chart.timestamp),
    isActive: false
  }))

  // 合并所有卡片
  const allCards = [...presetCards, ...dynamicCards].map(card => ({
    ...card,
    isActive: card.id === activeChartId
  }))

  // 添加动态图表
  const addDynamicChart = useCallback((chart: ChartData) => {
    setDynamicCharts(prev => [...prev, chart])
    setActiveChartId(chart.id)
    setChartContainerState('dynamic')
  }, [])

  // 选择图表
  const selectChart = useCallback((chartId: string) => {
    setActiveChartId(chartId)
    
    const card = allCards.find(c => c.id === chartId)
    if (card) {
      if (card.type === 'preset') {
        setChartContainerState('navigation')
      } else {
        setChartContainerState('dynamic')
      }
    }
  }, [allCards])

  // 清除动态图表
  const clearDynamicCharts = useCallback(() => {
    setDynamicCharts([])
    if (activeChartId && dynamicCards.some(card => card.id === activeChartId)) {
      setActiveChartId(null)
      setChartContainerState('default')
    }
  }, [activeChartId, dynamicCards])

  return {
    // 状态
    chartContainerState,
    activeChartId,
    dynamicCharts,
    allCards,
    
    // 操作
    setChartContainerState,
    addDynamicChart,
    selectChart,
    clearDynamicCharts
  }
} 