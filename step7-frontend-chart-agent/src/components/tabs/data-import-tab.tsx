'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ScrapingResult {
  task_id: string;
  status: 'completed' | 'failed' | 'running';
  message?: string;
  results?: {
    products_scraped: number;
    reviews_scraped: number;
    data_saved_to: string;
  };
  error?: string;
}

export function DataImportTab() {
  const [url, setUrl] = useState('');
  const [maxProducts, setMaxProducts] = useState(100);
  const [maxReviews, setMaxReviews] = useState(50);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ScrapingResult | null>(null);


  // 启动爬虫
  const handleStartScraping = async () => {
    if (!url.trim()) {
      alert('Please enter a URL first');
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/scraping/process-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.trim(),
          max_products: maxProducts,
          max_reviews: maxReviews,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Scraping failed:', error);
      setResult({
        task_id: 'error',
        status: 'failed',
        error: 'Failed to start scraping task',
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

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 页面标题 */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Step 1: Data Import</h1>
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
                  type="number"
                  min="1"
                  max="500"
                  value={maxProducts}
                  onChange={(e) => setMaxProducts(parseInt(e.target.value) || 100)}
                />
                <p className="text-sm text-muted-foreground">
                  Maximum number of products to scrape (1-500)
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxReviews">Max Reviews</Label>
                <Input
                  id="maxReviews"
                  type="number"
                  min="0"
                  max="200"
                  value={maxReviews}
                  onChange={(e) => setMaxReviews(parseInt(e.target.value) || 50)}
                />
                <p className="text-sm text-muted-foreground">
                  Maximum number of reviews to scrape per product (0-200)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>



        {/* 结果显示 */}
        {result && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Scraping Results
                {getStatusBadge(result.status)}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label>Task ID</Label>
                  <div className="font-mono text-xs bg-muted p-2 rounded">
                    {result.task_id}
                  </div>
                </div>
                <div>
                  <Label>Status</Label>
                  <div className="mt-1">
                    {getStatusBadge(result.status)}
                  </div>
                </div>
              </div>

              {result.results && (
                <div className="space-y-2">
                  <Label>Results Summary</Label>
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

              {result.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="font-medium">Error occurred</div>
                    <div className="text-sm mt-1">{result.error}</div>
                  </AlertDescription>
                </Alert>
              )}

              {result.message && (
                <div className="text-sm text-muted-foreground">
                  {result.message}
                </div>
              )}
            </CardContent>
          </Card>
        )}


      </div>
    </div>
  );
} 