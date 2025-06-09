# Next.js Chart Agent 项目架构设计

## 技术栈选择

### 核心技术栈
```
前端框架: Next.js 14 (App Router) + React 18
样式框架: Tailwind CSS + shadcn/ui
图表库: Recharts
聊天集成: Vercel AI SDK (@ai-sdk/react)
代码编译: @babel/standalone
状态管理: React Context API
部署平台: Vercel
```

### 为什么选择这些技术？

**shadcn/ui vs Headless UI:**
- ✅ **更现代的设计**: 基于Radix UI，设计更精美
- ✅ **更好的定制性**: 可以直接修改组件代码
- ✅ **TypeScript原生支持**: 类型定义完善
- ✅ **与Tailwind完美集成**: 样式一致性更好
- ✅ **更活跃的社区**: 更频繁的更新和维护

**Context API vs 其他状态管理:**
- ✅ **Next.js官方推荐**: 原生React解决方案
- ✅ **零额外依赖**: 不增加bundle大小
- ✅ **简单易用**: 学习成本低
- ✅ **SSR友好**: 与Next.js服务端渲染兼容性好

## 项目结构设计

```
chart-agent/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat/
│   │   │       └── route.ts          # Vercel AI SDK聊天路由
│   │   ├── globals.css               # 全局样式 + Tailwind
│   │   ├── layout.tsx               # 根布局组件
│   │   └── page.tsx                 # 主页面
│   ├── components/
│   │   ├── ui/                      # shadcn/ui组件目录
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   └── ...                  # 其他shadcn组件
│   │   ├── chat/
│   │   │   ├── chat-interface.tsx   # 聊天主界面
│   │   │   ├── message-list.tsx     # 消息列表组件
│   │   │   ├── message-item.tsx     # 单条消息组件
│   │   │   └── chat-input.tsx       # 聊天输入框
│   │   ├── charts/
│   │   │   ├── chart-renderer.tsx   # 图表渲染器
│   │   │   ├── dynamic-compiler.tsx # 动态代码编译器
│   │   │   ├── chart-container.tsx  # 图表容器组件
│   │   │   └── chart-error.tsx      # 图表错误显示
│   │   └── layout/
│   │       ├── main-layout.tsx      # 主布局(左右分栏)
│   │       └── resizable-panel.tsx  # 可调整面板
│   ├── contexts/
│   │   ├── chart-context.tsx        # 图表状态Context
│   │   └── app-context.tsx          # 应用全局状态
│   ├── lib/
│   │   ├── chart-compiler.ts        # 图表编译逻辑
│   │   ├── utils.ts                 # 工具函数
│   │   └── types.ts                 # TypeScript类型定义
│   └── hooks/
│       ├── use-chart.ts             # 图表相关hooks
│       └── use-dynamic-compiler.ts  # 动态编译hooks
├── components.json                   # shadcn/ui配置
├── tailwind.config.js               # Tailwind配置
├── next.config.js                   # Next.js配置
└── package.json
```

## 核心架构设计

### 1. 整体布局架构
```
┌─────────────────────────────────────────────────┐
│                  Header                         │
├────────────────────┬────────────────────────────┤
│                    │                            │
│    Chat Panel      │      Chart Panel           │
│     (50%)          │        (50%)               │
│                    │                            │
│  ┌──────────────┐  │  ┌──────────────────────┐  │
│  │ Message List │  │  │   Chart Display      │  │
│  │              │  │  │                      │  │
│  │              │  │  │                      │  │
│  │              │  │  │                      │  │
│  └──────────────┘  │  └──────────────────────┘  │
│  ┌──────────────┐  │  ┌──────────────────────┐  │
│  │  Chat Input  │  │  │  Data Insights       │  │
│  └──────────────┘  │  └──────────────────────┘  │
│                    │                            │
└────────────────────┴────────────────────────────┘
```

### 2. 数据流架构
```
用户输入消息
    ↓
useChat Hook (Vercel AI SDK)
    ↓
/api/chat 路由
    ↓
LLM处理 + CSV数据分析
    ↓
返回图表代码字符串
    ↓
Chart Context 状态更新
    ↓
Dynamic Compiler 编译JSX
    ↓
Chart Renderer 渲染图表
    ↓
UI 更新显示
```

### 3. Context状态管理设计
```typescript
// Chart Context 结构
interface ChartContextType {
  // 当前图表状态
  currentChart: {
    code: string;
    explanation: string;
    insights: string;
  } | null;
  
  // 图表历史
  chartHistory: ChartData[];
  
  // 编译状态
  isCompiling: boolean;
  compilationError: string | null;
  
  // Actions
  updateChart: (chartData: ChartData) => void;
  addToHistory: (chartData: ChartData) => void;
  setCompiling: (status: boolean) => void;
  setError: (error: string | null) => void;
}

// App Context 结构
interface AppContextType {
  // UI状态
  leftPanelWidth: number;
  rightPanelCollapsed: boolean;
  
  // Actions
  setPanelWidth: (width: number) => void;
  toggleRightPanel: () => void;
}
```

## API路由设计

### 聊天API (`/api/chat/route.ts`)
```typescript
// 使用Vercel AI SDK的streamText
import { openai } from '@ai-sdk/openai';
import { streamText, tool } from 'ai';

POST /api/chat
输入: { messages: Message[] }
输出: AI Stream Response

核心功能:
1. 接收用户消息
2. 分析用户意图
3. 访问CSV数据源
4. 调用LLM生成图表代码
5. 返回流式响应
```

