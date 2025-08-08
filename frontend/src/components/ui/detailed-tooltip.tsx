"use client"

import { useState, useRef, useEffect, ReactNode } from 'react';

interface DetailedTooltipContent {
  title: string;
  type?: string;
  positiveReviews: number;
  negativeReviews: number;
  totalMentions?: number;
  totalReviews?: number;
  satisfactionRate: number;
  additionalInfo?: string[];
}

interface DetailedTooltipProps {
  content: DetailedTooltipContent;
  children: ReactNode;
  className?: string;
}

export function DetailedTooltip({ content, children, className = '' }: DetailedTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const updatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    
    // Position tooltip above the trigger element
    let top = triggerRect.top - tooltipRect.height - 8;
    let left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;

    // Adjust if tooltip goes outside viewport
    if (left < 8) left = 8;
    if (left + tooltipRect.width > window.innerWidth - 8) {
      left = window.innerWidth - tooltipRect.width - 8;
    }
    if (top < 8) {
      // If no space above, show below
      top = triggerRect.bottom + 8;
    }

    setPosition({ top, left });
  };

  useEffect(() => {
    if (isVisible) {
      updatePosition();
      const handleResize = () => updatePosition();
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, [isVisible]);

  return (
    <>
      <div
        ref={triggerRef}
        className={`relative ${className}`}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </div>
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className="fixed z-50 px-4 py-3 text-sm bg-white border border-gray-300 rounded-lg shadow-lg pointer-events-none animate-in fade-in-0 zoom-in-95 duration-200 max-w-80"
          style={{
            top: `${position.top}px`,
            left: `${position.left}px`,
          }}
        >
          {/* Title */}
          <div className="font-semibold text-gray-900 mb-2 text-base">
            {content.title}
          </div>
          
          {/* Type (if provided) */}
          {content.type && (
            <div className="text-gray-600 mb-2">
              <span className="font-medium">Type:</span> {content.type}
            </div>
          )}
          
          {/* Statistics */}
          <div className="space-y-1 mb-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Total Reviews:</span>
              <span className="font-medium text-gray-900">{content.totalReviews}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-green-700">Positive mentioned aspects:</span>
              <span className="font-medium text-green-800">{content.positiveReviews}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-red-700">Negative mentioned aspects:</span>
              <span className="font-medium text-red-800">{content.negativeReviews}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-blue-700">Satisfaction Rate:</span>
              <span className="font-medium text-blue-800">{content.satisfactionRate}%</span>
            </div>
          </div>
          
          {/* Additional Info */}
          {content.additionalInfo && content.additionalInfo.length > 0 && (
            <div className="border-t border-gray-200 pt-2">
              <div className="text-gray-700 text-xs space-y-1">
                {content.additionalInfo.map((info, index) => (
                  <div key={index}>• {info}</div>
                ))}
              </div>
            </div>
          )}
          
          {/* Arrow pointing to the trigger */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-white" />
        </div>
      )}
    </>
  );
} 