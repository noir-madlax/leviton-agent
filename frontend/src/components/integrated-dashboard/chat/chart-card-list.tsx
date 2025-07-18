"use client"

import { useState } from 'react'
import { ChartCard } from './chart-card'
import { UnifiedChartCard } from '../shared/types'

interface ChartCardListProps {
  cards: UnifiedChartCard[]
  activeChartId: string | null
  onCardClick: (chartId: string) => void
}

// 定义每个图表类别下的具体图表
const CHART_DETAILS = {
  'brand-analysis': {
    title: 'Market Analysis',
    charts: [
      {
        name: 'Total addressable market (TAM) and Market Share by Brands/Product Segments',
        id: 'market-share-analysis'
      },
      {
        name: 'Top 10 Best-Selling Brands',
        id: 'brand-analysis'
      },
      {
        name: 'Sales Trend of Top 10 Brands',
        id: 'sales-trend-analysis'
      },
      {
        name: 'Top 10 Product Segments by Revenue/Volume',
        id: 'market-insights'
      },
      {
        name: 'Market Share by Package-Type',
        id: 'package-preference'
      }
    ]
  },
  'pricing-analysis': {
    title: 'Pricing Analysis',
    charts: [
      {
        name: 'Price Distribution Overview',
        id: 'price-distribution-overview'
      },
      {
        name: 'Price Distribution by Product Type',
        id: 'price-distribution-by-type'
      },
      {
        name: 'Price distribution by Brands',
        id: 'price-distribution-by-brands'
      },
      {
        name: 'Price vs. Revenue Distribution of Top Selling 20 Products',
        id: 'price-vs-revenue'
      }
    ]
  },
  'review-insights': {
    title: 'Customer Insights',
    charts: [
      {
        name: 'Top 10 Customer Pain Points by Product Segments',
        id: 'customer-pain-points'
      },
      {
        name: 'Top 10 Customer Delights by Product Segments',
        id: 'customer-delights'
      },
      {
        name: 'Use Case Sentiment Analysis',
        id: 'use-case-sentiment'
      }
    ]
  },
  'competitor-analysis': {
    title: 'Competitive Product Analysis',
    charts: [
      {
        name: 'Customer satisfaction overview',
        id: 'customer-satisfaction-overview'
      },
      {
        name: 'Product Comparison by Key Dimensions',
        id: 'product-comparison-dimensions'
      },
      {
        name: 'Product Comparison by Main Use Cases',
        id: 'product-comparison-use-cases'
      }
    ]
  }
}

export function ChartCardList({ cards, activeChartId, onCardClick }: ChartCardListProps) {
  const [navigatingToChart, setNavigatingToChart] = useState<string | null>(null)
  
  // 滚动到指定图表的函数
  const scrollToChart = (chartId: string) => {
    // 设置正在导航状态
    setNavigatingToChart(chartId)
    
    // 找到包含该图表的卡片
    let targetCardId = null
    
    for (const [cardId, details] of Object.entries(CHART_DETAILS)) {
      if (details.charts.some(chart => chart.id === chartId)) {
        targetCardId = cardId
        break
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
          
          {/* 图表名称列表 - 只对预设卡片显示，且只对有详细信息的卡片显示 */}
          {card.type === 'preset' && card.id in CHART_DETAILS && (
            <div className="ml-4 border-l-2 border-gray-200 pl-3">
              <ul className="space-y-1">
                {CHART_DETAILS[card.id as keyof typeof CHART_DETAILS].charts.map((chart) => (
                  <li key={chart.id}>
                    <button
                      onClick={() => scrollToChart(chart.id)}
                      disabled={navigatingToChart === chart.id}
                      className={`chart-navigation-item ${
                        navigatingToChart === chart.id ? 'navigating' : ''
                      }`}
                    >
                      <span className={`chart-navigation-bullet ${navigatingToChart === chart.id ? 'spinning' : ''}`}>
                        {navigatingToChart === chart.id ? '⟳' : '•'}
                      </span>
                      <span className="leading-relaxed flex-1">
                        {chart.name}
                        {navigatingToChart === chart.id && (
                          <span className="text-blue-600 text-xs ml-2 animate-pulse">
                            Navigating...
                          </span>
                        )}
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