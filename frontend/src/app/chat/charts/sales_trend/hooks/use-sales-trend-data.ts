// Sales Trend Data Hook

import { useState, useEffect } from 'react'
import { salesTrendApi } from '../services/sales-trend-api'
import type { SalesTrendData, SalesTrendFilters } from '../types/sales-trend.types'

export function useSalesTrendData(
  projectId: string,
  filters?: SalesTrendFilters,
  dateRange?: { start_date: string; end_date: string },
  enabled = true
) {
  const [data, setData] = useState<SalesTrendData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId || !enabled) {
      setData(null)
      setError(null)
      setLoading(false)
      return
    }

    const fetchData = async () => {
      setLoading(true)
      setError(null)

      try {
        const result = await salesTrendApi.getSalesTrendData(projectId, filters, dateRange)
        setData(result)
      } catch (err) {
        console.error('Failed to fetch sales trend data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
        setData(null)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [projectId, JSON.stringify(filters), JSON.stringify(dateRange), enabled])

  return { 
    data, 
    loading, 
    error,
    refetch: () => {
      if (projectId) {
        const fetchData = async () => {
          setLoading(true)
          setError(null)
          try {
            const result = await salesTrendApi.getSalesTrendData(projectId, filters, dateRange)
            setData(result)
          } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error occurred')
          } finally {
            setLoading(false)
          }
        }
        fetchData()
      }
    }
  }
} 