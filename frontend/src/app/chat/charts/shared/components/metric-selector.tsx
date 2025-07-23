'use client'

import React from 'react'
import type { MetricType } from '../types/chart-common.types'

interface MetricSelectorProps {
  value: MetricType
  onChange: (metricType: MetricType) => void
  disabled?: boolean
}

export function MetricSelector({ value, onChange, disabled = false }: MetricSelectorProps) {
  return (
    <div className="flex items-center gap-4 mb-6">
      <label htmlFor="metric-type" className="text-sm font-medium text-gray-700">
        Display Metric:
      </label>
      <select
        id="metric-type"
        value={value}
        onChange={(e) => onChange(e.target.value as MetricType)}
        disabled={disabled}
        className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <option value="revenue">Revenue ($)</option>
        <option value="volume">Volume (Units)</option>
      </select>
      {disabled && (
        <span className="text-sm text-gray-500">Loading...</span>
      )}
    </div>
  )
} 