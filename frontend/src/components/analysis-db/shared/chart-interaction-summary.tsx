import React from 'react'

interface ChartInteractionSummaryProps {
  children: React.ReactNode
  className?: string
}

export function ChartInteractionSummary({ children, className = "" }: ChartInteractionSummaryProps) {
  return (
    <div className={`bg-blue-50 border-l-4 border-blue-400 p-4 mb-4 ${className}`}>
      {children}
    </div>
  )
} 