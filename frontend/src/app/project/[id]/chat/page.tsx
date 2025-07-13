"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"

import { ChartRenderer } from "@/components/charts/chart-renderer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { DatabaseService } from "@/components/analysis-db/data/database-service"
import { ArrowLeft, MessageSquare, TrendingUp, BarChart3, PieChart, Lightbulb, Send, Loader2, ChevronDown, ChevronUp } from "lucide-react"
import { ChartProvider, useChart } from "@/contexts/chart-context"
import { config } from "@/lib/config"
import { ChartData } from "@/lib/types"
import { usePermissions } from "@/hooks/use-permissions"
import ReactMarkdown from 'react-markdown'
import React from 'react'
import { compileChartCode, validateChartCode } from '@/lib/chart-compiler'

import { CategoryFilterAndProjectScope } from '@/components/analysis-db/shared/category-filter-and-project-scope'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'

// 使用现有的Project接口
interface Project {
  id: string
  project_name: string
  description?: string
  created_at: string
  updated_at: string
  status: string
}

// Agent API 请求接口定义
interface AgentFilters {
  categories: string[]
  brands?: string[]
  dateRange?: {
    start: string
    end: string
  }
  priceRange?: {
    min: number
    max: number
  }
}

interface AgentStreamRequest {
  query: string
  projectId: string
  filters: AgentFilters
}

interface ContentPart {
  type: 'text' | 'insight' | 'chart'
  content: string
  isComplete?: boolean
  index?: number
}

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  isAnalyzing?: boolean
  contentParts?: ContentPart[]  // 支持多种内容类型
  isStreaming?: boolean         // 标识是否正在流式接收
  // 保留原有字段以兼容现有逻辑
  keyInsights?: string[]
  executiveSummary?: string
  hasChart?: boolean
  showExecutiveSummary?: boolean
  showSupportingCharts?: boolean
  showKeyInsights?: boolean
  currentInsightIndex?: number
  initialResponseComplete?: boolean
  chartType?: string
  isHistorical?: boolean
}

interface TypewriterTextProps {
  text: string
  speed?: number
  onComplete?: () => void
  className?: string
}

function TypewriterText({ text, speed = 15, onComplete, className = "" }: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState("")
  const [currentIndex, setCurrentIndex] = useState(0)
  const [hasCompleted, setHasCompleted] = useState(false)

  useEffect(() => {
    setDisplayedText("")
    setCurrentIndex(0)
    setHasCompleted(false)
  }, [text])

  useEffect(() => {
    if (!hasCompleted && currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex])
        setCurrentIndex(prev => prev + 1)
      }, speed)
      return () => clearTimeout(timer)
    } else if (!hasCompleted && currentIndex === text.length && text.length > 0) {
      setHasCompleted(true)
      if (onComplete) {
        onComplete()
      }
    }
  }, [currentIndex, text, speed, onComplete, hasCompleted])

  return <span className={className}>{displayedText}</span>
}

// 内联图表渲染组件
function InlineChartRenderer({ chartCode }: { chartCode: string }) {
  const [CompiledChart, setCompiledChart] = useState<React.ComponentType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    renderChart()
  }, [chartCode])

  const renderChart = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      // 验证代码安全性
      const validation = validateChartCode(chartCode)
      if (!validation.valid) {
        throw new Error(validation.error)
      }

      // 编译代码
      const result = compileChartCode(chartCode)
      if (!result.success) {
        throw new Error(result.error)
      }

      // 设置组件
      setCompiledChart(() => result.component!)
      
    } catch (error) {
      setError(error instanceof Error ? error.message : '未知错误')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
        <span className="ml-2 text-gray-600">生成图表中...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <div className="text-red-500 mb-2">图表生成失败</div>
        <div className="text-sm text-gray-500">{error}</div>
      </div>
    )
  }

  if (!CompiledChart) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">没有可渲染的图表</div>
      </div>
    )
  }

  return (
    <div className="w-full h-full">
      <CompiledChart />
    </div>
  )
}

