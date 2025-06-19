"use client"

import { useState, useMemo } from "react"
import { Card } from "@/components/ui/card"
import { ViolinChart } from "@/components/analysis-db/charts/violin-chart"
import { BrandViolinChart } from "@/components/analysis-db/charts/brand-violin-chart"
import { PriceTypeSelector, type PriceType } from "@/components/analysis-db/shared/price-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import type { Product } from "@/components/analysis-db/types/analysis"

function calculateStats(products: Product[], priceType: PriceType) {
  const prices = products.map(p => priceType === 'unit' ? p.unitPrice : p.price).filter(p => p !== null && p !== undefined);
  if (prices.length === 0) {
    return { min: 0, q1: 0, median: 0, mean: 0, q3: 0, max: 0 };
  }
  prices.sort((a, b) => a - b);
  const min = prices[0];
  const max = prices[prices.length - 1];
  const q1 = prices[Math.floor(prices.length / 4)];
  const median = prices[Math.floor(prices.length / 2)];
  const q3 = prices[Math.floor((prices.length * 3) / 4)];
  const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
  return { min, q1, median, mean, q3, max };
}

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
  productAnalysis: {
    priceVsRevenue: {
      category: string
      products: Product[]
    }[]
  }
  productLists: {
    byBrand: Record<string, Product[]>
    bySegment: Record<string, Product[]>
    byPackageSize: Record<string, Product[]>
  }
}

export function PricingAnalysis({ data, productLists, productAnalysis }: PricingAnalysisProps) {
  const [priceType, setPriceType] = useState<PriceType>("unit")
  const { openPanel } = useProductPanel()

  const dimmerProducts = useMemo(() => 
    productAnalysis.priceVsRevenue.find(c => c.category === "Dimmer Switches")?.products || [], 
    [productAnalysis]
  );
  
  const switchProducts = useMemo(() =>
    productAnalysis.priceVsRevenue.find(c => c.category === "Light Switches")?.products || [],
    [productAnalysis]
  );

  const dimmerPrices = useMemo(() => 
    dimmerProducts.map(p => priceType === 'unit' ? p.unitPrice : p.price),
    [dimmerProducts, priceType]
  );

  const switchPrices = useMemo(() =>
    switchProducts.map(p => priceType === 'unit' ? p.unitPrice : p.price),
    [switchProducts, priceType]
  );

  const dimmerStats = useMemo(() => 
    calculateStats(dimmerProducts, priceType),
    [dimmerProducts, priceType]
  );

  const switchStats = useMemo(() =>
    calculateStats(switchProducts, priceType),
    [switchProducts, priceType]
  );

  const getBrands = (category: number) => {
    if (!data?.brandPriceDistribution?.[category]?.brands) {
      console.error(`Brand price distribution data not found for category ${category}`)
      return []
    }
    return data.brandPriceDistribution[category].brands
  }

  const handleViolinClick = (category: string, priceRange: { min: number; max: number }) => {
    const centerPrice = (priceRange.min + priceRange.max) / 2
    const tolerance = (priceRange.max - priceRange.min) / 2

    const productsForCategory = category.includes("Dimmer") ? dimmerProducts : switchProducts;

    const filteredProducts = productsForCategory.filter(product => {
      const price = priceType === 'unit' ? product.unitPrice : product.price
      return Math.abs(price - centerPrice) <= tolerance
    })

    openPanel(
      filteredProducts,
      `${category}: $${priceRange.min.toFixed(2)} - $${priceRange.max.toFixed(2)}`,
      `${filteredProducts.length} products found in ${category} with ${priceType === 'unit' ? 'unit' : 'SKU'} price within ±${tolerance.toFixed(2)} of $${centerPrice.toFixed(2)}`,
      { brand: true, category: false, priceRange: false, packSize: true }
    )
  }

  const handleBrandViolinClick = (brand: string, category: string) => {
    const allBrandProducts = productLists.byBrand[brand] || []
    
    // Filter brand products directly by category instead of trying to match different datasets
    const filteredProducts = allBrandProducts.filter(product => {
      // Check if product has a category field
      if (product.category) {
        return product.category === category
      }
      // If no category field, infer from product name or other fields
      const productName = product.name?.toLowerCase() || ''
      const isDimmer = productName.includes('dimmer')
      const isTargetDimmer = category === "Dimmer Switches"
      
      return isDimmer === isTargetDimmer
    })
    
    console.log('Filtered products:', filteredProducts.length)
    
    openPanel(
      filteredProducts,
      `${brand} - ${category}`,
      `${filteredProducts.length} ${category.toLowerCase()} from ${brand}`,
      { brand: false, category: false, priceRange: true, packSize: true }
    )
  }

  // Check if we have the required data
  if (!data?.priceDistribution || data.priceDistribution.length < 2) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">💰 Pricing Analysis</h2>
        <Card className="p-6 bg-gray-50">
          <p className="text-center text-gray-500">Price distribution data is not available.</p>
        </Card>
      </section>
    )
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">💰 Pricing Analysis</h2>

      <h3 className="text-xl font-semibold mb-4">Price Distribution: Dimmers vs Switches</h3>
      <Card className="p-6 bg-gray-50 mb-8">
        <PriceTypeSelector onChange={setPriceType} />
        <div className="h-[400px]">
          <ViolinChart
            dimmerPrices={dimmerPrices}
            switchPrices={switchPrices}
            dimmerStats={dimmerStats}
            switchStats={switchStats}
            priceType={priceType}
            productLists={productLists}
            onViolinClick={handleViolinClick}
            dimmerProducts={dimmerProducts}
            switchProducts={switchProducts}
          />
        </div>
      </Card>

      <h3 className="text-xl font-semibold mb-4">Brand Price Distribution by Category</h3>
      <Card className="p-6 bg-gray-50">
        <PriceTypeSelector onChange={setPriceType} />
        <div className="space-y-8">
          <div className="w-full">
            <h4 className="text-lg font-medium mb-3 text-center">🔆 Dimmer Switches</h4>
            <div className="h-[420px] w-full">
              <BrandViolinChart brands={getBrands(0)} priceType={priceType} category="Dimmer Switches" onViolinClick={handleBrandViolinClick} />
            </div>
          </div>
          <div className="w-full">
            <h4 className="text-lg font-medium mb-3 text-center">💡 Light Switches</h4>
            <div className="h-[420px] w-full">
              <BrandViolinChart brands={getBrands(1)} priceType={priceType} category="Light Switches" onViolinClick={handleBrandViolinClick} />
            </div>
          </div>
        </div>
      </Card>
    </section>
  )
}
