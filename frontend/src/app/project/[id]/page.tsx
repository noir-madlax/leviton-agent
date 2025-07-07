"use client"

import { useState, useEffect } from "react"
import { AnalysisDbTab } from "@/components/tabs/analysis-db-tab"
import { Button } from "@/components/ui/button"
import { DatabaseService } from "@/components/analysis-db/data/database-service"
import { ArrowLeft, MessageSquare, Download } from "lucide-react"
import Link from "next/link"
import { ChartProvider } from "@/contexts/chart-context"
import { ProtectedRoute } from "@/components/auth/protected-route"

// 使用现有的Project接口
interface Project {
  id: string
  project_name: string
  description?: string
  created_at: string
  updated_at: string
  status: string
}

export default function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [projectId, setProjectId] = useState<string | null>(null)

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
      } catch (error) {
        console.error('Failed to load project:', error)
      } finally {
        setLoading(false)
      }
    }

    loadProject()
  }, [projectId])

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
          <p className="text-gray-600 mb-4">The project you're looking for doesn't exist.</p>
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
                  <div>
                    <h1 className="text-xl font-semibold">{project.project_name}</h1>
                    <p className="text-sm text-muted-foreground">
                      {project.description || "Project Dashboard"}
                    </p>
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
            </div>
          </header>

          {/* Main Content */}
          <main className="h-[calc(100vh-4rem)]">
            {projectId && <AnalysisDbTab selectedProjectId={projectId} />}
          </main>
        </div>
      </ChartProvider>
    </ProtectedRoute>
  )
} 