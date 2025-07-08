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
      {/* Category Filter & Project Scope */}
      <CategoryFilterAndProjectScope 
        projectId={selectedProjectId} 
        onFiltersChange={handleFiltersChange}
      />
    </div>
  );
}
