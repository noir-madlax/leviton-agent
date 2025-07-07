'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { BarChart3, AlertTriangle, Loader2 } from 'lucide-react';
import { useChart } from '@/contexts/chart-context';
import { compileChartCode, validateChartCode } from '@/lib/chart-compiler';
import { SingleChart } from '@/lib/types';
import React from 'react';

// 单个图表渲染组件
function SingleChartRenderer({ chartData, title }: { chartData: SingleChart, title?: string }) {
  const [CompiledChart, setCompiledChart] = useState<React.ComponentType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState(false);

  useEffect(() => {
    renderChart(chartData.code);
  }, [chartData.code]);

  const renderChart = async (chartCode: string) => {
    setIsRendering(true);
    setError(null);

    try {
      // 验证代码安全性
      const validation = validateChartCode(chartCode);
      if (!validation.valid) {
        throw new Error(validation.error);
      }

      // 编译代码
      const result = compileChartCode(chartCode);
      if (!result.success) {
        throw new Error(result.error);
      }

      // 设置组件
      setCompiledChart(() => result.component!);
      
    } catch (error) {
      console.error('Chart rendering failed:', error);
      setError(error instanceof Error ? error.message : 'Unknown rendering error');
      setCompiledChart(null);
    } finally {
      setIsRendering(false);
    }
  };

  if (isRendering) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {title && (
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          {title}
        </h3>
      )}
      
      {/* 图表渲染区域 */}
      <div className="bg-gray-50 rounded-lg p-4 min-h-[400px]">
        {CompiledChart ? (
          <div className="w-full h-full">
            <CompiledChart />
          </div>
        ) : (
          <div className="flex items-center justify-center h-64">
                          <p className="text-muted-foreground">Loading chart...</p>
          </div>
        )}
      </div>

      {/* 图表说明和洞察 */}
      <div className="space-y-3">
        <div>
                        <h4 className="text-sm font-semibold mb-1">Chart Description</h4>
          <p className="text-sm text-muted-foreground">
            {chartData.explanation}
          </p>
        </div>
        
        <div>
                        <h4 className="text-sm font-semibold mb-1">Data Insights</h4>
          <p className="text-sm text-muted-foreground">
            {chartData.insights}
          </p>
        </div>
      </div>
    </div>
  );
}

export function ChartRenderer() {
  const { currentChart, isCompiling, compilationError } = useChart();

  // 渲染空状态
  if (!currentChart && !isCompiling) {
    return (
      <Card className="h-full flex items-center justify-center">
        <CardContent className="text-center">
          <BarChart3 className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Waiting for Chart Generation</h3>
          <p className="text-muted-foreground">
            Ask questions about your data in the chat area, and I'll generate corresponding visualizations
          </p>
        </CardContent>
      </Card>
    );
  }

  // 渲染加载状态
  if (isCompiling) {
    return (
      <Card className="h-full flex items-center justify-center">
        <CardContent className="text-center">
          <Loader2 className="h-16 w-16 text-blue-500 animate-spin mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Generating Chart...</h3>
          <p className="text-muted-foreground">AI is analyzing your data</p>
        </CardContent>
      </Card>
    );
  }

  // 渲染错误状态
  if (compilationError) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            Chart Generation Failed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {compilationError}
            </AlertDescription>
          </Alert>
          <div className="mt-4 text-sm text-muted-foreground">
            <p>Possible solutions:</p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>Rephrase your data analysis request</li>
              <li>Ensure your question is clear and specific</li>
              <li>Try again later</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!currentChart) return null;

  // 确定图表类型和渲染方式
  const isMultipleCharts = currentChart.type === 'multiple' || 
                          (currentChart.chart1 && currentChart.chart2);

  return (
    <div className="h-full flex flex-col">
      {/* 标题栏 */}
      <div className="flex-shrink-0 p-4 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            {isMultipleCharts ? 'Product Market Analysis Report' : 'Data Visualization'}
          </h2>
          <Badge variant="outline" className="text-xs">
            {new Date(currentChart.timestamp).toLocaleString('en-US')}
          </Badge>
        </div>
      </div>

      {/* 图表内容区域 */}
      <div className="flex-1 overflow-auto p-4">
        {isMultipleCharts ? (
          // 多图表布局
          <div className="space-y-8">
            {currentChart.chart1 && (
              <Card>
                <CardContent className="p-6">
                  <SingleChartRenderer 
                    chartData={currentChart.chart1} 
                    title="Dimension 1: Customer Pain Point Analysis"
                  />
                </CardContent>
              </Card>
            )}
            
            {currentChart.chart2 && (
              <Card>
                <CardContent className="p-6">
                  <SingleChartRenderer 
                    chartData={currentChart.chart2} 
                    title="Dimension 2: Market Opportunity Analysis"
                  />
                </CardContent>
              </Card>
            )}
            
            {currentChart.chart3 && (
              <Card>
                <CardContent className="p-6">
                  <SingleChartRenderer 
                    chartData={currentChart.chart3} 
                    title="Dimension 3: Competitive Advantage Analysis"
                  />
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          // 单图表布局 - 支持chartData格式和向后兼容
          <Card className="h-full">
            <CardContent className="p-6">
              {currentChart.chartData ? (
                // 新格式：{ chartData: { code, explanation, insights } }
                <SingleChartRenderer 
                  chartData={currentChart.chartData}
                />
              ) : (
                // 向后兼容：旧的直接属性格式（如果存在）
                <div className="text-center text-muted-foreground">
                  <BarChart3 className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <p>Chart data format is incorrect</p>
                  <p className="text-sm mt-2">Please use standard chart data format</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
} 