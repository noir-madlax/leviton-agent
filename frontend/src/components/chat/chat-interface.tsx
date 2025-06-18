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
      // 自定义fetch以适配后端的GET + query参数方式
      if (!options?.body) {
        throw new Error('No request body provided');
      }
      
      const body = JSON.parse(options.body as string);
      const query = body.messages[body.messages.length - 1].content;
      const getUrl = `${url}?query=${encodeURIComponent(query)}`;
      
      return fetch(getUrl, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
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
      
      // 从消息内容中提取图表数据
      try {
        const extractChartData = (content: string) => {
          console.log('🔍 尝试提取图表数据，消息内容:', content);
          
          // 方法1: 查找标记包装的图表数据（情况2）
          const chartStartRegex = /<<<CHART_START>>>/g;
          const chartEndRegex = /<<<CHART_END>>>/g;
          
          const startMatch = chartStartRegex.exec(content);
          const endMatch = chartEndRegex.exec(content);
          
          if (startMatch && endMatch) {
            console.log('📦 检测到标记包装的图表数据');
            // 提取图表数据JSON部分
            const startPos = startMatch.index + startMatch[0].length;
            const endPos = endMatch.index;
            const jsonContent = content.substring(startPos, endPos);
            
            // 移除可能存在的类型标记行
            const lines = jsonContent.split('\n').filter(line => 
              !line.includes('<<<CHART_TYPE:') && line.trim() !== ''
            );
            const cleanJson = lines.join('\n').trim();
            
            if (cleanJson) {
              try {
                return JSON.parse(cleanJson);
              } catch (error) {
                console.error('❌ 解析标记包装的JSON失败:', error);
              }
            }
          }
          
          // 方法2: 查找消息中的JSON块（情况1）
          console.log('🔍 尝试提取嵌入的JSON数据');
          
          // 查找```json 代码块
          const jsonBlockRegex = /```json\s*\n([\s\S]*?)\n```/g;
                     const jsonBlockMatch = jsonBlockRegex.exec(content);
          
          if (jsonBlockMatch) {
            console.log('📝 在代码块中找到JSON数据');
            try {
              const jsonData = JSON.parse(jsonBlockMatch[1].trim());
              if (jsonData.chart1 || jsonData.chart2 || jsonData.chartData) {
                return jsonData;
              }
            } catch (error) {
              console.error('❌ 解析代码块JSON失败:', error);
            }
          }
          
          // 方法3: 查找独立的JSON对象（以{开头，chart1/chart2/chartData为键）
          const jsonObjectRegex = /\{[\s\S]*?"chart[12]"[\s\S]*?\}(?=\s*$)/gm;
                     const jsonObjectMatch = jsonObjectRegex.exec(content);
          
          if (jsonObjectMatch) {
            console.log('🎯 找到独立的JSON对象');
            try {
              const jsonData = JSON.parse(jsonObjectMatch[0]);
              if (jsonData.chart1 || jsonData.chart2 || jsonData.chartData) {
                return jsonData;
              }
            } catch (error) {
              console.error('❌ 解析独立JSON对象失败:', error);
            }
          }
          
          // 方法4: 更宽泛的JSON提取（在消息的最后部分查找）
          const lines = content.split('\n');
                     let jsonStartIndex = -1;
           let jsonContent = '';
          
          // 从后往前查找可能的JSON开始位置
          for (let i = lines.length - 1; i >= 0; i--) {
            const line = lines[i].trim();
            if (line.includes('"chart1"') || line.includes('"chart2"') || line.includes('"chartData"')) {
              // 找到包含图表数据的行，开始收集JSON
              jsonStartIndex = i;
              break;
            }
          }
          
          if (jsonStartIndex >= 0) {
            console.log('🔍 尝试从行', jsonStartIndex, '开始提取JSON');
            
            // 向前搜索找到JSON的开始
            for (let i = jsonStartIndex; i >= 0; i--) {
              const line = lines[i].trim();
              if (line.startsWith('{')) {
                // 从这里开始构建JSON
                for (let j = i; j < lines.length; j++) {
                  const currentLine = lines[j].trim();
                  if (currentLine) {
                    jsonContent = lines.slice(i, j + 1).join('\n').trim();
                    try {
                      const jsonData = JSON.parse(jsonContent);
                      if (jsonData.chart1 || jsonData.chart2 || jsonData.chartData) {
                        console.log('✅ 成功提取JSON数据');
                        return jsonData;
                      }
                    } catch {
                      // 继续尝试更多行
                    }
                  }
                }
                break;
              }
            }
          }
          
          console.log('❌ 未能提取到有效的图表数据');
          return null;
        };
        
        const rawChartData = extractChartData(message.content);
        
        if (rawChartData) {
          console.log('🎯 从消息中提取到图表数据:', rawChartData);
          
          if (rawChartData.chart1 || rawChartData.chart2 || rawChartData.chart3) {
            const multiChartData: MultiChartData = {
              chart1: rawChartData.chart1,
              chart2: rawChartData.chart2,
              chart3: rawChartData.chart3,
              timestamp: Date.now(),
              type: 'multiple' as const,
            };
            updateChart(multiChartData);
          } else if (rawChartData.chartData) {
            const singleChartData: SingleChartData = {
              chartData: rawChartData.chartData,
              timestamp: Date.now(),
              type: 'single' as const,
            };
            updateChart(singleChartData);
          }
        }
      } catch (error) {
        console.error('解析图表数据失败:', error);
        // Not a chart response, do nothing. The message will be displayed in the chat.
      }
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
          <div className="p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">欢迎使用 AI 数据分析助手</p>
                <p className="text-sm">
                  询问关于数据的任何问题，我会为您生成相应的图表来可视化展示
                </p>
                <div className="mt-4 text-xs space-y-1">
                  <p>• &quot;显示最近6个月的销售趋势&quot;</p>
                  <p>• &quot;对比各产品的销量表现&quot;</p>
                  <p>• &quot;分析用户增长情况&quot;</p>
                  <p>• &quot;产品市场痛点分析&quot;</p>
                </div>
              </div>
            )}
            
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm">
                    {message.content}
                  </div>
                </div>
              </div>
            ))}
            
            {/* 添加底部间距，确保最后一条消息不会被输入框遮挡 */}
            <div className="h-4" />
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