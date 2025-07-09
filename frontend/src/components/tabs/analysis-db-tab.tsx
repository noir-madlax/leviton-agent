'use client';

import { AnalysisDbContainer } from '@/components/analysis-db';

interface AnalysisDbTabProps {
  selectedProjectId?: string | null;
  filters?: { categories: string[]; asins: string[] };
}
 
export function AnalysisDbTab({ selectedProjectId, filters }: AnalysisDbTabProps) {
  return <AnalysisDbContainer selectedProjectId={selectedProjectId} filters={filters} />;
} 