"use client"

import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ThumbnailPreview } from './chart-thumbnails'
import { BarChart3, TrendingUp, Users, Package, MessageSquare, Zap, Target } from 'lucide-react'

// 每个card配一句精炼的介绍，并添加图标和数据预览
const chartItems = [
  {
    id: 'brand-analysis',
    title: 'Brand Performance',
    description: 'Market share and brand positioning analysis',
    tabKey: 'brand-analysis',
    introduction: 'Let me show you the brand performance analysis to understand market positioning:',
    icon: TrendingUp,
    dataPreview: 'Revenue by Brand',
    bgColor: 'bg-blue-50',
    iconColor: 'text-blue-600'
  },
  {
    id: 'market-insights',
    title: 'Market Trends',
    description: 'Growth opportunities and market dynamics',
    tabKey: 'market-insights',
    introduction: 'Next, here are the key market trends and growth opportunities:',
    icon: BarChart3,
    dataPreview: 'Top Segments',
    bgColor: 'bg-green-50',
    iconColor: 'text-green-600'
  },
  {
    id: 'product-analysis',
    title: 'Product Deep Dive',
    description: 'Pricing, volume and revenue relationships',
    tabKey: 'product-analysis',
    introduction: 'For detailed product analysis, this chart shows pricing and sales relationships:',
    icon: Package,
    dataPreview: 'Price vs Volume',
    bgColor: 'bg-purple-50',
    iconColor: 'text-purple-600'
  },
  {
    id: 'pricing-analysis',
    title: 'Pricing Strategy',
    description: 'Competitive pricing and distribution analysis',
    tabKey: 'pricing-analysis',
    introduction: 'The pricing strategy analysis reveals competitive positioning:',
    icon: Target,
    dataPreview: 'Price Distribution',
    bgColor: 'bg-orange-50',
    iconColor: 'text-orange-600'
  },
  {
    id: 'review-insights',
    title: 'Customer Reviews',
    description: 'Pain points and satisfaction analysis',
    tabKey: 'review-insights',
    introduction: 'Customer feedback analysis provides valuable insights:',
    icon: MessageSquare,
    dataPreview: 'Sentiment Analysis',
    bgColor: 'bg-pink-50',
    iconColor: 'text-pink-600'
  },
  {
    id: 'package-preference',
    title: 'Package Preference',
    description: 'Customer buying patterns and preferences',
    tabKey: 'package-preference',
    introduction: 'Package preference data shows customer buying patterns:',
    icon: Users,
    dataPreview: 'Package Size Trends',
    bgColor: 'bg-indigo-50',
    iconColor: 'text-indigo-600'
  },
  {
    id: 'competitor-analysis',
    title: 'Competitive Analysis',
    description: 'Market positioning and competitive landscape',
    tabKey: 'competitor-analysis',
    introduction: 'Finally, competitive landscape analysis for strategic positioning:',
    icon: Zap,
    dataPreview: 'Competitor Matrix',
    bgColor: 'bg-red-50',
    iconColor: 'text-red-600'
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
    <div className="space-y-3">
      {/* Single AI response with structured content */}
      <div className="flex items-start gap-2">
        <Avatar className="h-6 w-6 mt-0.5">
          <AvatarFallback className="text-xs">AI</AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-3 leading-relaxed">
            I&apos;ve prepared comprehensive data analysis charts for your market research. Each chart provides unique insights:
          </p>
          
          {/* Chart items with introduction + card */}
          <div className="space-y-2.5">
            {chartItems.map((item) => (
              <div key={item.id} className="space-y-1.5">
                {/* Introduction text */}
                <p className="text-xs text-gray-700 leading-relaxed">
                  {item.introduction}
                </p>
                
                {/* Redesigned Card */}
                <Card 
                  className={`cursor-pointer transition-all duration-200 w-90 hover:shadow-md border-l-4 ${
                    activeTab === item.tabKey 
                      ? `border-l-blue-500 ${item.bgColor} ring-1 ring-blue-200` 
                      : 'border-l-gray-200 hover:border-l-blue-300 hover:bg-gray-50'
                  }`}
                  onClick={() => onTabChange(item.tabKey)}
                >
                  <CardHeader className="p-0">
                    <div className="flex items-center gap-3 h-10">
                      {/* Icon */}
                      <div className={`p-2 rounded-lg ${item.bgColor}`}>
                        <item.icon className={`w-4 h-4 ${item.iconColor}`} />
                      </div>
                      
                      {/* Main content */}
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-sm font-semibold text-gray-900 mb-1">
                          {item.title}
                        </CardTitle>
                        <p className="text-xs text-gray-600 mb-1">
                          {item.description}
                        </p>
                        <div className="flex items-center gap-2">
                          <ThumbnailPreview type={item.id} className="w-4 h-2.5 flex-shrink-0" />
                          <span className="text-xs text-gray-500 font-medium">
                            {item.dataPreview}
                          </span>
                        </div>
                      </div>
                      
                      {/* Active indicator */}
                      {activeTab === item.tabKey && (
                        <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                      )}
                    </div>
                  </CardHeader>
                </Card>
              </div>
            ))}
          </div>
          
          {/* Follow-up suggestion */}
          <p className="text-xs text-gray-600 leading-relaxed mt-3">
            💡 <strong>Need deeper insights?</strong> Click any chart above or ask follow-up questions about specific data points.
          </p>
        </div>
      </div>
    </div>
  )
} 