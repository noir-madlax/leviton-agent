import React from 'react'
import { Avatar } from '@/components/ui/avatar'
import { ChartCardList } from './chart-card-list'
import { ChatMessage, ChartItemConfig, UnifiedChartCard } from '../shared/types'

interface ChatTemplateProps {
  chatMessages: ChatMessage[]
  chartCards: UnifiedChartCard[]
  activeChartId: string | null
  onCardClick: (chartId: string) => void
  chartItems?: Record<string, ChartItemConfig[]>
}

export default function ChatTemplate({
  chatMessages,
  chartCards,
  activeChartId,
  onCardClick,
  chartItems
}: ChatTemplateProps) {
  // 如果没有chat messages，使用fallback内容
  if (!chatMessages || chatMessages.length === 0) {
    return (
      <div className="space-y-3">
        <div className="flex items-start gap-2">
          <Avatar className="h-6 w-2 mt-0.5">
          </Avatar>
          <div className="flex-1">
            <div className="p-3 mb-3">
              <div className="ai-text">
                The data is ready for further analysis.<br/>
                Based on your questions, these charts present the key information:
              </div>
            </div>
            <ChartCardList 
              cards={chartCards}
              activeChartId={activeChartId}
              onCardClick={onCardClick}
              chartItems={chartItems}
            />
          </div>
        </div>
        
        <div className="flex items-start gap-2">
          <Avatar className="h-6 w-2 mt-0.5">
          </Avatar>
          <div className="p-3">
            <div className="ai-text">
              Let me know if you&apos;d like to explore anything further.
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 渲染配置的chat messages
  return (
    <div className="space-y-3">
      {chatMessages.map((message, index) => (
        <div key={`${message.message_type}-${message.message_order}`} className="flex items-start gap-2">
          <Avatar className="h-6 w-2 mt-0.5">
          </Avatar>
          <div className="flex-1">
            {renderMessageContent(message, chartCards, activeChartId, onCardClick, chartItems)}
          </div>
        </div>
      ))}
    </div>
  )
}

function renderMessageContent(
  message: ChatMessage,
  chartCards: UnifiedChartCard[],
  activeChartId: string | null,
  onCardClick: (chartId: string) => void,
  chartItems?: Record<string, ChartItemConfig[]>
) {
  // 处理占位符替换
  if (message.message_type === 'chart_cards' && message.message_content === '{{CHART_CARDS}}') {
    return (
      <ChartCardList 
        cards={chartCards}
        activeChartId={activeChartId}
        onCardClick={onCardClick}
        chartItems={chartItems}
      />
    )
  }

  // 处理普通文本消息
  return (
    <div className="p-3">
      <div 
        className="ai-text"
        dangerouslySetInnerHTML={{ __html: message.message_content }}
      />
    </div>
  )
} 