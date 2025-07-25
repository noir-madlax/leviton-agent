// Customer Satisfaction Chart Component

"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ExternalLink } from "lucide-react"
import { Tooltip } from "@/components/ui/tooltip"
import { useCustomerSatisfactionData } from '../hooks/use-customer-satisfaction-data'
import type { CustomerSatisfactionChartProps, ProductSatisfactionData } from '../types/customer-satisfaction.types'

export function CustomerSatisfactionChart({ 
  projectId, 
  filters, 
  onProductClick 
}: CustomerSatisfactionChartProps) {
  const { data, loading, error } = useCustomerSatisfactionData(projectId, filters)

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, index) => (
          <Card key={index} className="p-4">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </div>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-red-600">
          <h3 className="text-lg font-semibold mb-2">Error Loading Data</h3>
          <p>{error}</p>
        </div>
      </Card>
    )
  }

  if (!data?.data || data.data.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <h3 className="text-lg font-semibold mb-2">No Data Available</h3>
          <p>No customer satisfaction data found for this project.</p>
        </div>
      </Card>
    )
  }

  const getSatisfactionColor = (score: number) => {
    if (score >= 85) return 'text-green-600 bg-green-50'
    if (score >= 70) return 'text-yellow-600 bg-yellow-50'
    if (score >= 60) return 'text-orange-600 bg-orange-50'
    return 'text-red-600 bg-red-50'
  }

  const formatPrice = (price?: number) => {
    if (!price) return 'N/A'
    return `$${price.toFixed(2)}`
  }

  const handleProductClick = (product: ProductSatisfactionData) => {
    onProductClick?.(product)
  }

  const handleExternalLinkClick = (url?: string) => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{data.data.length}</div>
          <div className="text-sm text-gray-500">Products Analyzed</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-green-600">
            {(data.data.reduce((sum, p) => sum + p.satisfaction_score, 0) / data.data.length).toFixed(1)}
          </div>
          <div className="text-sm text-gray-500">Avg Satisfaction</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-purple-600">
            {data.data.reduce((sum, p) => sum + p.total_reviews, 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-500">Total Reviews</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-orange-600">
            {data.data[0]?.brand || 'N/A'}
          </div>
          <div className="text-sm text-gray-500">Top Performer</div>
        </Card>
      </div>

      {/* Product Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.data.map((product, index) => (
          <Card 
            key={product.asin} 
            className="p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => handleProductClick(product)}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <Tooltip content={product.full_title}>
                  <h3 className="font-semibold text-gray-800 text-sm leading-tight">
                    {product.name}
                  </h3>
                </Tooltip>
                <p className="text-xs text-gray-500 mt-1">{product.brand}</p>
              </div>
              {product.product_url && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="p-1 h-auto"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleExternalLinkClick(product.product_url)
                  }}
                >
                  <ExternalLink className="h-3 w-3" />
                </Button>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Satisfaction Score</span>
                <span className={`text-sm font-bold px-2 py-1 rounded ${getSatisfactionColor(product.satisfaction_score)}`}>
                  {product.satisfaction_score.toFixed(1)}%
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Reviews Analyzed</span>
                <span className="text-sm font-medium">{product.total_reviews.toLocaleString()}</span>
              </div>

              {product.average_rating && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Avg Rating</span>
                  <span className="text-sm font-medium">
                    {product.average_rating.toFixed(1)} ⭐
                  </span>
                </div>
              )}

              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Price</span>
                <span className="text-sm font-medium">{formatPrice(product.price_usd)}</span>
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-gray-100">
              <div className="text-xs text-gray-400">
                Rank #{index + 1} by satisfaction
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Metadata */}
      <div className="mt-4 text-xs text-gray-400 text-center">
        Data generated at {new Date(data.timestamp).toLocaleString()}
      </div>
    </div>
  )
}
