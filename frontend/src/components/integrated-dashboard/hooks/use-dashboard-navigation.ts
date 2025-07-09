"use client"

import { useState, useCallback } from 'react'

export function useDashboardNavigation() {
  const [activeTab, setActiveTab] = useState('brand-analysis')

  const handleTabChange = useCallback((tab: string) => {
    setActiveTab(tab)
  }, [])

  return {
    activeTab,
    setActiveTab: handleTabChange
  }
} 