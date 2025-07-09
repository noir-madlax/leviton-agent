"use client"

import { useState, useEffect } from 'react'
import { ChartNavigationCards } from './chart-navigation-cards'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Send, MessageSquare, Loader2 } from 'lucide-react'
import { useChat } from 'ai/react'
import { useChart } from '@/contexts/chart-context'
import { config } from '@/lib/config'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { SingleChart } from '@/lib/types'

// 复用现有的消息接口
interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  isAnalyzing?: boolean
  contentParts?: ContentPart[]
  isStreaming?: boolean
}

interface ContentPart {
  type: 'text' | 'insight' | 'chart'
  content: string
  isComplete?: boolean
  index?: number
}

interface ChartData {
  code: string
  explanation: string
  insights: string
}

interface SingleChartData {
  chartData: ChartData
  timestamp: number
  type: 'single'
  chartType?: string
}

interface MultiChartData {
  chart1?: ChartData
  chart2?: ChartData
  chart3?: ChartData
  timestamp: number
  type: 'multiple'
  chartType?: string
}

interface ChatWithNavigationProps {
  projectId: string
  onTabChange: (tab: string) => void
  activeTab: string
}

export function ChatWithNavigation({ 
  projectId, 
  onTabChange, 
  activeTab 
}: ChatWithNavigationProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentCharts, setCurrentCharts] = useState<SingleChart[]>([])
  const { updateChart, setCompiling, setError } = useChart()
  
  const backendUrl = config.backendUrl

  // 初始化时添加AI的"第一句话"
  useEffect(() => {
    const initialMessage: Message = {
      id: 'initial-charts',
      content: 'chart-navigation', // 特殊标识
      isUser: false,
      timestamp: new Date()
    }
    setMessages([initialMessage])
  }, [])

  // 使用 Vercel AI SDK 的 useChat hook，复用现有逻辑
  const { 
    messages: aiMessages, 
    input, 
    handleInputChange, 
    handleSubmit, 
    isLoading,
    error: aiError 
  } = useChat({
    api: `${backendUrl}/agent-stream`,
    streamProtocol: 'text',
    fetch: async (url, options) => {
      if (!options?.body) {
        throw new Error('No request body provided')
      }
      
      const body = JSON.parse(options.body as string)
      const query = body.messages[body.messages.length - 1].content
      const getUrl = `${url}?query=${encodeURIComponent(query)}&projectId=${projectId}`
      
      const response = await fetch(getUrl, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      // 创建自定义的 ReadableStream 来处理 SSE 消息
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      const stream = new ReadableStream({
        start(controller) {
          function pump(): Promise<void> {
            return reader!.read().then(({ done, value }) => {
              if (done) {
                controller.close()
                return
              }

              const chunk = decoder.decode(value)
              const lines = chunk.split('\n')

              let shouldPassthrough = true

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const jsonStr = line.substring(6)
                  try {
                    const sseData = JSON.parse(jsonStr)
                    
                    // 处理 rechart 消息
                    if (sseData.status === 'rechart' && sseData.message) {
                      console.log('📊 Received rechart script:', sseData.message)
                      
                      // 创建新的图表数据
                      const newChartData = {
                        code: sseData.message,
                        explanation: 'AI Generated Recharts Chart',
                        insights: 'Chart generated based on data analysis'
                      }
                      
                      // 更新图表列表
                      setCurrentCharts(prev => {
                        const updatedCharts = [...prev, newChartData]
                        
                        // 根据图表数量构建不同格式的 ChartData
                        let chartDataToUpdate: SingleChartData | MultiChartData
                        
                        if (updatedCharts.length === 1) {
                          // 单图表格式
                          chartDataToUpdate = {
                            chartData: updatedCharts[0],
                            timestamp: Date.now(),
                            type: 'single' as const,
                          }
                        } else {
                          // 多图表格式
                          const multiChartData: MultiChartData = {
                            timestamp: Date.now(),
                            type: 'multiple' as const,
                          }
                          
                          // 添加图表到对应的属性
                          updatedCharts.forEach((chart, index) => {
                            if (index === 0) multiChartData.chart1 = chart
                            else if (index === 1) multiChartData.chart2 = chart
                            else if (index === 2) multiChartData.chart3 = chart
                          })
                          
                          chartDataToUpdate = multiChartData
                        }
                        
                        // 立即更新图表
                        updateChart(chartDataToUpdate)
                        
                        return updatedCharts
                      })
                      
                      // rechart 消息不需要传递给 useChat
                      shouldPassthrough = false
                    }
                  } catch {
                    // 不是 JSON 格式，继续传递
                  }
                }
              }

              // 只有当不是 rechart 消息时才传递
              if (shouldPassthrough) {
                controller.enqueue(value)
              }

              return pump()
            })
          }

          return pump()
        }
      })

      return new Response(stream, {
        headers: response.headers,
      })
    },
    onResponse: (response) => {
      if (!response.ok) {
        setError(`Server error: ${response.status}`)
        return
      }
      setCompiling(true)
      setError(null)
    },
    onFinish: (message) => {
      setCompiling(false)
      console.log('💬 Message completed:', message.content)
    },
    onError: (error) => {
      setCompiling(false)
      setError(`Connection failed: ${error.message}`)
    }
  })

  // 转换AI消息为统一格式
  const convertedAiMessages: Message[] = aiMessages.map(msg => ({
    id: msg.id,
    content: msg.content,
    isUser: msg.role === 'user',
    timestamp: new Date(msg.createdAt || Date.now())
  }))

  // 合并消息：初始消息 + AI消息
  const allMessages = [...messages, ...convertedAiMessages]

  // 发送消息函数
  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    
    // 开始新对话时清空图表列表
    setCurrentCharts([])
    setError(aiError ? `Error: ${aiError.message}` : null)
    handleSubmit(e)
  }

  return (
    <div className="min-h-full flex flex-col bg-background">
      {/* Chat Header */}
      <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-2 p-2">
          <MessageSquare className="h-4 w-4" />
          <h2 className="font-medium text-sm">Chart Navigator</h2>
          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Generating...
            </div>
          )}
          {currentCharts.length > 0 && (
            <div className="text-xs text-green-600">
              {currentCharts.length} chart{currentCharts.length > 1 ? 's' : ''} ready
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1">
        <div className="p-2 space-y-2">
          {allMessages.map((message) => (
            <div key={message.id} className="space-y-1">
              {message.content === 'chart-navigation' ? (
                <ChartNavigationCards 
                  onTabChange={onTabChange}
                  activeTab={activeTab}
                />
              ) : (
                <div className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}>
                  {!message.isUser && (
                    <Avatar className="h-5 w-5 mr-1.5 mt-0.5">
                      <AvatarFallback className="text-xs">AI</AvatarFallback>
                    </Avatar>
                  )}
                  <div className={`max-w-[80%] p-2 rounded-lg ${
                    message.isUser 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    <div className="text-xs whitespace-pre-wrap">
                      {message.content}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Input Area - 固定在底部 */}
      <div className="flex-shrink-0 p-2 border-t bg-background sticky bottom-0">
        <form onSubmit={handleFormSubmit} className="flex gap-2">
          <Textarea
            value={input}
            onChange={handleInputChange}
            placeholder="Ask me anything about the data..."
            className="flex-1 min-h-[2rem] max-h-16 resize-none text-sm"
            rows={1}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleFormSubmit(e)
              }
            }}
          />
          <Button 
            type="submit"
            disabled={isLoading || !input.trim()}
            size="sm"
            className="px-2"
          >
            <Send className="h-3 w-3" />
          </Button>
        </form>
      </div>
    </div>
  )
} 