'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Play, FileCode, AlertTriangle, Loader2, BarChart3 } from 'lucide-react';
import { compileChartCode, validateChartCode } from '@/lib/chart-compiler';
import React from 'react';

// 示例代码模板
const EXAMPLE_CHARTS = {
  bar: `const data = [
  { name: '产品A', sales: 4000, profit: 2400 },
  { name: '产品B', sales: 3000, profit: 1398 },
  { name: '产品C', sales: 2000, profit: 9800 },
  { name: '产品D', sales: 2780, profit: 3908 },
  { name: '产品E', sales: 1890, profit: 4800 }
];

const DynamicChart = () => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 40, bottom: 80 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="name" 
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis />
        <Tooltip />
        <Legend verticalAlign="top" height={36} />
        <Bar dataKey="sales" fill="#8884d8" name="销售额" />
        <Bar dataKey="profit" fill="#82ca9d" name="利润" />
      </BarChart>
    </ResponsiveContainer>
  );
};`,
  
  line: `const data = [
  { month: '1月', revenue: 4000, cost: 2400 },
  { month: '2月', revenue: 3000, cost: 1398 },
  { month: '3月', revenue: 2000, cost: 9800 },
  { month: '4月', revenue: 2780, cost: 3908 },
  { month: '5月', revenue: 1890, cost: 4800 },
  { month: '6月', revenue: 2390, cost: 3800 }
];

const DynamicChart = () => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 20, right: 30, left: 40, bottom: 80 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend verticalAlign="top" height={36} />
        <Line type="monotone" dataKey="revenue" stroke="#8884d8" strokeWidth={2} name="收入" />
        <Line type="monotone" dataKey="cost" stroke="#82ca9d" strokeWidth={2} name="成本" />
      </LineChart>
    </ResponsiveContainer>
  );
};`,

  pie: `const data = [
  { name: '移动端', value: 45, color: '#0088FE' },
  { name: '桌面端', value: 30, color: '#00C49F' },
  { name: '平板', value: 15, color: '#FFBB28' },
  { name: '其他', value: 10, color: '#FF8042' }
];

const DynamicChart = () => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart margin={{ top: 20, right: 30, left: 40, bottom: 80 }}>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
          label={({name, percent}) => name + ' ' + (percent * 100).toFixed(0) + '%'}
        >
          {data.map((entry, index) => (
            <Cell key={'cell-' + index} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => [value + '%', '占比']} />
        <Legend verticalAlign="bottom" height={36} />
      </PieChart>
    </ResponsiveContainer>
  );
};`
};

export default function TestChartPage() {
  const [code, setCode] = useState(EXAMPLE_CHARTS.bar);
  const [CompiledChart, setCompiledChart] = useState<React.ComponentType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [lastCompiled, setLastCompiled] = useState<string>('');

  const handleCompile = async () => {
    if (!code.trim()) {
      setError('请输入图表代码');
      return;
    }

    setIsCompiling(true);
    setError(null);

    try {
      // 验证代码安全性
      const validation = validateChartCode(code);
      if (!validation.valid) {
        throw new Error(validation.error);
      }

      // 编译代码
      const result = compileChartCode(code);
      if (!result.success) {
        throw new Error(result.error);
      }

      // 设置组件
      setCompiledChart(() => result.component!);
      setLastCompiled(new Date().toLocaleTimeString());
      
    } catch (error) {
      console.error('图表编译失败:', error);
      setError(error instanceof Error ? error.message : '未知编译错误');
      setCompiledChart(null);
    } finally {
      setIsCompiling(false);
    }
  };

  const loadExample = (type: keyof typeof EXAMPLE_CHARTS) => {
    setCode(EXAMPLE_CHARTS[type]);
    setError(null);
  };

  return (
    <div className="h-full bg-background">
      {/* 头部标题 */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-3 p-4">
          <BarChart3 className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">图表代码测试器</h1>
          <Badge variant="outline">Recharts 动态渲染</Badge>
        </div>
      </div>

      {/* 主内容区域 */}
      <div className="flex gap-4 h-[calc(100%-80px)] p-4">
        {/* 左侧：代码编辑区域 */}
        <Card className="flex flex-col w-1/2">
          <CardHeader className="flex-shrink-0">
            <CardTitle className="flex items-center gap-2">
              <FileCode className="h-5 w-5" />
              图表代码输入
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            {/* 示例按钮 */}
            <div className="flex gap-2 mb-4 flex-wrap">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadExample('bar')}
              >
                柱状图
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadExample('line')}
              >
                折线图
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadExample('pie')}
              >
                饼图
              </Button>
            </div>

            {/* 代码输入框 */}
            <div className="flex-1 flex flex-col">
              <Textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="请输入 Recharts 图表代码..."
                className="flex-1 min-h-[300px] font-mono text-sm resize-none"
              />
            </div>

            <Separator className="my-4" />

            {/* 操作按钮 */}
            <div className="flex gap-2">
              <Button 
                onClick={handleCompile}
                disabled={isCompiling}
                className="flex-1"
              >
                {isCompiling ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    编译中...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    解析渲染
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setCode('');
                  setError(null);
                  setCompiledChart(null);
                }}
              >
                清空
              </Button>
            </div>

            {/* 错误提示 */}
            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* 编译状态 */}
            {lastCompiled && !error && (
              <div className="mt-4 text-sm text-muted-foreground">
                最后编译时间: {lastCompiled}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 右侧：图表预览区域 */}
        <Card className="flex flex-col w-1/2">
          <CardHeader className="flex-shrink-0">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              图表预览
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            <div className="flex-1 bg-gray-50 rounded-lg p-4 min-h-[400px] flex items-center justify-center">
              {isCompiling ? (
                <div className="text-center">
                  <Loader2 className="h-12 w-12 text-primary animate-spin mx-auto mb-4" />
                  <p className="text-muted-foreground">正在编译图表...</p>
                </div>
              ) : error ? (
                <div className="text-center">
                  <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
                  <p className="text-destructive font-medium">编译失败</p>
                  <p className="text-sm text-muted-foreground mt-2">请检查代码格式</p>
                </div>
              ) : CompiledChart ? (
                <div className="w-full h-full">
                  <CompiledChart />
                </div>
              ) : (
                <div className="text-center">
                  <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                  <p className="text-muted-foreground">点击"解析渲染"生成图表</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    或选择左侧的示例代码开始
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 