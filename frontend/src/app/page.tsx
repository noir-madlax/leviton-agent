"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Sidebar } from "@/components/layout/sidebar"
import { ProjectCard } from "@/components/layout/project-card"
import { Card, CardContent } from "@/components/ui/card"
import { DatabaseService } from "@/components/analysis-db/data/database-service"
import {
  Plus,
  Upload,
  Loader2,
} from "lucide-react"
import Link from "next/link"

// 使用现有的Project接口
interface Project {
  id: string
  project_name: string
  description?: string
  created_at: string
  updated_at: string
  status: string
  total_products?: number
  total_brands?: number
  total_reviews?: number
}

export default function HomePage() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 获取最近使用的项目（作为Current Project）
  const mostRecentProject = projects.length > 0 ? projects[0] : null

  // 加载项目列表
  useEffect(() => {
    const loadProjects = async () => {
      try {
        setLoading(true)
        const databaseService = new DatabaseService()
        const projectList = await databaseService.getProjects()
        
        // 按更新时间排序，最新的在前面
        const sortedProjects = projectList.sort((a, b) => 
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        )
        
        setProjects(sortedProjects)
        setError(null)
      } catch (err) {
        console.error('Failed to load projects:', err)
        setError('Failed to load projects. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    loadProjects()
  }, [])

  if (loading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
            <p className="text-gray-600">Loading projects...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        projects={projects}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900">Xenith</h1>
          </div>

          <div className="flex items-center space-x-4">
            {/* Import Data Button */}
            <Link href="/import-data">
              <Button variant="outline">
                <Upload className="w-4 h-4 mr-1" />
                Import Data
              </Button>
            </Link>
            {/* New Project Button */}
            <Link href="/onboarding">
              <Button>
                <Plus className="w-4 h-4 mr-1" />
                New Project
              </Button>
            </Link>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-6xl mx-auto space-y-6">
            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="pt-6">
                  <p className="text-red-600">{error}</p>
                </CardContent>
              </Card>
            )}

            {/* Current Project */}
            {mostRecentProject && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">Current Project</h2>
                </div>
                <ProjectCard project={mostRecentProject} featured={true} />
              </div>
            )}



            {/* No projects message */}
            {projects.length === 0 && (
              <Card>
                <CardContent className="pt-6 text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
                  <p className="text-gray-600 mb-4">
                    Create your first project to get started with data analysis.
                  </p>
                  <Link href="/onboarding">
                    <Button>
                      <Plus className="w-4 h-4 mr-2" />
                      Create First Project
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
