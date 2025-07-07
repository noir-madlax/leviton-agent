'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { config } from '@/lib/config';

interface ScrapingResult {
  task_id?: string;
  status?: 'completed' | 'failed' | 'running';
  message?: string;
  results?: {
    products_scraped: number;
    reviews_scraped: number;
    data_saved_to: string;
  };
  error?: string;
  url?: string;
  batch_id?: number;
  overall_status?: string;
  products_phase?: {
    scraping?: any;
    importing?: any;
  };
  transformation_phase?: {
    success?: boolean;
    processed_count?: number;
    error_count?: number;
    duration_seconds?: number;
    summary?: any;
    errors?: string[];
  };
  reviews_phase?: {
    scraping?: any;
    importing?: any;
    transformation?: any;
  };
  execution_stats?: {
    start_time?: string;
    end_time?: string;
    total_duration?: number;
    phase_durations?: {
      product_scraping?: number;
      product_importing?: number;
      data_transformation?: number;
      review_scraping?: number;
      review_importing?: number;
      review_transformation?: number;
    };
    api_calls?: {
      category_api?: number;
      product_details_api?: number;
      reviews_api?: number;
      total?: number;
    };
  };
  data_quality?: {
    total_products?: number;
    overall_quality_score?: number;
    field_coverage?: Record<string, {
      total: number;
      with_value: number;
      coverage_percent: number;
    }>;
    quality_summary?: {
      best_field?: { name: string; coverage: number };
      worst_field?: { name: string; coverage: number };
      key_fields_avg_coverage?: number;
      recommendations?: string[];
    };
  };
}

