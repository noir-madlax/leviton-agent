'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { CheckCircle, Database, TrendingUp, Users, MessageSquare, Filter, Eye, ChevronDown, ChevronRight, Edit2, Check, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { DatabaseService, type DataConfirmationData, type DataConfirmationFilters } from '@/components/analysis-db/data/database-service';

// 扩展筛选接口
interface ExtendedDataConfirmationFilters extends DataConfirmationFilters {
  brands: string[]
}

export function DataConfirmationTab({ onNavigateToAnalysis }: { onNavigateToAnalysis?: (assignmentName: string) => void }) {
  const [data, setData] = useState<DataConfirmationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<ExtendedDataConfirmationFilters>({
    categories: [],
    sources: [],
    brands: [],
    topSalesCount: 100
  });
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [assignmentName, setAssignmentName] = useState('');
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempAssignmentName, setTempAssignmentName] = useState('');
  const [isInitialized, setIsInitialized] = useState(false);
  const [isBrandsExpanded, setIsBrandsExpanded] = useState(false);

  const dbService = useMemo(() => new DatabaseService(), []);

  // 生成智能assignment名字
  const generateSmartAssignmentName = () => {
    const categoriesPart = filters.categories.length > 0 
      ? filters.categories.join('_').replace(/\s+/g, '') 
      : 'AllCategories';
    
    const sourcesPart = filters.sources.length > 0 && data && filters.sources.length < data.availableSources.length
      ? filters.sources.join('_').replace(/\s+/g, '')
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
    loadData();
  }, []);

  // 实时更新assignment名字
  useEffect(() => {
    if (data && !isEditingName) {
      setAssignmentName(generateSmartAssignmentName());
    }
  }, [filters, data, isEditingName]);

  // 当筛选条件改变时重新加载数据
  useEffect(() => {
    if (isInitialized) {
      loadData();
    }
  }, [filters, isInitialized]);

  const loadData = async () => {
    setLoading(true);
    try {
      // 使用当前筛选条件查询后端
      const result = await dbService.getDataConfirmationData(filters);
      setData(result);
      
      // 首次加载时设置默认选中
      if (!isInitialized) {
        setFilters(prev => ({
          ...prev,
          sources: result.availableSources // 默认选中所有sources
        }));
        setIsInitialized(true);
      }
    } catch (error) {
      console.error('Failed to load data confirmation data:', error);
    } finally {
      setLoading(false);
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

  const handleConfirmSelection = () => {
    setIsConfirmed(true);
    // 保存筛选条件到全局状态或发送到后端
    console.log('Confirmed filters:', filters);
    console.log('Selected data stats:', filteredStats);
    console.log('Assignment name:', assignmentName);
    
    // 跳转到Analysis by DB tab
    if (onNavigateToAnalysis) {
      onNavigateToAnalysis(assignmentName);
    }
  };

  const resetFilters = () => {
    setFilters({
      categories: [],
      sources: data?.availableSources || [],
      brands: [],
      topSalesCount: 100
    });
    setIsConfirmed(false);
  };

  // 处理assignment名字编辑
  const handleEditName = () => {
    setTempAssignmentName(assignmentName);
    setIsEditingName(true);
  };

  const handleSaveName = () => {
    setAssignmentName(tempAssignmentName);
    setIsEditingName(false);
  };

  const handleCancelEdit = () => {
    setTempAssignmentName('');
    setIsEditingName(false);
  };

  if (loading) {
    return (
      <div className="h-full overflow-auto">
        <div className="max-w-7xl mx-auto space-y-6 p-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Step 2: Data Confirmation</h1>
            <p className="text-muted-foreground mt-2">
              Loading product data for confirmation...
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
            <h1 className="text-3xl font-bold tracking-tight">Step 2: Data Confirmation</h1>
            <p className="text-muted-foreground mt-2">
              Failed to load product data. Please try again.
            </p>
          </div>
          <Button onClick={loadData}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-7xl mx-auto space-y-4 p-4">
        {/* 页面标题和Actions按钮 */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Step 2: Data Confirmation</h1>
            <p className="text-muted-foreground text-sm">
              Review and confirm the scraped data before proceeding to analysis.
            </p>
          </div>
          
          {/* Actions按钮 - 移到右上角 */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={resetFilters}
              className="h-9"
            >
              Reset Filters
            </Button>
            <Button
              onClick={handleConfirmSelection}
              className="h-9"
              disabled={isConfirmed}
            >
              {isConfirmed ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Confirmed
                </>
              ) : (
                'Confirm Selection'
              )}
            </Button>
          </div>
        </div>

        {/* Assignment名字编辑区域 */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-blue-800">Assignment Name:</span>
            {isEditingName ? (
              <div className="flex items-center gap-2">
                <Input
                  value={tempAssignmentName}
                  onChange={(e) => setTempAssignmentName(e.target.value)}
                  className="h-6 text-sm bg-white border-blue-300"
                  autoFocus
                />
                <Button size="sm" variant="ghost" onClick={handleSaveName} className="h-6 w-6 p-0">
                  <Check className="h-3 w-3 text-green-600" />
                </Button>
                <Button size="sm" variant="ghost" onClick={handleCancelEdit} className="h-6 w-6 p-0">
                  <X className="h-3 w-3 text-red-600" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-blue-800">{assignmentName}</span>
                <Button size="sm" variant="ghost" onClick={handleEditName} className="h-6 w-6 p-0">
                  <Edit2 className="h-3 w-3 text-blue-600" />
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* 数据范围提示 */}
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-amber-600" />
            <span className="text-sm font-medium text-amber-800">
              Current Assignment Data Scope: 
            </span>
          </div>
          <p className="text-xs text-amber-700 mt-1">
            The data displayed below represents the filtered dataset for this assignment. 
            Analysis and chat functions will operate on this selected data scope only.
          </p>
        </div>

        {/* 横向筛选区域 - Data Filters */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Filter className="w-5 h-5" />
              Data Filters
            </CardTitle>
            <CardDescription className="text-sm">
              Select the data scope for your research assignment
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-6">
              {/* 产品类别筛选 */}
              <div>
                <Label className="text-sm font-medium">Product Categories</Label>
                <div className="space-y-2 mt-2">
                  {data.availableCategories.map(category => (
                    <div key={category} className="flex items-center space-x-2">
                      <Checkbox
                        id={`category-${category}`}
                        checked={filters.categories.length === 0 || filters.categories.includes(category)}
                        onCheckedChange={(checked) => 
                          handleCategoryChange(category, checked as boolean)
                        }
                      />
                      <Label 
                        htmlFor={`category-${category}`}
                        className="text-xs cursor-pointer"
                      >
                        {category}
                      </Label>
                    </div>
                  ))}
                  {filters.categories.length === 0 && (
                    <p className="text-xs text-muted-foreground">
                      All categories selected by default
                    </p>
                  )}
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
                          className="text-xs cursor-pointer capitalize"
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
              </div>

              {/* 品牌筛选 */}
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
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              id={`brand-${brand.name}`}
                              checked={filters.brands.length === 0 || filters.brands.includes(brand.name)}
                              onCheckedChange={(checked) => 
                                handleBrandChange(brand.name, checked as boolean)
                              }
                            />
                            <Label 
                              htmlFor={`brand-${brand.name}`}
                              className="text-xs cursor-pointer"
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
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                id={`brand-${brand.name}`}
                                checked={filters.brands.length === 0 || filters.brands.includes(brand.name)}
                                onCheckedChange={(checked) => 
                                  handleBrandChange(brand.name, checked as boolean)
                                }
                              />
                              <Label 
                                htmlFor={`brand-${brand.name}`}
                                className="text-xs cursor-pointer"
                              >
                                {brand.name}
                              </Label>
                            </div>
                            <span className="text-xs text-muted-foreground">{brand.percentage}%</span>
                          </div>
                        ))}
                      </div>
                    </CollapsibleContent>
                    {filters.brands.length === 0 && (
                      <p className="text-xs text-muted-foreground mt-2">
                        All brands selected by default
                      </p>
                    )}
                  </div>
                </Collapsible>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 横向数据统计区域 - Data Scope */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Data Scope Overview</CardTitle>
            <CardDescription className="text-sm">
              Real-time statistics based on your current filter selection
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
                  <p className="font-medium">Data Selection Confirmed - {assignmentName}</p>
                  <p className="text-sm">
                    Ready to proceed with {filteredStats?.totalProducts} products from{' '}
                    {filters.categories.length === 0 ? 'all categories' : filters.categories.join(', ')}{' '}
                    and {filters.sources.length === 0 ? 'all sources' : filters.sources.join(', ')}.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
} 