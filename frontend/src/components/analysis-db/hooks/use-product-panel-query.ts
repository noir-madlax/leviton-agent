/**
 * 产品浮窗查询 Hook - 简化图表点击时的产品浮窗调用
 */

import { useCallback } from 'react'
import { useProductPanel, ProductFilterCriteria, ProductPanelShowFilters } from '@/components/analysis-db/contexts/product-panel-context'

export interface UseProductPanelQueryReturn {
  // 基础方法
  openPanelWithFilters: (
    projectId: string,
    filters: ProductFilterCriteria,
    title: string,
    subtitle?: string,
    showFilters?: ProductPanelShowFilters
  ) => Promise<void>
  
  // 图表点击处理器
  handleViolinClick: (
    projectId: string,
    category: string,
    title?: string,
    subtitle?: string
  ) => Promise<void>
  
  handleBrandViolinClick: (
    projectId: string,
    brand: string,
    category?: string,
    title?: string,
    subtitle?: string
  ) => Promise<void>
  
  handleMultiSegmentViolinClick: (
    projectId: string,
    segment: string,
    title?: string,
    subtitle?: string
  ) => Promise<void>
  
  handleBarClick: (
    projectId: string,
    segment: string,
    title?: string,
    subtitle?: string
  ) => Promise<void>
  
  handleCategoryClick: (
    projectId: string,
    category: string,
    title?: string,
    subtitle?: string
  ) => Promise<void>
  
  handleBrandClick: (
    projectId: string,
    brand: string,
    title?: string,
    subtitle?: string
  ) => Promise<void>
  
  handleSegmentClick: (
    projectId: string,
    segment: string,
    title?: string,
    subtitle?: string
  ) => Promise<void>
  
  // 组合筛选
  handleMultipleFiltersClick: (
    projectId: string,
    filters: ProductFilterCriteria,
    title: string,
    subtitle?: string,
    showFilters?: ProductPanelShowFilters
  ) => Promise<void>
  
  // 状态
  loading: boolean
  error: string | null
}

export function useProductPanelQuery(): UseProductPanelQueryReturn {
  const { openPanel, loading, error } = useProductPanel()

  const openPanelWithFilters = useCallback(async (
    projectId: string,
    filters: ProductFilterCriteria,
    title: string,
    subtitle?: string,
    showFilters?: ProductPanelShowFilters
  ) => {
    await openPanel({
      projectId,
      filters,
      title,
      subtitle,
      showFilters
    })
  }, [openPanel])

  const handleViolinClick = useCallback(async (
    projectId: string,
    category: string,
    title?: string,
    subtitle?: string
  ) => {
    await openPanelWithFilters(
      projectId,
      { categories: [category] },
      title || `${category} Products`,
      subtitle || `All products in ${category}`,
      { brand: true, category: false, priceRange: true, packSize: true }
    )
  }, [openPanelWithFilters])

  const handleBrandViolinClick = useCallback(async (
    projectId: string,
    brand: string,
    category?: string,
    title?: string,
    subtitle?: string
  ) => {
    const filters: ProductFilterCriteria = { brands: [brand] }
    if (category) {
      filters.categories = [category]
    }
    
    await openPanelWithFilters(
      projectId,
      filters,
      title || `${brand} Products`,
      subtitle || (category ? `${brand} products in ${category}` : `All ${brand} products`),
      { brand: false, category: true, priceRange: true, packSize: true }
    )
  }, [openPanelWithFilters])

  const handleMultiSegmentViolinClick = useCallback(async (
    projectId: string,
    segment: string,
    title?: string,
    subtitle?: string
  ) => {
    await openPanelWithFilters(
      projectId,
      { segments: [segment] },
      title || `${segment} Products`,
      subtitle || `All products in ${segment} segment`,
      { brand: true, category: true, priceRange: true, packSize: true }
    )
  }, [openPanelWithFilters])

  const handleBarClick = useCallback(async (
    projectId: string,
    segment: string,
    title?: string,
    subtitle?: string
  ) => {
    await openPanelWithFilters(
      projectId,
      { segments: [segment] },
      title || `${segment} Products`,
      subtitle || `All products in ${segment} segment`,
      { brand: true, category: true, priceRange: true, packSize: true }
    )
  }, [openPanelWithFilters])

  const handleCategoryClick = useCallback(async (
    projectId: string,
    category: string,
    title?: string,
    subtitle?: string
  ) => {
    await openPanelWithFilters(
      projectId,
      { categories: [category] },
      title || `${category} Products`,
      subtitle || `All products in ${category}`,
      { brand: true, category: false, priceRange: true, packSize: true }
    )
  }, [openPanelWithFilters])

  const handleBrandClick = useCallback(async (
    projectId: string,
    brand: string,
    title?: string,
    subtitle?: string
  ) => {
    await openPanelWithFilters(
      projectId,
      { brands: [brand] },
      title || `${brand} Products`,
      subtitle || `All ${brand} products`,
      { brand: false, category: true, priceRange: true, packSize: true }
    )
  }, [openPanelWithFilters])

  const handleSegmentClick = useCallback(async (
    projectId: string,
    segment: string,
    title?: string,
    subtitle?: string
  ) => {
    await openPanelWithFilters(
      projectId,
      { segments: [segment] },
      title || `${segment} Products`,
      subtitle || `All products in ${segment} segment`,
      { brand: true, category: true, priceRange: true, packSize: true }
    )
  }, [openPanelWithFilters])

  const handleMultipleFiltersClick = useCallback(async (
    projectId: string,
    filters: ProductFilterCriteria,
    title: string,
    subtitle?: string,
    showFilters?: ProductPanelShowFilters
  ) => {
    await openPanelWithFilters(
      projectId,
      filters,
      title,
      subtitle,
      showFilters
    )
  }, [openPanelWithFilters])

  return {
    openPanelWithFilters,
    handleViolinClick,
    handleBrandViolinClick,
    handleMultiSegmentViolinClick,
    handleBarClick,
    handleCategoryClick,
    handleBrandClick,
    handleSegmentClick,
    handleMultipleFiltersClick,
    loading,
    error
  }
}

// 便捷的导出函数，用于特定场景
export function useViolinProductPanel() {
  const { handleViolinClick, loading, error } = useProductPanelQuery()
  return { handleViolinClick, loading, error }
}

export function useBrandViolinProductPanel() {
  const { handleBrandViolinClick, loading, error } = useProductPanelQuery()
  return { handleBrandViolinClick, loading, error }
}

export function useMultiSegmentViolinProductPanel() {
  const { handleMultiSegmentViolinClick, loading, error } = useProductPanelQuery()
  return { handleMultiSegmentViolinClick, loading, error }
}

export function useBarProductPanel() {
  const { handleBarClick, loading, error } = useProductPanelQuery()
  return { handleBarClick, loading, error }
}

export function useCategoryProductPanel() {
  const { handleCategoryClick, loading, error } = useProductPanelQuery()
  return { handleCategoryClick, loading, error }
}

export function useBrandProductPanel() {
  const { handleBrandClick, loading, error } = useProductPanelQuery()
  return { handleBrandClick, loading, error }
}

export function useSegmentProductPanel() {
  const { handleSegmentClick, loading, error } = useProductPanelQuery()
  return { handleSegmentClick, loading, error }
}
