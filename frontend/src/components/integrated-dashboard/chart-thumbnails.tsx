"use client"

import React from 'react'

// Unified size configuration for all thumbnails
const THUMBNAIL_CONFIG = {
  containerClass: "w-16 h-12", // More appropriate size for cards
  svgWidth: 32,               // Adjusted accordingly
  svgHeight: 24,              // Adjusted accordingly
  viewBox: "0 0 64 48"        // Adjusted accordingly
}

interface ThumbnailPreviewProps {
  type: string
  className?: string
}

export function ThumbnailPreview({ type, className = THUMBNAIL_CONFIG.containerClass }: ThumbnailPreviewProps) {
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
    <div className={`${className}  rounded bg-gray-50 flex items-center justify-center overflow-hidden`}>
      {thumbnails[type as keyof typeof thumbnails] || <MiniBarChart />}
    </div>
  )
}

function MiniBarChart() {
  return (
    <svg width={THUMBNAIL_CONFIG.svgWidth} height={THUMBNAIL_CONFIG.svgHeight} viewBox={THUMBNAIL_CONFIG.viewBox} className="text-blue-500">
      <rect x="8" y="30" width="8" height="16" fill="currentColor" opacity="0.8" />
      <rect x="20" y="20" width="8" height="26" fill="currentColor" opacity="0.9" />
      <rect x="32" y="12" width="8" height="34" fill="currentColor" />
      <rect x="44" y="24" width="8" height="22" fill="currentColor" opacity="0.7" />
      <rect x="56" y="16" width="8" height="30" fill="currentColor" opacity="0.8" />
    </svg>
  )
}

function MiniScatterChart() {
  return (
    <svg width={THUMBNAIL_CONFIG.svgWidth} height={THUMBNAIL_CONFIG.svgHeight} viewBox={THUMBNAIL_CONFIG.viewBox} className="text-green-500">
      <circle cx="12" cy="36" r="3" fill="currentColor" opacity="0.8" />
      <circle cx="20" cy="24" r="3" fill="currentColor" opacity="0.9" />
      <circle cx="28" cy="16" r="3" fill="currentColor" />
      <circle cx="36" cy="28" r="3" fill="currentColor" opacity="0.7" />
      <circle cx="44" cy="20" r="3" fill="currentColor" opacity="0.8" />
      <circle cx="52" cy="32" r="3" fill="currentColor" opacity="0.6" />
      <circle cx="60" cy="12" r="3" fill="currentColor" opacity="0.9" />
      <circle cx="68" cy="26" r="3" fill="currentColor" opacity="0.7" />
    </svg>
  )
}

function MiniPieChart() {
  return (
    <svg width={THUMBNAIL_CONFIG.svgWidth} height={THUMBNAIL_CONFIG.svgHeight} viewBox={THUMBNAIL_CONFIG.viewBox} className="text-purple-500">
      <circle cx="40" cy="24" r="18" fill="currentColor" opacity="0.2" />
      <path 
        d="M 40 24 L 40 6 A 18 18 0 0 1 53.18 18 Z" 
        fill="currentColor" 
        opacity="0.8" 
      />
      <path 
        d="M 40 24 L 53.18 18 A 18 18 0 0 1 53.18 30 Z" 
        fill="currentColor" 
        opacity="0.6" 
      />
      <path 
        d="M 40 24 L 53.18 30 A 18 18 0 0 1 26.82 30 Z" 
        fill="currentColor" 
        opacity="0.9" 
      />
    </svg>
  )
}

function MiniLineChart() {
  return (
    <svg width={THUMBNAIL_CONFIG.svgWidth} height={THUMBNAIL_CONFIG.svgHeight} viewBox={THUMBNAIL_CONFIG.viewBox} className="text-orange-500">
      <polyline 
        points="8,36 18,24 28,28 38,16 48,20 58,12 68,18" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="4" 
        opacity="0.8"
      />
      <circle cx="8" cy="36" r="3" fill="currentColor" />
      <circle cx="18" cy="24" r="3" fill="currentColor" />
      <circle cx="28" cy="28" r="3" fill="currentColor" />
      <circle cx="38" cy="16" r="3" fill="currentColor" />
      <circle cx="48" cy="20" r="3" fill="currentColor" />
      <circle cx="58" cy="12" r="3" fill="currentColor" />
      <circle cx="68" cy="18" r="3" fill="currentColor" />
    </svg>
  )
}