export function DataImportTab() {
  const [url, setUrl] = useState('');
  const [maxProducts, setMaxProducts] = useState<number | string>(5);
  const [maxReviews, setMaxReviews] = useState<number | string>(15);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ScrapingResult | null>(null);
  
  // 🔥 新增：实时进度状态管理
  const [isScrapingStarted, setIsScrapingStarted] = useState(false);
  const [currentBatchId, setCurrentBatchId] = useState<number | null>(null);
  const [currentRequestId, setCurrentRequestId] = useState<number | null>(null);
  
  // 使用统一配置
  const backendUrl = config.backendUrl;

  // 🔥 新增：轮询实时状态
  const pollScrapingStatus = async (batchId: number) => {
    try {
      const response = await fetch(`${backendUrl}/api/scraping/status/${batchId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const statusData = await response.json();
      
      // 更新结果状态
      if (statusData) {
        setResult(prev => ({
          ...prev,
          ...statusData,
          batch_id: batchId
        }));
      }
      
      return statusData;
    } catch (error) {
      console.error('Failed to poll scraping status:', error);
      return null;
    }
  };

  // 🔥 修改：支持实时进度的启动逻辑
  const handleStartScraping = async () => {
    if (!url.trim()) {
      alert('Please enter a URL first');
      return;
    }

    setIsLoading(true);
    setResult(null);
    setIsScrapingStarted(true); // 🔥 立即显示进度界面
    setCurrentBatchId(null);
    setCurrentRequestId(null);

    try {
      // 🔥 修改：使用异步启动方式
      const response = await fetch(`${backendUrl}/api/scraping/process-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.trim(),
          max_products: maxProducts === '' ? 5 : maxProducts,
          max_reviews: maxReviews === '' ? 15 : maxReviews,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      
      // 🔥 新增：如果获得了batch_id，开始轮询状态
      if (data.batch_id) {
        setCurrentBatchId(data.batch_id);
        
        // 开始轮询（但现在API是同步的，所以这里主要是为了兼容未来的异步API）
        // 暂时显示完整结果
      }
      
    } catch (error) {
      console.error('Scraping failed:', error);
      setResult({
        task_id: 'error',
        status: 'failed',
        error: error instanceof Error ? error.message : 'Failed to start scraping task',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Completed</Badge>;
      case 'failed':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />Failed</Badge>;
      case 'running':
        return <Badge variant="secondary"><Loader2 className="w-3 h-3 mr-1 animate-spin" />Running</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getStepStatus = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Success</Badge>;
      case 'failed':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />Failed</Badge>;
      case 'running':
        return <Badge variant="secondary"><Loader2 className="w-3 h-3 mr-1 animate-spin" />Running</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getTransformationStatus = (phase: any) => {
    if (phase.success) {
      return (
        <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Success</Badge>
      );
    } else {
      return (
        <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />Failed</Badge>
      );
    }
  };

  const getOverallStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Completed</Badge>;
      case 'products_only_completed':
        return <Badge variant="default" className="bg-blue-500"><CheckCircle className="w-3 h-3 mr-1" />Products Only</Badge>;
      case 'failed':
      case 'product_scraping_failed':
      case 'product_importing_failed':
      case 'transformation_failed':
      case 'review_scraping_failed':
      case 'review_importing_failed':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />Failed</Badge>;
      case 'running':
        return <Badge variant="secondary"><Loader2 className="w-3 h-3 mr-1 animate-spin" />Running</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 页面标题 */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Import Data</h1>
          <p className="text-muted-foreground mt-2">
            Import product and review data from Amazon URLs. Supports product pages, search results, and category pages.
          </p>
        </div>

        {/* URL输入区域 */}
        <Card>
          <CardHeader>
            <CardTitle>Amazon URL Input</CardTitle>
            <CardDescription>
              Enter an Amazon URL to scrape product and review data. Supported URL types include product pages, search results, and category pages.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="url">Amazon URL</Label>
              <div className="flex gap-2">
                <Input
                  id="url"
                  placeholder="https://www.amazon.com/dp/B08N5WRWNW or https://www.amazon.com/s?k=light+switches"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1"
                />
                <Button 
                  onClick={handleStartScraping} 
                  disabled={isLoading || !url.trim()}
                  className="min-w-[120px]"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Scraping...
                    </>
                  ) : (
                    'Start Scraping'
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 参数设置 */}
        <Card>
          <CardHeader>
            <CardTitle>Scraping Parameters</CardTitle>
            <CardDescription>
              Configure the maximum number of products and reviews to scrape.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="maxProducts">Max Products</Label>
                <Input
                  id="maxProducts"
                  type="text"
                  placeholder="5"
                  value={maxProducts}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d+$/.test(val)) {
                      setMaxProducts(val === '' ? '' : parseInt(val));
                    }
                  }}
                />
                <p className="text-sm text-muted-foreground">
                  Maximum number of products to scrape (1-500)
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxReviews">Max Reviews</Label>
                <Input
                  id="maxReviews"
                  type="text"
                  placeholder="15"
                  value={maxReviews}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === '' || /^\d+$/.test(val)) {
                      setMaxReviews(val === '' ? '' : parseInt(val));
                    }
                  }}
                />
                <p className="text-sm text-muted-foreground">
                  Maximum number of reviews to scrape <strong>per product</strong> (0-200)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 结果显示 - 🔥 修改：支持立即显示进度 */}
        {(result || isScrapingStarted) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Scraping Results
                {result?.overall_status && getStatusBadge(result.overall_status)}
                {isScrapingStarted && !result && (
                  <Badge variant="secondary">
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    Starting...
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label>URL</Label>
                  <div className="font-mono text-xs bg-muted p-2 rounded break-all">
                    {result?.url || url || 'N/A'}
                  </div>
                </div>
                <div>
                  <Label>Batch ID</Label>
                  <div className="font-mono text-xs bg-muted p-2 rounded">
                    {result?.batch_id || currentBatchId || 'Pending...'}
                  </div>
                </div>
              </div>

              {/* 🔥 修改：立即显示步骤进度 */}
              <div className="space-y-4">
                <Label className="text-base font-medium">Processing Steps</Label>
                
                {/* Step 1: 产品爬取 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-sm font-bold text-blue-600">1</div>
                    <span className="font-medium">Product Scraping (API → JSON)</span>
                    {result?.products_phase?.scraping ? (
                      getStepStatus(result.products_phase.scraping.status)
                    ) : isScrapingStarted ? (
                      <Badge variant="secondary">
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                        In Progress
                      </Badge>
                    ) : (
                      <Badge variant="outline">Pending</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.products_phase?.scraping ? (
                      result.products_phase.scraping.status === 'success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {result.products_phase.scraping.products_scraped || 0} products scraped</span>
                          {result.products_phase.scraping.file_path && (
                            <span className="text-xs font-mono bg-green-50 px-2 py-1 rounded">
                              Data saved
                            </span>
                          )}
                        </div>
                      ) : result.products_phase.scraping.status === 'failed' ? (
                        <span className="text-red-600">❌ Failed: {result.products_phase.scraping.error || 'Unknown error'}</span>
                      ) : (
                        <span>🔄 In progress...</span>
                      )
                    ) : isScrapingStarted ? (
                      <span>🔄 Starting product scraping...</span>
                    ) : (
                      <span>⏳ Waiting to start...</span>
                    )}
                  </div>
                </div>

                {/* Step 2: 产品导入 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-sm font-bold text-blue-600">2</div>
                    <span className="font-medium">Product Import (JSON → amazon_products)</span>
                    {result?.products_phase?.importing ? (
                      getStepStatus(result.products_phase.importing.status)
                    ) : (
                      <Badge variant="outline">Pending</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.products_phase?.importing ? (
                      result.products_phase.importing.status === 'success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {result.products_phase.importing.products_imported || 0} products imported</span>
                          <span className="text-xs font-mono bg-green-50 px-2 py-1 rounded">
                            Batch ID: {result.batch_id}
                          </span>
                        </div>
                      ) : result.products_phase.importing.status === 'failed' ? (
                        <span className="text-red-600">❌ Failed: {result.products_phase.importing.error || 'Import failed'}</span>
                      ) : (
                        <span>🔄 In progress...</span>
                      )
                    ) : (
                      <span>⏳ Waiting for product scraping to complete...</span>
                    )}
                  </div>
                </div>

                {/* Step 3: 数据转换 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center text-sm font-bold text-purple-600">3</div>
                    <span className="font-medium">Product Transformation (amazon_products → product_wide_table)</span>
                    {result?.transformation_phase ? (
                      getTransformationStatus(result.transformation_phase)
                    ) : (
                      <Badge variant="outline">Pending</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.transformation_phase ? (
                      result.transformation_phase.success ? (
                        <div className="space-y-1">
                          <div className="flex items-center gap-4">
                            <span>✅ {result.transformation_phase.processed_count || 0} products transformed</span>
                            <span className="text-xs font-mono bg-purple-50 px-2 py-1 rounded">
                              {result.transformation_phase.duration_seconds ? `${result.transformation_phase.duration_seconds.toFixed(1)}s` : 'N/A'}
                            </span>
                          </div>
                          {(result.transformation_phase.error_count || 0) > 0 && (
                            <div className="text-amber-600">
                              ⚠️ {result.transformation_phase.error_count || 0} errors occurred
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <span className="text-red-600">❌ Transformation failed</span>
                          {result.transformation_phase.errors && result.transformation_phase.errors.length > 0 && (
                            <div className="text-xs bg-red-50 p-2 rounded mt-1">
                              {result.transformation_phase.errors[0]}
                            </div>
                          )}
                        </div>
                      )
                    ) : (
                      <span>⏳ Waiting for product import to complete...</span>
                    )}
                  </div>
                </div>

                {/* Step 4: 评论爬取 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center text-sm font-bold text-green-600">4</div>
                    <span className="font-medium">Review Scraping (API → JSON)</span>
                    {result?.reviews_phase?.scraping ? (
                      getStepStatus(result.reviews_phase.scraping.status)
                    ) : (
                      <Badge variant="outline">Pending</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.reviews_phase?.scraping ? (
                      result.reviews_phase.scraping.status === 'success' || result.reviews_phase.scraping.status === 'partial_success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ Reviews scraped for {result.reviews_phase.scraping.products_processed || 0} products</span>
                          <span className="text-xs font-mono bg-green-50 px-2 py-1 rounded">
                            {result.reviews_phase.scraping.total_reviews_scraped || 0} reviews
                          </span>
                        </div>
                      ) : result.reviews_phase.scraping.status === 'failed' ? (
                        <span className="text-red-600">❌ Failed: {result.reviews_phase.scraping.error || 'Review scraping failed'}</span>
                      ) : (
                        <span>🔄 In progress...</span>
                      )
                    ) : (
                      <span>⏳ Waiting for data transformation to complete...</span>
                    )}
                  </div>
                </div>

                {/* Step 5: 评论导入 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center text-sm font-bold text-green-600">5</div>
                    <span className="font-medium">Review Import (JSON → amazon_reviews)</span>
                    {result?.reviews_phase?.importing ? (
                      getStepStatus(result.reviews_phase.importing.status)
                    ) : (
                      <Badge variant="outline">Pending</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.reviews_phase?.importing ? (
                      result.reviews_phase.importing.status === 'success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {result.reviews_phase.importing.reviews_imported || 0} reviews imported</span>
                          <span className="text-xs font-mono bg-green-50 px-2 py-1 rounded">
                            {result.reviews_phase.importing.files_processed || 0} files processed
                          </span>
                        </div>
                      ) : result.reviews_phase.importing.status === 'failed' ? (
                        <span className="text-red-600">❌ Failed: {result.reviews_phase.importing.error || 'Review import failed'}</span>
                      ) : (
                        <span>🔄 In progress...</span>
                      )
                    ) : (
                      <span>⏳ Waiting for review scraping to complete...</span>
                    )}
                  </div>
                </div>

                {/* Step 6: 评论转换 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center text-sm font-bold text-orange-600">6</div>
                    <span className="font-medium">Review Transformation (amazon_reviews → product_reviews)</span>
                    {result?.reviews_phase?.transformation ? (
                      getTransformationStatus(result.reviews_phase.transformation)
                    ) : (
                      <Badge variant="outline">Pending</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.reviews_phase?.transformation ? (
                      result.reviews_phase.transformation.success ? (
                        <div className="space-y-1">
                          <div className="flex items-center gap-4">
                            <span>✅ {result.reviews_phase.transformation.processed_count || 0} reviews transformed</span>
                            <span className="text-xs font-mono bg-orange-50 px-2 py-1 rounded">
                              {result.reviews_phase.transformation.duration_seconds ? `${result.reviews_phase.transformation.duration_seconds.toFixed(1)}s` : 'N/A'}
                            </span>
                          </div>
                          {(result.reviews_phase.transformation.error_count || 0) > 0 && (
                            <div className="text-amber-600">
                              ⚠️ {result.reviews_phase.transformation.error_count || 0} errors occurred
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <span className="text-red-600">❌ Review transformation failed</span>
                          {result.reviews_phase.transformation.errors && result.reviews_phase.transformation.errors.length > 0 && (
                            <div className="text-xs bg-red-50 p-2 rounded mt-1">
                              {result.reviews_phase.transformation.errors[0]}
                            </div>
                          )}
                        </div>
                      )
                    ) : (
                      <span>⏳ Waiting for review import to complete...</span>
                    )}
                  </div>
                </div>
              </div>

              {/* 总体状态 */}
              {result?.overall_status && (
                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <Label className="text-base font-medium">Overall Status</Label>
                    {getOverallStatusBadge(result.overall_status)}
                  </div>
                  {result.error && (
                    <Alert variant="destructive" className="mt-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="font-medium">Error occurred</div>
                        <div className="text-sm mt-1">{result.error}</div>
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* 执行统计和数据质量报告 */}
              {(result?.execution_stats || result?.data_quality) && (
                <div className="space-y-4 pt-4 border-t">
                  <Label className="text-base font-medium">Execution Statistics & Data Quality</Label>
                  
                  {/* 执行时间统计 */}
                  {result?.execution_stats && (
                    <div className="space-y-3">
                      <div className="font-medium text-sm">⏱️ Execution Times</div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                        <div className="bg-blue-50 p-3 rounded-lg">
                          <div className="font-medium text-blue-900">Total Duration</div>
                          <div className="text-lg font-bold text-blue-600">
                            {result.execution_stats.total_duration?.toFixed(1)}s
                          </div>
                        </div>
                        {result?.execution_stats?.phase_durations && Object.entries(result.execution_stats.phase_durations).map(([phase, duration]) => (
                          <div key={phase} className="bg-gray-50 p-3 rounded-lg">
                            <div className="font-medium text-gray-700 capitalize">
                              {phase.replace(/_/g, ' ').replace(/transformation/g, 'transform')}
                            </div>
                            <div className="text-sm font-bold text-gray-600">
                              {(duration as number)?.toFixed(1)}s
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* API调用统计 */}
                  {result?.execution_stats?.api_calls && (
                    <div className="space-y-3">
                      <div className="font-medium text-sm">🔗 API Calls</div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div className="bg-purple-50 p-3 rounded-lg">
                          <div className="font-medium text-purple-900">Total Calls</div>
                          <div className="text-lg font-bold text-purple-600">
                            {result.execution_stats.api_calls.total || 0}
                          </div>
                        </div>
                        <div className="bg-indigo-50 p-3 rounded-lg">
                          <div className="font-medium text-indigo-900">Category API</div>
                          <div className="text-sm font-bold text-indigo-600">
                            {result.execution_stats.api_calls.category_api || 0}
                          </div>
                        </div>
                        <div className="bg-cyan-50 p-3 rounded-lg">
                          <div className="font-medium text-cyan-900">Product Details</div>
                          <div className="text-sm font-bold text-cyan-600">
                            {result.execution_stats.api_calls.product_details_api || 0}
                          </div>
                        </div>
                        <div className="bg-teal-50 p-3 rounded-lg">
                          <div className="font-medium text-teal-900">Reviews API</div>
                          <div className="text-sm font-bold text-teal-600">
                            {result.execution_stats.api_calls.reviews_api || 0}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 数据质量报告 */}
                  {result?.data_quality && (
                    <div className="space-y-3">
                      <div className="font-medium text-sm">📊 Data Quality Report</div>
                      
                      {/* 总体评分 */}
                      <div className="bg-gradient-to-r from-emerald-50 to-green-50 p-4 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-emerald-900">Overall Quality Score</div>
                            <div className="text-2xl font-bold text-emerald-600">
                              {result.data_quality.overall_quality_score}/100
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-emerald-700">
                              {result.data_quality.total_products} products analyzed
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* 关键字段覆盖率 */}
                      {result.data_quality.field_coverage && (
                        <div className="space-y-2">
                          <div className="text-sm font-medium">Key Field Coverage</div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                            {['platform_id', 'brand', 'recent_sales', 'unit_price', 'list_price_usd', 'is_bestseller'].map((field) => {
                              const coverage = result.data_quality?.field_coverage?.[field];
                              const percent = coverage?.coverage_percent || 0;
                              const color = percent >= 80 ? 'green' : percent >= 60 ? 'yellow' : 'red';
                              
                              return (
                                <div key={field} className={`bg-${color}-50 p-2 rounded`}>
                                  <div className={`font-medium text-${color}-900 capitalize`}>
                                    {field.replace(/_/g, ' ')}
                                  </div>
                                  <div className={`text-lg font-bold text-${color}-600`}>
                                    {percent.toFixed(1)}%
                                  </div>
                                  <div className={`text-${color}-700`}>
                                    {coverage?.with_value || 0}/{coverage?.total || 0}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* 改进建议 */}
                      {result.data_quality.quality_summary?.recommendations && (
                        <div className="bg-amber-50 p-3 rounded-lg">
                          <div className="font-medium text-amber-900 mb-2">💡 Recommendations</div>
                          <ul className="text-sm text-amber-800 space-y-1">
                            {result.data_quality.quality_summary.recommendations.map((rec, index) => (
                              <li key={index} className="flex items-start gap-2">
                                <span className="text-amber-600">•</span>
                                <span>{rec}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* 兼容旧格式的结果显示 */}
              {result?.results && (
                <div className="space-y-2 pt-4 border-t">
                  <Label>Legacy Results Summary</Label>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <div className="font-medium text-blue-900">Products Scraped</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {result.results.products_scraped}
                      </div>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <div className="font-medium text-green-900">Reviews Scraped</div>
                      <div className="text-2xl font-bold text-green-600">
                        {result.results.reviews_scraped}
                      </div>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg">
                      <div className="font-medium text-purple-900">Data Location</div>
                      <div className="text-xs font-mono text-purple-600 break-all">
                        {result.results.data_saved_to}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

      </div>
    </div>
  );
} 