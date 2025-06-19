"use client"

import React, { createContext, useContext, useState } from 'react'
import type { Product } from '@/components/analysis/types/analysis'

interface ProductPanelContextType {
  isOpen: boolean
  products: Product[]
  title: string
  subtitle?: string
  showFilters?: {
    brand?: boolean
    category?: boolean
    priceRange?: boolean
    packSize?: boolean
  }
  openPanel: (products: Product[], title: string, subtitle?: string, showFilters?: {
    brand?: boolean
    category?: boolean
    priceRange?: boolean
    packSize?: boolean
  }) => void
  closePanel: () => void
}

const ProductPanelContext = createContext<ProductPanelContextType | undefined>(undefined)

export function ProductPanelProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [products, setProducts] = useState<Product[]>([])
  const [title, setTitle] = useState('')
  const [subtitle, setSubtitle] = useState<string | undefined>()
  const [showFilters, setShowFilters] = useState<{
    brand?: boolean
    category?: boolean
    priceRange?: boolean
    packSize?: boolean
  }>({ brand: true, category: true, priceRange: true, packSize: true })

  const openPanel = (
    newProducts: Product[], 
    newTitle: string, 
    newSubtitle?: string,
    newShowFilters?: {
      brand?: boolean
      category?: boolean
      priceRange?: boolean
      packSize?: boolean
    }
  ) => {
    setProducts(newProducts)
    setTitle(newTitle)
    setSubtitle(newSubtitle)
    setShowFilters(newShowFilters || { brand: true, category: true, priceRange: true, packSize: true })
    setIsOpen(true)
  }

  const closePanel = () => {
    setIsOpen(false)
  }

  return (
    <ProductPanelContext.Provider value={{
      isOpen,
      products,
      title,
      subtitle,
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