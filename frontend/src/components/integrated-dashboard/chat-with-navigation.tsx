"use client"

import { useState } from 'react'
import { MessageSquare, Send, Loader2 } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ChartCardList } from './chat/chart-card-list'
import { UnifiedChartCard, ChartData } from './shared/types'
import { useChart } from '@/contexts/chart-context'
import { config } from '@/lib/config'

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
  type: 'text' | 'chart'
  content: string
  isComplete?: boolean
  index?: number
}

interface ChatWithNavigationProps {
  projectId: string
  chartCards: UnifiedChartCard[]
  activeChartId: string | null
  onChartSelect: (chartId: string) => void
  onAddDynamicChart: (chart: ChartData) => void
}

export function ChatWithNavigation({ 
  projectId, 
  chartCards,
  activeChartId,
  onChartSelect,
  onAddDynamicChart
}: ChatWithNavigationProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "I've prepared comprehensive data analysis charts for your market research. Each chart provides unique insights:",
      isUser: false,
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [compiling, setCompiling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const { updateChart } = useChart()
  
  // 解析图表标题的函数
  const parseChartTitle = (text: string): string => {
    // 匹配类似 "图表概括：这个图表展示了 XXX的各个销量对比" 的模式
    const titlePatterns = [
      /图表概括[：:]\s*这个图表展示了?\s*([^。\n]+)/,
      /图表概括[：:]\s*([^。\n]+)/,
      /This chart shows\s*([^。\n.]+)/i,
      /Chart shows\s*([^。\n.]+)/i,
      /Analysis of\s*([^。\n.]+)/i,
    ]
    
    for (const pattern of titlePatterns) {
      const match = text.match(pattern)
      if (match) {
        return match[1].trim()
      }
    }
    
    return ''
  }
  
  // 解析图表描述的函数
  const parseChartDescription = (text: string): string => {
    // 匹配类似 "数据洞察：充分反映了某产品在这一领域的卓越表现" 的模式
    const descriptionPatterns = [
      /数据洞察[：:]\s*([^。\n]+)/,
      /Data insights?[：:]\s*([^。\n.]+)/i,
      /Key insights?[：:]\s*([^。\n.]+)/i,
      /Analysis shows?\s*([^。\n.]+)/i,
    ]
    
    for (const pattern of descriptionPatterns) {
      const match = text.match(pattern)
      if (match) {
        return match[1].trim()
      }
    }
    
    return text.split('\n')[0].substring(0, 100) + '...'
  }

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return
    
    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      isUser: true,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setCompiling(false)
    setError(null)
    
    // 添加分析中的消息
    const analyzingMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      isUser: false,
      timestamp: new Date(),
      isAnalyzing: true
    }
    
    setMessages(prev => [...prev, analyzingMessage])
    
    try {
      const response = await fetch(`${config.backendUrl}/agent/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          projectId,
          filters: {
            categories: []
          }
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('No response body')
      }
      
      const aiResponseId = (Date.now() + 1).toString()
      let fullTextContent = '' // 用于存储完整的文本内容
      
      // 添加AI回复消息
      const aiResponse: Message = {
        id: aiResponseId,
        content: '',
        isUser: false,
        timestamp: new Date(),
        contentParts: [],
        isStreaming: true
      }
      
      setMessages(prev => prev.filter(msg => msg.id !== analyzingMessage.id).concat([aiResponse]))
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.substring(6)
            try {
              const sseData = JSON.parse(jsonStr)
              
              if (sseData.status === 'rechart' && sseData.message) {
                setCompiling(true)
                
                // 解析图表标题和描述
                const chartTitle = parseChartTitle(fullTextContent) || 'Dynamic Chart'
                const chartDescription = parseChartDescription(fullTextContent) || 'Chart generated from your query'
                
                const chartId = `chart-${Date.now()}`
                
                // 创建图表数据
                const chartData: ChartData = {
                  id: chartId,
                  code: sseData.message,
                  explanation: chartDescription,
                  insights: 'This visualization represents the key findings from your query',
                  timestamp: Date.now(),
                  type: 'single',
                  title: chartTitle
                }
                
                // 更新全局chart context
                updateChart({
                  chartData: {
                    code: sseData.message,
                    explanation: chartDescription,
                    insights: 'This visualization represents the key findings from your query'
                  },
                  timestamp: Date.now(),
                  type: 'single'
                })
                
                // 添加到动态图表
                onAddDynamicChart(chartData)
                
                // 添加图表内容部分到消息
                setMessages(prev => prev.map(msg => 
                  msg.id === aiResponseId 
                    ? { 
                        ...msg, 
                        contentParts: [
                          ...(msg.contentParts || []),
                          {
                            type: 'chart',
                            content: sseData.message,
                            isComplete: true,
                            index: sseData.script_index || 0
                          }
                        ]
                      }
                    : msg
                ))
                
                setCompiling(false)
                
              } else if (sseData.status === 'streaming' && sseData.message) {
                // 累积全文内容用于解析
                fullTextContent += sseData.message
                
                // 处理流式文本
                setMessages(prev => prev.map(msg => 
                  msg.id === aiResponseId 
                    ? { 
                        ...msg, 
                        content: msg.content + sseData.message,
                        contentParts: updateTextContent(msg.contentParts || [], sseData.message)
                      }
                    : msg
                ))
                
              } else if (sseData.status === 'completed') {
                // 完成流式传输
                setMessages(prev => prev.map(msg => 
                  msg.id === aiResponseId 
                    ? { ...msg, isStreaming: false }
                    : msg
                ))
                break
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError)
            }
          }
        }
      }

    } catch (error) {
      console.error('Error sending message:', error)
      setError(`Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      
      // 移除analyzing消息，添加错误消息
      setMessages(prev => prev.filter(msg => !msg.isAnalyzing))
      const errorMsg: Message = {
        id: (Date.now() + 2).toString(),
        content: "Sorry, I encountered an error while processing your request. Please try again.",
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
      setCompiling(false)
    }
  }

  // 辅助函数：更新文本内容
  const updateTextContent = (contentParts: ContentPart[], newText: string): ContentPart[] => {
    const textParts = contentParts.filter(p => p.type === 'text')
    const otherParts = contentParts.filter(p => p.type !== 'text')
    
    const lastTextPart = textParts[textParts.length - 1]
    
    if (lastTextPart && !lastTextPart.isComplete) {
      // 更新最后一个文本部分
      const updatedTextParts = textParts.map((part, index) => 
        index === textParts.length - 1 
          ? { ...part, content: part.content + newText }
          : part
      )
      return [...updatedTextParts, ...otherParts]
    } else {
      // 创建新的文本部分
      const newTextPart: ContentPart = {
        type: 'text',
        content: newText,
        isComplete: false
      }
      return [...contentParts, newTextPart]
    }
  }

  // 处理表单提交
  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleSendMessage()
  }

  return (
    <div className="min-h-full flex flex-col bg-background">
      {/* Chat Header */}
      <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-2 p-2">
          <MessageSquare className="h-4 w-4" />
          <h2 className="font-medium text-sm">AI Assistant</h2>
          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              {compiling ? 'Compiling chart...' : 'Analyzing...'}
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-3 space-y-4">
          {/* AI Introduction with Chart Cards */}
          <div className="space-y-3">
            <div className="flex items-start gap-2">
              <Avatar className="h-6 w-6 mt-0.5">
                <AvatarFallback className="text-xs">AI</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="max-w-[85%] p-3 rounded-lg bg-gray-100 text-gray-900 mb-3">
                  <div className="text-sm font-semibold whitespace-pre-wrap">
                    I&apos;ve prepared comprehensive data analysis charts for your market research. Each chart provides unique insights:
                  </div>
                </div>
                <ChartCardList 
                  cards={chartCards}
                  activeChartId={activeChartId}
                  onCardClick={onChartSelect}
                />
              </div>
            </div>
          </div>
          
          {/* Additional AI Introduction */}
          <div className="flex items-start gap-2">
            <Avatar className="h-6 w-6 mt-0.5">
            
            </Avatar>
            <div className="max-w-[85%] p-3 rounded-lg bg-gray-100 text-gray-900">
              <div className="text-sm font-semibold whitespace-pre-wrap">
                                 Feel free to explore these insights or ask me any specific questions about your market data. I&apos;m here to help you dive deeper into any aspect of your analysis!
              </div>
            </div>
          </div>
          
          {/* Chat Messages */}
          {messages.slice(1).map((message) => (
            <div key={message.id} className="space-y-1">
              <div className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}>
                {!message.isUser && (
                  <Avatar className="h-6 w-6 mr-2 mt-0.5">
                    <AvatarFallback className="text-xs">AI</AvatarFallback>
                  </Avatar>
                )}
                <div className={`max-w-[85%] p-3 rounded-lg ${
                  message.isUser 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  {message.isAnalyzing ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Analyzing your request...</span>
                    </div>
                  ) : (
                    <div className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {error && (
            <div className="text-red-500 text-sm p-3 bg-red-50 rounded-lg">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 p-3 border-t bg-background sticky bottom-0">
        <form onSubmit={handleFormSubmit} className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about your data..."
            className="flex-1 min-h-[2.5rem] max-h-20 resize-none text-sm"
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
            className="px-3"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
} 