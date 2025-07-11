"use client"

import React from 'react'
import { UnifiedChartCard } from '../shared/types'
import { ThumbnailPreview } from '../chart-thumbnails'

interface ChartCardProps {
  card: UnifiedChartCard
  isActive: boolean
  onClick: () => void
}

// 图标颜色映射
const iconColorMap = {
  'brand-analysis': 'text-blue-600',
  'market-insights': 'text-orange-600', 
  'product-analysis': 'text-green-600',
  'pricing-analysis': 'text-purple-600',
  'review-insights': 'text-pink-600',
  'package-preference': 'text-teal-600',
  'competitor-analysis': 'text-red-600'
}

export function ChartCard({ card, isActive, onClick }: ChartCardProps) {
  // 获取图标颜色
  const getIconColor = () => {
    if (card.type === 'dynamic') return 'text-blue-600'
    return iconColorMap[card.tabKey as keyof typeof iconColorMap] || 'text-gray-600'
  }

  return (
    <div 
      className={`bg-white rounded-lg border-2 transition-all duration-200 cursor-pointer transform hover:scale-[1.02] hover:shadow-lg ${
        isActive 
          ? 'border-blue-500 bg-blue-50 shadow-md' 
          : 'border-gray-200 hover:border-blue-300 hover:shadow-md'
      }`}
      onClick={onClick}
    >
      <div className="p-3 flex items-start justify-between">
        {/* 左侧内容区域 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            {card.icon && <card.icon className={`h-4 w-4 ${getIconColor()}`} />}
            <h3 className="font-medium text-sm truncate">{card.title}</h3>
            {card.type === 'dynamic' && card.timestamp && (
              <span className="text-xs text-gray-500 ml-auto">
                {card.timestamp.toLocaleTimeString()}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-600 line-clamp-2 mb-1">{card.description}</p>
          {card.type === 'dynamic' && (
            <div className="text-xs text-blue-600">
              🤖 AI Generated
            </div>
          )}
        </div>
        
        {/* 右侧图表预览区域 */}
        {card.type === 'preset' && card.tabKey && (
          <div className="flex-shrink-0 ml-3">
            <ThumbnailPreview 
              type={card.tabKey}
              className="opacity-75 hover:opacity-100 transition-opacity"
            />
          </div>
        )}
        
        {/* 动态图表的预览图标 */}
        {card.type === 'dynamic' && (
          <div className="flex-shrink-0 ml-3">
            <div className="w-12 h-8 border rounded bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
              <div className="text-blue-600 text-xs">📊</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 