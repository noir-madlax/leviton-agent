"use client"

import { createContext, useContext, useState } from 'react'
import { Review } from '@/components/analysis-db/types/analysis'

interface ReviewPanelContextType {
  isOpen: boolean
  reviews: Review[]
  title: string
  subtitle?: string
  projectId?: string // 🆕 Added for API calls
  categoryId?: number // 🆕 Added for API calls
  showFilters?: {
    causeAnalysis?: boolean // 🆕 Replaced sentiment
    aspectType?: boolean    // 🆕 New filter
    rating?: boolean
    verified?: boolean
    brand?: boolean // 🔄 Keep logic but hide by default
  }
  openPanel: (
    reviews: Review[], 
    title: string, 
    subtitle?: string,
    options?: {
      projectId?: string
      categoryId?: number
      showFilters?: {
        causeAnalysis?: boolean
        aspectType?: boolean
        rating?: boolean
        verified?: boolean
        brand?: boolean
      }
    }
  ) => void
  closePanel: () => void
}

const ReviewPanelContext = createContext<ReviewPanelContextType | undefined>(undefined)

export function ReviewPanelProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [reviews, setReviews] = useState<Review[]>([])
  const [title, setTitle] = useState('')
  const [subtitle, setSubtitle] = useState<string | undefined>()
  const [projectId, setProjectId] = useState<string | undefined>()
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [showFilters, setShowFilters] = useState<{
    causeAnalysis?: boolean
    aspectType?: boolean
    rating?: boolean
    verified?: boolean
    brand?: boolean
  }>({ causeAnalysis: true, aspectType: true, rating: true, verified: true, brand: false })

  const openPanel = (
    newReviews: Review[], 
    newTitle: string, 
    newSubtitle?: string,
    options?: {
      projectId?: string
      categoryId?: number
      showFilters?: {
        causeAnalysis?: boolean
        aspectType?: boolean
        rating?: boolean
        verified?: boolean
        brand?: boolean
      }
    }
  ) => {
    setReviews(newReviews)
    setTitle(newTitle)
    setSubtitle(newSubtitle)
    setProjectId(options?.projectId)
    setCategoryId(options?.categoryId)
    setShowFilters(options?.showFilters || { causeAnalysis: true, aspectType: true, rating: true, verified: true, brand: false })
    setIsOpen(true)
  }

  const closePanel = () => {
    setIsOpen(false)
  }

  return (
    <ReviewPanelContext.Provider value={{
      isOpen,
      reviews,
      title,
      subtitle,
      projectId,
      categoryId,
      showFilters,
      openPanel,
      closePanel
    }}>
      {children}
    </ReviewPanelContext.Provider>
  )
}

export function useReviewPanel() {
  const context = useContext(ReviewPanelContext)
  if (context === undefined) {
    throw new Error('useReviewPanel must be used within a ReviewPanelProvider')
  }
  return context
} 