function MiniStackedBarChart() {
  return (
    <svg width={THUMBNAIL_CONFIG.svgWidth} height={THUMBNAIL_CONFIG.svgHeight} viewBox={THUMBNAIL_CONFIG.viewBox} className="text-teal-500">
      <rect x="12" y="28" width="8" height="12" fill="currentColor" opacity="0.9" />
      <rect x="12" y="16" width="8" height="12" fill="currentColor" opacity="0.6" />
      
      <rect x="24" y="20" width="8" height="20" fill="currentColor" opacity="0.9" />
      <rect x="24" y="12" width="8" height="8" fill="currentColor" opacity="0.6" />
      
      <rect x="36" y="24" width="8" height="16" fill="currentColor" opacity="0.9" />
      <rect x="36" y="8" width="8" height="16" fill="currentColor" opacity="0.6" />
      
      <rect x="48" y="32" width="8" height="8" fill="currentColor" opacity="0.9" />
      <rect x="48" y="20" width="8" height="12" fill="currentColor" opacity="0.6" />
    </svg>
  )
}

function MiniRadarChart() {
  return (
    <svg width={THUMBNAIL_CONFIG.svgWidth} height={THUMBNAIL_CONFIG.svgHeight} viewBox={THUMBNAIL_CONFIG.viewBox} className="text-pink-500">
      <polygon 
        points="40,8 48,20 44,36 28,36 20,20" 
        fill="currentColor" 
        opacity="0.2" 
        stroke="currentColor" 
        strokeWidth="3"
      />
      <circle cx="40" cy="24" r="14" fill="none" stroke="currentColor" opacity="0.3" strokeWidth="1.5" />
      <circle cx="40" cy="24" r="7" fill="none" stroke="currentColor" opacity="0.3" strokeWidth="1.5" />
      <line x1="40" y1="10" x2="40" y2="38" stroke="currentColor" opacity="0.3" strokeWidth="1.5" />
      <line x1="26" y1="24" x2="54" y2="24" stroke="currentColor" opacity="0.3" strokeWidth="1.5" />
    </svg>
  )
}

function MiniHeatmapChart() {
  return (
    <svg width={THUMBNAIL_CONFIG.svgWidth} height={THUMBNAIL_CONFIG.svgHeight} viewBox={THUMBNAIL_CONFIG.viewBox} className="text-red-500">
      <rect x="8" y="8" width="8" height="8" fill="currentColor" opacity="0.9" />
      <rect x="20" y="8" width="8" height="8" fill="currentColor" opacity="0.6" />
      <rect x="32" y="8" width="8" height="8" fill="currentColor" opacity="0.8" />
      <rect x="44" y="8" width="8" height="8" fill="currentColor" opacity="0.4" />
      
      <rect x="8" y="20" width="8" height="8" fill="currentColor" opacity="0.7" />
      <rect x="20" y="20" width="8" height="8" fill="currentColor" opacity="0.9" />
      <rect x="32" y="20" width="8" height="8" fill="currentColor" opacity="0.5" />
      <rect x="44" y="20" width="8" height="8" fill="currentColor" opacity="0.8" />
      
      <rect x="8" y="32" width="8" height="8" fill="currentColor" opacity="0.5" />
      <rect x="20" y="32" width="8" height="8" fill="currentColor" opacity="0.7" />
      <rect x="32" y="32" width="8" height="8" fill="currentColor" opacity="0.9" />
      <rect x="44" y="32" width="8" height="8" fill="currentColor" opacity="0.6" />
    </svg>
  )
} 