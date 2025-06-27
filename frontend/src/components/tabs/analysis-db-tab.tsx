'use client';

import { AnalysisDbContainer } from '@/components/analysis-db';

interface AnalysisDbTabProps {
  selectedProjectId?: string | null;
}
 
export function AnalysisDbTab({ selectedProjectId }: AnalysisDbTabProps) {
  return <AnalysisDbContainer selectedProjectId={selectedProjectId} />;
} 