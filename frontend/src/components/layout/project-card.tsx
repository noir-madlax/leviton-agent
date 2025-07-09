import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Calendar, ArrowRight, BarChart3, TrendingUp, MessageSquare, Clock, CheckCircle, AlertCircle, Loader2 } from "lucide-react"
import Link from "next/link"

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

interface ProjectCardProps {
  project: Project
  featured?: boolean
}

export function ProjectCard({ project, featured = false }: ProjectCardProps) {
  // Determine the correct link based on project status
  const getLinkHref = () => {
    if (project.overall_status === 'creating') {
      return `/project/${project.id}/progress`
    }
    return `/project/${project.id}`
  }

  // Determine if we should show the processing badge
  const showProcessingBadge = project.overall_status === 'creating'
  
  const linkHref = getLinkHref()
  const chatHref = `/project/${project.id}/chat?from=home`
  
  return (
    <Card className={`${featured ? "border-blue-200 bg-blue-50/30" : ""} hover:shadow-md transition-shadow`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <CardTitle className={`${featured ? "text-lg" : "text-base"} line-clamp-2`}>{project.project_name}</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs w-fit">
                {project.description || "Analysis Project"}
              </Badge>
              {/* Only show processing badge when project is being created */}
              {showProcessingBadge && (
                <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700 border-blue-200">
                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  Processing
                </Badge>
              )}
            </div>
          </div>
          {featured && <Badge className="bg-blue-100 text-blue-700 border-blue-200">Current</Badge>}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Calendar className="w-3 h-3" />
              <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center space-x-1">
              <TrendingUp className="w-3 h-3" />
              <span>Updated {new Date(project.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Display project statistics if available */}
        {(project.total_products || project.total_brands || project.total_reviews) && (
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-4">
            {project.total_products && (
              <span>{project.total_products} products</span>
            )}
            {project.total_brands && (
              <span>{project.total_brands} brands</span>
            )}
            {project.total_reviews && (
              <span>{project.total_reviews} reviews</span>
            )}
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {/* Simplified status display based on overall_status */}
            {project.overall_status === 'ready' ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-700">Ready for Analysis</span>
              </>
            ) : project.overall_status === 'failed' ? (
              <>
                <AlertCircle className="w-4 h-4 text-red-500" />
                <span className="text-sm text-red-700">Failed</span>
              </>
            ) : project.overall_status === 'creating' ? (
              <></>
            ) : (
              <>
                <BarChart3 className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-600">Ready</span>
              </>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {/* Only show Chat button for ready projects */}
            {project.overall_status === 'ready' && (
              <Link href={chatHref}>
                <Button variant="ghost" size="sm">
                  <MessageSquare className="w-3 h-3 mr-1" />
                  Chat
                </Button>
              </Link>
            )}
            
            {/* Main action button */}
            <Link href={linkHref}>
              <Button variant={featured ? "default" : "outline"} size="sm">
                {project.overall_status === 'creating' ? (
                  <>
                    <Clock className="w-3 h-3 mr-1" />
                    View Progress
                  </>
                ) : featured ? (
                  <>
                    Continue
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </>
                ) : (
                  <>
                    View Project
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </>
                )}
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 