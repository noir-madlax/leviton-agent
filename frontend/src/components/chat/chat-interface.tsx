'use client';

import { useChat } from 'ai/react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, MessageSquare, TestTube2, ChevronDown, ChevronUp } from 'lucide-react';
import { useChart } from '@/contexts/chart-context';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { config } from '@/lib/config';
import { MessageList } from './message-list';

// 图表数据类型定义
interface ChartData {
  code: string;
  explanation: string;
  insights: string;
}

interface SingleChartData {
  chartData: ChartData;
  timestamp: number;
  type: 'single';
  chartType?: string;
}

interface MultiChartData {
  chart1?: ChartData;
  chart2?: ChartData;
  chart3?: ChartData;
  timestamp: number;
  type: 'multiple';
  chartType?: string;
}

export function ChatInterface() {
  const { updateChart, setCompiling, setError } = useChart();
  
  // 使用统一配置
  const backendUrl = config.backendUrl;
  
  // 测试区域相关状态
  const [testDataOpen, setTestDataOpen] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testError, setTestError] = useState<string | null>(null);

  // 使用 Vercel AI SDK 的 useChat hook
  const { 
    messages, 
    input, 
    handleInputChange, 
    handleSubmit, 
    isLoading,
    error 
  } = useChat({
    api: `${backendUrl}/agent-stream`,
    streamProtocol: 'text',
    fetch: async (url, options) => {
      // 自定义fetch以适配后端的GET + query参数方式并处理 rechart 消息
      if (!options?.body) {
        throw new Error('No request body provided');
      }
      
      const body = JSON.parse(options.body as string);
      const query = body.messages[body.messages.length - 1].content;
      const getUrl = `${url}?query=${encodeURIComponent(query)}`;
      
      const response = await fetch(getUrl, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // 创建自定义的 ReadableStream 来处理 SSE 消息
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      const stream = new ReadableStream({
        start(controller) {
          function pump(): Promise<void> {
            return reader!.read().then(({ done, value }) => {
              if (done) {
                controller.close();
                return;
              }

              const chunk = decoder.decode(value);
              const lines = chunk.split('\n');

              let shouldPassthrough = true;

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const jsonStr = line.substring(6);
                  try {
                    const sseData = JSON.parse(jsonStr);
                    
                    // 处理 rechart 消息
                    if (sseData.status === 'rechart' && sseData.message) {
                      console.log('📊 收到 rechart 脚本:', sseData.message);
                      
                      // 创建图表数据格式
                      const singleChartData: SingleChartData = {
                        chartData: {
                          code: sseData.message,
                          explanation: 'AI 生成的 Recharts 图表',
                          insights: '基于数据分析生成的可视化图表'
                        },
                        timestamp: Date.now(),
                        type: 'single' as const,
                      };
                      
                      // 立即更新图表
                      updateChart(singleChartData);
                      // rechart 消息不需要传递给 useChat
                      shouldPassthrough = false;
                    }
                    
                    // 对于其他类型的消息，继续传递给 useChat
                    if (sseData.status === 'streaming' || sseData.status === 'completed') {
                      // 保持原始传递逻辑
                    } else if (sseData.status !== 'rechart') {
                      // 未知状态也传递，但排除 rechart
                    }
                  } catch {
                    // 不是 JSON 格式，继续传递
                  }
                }
              }

              // 只有当不是 rechart 消息时才传递
              if (shouldPassthrough) {
                controller.enqueue(value);
              }

              return pump();
            });
          }

          return pump();
        }
      });

      return new Response(stream, {
        headers: response.headers,
      });
    },
    onResponse: (response) => {
      if (!response.ok) {
        setError(`服务器错误: ${response.status}`);
        return;
      }
      setCompiling(true);
      setError(null);
    },
    onFinish: (message) => {
      setCompiling(false);
      // 简化：不再处理复杂的 JSON 提取，rechart 消息已在流式处理中处理
      console.log('💬 消息完成:', message.content);
    },
    onError: (error) => {
      setCompiling(false);
      setError(`连接失败: ${error.message}`);
    }
  });

  // 发送消息函数
  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    setError(null);
    handleSubmit(e);
  };

  // 测试图表渲染函数 - 支持单图表和多图表格式
  const handleTestChart = () => {
    setTestError(null);
    
    if (!testInput.trim()) {
      setTestError('请输入测试数据');
      return;
    }

    try {
      // 尝试解析JSON数据
      const parsedData = JSON.parse(testInput);
      
      let chartDataWithTimestamp: SingleChartData | MultiChartData;
      
      // 检查是否为多图表格式
      if (parsedData.chart1 || parsedData.chart2) {
        // 多图表格式验证
        const charts = [];
        if (parsedData.chart1) {
          if (!parsedData.chart1.code || !parsedData.chart1.explanation || !parsedData.chart1.insights) {
            setTestError('chart1 格式错误：缺少必要字段 (code, explanation, insights)');
            return;
          }
          charts.push('chart1');
        }
        if (parsedData.chart2) {
          if (!parsedData.chart2.code || !parsedData.chart2.explanation || !parsedData.chart2.insights) {
            setTestError('chart2 格式错误：缺少必要字段 (code, explanation, insights)');
            return;
          }
          charts.push('chart2');
        }
        if (parsedData.chart3) {
          if (!parsedData.chart3.code || !parsedData.chart3.explanation || !parsedData.chart3.insights) {
            setTestError('chart3 格式错误：缺少必要字段 (code, explanation, insights)');
            return;
          }
          charts.push('chart3');
        }
        
        // 构建多图表数据
        chartDataWithTimestamp = {
          ...parsedData,
          timestamp: Date.now(),
          type: 'multiple' as const,
        };
        
      } else if (parsedData.chartData) {
        // 单图表格式验证（向后兼容）
        const { chartData } = parsedData;
        
        if (!chartData.code || !chartData.explanation || !chartData.insights) {
          setTestError('chartData 格式错误：缺少必要字段 (code, explanation, insights)');
          return;
        }

        // 构建单图表数据
        chartDataWithTimestamp = {
          ...parsedData,
          timestamp: Date.now(),
          type: 'single' as const,
        };
        
      } else {
        setTestError('数据格式错误：需要包含 chartData 字段或 chart1/chart2 字段');
        return;
      }

      // 更新图表
      updateChart(chartDataWithTimestamp);
      
    } catch (error) {
      console.error('解析测试数据失败:', error);
      setTestError('JSON 格式错误，请检查数据格式');
    }
  };

  return (
    <div className="h-full flex flex-col bg-background">
      {/* 顶部标题栏 - 固定高度 */}
      <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-2 p-4">
          <MessageSquare className="h-5 w-5" />
          <h2 className="font-semibold">AI 数据分析助手</h2>
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
              生成中...
            </div>
          )}
        </div>
      </div>
      
      {/* 测试数据输入区域 - 可折叠，限制最大高度 */}
      <div className="flex-shrink-0 border-b bg-background">
        <div className="p-4">
          <Collapsible open={testDataOpen} onOpenChange={setTestDataOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="outline" className="w-full justify-between">
                <div className="flex items-center gap-2">
                  <TestTube2 className="h-4 w-4" />
                  测试图表数据输入
                </div>
                {testDataOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-4">
              {/* 限制测试区域最大高度，内容可滚动 */}
              <div className="max-h-[400px] overflow-y-auto">
                <div className="space-y-4 pr-2">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">
                        输入图表数据 (JSON格式)
                      </label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setTestInput('');
                          setTestError(null);
                        }}
                        className="text-xs h-6 px-2"
                      >
                        清空
                      </Button>
                    </div>
                    
                    {/* 使用ScrollArea包装Textarea确保长内容可以滚动 */}
                    <div className="border rounded-md">
                      <ScrollArea className="h-[200px] w-full">
                        <Textarea
                          value={testInput}
                          onChange={(e) => setTestInput(e.target.value)}
                          placeholder={`请输入图表数据，例如：
{
  "chartData": {
    "code": "React组件代码",
    "explanation": "图表说明",
    "insights": "数据洞察"
  }
}

或多图表格式：
{
  "chart1": {
    "code": "第一个图表代码",
    "explanation": "第一个图表说明",
    "insights": "第一个图表洞察"
  },
  "chart2": {
    "code": "第二个图表代码",
    "explanation": "第二个图表说明", 
    "insights": "第二个图表洞察"
  }
}`}
                          className="min-h-[180px] text-xs font-mono border-0 resize-none focus-visible:ring-0"
                        />
                      </ScrollArea>
                    </div>
                  </div>
                  
                  {testError && (
                    <Alert variant="destructive">
                      <AlertDescription>{testError}</AlertDescription>
                    </Alert>
                  )}
                  
                  {/* 操作按钮区域 - 固定在底部 */}
                  <div className="flex gap-2 pt-2 border-t bg-background">
                    <Button onClick={handleTestChart} className="flex-1">
                      <TestTube2 className="h-4 w-4 mr-2" />
                      测试渲染图表
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setTestDataOpen(false)}
                      className="px-4"
                    >
                      收起
                    </Button>
                  </div>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </div>

      {/* 消息列表区域 - 占据剩余空间并可滚动 */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4">
            <MessageList 
              messages={messages
                .filter(msg => msg.role === 'user' || msg.role === 'assistant')
                .map(msg => ({
                  id: msg.id,
                  role: msg.role as 'user' | 'assistant',
                  content: msg.content,
                  timestamp: msg.createdAt ? new Date(msg.createdAt).getTime() : Date.now()
                }))} 
              isLoading={isLoading} 
            />
          </div>
        </ScrollArea>
      </div>

      {/* 输入框 - 固定在底部 */}
      <div className="flex-shrink-0 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="p-4">
          <form onSubmit={handleFormSubmit} className="flex gap-2">
            <Textarea
              value={input}
              onChange={handleInputChange}
              placeholder="询问关于数据的任何问题..."
              className="min-h-[40px] max-h-[120px] resize-none"
              disabled={isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleFormSubmit(e);
                }
              }}
            />
            <Button 
              type="submit" 
              size="icon"
              disabled={isLoading || !input.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
          
          <p className="text-xs text-muted-foreground mt-2 text-center">
            按 Enter 发送，Shift + Enter 换行
          </p>
          
          {error && (
            <Alert variant="destructive" className="mt-2">
              <AlertDescription>{typeof error === 'string' ? error : error.message}</AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    </div>
  );
} 