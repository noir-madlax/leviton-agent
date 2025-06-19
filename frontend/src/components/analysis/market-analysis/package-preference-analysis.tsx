'use client'

import { useState } from 'react'
import { PieChart, Pie, Cell, Legend, ResponsiveContainer, Tooltip } from 'recharts'
import { MetricTypeSelector, type MetricType } from "@/components/analysis/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis/contexts/product-panel-context"

interface PackagePreferenceData {
  sameProductComparison: {
    productName: string;
    packSize: string;
    packCount: number;
    salesVolume: number;
    price: number;
    unitPrice: number;
  }[];
  packageDistribution: {
    packSize: string;
    count: number;
    percentage: number;
    salesVolume: number;
  }[];
  dimmerSwitches: {
    packSize: string;
    count: number;
    percentage: number;
    salesVolume: number;
    salesRevenue: number;
  }[];
  lightSwitches: {
    packSize: string;
    count: number;
    percentage: number;
    salesVolume: number;
    salesRevenue: number;
  }[];
}

export function PackagePreferenceAnalysis({ 
  data, 
  productLists 
}: { 
  data: PackagePreferenceData
  productLists: {
    byBrand: Record<string, any[]>
    bySegment: Record<string, any[]>
    byPackageSize: Record<string, any[]>
  }
}) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")
  const { openPanel } = useProductPanel()

  // Gentle, pastel color palette
  const colors = [
    '#A8D5BA', // Soft mint green
    '#F4C2A1', // Warm peach
    '#B8C5D6', // Soft lavender blue
    '#F7D794', // Gentle yellow
    '#E8A4C9', // Soft pink
    '#C7D2CC', // Sage green
    '#F2E2CE', // Cream beige
    '#D4B5D4'  // Light purple
  ]

  // Transform data based on selected metric
  const getDimmerChartData = () => {
    return data.dimmerSwitches.map(item => ({
      name: item.packSize,
      value: metricType === "revenue" ? item.salesRevenue : item.salesVolume,
      percentage: item.percentage
    }))
  }

  const getSwitchChartData = () => {
    return data.lightSwitches.map(item => ({
      name: item.packSize,
      value: metricType === "revenue" ? item.salesRevenue : item.salesVolume,
      percentage: item.percentage
    }))
  }

  const formatValue = (value: number) => {
    return metricType === "revenue" ? `$${value.toLocaleString()}` : value.toLocaleString()
  }

  const titleSuffix = metricType === "revenue" ? "Revenue" : "Volume (Packages Sold)"

  const handlePieClick = (data: any) => {
    if (data && data.name) {
      const packSize = data.name
      const products = productLists.byPackageSize[packSize] || []
      openPanel(
        products,
        `${packSize} Products`,
        `All products sold in ${packSize} packages`,
        { brand: true, category: true, priceRange: true, packSize: false }
      )
    }
  }

  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name }: any) => {
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    if (percent < 0.05) return null // Don't show labels for slices < 5%

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="12"
        fontWeight="bold"
        style={{ textShadow: '1px 1px 1px rgba(0,0,0,0.7)' }}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    )
  }

  // Custom tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-300 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-800">{`Package Size: ${label}`}</p>
          <p className="text-blue-600">
            {metricType === "revenue" ? "Revenue: " : "Packages Sold: "}
            <span className="font-medium">{formatValue(data.value)}</span>
          </p>
          <p className="text-green-600">
            Percentage: <span className="font-medium">{data.percentage.toFixed(1)}%</span>
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">
        📦 Package Preference Analysis
      </h2>

      <MetricTypeSelector onChange={setMetricType} value={metricType} />

      <h3 className="text-xl font-semibold mb-4">Package Size Distribution by {titleSuffix}</h3>
      
      {/* Clarification note */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
        <div className="flex">
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              <strong>Note:</strong> {metricType === "revenue" ? 
                "Revenue shows total sales value for each package size." : 
                "Volume shows the number of packages sold (not individual units). For example, if 10 customers buy a '2 Pack', the volume would be 10 packages sold, representing 20 individual units total."
              }
            </p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Dimmer Switches Pie Chart */}
        <div className="bg-gray-50 p-6 rounded-lg">
          <h4 className="text-lg font-medium mb-4 text-center">🔆 Dimmer Switches - Package Size by {titleSuffix}</h4>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={getDimmerChartData()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                  onClick={handlePieClick}
                >
                  {getDimmerChartData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  verticalAlign="bottom" 
                  height={36}
                  formatter={(value, entry) => {
                    const item = getDimmerChartData().find(d => d.name === value)
                    return `${value} (${item?.percentage.toFixed(1)}%)`
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Light Switches Pie Chart */}
        <div className="bg-gray-50 p-6 rounded-lg">
          <h4 className="text-lg font-medium mb-4 text-center">💡 Light Switches - Package Size by {titleSuffix}</h4>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={getSwitchChartData()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                  onClick={handlePieClick}
                >
                  {getSwitchChartData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  verticalAlign="bottom" 
                  height={36}
                  formatter={(value, entry) => {
                    const item = getSwitchChartData().find(d => d.name === value)
                    return `${value} (${item?.percentage.toFixed(1)}%)`
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  )
} 