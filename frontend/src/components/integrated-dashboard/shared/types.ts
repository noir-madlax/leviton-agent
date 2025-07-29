// Unified types for integrated dashboard
export interface UnifiedChartCard {
  id: string
  type: 'preset' | 'dynamic'
  title: string
  description: string
  icon?: any
  tabKey?: string
  chartCode?: string
  timestamp?: Date
  isActive: boolean
  aiIntroduction?: string  // AI介绍文本
}

export type ChartContainerState = 
  | 'collapsed'    // 收起状态
  | 'default'      // 默认空白状态
  | 'navigation'   // 预设图表状态
  | 'dynamic'      // 动态图表状态

export interface ChartContainerProps {
  state: ChartContainerState
  activeChartId: string | null
  dynamicCharts: ChartData[]
  navigationTab: string
  onStateChange: (state: ChartContainerState) => void
}

export interface ChartData {
  id: string
  code: string
  explanation: string
  insights?: string
  timestamp: number
  type: 'single' | 'multiple'
  title?: string  // 添加图表标题
  
  // 兼容原有格式
  chartData?: {
    code: string
    explanation: string
    insights?: string
  }
}

export interface ContentPart {
  type: 'text' | 'insight' | 'chart'
  content: string
  isComplete?: boolean
  index?: number
}

export interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  isAnalyzing?: boolean
  contentParts?: ContentPart[]
  isStreaming?: boolean
  charts?: ChartReference[]
}

export interface ChartReference {
  chartId: string
  title: string
  description: string
  insertPosition: number
}

export interface ChatWithNavigationProps {
  projectId: string
  onTabChange: (tab: string) => void
  activeTab: string
  onChartSelect: (chartId: string) => void
  chartCards: UnifiedChartCard[]
  activeChartId: string | null
}

// ==================== Chat Config Types ====================

export interface ChatMessage {
  message_order: number
  message_type: 'opening' | 'chart_cards' | 'closing'
  message_content: string
}

export interface ChartCardConfig {
  card_order: number
  card_id: string
  card_config: {
    title: string
    description: string
    icon: string
    tabKey: string
    aiIntroduction: string
  }
}

export interface ChartItemConfig {
  chart_order: number
  chart_name: string
  chart_id: string
  chart_component?: string
}

export interface ChatConfig {
  chat_messages: ChatMessage[]
  chart_cards: ChartCardConfig[]
  chart_items: Record<string, ChartItemConfig[]>
  project_id?: string
}

// Updated props interface to support new configuration
export interface ChatWithNavigationPropsV2 {
  projectId: string
  chartCards: UnifiedChartCard[]
  activeChartId: string | null
  onChartSelect: (chartId: string) => void
  onAddDynamicChart: (chart: ChartData) => void
  chatConfig?: ChatConfig // New configuration data
}

export interface ChartCardListProps {
  cards: UnifiedChartCard[]
  activeChartId: string | null
  onCardClick: (chartId: string) => void
  chartItems?: Record<string, ChartItemConfig[]> // New chart items configuration
} 