// Markdown打字机组件
function MarkdownTypewriter({ text, speed = 15, onComplete, className = "" }: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState("")
  const [currentIndex, setCurrentIndex] = useState(0)
  const [hasCompleted, setHasCompleted] = useState(false)

  useEffect(() => {
    setDisplayedText("")
    setCurrentIndex(0)
    setHasCompleted(false)
  }, [text])

  useEffect(() => {
    if (!hasCompleted && currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex])
        setCurrentIndex(prev => prev + 1)
      }, speed)
      return () => clearTimeout(timer)
    } else if (!hasCompleted && currentIndex === text.length && text.length > 0) {
      setHasCompleted(true)
      if (onComplete) {
        onComplete()
      }
    }
  }, [currentIndex, text, speed, onComplete, hasCompleted])

  return (
    <div className={`prose prose-gray max-w-none ${className}`}>
      <ReactMarkdown
        components={{
          // 自定义样式
          h1: ({ children }) => <h1 className="text-xl font-bold text-gray-900 mb-3">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-semibold text-gray-900 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-medium text-gray-900 mb-2">{children}</h3>,
          p: ({ children }) => <p className="text-gray-700 mb-2 leading-relaxed">{children}</p>,
          code: ({ children }) => <code className="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
          pre: ({ children }) => <pre className="bg-gray-100 text-gray-800 p-3 rounded overflow-x-auto text-sm font-mono">{children}</pre>,
          ul: ({ children }) => <ul className="list-disc list-inside text-gray-700 mb-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal list-inside text-gray-700 mb-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="text-gray-700">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
          em: ({ children }) => <em className="italic text-gray-600">{children}</em>,
        }}
      >
        {displayedText}
      </ReactMarkdown>
    </div>
  )
}

interface AnalyzingLoaderProps {
  stage: string
  progress: number
}

