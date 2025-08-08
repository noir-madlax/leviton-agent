"use client"

import React from 'react'
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { useChartSections } from "@/components/integrated-dashboard/hooks/use-chart-sections"
import { useChartsT } from "@/i18n/hooks"

// 🆕 导入独立的图表组件
import { PriceDistributionOverview } from "./price-distribution-overview"
import { PriceDistributionByTypeChart } from "./price-distribution-by-type"
import { PriceVsRevenueChart } from "./price-vs-revenue-chart"
import { BrandPriceDistributionChart } from "./brand-price-distribution-chart"


interface PricingAnalysisProps {
  projectId?: string
  initialFilters?: ProjectFilters
}

export function PricingAnalysis({ projectId, initialFilters }: PricingAnalysisProps) {
  const chartsT = useChartsT()
  
  // Get chart sections configuration for conditional rendering
  const { shouldShowChart } = useChartSections('pricing-analysis', projectId || '')

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-red-500 pl-4 mb-6">
          💰 {chartsT('pricingAnalysis')}
        </h2>

      {/* 🆕 Price Distribution Overview - 独立组件 */}
      {shouldShowChart('price-distribution-overview') && (
        <PriceDistributionOverview
          projectId={projectId}
          initialFilters={initialFilters}
        />
      )}

      {/* 🆕 Price Distribution by Product Type - 独立组件 */}
      {shouldShowChart('price-distribution-by-type') && (
        <PriceDistributionByTypeChart
          projectId={projectId}
          initialFilters={initialFilters}
        />
      )}

      {/* 🆕 Brand Price Distribution - 独立组件 */}
      {shouldShowChart('price-distribution-by-brands') && (
        <BrandPriceDistributionChart
          projectId={projectId}
          initialFilters={initialFilters}
        />
      )}

      {/* 🆕 Price vs Revenue Distribution - 独立组件 (放到页面最后) */}
      {shouldShowChart('price-vs-revenue') && (
        <PriceVsRevenueChart
          projectId={projectId}
          initialFilters={initialFilters}
        />
      )}
    </section>
  )
}
