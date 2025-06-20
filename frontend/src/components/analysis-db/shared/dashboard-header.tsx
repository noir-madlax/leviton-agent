'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { databaseService, type Project } from '@/components/analysis-db/data/database-service';

interface DashboardHeaderProps {
  projectName?: string;
  onProjectChange?: (projectId: string) => void;
}

export function DashboardHeader({ projectName = 'Default Project', onProjectChange }: DashboardHeaderProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [loading, setLoading] = useState(false);

  // 加载项目列表
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const projectList = await databaseService.getProjects();
      setProjects(projectList);
      
      // 如果有项目且没有选中任何项目，选中第一个
      if (projectList.length > 0 && !selectedProjectId) {
        const firstProject = projectList[0];
        setSelectedProjectId(firstProject.id);
        // 如果有回调，通知父组件项目变更
        if (onProjectChange) {
          onProjectChange(firstProject.id);
        }
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const handleProjectChange = async (projectId: string) => {
    if (projectId === selectedProjectId) return;
    
    setLoading(true);
    try {
      setSelectedProjectId(projectId);
      if (onProjectChange) {
        onProjectChange(projectId);
      }
    } catch (error) {
      console.error('Failed to change project:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectedProject = projects.find(p => p.id === selectedProjectId);

  return (
    <div className="flex items-center justify-between mb-8">
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
  );
}
