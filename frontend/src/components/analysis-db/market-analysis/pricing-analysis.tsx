"use client"

import React, { useState, useMemo } from 'react'
import { Card } from "@/components/ui/card"
import { BrandViolinChart } from "../charts/brand-violin-chart"
import { MultiSegmentViolinChart } from "../charts/multi-segment-violin-chart"
import { PriceTypeSelector, type PriceType } from "@/components/analysis-db/shared/price-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import type { Product } from "@/components/analysis-db/types/analysis"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"

interface PricingAnalysisProps {
  data: {
    priceDistribution: {
      category: string
      skuPrices: number[]
      unitPrices: number[]
      productCount: number
      stats: {
        sku: {
          min: number
          q1: number
          median: number
          mean: number
          q3: number
          max: number
        }
        unit: {
          min: number
          q1: number
          median: number
          mean: number
          q3: number
          max: number
        }
      }
    }[]
    brandPriceDistribution: {
      category: string
      brands: {
        name: string
        skuPrices: number[]
        unitPrices: number[]
      }[]
    }[]
  }
  productLists: {
    byBrand: Record<string, Product[]>
    bySegment: Record<string, Product[]>
    byPackageSize: Record<string, Product[]>
  }
}

export function PricingAnalysis({ data, productLists }: PricingAnalysisProps) {
  const [priceType, setPriceType] = useState<PriceType>('unit')
  const { openPanel } = useProductPanel()

  // 获取所有分类数据
  const allCategories = useMemo(() => 
    data?.priceDistribution || [],
    [data]
  )

  // 生成Multi-Segment Violin Chart数据
  const violinSegments = useMemo(() => {
    return allCategories.map((category, index) => ({
      name: category.category,
      prices: priceType === 'unit' ? category.unitPrices : category.skuPrices,
      color: getChartColor(index),
      productCount: category.productCount,
      stats: priceType === 'unit' ? category.stats.unit : category.stats.sku
    }))
  }, [allCategories, priceType])

  const handleViolinClick = (segmentName: string) => {
    const products = productLists.bySegment[segmentName] || []
    openPanel(
      products,
      segmentName,
      `${products.length} products in ${segmentName}`,
      { brand: true, category: false, priceRange: true, packSize: true }
    )
  }

  const handleBrandViolinClick = (brand: string, category: string) => {
    const allBrandProducts = productLists.byBrand[brand] || []
    
    // 通过segment匹配产品
    const filteredProducts = allBrandProducts.filter(product => {
      // 首先尝试直接匹配分类名称
      if (product.category === category) {
        return true
      }
      // 然后通过segment匹配（如果product有segment信息）
      if (productLists.bySegment[category]) {
        return productLists.bySegment[category].some(p => p.id === product.id)
      }
      return false
    })
    
    console.log('Filtered products:', filteredProducts.length)
    
    openPanel(
      filteredProducts,
      `${brand} - ${category}`,
      `${filteredProducts.length} products from ${brand} in ${category}`,
      { brand: false, category: false, priceRange: true, packSize: true }
    )
  }

  // 检查是否有所需的数据
  if (!data?.priceDistribution || data.priceDistribution.length === 0) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">💰 Pricing Analysis</h2>
        <Card className="p-6 bg-gray-50">
          <p className="text-center text-gray-500">Price distribution data is not available.</p>
          <p className="text-center text-gray-400 text-sm mt-2">Waiting for valid product data...</p>
        </Card>
      </section>
    )
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">💰 Pricing Analysis</h2>

      {/* 显示所有segments的价格分布概览 */}
      <h3 className="text-xl font-semibold mb-4">Price Distribution by Segment</h3>
      <Card className="p-6 bg-gray-50 mb-8">
        <PriceTypeSelector onChange={setPriceType} />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="text-left p-3 font-semibold">Segment</th>
                <th className="text-right p-3 font-semibold">Products</th>
                <th className="text-right p-3 font-semibold">Min</th>
                <th className="text-right p-3 font-semibold">Median</th>
                <th className="text-right p-3 font-semibold">Max</th>
                <th className="text-right p-3 font-semibold">Average</th>
              </tr>
            </thead>
            <tbody>
              {allCategories.map((category, index) => {
                const categoryPrices = priceType === 'unit' ? category.unitPrices : category.skuPrices
                const categoryStats = priceType === 'unit' ? category.stats.unit : category.stats.sku
                const icons = ["🔆", "💡", "🔥", "⚡", "🌟", "🎯", "📊", "💎", "🚀", "💡", "🔧", "⚙️", "🎨", "🏆", "⭐"]
                const icon = icons[index % icons.length]
                
                return (
                  <tr key={category.category} className="border-b border-gray-100 hover:bg-white transition-colors">
                    <td className="p-3">
                      <div className="font-medium text-gray-900">
                        {icon} {category.category}
                      </div>
                    </td>
                    <td className="p-3 text-right font-medium text-gray-700">
                      {categoryPrices.length}
                    </td>
                    <td className="p-3 text-right font-medium text-green-600">
                      ${categoryStats.min.toFixed(2)}
                    </td>
                    <td className="p-3 text-right font-medium text-blue-600">
                      ${categoryStats.median.toFixed(2)}
                    </td>
                    <td className="p-3 text-right font-medium text-red-600">
                      ${categoryStats.max.toFixed(2)}
                    </td>
                    <td className="p-3 text-right font-medium text-purple-600">
                      ${categoryStats.mean.toFixed(2)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Multi-Segment Violin Chart: 显示所有segments的价格分布 */}
      <h3 className="text-xl font-semibold mb-4">
        All Segments Price Distribution Comparison
      </h3>
      <Card className="p-6 bg-gray-50 mb-8">
        <PriceTypeSelector onChange={setPriceType} />
        <div className="text-sm text-gray-600 mb-4">
          <strong>Violin Chart:</strong> The width of each violin shows the density of products at different price points. 
          Wider areas indicate more products at that price range.
        </div>
        <div className="h-[500px]">
          <MultiSegmentViolinChart 
            segments={violinSegments}
            priceType={priceType}
            onViolinClick={handleViolinClick}
          />
        </div>
      </Card>

      {/* Brand Price Distribution: 显示所有segments */}
      <h3 className="text-xl font-semibold mb-4">Brand Price Distribution by Segment</h3>
      <Card className="p-6 bg-gray-50">
        <PriceTypeSelector onChange={setPriceType} />
        <div className="space-y-8">
          {data.brandPriceDistribution.map((categoryData, index) => (
            <div key={categoryData.category} className="w-full">
              <h4 className="text-lg font-medium mb-3 text-center">
                {index === 0 ? "🔆" : index === 1 ? "💡" : index === 2 ? "🔥" : "📊"} {categoryData.category}
              </h4>
              <div className="h-[420px] w-full">
                <BrandViolinChart 
                  brands={categoryData.brands} 
                  priceType={priceType} 
                  category={categoryData.category} 
                  onViolinClick={handleBrandViolinClick} 
                />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </section>
  )
}
