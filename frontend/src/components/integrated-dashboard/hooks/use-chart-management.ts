"use client"

import { useState, useCallback, useEffect } from 'react'
import { UnifiedChartCard, ChartData, ChartContainerState, ChatConfig, ChartCardConfig } from '../shared/types'
import { chatConfigService } from '@/lib/services/chat-config-service'
import { 
  TrendingUp, 
  PieChart, 
  Building, 
  Package, 
  MessageCircle, 
  Target,
  Zap
} from 'lucide-react'

// Icon mapping for dynamic configuration
const ICON_MAP: Record<string, any> = {
  'Building': Building,
  'Target': Target,
  'MessageCircle': MessageCircle,
  'Zap': Zap,
  'TrendingUp': TrendingUp,
  'PieChart': PieChart,
  'Package': Package
}

interface UseChartManagementProps {
  projectId?: string
}

export function useChartManagement(props?: UseChartManagementProps) {
  const [chartContainerState, setChartContainerState] = useState<ChartContainerState>('default')
  const [activeChartId, setActiveChartId] = useState<string | null>(null)
  const [dynamicCharts, setDynamicCharts] = useState<ChartData[]>([])
  
  // New state for configuration management
  const [chatConfig, setChatConfig] = useState<ChatConfig | null>(null)
  const [configLoading, setConfigLoading] = useState(false)
  const [configError, setConfigError] = useState<string | null>(null)

  // Load configuration when projectId changes
  useEffect(() => {
    if (props?.projectId) {
      loadChatConfig(props.projectId)
    }
  }, [props?.projectId])

  const loadChatConfig = async (projectId: string) => {
    try {
      setConfigLoading(true)
      setConfigError(null)
      
      const config = await chatConfigService.getChatConfig(projectId)
      setChatConfig(config)
      console.log(`🔧 Chat config loaded for project ${projectId}:`, config)
      
    } catch (error) {
      console.error('Failed to load chat config:', error)
      setConfigError(error instanceof Error ? error.message : 'Unknown error')
      
      // Set fallback config
      setChatConfig(await chatConfigService.getChatConfig(projectId))
    } finally {
      setConfigLoading(false)
    }
  }

  // Convert configuration to UnifiedChartCard format
  const presetCards: UnifiedChartCard[] = chatConfig ? 
    chatConfig.chart_cards.map((cardConfig: ChartCardConfig) => ({
      id: cardConfig.card_id,
      type: 'preset' as const,
      title: cardConfig.card_config.title,
      description: cardConfig.card_config.description,
      icon: ICON_MAP[cardConfig.card_config.icon] || Building,
      tabKey: cardConfig.card_config.tabKey,
      isActive: false,
      aiIntroduction: cardConfig.card_config.aiIntroduction
    })) : []

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
    
    // 配置相关状态
    chatConfig,
    configLoading,
    configError,
    
    // 操作
    setChartContainerState,
    addDynamicChart,
    selectChart,
    clearDynamicCharts,
    loadChatConfig
  }
} 