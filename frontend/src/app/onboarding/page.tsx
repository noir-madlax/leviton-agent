"use client"

import { DataConfirmationTab } from "@/components/tabs/data-confirmation-tab"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ArrowLeft, CheckCircle, Edit2, Check, X } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { useState, useEffect } from "react"

export default function OnboardingPage() {
  const router = useRouter()
  const [createProjectRef, setCreateProjectRef] = useState<{
    handleConfirmSelection: () => void;
    isConfirmed: boolean;
    isFilterApplied: boolean;
    generateSmartProjectName: () => string;
    estimatedTime: string;
  } | null>(null)
  
  // 项目名状态管理
  const [projectName, setProjectName] = useState('New Project 1')
  const [isEditingName, setIsEditingName] = useState(false)
  const [tempProjectName, setTempProjectName] = useState('')

  // Handle navigation after project creation is complete
  const handleNavigateToAnalysis = (projectId: string) => {
    router.push(`/project/${projectId}`)
  }

  const handleCreateProject = () => {
    if (createProjectRef) {
      createProjectRef.handleConfirmSelection()
    }
  }

  // 当apply filters后，自动生成智能项目名
  useEffect(() => {
    if (createProjectRef?.isFilterApplied && !isEditingName) {
      const smartName = createProjectRef.generateSmartProjectName()
      setProjectName(smartName)
    }
  }, [createProjectRef?.isFilterApplied, isEditingName])

  const handleEditName = () => {
    setTempProjectName(projectName)
    setIsEditingName(true)
  }

  const handleSaveName = () => {
    setProjectName(tempProjectName)
    setIsEditingName(false)
  }

  const handleCancelEdit = () => {
    setTempProjectName('')
    setIsEditingName(false)
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50/50">
        {/* Header */}
        <header className="sticky top-0 z-10 border-b bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-6">
                <Link href="/">
                  <Button variant="ghost" size="sm">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Home
                  </Button>
                </Link>
                
                {/* 项目创建区域 */}
                <div className="flex items-center gap-4">
                  <div className="flex flex-col">
                    <h1 className="text-xl font-semibold">Create New Project</h1>
                    <p className="text-sm text-muted-foreground">
                      Select project data scope
                    </p>
                  </div>
                  
                  {/* 项目名编辑区域 - 重新设计 */}
                  <div className="flex items-center">
                    {isEditingName ? (
                      <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-blue-300 rounded-lg shadow-sm">
                        <Input
                          value={tempProjectName}
                          onChange={(e) => setTempProjectName(e.target.value)}
                          className="h-6 w-64 text-sm border-0 shadow-none p-0 focus-visible:ring-0"
                          autoFocus
                        />
                        <div className="flex items-center gap-1">
                          <Button size="sm" variant="ghost" onClick={handleSaveName} className="h-6 w-6 p-0 hover:bg-green-100">
                            <Check className="h-3 w-3 text-green-600" />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={handleCancelEdit} className="h-6 w-6 p-0 hover:bg-red-100">
                            <X className="h-3 w-3 text-red-600" />
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors group cursor-pointer" onClick={handleEditName}>
                        <span className="text-sm font-medium text-blue-900 whitespace-nowrap" title={projectName}>
                          {projectName}
                        </span>
                        <Edit2 className="h-3 w-3 text-blue-600 group-hover:text-blue-700" />
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Create Research Project Button */}
              <div className="flex gap-2">
                <div className="flex flex-col items-end">
                  <Button
                    onClick={handleCreateProject}
                    disabled={!createProjectRef || createProjectRef.isConfirmed || !createProjectRef.isFilterApplied}
                    title={!createProjectRef || !createProjectRef.isFilterApplied ? "Please apply filters first" : ""}
                  >
                    {createProjectRef && createProjectRef.isConfirmed ? (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Project Created
                      </>
                    ) : (
                      'Create Research Project'
                    )}
                  </Button>
                  {createProjectRef?.isFilterApplied && createProjectRef?.estimatedTime && (
                    <p className="text-xs text-gray-500 mt-1">
                      Estimated time: {createProjectRef.estimatedTime}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <DataConfirmationTab 
            onNavigateToAnalysis={handleNavigateToAnalysis}
            onRegisterCreateProject={setCreateProjectRef}
            projectName={projectName}
          />
        </main>
      </div>
    </ProtectedRoute>
  )
} 