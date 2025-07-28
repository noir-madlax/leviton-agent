"use client"

import { useCallback } from 'react'
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
    }
  ) => Promise<void>
  
  // 图表点击处理器
  handleCategoryClick: (
    projectId: string,
    categoryId: number,
    categoryName: string,
    chartType?: 'pain-points' | 'delights' | 'use-case',
    filters?: {
      categories?: string[]
      brands?: string[]
      segments?: string[]
      extend_fields?: Record<string, any>
      asins?: string[]
    }
  ) => Promise<void>
}

export function useReviewPanelQuery(): UseReviewPanelQueryReturn {
  const { openPanel } = useReviewPanel()

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
    filters?: {
      categories?: string[]
      brands?: string[]
      segments?: string[]
      extend_fields?: Record<string, any>
      asins?: string[]
    }
  ) => {
    try {
      // 获取第一页数据
      const result = await databaseService.getReviewsByCategory(
        projectId,
        categoryId,
        {
          limit: 500, // 初始加载500条评论
          offset: 0,
          sortBy: 'review_id',
          sortOrder: 'desc'
        },
        filters // 传递过滤器参数
      )

      // 转换数据格式为 Review 接口
      const reviews: Review[] = result.data.reviews.map(item => ({
        id: item.review_id.toString(),
        productId: item.product_id,
        text: item.review_text,
        sentiment: item.sentiment,
        category: item.category_name,
        aspect: item.category_name, // 使用 category_name 作为 aspect
        rating: item.rating,
        verified: item.verified,
        date: item.review_date,
        brand: item.brand
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
    }
  }, [openPanel])

  const handleCategoryClick = useCallback(async (
    projectId: string,
    categoryId: number,
    categoryName: string,
    chartType: 'pain-points' | 'delights' | 'use-case' = 'pain-points',
    filters?: {
      categories?: string[]
      brands?: string[]
      segments?: string[]
      extend_fields?: Record<string, any>
      asins?: string[]
    }
  ) => {
    const titles = {
      'pain-points': `${categoryName} - Pain Points`,
      'delights': `${categoryName} - Customer Delights`,
      'use-case': `${categoryName} - Use Case Reviews`
    }

    const subtitles = {
      'pain-points': `Customer feedback about "${categoryName}" issues and concerns`,
      'delights': `Positive customer feedback about "${categoryName}"`,
      'use-case': `Customer reviews related to "${categoryName}" use cases`
    }

    await openPanelWithCategoryId(
      projectId,
      categoryId,
      categoryName,
      titles[chartType],
      subtitles[chartType],
      undefined, // showFilters 使用默认值
      filters // 传递过滤器参数
    )
  }, [openPanelWithCategoryId])

  return {
    openPanelWithCategoryId,
    handleCategoryClick
  }
}