### 图表生成工具定义
```typescript
const generateChartTool = tool({
  description: '根据用户问题生成数据图表',
  parameters: z.object({
    query: z.string(),
    chartType: z.string(),
    data: z.array(z.any())
  }),
  execute: async ({ query, chartType, data }) => {
    // 1. 处理CSV数据
    // 2. 调用LLM生成图表代码
    // 3. 返回完整的React组件代码
    return {
      chartCode: "...",
      explanation: "...",
      insights: "..."
    };
  }
});
```

## 核心组件设计

### 1. Chat Interface 设计
```typescript
// 使用Vercel AI SDK的useChat hook
const ChatInterface = () => {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    onFinish: (message) => {
      // 处理图表生成结果
      if (message.toolInvocations) {
        // 更新图表状态
      }
    }
  });
  
  // 渲染聊天界面
};
```

### 2. Chart Renderer 设计
```typescript
const ChartRenderer = () => {
  const { currentChart } = useChart();
  const [CompiledChart, setCompiledChart] = useState(null);
  
  // 动态编译图表代码
  const compileChart = async (chartCode: string) => {
    // 使用@babel/standalone编译JSX
    // 执行编译后的代码
    // 返回React组件
  };
  
  // 渲染编译后的图表
};
```

### 3. Dynamic Compiler 设计
```typescript
const useDynamicCompiler = () => {
  const compileJSX = useCallback((code: string) => {
    // 1. 使用@babel/standalone编译
    const compiledCode = transform(code, {
      presets: ['react']
    }).code;
    
    // 2. 创建可执行函数
    const createComponent = new Function(
      'React', 'Recharts',
      `${compiledCode}; return DynamicChart;`
    );
    
    // 3. 执行并返回组件
    return createComponent(React, require('recharts'));
  }, []);
  
  return { compileJSX };
};
```

## shadcn/ui 组件使用

### 需要安装的shadcn组件
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add scroll-area
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add badge
```

### 组件使用示例
```typescript
// 聊天输入区域
<Card className="p-4">
  <div className="flex space-x-2">
    <Textarea
      placeholder="Ask about your data..."
      value={input}
      onChange={handleInputChange}
    />
    <Button onClick={handleSubmit} disabled={isLoading}>
      Send
    </Button>
  </div>
</Card>

// 图表展示区域
<Card className="h-full">
  <CardHeader>
    <CardTitle>Data Visualization</CardTitle>
  </CardHeader>
  <CardContent>
    <ChartRenderer />
  </CardContent>
</Card>
```

## 依赖包清单

### package.json 依赖
```json
{
  "dependencies": {
    "next": "^14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    
    // AI 和聊天
    "ai": "^3.0.12",
    "@ai-sdk/openai": "^0.0.9",
    
    // 图表和编译
    "recharts": "^2.8.0",
    "@babel/standalone": "^7.23.6",
    
    // UI 框架
    "tailwindcss": "^3.3.6",
    "@radix-ui/react-slot": "^1.0.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.2.0",
    "lucide-react": "^0.303.0",
    
    // 类型支持
    "typescript": "^5.3.3",
    "@types/node": "^20.10.6",
    "@types/react": "^18.2.46",
    "@types/react-dom": "^18.2.18"
  },
  "devDependencies": {
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.0.4"
  }
}
```

## 开发阶段规划

### Phase 1: 项目基础搭建 (1-2天)
1. ✅ 创建Next.js 14项目
2. ✅ 配置Tailwind CSS
3. ✅ 安装shadcn/ui，配置基础组件
4. ✅ 搭建基本的左右分栏布局

### Phase 2: 聊天功能实现 (2-3天)
1. ✅ 集成Vercel AI SDK
2. ✅ 创建/api/chat路由
3. ✅ 实现基础聊天界面
4. ✅ 添加消息历史管理

### Phase 3: 图表功能实现 (3-4天)
1. ✅ 实现动态代码编译器
2. ✅ 集成Recharts图表渲染
3. ✅ 创建图表容器组件
4. ✅ 实现Context状态管理

### Phase 4: 集成和优化 (2-3天)
1. ✅ 连接聊天和图表功能
2. ✅ 添加错误处理机制
3. ✅ 优化用户界面和体验
4. ✅ 测试和调试

### Phase 5: 部署和配置 (1天)
1. ✅ 配置Vercel部署
2. ✅ 设置环境变量
3. ✅ 性能测试和优化

## 核心功能流程

### 用户交互流程
```
1. 用户在左侧聊天框输入问题
   ↓
2. 点击发送，触发useChat的handleSubmit
   ↓
3. 消息发送到/api/chat路由
   ↓
4. 后端分析问题，访问CSV数据，调用LLM
   ↓
5. LLM返回图表代码字符串
   ↓
6. 前端接收响应，更新Chart Context
   ↓
7. Chart Renderer检测到状态变化
   ↓
8. Dynamic Compiler编译图表代码
   ↓
9. 编译成功后在右侧渲染图表
   ↓
10. 用户看到可视化结果
```

### 关键实现细节
- **流式响应**: 使用Vercel AI SDK的stream功能实现打字效果
- **状态同步**: Context API确保左右面板状态一致
- **错误处理**: React Error Boundary + 编译错误捕获
- **响应式设计**: Tailwind CSS实现移动端适配

这个架构设计如何？有什么需要调整或者补充的地方吗？ 