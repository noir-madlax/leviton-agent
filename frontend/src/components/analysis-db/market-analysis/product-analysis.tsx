"use client"

import { Card } from "@/components/ui/card"

export function ProductAnalysis() {
  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📊 Product Analysis</h2>
      
      <Card className="p-6 bg-gray-50">
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">This section has been moved to Product Deep Dive</p>
          <p className="text-gray-400 text-sm">Please use the Market Insights tab for product deep dive analysis</p>
        </div>
      </Card>
    </section>
  )
}
