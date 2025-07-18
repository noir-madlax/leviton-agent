"use client"

import { createContext, useContext, useState, ReactNode } from 'react'
import type { Product } from '@/components/analysis-db/types/analysis'

// 产品筛选条件接口
export interface ProductFilterCriteria {
  categories?: string[]
  brands?: string[]
  segments?: string[]
  extend_fields?: Record<string, any>
  exclude_asins?: string[]
}

// 浮窗显示选项
export interface ProductPanelShowFilters {
  brand?: boolean
  category?: boolean
  priceRange?: boolean
  packSize?: boolean
}

// 打开浮窗的参数
export interface OpenPanelParams {
  projectId: string
  filters: ProductFilterCriteria
  title: string
  subtitle?: string
  showFilters?: ProductPanelShowFilters
}

interface ProductPanelContextType {
  isOpen: boolean
  products: Product[]
  title: string
  subtitle?: string
  loading: boolean
  error: string | null
  showFilters?: ProductPanelShowFilters

  // 新的方法
  openPanel: (params: OpenPanelParams) => Promise<void>

  closePanel: () => void
}

const ProductPanelContext = createContext<ProductPanelContextType | undefined>(undefined)

export function ProductPanelProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [products, setProducts] = useState<Product[]>([])
  const [title, setTitle] = useState('')
  const [subtitle, setSubtitle] = useState<string | undefined>()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState<ProductPanelShowFilters>({
    brand: true,
    category: true,
    priceRange: true,
    packSize: true
  })

  // 新的方法：根据查询参数获取产品
  const openPanel = async (params: OpenPanelParams) => {
    try {
      setLoading(true)
      setError(null)
      setTitle(params.title)
      setSubtitle(params.subtitle)
      setShowFilters(params.showFilters || { brand: true, category: true, priceRange: true, packSize: true })

      // 根据查询参数获取产品
      const { productQueryService } = await import('@/components/analysis-db/services/product-query-service')

      const result = await productQueryService.queryProducts(
        params.projectId,
        params.filters,
        {
          limit: 200, // 默认限制
          sort_by: 'revenue',
          sort_order: 'desc'
        }
      )

      setProducts(result.products.map(product => ({
        ...product,
        url: product.url || ''  // Handle optional url field
      })))
      setIsOpen(true)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load products'
      setError(errorMessage)
      console.error('Error opening product panel:', err)
    } finally {
      setLoading(false)
    }
  }

  const closePanel = () => {
    setIsOpen(false)
    setError(null)
  }

  return (
    <ProductPanelContext.Provider value={{
      isOpen,
      products,
      title,
      subtitle,
      loading,
      error,
      showFilters,
      openPanel,
      closePanel
    }}>
      {children}
    </ProductPanelContext.Provider>
  )
}

export function useProductPanel() {
  const context = useContext(ProductPanelContext)
  if (context === undefined) {
    throw new Error('useProductPanel must be used within a ProductPanelProvider')
  }
  return context
} 