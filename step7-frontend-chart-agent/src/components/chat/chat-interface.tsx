'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, MessageSquare, TestTube2, ChevronDown, ChevronUp } from 'lucide-react';
import { MessageList } from './message-list';
import { ChatMessage } from '@/lib/types';
import { useChart } from '@/contexts/chart-context';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Alert, AlertDescription } from '@/components/ui/alert';

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { updateChart, setCompiling } = useChart();
  
  // 测试区域相关状态
  const [testDataOpen, setTestDataOpen] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testError, setTestError] = useState<string | null>(null);

  // 发送消息函数
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);
    setCompiling(true);

    try {
      // 调用API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: newMessages,
        }),
      });

      if (!response.ok) {
        throw new Error('API调用失败');
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.content,
        timestamp: Date.now(),
        chartData: data.chartData,
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      if (data.chartData) {
        updateChart(data.chartData);
      }
      
    } catch (error) {
      console.error('发送消息失败:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，生成图表时出现了错误。请稍后重试。',
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
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
      
      let chartDataWithTimestamp;
      
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
          ...chartData,
          timestamp: Date.now(),
          type: 'single' as const,
        };
        
      } else {
        setTestError('数据格式错误：需要包含 chartData 字段或 chart1/chart2 字段');
        return;
      }

      // 更新图表
      updateChart(chartDataWithTimestamp);
      
      // 添加到消息列表
      const testMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: chartDataWithTimestamp.type === 'multiple' ? '测试多图表已生成' : '测试图表已生成',
        timestamp: Date.now(),
        chartData: chartDataWithTimestamp,
      };
      setMessages(prev => [...prev, testMessage]);
      
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
        </div>
      </div>
      
      {/* 测试数据输入区域 - 可折叠 */}
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
            <CollapsibleContent className="space-y-3 mt-3">
              <div className="space-y-2">
                <ScrollArea className="h-[250px] w-full border rounded-md">
                  <Textarea
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    placeholder='粘贴 LLM 返回的 JSON 数据，支持以下格式：

单图表格式：
{
  "chartData": {
    "code": "React图表代码...",
    "explanation": "图表说明...",
    "insights": "数据洞察..."
  }
}

多图表格式：
{
  "chart1": {
    "code": "第一个图表代码...",
    "explanation": "第一个图表说明...",
    "insights": "第一个图表洞察..."
  },
  "chart2": {
    "code": "第二个图表代码...",
    "explanation": "第二个图表说明...",
    "insights": "第二个图表洞察..."
  }
}'
                    className="min-h-[200px] font-mono text-sm border-0 resize-none"
                  />
                </ScrollArea>
                <div className="flex gap-2">
                  <Button 
                    onClick={handleTestChart}
                    className="flex-1"
                    variant="secondary"
                  >
                    <TestTube2 className="h-4 w-4 mr-2" />
                    测试渲染图表
                  </Button>
                  <Button 
                    onClick={() => {
                      setTestInput('');
                      setTestError(null);
                    }}
                    variant="outline"
                  >
                    清空
                  </Button>
                </div>
                {testError && (
                  <Alert variant="destructive">
                    <AlertDescription>{testError}</AlertDescription>
                  </Alert>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </div>

      {/* 消息列表区域 - 可滚动，占据剩余空间 */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4">
            <MessageList messages={messages} isLoading={isLoading} />
          </div>
        </ScrollArea>
      </div>

      {/* 输入区域 - 固定在底部 */}
      <div className="flex-shrink-0 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="p-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="问我关于数据的任何问题..."
              className="flex-1 min-h-[80px] max-h-[200px] resize-none"
              disabled={isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <Button 
              type="submit" 
              disabled={!input.trim() || isLoading}
              className="self-end"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
          <p className="text-xs text-muted-foreground mt-2">
            按 Enter 发送，Shift + Enter 换行
          </p>
        </div>
      </div>
    </div>
  );
} 