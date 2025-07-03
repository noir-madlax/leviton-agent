'use client';

import { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { databaseService, type Project } from '@/components/analysis-db/data/database-service';
import { ProjectDataOverview } from './project-data-overview';
import { ProjectFilters } from './project-filters';

interface DashboardHeaderProps {
  onProjectChange?: (projectId: string) => void;
  selectedProjectId?: string | null;
}

export function DashboardHeader({ onProjectChange, selectedProjectId: parentSelectedProjectId }: DashboardHeaderProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [localSelectedProjectId, setLocalSelectedProjectId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  
  // Use parent's selectedProjectId if provided, otherwise use local state
  const selectedProjectId = parentSelectedProjectId || localSelectedProjectId;

  // 加载项目列表
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const projectList = await databaseService.getProjects();
      setProjects(projectList);
      
      // 🎯 NEW APPROACH: Don't auto-select any project - let user choose
      console.log(`📋 Loaded ${projectList.length} projects, waiting for user selection...`);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const handleProjectChange = async (projectId: string) => {
    if (projectId === selectedProjectId) return;
    
    setLoading(true);
    try {
      // Update local state only if parent doesn't control the state
      if (!parentSelectedProjectId) {
        setLocalSelectedProjectId(projectId);
      }
      
      console.log(`🎯 DashboardHeader: Project selected - ${projectId}`);
      
      if (onProjectChange) {
        onProjectChange(projectId);
      }
    } catch (error) {
      console.error('Failed to change project:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFiltersChange = (filters: { categories: string[]; asins: string[] }) => {
    // TODO: Implement filter application logic in next phase
    console.log('Filters changed:', filters);
  };

  return (
    <div className="mb-8">
      {/* Original header section */}
      <div className="flex items-center justify-between mb-6">
        {/* 简化的页面标题 - 不显示具体项目名 */}
        <div className="flex-1">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 border-b-3 border-blue-500 pb-3 mb-4">
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

        {/* 项目选择器 - 始终显示 */}
        {projects.length > 0 && (
          <div className="flex-shrink-0 ml-8">
            <div className="text-sm text-gray-600 mb-2">Switch Project:</div>
            <Select value={selectedProjectId} onValueChange={handleProjectChange} disabled={loading}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select a project..." />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    <div className="flex flex-col">
                      <span className="font-medium">{project.project_name}</span>
                      <span className="text-xs text-gray-500">
                        {project.total_products} products • {project.total_brands} brands
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Project Data Overview */}
      <ProjectDataOverview projectId={selectedProjectId} />

      {/* Project Filters */}
      <ProjectFilters 
        projectId={selectedProjectId} 
        onFiltersChange={handleFiltersChange}
      />
    </div>
  );
}
