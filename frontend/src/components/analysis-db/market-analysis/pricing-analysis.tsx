"use client"

import React, { useState, useMemo } from 'react'
import { Card } from "@/components/ui/card"
import { BrandViolinChart } from "../charts/brand-violin-chart"
import { MultiSegmentViolinChart } from "../charts/multi-segment-violin-chart"
import { PriceTypeSelector, type PriceType } from "@/components/analysis-db/shared/price-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import type { Product } from "@/components/analysis-db/types/analysis"

interface PricingAnalysisProps {
  data: {
    priceDistribution: {
      category: string
      skuPrices: number[]
      unitPrices: number[]
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
    const colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300"]
    
    return allCategories.map((category, index) => ({
      name: category.category,
      prices: priceType === 'unit' ? category.unitPrices : category.skuPrices,
      color: colors[index % colors.length],
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
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {allCategories.map((category, index) => {
            const categoryPrices = priceType === 'unit' ? category.unitPrices : category.skuPrices
            const categoryStats = priceType === 'unit' ? category.stats.unit : category.stats.sku
            const icons = ["🔆", "💡", "🔥", "⚡"]
            const icon = icons[index % icons.length]
            
            return (
              <div key={category.category} className="bg-white p-4 rounded-lg border">
                <h4 className="text-md font-medium mb-3 text-center">
                  {icon} {category.category}
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Products:</span>
                    <span className="font-medium">{categoryPrices.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Min:</span>
                    <span className="font-medium">${categoryStats.min.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Median:</span>
                    <span className="font-medium">${categoryStats.median.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Max:</span>
                    <span className="font-medium">${categoryStats.max.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average:</span>
                    <span className="font-medium">${categoryStats.mean.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            )
          })}
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
