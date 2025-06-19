import { Card } from "@/components/ui/card"
import { PieChart } from "@/components/analysis/charts/pie-chart"

interface ExecutiveSummaryProps {
  data: {
    totalProducts: number
    totalSalesVolume: number
    averagePrice: number
    totalBrands: number
    marketLeader: string
    marketLeaderShare: number
    marketLeaderProducts: number
    productDistribution: {
      name: string
      value: number
    }[]
  }
}

export function ExecutiveSummary({ data }: ExecutiveSummaryProps) {
  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📊 Executive Summary</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard value={data.totalProducts} label="Total Products" />
        <MetricCard value={data.totalSalesVolume.toLocaleString()} label="Total Sales Volume" />
        <MetricCard value={`$${data.averagePrice.toFixed(2)}`} label="Average Price" />
        <MetricCard value={data.totalBrands} label="Total Brands" />
      </div>

      <div className="bg-emerald-50 border-l-4 border-emerald-600 p-4 mb-6">
        <strong>Key Insight:</strong> The market leader is {data.marketLeader} with {data.marketLeaderShare.toFixed(2)}%
        market share and {data.marketLeaderProducts} products.
      </div>

      <Card className="p-6 bg-gray-50">
        <div className="h-80">
          <PieChart
            data={data.productDistribution}
            title="Product Distribution: Dimmers vs Light Switches"
            colors={["#FF6B6B", "#4ECDC4"]}
            annotation={`Total: ${data.totalProducts} products\nVolume: ${data.totalSalesVolume}\nAvg Price: $${data.averagePrice.toFixed(2)}`}
          />
        </div>
      </Card>
    </section>
  )
}

function MetricCard({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="bg-gray-100 p-5 rounded-lg text-center">
      <div className="text-2xl font-bold text-blue-600">{value}</div>
      <div className="text-gray-500 mt-1">{label}</div>
    </div>
  )
}
