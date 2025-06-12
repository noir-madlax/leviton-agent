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
      console.error('图表渲染失败:', error);
      setError(error instanceof Error ? error.message : '未知渲染错误');
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
            <p className="text-muted-foreground">图表加载中...</p>
          </div>
        )}
      </div>

      {/* 图表说明和洞察 */}
      <div className="space-y-3">
        <div>
          <h4 className="text-sm font-semibold mb-1">图表说明</h4>
          <p className="text-sm text-muted-foreground">
            {chartData.explanation}
          </p>
        </div>
        
        <div>
          <h4 className="text-sm font-semibold mb-1">数据洞察</h4>
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
          <h3 className="text-lg font-semibold mb-2">等待生成图表</h3>
          <p className="text-muted-foreground">
            在左侧聊天区域问我关于数据的问题，我会为您生成相应的可视化图表
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
          <h3 className="text-lg font-semibold mb-2">正在生成图表...</h3>
          <p className="text-muted-foreground">AI 正在分析您的数据</p>
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
            图表生成失败
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
            <p>可能的解决方法：</p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>重新描述您的数据分析需求</li>
              <li>确保问题描述清晰明确</li>
              <li>稍后再试</li>
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
            {isMultipleCharts ? '产品市场分析报告' : '数据可视化'}
          </h2>
          <Badge variant="outline" className="text-xs">
            {new Date(currentChart.timestamp).toLocaleString('zh-CN')}
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
                    title="维度一：客户痛点分析"
                  />
                </CardContent>
              </Card>
            )}
            
            {currentChart.chart2 && (
              <Card>
                <CardContent className="p-6">
                  <SingleChartRenderer 
                    chartData={currentChart.chart2} 
                    title="维度二：市场机会分析"
                  />
                </CardContent>
              </Card>
            )}
            
            {currentChart.chart3 && (
              <Card>
                <CardContent className="p-6">
                  <SingleChartRenderer 
                    chartData={currentChart.chart3} 
                    title="维度三：竞争优势分析"
                  />
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          // 单图表布局（向后兼容）
          <Card className="h-full">
            <CardContent className="p-6">
              <SingleChartRenderer 
                chartData={{
                  code: currentChart.code!,
                  explanation: currentChart.explanation!,
                  insights: currentChart.insights!
                }}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
} 