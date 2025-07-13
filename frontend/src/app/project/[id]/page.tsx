"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { DatabaseService } from "@/components/analysis-db/data/database-service"
import Link from "next/link"
import { ChartProvider } from "@/contexts/chart-context"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { IntegratedLayout } from "@/components/integrated-dashboard/integrated-layout"

// 使用现有的Project接口
interface Project {
  id: string
  project_name: string
  description?: string
  created_at: string
  updated_at: string
  status: string
}

// 添加项目概览数据接口
interface ProjectOverviewData {
  project_name: string;
  created_at: string;
  stats: {
    total_products: number;
    total_brands: number;
    total_reviews: number;
    segment_count: number;
  };
  distributions: {
    sources: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    categories: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
  };
  available_categories: {
    flat_categories: string[];
    hierarchical_categories: Array<{
      parent_category: string;
      parent_count: number;
      children: Array<{
        category: string;
        count: number;
        percentage: number;
      }>;
    }>;
    total_products: number;
  };
}

export default function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [projectId, setProjectId] = useState<string | null>(null)
  // 添加过滤器展开状态
  const [isFilterExpanded, setIsFilterExpanded] = useState(false)
  // 添加过滤器变更处理
  const [filters, setFilters] = useState<{ categories: string[]; asins: string[] }>({
    categories: [],
    asins: []
  })
  // 添加预加载的项目概览数据
  const [projectOverviewData, setProjectOverviewData] = useState<ProjectOverviewData | null>(null)
  const [overviewLoading, setOverviewLoading] = useState(false)

  // 解析异步params
  useEffect(() => {
    const resolveParams = async () => {
      const resolvedParams = await params
      setProjectId(resolvedParams.id)
    }
    resolveParams()
  }, [params])

  // 加载项目信息
  useEffect(() => {
    const loadProject = async () => {
      if (!projectId) return
      
      try {
        setLoading(true)
        const databaseService = new DatabaseService()
        const projectData = await databaseService.getProject(projectId)
        setProject(projectData)
        
        // 同时预加载项目概览数据
        await loadProjectOverview()
      } catch (error) {
        console.error('Failed to load project:', error)
      } finally {
        setLoading(false)
      }
    }

    loadProject()
  }, [projectId])

  // 预加载项目概览数据
  const loadProjectOverview = async () => {
    if (!projectId) return

    setOverviewLoading(true)
    try {
      const databaseService = new DatabaseService()
      const overview = await databaseService.getProjectOverview(projectId)
      setProjectOverviewData(overview)
    } catch (error) {
      console.error('Failed to load project overview:', error)
      setProjectOverviewData(null)
    } finally {
      setOverviewLoading(false)
    }
  }

  // 处理过滤器变更
  const handleFiltersChange = (newFilters: { categories: string[]; asins: string[] }) => {
    setFilters(newFilters)
    // 这里可以传递给AnalysisDbTab组件或其他需要过滤器的组件
  }

  // 切换过滤器展开状态
  const toggleFilterExpanded = () => {
    setIsFilterExpanded(!isFilterExpanded)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading project...</p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-medium text-gray-900 mb-2">Project not found</h2>
          <p className="text-gray-600 mb-4">The project you&apos;re looking for doesn&apos;t exist.</p>
          <Link href="/">
            <Button>Back to Home</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <ChartProvider>
        <IntegratedLayout
          projectId={projectId!}
          project={project}
          projectOverviewData={projectOverviewData}
          overviewLoading={overviewLoading}
          onFiltersChange={handleFiltersChange}
          filters={filters}
          isFilterExpanded={isFilterExpanded}
          onToggleFilter={toggleFilterExpanded}
        />
      </ChartProvider>
    </ProtectedRoute>
  )
} 