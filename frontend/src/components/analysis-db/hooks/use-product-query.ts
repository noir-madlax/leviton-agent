/**
 * 产品查询 Hook - 用于图表点击时的产品数据获取
 */

import { useState, useCallback } from 'react'
import { useProductPanel } from '@/components/analysis-db/contexts/product-panel-context'
import { 
  productQueryService, 
  ProductFilterCriteria, 
  ProductQueryOptions, 
  ProductItem 
} from '@/components/analysis-db/services/product-query-service'

interface UseProductQueryReturn {
  loading: boolean
  error: string | null
  queryProducts: (
    projectId: string,
    filters: ProductFilterCriteria,
    options?: ProductQueryOptions
  ) => Promise<ProductItem[]>
  
  // 图表点击处理器
  handleViolinClick: (
    projectId: string,
    category: string,
    priceRange: { min: number, max: number },
    priceType?: 'sku' | 'unit'
  ) => Promise<void>
  
  handleBrandViolinClick: (
    projectId: string,
    brand: string,
    category?: string
  ) => Promise<void>
  
  handleMultiSegmentViolinClick: (
    projectId: string,
    segment: string,
    priceRange: { min: number, max: number }
  ) => Promise<void>
  
  handleBarClick: (
    projectId: string,
    segment: string
  ) => Promise<void>
  
  handleScatterClick: (
    projectId: string,
    productId: string
  ) => Promise<void>
}

export function useProductQuery(): UseProductQueryReturn {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { openPanel } = useProductPanel()

  const queryProducts = useCallback(async (
    projectId: string,
    filters: ProductFilterCriteria,
    options?: ProductQueryOptions
  ): Promise<ProductItem[]> => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await productQueryService.queryProducts(projectId, filters, options)
      return result.products
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const handleViolinClick = useCallback(async (
    projectId: string,
    category: string,
    priceRange: { min: number, max: number },
    priceType: 'sku' | 'unit' = 'sku'
  ) => {
    try {
      const products = await productQueryService.queryByViolinClick(
        projectId,
        category,
        priceRange,
        priceType
      )
      
      const title = `${category} Products`
      const subtitle = `Price range: $${priceRange.min.toFixed(2)} - $${priceRange.max.toFixed(2)} (${priceType.toUpperCase()})`
      
      openPanel(
        products,
        title,
        subtitle,
        { brand: true, category: true, priceRange: true, packSize: true }
      )
    } catch (err) {
      console.error('Error in violin click handler:', err)
      setError(err instanceof Error ? err.message : 'Failed to load products')
    }
  }, [openPanel])

  const handleBrandViolinClick = useCallback(async (
    projectId: string,
    brand: string,
    category?: string
  ) => {
    try {
      const products = await productQueryService.queryByBrandViolinClick(
        projectId,
        brand,
        category
      )
      
      const title = `${brand} Products`
      const subtitle = category ? `Category: ${category}` : 'All categories'
      
      openPanel(
        products,
        title,
        subtitle,
        { brand: false, category: true, priceRange: true, packSize: true }
      )
    } catch (err) {
      console.error('Error in brand violin click handler:', err)
      setError(err instanceof Error ? err.message : 'Failed to load products')
    }
  }, [openPanel])

  const handleMultiSegmentViolinClick = useCallback(async (
    projectId: string,
    segment: string,
    priceRange: { min: number, max: number }
  ) => {
    try {
      const products = await productQueryService.queryByMultiSegmentViolinClick(
        projectId,
        segment,
        priceRange
      )
      
      const title = `${segment} Products`
      const subtitle = `Price range: $${priceRange.min.toFixed(2)} - $${priceRange.max.toFixed(2)}`
      
      openPanel(
        products,
        title,
        subtitle,
        { brand: true, category: true, priceRange: true, packSize: true }
      )
    } catch (err) {
      console.error('Error in multi-segment violin click handler:', err)
      setError(err instanceof Error ? err.message : 'Failed to load products')
    }
  }, [openPanel])

  const handleBarClick = useCallback(async (
    projectId: string,
    segment: string
  ) => {
    try {
      const products = await productQueryService.queryByBarClick(projectId, segment)
      
      const title = `${segment} Products`
      const subtitle = `All products in ${segment}`
      
      openPanel(
        products,
        title,
        subtitle,
        { brand: true, category: true, priceRange: true, packSize: true }
      )
    } catch (err) {
      console.error('Error in bar click handler:', err)
      setError(err instanceof Error ? err.message : 'Failed to load products')
    }
  }, [openPanel])

  const handleScatterClick = useCallback(async (
    projectId: string,
    productId: string
  ) => {
    try {
      const products = await productQueryService.queryByScatterClick(projectId, productId)
      
      if (products.length > 0) {
        const product = products[0]
        const title = `Product Details`
        const subtitle = `${product.name} • ${product.brand}`
        
        openPanel(
          products,
          title,
          subtitle,
          { brand: false, category: false, priceRange: false, packSize: false }
        )
      }
    } catch (err) {
      console.error('Error in scatter click handler:', err)
      setError(err instanceof Error ? err.message : 'Failed to load product')
    }
  }, [openPanel])

  return {
    loading,
    error,
    queryProducts,
    handleViolinClick,
    handleBrandViolinClick,
    handleMultiSegmentViolinClick,
    handleBarClick,
    handleScatterClick
  }
}

// 便捷的导出 Hook，用于特定图表类型
export function useViolinProductQuery() {
  const { handleViolinClick, loading, error } = useProductQuery()
  return { handleViolinClick, loading, error }
}

export function useBrandViolinProductQuery() {
  const { handleBrandViolinClick, loading, error } = useProductQuery()
  return { handleBrandViolinClick, loading, error }
}

export function useMultiSegmentViolinProductQuery() {
  const { handleMultiSegmentViolinClick, loading, error } = useProductQuery()
  return { handleMultiSegmentViolinClick, loading, error }
}

export function useBarProductQuery() {
  const { handleBarClick, loading, error } = useProductQuery()
  return { handleBarClick, loading, error }
}

export function useScatterProductQuery() {
  const { handleScatterClick, loading, error } = useProductQuery()
  return { handleScatterClick, loading, error }
}
