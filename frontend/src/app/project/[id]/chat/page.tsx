"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { ChatInterface } from "@/components/chat/chat-interface"
import { ChartRenderer } from "@/components/charts/chart-renderer"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { DatabaseService } from "@/components/analysis-db/data/database-service"
import { ArrowLeft, MessageSquare, TrendingUp, BarChart3, PieChart, Lightbulb, Send, Loader2 } from "lucide-react"
import { ChartProvider, useChart } from "@/contexts/chart-context"
import { config } from "@/lib/config"
import { ChartData, SingleChart } from "@/lib/types"

// 使用现有的Project接口
interface Project {
  id: string
  project_name: string
  description?: string
  created_at: string
  updated_at: string
  status: string
}

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  isAnalyzing?: boolean
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

// 内部组件，使用useChart hook
function ChatPageContent({ projectId }: { projectId: string }) {
  const router = useRouter()
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [showTopics, setShowTopics] = useState(false)
  const [currentStage, setCurrentStage] = useState("")
  const [currentProgress, setCurrentProgress] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
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
      const response = await fetch(`${backendUrl}/agent-stream?query=${encodeURIComponent(originalInput)}`, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ""
      let aiResponseId = (Date.now() + 2).toString()

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
                // 处理图表数据
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
              } else if (sseData.status === 'streaming' && sseData.message) {
                // 累积完整响应
                fullResponse += sseData.message
              } else if (sseData.status === 'completed') {
                // 处理完成，解析完整响应
                const parsedResponse = parseFullResponse(fullResponse)
                
                // 如果有RechartScript，处理图表
                if (parsedResponse.rechartScript) {
                  const chartData: ChartData = {
                    chartData: {
                      code: parsedResponse.rechartScript,
                      explanation: 'Interactive chart generated from your data analysis',
                      insights: 'This visualization represents the key findings from your query'
                    },
                    timestamp: Date.now(),
                    type: 'single'
                  }
                  updateChart(chartData)
                }
                
                // 移除analyzing消息，创建最终回复
                setMessages(prev => {
                  const filtered = prev.filter(msg => msg.id !== analyzingMessage.id)
                  
                  const finalResponse: Message = {
                    id: aiResponseId,
                    content: parsedResponse.summary || "Here's the comprehensive analysis of your product segment data.",
                    isUser: false,
                    timestamp: new Date(),
                    hasChart: !!parsedResponse.rechartScript,
                    showKeyInsights: parsedResponse.insights.length > 0,
                    keyInsights: parsedResponse.insights
                  }
                  return [...filtered, finalResponse]
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
      setError(`Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      
      // 移除analyzing消息，添加错误消息
      setMessages(prev => prev.filter(msg => !msg.isAnalyzing))
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        content: "Sorry, I encountered an error while processing your request. Please try again.",
        isUser: false,
        timestamp: new Date(),
        hasChart: false,
        showKeyInsights: false
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setCompiling(false)
      setCurrentStage("")
      setCurrentProgress(0)
    }
  }

  // 解析完整响应的函数
  const parseFullResponse = (response: string) => {
    const result = {
      summary: "",
      rechartScript: "",
      insights: [] as string[]
    }

    // 提取图表概括部分
    const summaryMatch = response.match(/## 图表概括\s*([\s\S]*?)(?=\[RechartScript\]|## 数据洞察|$)/i)
    if (summaryMatch) {
      result.summary = summaryMatch[1].trim()
    }

    // 提取RechartScript部分
    const rechartMatch = response.match(/\[RechartScript\]\s*([\s\S]*?)(?=\[\/RechartScript\]|## 数据洞察|$)/i)
    if (rechartMatch) {
      result.rechartScript = rechartMatch[1].trim()
    }

    // 提取数据洞察部分并转换为英文
    const insightsMatch = response.match(/## 数据洞察\s*([\s\S]*?)$/i)
    if (insightsMatch) {
      const insightsText = insightsMatch[1].trim()
      result.insights = extractAndTranslateInsights(insightsText)
    }

    return result
  }

  // 提取并翻译洞察的函数
  const extractAndTranslateInsights = (chineseInsights: string): string[] => {
    const insights: string[] = []
    
    // 智能家居/智能产品相关洞察
    if (chineseInsights.includes('智能调光开关') || chineseInsights.includes('Smart Hub-Dependent')) {
      insights.push("Smart Hub-Dependent Dimmer Switches lead the market with highest revenue performance.")
    }
    
    if (chineseInsights.includes('智能Wi-Fi') || chineseInsights.includes('Smart Wi-Fi')) {
      insights.push("Smart Wi-Fi enabled products show strong consumer adoption and revenue growth.")
    }
    
    if (chineseInsights.includes('智能家居') || chineseInsights.includes('智能产品')) {
      insights.push("The market shows clear preference for connected and intelligent home automation solutions.")
    }
    
    // 传统产品相关洞察
    if (chineseInsights.includes('传统产品') || chineseInsights.includes('Single Pole')) {
      insights.push("Traditional switches maintain significant market share through volume sales strategy.")
    }
    
    // 市场集中度相关洞察
    if (chineseInsights.includes('市场集中度') || chineseInsights.includes('前三名')) {
      insights.push("Top three product segments dominate market revenue with high concentration.")
    }
    
    // 价格策略相关洞察
    if (chineseInsights.includes('量价平衡') || chineseInsights.includes('规模效应')) {
      insights.push("Volume-based pricing strategy proves effective for traditional product categories.")
    }
    
    // 创新相关洞察
    if (chineseInsights.includes('产品创新') || chineseInsights.includes('技术发展')) {
      insights.push("Product innovation and smart technology integration are key revenue drivers.")
    }
    
    // 如果没有提取到任何洞察，使用默认洞察
    if (insights.length === 0) {
      insights.push(
        "Analysis reveals important trends in product segment performance and market positioning.",
        "Smart product segments demonstrate significantly higher revenue per unit.",
        "Market data indicates strong demand for intelligent home automation solutions.",
        "Strategic opportunities exist in both premium smart products and volume-based traditional products."
      )
    }
    
    return insights.slice(0, 4) // 限制最多4个洞察
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
          <div className="p-6">
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
                        disabled={!input.trim() || isLoading}
                        className="px-4 py-2"
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
                            ) : message.content ? (
                              <div className="p-4 rounded-lg bg-white border border-gray-200">
                                <TypewriterText 
                                  text={message.content}
                                  speed={10}
                                  className="text-gray-900"
                                />
                              </div>
                            ) : null}

                            {/* Key Insights */}
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

                            {/* Supporting Charts */}
                            {message.hasChart && (
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
                    disabled={!input.trim() || isLoading}
                    className="px-4 py-2"
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