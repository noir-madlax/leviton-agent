"use client"

import React from 'react'
import { UnifiedChartCard } from '../shared/types'

interface ChartCardProps {
  card: UnifiedChartCard
  isActive: boolean
  onClick: () => void
}

export function ChartCard({ card, isActive, onClick }: ChartCardProps) {
  return (
    <div 
      className={`bg-white rounded-lg border-2 transition-all duration-200 cursor-pointer ${
        isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={onClick}
    >
      <div className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          {card.icon && <card.icon className="h-4 w-4" />}
          <h3 className="font-medium text-sm">{card.title}</h3>
          {card.type === 'dynamic' && card.timestamp && (
            <span className="text-xs text-gray-500 ml-auto">
              {card.timestamp.toLocaleTimeString()}
            </span>
          )}
        </div>
        <p className="text-xs text-gray-600 line-clamp-2">{card.description}</p>
        {card.type === 'dynamic' && (
          <div className="mt-2 text-xs text-blue-600">
            🤖 AI Generated
          </div>
        )}
      </div>
    </div>
  )
} 