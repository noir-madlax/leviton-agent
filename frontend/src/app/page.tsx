"use client"

import { ProjectCard } from "@/components/layout/project-card"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Clock, Upload, Loader2, Info } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { DatabaseService } from "@/components/analysis-db/data/database-service"
import { Sidebar } from "@/components/layout/sidebar"
import { useAuth } from "@/contexts/auth-context"
import { usePermissions } from "@/hooks/use-permissions"
import { useProjectT, useCommonT } from "@/i18n/hooks"

// Updated Project interface with overall_status
interface Project {
  id: string
  project_name: string
  description?: string
  created_at: string
  updated_at: string
  status: string
  overall_status?: string  // New simplified status field
  total_products?: number
  total_brands?: number
  total_reviews?: number
}

export default function HomePage() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const [isClient, setIsClient] = useState(false)
  const { isAuthenticated, user } = useAuth()
  const { permissions } = usePermissions()
  
  // 总是调用hooks，但在客户端渲染前返回fallback
  const projectTRaw = useProjectT()
  const commonTRaw = useCommonT()
  
  const t = (key: string) => isClient ? projectTRaw(key) : key
  const commonT = (key: string) => isClient ? commonTRaw(key) : key

  // 确保组件已挂载
  useEffect(() => {
    setMounted(true)
    setIsClient(true)
  }, [])

  // Get the most recent project as Current Project
  const mostRecentProject = projects.length > 0 ? projects[0] : null
  
  // Check if there are any processing projects
  const processingProjects = projects.filter(p => p.overall_status === 'creating')
  const hasProcessingProjects = processingProjects.length > 0

  // Load projects list
  useEffect(() => {
    const loadProjects = async () => {
      if (!isAuthenticated || !mounted) {
        console.log('User not authenticated or not mounted, skipping project load')
        setLoading(false)
        return
      }
      
      try {
        console.log('Loading projects...')
        setLoading(true)
        const databaseService = new DatabaseService()
        const userUid = user?.id || undefined
        console.log('🔍 [HOMEPAGE] User UID for project filtering:', userUid, 'User data:', user)
        const projectList = await databaseService.getProjects(userUid)
        
        console.log('Projects loaded:', projectList.length)
        
        // Sort by update time, newest first
        const sortedProjects = projectList.sort((a, b) => 
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        )
        
        setProjects(sortedProjects)
        setError(null)
      } catch (err) {
        console.error('Failed to load projects:', err)
        setError(`Failed to load projects: ${err instanceof Error ? err.message : 'Unknown error'}`)
      } finally {
        setLoading(false)
      }
    }

    loadProjects()
  }, [isAuthenticated, mounted, user?.id])

  // 在组件未挂载时显示加载状态
  if (!mounted) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
            <p className="text-gray-600">{commonT('loading')}</p>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
            <p className="text-gray-600">{t('processingData')}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-gray-50">
        <Sidebar
          projects={projects}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        <div className="flex-1 flex flex-col">
          {/* Top Bar */}
          <header className="bg-white border-b border-gray-200 px-6 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">Xenith</h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* Create Project Button */}
              <Link href="/onboarding">
                <Button 
                  disabled={!permissions?.can_create_project}
                  title={!permissions?.can_create_project ? "Currently in internal testing" : ""}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {t('createProject')}
                </Button>
              </Link>
              
              {/* Import Data Button */}
              <Link href="/import-data">
                <Button 
                  variant="outline"
                  disabled={!permissions?.can_import_data}
                  title={!permissions?.can_import_data ? "Currently in internal testing" : ""}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {t('dataScraping')}
                </Button>
              </Link>
            </div>
          </header>
        
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-6xl mx-auto space-y-6">
            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="pt-6">
                  <p className="text-red-600">{error}</p>
                </CardContent>
              </Card>
            )}

            {/* User Tips Section */}
            {hasProcessingProjects && (
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="pt-6">
                  <div className="flex items-start space-x-3">
                    <Clock className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h3 className="font-medium text-blue-900 mb-1">Projects in Progress</h3>
                      <p className="text-blue-800 text-sm">
                        You have {processingProjects.length} project{processingProjects.length > 1 ? 's' : ''} currently being processed. 
                        The analysis typically takes 10-30 minutes to complete depending on the data size. You can click on any processing project to view detailed progress.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

           

            {/* Welcome Tips for New Users */}
            {projects.length === 0 && (
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="pt-6">
                  <div className="flex items-start space-x-3">
                    <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h3 className="font-medium text-blue-900 mb-1">Welcome to Xenith</h3>
                      <p className="text-blue-800 text-sm">
                        Get started by creating your first research project. Select your product categories, apply filters, and let our AI analyze market insights for you.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Current Project */}
            {mostRecentProject && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">{t('projectOverview')}</h2>
                </div>
                <ProjectCard project={mostRecentProject} featured={true} />
              </div>
            )}

            {/* No projects message */}
            {projects.length === 0 && (
              <Card>
                <CardContent className="pt-6 text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">{t('createNewProject')}</h3>
                  <p className="text-gray-600 mb-4">
                    {t('selectProjectScope')}
                  </p>
                  <Link href="/onboarding">
                    <Button>
                      <Plus className="w-4 h-4 mr-2" />
                      {t('createProject')}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
    </ProtectedRoute>
  )
}
