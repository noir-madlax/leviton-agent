'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { config } from '@/lib/config';
import { usePermissions } from '@/hooks/use-permissions';
import { useAuth } from '@/contexts/auth-context';
import { usePostHog } from 'posthog-js/react';
import { useScrapingT } from '@/i18n/hooks';
import { DatabaseService } from '@/components/analysis-db/data/database-service'

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
    status?: 'success' | 'failed' | 'running' | 'pending'; // 🔥 修复
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
  const [isClient, setIsClient] = useState(false);
  const [enableSalesHistory, setEnableSalesHistory] = useState<boolean>(false);
  
  const { permissions } = usePermissions();
  const { user } = useAuth();
  const posthog = usePostHog();
  
  // 翻译hook
  const scrapingTRaw = useScrapingT();
  const t = (key: string) => isClient ? scrapingTRaw(key) : key;

  useEffect(() => {
    setIsClient(true);
  }, []);
  
  // 🔥 新增：实时进度状态管理
  const [isScrapingStarted, setIsScrapingStarted] = useState(false);
  const [currentBatchId, setCurrentBatchId] = useState<number | null>(null);

  
  // 使用统一配置
  const backendUrl = config.backendUrl;

  // 🔥 新增：轮询实时状态
  const pollScrapingStatus = async (batchId: number) => {
    try {
      console.log(`📡 Polling scraping status for batch_id: ${batchId}`);
      const response = await fetch(`${backendUrl}/api/scraping/status/${batchId}`);
      if (!response.ok) {
        console.error(`❌ Polling failed: HTTP ${response.status}`);
        throw new Error(`HTTP ${response.status}`);
      }
      const statusData = await response.json();
      
      console.log(`📊 Received status update:`, {
        batch_id: batchId,
        overall_status: statusData.overall_status,
        workflow_stage: statusData.workflow_stage,
        products_scraped: statusData.products_scraped || 0,
        reviews_scraped: statusData.reviews_scraped || 0
      });
      
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
      console.error(`❌ Failed to poll scraping status for batch_id ${batchId}:`, error);
      return null;
    }
  };

  // 🔥 新增：启动轮询状态
  const startPollingStatus = (taskId: number) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusData = await pollScrapingStatus(taskId);
        
        if (statusData) {
          // 检查是否完成或失败 - 改进状态判断逻辑
          const isCompleted = statusData.overall_status === 'completed' || 
                             statusData.workflow_stage === 'completed';
          
          const isFailed = statusData.overall_status === 'failed' || 
                          statusData.workflow_stage === 'failed' ||
                          statusData.error;
          
          // 🔥 新增：检查智能跳过状态
          const isSmartSkipped = statusData.overall_status && 
                                (statusData.overall_status.includes('Smart Skip') ||
                                 statusData.overall_status.includes('skip'));
          
          const isFinished = isCompleted || isFailed || isSmartSkipped;
          
          if (isFinished) {
            console.log(`✅ Task finished for batch_id ${taskId}:`, {
              overall_status: statusData.overall_status,
              workflow_stage: statusData.workflow_stage,
              is_completed: isCompleted,
              is_failed: isFailed,
              is_smart_skipped: isSmartSkipped
            });
            
            clearInterval(pollInterval);
            setIsLoading(false);
            
            // 记录最终结果
            if (isCompleted || isSmartSkipped) {
              posthog.capture('data_import_success', {
                url: url.trim(),
                max_products: maxProducts === '' ? 5 : maxProducts,
                max_reviews: maxReviews === '' ? 15 : maxReviews,
                batch_id: taskId,
                products_scraped: statusData.products_scraped || 0,
                reviews_scraped: statusData.reviews_scraped || 0,
                overall_status: statusData.overall_status,
                user_id: user?.id,
                user_email: user?.email,
              });

              // 🔄 If enabled, trigger sales history scraping for the latest project
              if (enableSalesHistory) {
                try {
                  const dbSvc = new DatabaseService();
                  const projects = await dbSvc.getProjects(user?.id);
                  const sorted = (projects || []).sort((a: any, b: any) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
                  const latestProjectId = sorted.length > 0 ? sorted[0].id : null;

                  if (latestProjectId) {
                    const params = new URLSearchParams({
                      platform_source: 'amazon',
                      api_source: 'jungle_scout',
                    });
                    console.log('🔄 Scraping sales history for project:', latestProjectId);
                    const resp = await fetch(`${backendUrl}/api/v1/sales-history/scrape/project/${latestProjectId}?${params.toString()}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                    });
                    const scrapeData = await resp.json().catch(() => ({}));
                    if (!(resp.ok || resp.status === 207)) {
                      console.warn('❌ Sales history scrape failed:', scrapeData?.message || resp.status);
                    } else {
                      console.log('✅ Sales history scraping summary:', scrapeData?.scraping_summary);
                    }
                  } else {
                    console.warn('⚠️  No project found to run sales history scraping');
                  }
                } catch (e) {
                  console.error('❌ Failed to run sales history scraping:', e);
                }
              }
            } else {
              posthog.capture('data_import_failed', {
                url: url.trim(),
                max_products: maxProducts === '' ? 5 : maxProducts,
                max_reviews: maxReviews === '' ? 15 : maxReviews,
                error: statusData.error || 'Task failed',
                batch_id: taskId,
                user_id: user?.id,
                user_email: user?.email,
              });
            }
          }
        } else {
          console.warn(`⚠️  No status data received for batch_id ${taskId}`);
        }
      } catch (error) {
        console.error(`❌ Polling error for batch_id ${taskId}:`, error);
        clearInterval(pollInterval);
        setIsLoading(false);
        
        // 设置错误状态
        setResult(prev => ({
          ...prev,
          overall_status: 'failed',
          error: error instanceof Error ? error.message : 'Polling failed'
        }));
      }
    }, 10000); // 每10秒轮询一次
    
    // 设置最大轮询时间（10分钟）
    const timeoutId = setTimeout(() => {
      console.warn(`⏰ Polling timeout for batch_id ${taskId}, stopping polling after 10 minutes`);
      clearInterval(pollInterval);
      setIsLoading(false);
      
      // 设置超时状态
      setResult(prev => ({
        ...prev,
        overall_status: 'timeout',
        error: 'Task execution timeout (10 minutes)'
      }));
    }, 10 * 60 * 1000);
    
    // 返回清理函数
    return () => {
      clearInterval(pollInterval);
      clearTimeout(timeoutId);
    };
  };

  // 🔥 修改：支持实时进度的启动逻辑
  const handleStartScraping = async () => {
    if (!url.trim()) {
      alert(t('pasteAmazonUrl'));
      return;
    }

    // PostHog 埋点：数据导入尝试
    posthog.capture('data_import_attempt', {
      url: url.trim(),
      max_products: maxProducts === '' ? 5 : maxProducts,
      max_reviews: maxReviews === '' ? 15 : maxReviews,
      user_id: user?.id,
      user_email: user?.email,
    });

    setIsLoading(true);
    setResult(null);
    setIsScrapingStarted(true); // 🔥 立即显示进度界面
    setCurrentBatchId(null);

    try {
      // 先尝试解析为ASIN列表
      const raw = url.trim().toUpperCase();
      const asinMatches = raw.match(/[A-Z0-9]{10}/g) || [];
      const asinList = Array.from(new Set(asinMatches));

      // 🔥 修改：使用异步启动方式
      const isAsinMode = asinList.length >= 1;
      const endpoint = isAsinMode ? `${backendUrl}/api/scraping/import-asins` : `${backendUrl}/api/scraping/process-url`;
      const payload = isAsinMode
        ? { asins: asinList }
        : { url: url.trim(), max_products: maxProducts === '' ? 5 : maxProducts, max_reviews: maxReviews === '' ? 15 : maxReviews };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      
      // 🔥 检查是否为错误状态
      if (data.status === 'failed' || data.overall_status === 'failed' || data.task_id === 'error') {
        console.error('任务创建失败:', data.error);
        // 抛出错误，让catch块处理
        throw new Error(data.error || '任务创建失败');
      }
      
      // 🔥 立即开始轮询状态
      if (data.batch_id || (data.task_id && data.task_id !== 'error')) {
        const taskId = data.batch_id || data.task_id;
        setCurrentBatchId(taskId);
        
        console.log(`🚀 Starting polling for task_id: ${taskId}`);
        
        // 启动轮询
        const cleanupPolling = startPollingStatus(taskId);
        
        // 保存清理函数以备后用
        if (cleanupPolling) {
          // 在组件卸载时清理
          return () => cleanupPolling();
        }
      } else {
        // 如果没有task_id，说明是旧的同步模式，记录成功
        posthog.capture('data_import_success', {
          url: url.trim(),
          max_products: maxProducts === '' ? 5 : maxProducts,
          max_reviews: maxReviews === '' ? 15 : maxReviews,
          batch_id: data.batch_id,
          products_scraped: data.results?.products_scraped || 0,
          reviews_scraped: data.results?.reviews_scraped || 0,
          overall_status: data.overall_status,
          user_id: user?.id,
          user_email: user?.email,
        });
      }
      
    } catch (error) {
      console.error('Scraping failed:', error);
      
      // PostHog 埋点：数据导入失败
      posthog.capture('data_import_failed', {
        url: url.trim(),
        max_products: maxProducts === '' ? 5 : maxProducts,
        max_reviews: maxReviews === '' ? 15 : maxReviews,
        error: error instanceof Error ? error.message : 'Failed to start scraping task',
        user_id: user?.id,
        user_email: user?.email,
      });
      
      setResult({
        task_id: 'error',
        status: 'failed',
        error: error instanceof Error ? error.message : 'Failed to start scraping task',
      });
    } finally {
      // Note: We don't set setIsLoading to false here for async tasks, 
      // it will be handled by the poller.
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />{t('completed')}</Badge>;
      case 'failed':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />{t('failed')}</Badge>;
      case 'running':
        return <Badge variant="secondary"><Loader2 className="w-3 h-3 mr-1 animate-spin" />{t('running')}</Badge>;
      case 'timeout':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />{t('timeout')}</Badge>;
      default:
        if (status && (status.includes('Smart Skip') || status.includes('skip'))) {
          return <Badge variant="default" className="bg-sky-500"><CheckCircle className="w-3 h-3 mr-1" />{t('smartSkip')}</Badge>;
        }
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getStepStatus = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />{t('success')}</Badge>;
      case 'failed':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />{t('failed')}</Badge>;
      case 'running':
        return <Badge variant="secondary"><Loader2 className="w-3 h-3 mr-1 animate-spin" />{t('running')}</Badge>;
      case 'pending':
        return <Badge variant="outline">{t('pending')}</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getOverallStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />{t('completed')}</Badge>;
      case 'products_only_completed':
        return <Badge variant="default" className="bg-blue-500"><CheckCircle className="w-3 h-3 mr-1" />{t('products')} Only</Badge>;
      case 'failed':
      case 'product_scraping_failed':
      case 'product_importing_failed':
      case 'transformation_failed':
      case 'review_scraping_failed':
      case 'review_importing_failed':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />{t('failed')}</Badge>;
      case 'running':
        return <Badge variant="secondary"><Loader2 className="w-3 h-3 mr-1 animate-spin" />{t('running')}</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-4xl mx-auto space-y-6">
      

        {/* URL输入区域 */}
        <Card>
          <CardHeader>
            <CardTitle>{t('dataSource')}</CardTitle>
            <CardDescription>
             
              <div className="text-sm text-muted-foreground space-y-2">
                <div>
                  <strong>{t('categoryUrl')}</strong> ({t('collectsTopProducts')}): https://www.amazon.com/b?node=629135801
                </div>
                <div>
                  <strong>{t('productUrl')}</strong> ({t('collectsDataFor')} <strong>{t('specificProduct')}</strong>): https://www.amazon.com/dp/B00NG0ELL0
                </div>
              </div>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="url">{t('amazonUrl')}</Label>
              <div className="flex gap-2">
                <Input
                  id="url"
                  placeholder={t('pasteAmazonUrl')}
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1"
                />
                <Button 
                  onClick={handleStartScraping} 
                  disabled={isLoading || !url.trim() || !permissions?.can_import_data}
                  className="min-w-[120px]"
                  title={!permissions?.can_import_data ? t('internalTesting') : ""}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      {t('collecting')}
                    </>
                  ) : (
                    t('startCollection')
                  )}
                </Button>
              </div>
             
            </div>
          </CardContent>
        </Card>

        {/* 参数设置 */}
        <Card>
          <CardHeader>
            <CardTitle>{t('collectionParameters')}</CardTitle>
            <CardDescription>
              {t('configureDataCollection')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="maxProducts">{t('maxProductsCategory')}</Label>
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
                  {t('maxProductsScrape')}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxReviews">{t('maxReviews')}</Label>
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
                  {t('maxReviewsPerProduct')}
                </p>
              </div>
              {/* 🔄 新增：是否同时导入销售历史 */}
              <div className="col-span-2 flex items-center gap-3 pt-2">
                <input
                  id="enableSalesHistory"
                  type="checkbox"
                  className="h-4 w-4"
                  checked={enableSalesHistory}
                  onChange={(e) => setEnableSalesHistory(e.target.checked)}
                />
                <Label htmlFor="enableSalesHistory" className="cursor-pointer">
                  Import Sales History (Jungle Scout) after data import
                </Label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 结果显示 - 🔥 修改：支持立即显示进度 */}
        {(result || isScrapingStarted) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {t('scrapingResults')}
                {result?.overall_status && getStatusBadge(result.overall_status)}
                {isScrapingStarted && !result && (
                  <Badge variant="secondary">
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    {t('starting')}
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label>{t('url')}</Label>
                  <div className="font-mono text-xs bg-muted p-2 rounded break-all">
                    {result?.url || url || 'N/A'}
                  </div>
                </div>
                <div>
                  <Label>{t('batchId')}</Label>
                  <div className="font-mono text-xs bg-muted p-2 rounded">
                    {result?.batch_id || currentBatchId || 'Pending...'}
                  </div>
                </div>
              </div>

              {/* 🔥 修改：立即显示步骤进度 */}
              <div className="space-y-4">
                <Label className="text-base font-medium">{t('processingSteps')}</Label>
                
                {/* Step 1: 产品爬取 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-sm font-bold text-blue-600">1</div>
                    <span className="font-medium">{t('productScraping')}</span>
                    {result?.products_phase?.scraping ? (
                      getStepStatus(result.products_phase.scraping.status)
                    ) : isScrapingStarted ? (
                      <Badge variant="secondary">
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                        {t('inProgress')}
                      </Badge>
                    ) : (
                      <Badge variant="outline">{t('pending')}</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.products_phase?.scraping ? (
                      result.products_phase.scraping.status === 'success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {result.products_phase.scraping.products_scraped || 0} {t('productsScrapped')}</span>
                          {result.products_phase.scraping.file_path && (
                            <span className="text-xs font-mono bg-green-50 px-2 py-1 rounded">
                              {t('dataSaved')}
                            </span>
                          )}
                        </div>
                      ) : result.products_phase.scraping.status === 'failed' ? (
                        <span className="text-red-600">❌ {t('failed')}: {result.products_phase.scraping.error || t('unknownError')}</span>
                      ) : (
                        <span>🔄 {t('inProgress')}...</span>
                      )
                    ) : isScrapingStarted ? (
                      <span>🔄 {t('startingProductScraping')}</span>
                    ) : (
                      <span>⏳ {t('waitingToStart')}</span>
                    )}
                  </div>
                </div>

                {/* Step 2: 产品导入 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-sm font-bold text-blue-600">2</div>
                    <span className="font-medium">{t('productImport')}</span>
                    {result?.products_phase?.importing ? (
                      getStepStatus(result.products_phase.importing.status)
                    ) : (
                      <Badge variant="outline">{t('pending')}</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.products_phase?.importing ? (
                      result.products_phase.importing.status === 'success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {result.products_phase.importing.products_imported || 0} {t('productsImported')}</span>
                          <span className="text-xs font-mono bg-green-50 px-2 py-1 rounded">
                            {t('batchId')}: {result.batch_id}
                          </span>
                        </div>
                      ) : result.products_phase.importing.status === 'failed' ? (
                        <span className="text-red-600">❌ {t('failed')}: {result.products_phase.importing.error || t('importFailed')}</span>
                      ) : (
                        <span>🔄 {t('inProgress')}...</span>
                      )
                    ) : (
                      <span>⏳ {t('waitingProductScraping')}</span>
                    )}
                  </div>
                </div>

                {/* Step 3: 数据转换 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center text-sm font-bold text-purple-600">3</div>
                    <span className="font-medium">{t('productTransformation')}</span>
                    {result?.transformation_phase ? (
                      getStepStatus(result.transformation_phase.status || 'pending')
                    ) : (
                      <Badge variant="outline">{t('pending')}</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.transformation_phase ? (
                      result.transformation_phase.status === 'success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {result.transformation_phase.processed_count || 0} {t('productsTransformed')}</span>
                        </div>
                      ) : result.transformation_phase.status === 'failed' ? (
                        <span className="text-red-600">❌ {t('transformationFailed')}</span>
                      ) : result.transformation_phase.status === 'running' ? (
                        <span>🔄 {t('inProgress')}...</span>
                      ) : (
                        <span>⏳ {t('waitingForProductImport')}</span>
                      )
                    ) : (
                      <span>⏳ {t('waitingForProductImport')}</span>
                    )}
                  </div>
                </div>

                {/* Step 4: 评论爬取 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center text-sm font-bold text-green-600">4</div>
                    <span className="font-medium">{t('reviewScraping')}</span>
                    {result?.reviews_phase?.scraping ? (
                      getStepStatus(result.reviews_phase.scraping.status)
                    ) : (
                      <Badge variant="outline">{t('pending')}</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.reviews_phase?.scraping ? (
                      result.reviews_phase.scraping.status === 'success' || result.reviews_phase.scraping.status === 'partial_success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {t('reviewsScrapedFor')} {result.reviews_phase.scraping.reviews_scraped || 0} {t('reviews')}</span>
                        </div>
                      ) : result.reviews_phase.scraping.status === 'failed' ? (
                        <span className="text-red-600">❌ {t('failed')}: {result.reviews_phase.scraping.error || t('reviewScrapingFailed')}</span>
                      ) : (
                        <span>🔄 {t('inProgress')}...</span>
                      )
                    ) : (
                      <span>⏳ {t('waitingDataTransformation')}</span>
                    )}
                  </div>
                </div>

                {/* Step 5: 评论导入 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center text-sm font-bold text-green-600">5</div>
                    <span className="font-medium">{t('reviewImport')}</span>
                    {result?.reviews_phase?.importing ? (
                      getStepStatus(result.reviews_phase.importing.status)
                    ) : (
                      <Badge variant="outline">{t('pending')}</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.reviews_phase?.importing ? (
                      result.reviews_phase.importing.status === 'success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {result.reviews_phase.importing.reviews_imported || 0} {t('reviewsImported')}</span>
                          <span className="text-xs font-mono bg-green-50 px-2 py-1 rounded">
                            {result.reviews_phase.importing.files_processed || 0} {t('filesProcessed')}
                          </span>
                        </div>
                      ) : result.reviews_phase.importing.status === 'failed' ? (
                        <span className="text-red-600">❌ {t('failed')}: {result.reviews_phase.importing.error || t('reviewImportFailed')}</span>
                      ) : (
                        <span>🔄 {t('inProgress')}...</span>
                      )
                    ) : (
                      <span>⏳ {t('waitingReviewScraping')}</span>
                    )}
                  </div>
                </div>

                {/* Step 6: 评论转换 */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center text-sm font-bold text-orange-600">6</div>
                    <span className="font-medium">{t('reviewTransformation')}</span>
                    {result?.reviews_phase?.transformation ? (
                      getStepStatus(result.reviews_phase.transformation.status || 'pending')
                    ) : (
                      <Badge variant="outline">{t('pending')}</Badge>
                    )}
                  </div>
                  <div className="ml-8 text-sm text-muted-foreground">
                    {result?.reviews_phase?.transformation ? (
                      result.reviews_phase.transformation.status === 'success' ? (
                        <div className="flex items-center gap-4">
                          <span>✅ {result.reviews_phase.transformation.processed_count || 0} {t('reviewsTransformed')}</span>
                        </div>
                      ) : result.reviews_phase.transformation.status === 'failed' ? (
                        <span className="text-red-600">❌ {t('reviewTransformationFailed')}</span>
                      ) : result.reviews_phase.transformation.status === 'running' ? (
                        <span>🔄 {t('inProgress')}...</span>
                      ) : (
                        <span>⏳ {t('waitingReviewImport')}</span>
                      )
                    ) : (
                      <span>⏳ {t('waitingReviewImport')}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* 总体状态 */}
              {result?.overall_status && (
                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <Label className="text-base font-medium">{t('overallStatus')}</Label>
                    {getOverallStatusBadge(result.overall_status)}
                  </div>
                  {result.error && (
                    <Alert variant="destructive" className="mt-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="font-medium">{t('errorOccurred')}</div>
                        <div className="text-sm mt-1">{result.error}</div>
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* 执行统计和数据质量报告 */}
              {(result?.execution_stats || result?.data_quality) && (
                <div className="space-y-4 pt-4 border-t">
                  <Label className="text-base font-medium">{t('executionStatsDataQuality')}</Label>
                  
                  {/* 执行时间统计 */}
                  {result?.execution_stats && (
                    <div className="space-y-3">
                      <div className="font-medium text-sm">{t('executionTimes')}</div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                        <div className="bg-blue-50 p-3 rounded-lg">
                          <div className="font-medium text-blue-900">{t('totalDuration')}</div>
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
                      <div className="font-medium text-sm">{t('apiCalls')}</div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div className="bg-purple-50 p-3 rounded-lg">
                          <div className="font-medium text-purple-900">{t('totalCalls')}</div>
                          <div className="text-lg font-bold text-purple-600">
                            {result.execution_stats.api_calls.total || 0}
                          </div>
                        </div>
                        <div className="bg-indigo-50 p-3 rounded-lg">
                          <div className="font-medium text-indigo-900">{t('categoryApi')}</div>
                          <div className="text-sm font-bold text-indigo-600">
                            {result.execution_stats.api_calls.category_api || 0}
                          </div>
                        </div>
                        <div className="bg-cyan-50 p-3 rounded-lg">
                          <div className="font-medium text-cyan-900">{t('productDetails')}</div>
                          <div className="text-sm font-bold text-cyan-600">
                            {result.execution_stats.api_calls.product_details_api || 0}
                          </div>
                        </div>
                        <div className="bg-teal-50 p-3 rounded-lg">
                          <div className="font-medium text-teal-900">{t('reviewsApi')}</div>
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
                      <div className="font-medium text-sm">{t('dataQualityReport')}</div>
                      
                      {/* 总体评分 */}
                      <div className="bg-gradient-to-r from-emerald-50 to-green-50 p-4 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-emerald-900">{t('overallQualityScore')}</div>
                            <div className="text-2xl font-bold text-emerald-600">
                              {result.data_quality.overall_quality_score}/100
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-emerald-700">
                              {result.data_quality.total_products} {t('productsAnalyzed')}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* 关键字段覆盖率 */}
                      {result.data_quality.field_coverage && (
                        <div className="space-y-2">
                          <div className="text-sm font-medium">{t('keyFieldCoverage')}</div>
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
                          <div className="font-medium text-amber-900 mb-2">{t('recommendations')}</div>
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
                  <Label>{t('legacyResultsSummary')}</Label>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <div className="font-medium text-blue-900">{t('productsScraped')}</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {result.results.products_scraped}
                      </div>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <div className="font-medium text-green-900">{t('reviewsScraped')}</div>
                      <div className="text-2xl font-bold text-green-600">
                        {result.results.reviews_scraped}
                      </div>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg">
                      <div className="font-medium text-purple-900">{t('dataLocation')}</div>
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
