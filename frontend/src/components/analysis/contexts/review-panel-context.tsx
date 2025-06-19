"use client"

import React, { createContext, useContext, useState } from 'react'
import { Review } from '@/components/analysis/data/review-data'

interface ReviewPanelContextType {
  isOpen: boolean
  reviews: Review[]
  title: string
  subtitle?: string
  showFilters?: {
    sentiment?: boolean
    brand?: boolean
    rating?: boolean
    verified?: boolean
  }
  openPanel: (reviews: Review[], title: string, subtitle?: string, showFilters?: {
    sentiment?: boolean
    brand?: boolean
    rating?: boolean
    verified?: boolean
  }) => void
  closePanel: () => void
}

const ReviewPanelContext = createContext<ReviewPanelContextType | undefined>(undefined)

export function ReviewPanelProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [reviews, setReviews] = useState<Review[]>([])
  const [title, setTitle] = useState('')
  const [subtitle, setSubtitle] = useState<string | undefined>()
  const [showFilters, setShowFilters] = useState<{
    sentiment?: boolean
    brand?: boolean
    rating?: boolean
    verified?: boolean
  }>({ sentiment: true, brand: true, rating: true, verified: true })

  const openPanel = (
    newReviews: Review[], 
    newTitle: string, 
    newSubtitle?: string,
    newShowFilters?: {
      sentiment?: boolean
      brand?: boolean
      rating?: boolean
      verified?: boolean
    }
  ) => {
    setReviews(newReviews)
    setTitle(newTitle)
    setSubtitle(newSubtitle)
    setShowFilters(newShowFilters || { sentiment: true, brand: true, rating: true, verified: true })
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