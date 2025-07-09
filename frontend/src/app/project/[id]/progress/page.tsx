"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ArrowLeft, CheckCircle } from "lucide-react"
import Link from "next/link"
import { ProtectedRoute } from "@/components/auth/protected-route"

// Import the same components used in data-confirmation-tab.tsx
const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

interface ProjectProgress {
  project_id: string;
  project_name: string;
  status: string;
  segmentation_status: string;
  review_analysis_status?: string;
  total_products: number;
  total_reviews?: number;
  estimated_llm_calls?: number;
  created_at?: string;
  steps: {
    step: string;
    name: string;
    status: string;
    started_at?: string;
    completed_at?: string;
    description: string;
    sub_steps?: {
      name: string;
      status: string;
      description?: string;
    }[];
    current_stage?: string;
  }[];
}

// Re-use the exact same ProjectProgressDisplay component logic
function ProjectProgressDisplay({ projectId, onAnalysisReady }: { 
  projectId: string; 
  onAnalysisReady?: (projectId: string) => void;
}) {
  const [progress, setProgress] = useState<ProjectProgress | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error' | 'closed'>('closed');
  const [isExpanded, setIsExpanded] = useState(true); // Default to expanded for dedicated progress page
  const [projectStartTime] = useState<Date>(new Date());
  const [, setTimeUpdate] = useState(0);

  const router = useRouter()

  // Calculate time progress
  const calculateTimeProgress = () => {
    const now = new Date();
    const elapsed = now.getTime() - projectStartTime.getTime();
    
    // 使用项目的实际评论数量计算估计时间，而不是写死的30分钟
    const totalReviews = progress?.total_reviews || 0;
    const estimatedMinutes = Math.max(10, Math.ceil(totalReviews / 100) * 1.5);
    const totalTime = estimatedMinutes * 60 * 1000; // 转换为毫秒
    
    const progressPercent = Math.min((elapsed / totalTime) * 100, 100);
    const remainingMinutes = Math.max(0, Math.ceil((totalTime - elapsed) / (60 * 1000)));
    
    return {
      progress: progressPercent,
      remainingMinutes,
      elapsed: Math.floor(elapsed / (60 * 1000)),
      isOverdue: elapsed > totalTime,
      estimatedTotal: estimatedMinutes
    };
  };

  // Update timer
  useEffect(() => {
    if (!projectId) return;
    
    const updateTimer = setInterval(() => {
      setTimeUpdate(prev => prev + 1);
    }, 30000);
    
    return () => clearInterval(updateTimer);
  }, [projectId]);

  // SSE connection logic (same as data-confirmation-tab.tsx)
  useEffect(() => {
    if (!projectId) {
      setProgress(null);
      setConnectionStatus('closed');
      return;
    }

    console.log('🚀 Setting up SSE connection for project:', projectId);
    setConnectionStatus('connecting');
    
    const eventSource = new EventSource(`${API_BASE_URL}/api/v1/projects/progress-stream/${projectId}`);
    
    eventSource.onopen = () => {
      console.log('✅ SSE connection opened for project:', projectId);
      setConnectionStatus('connected');
    };
    
    eventSource.onmessage = (event) => {
      try {
        const progressData = JSON.parse(event.data);
        
        if (progressData.type === 'heartbeat') {
          console.log('💓 Received heartbeat');
          return;
        }
        
        console.log('📨 Received SSE progress update:', {
          project_id: progressData.project_id,
          steps: progressData.steps?.map((s: { name: string; status: string }) => `${s.name}: ${s.status}`) || []
        });
        
        setProgress(progressData);
        
        const isCompleted = progressData.segmentation_status === 'completed' && 
                           progressData.review_analysis_status === 'completed';
        
        if (isCompleted) {
          console.log('🎉 Project completed, closing SSE connection');
          setConnectionStatus('closed');
          eventSource.close();
          
          // Auto-redirect to project analysis page when completed
          if (onAnalysisReady) {
            onAnalysisReady(projectId);
          }
        }
      } catch (error) {
        console.error('❌ Error parsing SSE message:', error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('❌ SSE connection error for project:', projectId, error);
      setConnectionStatus('error');
    };

    return () => {
      console.log('🧹 Cleaning up SSE connection for project:', projectId);
      eventSource.close();
      setConnectionStatus('closed');
    };
  }, [projectId, onAnalysisReady]);

  // Handle navigation when analysis is ready
  const handleAnalysisReady = (projectId: string) => {
    router.push(`/project/${projectId}`)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
        return (
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        );
      case 'failed':
        return <div className="w-4 h-4 bg-red-500 rounded-full" />;
      default:
        return <div className="w-4 h-4 bg-gray-300 rounded-full" />;
    }
  };

  // Show loading if no progress data yet
  if (!progress) {
    return (
      <div className="space-y-6">
        <div className="text-center py-8">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">
            {connectionStatus === 'connecting' ? 'Connecting to progress stream...' :
             connectionStatus === 'error' ? 'Connection error. Please refresh the page.' :
             'Loading project progress...'}
          </p>
        </div>
      </div>
    );
  }

  const timeProgress = calculateTimeProgress();
  const isCompleted = progress.segmentation_status === 'completed' && 
                     progress.review_analysis_status === 'completed';

  return (
    <div className="space-y-6">
      {/* Project Info */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">{progress.project_name}</h2>
            <p className="text-gray-600">{progress.total_products} products selected for analysis</p>
          </div>
          {isCompleted && (
            <Button onClick={() => handleAnalysisReady(progress.project_id)}>
              <CheckCircle className="w-4 h-4 mr-2" />
              View Analysis Results
            </Button>
          )}
        </div>

        {/* Time Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Processing Progress</span>
            <span>
              {timeProgress.isOverdue 
                ? `Overdue by ${timeProgress.elapsed - timeProgress.estimatedTotal} minutes` 
                : `${timeProgress.remainingMinutes} minutes remaining`}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                timeProgress.isOverdue ? 'bg-red-500' : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(timeProgress.progress, 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Estimated completion time: ~{timeProgress.estimatedTotal} minutes
          </p>
        </div>

        {/* Steps Progress */}
        <div className="space-y-4">
          {progress.steps.map((step, index) => (
            <div key={step.step} className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(step.status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-gray-900">{step.name}</h4>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    step.status === 'completed' ? 'bg-green-100 text-green-800' :
                    step.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                    step.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {step.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                
                {/* Sub-steps */}
                {step.sub_steps && step.sub_steps.length > 0 && (
                  <div className="mt-3 ml-4 space-y-2">
                    {step.sub_steps.map((subStep, subIndex) => (
                      <div key={subIndex} className="flex items-center space-x-2">
                        <div className="w-2 h-2 rounded-full bg-gray-300" />
                        <span className="text-xs text-gray-600">{subStep.name}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          subStep.status === 'completed' ? 'bg-green-100 text-green-700' :
                          subStep.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {subStep.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Current stage info */}
                {step.current_stage && step.status === 'processing' && (
                  <div className="mt-2 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    Current: {step.current_stage}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ProjectProgressPage() {
  const params = useParams()
  const projectId = params.id as string

  const handleAnalysisReady = (projectId: string) => {
    // This will be handled by the component itself
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
                
                <div className="flex flex-col">
                  <h1 className="text-xl font-semibold">Project Progress</h1>
                  <p className="text-sm text-muted-foreground">
                    Monitoring research project creation and analysis
                  </p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <ProjectProgressDisplay 
            projectId={projectId} 
            onAnalysisReady={handleAnalysisReady} 
          />
        </main>
      </div>
    </ProtectedRoute>
  )
} 