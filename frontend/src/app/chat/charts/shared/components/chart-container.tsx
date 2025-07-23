'use client'

import React from 'react'
import { Card } from '@/components/ui/card'
import type { ChartContainerProps } from '../types/chart-common.types'

export function ChartContainer({ 
  title, 
  loading = false, 
  error = null, 
  children 
}: ChartContainerProps) {
  return (
    <Card className="p-6 bg-white shadow-sm">
      {/* Chart Title */}
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-800 border-l-4 border-blue-500 pl-4">
          {title}
        </h3>
      </div>

      {/* Chart Content */}
      <div className="relative">
        {loading && (
          <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10 rounded-lg">
            <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              <span className="text-gray-700 font-medium">Loading chart data...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-64 text-red-500">
            <div className="text-center">
              <div className="text-red-400 mb-2">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="font-medium">Error loading chart</p>
              <p className="text-sm text-gray-500 mt-1">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && children}
      </div>
    </Card>
  )
} 