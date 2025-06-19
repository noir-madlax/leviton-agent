"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DashboardHeader } from "@/components/analysis/shared/dashboard-header"
import { BrandAnalysis } from "@/components/analysis/market-analysis/brand-analysis"
import { ProductAnalysis } from "@/components/analysis/market-analysis/product-analysis"
import { PricingAnalysis } from "@/components/analysis/market-analysis/pricing-analysis"
import { MarketInsights } from "@/components/analysis/market-analysis/market-insights"
import { PackagePreferenceAnalysis } from "@/components/analysis/market-analysis/package-preference-analysis"
import { ReviewInsights } from "@/components/analysis/review-insights/review-insights"
import { CompetitorAnalysis } from "@/components/analysis/competitor-analysis/competitor-analysis"
import { fetchDashboardData } from "@/components/analysis/data/dashboard-data"
import { ProductPanelProvider } from "@/components/analysis/contexts/product-panel-context"
import { ProductPanel } from "@/components/analysis/panels/product-panel"
import { ReviewPanelProvider } from "@/components/analysis/contexts/review-panel-context"
import { useEffect, useState } from 'react'

export function AnalysisContainer() {
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const dashboardData = await fetchDashboardData()
        setData(dashboardData)
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-lg">Loading analysis data...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-lg text-red-500">Failed to load analysis data</div>
      </div>
    )
  }

  return (
    <ProductPanelProvider>
      <ReviewPanelProvider>
        <div className="h-full overflow-auto bg-gray-50">
          <div className="container mx-auto max-w-7xl bg-white p-6 md:p-8 rounded-lg shadow-md my-6">
            <DashboardHeader />
            
            <Tabs defaultValue="market-analysis" className="mt-6">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="market-analysis">Market Analysis</TabsTrigger>
                <TabsTrigger value="review-insights">Review Insights by Product Category</TabsTrigger>
                <TabsTrigger value="competitor-analysis">Focal Products Analysis</TabsTrigger>
              </TabsList>
              
              <TabsContent value="market-analysis" className="mt-6">
                <BrandAnalysis data={data.brandAnalysis as any} productLists={data.productLists as any} />
                <ProductAnalysis data={data.productAnalysis as any} />
                <PricingAnalysis data={data.pricingAnalysis as any} productLists={data.productLists as any} productAnalysis={data.productAnalysis as any} />
                <MarketInsights data={data.marketInsights as any} productLists={data.productLists as any} />
                <PackagePreferenceAnalysis data={data.packagePreferenceAnalysis as any} productLists={data.productLists as any} />
              </TabsContent>  
              
              <TabsContent value="review-insights" className="mt-6">
                <ReviewInsights />
              </TabsContent>

              <TabsContent value="competitor-analysis" className="mt-6">
                <CompetitorAnalysis />
              </TabsContent>
            </Tabs>

            <div className="text-center text-gray-500 italic mt-8">
              Report Generated:{" "}
              {new Date().toLocaleDateString("en-US", {
                month: "long",
                day: "numeric",
                year: "numeric",
                hour: "numeric",
                minute: "numeric",
                hour12: true,
              })}
            </div>
          </div>
          
          <ProductPanel />
        </div>
      </ReviewPanelProvider>
    </ProductPanelProvider>
  )
} 