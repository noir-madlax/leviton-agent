'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

import { CheckCircle, Database, Users, MessageSquare, Filter, Eye, Check, RefreshCw, Clock, AlertCircle, Loader2, Lightbulb } from 'lucide-react';
import { type DataConfirmationData, type DataConfirmationFilters } from '@/components/analysis-db/data/database-service';
import { CategorySelector } from '@/components/category-selector';
import { useAuth } from '@/contexts/auth-context';
import { usePermissions } from '@/hooks/use-permissions';

// URL分析相关接口
interface CategorySuggestion {
  category_id: string;
  category_name: string;
  confidence: number;
  reason: string;
}

interface AnalyzeUrlResponse {
  success: boolean;
  url_type: string;
  suggestions: CategorySuggestion[];
  confidence_level: string;
  message: string;
}

// 进度显示接口
interface ProjectProgress {
  project_id: string;
  project_name: string;
  status: string;
  segmentation_status: string;
  review_analysis_status?: string;
  total_products: number;
  total_reviews?: number;
  estimated_llm_calls?: number;
  created_at?: string; // 项目创建时间
  segmentation_started_at?: string; // 分割开始时间
  segmentation_completed_at?: string; // 分割完成时间
  review_analysis_started_at?: string; // 评论分析开始时间
  review_analysis_completed_at?: string; // 评论分析完成时间
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

// 🔥 重新设计：项目进度显示组件 - 简化状态管理
function ProjectProgressDisplay({ projectId, onAnalysisReady, totalProducts, totalReviews, projectName }: { 
  projectId: string | null; 
  onAnalysisReady?: (projectId: string) => void;
  totalProducts?: number;
  totalReviews?: number;
  projectName?: string;
}) {
  const [progress, setProgress] = useState<ProjectProgress | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error' | 'closed'>('closed');
  const [isExpanded, setIsExpanded] = useState(false);
  const [, setTimeUpdate] = useState(0); // 用于强制重新渲染时间进度条

  // 🔥 修复：计算时间进度的函数 - 正确处理项目时间状态
  const calculateTimeProgress = () => {
    const now = new Date();
    
    // 🔥 关键修复：根据项目状态使用正确的时间基准
    let actualStartTime: Date;
    let actualEndTime: Date | null = null;
    let isProjectCompleted = false;
    
    // 1. 确定项目的实际开始时间（处理开始时间，不是创建时间）
    if (progress?.segmentation_started_at) {
      actualStartTime = new Date(progress.segmentation_started_at);
    } else if (progress?.created_at) {
      // 如果没有分割开始时间，使用创建时间作为fallback
      actualStartTime = new Date(progress.created_at);
    } else {
      // 最后的fallback
      actualStartTime = new Date(now.getTime() - 5 * 60 * 1000);
    }
    
    // 2. 确定项目是否完成以及完成时间
    const segmentationCompleted = progress?.segmentation_status === 'completed';
    const reviewAnalysisCompleted = progress?.review_analysis_status === 'completed';
    isProjectCompleted = segmentationCompleted && reviewAnalysisCompleted;
    
    if (isProjectCompleted && progress?.review_analysis_completed_at) {
      actualEndTime = new Date(progress.review_analysis_completed_at);
    }
    
    // 3. 计算时间进度
    const currentTime = actualEndTime || now; // 如果完成了使用完成时间，否则使用当前时间
    const elapsed = currentTime.getTime() - actualStartTime.getTime();
    const elapsedMinutes = Math.floor(elapsed / (60 * 1000));
    
    // 4. 计算预计时间和剩余时间
    let estimatedMinutes: number;
    let remainingMinutes: number;
    let progressPercentage: number;
    
    if (isProjectCompleted) {
      // 项目已完成：显示实际耗时
      estimatedMinutes = elapsedMinutes;
      remainingMinutes = 0;
      progressPercentage = 100;
    } else {
      // 项目进行中：基于当前状态动态估算
      const baseEstimate = Math.max(10, Math.ceil((totalReviews || 0) / 100) * 1.5);
      
      // 根据项目进度调整估算时间
      if (reviewAnalysisCompleted) {
        // 评论分析完成，只剩数据准备
        estimatedMinutes = elapsedMinutes + 1;
        remainingMinutes = 1;
        progressPercentage = 95;
      } else if (segmentationCompleted) {
        // 分割完成，评论分析进行中
        const reviewEstimate = Math.max(5, Math.ceil((totalReviews || 0) / 200) * 1.2);
        estimatedMinutes = elapsedMinutes + reviewEstimate;
        remainingMinutes = reviewEstimate;
        progressPercentage = Math.min((elapsedMinutes / estimatedMinutes) * 100, 90);
      } else {
        // 分割进行中
        estimatedMinutes = baseEstimate;
        const totalTime = estimatedMinutes * 60 * 1000;
        progressPercentage = Math.min((elapsed / totalTime) * 100, 80);
        remainingMinutes = Math.max(0, Math.ceil((totalTime - elapsed) / (60 * 1000)));
      }
    }
    
    return {
      progress: progressPercentage,
      remainingMinutes,
      elapsed: elapsedMinutes,
      isOverdue: !isProjectCompleted && elapsed > (estimatedMinutes * 60 * 1000),
      estimatedTotal: estimatedMinutes,
      isCompleted: isProjectCompleted,
      actualStartTime: actualStartTime.toISOString(),
      actualEndTime: actualEndTime?.toISOString() || null,
      // 🔥 新增：用于显示的状态信息
      statusText: isProjectCompleted ? 'Completed' : 'In Progress'
    };
  };

  // 时间进度条定时更新
  useEffect(() => {
    if (!projectId) return;
    
    const updateTimer = setInterval(() => {
      setTimeUpdate(prev => prev + 1);
    }, 30000); // 每30秒更新一次
    
    return () => clearInterval(updateTimer);
  }, [projectId]);

  // 🔥 重新设计：简化的SSE连接逻辑
  useEffect(() => {
    // 如果没有projectId，说明还未创建或正在等待ID
    if (!projectId) {
      setProgress(null);
      setConnectionStatus('closed');
      return;
    }

    console.log('🚀 Setting up SSE connection for project:', projectId);
    setConnectionStatus('connecting');
    
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
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
  }, [projectId]); // 只依赖projectId

  // 🔥 新的渲染逻辑
  // 1. 正在创建，但还没有ID
  if (projectId === null) {
    return (
      <Card className="mb-6 border-l-4 border-l-blue-500">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
            Creating New Project...
          </CardTitle>
          <CardDescription>
            Please wait while we initialize the project and prepare for analysis.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // 2. 有ID了，但还没有收到第一个进度消息
  if (!progress) {
    return (
      <Card className="mb-6 border-l-4 border-l-blue-500">
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
            <span className="text-sm text-gray-600">
              {connectionStatus === 'connecting' ? 'Connecting to progress stream...' :
               connectionStatus === 'error' ? 'Connection error. Please refresh the page.' :
               'Loading project progress...'}
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'in_progress':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'in_progress':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'failed':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  // 3. 正常显示进度
  const isProjectFullyCompleted = progress.segmentation_status === 'completed' && 
    progress.steps?.every(step => step.status === 'completed' || step.status === 'failed');

  const timeProgress = calculateTimeProgress();
  const displayProjectName = projectName || progress.project_name || 'Research Project';

  return (
    <Card className={`mb-6 border-l-4 ${isProjectFullyCompleted ? 'border-l-green-500' : 'border-l-blue-500'}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className={`w-5 h-5 ${isProjectFullyCompleted ? 'text-green-500' : 'text-blue-500'}`} />
            <span className="text-lg">Project Progress: {displayProjectName}</span>
            {connectionStatus === 'connecting' && <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />}
            {isProjectFullyCompleted && <CheckCircle className="w-5 h-5 text-green-500" />}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs"
          >
            {isExpanded ? 'Hide Details' : 'Show Details'}
          </Button>
        </CardTitle>
        
        {/* 时间进度条 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">
              {timeProgress.isCompleted ? 'Total Processing Time' : 'Time Progress'}: {timeProgress.elapsed}min
              {!timeProgress.isCompleted && timeProgress.estimatedTotal > 0 && ` / ${timeProgress.estimatedTotal}min`}
            </span>
            <span className={`text-sm ${timeProgress.isCompleted ? 'text-green-600' : timeProgress.isOverdue ? 'text-red-600' : 'text-gray-600'}`}>
              {timeProgress.isCompleted ? 'Project Completed!' : 
               timeProgress.isOverdue ? 'Overdue' : 
               `${timeProgress.remainingMinutes}min remaining`}
            </span>
          </div>
          {/* 🔥 调试信息：在开发环境下显示实际的项目时间信息 */}
          {process.env.NODE_ENV === 'development' && (
            <div className="text-xs text-gray-400 space-y-1">
              {timeProgress.actualStartTime && (
                <div>Started: {new Date(timeProgress.actualStartTime).toLocaleString()}</div>
              )}
              {timeProgress.actualEndTime && (
                <div>Completed: {new Date(timeProgress.actualEndTime).toLocaleString()}</div>
              )}
              <div>Status: {timeProgress.statusText}</div>
            </div>
          )}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                timeProgress.isOverdue ? 'bg-red-500' : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(timeProgress.progress, 100)}%` }}
            />
          </div>
          {!isProjectFullyCompleted && (
            <div className="text-xs text-gray-500 mt-1">
              💡 You can safely leave this page. Your project will continue processing in the background.
            </div>
          )}
        </div>
        
        <CardDescription>
          Processing status for {progress.total_products || totalProducts || 0} products
         
         
          {isProjectFullyCompleted && (
            <span className="text-green-600 font-medium"> • Analysis Ready!</span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* 简化版本显示 */}
        {!isExpanded && (
          <div className="space-y-3">
            {/* 总体进度概览 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex -space-x-1">
                                     {progress.steps.map((step) => (
                    <div key={step.step} className="w-3 h-3 rounded-full border border-white">
                      {step.status === 'completed' && <div className="w-full h-full bg-green-500 rounded-full" />}
                      {step.status === 'in_progress' && <div className="w-full h-full bg-blue-500 rounded-full animate-pulse" />}
                      {step.status === 'failed' && <div className="w-full h-full bg-red-500 rounded-full" />}
                      {step.status === 'pending' && <div className="w-full h-full bg-gray-300 rounded-full" />}
                    </div>
                  ))}
                </div>
                <span className="text-sm text-gray-600">
                  {progress.steps.filter(s => s.status === 'completed').length} of {progress.steps.length} steps completed
                </span>
              </div>
              {/* 只在项目完成或失败时显示Badge状态 */}
              {(progress.status === 'completed' || progress.status === 'failed') && (
                <Badge variant="outline" className={getStatusColor(progress.status)}>
                  {progress.status.replace('_', ' ')}
                </Badge>
              )}
            </div>
            
            {/* 当前进行的步骤 */}
            {progress.steps.find(s => s.status === 'in_progress') && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                  <span className="text-sm font-medium text-blue-900">
                    {progress.steps.find(s => s.status === 'in_progress')?.name}
                  </span>
                </div>
                <p className="text-xs text-blue-700 mt-1">
                  {progress.steps.find(s => s.status === 'in_progress')?.description}
                </p>
              </div>
            )}
          </div>
        )}
        
        {/* 详细版本显示 */}
        {isExpanded && (
          <div className="space-y-3">
            {progress.steps.map((step) => (
              <div key={step.step} className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-1">
                  {getStatusIcon(step.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-sm">{step.name}</h4>
                    <Badge variant="outline" className={getStatusColor(step.status)}>
                      {step.status.replace('_', ' ')}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{step.description}</p>
                  
                  {/* 🔥 增强子步骤显示 - 显示更详细的批次信息 */}
                  {step.sub_steps && step.sub_steps.length > 0 && (
                    <div className="mt-2 ml-4 space-y-1">
                      {step.sub_steps.map((subStep, subIndex) => (
                        <div key={subIndex} className="flex items-center justify-between gap-2 text-xs">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(subStep.status)}
                            <span className={subStep.status === 'completed' ? 'text-green-700' : subStep.status === 'in_progress' ? 'text-blue-700' : 'text-gray-500'}>
                              {subStep.name}
                            </span>
                          </div>
                          {subStep.description && (
                            <span className="text-gray-500 text-xs">
                              {subStep.description}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* 🔥 新增：显示当前处理阶段的详细信息 */}
                  {step.current_stage && step.status === 'in_progress' && (
                    <div className="mt-2 ml-4 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                      <span className="font-medium text-blue-800">Current Stage: </span>
                      <span className="text-blue-700 capitalize">{step.current_stage.replace('_', ' ')}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* 项目状态显示 - 根据项目状态显示不同内容 */}
        {!isProjectFullyCompleted ? (
          <div className="pt-4 border-t mt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                <span className="font-medium text-blue-700">Processing</span>
              </div>
              <span className="text-sm text-gray-600">
                {progress.steps.filter(s => s.status === 'completed').length} of {progress.steps.length} steps completed
              </span>
            </div>
          </div>
        ) : (
          /* 项目完成后显示跳转按钮 */
          onAnalysisReady && projectId && (
            <div className="pt-4 border-t mt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span className="font-medium text-green-700">Project Ready for Analysis!</span>
                </div>
                <Button 
                  onClick={() => onAnalysisReady(projectId)}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  Go to Analysis Dashboard
                </Button>
              </div>
            </div>
          )
        )}
      </CardContent>
    </Card>
  );
}

export function DataConfirmationTab({ 
  onNavigateToAnalysis, 
  onRegisterCreateProject,
  projectName 
}: { 
  onNavigateToAnalysis?: (projectId: string) => void;
  onRegisterCreateProject?: (ref: {
    handleConfirmSelection: () => void;
    isConfirmed: boolean;
    isFilterApplied: boolean;
    hasEnoughData: boolean;
    generateSmartProjectName: () => string;
    estimatedTime: string;
  }) => void;
  projectName?: string;
}) {
  // 暂时不使用onNavigateToAnalysis，让用户看到进度后手动跳转
  console.log('Navigation callback available:', !!onNavigateToAnalysis);
  const { user } = useAuth();
  const { permissions } = usePermissions();
  const [data, setData] = useState<DataConfirmationData | null>(null);
  const [pageLoading, setPageLoading] = useState(true); // 页面初始加载
  const [filterLoading, setFilterLoading] = useState(false); // 筛选数据加载
  const [filters, setFilters] = useState<DataConfirmationFilters>({
    categories: [],
    sources: [],
    brands: [],
    topSalesCount: 100
  });
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [createdProjectId, setCreatedProjectId] = useState<string | null>(null);
  const [projectCreationStatus, setProjectCreationStatus] = useState<'idle' | 'creating' | 'created'>('idle');
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('');
  const [selectedCategoryName, setSelectedCategoryName] = useState<string>('');
  const [selectedCategoryPath, setSelectedCategoryPath] = useState<string>('');
  const [isFilterApplied, setIsFilterApplied] = useState(false); // Track if filter has been applied
  const [hasEverAppliedFilter, setHasEverAppliedFilter] = useState(false); // Track if user has ever applied filter
  const [showAllCategories, setShowAllCategories] = useState(false); // 控制Categories展开状态
  const [showAllBrands, setShowAllBrands] = useState(false); // 控制Brands展开状态
  const [categoryInput, setCategoryInput] = useState<string>(''); // 新增：类别URL或node ID输入
  
  // URL分析相关状态
  const [urlAnalyzing, setUrlAnalyzing] = useState(false);
  const [urlAnalysisResult, setUrlAnalysisResult] = useState<AnalyzeUrlResponse | null>(null);
  const [showUrlSuggestions, setShowUrlSuggestions] = useState(false);
  
  // Preview区域的ref，用于自动滚动
  const previewRef = useRef<HTMLDivElement>(null);

  // 生成智能project名字
  const generateSmartProjectName = () => {
    const now = new Date();
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = monthNames[now.getMonth()];
    const day = String(now.getDate()).padStart(2, '0');
    
    // Use the last part of the category path or fallback to category name
    let categoryForName = selectedCategoryName || '';
    if (selectedCategoryPath) {
      const pathParts = selectedCategoryPath.split(' > ');
      categoryForName = pathParts[pathParts.length - 1]; // Use the most specific category
    }
    
    // 如果没有选择category，使用默认名称
    if (!categoryForName) {
      categoryForName = 'Products';
    }
    
    // Clean category name for use in project name
    const cleanCategory = categoryForName.replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '_');
    
    return `${cleanCategory}_Top${filters.topSalesCount || 100}_${month}${day}`;
  };

  // 初始加载数据（只执行一次）
  useEffect(() => {
    loadInitialData();
  }, []);

  // 移除实时更新project名字的逻辑，改为在Apply后由父组件处理

  // 初始加载数据 - 只加载基础配置数据，不计算统计信息
  const loadInitialData = async () => {
    setPageLoading(true);
    try {
      // 使用后端API获取基础数据（不包含统计信息）
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/data-confirmation`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      
      // 只保留基础配置数据，清空统计信息
      setData({
        ...result,
        stats: {
          totalProducts: 0,
          totalBrands: 0,
          totalReviews: 0,
          sources: [],
          categories: [],
          brands: []
        },
        topProducts: [] // 清空产品预览
      });
      
      // 修改：Categories默认为空，不全选，用户必须手动选择
      setFilters({
        categories: [], // 默认为空，用户必须手动选择
        sources: result.availableSources, // 数据源默认全选
        brands: [], // 品牌默认为空，等用户选择品类后动态加载
        topSalesCount: 100
      });
    } catch (error) {
      console.error('Failed to load initial data:', error);
    } finally {
      setPageLoading(false);
    }
  };

  // Handle category selection from CategorySelector
  const handleCategorySelect = (categoryId: string, categoryName: string, level: number, categoryPath?: string) => {
    setSelectedCategoryId(categoryId);
    setSelectedCategoryName(categoryName);
    setSelectedCategoryPath(categoryPath || categoryName);
    setIsConfirmed(false); // Reset confirmation when category changes
    setIsFilterApplied(false); // Reset filter applied state when category changes
    // 重置展开状态
    setShowAllCategories(false);
    setShowAllBrands(false);
    
    // 🔥 关键修复：将选中的类别同步到filters.categories
    setFilters(prev => ({
      ...prev,
      categories: categoryName ? [categoryName] : [] // 将类别名称添加到filters中
    }));
  };

  // 检测URL类型的辅助函数
  const detectInputType = (input: string): 'url' | 'node_id' | 'empty' => {
    if (!input.trim()) return 'empty';
    
    // Check if it's a URL (contains amazon.com or amazon domain)
    if (input.includes('amazon.') || input.includes('amzn.') || input.startsWith('http')) {
      return 'url';
    }
    
    // Check if it's node ID format
    if (input.includes('node=') || /^\d+$/.test(input.trim())) {
      return 'node_id';
    }
    
    // If contains other URL patterns, treat as URL
    if (input.includes('/') || input.includes('?') || input.includes('&')) {
      return 'url';
    }
    
    return 'node_id'; // Default fallback
  };

  // 新增：处理类别输入（URL或node ID）
  const handleCategoryInputChange = async (value: string) => {
    setCategoryInput(value);
    
    // Reset previous analysis
    setUrlAnalysisResult(null);
    setShowUrlSuggestions(false);
    
    const inputType = detectInputType(value);
    
    if (inputType === 'empty') {
      // 清空选择
      setSelectedCategoryId('');
      setSelectedCategoryName('');
      setSelectedCategoryPath('');
      setFilters(prev => ({
        ...prev,
        categories: []
      }));
      return;
    }
    
    if (inputType === 'url') {
      // 处理URL分析
      await handleUrlAnalysis(value);
    } else {
      // 处理node ID（保持原有逻辑）
      await handleNodeIdInput(value);
    }
  };

  // 处理URL分析
  const handleUrlAnalysis = async (url: string) => {
    console.log('🔍 Starting URL analysis for:', url);
    setUrlAnalyzing(true);
    
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      console.log('📡 Making API request to:', `${API_BASE_URL}/api/v1/categories/analyze-url`);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/categories/analyze-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });
      
      console.log('📨 Response status:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ HTTP error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }
      
      const result: AnalyzeUrlResponse = await response.json();
      console.log('✅ URL analysis result received:', result);
      setUrlAnalysisResult(result);
      
      if (result.success && result.suggestions.length > 0) {
        console.log(`🎯 Found ${result.suggestions.length} suggestions`);
        setShowUrlSuggestions(true);
        
        // If high confidence, auto-select the first suggestion
        if (result.confidence_level === 'high' && result.suggestions[0].confidence >= 0.9) {
          console.log('🚀 Auto-selecting high confidence suggestion');
          const suggestion = result.suggestions[0];
          await applyCategorySuggestion(suggestion);
        }
      } else {
        console.log('⚠️ No valid suggestions received');
        setShowUrlSuggestions(true);
      }
      
    } catch (error) {
      console.error('💥 Error analyzing URL:', error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      setUrlAnalysisResult({
        success: false,
        url_type: 'unknown',
        suggestions: [],
        confidence_level: 'none',
        message: `Failed to analyze URL: ${errorMessage}`
      });
      setShowUrlSuggestions(true);
    } finally {
      setUrlAnalyzing(false);
      console.log('🔍 URL analysis completed');
    }
  };

  // 处理node ID输入（原有逻辑）
  const handleNodeIdInput = async (value: string) => {
    let nodeId = '';
    if (value.includes('node=')) {
      const match = value.match(/node=(\d+)/);
      if (match) {
        nodeId = match[1];
      }
    } else if (/^\d+$/.test(value.trim())) {
      nodeId = value.trim();
    }
    
    if (nodeId) {
      console.log('🔍 Starting Node ID analysis for:', nodeId);
      setUrlAnalyzing(true);
      
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/v1/categories/name/${nodeId}`);
        
        let categoryName = `Category ${nodeId}`;
        let categoryPath = `Category ${nodeId}`;
        
        if (response.ok) {
          const categoryData = await response.json();
          categoryName = categoryData.name || `Category ${nodeId}`;
          categoryPath = categoryData.full_path || categoryData.name || `Category ${nodeId}`;
        } else {
          console.warn(`Failed to fetch category name for ${nodeId}, using fallback`);
        }
        
        // 设置选中的类别
        setSelectedCategoryId(nodeId);
        setSelectedCategoryName(categoryName);
        setSelectedCategoryPath(categoryPath);
        setIsConfirmed(false);
        setIsFilterApplied(false);
        setShowAllCategories(false);
        setShowAllBrands(false);
        
        setFilters(prev => ({
          ...prev,
          categories: [categoryName]
        }));
      } catch (error) {
        console.error('Error fetching category name:', error);
        // 使用fallback显示
        setSelectedCategoryId(nodeId);
        setSelectedCategoryName(`Category ${nodeId}`);
        setSelectedCategoryPath(`Category ${nodeId}`);
        setIsConfirmed(false);
        setIsFilterApplied(false);
        setShowAllCategories(false);
        setShowAllBrands(false);
        
        setFilters(prev => ({
          ...prev,
          categories: [`Category ${nodeId}`]
        }));
      } finally {
        setUrlAnalyzing(false);
        console.log('🔍 Node ID analysis completed');
      }
    }
  };

  // 应用类别建议
  const applyCategorySuggestion = async (suggestion: CategorySuggestion) => {
    setSelectedCategoryId(suggestion.category_id);
    setSelectedCategoryName(suggestion.category_name);
    setSelectedCategoryPath(suggestion.category_name); // Will be updated if we have full path info
    setIsConfirmed(false);
    setIsFilterApplied(false);
    setShowAllCategories(false);
    setShowAllBrands(false);
    setShowUrlSuggestions(false);
    
    setFilters(prev => ({
      ...prev,
      categories: [suggestion.category_name]
    }));
    
    // Try to get full path info
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/categories/name/${suggestion.category_id}`);
      
      if (response.ok) {
        const categoryData = await response.json();
        if (categoryData.full_path) {
          setSelectedCategoryPath(categoryData.full_path);
        }
      }
    } catch (error) {
      console.error('Error fetching category path:', error);
    }
  };

  // 手动筛选数据
  const handleFilterData = async () => {
    if (!selectedCategoryId) {
      alert('Please select a category first');
      return;
    }
    
    // 🔥 修复：立即显示loading状态
    setFilterLoading(true);
    // 重置展开状态
    setShowAllCategories(false);
    setShowAllBrands(false);
    
    try {
      // 构建查询参数
      const params = new URLSearchParams();
      
      // Use category_id instead of category names
      if (selectedCategoryId) {
        params.append('category_id', selectedCategoryId);
      }
      if (filters.sources.length > 0) {
        filters.sources.forEach(src => params.append('sources', src));
      }
      if (filters.brands.length > 0) {
        filters.brands.forEach(brand => params.append('brands', brand));
      }
      if (filters.topSalesCount) {
        params.append('top_sales_count', filters.topSalesCount.toString());
      }
      
      // 使用新的category-based API进行筛选查询
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/data-confirmation-by-category?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setData(result);
      setIsFilterApplied(true); // Mark filter as applied
      setHasEverAppliedFilter(true); // Mark that user has ever applied filter
      
      // 自动滚动到Preview区域
      setTimeout(() => {
        previewRef.current?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'center'
        });
      }, 200);
    } catch (error) {
      console.error('Failed to filter data:', error);
    } finally {
      setFilterLoading(false);
    }
  };

  // 直接使用后端返回的统计数据
  const filteredStats = useMemo(() => {
    if (!data) return null;
    return data.stats;
  }, [data]);

  // 计算预计处理时间的函数
  const calculateEstimatedTime = useMemo(() => {
    if (!filteredStats?.totalReviews) return { minutes: 10, text: "~10 minutes" };
    
    // 每100条评论需要1.5分钟，最少10分钟
    const minutes = Math.max(10, Math.ceil((filteredStats.totalReviews / 100) * 1.5));
    
    if (minutes < 60) {
      return { minutes, text: `~${minutes} minutes` };
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      if (remainingMinutes === 0) {
        return { minutes, text: `~${hours} hour${hours > 1 ? 's' : ''}` };
      } else {
        return { minutes, text: `~${hours}h ${remainingMinutes}m` };
      }
         }
   }, [filteredStats?.totalReviews]);

  // 检查数据是否足够创建项目
  const hasEnoughData = useMemo(() => {
    return Boolean(
      isFilterApplied && 
      filteredStats && 
      filteredStats.totalProducts > 0 && 
      filteredStats.totalReviews > 0
    );
  }, [filteredStats, isFilterApplied]);

  // 注册创建项目的方法到父组件
  useEffect(() => {
    if (onRegisterCreateProject) {
      onRegisterCreateProject({
        handleConfirmSelection,
        isConfirmed,
        isFilterApplied,
        hasEnoughData,
        generateSmartProjectName,
        estimatedTime: hasEnoughData ? calculateEstimatedTime.text : ''
      });
    }
  }, [isConfirmed, isFilterApplied, hasEnoughData, onRegisterCreateProject, calculateEstimatedTime.text]);
  
    // 未使用的处理函数，保留以备后续使用
  // const handleSourceChange = (source: string, checked: boolean) => {
  //   setFilters(prev => ({
  //     ...prev,
  //     sources: checked 
  //       ? [...prev.sources, source]
  //       : prev.sources.filter(s => s !== source)
  //   }));
  // };

  // const handleSelectAllSources = () => {
  //   if (!data) return;
  //   setFilters(prev => ({
  //     ...prev,
  //     sources: [...data.availableSources]
  //   }));
  // };

  // const handleClearAllSources = () => {
  //   setFilters(prev => ({
  //     ...prev,
  //     sources: []
  //   }));
  // };

  const handleTopSalesCountChange = (value: string) => {
    setFilters(prev => ({
      ...prev,
      topSalesCount: value === 'all' ? undefined : parseInt(value)
    }));
  };

  const handleConfirmSelection = async () => {
    if (!filteredStats) return;
    
    setProjectCreationStatus('creating');
    setIsConfirmed(true);
    
    try {
      // 🔥 修复：确保项目名正确生成
      const finalProjectName = projectName && projectName !== 'New Project 1' 
        ? projectName 
        : generateSmartProjectName();
      
      // 调用后端API创建项目
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_name: finalProjectName,
          company_name: 'Leviton',
          user_name: user?.email || 'Current User',
          user_uid: user?.id, // 添加用户UID
          description: `Analysis project for ${filters.categories.join(', ')} products from ${filters.sources.join(', ')}`,
          filters: {
            categories: filters.categories,
            sources: filters.sources,
            brands: filters.brands,
            top_sales_count: filters.topSalesCount,
            // 🔥 关键修复：同时传递category_id，确保与Apply Filter逻辑一致
            category_id: selectedCategoryId
          }
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const savedProject = await response.json();
      console.log('Project saved successfully:', savedProject);
      
      // 🔥 关键修复：设置项目ID，并更新状态为'created'
      setCreatedProjectId(savedProject.id);
      setProjectCreationStatus('created');
      
      // 🔥 新增：立即获取一次真实进度，避免显示延迟
      console.log('Project created successfully, immediately fetching real progress...');
      
      // 🔥 新增：自动滚动到页面顶部
      window.scrollTo({ top: 0, behavior: 'smooth' });
      
      // 不自动跳转，让用户看到进度
      // 可以在进度完成后再跳转
      // if (onNavigateToAnalysis) {
      //   onNavigateToAnalysis(savedProject.id);
      // }
    } catch (error) {
      console.error('Failed to save project:', error);
      setIsConfirmed(false); // 重置确认状态
      setProjectCreationStatus('idle'); // 🔥 状态重置
      setCreatedProjectId(null); // 重置项目ID
      // 显示错误提示
      alert('Failed to create project. Please try again.');
    }
  };

  const resetFilters = () => {
    if (!data) return;
    setFilters({
      categories: [], // 重置时也不默认选择品类
      sources: data.availableSources,
      brands: [], // 重置时清空品牌，等用户选择品类后动态加载
      topSalesCount: 100
    });
    setSelectedCategoryId('');
    setSelectedCategoryName('');
    setSelectedCategoryPath('');
    setCategoryInput(''); // 重置类别输入框
    setIsConfirmed(false);
    setIsFilterApplied(false); // Reset filter applied state
    setHasEverAppliedFilter(false); // Reset ever applied filter state
    setProjectCreationStatus('idle'); // 🔥 重置时也重置创建状态
    setCreatedProjectId(null);
    
    // 重置时需要清空品牌数据显示
    if (data) {
      setData(prev => ({
        ...prev!,
        stats: {
          ...prev!.stats,
          brands: [] // 清空品牌统计
        }
      }));
    }
  };

  // 项目名编辑功能已移到父组件处理

  if (pageLoading) {
    return (
      <div className="h-full overflow-auto">
        <div className="max-w-7xl mx-auto space-y-6 p-6">
          <div>
            
          </div>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="h-full overflow-auto">
        <div className="max-w-7xl mx-auto space-y-6 p-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Create New Project</h1>
            <p className="text-muted-foreground mt-2">
              Failed to load product data. Please try again.
            </p>
          </div>
          <Button onClick={loadInitialData}>Retry</Button>
        </div>
      </div>
    );
  }

  return (

    
    <div className="h-full overflow-auto">
      <div className="max-w-7xl mx-auto space-y-4 p-4">
        
{/* 蓝色说明区域 - 告诉用户项目分析基于整个产品类别 - 只在项目创建前且从未应用过筛选时显示 */}
{projectCreationStatus === 'idle' && !hasEverAppliedFilter && (
<div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center mt-0.5">
                  <span className="text-white text-xs font-bold">i</span>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-blue-900 mb-1">Category-Based Analysis</h4>
                  <p className="text-sm text-blue-800 leading-relaxed">
                    Your project analysis is based on Amazon product category. We compare brand performance, 
                    competitive analysis, and user-preferred product features<strong> across products of different brands within Selected Category</strong> . 
                    This comprehensive approach ensures you get complete market insights for strategic decision making.
                  </p>
                </div>
              </div>
            </div>
)}




        {/* 选中类别显示区域 */}
        {selectedCategoryPath && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-800">Selected Category:</span>
              <span className="text-sm text-green-700 font-medium">{selectedCategoryPath}</span>
            </div>
          </div>
        )}
        
        {/* 🔥 重新设计渲染逻辑 */}
        {projectCreationStatus !== 'idle' && (
           <ProjectProgressDisplay 
             projectId={createdProjectId} 
             totalProducts={filteredStats?.totalProducts}
             totalReviews={filteredStats?.totalReviews}
             projectName={projectName}
             onAnalysisReady={(projectId) => {
               if (onNavigateToAnalysis) {
                 onNavigateToAnalysis(projectId);
               }
             }}
           />
        )}
        
        {/* 横向筛选区域 - Data Filters */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Filter className="w-5 h-5" />
              Data Selection
            </CardTitle>
            <CardDescription className="text-sm">
              Input which <strong>product category</strong> and <strong>number of products</strong> to include in your project
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-6">
              {/* Amazon Category Selector - 新版本：URL/Node ID输入 */}
              <div>
                <Label className="text-sm font-medium mb-3 block">Amazon Category Selection</Label>
                
                {/* 示例说明 */}
                <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-xs text-blue-800 font-medium mb-1">Supported Input Types:</p>
                  <div className="space-y-1 text-xs text-blue-700">
                    <div><strong>Category URLs:</strong> <code className="bg-blue-100 px-1 rounded">https://amazon.com/b?node=495324</code></div>
                    <div><strong>Node IDs:</strong> <code className="bg-blue-100 px-1 rounded">495324</code> or <code className="bg-blue-100 px-1 rounded">node=495324</code></div>
                  
                   
                  </div>
                </div>

                {/* 输入框 */}
                <Input
                  placeholder="Enter category URL or node ID"
                  value={categoryInput}
                  onChange={(e) => handleCategoryInputChange(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      if (selectedCategoryId && !filterLoading && !urlAnalyzing) {
                        handleFilterData();
                      }
                    }
                  }}
                  className="mb-2"
                />
                
                {/* URL分析状态显示 - 固定高度区域防止布局跳动 */}
                <div className="mb-0 min-h-[80px]">
                  {urlAnalyzing && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                        <span className="text-sm text-blue-700">Analyzing URL...</span>
                      </div>
                    </div>
                  )}
                  
                  {/* URL分析结果显示 */}
                  {showUrlSuggestions && urlAnalysisResult && (
                    <div>
                    {urlAnalysisResult.success ? (
                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-start gap-2 mb-2">
                          <Lightbulb className="w-4 h-4 text-green-600 mt-0.5" />
                          <div className="flex-1">
                            <div className="text-sm font-medium text-green-800 mb-1">
                              ✨ Smart Category Detection
                            </div>
                            <div className="text-xs text-green-700 mb-2">
                              We&apos;ve analyzed your {urlAnalysisResult.url_type} URL and automatically extracted the highest relevance category for your analysis.
                            </div>
                            <div className="text-xs text-green-600 mb-2 bg-green-100 px-2 py-1 rounded">
                              💡 <strong>Analysis Result:</strong> {urlAnalysisResult.message}
                            </div>
                            <div className="text-xs text-green-600 mb-2">
                              📊 <strong>Analysis Type:</strong> {urlAnalysisResult.url_type.charAt(0).toUpperCase() + urlAnalysisResult.url_type.slice(1)} URL
                            </div>
                            
                            {/* 类别建议列表 */}
                            <div className="space-y-2">
                              {urlAnalysisResult.suggestions.map((suggestion, index) => (
                                <div key={suggestion.category_id} className="bg-white border border-green-300 rounded p-3">
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <div className="font-medium text-sm text-gray-900 mb-1">
                                        {suggestion.category_name}
                                      </div>
                                      <div className="text-xs text-gray-600 mb-2">
                                        {suggestion.reason}
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <Badge 
                                          variant={suggestion.confidence >= 0.8 ? 'default' : 'secondary'}
                                          className="text-xs"
                                        >
                                          {Math.round(suggestion.confidence * 100)}% confidence
                                        </Badge>
                                        <span className="text-xs text-gray-500">
                                          ID: {suggestion.category_id}
                                        </span>
                                      </div>
                                    </div>
                                    <Button
                                      size="sm"
                                      variant={index === 0 ? "default" : "outline"}
                                      onClick={() => applyCategorySuggestion(suggestion)}
                                      className="ml-3"
                                    >
                                      Use This Category
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </div>
                            
                            {/* 高置信度自动选择提示 */}
                            {urlAnalysisResult.confidence_level === 'high' && 
                             urlAnalysisResult.suggestions.length > 0 && 
                             urlAnalysisResult.suggestions[0].confidence >= 0.9 && (
                              <div className="mt-2 text-xs text-green-600 font-medium">
                                ✓ High confidence match - automatically selected
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-red-500 mt-0.5" />
                          <div className="flex-1">
                            <div className="text-sm font-medium text-red-800 mb-1">
                              URL Analysis Failed
                            </div>
                            <div className="text-xs text-red-700">
                              {urlAnalysisResult.message}
                            </div>
                            <div className="mt-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setShowUrlSuggestions(false)}
                                className="text-xs h-6"
                              >
                                Dismiss
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                </div>
                
                {/* 原有的CategorySelector - 保留但隐藏，以备后续使用 */}
                {/* 
                  保留原有CategorySelector组件，以备后续需要时重新启用
                  如需重新使用，请取消下面代码的注释并隐藏上面的输入框
                */}
                {false && (
                  <CategorySelector
                    onCategorySelect={handleCategorySelect}
                    selectedCategoryId={selectedCategoryId}
                    selectedCategoryName={selectedCategoryName}
                    selectedCategoryPath={selectedCategoryPath}
                  />
                )}
              </div>

              {/* 数据来源筛选和销量排名筛选 - 合并在一列 */}
              <div className="space-y-4">
                {/* 数据来源筛选 */}
                
                {/* 销量排名筛选 */}
                <div>
                  <Label className="text-sm font-medium">Number of products</Label>
                  <Select
                    value={filters.topSalesCount?.toString() || 'all'}
                    onValueChange={handleTopSalesCountChange}
                  >
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                    <SelectItem value="80percent" disabled>
                        <div className="flex items-center justify-between w-full">
                          <span>Exclude Low-Volume Products</span>
                          <span className="text-xs text-gray-500 ml-2">Support soon</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="50">Top 50 Products</SelectItem>
                      <SelectItem value="100">Top 100 Products</SelectItem>
                      <SelectItem value="200" disabled>
                        <div className="flex items-center justify-between w-full">
                          <span>Top 200 Products</span>
                          <span className="text-xs text-gray-500 ml-2">Not supported during beta testing</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="500" disabled>
                        <div className="flex items-center justify-between w-full">
                          <span>Top 500 Products</span>
                          <span className="text-xs text-gray-500 ml-2">Not supported during beta testing</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="all" disabled>
                        <div className="flex items-center justify-between w-full">
                          <span>All Products</span>
                          <span className="text-xs text-gray-500 ml-2">Not supported during beta testing</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground mt-1">
                    Based on monthly sales volume
                  </p>
                </div>
              </div>
            </div>
            
            {/* Filter按钮 - 移动到Data Selection区域底部居中 */}
            <div className="flex justify-center gap-2 pt-0 mt-0">
              <Button
                variant="ghost"
                size="sm"
                onClick={resetFilters}
                className="h-8 text-xs text-gray-500 hover:text-gray-700"
              >
                Reset Filters
              </Button>
              <Button
                onClick={handleFilterData}
                disabled={filterLoading || !selectedCategoryId}
                className="h-8 text-xs bg-blue-600 hover:bg-blue-700"
              >
                {filterLoading ? (
                  <>
                    <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                    Filtering...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Apply Filters
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 横向数据统计区域 - Data Scope Overview - 总是显示 */}
        <Card ref={previewRef} className={filterLoading ? 'opacity-60' : ''}>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center justify-between">
              <div className="flex items-center gap-2">
                Preview of Project Data Scope
                {filterLoading && (
                  <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
                )}
              </div>
              
              {/* 移动到这里的创建项目按钮 */}
              <div className="flex flex-col items-end gap-2">
                {/* 创建项目按钮 */}
                <Button
                  onClick={handleConfirmSelection}
                  disabled={!hasEnoughData || isConfirmed || !permissions?.can_create_project}
                  title={!permissions?.can_create_project ? "Currently in internal testing" : !hasEnoughData ? "Please apply filters and ensure you have enough data" : ""}
                  className="bg-black hover:bg-gray-800 text-white"
                >
                  {isConfirmed ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Project Created
                    </>
                  ) : (
                    'Create  Project'
                  )}
                </Button>
                
                {hasEnoughData && (
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="w-4 h-4 text-blue-500" />
                    <span className="text-blue-600 font-medium">
                      Estimated processing time: {calculateEstimatedTime.text}
                    </span>
                  </div>
                )}
              </div>
            </CardTitle>
            <CardDescription className="text-sm">
              {isFilterApplied 
                ? (
                  <span>
                    Your project analysis will be based on these data.{" "}
                    <a 
                      href="/import-data" 
                      className="text-blue-600 hover:text-blue-800 underline font-medium cursor-pointer"
                      onClick={(e) => {
                        e.preventDefault();
                        window.location.href = '/import-data';
                      }}
                    >
                      Not enough data? Click to scrape more →
                    </a>
                  </span>
                )
                : "Apply filters above to see your data scope preview."
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            
            
            {isFilterApplied ? (
              <>
                {/* 主要统计数据 - 水平布局 */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <Card className="border-blue-200">
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2">
                        <Database className="w-4 h-4 text-blue-500" />
                        <div>
                          <p className="text-xl font-bold">{filteredStats?.totalProducts.toLocaleString()}</p>
                          <p className="text-xs text-muted-foreground">Products</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-green-200">
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-green-500" />
                        <div>
                          <p className="text-xl font-bold">{filteredStats?.totalBrands}</p>
                          <p className="text-xs text-muted-foreground">Brands</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-purple-200">
                    <CardContent className="p-3">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-purple-500" />
                        <div>
                          <p className="text-xl font-bold">{filteredStats?.totalReviews.toLocaleString()}</p>
                          <p className="text-xs text-muted-foreground">Reviews</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* 详细分布统计 - 水平布局 */}
                <div className="grid grid-cols-3 gap-4">
                  {/* 按来源分布 */}
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Data Sources</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-1">
                        {filteredStats?.sources.map(source => (
                          <div key={source.name} className="flex justify-between items-center">
                            <span className="text-xs capitalize">{source.name.replace('_', ' ')}</span>
                            <div className="flex items-center gap-1">
                              <Badge variant="secondary" className="text-xs">{source.count}</Badge>
                              <span className="text-xs text-muted-foreground">{source.percentage}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* 按类别分布 */}
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Categories</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-1">
                        {/* 确保按百分比排序 */}
                        {filteredStats?.categories
                          .sort((a, b) => b.percentage - a.percentage)
                          .slice(0, showAllCategories ? filteredStats.categories.length : 3)
                          .map(category => (
                          <div key={category.name} className="flex justify-between items-center">
                            <span className="text-xs">{category.name}</span>
                            <div className="flex items-center gap-1">
                              <Badge variant="secondary" className="text-xs">{category.count}</Badge>
                              <span className="text-xs text-muted-foreground">{category.percentage}%</span>
                            </div>
                          </div>
                        ))}
                        {filteredStats && filteredStats.categories.length > 3 && (
                          <button 
                            onClick={() => setShowAllCategories(!showAllCategories)}
                            className="text-xs text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                          >
                            {showAllCategories 
                              ? "Show Less" 
                              : `+${filteredStats.categories.length - 3} more categories`
                            }
                          </button>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Top品牌 */}
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Top Brands</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-1">
                        {/* 确保按百分比排序 */}
                        {filteredStats?.brands
                          .sort((a, b) => b.percentage - a.percentage)
                          .slice(0, showAllBrands ? filteredStats.brands.length : 3)
                          .map(brand => (
                          <div key={brand.name} className="flex justify-between items-center">
                            <span className="text-xs">{brand.name}</span>
                            <div className="flex items-center gap-1">
                              <Badge variant="secondary" className="text-xs">{brand.count}</Badge>
                              <span className="text-xs text-muted-foreground">{brand.percentage}%</span>
                            </div>
                          </div>
                        ))}
                        {filteredStats && filteredStats.brands.length > 3 && (
                          <button 
                            onClick={() => setShowAllBrands(!showAllBrands)}
                            className="text-xs text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                          >
                            {showAllBrands 
                              ? "Show Less" 
                              : `+${filteredStats.brands.length - 3} more brands`
                            }
                          </button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            ) : (
              /* 占位符内容 */
              <div className="grid grid-cols-3 gap-4">
                <Card className="border-gray-200 bg-gray-50">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2">
                      <Database className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-xl font-bold text-gray-400">---</p>
                        <p className="text-xs text-muted-foreground">Products</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-gray-200 bg-gray-50">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-xl font-bold text-gray-400">---</p>
                        <p className="text-xs text-muted-foreground">Brands</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-gray-200 bg-gray-50">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-xl font-bold text-gray-400">---</p>
                        <p className="text-xs text-muted-foreground">Reviews</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 样本产品预览 - 只有点击Apply后才显示 */}
        {isFilterApplied && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Eye className="w-4 h-4" />
              Sample Products Preview
              <Badge variant="outline" className="text-xs">{data.topProducts?.length || 0} items</Badge>
            </CardTitle>
            <CardDescription className="text-xs">
              Preview of the filtered dataset for analysis (Top {filters.topSalesCount || 'All'} by sales volume)
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {data.topProducts.slice(0, 8).map(product => (
                <div key={product.platform_id} className="flex justify-between items-center p-2 border rounded-md">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-xs truncate" title={product.title}>
                      {product.title.length > 45 ? `${product.title.substring(0, 45)}...` : product.title}
                    </p>
                    <div className="flex items-center gap-1 mt-1">
                      <Badge variant="outline" className="text-xs px-1 py-0">{product.brand}</Badge>
                      <Badge variant="outline" className="text-xs px-1 py-0">{product.category}</Badge>
                      <span className="text-xs text-muted-foreground">{(product as typeof product & {source: string}).source}</span>
                    </div>
                  </div>
                  <div className="text-right ml-2">
                    <p className="text-xs font-medium">${product.price_usd}</p>
                    <p className="text-xs text-muted-foreground">
                      {product.monthly_sales_volume?.toLocaleString() || 0}/mo
                    </p>
                  </div>
                </div>
              ))}
              {data.topProducts.length > 8 && (
                <p className="text-xs text-muted-foreground text-center py-1">
                  +{data.topProducts.length - 8} more products will be included in the analysis
                </p>
              )}
            </div>
          </CardContent>
        </Card>
        )}

       
      </div>
    </div>
  );
} 