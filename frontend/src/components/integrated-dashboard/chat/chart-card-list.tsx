"use client"

import { useState } from 'react'
import { ChartCard } from './chart-card'
import { UnifiedChartCard, ChartItemConfig } from '../shared/types'

interface ChartCardListProps {
  cards: UnifiedChartCard[]
  activeChartId: string | null
  onCardClick: (chartId: string) => void
  chartItems?: Record<string, ChartItemConfig[]> // New prop for dynamic chart items
}

export function ChartCardList({ cards, activeChartId, onCardClick, chartItems }: ChartCardListProps) {
  const [navigatingToChart, setNavigatingToChart] = useState<string | null>(null)
  
  // 滚动到指定图表的函数
  const scrollToChart = (chartId: string) => {
    // 设置正在导航状态
    setNavigatingToChart(chartId)
    
    // 找到包含该图表的卡片
    let targetCardId = null
    
    if (chartItems) {
      for (const [cardId, charts] of Object.entries(chartItems)) {
        if (charts.some(chart => chart.chart_id === chartId)) {
          targetCardId = cardId
          break
        }
      }
    }
    
    // 如果找到了对应的卡片且不是当前激活的卡片，则先切换卡片
    if (targetCardId && targetCardId !== activeChartId) {
      onCardClick(targetCardId)
    }
    
    // 滚动到目标图表的函数
    const performScroll = () => {
      const element = document.querySelector(`[data-chart-id="${chartId}"]`)
      if (element) {
        element.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        })
        
        // 高亮显示滚动到的图表
        const htmlElement = element as HTMLElement
        htmlElement.style.backgroundColor = '#fef3c7'
        htmlElement.style.transition = 'background-color 0.3s ease'
        htmlElement.style.borderRadius = '8px'
        htmlElement.style.padding = '0px'
        setTimeout(() => {
          htmlElement.style.backgroundColor = ''
          htmlElement.style.padding = ''
          // 清除导航状态
          setNavigatingToChart(null)
        }, 2000)
        
        return true
      }
      return false
    }
    
    // 等待DOM更新和数据加载
    const waitForElementAndScroll = (attempt = 0) => {
      const maxAttempts = 15 // 最大尝试15次，约3秒
      
      if (performScroll()) {
        // 成功找到元素并滚动
        return
      }
      
      if (attempt < maxAttempts) {
        // 如果没找到元素，继续等待
        setTimeout(() => {
          waitForElementAndScroll(attempt + 1)
        }, 200) // 每200ms尝试一次
      } else {
        console.warn(`Chart element with id "${chartId}" not found after ${maxAttempts} attempts`)
        // 清除导航状态
        setNavigatingToChart(null)
      }
    }
    
    // 开始等待和滚动
    setTimeout(() => {
      waitForElementAndScroll()
    }, targetCardId !== activeChartId ? 500 : 100) // 如果需要切换卡片，等待更长时间
  }

  return (
    <div className="space-y-2">
      {cards.map((card) => (
        <div key={card.id} className="space-y-1.5">
          {/* AI介绍文本 - 保留介绍文本但删除AI Avatar */}
          {card.type === 'preset' && card.aiIntroduction && (
            <div className="ai-text-title">
           
            </div>
          )}
          
          {/* 图表卡片 */}
          <ChartCard
            card={card}
            isActive={card.id === activeChartId}
            onClick={() => onCardClick(card.id)}
          />
          
          {/* 图表名称列表 - 只对预设卡片显示，且只对有chart items配置的卡片显示 */}
          {card.type === 'preset' && chartItems && chartItems[card.id] && (
            <div className="ml-4 border-l-2 border-gray-200 pl-3">
              <ul className="space-y-1">
                {chartItems[card.id].map((chart) => (
                  <li key={chart.chart_id}>
                    <button
                      onClick={() => scrollToChart(chart.chart_id)}
                      disabled={navigatingToChart === chart.chart_id}
                      className={`chart-navigation-item ${
                        navigatingToChart === chart.chart_id ? 'navigating' : ''
                      }`}
                    >
                      <span className={`chart-navigation-bullet ${navigatingToChart === chart.chart_id ? 'spinning' : ''}`}>
                        {navigatingToChart === chart.chart_id ? '⟳' : '•'}
                      </span>
                      <span className="leading-relaxed flex-1">
                        {chart.chart_name}
                       
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  )
} 