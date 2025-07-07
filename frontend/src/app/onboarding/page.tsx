"use client"

import { DataConfirmationTab } from "@/components/tabs/data-confirmation-tab"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function OnboardingPage() {
  const router = useRouter()

  // Handle navigation after project creation is complete
  const handleNavigateToAnalysis = (projectId: string) => {
    router.push(`/project/${projectId}`)
  }

  return (
    <div className="min-h-screen bg-gray-50/50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Home
                </Button>
              </Link>
              <div>
                <h1 className="text-xl font-semibold">Create New Project</h1>
                <p className="text-sm text-muted-foreground">
                  Select data scope and configure your analysis project
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DataConfirmationTab onNavigateToAnalysis={handleNavigateToAnalysis} />
      </main>
    </div>
  )
} 