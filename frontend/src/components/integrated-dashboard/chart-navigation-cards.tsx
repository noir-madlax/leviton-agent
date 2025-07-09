"use client"

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ThumbnailPreview } from './chart-thumbnails'

interface ChartCard {
  id: string
  title: string
  description: string
  tabKey: string
}

const chartCards: ChartCard[] = [
  {
    id: 'brand-analysis',
    title: 'Brand Analysis',
    description: 'Analyze brand performance and market share across different product categories',
    tabKey: 'brand-analysis'
  },
  {
    id: 'product-analysis',
    title: 'Product Analysis',
    description: 'Deep dive into product pricing, sales volume and revenue relationships',
    tabKey: 'product-analysis'
  },
  {
    id: 'pricing-analysis',
    title: 'Pricing Analysis',
    description: 'Explore price distribution and pricing strategies across product categories',
    tabKey: 'pricing-analysis'
  },
  {
    id: 'market-insights',
    title: 'Market Insights',
    description: 'Discover market trends and opportunities for growth',
    tabKey: 'market-insights'
  },
  {
    id: 'package-preference',
    title: 'Package Preference',
    description: 'Analyze package size preferences and sales performance',
    tabKey: 'package-preference'
  },
  {
    id: 'review-insights',
    title: 'Review Insights',
    description: 'Extract key insights and pain points from customer reviews',
    tabKey: 'review-insights'
  },
  {
    id: 'competitor-analysis',
    title: 'Competitor Analysis',
    description: 'Analyze competitor products and market performance',
    tabKey: 'competitor-analysis'
  }
]

interface ChartNavigationCardsProps {
  onTabChange: (tab: string) => void
  activeTab: string
}

export function ChartNavigationCards({ 
  onTabChange, 
  activeTab 
}: ChartNavigationCardsProps) {
  return (
    <div className="space-y-1.5">
      {/* AI avatar and introduction */}
      <div className="flex items-start gap-1.5">
        <Avatar className="h-5 w-5 mt-0.5">
          <AvatarFallback className="text-xs">AI</AvatarFallback>
        </Avatar>
        <div>
          <p className="text-xs text-gray-600 mb-2 leading-snug">
            I&apos;ve prepared the following data analysis charts for you. Click any card to view detailed content on the right panel:
          </p>
        </div>
      </div>

      {/* Chart cards list */}
      <div className="space-y-1">
        {chartCards.map((card) => (
          <Card 
            key={card.id} 
            className={`cursor-pointer transition-all duration-200 hover:shadow-sm ${
              activeTab === card.tabKey 
                ? 'ring-1 ring-blue-500 bg-blue-50' 
                : 'hover:bg-gray-50'
            }`}
            onClick={() => onTabChange(card.tabKey)}
          >
            <CardHeader className="pb-0.5 pt-1.5 px-2">
              <CardTitle className="flex items-center gap-1.5 text-xs font-medium">
                <ThumbnailPreview type={card.id} className="w-5 h-3" />
                <span className="flex-1">{card.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0 pb-1.5 px-2">
              <p className="text-xs text-gray-600 mb-1 leading-snug">
                {card.description}
              </p>
             
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
} 