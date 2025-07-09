"use client"

import React from 'react'

interface ThumbnailPreviewProps {
  type: string
  className?: string
}

export function ThumbnailPreview({ type, className = "w-8 h-6" }: ThumbnailPreviewProps) {
  const thumbnails = {
    'brand-analysis': <MiniBarChart />,
    'product-analysis': <MiniScatterChart />,
    'pricing-analysis': <MiniPieChart />,
    'market-insights': <MiniLineChart />,
    'package-preference': <MiniStackedBarChart />,
    'review-insights': <MiniRadarChart />,
    'competitor-analysis': <MiniHeatmapChart />
  }
  
  return (
    <div className={`${className} border rounded bg-gray-50 flex items-center justify-center overflow-hidden`}>
      {thumbnails[type as keyof typeof thumbnails] || <MiniBarChart />}
    </div>
  )
}

function MiniBarChart() {
  return (
    <svg width="20" height="14" viewBox="0 0 20 14" className="text-blue-500">
      <rect x="2" y="9" width="2" height="4" fill="currentColor" opacity="0.8" />
      <rect x="5" y="6" width="2" height="7" fill="currentColor" opacity="0.9" />
      <rect x="8" y="4" width="2" height="9" fill="currentColor" />
      <rect x="11" y="7" width="2" height="6" fill="currentColor" opacity="0.7" />
      <rect x="14" y="5" width="2" height="8" fill="currentColor" opacity="0.8" />
    </svg>
  )
}

function MiniScatterChart() {
  return (
    <svg width="20" height="14" viewBox="0 0 20 14" className="text-green-500">
      <circle cx="3" cy="10" r="1" fill="currentColor" opacity="0.8" />
      <circle cx="6" cy="7" r="1" fill="currentColor" opacity="0.9" />
      <circle cx="9" cy="5" r="1" fill="currentColor" />
      <circle cx="12" cy="8" r="1" fill="currentColor" opacity="0.7" />
      <circle cx="15" cy="6" r="1" fill="currentColor" opacity="0.8" />
      <circle cx="7" cy="11" r="1" fill="currentColor" opacity="0.6" />
      <circle cx="13" cy="4" r="1" fill="currentColor" opacity="0.9" />
      <circle cx="16" cy="9" r="1" fill="currentColor" opacity="0.7" />
    </svg>
  )
}

function MiniPieChart() {
  return (
    <svg width="20" height="14" viewBox="0 0 20 14" className="text-purple-500">
      <circle cx="10" cy="7" r="5" fill="currentColor" opacity="0.2" />
      <path 
        d="M 10 7 L 10 2 A 5 5 0 0 1 13.66 5.5 Z" 
        fill="currentColor" 
        opacity="0.8" 
      />
      <path 
        d="M 10 7 L 13.66 5.5 A 5 5 0 0 1 13.66 8.5 Z" 
        fill="currentColor" 
        opacity="0.6" 
      />
      <path 
        d="M 10 7 L 13.66 8.5 A 5 5 0 0 1 6.34 8.5 Z" 
        fill="currentColor" 
        opacity="0.9" 
      />
    </svg>
  )
}

function MiniLineChart() {
  return (
    <svg width="20" height="14" viewBox="0 0 20 14" className="text-orange-500">
      <polyline 
        points="2,10 5,7 8,8 11,5 14,6 17,4" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="1.5" 
        opacity="0.8"
      />
      <circle cx="2" cy="10" r="1" fill="currentColor" />
      <circle cx="5" cy="7" r="1" fill="currentColor" />
      <circle cx="8" cy="8" r="1" fill="currentColor" />
      <circle cx="11" cy="5" r="1" fill="currentColor" />
      <circle cx="14" cy="6" r="1" fill="currentColor" />
      <circle cx="17" cy="4" r="1" fill="currentColor" />
    </svg>
  )
}

function MiniStackedBarChart() {
  return (
    <svg width="20" height="14" viewBox="0 0 20 14" className="text-teal-500">
      <rect x="3" y="8" width="2" height="3" fill="currentColor" opacity="0.9" />
      <rect x="3" y="5" width="2" height="3" fill="currentColor" opacity="0.6" />
      
      <rect x="7" y="6" width="2" height="5" fill="currentColor" opacity="0.9" />
      <rect x="7" y="4" width="2" height="2" fill="currentColor" opacity="0.6" />
      
      <rect x="11" y="7" width="2" height="4" fill="currentColor" opacity="0.9" />
      <rect x="11" y="3" width="2" height="4" fill="currentColor" opacity="0.6" />
      
      <rect x="15" y="9" width="2" height="2" fill="currentColor" opacity="0.9" />
      <rect x="15" y="6" width="2" height="3" fill="currentColor" opacity="0.6" />
    </svg>
  )
}

function MiniRadarChart() {
  return (
    <svg width="20" height="14" viewBox="0 0 20 14" className="text-pink-500">
      <polygon 
        points="10,3 13,6 11,10 7,10 5,6" 
        fill="currentColor" 
        opacity="0.2" 
        stroke="currentColor" 
        strokeWidth="1"
      />
      <circle cx="10" cy="7" r="4" fill="none" stroke="currentColor" opacity="0.3" strokeWidth="0.5" />
      <circle cx="10" cy="7" r="2" fill="none" stroke="currentColor" opacity="0.3" strokeWidth="0.5" />
      <line x1="10" y1="3" x2="10" y2="11" stroke="currentColor" opacity="0.3" strokeWidth="0.5" />
      <line x1="6" y1="7" x2="14" y2="7" stroke="currentColor" opacity="0.3" strokeWidth="0.5" />
    </svg>
  )
}

function MiniHeatmapChart() {
  return (
    <svg width="20" height="14" viewBox="0 0 20 14" className="text-red-500">
      <rect x="2" y="2" width="2" height="2" fill="currentColor" opacity="0.9" />
      <rect x="5" y="2" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="8" y="2" width="2" height="2" fill="currentColor" opacity="0.8" />
      <rect x="11" y="2" width="2" height="2" fill="currentColor" opacity="0.4" />
      
      <rect x="2" y="5" width="2" height="2" fill="currentColor" opacity="0.7" />
      <rect x="5" y="5" width="2" height="2" fill="currentColor" opacity="0.9" />
      <rect x="8" y="5" width="2" height="2" fill="currentColor" opacity="0.5" />
      <rect x="11" y="5" width="2" height="2" fill="currentColor" opacity="0.8" />
      
      <rect x="2" y="8" width="2" height="2" fill="currentColor" opacity="0.5" />
      <rect x="5" y="8" width="2" height="2" fill="currentColor" opacity="0.7" />
      <rect x="8" y="8" width="2" height="2" fill="currentColor" opacity="0.9" />
      <rect x="11" y="8" width="2" height="2" fill="currentColor" opacity="0.6" />
    </svg>
  )
} 