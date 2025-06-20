'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { CheckCircle, Database, TrendingUp, Users, MessageSquare, Filter, Eye, ChevronDown, ChevronRight, Edit2, Check, X, RefreshCw } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { DatabaseService, type DataConfirmationData, type DataConfirmationFilters } from '@/components/analysis-db/data/database-service';

export function DataConfirmationTab({ onNavigateToAnalysis }: { onNavigateToAnalysis?: (projectName: string) => void }) {
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

  const dbService = useMemo(() => new DatabaseService(), []);

  // 生成智能project名字
  const generateSmartProjectName = () => {
    const categoriesPart = filters.categories.length > 0 
      ? filters.categories.join('_').replace(/\s+/g, '') 
      : 'AllCategories';
    
    const sourcesPart = filters.sources.length > 0 && data && filters.sources.length < data.availableSources.length
      ? `_${filters.sources.join('_').replace(/\s+/g, '')}`
      : '';
    
    const brandsPart = filters.brands.length > 0 && filters.brands.length <= 3
      ? `_${filters.brands.slice(0, 3).join('_').replace(/\s+/g, '')}`
      : filters.brands.length > 3
      ? `_${filters.brands.length}Brands`
      : '';
    
    const topCountPart = filters.topSalesCount ? `_Top${filters.topSalesCount}` : '';
    
    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    return `${categoriesPart}${sourcesPart}${brandsPart}${topCountPart}_${month}${day}_${hours}${minutes}`;
  };

  // 初始加载数据（只执行一次）
  useEffect(() => {
    loadInitialData();
  }, []);

  // 实时更新project名字
  useEffect(() => {
    if (data && !isEditingName) {
      setProjectName(generateSmartProjectName());
    }
  }, [filters, data, isEditingName]);

  // 初始加载数据 - 全量查询
  const loadInitialData = async () => {
    setPageLoading(true);
    try {
      // 获取全量数据（不传筛选条件）
      const result = await dbService.getDataConfirmationData();
      setData(result);
      
      // 设置默认全选状态 - 修复：统一所有筛选的逻辑
      setFilters({
        categories: result.availableCategories, // 明确选中所有类别
        sources: result.availableSources, // 明确选中所有来源
        brands: result.stats.brands.map(brand => brand.name), // 明确选中所有品牌
        topSalesCount: 100
      });
    } catch (error) {
      console.error('Failed to load initial data:', error);
    } finally {
      setPageLoading(false);
    }
  };

  // 手动筛选数据
  const handleFilterData = async () => {
    if (!data) return;
    
    setFilterLoading(true);
    try {
      // 使用当前筛选条件查询后端
      const result = await dbService.getDataConfirmationData(filters);
      setData(result);
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

  const handleCategoryChange = (category: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      categories: checked 
        ? [...prev.categories, category]
        : prev.categories.filter(c => c !== category)
    }));
  };

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

  const handleTopSalesCountChange = (value: string) => {
    setFilters(prev => ({
      ...prev,
      topSalesCount: value === 'all' ? undefined : parseInt(value)
    }));
  };

  const handleConfirmSelection = async () => {
    if (!filteredStats) return;
    
    setIsConfirmed(true);
    
    try {
      // 保存项目到数据库
      const projectData = {
        project_name: projectName,
        company_name: 'Leviton', // 可以从用户设置获取
        user_name: 'Current User', // 可以从用户认证获取
        description: `Analysis project for ${filters.categories.join(', ')} products from ${filters.sources.join(', ')}`,
        selected_categories: filters.categories,
        selected_sources: filters.sources,
        selected_brands: filters.brands,
        top_sales_count: filters.topSalesCount,
        total_products: filteredStats.totalProducts,
        total_brands: filteredStats.totalBrands,
        total_reviews: filteredStats.totalReviews,
        avg_monthly_sales: filteredStats.avgMonthlySales,
        status: 'active' as const
      };
      
      const savedProject = await dbService.saveProject(projectData);
      console.log('Project saved successfully:', savedProject);
      
      // 跳转到Analysis by DB tab，传递项目ID
      if (onNavigateToAnalysis) {
        onNavigateToAnalysis(savedProject.id);
      }
    } catch (error) {
      console.error('Failed to save project:', error);
      // 可以显示错误提示，但仍然允许继续
      if (onNavigateToAnalysis) {
        onNavigateToAnalysis(projectName);
      }
    }
  };

  const resetFilters = () => {
    if (!data) return;
    setFilters({
      categories: data.availableCategories,
      sources: data.availableSources,
      brands: data.stats.brands.map(brand => brand.name),
      topSalesCount: 100
    });
    setIsConfirmed(false);
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
                disabled={isConfirmed}
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
        </div>
      </div>

      {/* 可滚动内容区域 */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto space-y-4 p-4">
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
                {/* 产品类别筛选 - 修复逻辑 */}
                <div>
                  <Label className="text-sm font-medium">Product Categories</Label>
                  <div className="space-y-2 mt-2">
                    {data.availableCategories.map(category => (
                      <div key={category} className="flex items-center space-x-2">
                        <Checkbox
                          id={`category-${category}`}
                          checked={filters.categories.includes(category)}
                          onCheckedChange={(checked) => 
                            handleCategoryChange(category, checked as boolean)
                          }
                        />
                        <Label 
                          htmlFor={`category-${category}`}
                          className="text-xs cursor-pointer flex-1 select-none"
                        >
                          {category}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 数据来源筛选和销量排名筛选 - 合并在一列 */}
                <div className="space-y-4">
                  {/* 数据来源筛选 */}
                  <div>
                    <Label className="text-sm font-medium">Data Sources</Label>
                    <div className="space-y-2 mt-2">
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
                    <CollapsibleTrigger asChild>
                      <Button variant="ghost" className="w-full justify-between p-0 h-auto">
                        <Label className="text-sm font-medium">Top Brands Filter</Label>
                        {isBrandsExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </Button>
                    </CollapsibleTrigger>
                    <div className="mt-2">
                      {/* 默认显示前5个品牌 */}
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
              <div className="grid grid-cols-4 gap-4 mb-4">
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

                <Card className="border-orange-200">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-orange-500" />
                      <div>
                        <p className="text-xl font-bold">{Math.round(filteredStats?.avgMonthlySales || 0)}</p>
                        <p className="text-xs text-muted-foreground">Avg Sales/Month</p>
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