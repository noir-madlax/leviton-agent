'use client';

import { AnalysisDbContainer } from '@/components/analysis-db';
import { ProjectFilters } from '@/components/analysis-db/types/filters';

interface AnalysisDbTabProps {
  selectedProjectId?: string | null;
  filters?: ProjectFilters;
}
 
export function AnalysisDbTab({ selectedProjectId, filters }: AnalysisDbTabProps) {
  return <AnalysisDbContainer selectedProjectId={selectedProjectId} filters={filters} />;
} 