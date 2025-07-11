"use client"

import { ChartCard } from './chart-card'
import { UnifiedChartCard } from '../shared/types'

interface ChartCardListProps {
  cards: UnifiedChartCard[]
  activeChartId: string | null
  onCardClick: (chartId: string) => void
}

export function ChartCardList({ cards, activeChartId, onCardClick }: ChartCardListProps) {
  return (
    <div className="space-y-2">
      {cards.map((card, index) => (
        <div key={card.id} className="space-y-1.5">
          {/* AI介绍文本 - 保留介绍文本但删除AI Avatar */}
          {card.type === 'preset' && card.aiIntroduction && (
            <p className="text-base font-semibold  text-gray-700 leading-relaxed">
              {card.aiIntroduction}
            </p>
          )}
          
          {/* 图表卡片 */}
          <ChartCard
            card={card}
            isActive={card.id === activeChartId}
            onClick={() => onCardClick(card.id)}
          />
          
         
        </div>
      ))}
    </div>
  )
} 