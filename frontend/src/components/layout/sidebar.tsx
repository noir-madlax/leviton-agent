"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  FolderOpen,
  BarChart3,
  Calendar,
  Settings,
} from "lucide-react"
import Link from "next/link"
import { UserMenu } from "./user-menu"
import { useProjectT } from "@/i18n/hooks"

// 使用现有的Project接口
interface Project {
  id: string
  project_name: string
  description?: string
  created_at: string
  updated_at: string
  status: string
}

// 简化的Chart接口（暂时不实现Pin功能）
interface Chart {
  id: string
  title: string
  projectName: string
  projectId?: string
  lastUpdated: string
  type: string
}

interface SidebarProps {
  projects: Project[]
  charts?: Chart[]
  collapsed: boolean
  onToggle: () => void
}

export function Sidebar({ projects, charts = [], collapsed, onToggle }: SidebarProps) {
  const [projectsExpanded, setProjectsExpanded] = useState(true)
  const [chartsExpanded, setChartsExpanded] = useState(true)
  const [isClient, setIsClient] = useState(false)
  
  // 总是调用hooks，但在客户端渲染前返回fallback
  const projectTRaw = useProjectT()
  const t = (key: string) => isClient ? projectTRaw(key) : key

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (collapsed) {
    return (
      <div className="w-16 bg-white border-r border-gray-200 flex flex-col items-center py-4">
        <Button variant="ghost" size="sm" onClick={onToggle} className="mb-4">
          <ChevronRight className="w-4 h-4" />
        </Button>
        <div className="space-y-2">
          <Button variant="ghost" size="sm" className="w-10 h-10 p-0">
            <FolderOpen className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm" className="w-10 h-10 p-0">
            <BarChart3 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* Sidebar Header */}
      <div className="h-16 border-b border-gray-200 flex items-center justify-between px-4">
        <UserMenu />
        <Button variant="ghost" size="sm" onClick={onToggle}>
          <ChevronLeft className="w-4 h-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-6">
        {/* Projects Section */}
        <Collapsible open={projectsExpanded} onOpenChange={setProjectsExpanded}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-2 h-auto">
              <div className="flex items-center space-x-2">
                <FolderOpen className="w-4 h-4" />
                <span className="font-medium">{t('projects')}</span>
                <Badge variant="secondary" className="text-xs">
                  {projects.length}
                </Badge>
              </div>
              {projectsExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
          </CollapsibleTrigger>

          <CollapsibleContent className="space-y-2 mt-2">
            {projects.map((project) => (
              <Link key={project.id} href={`/project/${project.id}`}>
                <div className="p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-transparent hover:border-gray-200 transition-colors">
                  <div className="font-medium text-sm text-gray-900 mb-1 line-clamp-2">{project.project_name}</div>
                  <div className="text-xs text-gray-500 mb-2">{project.description || t('noDescription')}</div>
                  <div className="flex items-center space-x-1 text-xs text-gray-400">
                    <Calendar className="w-3 h-3" />
                    <span>{t('created')} {new Date(project.created_at).toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric' })}</span>
                  </div>
                </div>
              </Link>
            ))}
          </CollapsibleContent>
          </Collapsible>

        {/* Charts Section - 暂时简化，不实现Pin功能 */}
        {charts.length > 0 && (
          <Collapsible open={chartsExpanded} onOpenChange={setChartsExpanded}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between p-2 h-auto">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="w-4 h-4" />
                  <span className="font-medium">{t('recentCharts')}</span>
                  <Badge variant="secondary" className="text-xs">
                    {charts.length}
                  </Badge>
                </div>
                {chartsExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="space-y-2 mt-2">
              {charts.map((chart) => (
                <div
                  key={chart.id}
                  className="p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-transparent hover:border-gray-200 transition-colors"
                >
                  <div className="font-medium text-sm text-gray-900 mb-1 line-clamp-2">{chart.title}</div>
                  <div className="text-xs text-gray-500 mb-2">{chart.projectName}</div>
                  <div className="flex items-center space-x-1 text-xs text-gray-400">
                    <Calendar className="w-3 h-3" />
                    <span>{new Date(chart.lastUpdated).toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric' })}</span>
                  </div>
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}
      </div>
    </div>
  )
} 