function AnalyzingLoader({ stage, progress }: AnalyzingLoaderProps) {
  return (
    <div className="flex items-center space-x-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
      <div className="relative">
        <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
        <div className="absolute inset-0 bg-blue-600 rounded-full opacity-20 animate-pulse" />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-blue-900">{stage}</span>
          <span className="text-xs text-blue-600">{progress}%</span>
        </div>
        <div className="w-full bg-blue-200 rounded-full h-1.5">
          <div 
            className="bg-blue-600 h-1.5 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  )
}

// 新增Insight卡片组件
function InsightCard({ insight }: { insight: string | string[]; index?: number }) {
  // 处理数组情况
  const parseInsights = (content: string | string[]): string[] => {
    if (Array.isArray(content)) {
      return content
    }
    
    try {
      // 尝试解析JSON字符串
      const parsed = JSON.parse(content)
      if (Array.isArray(parsed)) {
        return parsed
      }
    } catch {
      // 如果不是JSON，按换行符分割
      const lines = content.split('\n').filter(line => line.trim())
      if (lines.length > 1) {
        return lines
      }
    }
    
    // 如果都不是，返回单个字符串作为数组
    return [content]
  }

  const insights = parseInsights(insight)

  return (
    <Card className="mt-4 border-l-4 border-l-blue-500">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Lightbulb className="h-5 w-5 text-blue-600" />
          <span>Key Insights</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {insights.map((singleInsight, idx) => (
            <div key={`insight-${idx}`} className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-medium text-blue-600">{idx + 1}</span>
              </div>
              <div className="flex-1">
                <TypewriterText 
                  text={singleInsight}
                  speed={15}
                  className="text-gray-700 leading-relaxed"
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// 内容部分渲染组件
function ContentPartRenderer({ part }: { part: ContentPart }) {
  switch (part.type) {
    case 'text':
      return (
        <div className="p-4 rounded-lg bg-white border border-gray-200">
          <MarkdownTypewriter 
            text={part.content}
            speed={10}
            className="text-gray-900"
          />
        </div>
      )
    case 'insight':
      return <InsightCard insight={part.content} index={part.index} />
    case 'chart':
      return (
        <Card className="mt-6 border-l-4 border-l-purple-500">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-purple-600" />
              <span>Supporting Charts</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative h-[400px] bg-gray-50 rounded-lg p-4">
              <InlineChartRenderer chartCode={part.content} />
            </div>
          </CardContent>
        </Card>
      )
    default:
      return null
  }
}

// 内部组件，使用useChart hook
function ChatPageContent({ projectId }: { projectId: string }) {
  const router = useRouter()
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [showTopics, setShowTopics] = useState(false)
  const [showFilters, setShowFilters] = useState(false) // 默认折叠
  const [currentStage, setCurrentStage] = useState("")
  const [currentProgress, setCurrentProgress] = useState(0)
  const [categoryFilters, setCategoryFilters] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const { permissions } = usePermissions()
  const { updateChart, setCompiling, setError } = useChart()

  // 检测来源
  const [fromHome, setFromHome] = useState(false)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    setFromHome(urlParams.get('from') === 'home')
  }, [])

  // 加载项目信息
  useEffect(() => {
    const loadProject = async () => {
      if (!projectId) return
      
      // 项目加载时参数检查
      console.log('🏠 [CHAT PAGE] Project loading:')
      console.log('  📊 Project ID:', projectId)
      console.log('  🔍 Initial Category Filters:', categoryFilters)
      console.warn('🔥 INITIAL PARAMS CHECK:', {
        projectId: projectId,
        categoryFilters: categoryFilters,
        hasProjectId: !!projectId,
        categoryFiltersCount: categoryFilters.length
      })
      
      try {
        setLoading(true)
        const databaseService = new DatabaseService()
        const projectData = await databaseService.getProject(projectId)
        setProject(projectData)
      } catch (error) {
        console.error('Failed to load project:', error)
      } finally {
        setLoading(false)
      }
    }

    loadProject()
  }, [projectId])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const simulateAnalysis = async (): Promise<void> => {
    const stages = [
      "Analyzing market data...",
      "Processing product segments...",
      "Calculating insights...",
      "Generating visualizations..."
    ]

    for (let i = 0; i < stages.length; i++) {
      setCurrentStage(stages[i])
      
      for (let progress = 0; progress <= 100; progress += 10) {
        setCurrentProgress((i * 100 + progress) / stages.length)
        await new Promise(resolve => setTimeout(resolve, 50))
      }
      
      await new Promise(resolve => setTimeout(resolve, 300))
    }
  }

  // 创建API请求体的辅助函数
  const createAgentRequest = (query: string, projectId: string, categoryFilters: string[]): AgentStreamRequest => {
    return {
      query,
      projectId,
      filters: {
        categories: categoryFilters,
        // 预留扩展空间
        // brands: [],
        // dateRange: null,
        // priceRange: null
      }
    }
  }

  // 真实的API调用函数
  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const originalInput = input
    setInput("")

    // 立即开始loading效果
    setIsLoading(true)
    setCompiling(true)
    setError(null)

    // 添加分析loader消息
    const analyzingMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: "",
      isUser: false,
      timestamp: new Date(),
      isAnalyzing: true
    }
    setMessages(prev => [...prev, analyzingMessage])

    // 开始模拟分析过程
    simulateAnalysis()

    try {
      // 真实的API调用
      const backendUrl = config.backendUrl
      
      // 设置10分钟超时
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000) // 10分钟
      
      // 构建请求体
      const requestBody = createAgentRequest(originalInput, projectId, categoryFilters)
      
      // 重要参数日志 - 确保传递正确
      console.log('=' .repeat(80))
      console.log('🚀 [CHAT API] SENDING REQUEST TO BACKEND')
      console.log('📊 Project ID:', projectId)
      console.log('🔍 Category Filters:', categoryFilters)
      console.log('📝 Category Filters Count:', categoryFilters.length)
      console.log('❓ Query:', originalInput.substring(0, 100) + (originalInput.length > 100 ? '...' : ''))
      console.log('📦 Request Body:', JSON.stringify(requestBody, null, 2))
      console.log('🌐 API Endpoint:', `${backendUrl}/agent/stream`)
      console.log('=' .repeat(80))
      
      // 额外的确认机制 - 用警告形式确保可见
      console.warn('🔥 CRITICAL PARAMS CHECK:', {
        hasProjectId: !!projectId,
        projectIdValue: projectId,
        hasCategoryFilters: categoryFilters.length > 0,
        categoryFiltersValue: categoryFilters,
        requestBodyValid: !!requestBody.query && !!requestBody.projectId
      })
      
      const response = await fetch(`${backendUrl}/agent/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      const aiResponseId = (Date.now() + 2).toString()
      
      // 创建AI回复消息，支持动态内容更新
      const aiResponse: Message = {
        id: aiResponseId,
        content: "",
        isUser: false,
        timestamp: new Date(),
        contentParts: [],
        isStreaming: true
      }

      // 立即添加AI回复消息到消息列表
      setMessages(prev => prev.filter(msg => msg.id !== analyzingMessage.id).concat([aiResponse]))

      while (true) {
        const { done, value } = await reader!.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.substring(6)
            try {
              const sseData = JSON.parse(jsonStr)
              
              if (sseData.status === 'rechart' && sseData.message) {
                // 处理图表数据 - 更新全局chart context用于主要图表显示
                const chartData: ChartData = {
                  chartData: {
                    code: sseData.message,
                    explanation: 'Interactive chart generated from your data analysis',
                    insights: 'This visualization represents the key findings from your query'
                  },
                  timestamp: Date.now(),
                  type: 'single'
                }
                updateChart(chartData)
                
                // 添加图表内容部分
                setMessages(prev => {
                  const updated = prev.map(msg => {
                    if (msg.id === aiResponseId) {
                      const newPart: ContentPart = {
                        type: 'chart',
                        content: sseData.message,
                        isComplete: true,
                        index: sseData.script_index || 0
                      }
                      return {
                        ...msg,
                        contentParts: [...(msg.contentParts || []), newPart],
                        hasChart: true
                      }
                    }
                    return msg
                  })
                  return updated
                })
                
              } else if (sseData.status === 'insight' && sseData.message) {
                // 新增：处理insight数据
                setMessages(prev => {
                  const updated = prev.map(msg => {
                    if (msg.id === aiResponseId) {
                      const newPart: ContentPart = {
                        type: 'insight',
                        content: sseData.message,
                        isComplete: true,
                        index: sseData.script_index || 0
                      }
                      return {
                        ...msg,
                        contentParts: [...(msg.contentParts || []), newPart]
                      }
                    }
                    return msg
                  })
                  return updated
                })
                
              } else if (sseData.status === 'streaming' && sseData.message) {
                // 处理流式文本，实时更新
                setMessages(prev => {
                  const updated = prev.map(msg => {
                    if (msg.id === aiResponseId) {
                      // 查找或创建文本内容部分
                      const existingTextParts = msg.contentParts?.filter(p => p.type === 'text') || []
                      const lastTextPart = existingTextParts[existingTextParts.length - 1]
                      
                      if (lastTextPart && !lastTextPart.isComplete) {
                        // 更新现有的文本部分
                        const updatedParts = msg.contentParts?.map(part => {
                          if (part === lastTextPart) {
                            return {
                              ...part,
                              content: part.content + sseData.message
                            }
                          }
                          return part
                        }) || []
                        
                        return {
                          ...msg,
                          contentParts: updatedParts,
                          content: msg.content + sseData.message
                        }
                      } else {
                        // 创建新的文本部分
                        const newPart: ContentPart = {
                          type: 'text',
                          content: sseData.message,
                          isComplete: false,
                          index: sseData.chunk_index || 0
                        }
                        return {
                          ...msg,
                          contentParts: [...(msg.contentParts || []), newPart],
                          content: msg.content + sseData.message
                        }
                      }
                    }
                    return msg
                  })
                  return updated
                })
                
              } else if (sseData.status === 'completed') {
                // 处理完成，标记所有文本部分为完成
                setMessages(prev => {
                  const updated = prev.map(msg => {
                    if (msg.id === aiResponseId) {
                      const completedParts = msg.contentParts?.map(part => ({
                        ...part,
                        isComplete: true
                      })) || []
                      
                      return {
                        ...msg,
                        contentParts: completedParts,
                        isStreaming: false
                      }
                    }
                    return msg
                  })
                  return updated
                })
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
      
      // 检查是否为超时错误
      const errorMessage = error instanceof Error && error.name === 'AbortError' 
        ? "Request timed out after 10 minutes. Please try again."
        : `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      
      setError(errorMessage)
      
      // 移除analyzing消息，添加错误消息
      setMessages(prev => prev.filter(msg => !msg.isAnalyzing))
      const errorMsg: Message = {
        id: (Date.now() + 2).toString(),
        content: "Sorry, I encountered an error while processing your request. Please try again.",
        isUser: false,
        timestamp: new Date(),
        hasChart: false,
        showKeyInsights: false
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
      setCompiling(false)
      setCurrentStage("")
      setCurrentProgress(0)
    }
  }



  const examplePrompts = [
    {
      icon: BarChart3,
      title: "Top Selling Product Segments",
      description: "Identify which product segments lead in sales",
      prompt: "What are the top selling product segments?"
    },
    {
      icon: PieChart,
      title: "Brand Market Share",
      description: "Show market share for each brand",
      prompt: "What is the market share by brand?"
    },
    {
      icon: TrendingUp,
      title: "Customer Pain Points Trend",
      description: "Analyze trend of customer pain points",
      prompt: "How have customer pain points trended over time?"
    },
    {
      icon: Lightbulb,
      title: "Opportunities Missed by Competitors",
      description: "Find use cases competitors fail to address",
      prompt: "Which use cases are underserved by competitors?"
    }
  ]

  const handleExampleClick = (prompt: string) => {
    if (isLoading) return
    setInput(prompt)
    setTimeout(() => {
      handleSendMessage()
    }, 100)
  }

  const handleCategoryFiltersChange = (filters: { categories: string[]; asins: string[] }) => {
    setCategoryFilters(filters.categories)
    
    // 增强的过滤器变更日志
    console.log('🔍 [CHAT] Category filters updated:')
    console.log('  📝 Categories:', filters.categories)
    console.log('  🔢 Count:', filters.categories.length)
    console.log('  📊 Project ID:', projectId)
    console.log('  ⏰ Timestamp:', new Date().toISOString())
    
    // 警告形式确保可见
    console.warn('🔥 FILTER UPDATE:', {
      newCategories: filters.categories,
      oldCategories: categoryFilters,
      projectId: projectId
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading project...</p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-medium text-gray-900 mb-2">Project not found</h2>
          <p className="text-gray-600 mb-4">The project you're looking for doesn't exist.</p>
          <Button onClick={() => router.push("/")}>Back to Home</Button>
        </div>
      </div>
    )
  }

  return (
    <ChartProvider>
      <div className="flex h-screen bg-gray-50">
        {/* Topics Sidebar */}
        <div className={`${showTopics ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden bg-white border-r border-gray-200`}>
          <div className="p-6 space-y-6">
            {/* Topics Section */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Topics</h2>
              <div className="space-y-3">
                {["Market Analysis", "Competitive Intelligence", "Customer Insights", "Price Optimization"].map((topic) => (
                  <div key={topic} className="p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer">
                    <div className="font-medium text-sm">{topic}</div>
                    <div className="text-xs text-gray-500 mt-1">Recent discussions</div>
                  </div>
                ))}
              </div>
            </div>



            {/* Active Filters Display */}
            {categoryFilters.length > 0 && (
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Active Filters</h3>
                <div className="space-y-1">
                  {categoryFilters.map((filter) => (
                    <div key={filter} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                      {filter}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push(fromHome ? '/' : (projectId ? `/project/${projectId}` : '/'))}
                  className="text-gray-600"
                >
                  <ArrowLeft className="h-4 w-4" />
                  {fromHome ? 'Back to Home' : 'Back to Dashboard'}
                </Button>
                <Separator orientation="vertical" className="h-4" />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTopics(!showTopics)}
                  className="text-gray-600"
                >
                  <MessageSquare className="h-4 w-4" />
                  Topics
                </Button>
                <Separator orientation="vertical" className="h-4" />
                <div>
                  <h1 className="text-lg font-semibold">{project.project_name}</h1>
                  <p className="text-sm text-gray-600">Smart Home &gt; Dimmer &amp; Light Switches</p>
                </div>
              </div>
            </div>
          </div>

          {/* Filters Section - Collapsible */}
          <div className="bg-white border-b border-gray-200">
            <Collapsible open={showFilters} onOpenChange={setShowFilters}>
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  className="w-full justify-between px-6 py-4 hover:bg-gray-50"
                >
                  <span className="text-sm font-medium">Data Filters & Scope</span>
                  {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="px-6 py-4 border-t border-gray-100">
                <div className="max-w-6xl mx-auto">
                  {/* Category Filter & Project Scope */}
                  <CategoryFilterAndProjectScope 
                    projectId={projectId} 
                    onFiltersChange={handleCategoryFiltersChange}
                    initialFilters={{ categories: categoryFilters, asins: [] }}
                  />
                </div>
              </CollapsibleContent>
            </Collapsible>
          </div>

          {/* Messages Area */}
          <ScrollArea className="flex-1 p-6">
            <div className="max-w-6xl mx-auto space-y-6">
              {messages.length === 0 ? (
                /* Empty State */
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MessageSquare className="h-8 w-8 text-blue-600" />
                  </div>
                  <h2 className="text-xl font-semibold mb-2">Welcome to Xenith</h2>
                  
                  <div className="w-full max-w-4xl mx-auto">
                    {/* Chat input */}
                    <div className="flex space-x-3 max-w-2xl mx-auto">
                      <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault()
                            handleSendMessage()
                          }
                        }}
                        placeholder="How can I help you?"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={isLoading}
                      />
                      <Button
                        onClick={handleSendMessage}
                        disabled={!input.trim() || isLoading || !permissions?.can_send_chat}
                        className="px-4 py-2"
                        title={!permissions?.can_send_chat ? "Currently in internal testing" : ""}
                      >
                        {isLoading ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                      </Button>
                    </div>

                    {/* FAQ list with 2-column grid layout */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-6">
                      {examplePrompts.map((example, index) => (
                        <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => handleExampleClick(example.prompt)}>
                          <CardHeader className="pb-2 pt-3">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                <example.icon className="h-4 w-4 text-blue-600" />
                              </div>
                              <div className="min-w-0 flex-1">
                                <CardTitle className="text-sm text-left leading-tight">{example.title}</CardTitle>
                                <CardDescription className="text-xs text-left mt-1 leading-tight">{example.description}</CardDescription>
                              </div>
                            </div>
                          </CardHeader>
                        </Card>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                /* Messages */
                messages.map((message) => (
                  <div key={message.id} className="w-full">
                    {message.isUser ? (
                      /* User Message */
                      <div className="flex justify-end">
                        <div className="flex flex-row-reverse space-x-3 space-x-reverse max-w-2xl">
                          <Avatar className="w-8 h-8 flex-shrink-0">
                            <AvatarFallback className="bg-blue-600 text-white">JD</AvatarFallback>
                          </Avatar>
                          <div className="flex-1">
                            <div className="bg-blue-600 text-white rounded-lg px-4 py-2">
                              <span className="text-white">{message.content}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* AI Message */
                      <div className="w-full">
                        <div className="flex space-x-3">
                          <Avatar className="w-8 h-8 flex-shrink-0">
                            <AvatarFallback className="bg-gray-600 text-white">X</AvatarFallback>
                          </Avatar>
                          <div className="flex-1 pr-12">
                            {message.isAnalyzing ? (
                              <AnalyzingLoader stage={currentStage} progress={currentProgress} />
                            ) : (
                              <>
                                {/* 使用新的内容部分渲染器 */}
                                {message.contentParts && message.contentParts.length > 0 ? (
                                  <div className="space-y-4">
                                    {message.contentParts.map((part, index) => (
                                      <ContentPartRenderer 
                                        key={`${message.id}-part-${index}`} 
                                        part={part}
                                      />
                                    ))}
                                  </div>
                                ) : message.content ? (
                                  /* 兼容原有的content字段 */
                                  <div className="p-4 rounded-lg bg-white border border-gray-200">
                                    <TypewriterText 
                                      text={message.content}
                                      speed={10}
                                      className="text-gray-900"
                                    />
                                  </div>
                                ) : null}

                                {/* Key Insights - 保留兼容性 */}
                                {message.showKeyInsights && message.keyInsights && (
                                  <Card className="mt-6 border-l-4 border-l-blue-500">
                                    <CardHeader>
                                      <CardTitle className="flex items-center space-x-2">
                                        <Lightbulb className="h-5 w-5 text-blue-600" />
                                        <span>Key Insights</span>
                                      </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                      <div className="space-y-3">
                                        {message.keyInsights.map((insight, index) => (
                                          <div key={`insight-${message.id}-${index}`} className="flex items-start space-x-3">
                                            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                              <span className="text-xs font-medium text-blue-600">{index + 1}</span>
                                            </div>
                                            <span className="text-gray-700 leading-relaxed">{insight}</span>
                                          </div>
                                        ))}
                                      </div>
                                    </CardContent>
                                  </Card>
                                )}

                                {/* Supporting Charts - 保留兼容性 */}
                                {message.hasChart && !message.contentParts?.some(p => p.type === 'chart') && (
                                  <Card className="mt-6 border-l-4 border-l-purple-500">
                                    <CardHeader>
                                      <CardTitle className="flex items-center space-x-2">
                                        <BarChart3 className="h-5 w-5 text-purple-600" />
                                        <span>Supporting Charts</span>
                                      </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                      <div className="relative h-[400px]">
                                        <ChartRenderer />
                                      </div>
                                    </CardContent>
                                  </Card>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          {messages.length > 0 && (
            <div className="border-t border-gray-200 bg-white p-4">
              <div className="max-w-6xl mx-auto">
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        handleSendMessage()
                      }
                    }}
                    placeholder="How can I help you?"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isLoading}
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!input.trim() || isLoading || !permissions?.can_send_chat}
                    className="px-4 py-2"
                    title={!permissions?.can_send_chat ? "Currently in internal testing" : ""}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </ChartProvider>
  )
}

// 主要的ChatPage组件，处理参数解析
export default function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const [projectId, setProjectId] = useState<string | null>(null)

  // 解析异步params
  useEffect(() => {
    const resolveParams = async () => {
      const resolvedParams = await params
      setProjectId(resolvedParams.id)
    }
    resolveParams()
  }, [params])

  if (!projectId) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <ChartProvider>
      <ChatPageContent projectId={projectId} />
    </ChartProvider>
  )
}