'use client';

import { useState } from 'react';
import { CategoryFilterAndProjectScope } from './category-filter-and-project-scope';

interface DashboardHeaderProps {
  onProjectChange?: (projectId: string) => void;
  selectedProjectId?: string | null;
  onFiltersChange?: (filters: { categories: string[]; asins: string[] }) => void;
}

export function DashboardHeader({ selectedProjectId: parentSelectedProjectId, onFiltersChange }: DashboardHeaderProps) {
  const [localSelectedProjectId] = useState<string>('');
  
  // Use parent's selectedProjectId if provided, otherwise use local state
  const selectedProjectId = parentSelectedProjectId || localSelectedProjectId;

  const handleFiltersChange = (filters: { categories: string[]; asins: string[] }) => {
    console.log('🔄 Filters applied:', filters);
    
    // Pass filters up to parent component for dashboard data reload
    if (onFiltersChange) {
      onFiltersChange(filters);
    }
  };

  return (
    <div className="mb-8">
      {/* Original header section */}
      <div className="flex items-center justify-between mb-6">
        {/* 简化的页面标题 - 不显示具体项目名 */}
        <div className="flex-1">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 border-b border-gray-200 pb-3 mb-4">
            Project Analysis Report
          </h1>

          <div className="text-gray-500 italic">
            Report Generated:{" "}
            {new Date().toLocaleDateString("en-US", {
              month: "long",
              day: "numeric", 
              year: "numeric",
              hour: "numeric",
              minute: "numeric",
              hour12: true,
            })}
          </div>
        </div>
      </div>

      {/* Category Filter & Project Scope */}
      <CategoryFilterAndProjectScope 
        projectId={selectedProjectId} 
        onFiltersChange={handleFiltersChange}
      />
    </div>
  );
}
