"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { DatabaseService } from "@/components/analysis-db/data/database-service"
import Link from "next/link"
import { ChartProvider } from "@/contexts/chart-context"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { IntegratedLayout } from "@/components/integrated-dashboard/integrated-layout"
import { ProjectFilters, DEFAULT_FILTERS } from "@/components/analysis-db/types/filters"
import { preloadUnifiedFilterData } from "@/components/analysis-db/hooks/use-unified-filter-data"
import { useCommonT, useProjectT } from "@/i18n/hooks"
import { chatConfigService } from "@/lib/services/chat-config-service"

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
    brands: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    segments: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    extend_fields: Record<string, Array<{
      name: string;
      count: number;
      percentage: number;
    }>>;
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
  const [mounted, setMounted] = useState(false)
  
  // 国际化hooks
  const commonT = useCommonT()
  const projectT = useProjectT()
  
  // 添加过滤器展开状态
  const [isFilterExpanded, setIsFilterExpanded] = useState(false)
  // 添加过滤器变更处理
  const [filters, setFilters] = useState<ProjectFilters>(DEFAULT_FILTERS)
  // 添加预加载的项目概览数据
  const [projectOverviewData, setProjectOverviewData] = useState<ProjectOverviewData | null>(null)
  const [overviewLoading, setOverviewLoading] = useState(false)
  // 添加配置就绪状态
  const [configReady, setConfigReady] = useState(false)

  // 确保组件已挂载
  useEffect(() => {
    setMounted(true)
  }, [])

  // 解析异步params
  useEffect(() => {
    const resolveParams = async () => {
      try {
        const resolvedParams = await params
        setProjectId(resolvedParams.id)
      } catch (error) {
        console.error('Failed to resolve params:', error)
      }
    }
    resolveParams()
  }, [params])

  // 加载项目信息
  useEffect(() => {
    const loadProject = async () => {
      if (!projectId || !mounted) return
      
      try {
        setLoading(true)
        const databaseService = new DatabaseService()

        console.log(`🚀 [ProjectPage] Starting project load for ID: ${projectId}`)
        
        // 1. 先获取筛选器默认配置
        console.log(`🔍 [ProjectPage] Fetching filter defaults...`)
        const defaultFilters = await databaseService.getProjectFilterDefaults(projectId)
        setFilters(defaultFilters) // 设置到状态中
        console.log(`✅ [ProjectPage] Applied default filters:`, defaultFilters)

        // 2. 并行加载项目信息和使用配置好的筛选器加载概览数据
        console.log(`📊 [ProjectPage] Loading project data and overview with filters...`)
        const [projectData] = await Promise.all([
          databaseService.getProject(projectId),
          loadProjectOverview(defaultFilters), // 使用配置好的筛选器
          preloadUnifiedFilterData(projectId)
        ])

        setProject(projectData)
        console.log(`🎉 [ProjectPage] Project loaded successfully with pre-applied filters`)

        // 检查 chart config 是否已预载，如果没有则等待
        console.log(`🔍 [ProjectPage] Checking chart config readiness...`)
        await ensureConfigReady(projectId)
        setConfigReady(true)
        console.log(`✅ [ProjectPage] Chart config ready`)

      } catch (error) {
        console.error('❌ [ProjectPage] Failed to load project:', error)
      } finally {
        setLoading(false)
      }
    }

    loadProject()
  }, [projectId, mounted])

  // 确保配置就绪的函数
  const ensureConfigReady = async (projectId: string): Promise<void> => {
    try {
      // 尝试获取配置，如果缓存中有则立即返回，否则会触发加载
      await chatConfigService.getChatConfig(projectId)
      console.log(`📋 [ProjectPage] Chart config ensured for project: ${projectId}`)
    } catch (error) {
      console.warn(`⚠️ [ProjectPage] Failed to ensure config ready:`, error)
      // 即使配置加载失败，也继续渲染（使用 fallback 配置）
    }
  }

  // 预加载项目概览数据
  const loadProjectOverview = async (filters?: ProjectFilters) => {
    if (!projectId) return null

    setOverviewLoading(true)
    try {
      const databaseService = new DatabaseService()
      const overview = await databaseService.getProjectOverview(
        projectId,
        filters?.categories || [],
        filters?.brands || [], // 传递brands而不是packaging_types
        filters?.segments || [],
        filters?.extend_fields || {}
      )

      // 确保包含所有必需字段，提供默认值
      const completeOverview: ProjectOverviewData = {
        ...overview,
        distributions: {
          ...overview.distributions,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          brands: (overview.distributions as any).brands || [],
          // eslint-disable-next-line @typescript-eslint/no-explicit-any  
          segments: (overview.distributions as any).segments || [],
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          extend_fields: (overview.distributions as any).extend_fields || {}
        }
      };

      setProjectOverviewData(completeOverview)
      return overview // 返回原始的 overview 数据供 preloadFilterOptions 使用
    } catch (error) {
      console.error('Failed to load project overview:', error)
      setProjectOverviewData(null)
      return null
    } finally {
      setOverviewLoading(false)
    }
  }

  // 处理过滤器变更
  const handleFiltersChange = (newFilters: ProjectFilters) => {
    setFilters(newFilters)
    // 重新获取基于新筛选器的项目概览数据
    loadProjectOverview(newFilters)
  }

  // 切换过滤器展开状态
  const toggleFilterExpanded = () => {
    setIsFilterExpanded(!isFilterExpanded)
  }

  // 在组件未挂载或参数未解析时显示加载状态
  if (!mounted || !projectId) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (loading || !configReady) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {loading ? 'Loading project...' : 'Preparing dashboard...'}
          </p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-medium text-gray-900 mb-2">{projectT('projectNotFound')}</h2>
          <p className="text-gray-600 mb-4">{projectT('projectNotFoundDescription')}</p>
          <Link href="/">
            <Button>{commonT('backToHome')}</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <ChartProvider>
        <IntegratedLayout
          projectId={projectId}
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