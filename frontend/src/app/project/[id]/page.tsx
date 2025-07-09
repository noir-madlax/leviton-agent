"use client"

import { useState, useEffect } from "react"
import { AnalysisDbTab } from "@/components/tabs/analysis-db-tab"
import { Button } from "@/components/ui/button"
import { DatabaseService } from "@/components/analysis-db/data/database-service"
import { ArrowLeft, MessageSquare } from "lucide-react"
import Link from "next/link"
import { ChartProvider } from "@/contexts/chart-context"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { CategoryFilterAndProjectScope } from "@/components/analysis-db/shared/category-filter-and-project-scope"

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
  available_categories: string[];
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
        <div className="min-h-screen bg-gray-50/50">
          {/* Header */}
          <header className="border-b bg-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-16">
                <div className="flex items-center gap-4">
                  <Link href="/">
                    <Button variant="ghost" size="sm">
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back to Projects
                    </Button>
                  </Link>
                  <div className="flex items-center gap-3">
                    <h1 className="text-xl font-semibold">{project.project_name}</h1>
                    {/* 蓝色提示文字移到项目名称右边 */}
                    <button
                      onClick={toggleFilterExpanded}
                      className="text-xs text-blue-600 hover:text-blue-800 cursor-pointer transition-colors"
                    >
                      {isFilterExpanded ? 'Hide filters' : 'Click to adjust product category scope'}
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {/* Chat Button */}
                  <Link href={projectId ? `/project/${projectId}/chat?from=dashboard` : '/'}>
                    <Button variant="outline">
                      <MessageSquare className="h-4 w-4 mr-2" />
                      Chat
                    </Button>
                  </Link>
                </div>
              </div>
              
              {/* 动态展开的过滤器区域 */}
              {isFilterExpanded && projectId && (
                <div className="pb-4 pt-2 mt-4">
                  <CategoryFilterAndProjectScope 
                    projectId={projectId}
                    onFiltersChange={handleFiltersChange}
                    initialFilters={filters}
                    preloadedData={projectOverviewData}
                    isDataLoading={overviewLoading}
                  />
                </div>
              )}
            </div>
          </header>

          {/* Main Content */}
          <main className="h-[calc(100vh-4rem)]">
            {projectId && <AnalysisDbTab selectedProjectId={projectId} filters={filters} />}
          </main>
        </div>
      </ChartProvider>
    </ProtectedRoute>
  )
} 