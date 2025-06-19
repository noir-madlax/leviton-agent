interface SummaryMetricsProps {
  data: {
    priceRange: string
    avgVolumePerProduct: number
    medianPrice: number
    majorBrands: number
  }
}

export function SummaryMetrics({ data }: SummaryMetricsProps) {
  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📈 Summary Metrics</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard value={data.priceRange} label="Price Range" />
        <MetricCard value={data.avgVolumePerProduct.toFixed(2)} label="Avg Volume/Product" />
        <MetricCard value={`$${data.medianPrice.toFixed(2)}`} label="Median Price" />
        <MetricCard value={data.majorBrands} label="Major Brands (5%+ share)" />
      </div>

      <div className="text-center text-gray-500 italic mt-8">End of Report</div>
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
