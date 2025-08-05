"use client"

import { useCallback, useState } from 'react'
import { useReviewPanel } from '@/components/analysis-db/contexts/review-panel-context'
import { databaseService } from '@/components/analysis-db/data/database-service'
import { Review } from '@/components/analysis-db/types/analysis'

export interface UseReviewPanelQueryReturn {
  // 基于 category_id 获取评论详情
  openPanelWithCategoryId: (
    projectId: string,
    categoryId: number,
    categoryName: string,
    title?: string,
    subtitle?: string,
    showFilters?: {
      sentiment?: boolean
      brand?: boolean
      rating?: boolean
      verified?: boolean
    },
    aspectTypes?: string[]
  ) => Promise<void>
  
  // 图表点击处理器
  handleCategoryClick: (
    projectId: string,
    categoryId: number,
    categoryName: string,
    aspectTypes?: string[],
    filters?: {
      categories?: string[]
      brands?: string[]
      segments?: string[]
      extend_fields?: Record<string, any>
      asins?: string[]
    }
  ) => Promise<void>
  
  // Loading状态
  isLoading: boolean
}

export function useReviewPanelQuery(): UseReviewPanelQueryReturn {
  const { openPanel } = useReviewPanel()
  const [isLoading, setIsLoading] = useState(false)

  // 🆕 工具函数：将后端sentiment格式映射到frontend格式 (完全复用竞品分析)
  const mapSentiment = (backendSentiment: string): 'positive' | 'negative' | 'neutral' => {
    if (backendSentiment === '+') return 'positive'
    if (backendSentiment === '-') return 'negative'
    return 'neutral'
  }

  // 🆕 工具函数：基于aspects计算总体sentiment (完全复用竞品分析)
  const calculateOverallSentiment = (aspects: Array<{ sentiment: string }>): 'positive' | 'negative' | 'neutral' => {
    if (!aspects.length) return 'neutral'
    const positiveCount = aspects.filter(a => a.sentiment === '+').length
    const negativeCount = aspects.filter(a => a.sentiment === '-').length
    
    if (positiveCount > negativeCount) return 'positive'
    if (negativeCount > positiveCount) return 'negative'
    return 'neutral'
  }

  const openPanelWithCategoryId = useCallback(async (
    projectId: string,
    categoryId: number,
    categoryName: string,
    title?: string,
    subtitle?: string,
    showFilters?: {
      sentiment?: boolean
      brand?: boolean
      rating?: boolean
      verified?: boolean
    },
    aspectTypes?: string[]
  ) => {
    try {
      setIsLoading(true)
      // 获取第一页数据
      const result = await databaseService.getReviewsByCategory(
        projectId,
        categoryId,
        {
          limit: 500, // 初始加载500条评论
          offset: 0,
          sortBy: 'review_id',
          sortOrder: 'desc',
          aspectTypes: aspectTypes // 传递aspectTypes参数
        },
        {} // 传递过滤器参数
      )

      // 从API返回结果的顶层获取category name (参考图1的实现方式)
      const categoryNameFromApi = result.data.category_info?.category_name || categoryName;

      // 转换数据格式为 Review 接口 (完全参考竞品分析的数据转换逻辑)
      const reviews: Review[] = result.data.reviews.map(item => ({
        id: item.review_id.toString(),
        productId: item.product_id,
        text: item.review_text,
        sentiment: item.sentiment,
        category: categoryNameFromApi, // ✅ 修复：使用从顶层获取的category name
        aspect: item.category_name, // 使用 category_name 作为 aspect
        rating: item.rating,
        verified: item.verified,
        date: item.review_date,
        brand: item.brand,
        // 🆕 新增：完整的aspects信息转换 (完全复用竞品分析的实现)
        aspects: item.aspects?.map(aspect => ({
          description: aspect.aspect_description,
          sentiment: mapSentiment(aspect.sentiment),
          aspect_type: aspect.aspect_type
        })) || []
      }))

      // 打开面板
      openPanel(
        reviews,
        title || `${categoryName} - Customer Reviews`,
        subtitle || `${result.data.total_count} reviews found for "${categoryName}"`,
        showFilters || { sentiment: true, brand: true, rating: true, verified: true }
      )
    } catch (error) {
      console.error('Error fetching reviews by category:', error)
      // 显示错误状态
      openPanel(
        [],
        title || `${categoryName} - Customer Reviews`,
        'Failed to load reviews. Please try again.',
        showFilters || { sentiment: true, brand: true, rating: true, verified: true }
      )
    } finally {
      setIsLoading(false)
    }
  }, [openPanel])

  const handleCategoryClick = useCallback(async (
    projectId: string,
    categoryId: number,
    categoryName: string,
    aspectTypes: string[] = ['phy', 'perf'],
    filters?: {
      categories?: string[]
      brands?: string[]
      segments?: string[]
      extend_fields?: Record<string, any>
      asins?: string[]
    }
  ) => {
    // Generate title and subtitle based on aspect types
    const aspectTypeNames = aspectTypes.map(type => {
      switch(type) {
        case 'use': return 'Use Cases'
        case 'phy': return 'Physical Features'
        case 'perf': return 'Performance'
        default: return type
      }
    }).join(', ')

    const title = `${categoryName} - ${aspectTypeNames}`
    const subtitle = `Customer reviews related to "${categoryName}" ${aspectTypeNames.toLowerCase()}`

    await openPanelWithCategoryId(
      projectId,
      categoryId,
      categoryName,
      title,
      subtitle,
      undefined, // showFilters 使用默认值
      aspectTypes, // 传递aspectTypes
      filters // 传递过滤器参数
    )
  }, [openPanelWithCategoryId])

  return {
    openPanelWithCategoryId,
    handleCategoryClick,
    isLoading
  }
}
