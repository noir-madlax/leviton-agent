// Customer Satisfaction Data Hook

import { useState, useEffect } from 'react'
import { customerSatisfactionApi } from '../services/customer-satisfaction-api'
import type { CustomerSatisfactionResponse, CustomerSatisfactionFilters } from '../types/customer-satisfaction.types'

export function useCustomerSatisfactionData(
  projectId: string,
  filters?: CustomerSatisfactionFilters
) {
  const [data, setData] = useState<CustomerSatisfactionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) {
      setData(null)
      setError(null)
      return
    }

    const fetchData = async () => {
      setLoading(true)
      setError(null)

      try {
        const result = await customerSatisfactionApi.getCustomerSatisfactionData(projectId, filters)
        setData(result)
      } catch (err) {
        console.error('Failed to fetch customer satisfaction data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
        setData(null)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [projectId, JSON.stringify(filters)])

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
            const result = await customerSatisfactionApi.getCustomerSatisfactionData(projectId, filters)
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
