'use client';

import { useState } from 'react';
import { ProjectDataOverview } from './project-data-overview';
import { ProjectFilters } from './project-filters';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3 } from 'lucide-react';

interface DashboardHeaderProps {
  onProjectChange?: (projectId: string) => void;
  selectedProjectId?: string | null;
  onFiltersChange?: (filters: { categories: string[]; asins: string[] }) => void;
}

export function DashboardHeader({ selectedProjectId: parentSelectedProjectId, onFiltersChange }: DashboardHeaderProps) {
  const [localSelectedProjectId] = useState<string>('');
  const [currentFilters, setCurrentFilters] = useState<{ categories: string[]; asins: string[] }>({ categories: [], asins: [] });
  
  // Use parent's selectedProjectId if provided, otherwise use local state
  const selectedProjectId = parentSelectedProjectId || localSelectedProjectId;

  const handleFiltersChange = (filters: { categories: string[]; asins: string[] }) => {
    console.log('🔄 Filters applied:', filters);
    setCurrentFilters(filters);
    
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

      {/* Project Filters */}
      <ProjectFilters 
        projectId={selectedProjectId} 
        onFiltersChange={handleFiltersChange}
      />

      {/* Project Data Scope */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Project Data Scope
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ProjectDataOverview 
            projectId={selectedProjectId} 
            categoryFilters={currentFilters.categories}
          />
        </CardContent>
      </Card>
    </div>
  );
}
