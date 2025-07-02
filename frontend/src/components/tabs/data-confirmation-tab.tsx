'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { CheckCircle, Database, Users, MessageSquare, Filter, Eye, ChevronDown, ChevronRight, Edit2, Check, X, RefreshCw, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { type DataConfirmationData, type DataConfirmationFilters } from '@/components/analysis-db/data/database-service';
import { CategorySelector } from '@/components/category-selector';

// 进度显示接口
interface ProjectProgress {
  project_id: string;
  project_name: string;
  status: string;
  segmentation_status: string;
  total_products: number;
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
    }[];
    current_stage?: string;
  }[];
}

// 项目进度显示组件
function ProjectProgressDisplay({ projectId, isCreating, onAnalysisReady, totalProducts }: { 
  projectId: string | null; 
  isCreating: boolean;
  onAnalysisReady?: (projectId: string) => void;
  totalProducts?: number;
}) {
  const [progress, setProgress] = useState<ProjectProgress | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isCreating && !projectId) {
      setProgress(null);
      return;
    }

    const fetchProgress = async () => {
      // 如果正在创建但还没有projectId，显示创建中状态
      if (isCreating && !projectId) {
        setProgress({
          project_id: 'creating',
          project_name: 'Creating Project...',
          status: 'creating',
          segmentation_status: 'pending',
          total_products: 0,
          steps: [
            {
              step: 'project_creation',
              name: 'Project Creation',
              status: 'in_progress',
              description: 'Creating project and extracting ASINs...'
            },
            {
              step: 'product_selection',
              name: 'Product Selection',
              status: 'pending',
              description: 'Waiting for project creation...'
            },
            {
              step: 'product_segmentation',
              name: 'Product Segmentation',
              status: 'pending',
              description: 'Waiting for product selection...'
            },
            {
              step: 'data_preparation',
              name: 'Data Preparation',
              status: 'pending',
              description: 'Waiting for segmentation...'
            }
          ]
        });
        return;
      }

      if (!projectId) return;

      setLoading(true);
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/v1/projects/progress/${projectId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setProgress(data);
        
        // 如果完成，通知父组件
        if (data.segmentation_status === 'completed' && onAnalysisReady && projectId) {
          onAnalysisReady(projectId);
        }
      } catch (error) {
        console.error('Failed to fetch project progress:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
    
    // 如果处理中或正在创建，定期轮询更新
    const interval = setInterval(() => {
      if (isCreating || progress?.segmentation_status === 'processing') {
        fetchProgress();
      }
    }, 9000); // 每9秒检查一次

    return () => clearInterval(interval);
  }, [projectId, isCreating, progress?.segmentation_status]);

  if (!isCreating && !progress) {
    return null;
  }

  // 如果没有progress但正在创建，不显示任何内容（等待fetchProgress设置状态）
  if (!progress) {
    return null;
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

  return (
    <Card className="mb-6 border-l-4 border-l-blue-500">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Database className="w-5 h-5 text-blue-500" />
          Project Progress: {progress.project_name}
          {loading && <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />}
        </CardTitle>
        <CardDescription>
          Processing status for {progress.total_products || totalProducts || 0} products
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {progress.steps.map((step) => (
            <div key={step.step} className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(step.status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-sm">{step.name}</h4>
                  <Badge variant="outline" className={`text-xs ${getStatusColor(step.status)}`}>
                    {step.status.replace('_', ' ')}
                  </Badge>
                </div>
                <p className="text-xs text-gray-600 mt-1">{step.description}</p>
                
                {/* 子步骤显示 */}
                {step.sub_steps && step.sub_steps.length > 0 && (
                  <div className="mt-2 ml-4 space-y-1">
                    {step.sub_steps.map((subStep, subIndex) => (
                      <div key={subIndex} className="flex items-center gap-2 text-xs">
                        {getStatusIcon(subStep.status)}
                        <span className={subStep.status === 'completed' ? 'text-green-700' : subStep.status === 'in_progress' ? 'text-blue-700' : 'text-gray-500'}>
                          {subStep.name}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function DataConfirmationTab({ onNavigateToAnalysis }: { onNavigateToAnalysis?: (projectId: string) => void }) {
  // 暂时不使用onNavigateToAnalysis，让用户看到进度后手动跳转
  console.log('Navigation callback available:', !!onNavigateToAnalysis);
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
  const [projectName, setProjectName] = useState('');
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempProjectName, setTempProjectName] = useState('');
  const [isBrandsExpanded, setIsBrandsExpanded] = useState(false);
  const [createdProjectId, setCreatedProjectId] = useState<string | null>(null);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('');
  const [selectedCategoryName, setSelectedCategoryName] = useState<string>('');
  const [selectedCategoryPath, setSelectedCategoryPath] = useState<string>('');
  const [isFilterApplied, setIsFilterApplied] = useState(false); // Track if filter has been applied

  // 生成智能project名字
  const generateSmartProjectName = () => {
    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const year = now.getFullYear().toString().slice(-4);
    
    // Use the last part of the category path or fallback to category name
    let categoryForName = selectedCategoryName;
    if (selectedCategoryPath) {
      const pathParts = selectedCategoryPath.split(' > ');
      categoryForName = pathParts[pathParts.length - 1]; // Use the most specific category
    }
    
    // Clean category name for use in project name
    const cleanCategory = categoryForName.replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '_');
    
    return `${cleanCategory}_Top${filters.topSalesCount || 100}_${month}${day}_${year.slice(-4)}`;
  };

  // 初始加载数据（只执行一次）
  useEffect(() => {
    loadInitialData();
  }, []);

  // 实时更新project名字
  useEffect(() => {
    if (!isEditingName) {
      setProjectName(generateSmartProjectName());
    }
  }, [selectedCategoryName, filters.sources, filters.brands, filters.topSalesCount, data, isEditingName]);

  // 初始加载数据 - 全量查询
  const loadInitialData = async () => {
    setPageLoading(true);
    try {
      // 使用后端API获取全量数据
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/data-confirmation`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setData(result);
      
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
    
    // 🔥 关键修复：将选中的类别同步到filters.categories
    setFilters(prev => ({
      ...prev,
      categories: categoryName ? [categoryName] : [] // 将类别名称添加到filters中
    }));
  };

  // 手动筛选数据
  const handleFilterData = async () => {
    if (!selectedCategoryId) {
      alert('Please select a category first');
      return;
    }
    
    // 🔥 修复：立即显示loading状态
    setFilterLoading(true);
    
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

  const handleSourceChange = (source: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      sources: checked 
        ? [...prev.sources, source]
        : prev.sources.filter(s => s !== source)
    }));
  };

  const handleBrandChange = (brand: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      brands: checked 
        ? [...prev.brands, brand]
        : prev.brands.filter(b => b !== brand)
    }));
  };

  const handleSelectAllSources = () => {
    if (!data) return;
    setFilters(prev => ({
      ...prev,
      sources: [...data.availableSources]
    }));
  };

  const handleClearAllSources = () => {
    setFilters(prev => ({
      ...prev,
      sources: []
    }));
  };

  const handleSelectAllBrands = () => {
    if (!data) return;
    setFilters(prev => ({
      ...prev,
      brands: data.stats.brands.map((brand: { name: string }) => brand.name)
    }));
  };

  const handleClearAllBrands = () => {
    setFilters(prev => ({
      ...prev,
      brands: []
    }));
  };

  const handleTopSalesCountChange = (value: string) => {
    setFilters(prev => ({
      ...prev,
      topSalesCount: value === 'all' ? undefined : parseInt(value)
    }));
  };

  const handleConfirmSelection = async () => {
    if (!filteredStats) return;
    
    setIsConfirmed(true);
    setIsCreatingProject(true); // 立即显示进度区域
    
    try {
      // 调用后端API创建项目
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_name: projectName,
          company_name: 'Leviton',
          user_name: 'Current User',
          description: `Analysis project for ${filters.categories.join(', ')} products from ${filters.sources.join(', ')}`,
          filters: {
            categories: filters.categories,
            sources: filters.sources,
            brands: filters.brands,
            top_sales_count: filters.topSalesCount
          }
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const savedProject = await response.json();
      console.log('Project saved successfully:', savedProject);
      
      // 设置项目ID，更新进度显示状态
      setCreatedProjectId(savedProject.id);
      
      // 不自动跳转，让用户看到进度
      // 可以在进度完成后再跳转
      // if (onNavigateToAnalysis) {
      //   onNavigateToAnalysis(savedProject.id);
      // }
    } catch (error) {
      console.error('Failed to save project:', error);
      setIsConfirmed(false); // 重置确认状态
      setIsCreatingProject(false); // 重置创建状态
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
    setIsConfirmed(false);
    setIsFilterApplied(false); // Reset filter applied state
    
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

  // 处理project名字编辑
  const handleEditName = () => {
    setTempProjectName(projectName);
    setIsEditingName(true);
  };

  const handleSaveName = () => {
    setProjectName(tempProjectName);
    setIsEditingName(false);
  };

  const handleCancelEdit = () => {
    setTempProjectName('');
    setIsEditingName(false);
  };

  if (pageLoading) {
    return (
      <div className="h-full overflow-auto">
        <div className="max-w-7xl mx-auto space-y-6 p-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Step 2: Data Scope Selection</h1>
            <p className="text-muted-foreground mt-2">
              Loading product data for scope selection...
            </p>
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
            <h1 className="text-3xl font-bold tracking-tight">Step 2: Data Scope Selection</h1>
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
    <div className="h-full flex flex-col overflow-hidden">
      {/* 固定顶部区域 - 类似导航栏 */}
      <div className="flex-shrink-0 bg-background border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 space-y-4">
          {/* 页面标题和Confirm按钮 */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Step 2: Data Scope Selection</h1>
              <p className="text-muted-foreground text-sm">
                Define your research scope by selecting data filters to create a focused analysis project.
              </p>
            </div>
            
            {/* Create Project按钮 */}
            <div className="flex gap-2">
              <Button
                onClick={handleConfirmSelection}
                className="h-9"
                disabled={isConfirmed || !isFilterApplied}
                title={!isFilterApplied ? "Please apply filters first" : ""}
              >
                {isConfirmed ? (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Project Created
                  </>
                ) : (
                  'Create Research Project'
                )}
              </Button>
            </div>
          </div>

          {/* Project名字编辑区域 - 优化体验 */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-blue-800 whitespace-nowrap">Project Name:</span>
              {isEditingName ? (
                <div className="flex items-center gap-2 flex-1">
                  <Input
                    value={tempProjectName}
                    onChange={(e) => setTempProjectName(e.target.value)}
                    className="flex-1 h-8 text-sm bg-white border-blue-300 shadow-none focus:ring-1 focus:ring-blue-500"
                    autoFocus
                  />
                  <Button size="sm" variant="ghost" onClick={handleSaveName} className="h-8 w-8 p-0 hover:bg-green-100">
                    <Check className="h-4 w-4 text-green-600" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={handleCancelEdit} className="h-8 w-8 p-0 hover:bg-red-100">
                    <X className="h-4 w-4 text-red-600" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-sm font-medium text-blue-800 truncate flex-1" title={projectName}>
                    {projectName}
                  </span>
                  <Button size="sm" variant="ghost" onClick={handleEditName} className="h-8 w-8 p-0 hover:bg-blue-100 flex-shrink-0">
                    <Edit2 className="h-4 w-4 text-blue-600" />
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* 选中类别显示区域 */}
          {selectedCategoryPath && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-800">Selected Category:</span>
                <span className="text-sm text-green-700 font-medium">{selectedCategoryPath}</span>
                <Badge variant="outline" className="text-xs text-green-600 border-green-300">
                  Level {selectedCategoryName ? '5' : '0'}
                </Badge>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 可滚动内容区域 */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto space-y-4 p-4">
          
                     {/* 项目进度显示 */}
           <ProjectProgressDisplay 
             projectId={createdProjectId} 
             isCreating={isCreatingProject}
             totalProducts={filteredStats?.totalProducts}
             onAnalysisReady={(projectId) => {
               if (onNavigateToAnalysis) {
                 onNavigateToAnalysis(projectId);
               }
             }}
           />
          {/* 横向筛选区域 - Data Filters */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Filter className="w-5 h-5" />
                Data Filters
              </CardTitle>
              <CardDescription className="text-sm">
                Choose which products, brands, and data sources to include in your analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-6">
                {/* Amazon Category Selector */}
                <div>
                  <CategorySelector
                    onCategorySelect={handleCategorySelect}
                    selectedCategoryId={selectedCategoryId}
                    selectedCategoryName={selectedCategoryName}
                    selectedCategoryPath={selectedCategoryPath}
                  />
                </div>

                {/* 数据来源筛选和销量排名筛选 - 合并在一列 */}
                <div className="space-y-4">
                  {/* 数据来源筛选 */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <Label className="text-sm font-medium">Data Sources</Label>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleSelectAllSources}
                          className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                        >
                          Select All
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleClearAllSources}
                          className="h-6 px-2 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                        >
                          Clear All
                        </Button>
                      </div>
                    </div>
                    <div className="space-y-2">
                      {data.availableSources.map(source => (
                        <div key={source} className="flex items-center space-x-2">
                          <Checkbox
                            id={`source-${source}`}
                            checked={filters.sources.includes(source)}
                            onCheckedChange={(checked) => 
                              handleSourceChange(source, checked as boolean)
                            }
                          />
                          <Label 
                            htmlFor={`source-${source}`}
                            className="text-xs cursor-pointer capitalize flex-1 select-none"
                          >
                            {source.replace('_', ' ')}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 销量排名筛选 */}
                  <div>
                    <Label className="text-sm font-medium">Sales Ranking Filter</Label>
                    <Select
                      value={filters.topSalesCount?.toString() || 'all'}
                      onValueChange={handleTopSalesCountChange}
                    >
                      <SelectTrigger className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="50">Top 50 Products</SelectItem>
                        <SelectItem value="100">Top 100 Products</SelectItem>
                        <SelectItem value="200">Top 200 Products</SelectItem>
                        <SelectItem value="500">Top 500 Products</SelectItem>
                        <SelectItem value="all">All Products</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground mt-1">
                      Based on monthly sales volume
                    </p>
                  </div>

                  {/* Filter按钮 - 调整视觉层次 */}
                  <div className="flex gap-2 pt-2">
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
                      disabled={filterLoading}
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
                </div>

                {/* 品牌筛选 - 修复逻辑 */}
                <div>
                  <Collapsible open={isBrandsExpanded} onOpenChange={setIsBrandsExpanded}>
                    <div className="flex items-center justify-between mb-2">
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" className="p-0 h-auto flex items-center gap-2 hover:bg-transparent">
                          <Label className="text-sm font-medium">Top Brands Filter</Label>
                          {isBrandsExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </Button>
                      </CollapsibleTrigger>
                      {data.stats.brands.length > 0 && (
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleSelectAllBrands}
                            className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                          >
                            Select All
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleClearAllBrands}
                            className="h-6 px-2 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                          >
                            Clear All
                          </Button>
                        </div>
                      )}
                    </div>
                    
                    <div>
                      {/* 根据状态显示不同内容 */}
                      {!selectedCategoryId ? (
                        <div className="p-4 border-2 border-dashed border-gray-200 rounded-lg text-center">
                          <p className="text-sm text-gray-500">
                            Please select a category first to view corresponding brands
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            Use the category selector above
                          </p>
                        </div>
                      ) : data.stats.brands.length === 0 ? (
                        <div className="p-4 border-2 border-dashed border-yellow-200 rounded-lg text-center">
                          <p className="text-sm text-yellow-700">
                            No brand data available for selected category
                          </p>
                          <p className="text-xs text-yellow-600 mt-1">
                            Selected: {selectedCategoryName}
                          </p>
                        </div>
                      ) : (
                        <>
                          {/* 显示前5个品牌 */}
                          <div className="space-y-2">
                            {data.stats.brands.slice(0, 5).map(brand => (
                              <div key={brand.name} className="flex items-center justify-between">
                                <div className="flex items-center space-x-2 flex-1">
                                  <Checkbox
                                    id={`brand-${brand.name}`}
                                    checked={filters.brands.includes(brand.name)}
                                    onCheckedChange={(checked) => 
                                      handleBrandChange(brand.name, checked as boolean)
                                    }
                                  />
                                  <Label 
                                    htmlFor={`brand-${brand.name}`}
                                    className="text-xs cursor-pointer flex-1 select-none"
                                  >
                                    {brand.name}
                                  </Label>
                                </div>
                                <span className="text-xs text-muted-foreground">{brand.percentage}%</span>
                              </div>
                            ))}
                          </div>
                          
                          {/* 折叠显示更多品牌 */}
                          {data.stats.brands.length > 5 && (
                            <CollapsibleContent>
                              <div className="space-y-2 mt-2 pt-2 border-t">
                                {data.stats.brands.slice(5).map(brand => (
                                  <div key={brand.name} className="flex items-center justify-between">
                                    <div className="flex items-center space-x-2 flex-1">
                                      <Checkbox
                                        id={`brand-${brand.name}`}
                                        checked={filters.brands.includes(brand.name)}
                                        onCheckedChange={(checked) => 
                                          handleBrandChange(brand.name, checked as boolean)
                                        }
                                      />
                                      <Label 
                                        htmlFor={`brand-${brand.name}`}
                                        className="text-xs cursor-pointer flex-1 select-none"
                                      >
                                        {brand.name}
                                      </Label>
                                    </div>
                                    <span className="text-xs text-muted-foreground">{brand.percentage}%</span>
                                  </div>
                                ))}
                              </div>
                            </CollapsibleContent>
                          )}
                          
                          {/* 显示品牌统计信息 */}
                          <div className="mt-2 pt-2 border-t">
                            <p className="text-xs text-gray-500">
                              基于所选类别：{filters.categories.join(', ')} 
                              {data.stats.brands.length > 10 && ` (显示前10个品牌)`}
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  </Collapsible>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 横向数据统计区域 - Data Scope Overview */}
          <Card className={filterLoading ? 'opacity-60' : ''}>
            <CardHeader className="pb-3">
                          <CardTitle className="text-lg flex items-center gap-2">
              Selected Data Scope
              {filterLoading && (
                <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
              )}
            </CardTitle>
            <CardDescription className="text-sm">
              Preview of your research dataset. Your analysis project will be based on this filtered selection.
            </CardDescription>
            </CardHeader>
            <CardContent>
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
                      {filteredStats?.categories.map(category => (
                        <div key={category.name} className="flex justify-between items-center">
                          <span className="text-xs">{category.name}</span>
                          <div className="flex items-center gap-1">
                            <Badge variant="secondary" className="text-xs">{category.count}</Badge>
                            <span className="text-xs text-muted-foreground">{category.percentage}%</span>
                          </div>
                        </div>
                      ))}
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
                      {filteredStats?.brands.slice(0, 4).map(brand => (
                        <div key={brand.name} className="flex justify-between items-center">
                          <span className="text-xs">{brand.name}</span>
                          <div className="flex items-center gap-1">
                            <Badge variant="secondary" className="text-xs">{brand.count}</Badge>
                            <span className="text-xs text-muted-foreground">{brand.percentage}%</span>
                          </div>
                        </div>
                      ))}
                      {filteredStats && filteredStats.brands.length > 4 && (
                        <p className="text-xs text-muted-foreground">
                          +{filteredStats.brands.length - 4} more
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>

          {/* 样本产品预览 */}
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

          {/* 确认状态 */}
          {isConfirmed && (
            <Card className="border-green-200 bg-green-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-green-700">
                  <CheckCircle className="w-5 h-5" />
                  <div>
                    <p className="font-medium">Research Project Created - {projectName}</p>
                    <p className="text-sm">
                      Project includes {filteredStats?.totalProducts} products from{' '}
                      {filters.categories.length === 0 ? 'all categories' : filters.categories.join(', ')}{' '}
                      and {filters.sources.length === 0 ? 'all sources' : filters.sources.join(', ')}. Ready for analysis!
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
} 