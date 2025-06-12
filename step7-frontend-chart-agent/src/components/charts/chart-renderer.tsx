'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { BarChart3, AlertTriangle, Loader2 } from 'lucide-react';
import { useChart } from '@/contexts/chart-context';
import { compileChartCode, validateChartCode } from '@/lib/chart-compiler';
import React from 'react';

export function ChartRenderer() {
  const { currentChart, isCompiling, compilationError, setError } = useChart();
  const [CompiledChart, setCompiledChart] = useState<React.ComponentType | null>(null);
  const [isRendering, setIsRendering] = useState(false);

  useEffect(() => {
    if (currentChart) {
      renderChart(currentChart.code);
    }
  }, [currentChart]);

  const renderChart = async (chartCode: string) => {
    setIsRendering(true);
    setError(null);

    try {
      // 第一步：验证代码安全性
      const validation = validateChartCode(chartCode);
      if (!validation.valid) {
        throw new Error(validation.error);
      }

      // 第二步：编译代码
      const result = compileChartCode(chartCode);
      if (!result.success) {
        throw new Error(result.error);
      }

      // 第三步：设置组件
      setCompiledChart(() => result.component!);
      
    } catch (error) {
      console.error('图表渲染失败:', error);
      setError(error instanceof Error ? error.message : '未知渲染错误');
      setCompiledChart(null);
    } finally {
      setIsRendering(false);
    }
  };

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
  if (isCompiling || isRendering) {
    return (
      <Card className="h-full flex items-center justify-center">
        <CardContent className="text-center">
          <Loader2 className="h-16 w-16 text-blue-500 animate-spin mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">
            {isCompiling ? '正在生成图表...' : '正在渲染图表...'}
          </h3>
          <p className="text-muted-foreground">
            {isCompiling ? 'AI 正在分析您的数据' : '正在编译图表代码'}
          </p>
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

  // 渲染图表
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            数据可视化
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {new Date(currentChart!.timestamp).toLocaleString('zh-CN')}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-4 p-4">
        {/* 图表渲染区域 */}
        <div className="flex-1 min-h-0 bg-gray-50 rounded-lg p-4">
          {CompiledChart ? (
            <div className="w-full h-full">
              <CompiledChart />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-muted-foreground">图表加载中...</p>
            </div>
          )}
        </div>

        {/* 图表说明 */}
        {currentChart && (
          <div className="flex-shrink-0 space-y-3">
            <div>
              <h4 className="text-sm font-semibold mb-1">图表说明</h4>
              <p className="text-sm text-muted-foreground">
                {currentChart.explanation}
              </p>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold mb-1">数据洞察</h4>
              <p className="text-sm text-muted-foreground">
                {currentChart.insights}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 