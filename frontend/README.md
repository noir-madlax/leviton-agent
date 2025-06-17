# Chart Agent - 产品市场分析Agent第七步：动态图表渲染

> 这是产品市场分析Agent 7步骤流程中的第七步：**动态渲染** - 在Chat界面实时展示分析图表

## 📋 项目概述

### 在整体流程中的作用

本项目是产品市场分析Agent的核心前端组件，负责将AI生成的图表代码动态编译并渲染为可视化图表。

**完整7步骤流程**：
1. 数据获取 - 通过爬虫API获取Amazon产品和评论数据
2. 业务建模 - 将原始数据转换为具有业务意义的结构化数据  
3. 数据存储 - 存储到数据库供Agent访问
4. 需求定义 - 定义市场分析的核心图表和维度需求
5. 数据验证 - Agent确认现有数据能否满足分析需求
6. 图表实现 - Agent生成React图表代码
7. **动态渲染** - 在Chat界面实时展示分析图表 ← **本项目**

### 核心价值

- **无需预定义图表类型** - 完全动态，支持任何复杂的自定义图表
- **智能对话驱动** - 通过自然语言生成相应的可视化分析
- **实时编译渲染** - 将AI生成的React组件代码动态编译执行
- **分析洞察展示** - 不仅显示图表，还提供数据洞察和解释

## 🚀 功能特性

- **智能对话**: 通过自然语言描述数据分析需求
- **动态图表生成**: AI 自动生成相应的可视化图表代码
- **实时编译渲染**: 支持动态编译和渲染 React 图表组件
- **安全代码执行**: 内置安全验证，防止恶意代码执行
- **响应式布局**: 左右分栏设计，支持拖拽调整面板大小
- **多种图表类型**: 支持折线图、柱状图、饼图、散点图等
- **数据洞察展示**: 自动生成数据分析结论和建议

## 🛠 技术架构

### 技术栈选择

```
前端框架: Next.js 14 (App Router) + React 18
样式框架: Tailwind CSS + shadcn/ui  
图表库: Recharts
聊天集成: Vercel AI SDK (@ai-sdk/react)
代码编译: @babel/standalone
状态管理: React Context API
部署平台: Vercel
```

### 核心架构方案

**方案**: React组件代码动态生成
```
用户提问 → LLM生成图表代码 → 前端编译执行 → 动态渲染图表
```

### 整体布局架构
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

## 📦 项目结构

```
src/
├── app/                    # Next.js App Router
│   ├── api/
│   │   └── chat/
│   │       └── route.ts    # Vercel AI SDK聊天路由
│   ├── globals.css         # 全局样式 + Tailwind
│   ├── layout.tsx          # 根布局
│   └── page.tsx            # 主页面
├── components/             # React 组件
│   ├── ui/                 # shadcn/ui基础组件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ...             # 其他shadcn组件
│   ├── chat/               # 聊天相关组件
│   │   ├── chat-interface.tsx   # 聊天主界面
│   │   ├── message-list.tsx     # 消息列表组件
│   │   ├── message-item.tsx     # 单条消息组件
│   │   └── chat-input.tsx       # 聊天输入框
│   ├── charts/             # 图表相关组件
│   │   ├── chart-renderer.tsx   # 图表渲染器
│   │   ├── dynamic-compiler.tsx # 动态代码编译器
│   │   ├── chart-container.tsx  # 图表容器组件
│   │   └── chart-error.tsx      # 图表错误显示
│   └── layout/             # 布局组件
│       ├── main-layout.tsx      # 主布局(左右分栏)
│       └── resizable-panel.tsx  # 可调整面板
├── contexts/               # React Context
│   ├── chart-context.tsx   # 图表状态Context
│   └── app-context.tsx     # 应用全局状态
├── lib/                    # 工具函数
│   ├── chart-compiler.ts   # 图表编译逻辑  
│   ├── utils.ts            # 工具函数
│   └── types.ts            # TypeScript类型定义
└── hooks/                  # 自定义Hooks
    ├── use-chart.ts        # 图表相关hooks
    └── use-dynamic-compiler.ts  # 动态编译hooks
```

## 🔧 核心技术实现

### 1. 动态代码编译器

使用 `@babel/standalone` 在浏览器中动态编译 JSX 代码：

```javascript
// 核心编译流程
const codeString = "LLM生成的React组件代码";

// 1. JSX编译
const compiledCode = transform(codeString, {
  presets: ['react']
}).code;

// 2. 代码执行
const createComponent = new Function(
  'React', 'Recharts',
  `${compiledCode}; return DynamicChart;`
);

// 3. 获取组件
const Component = createComponent(React, require('recharts'));

// 4. 渲染组件
<Component />
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

### 3. 状态管理设计

使用 React Context API 管理应用状态：

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
```

### 4. 安全性验证

内置代码安全性检查，防止执行危险的 JavaScript 代码：
- 禁止使用 `eval`、`Function` 等危险函数
- 限制网络请求和文件系统操作
- 只允许使用 `recharts` 和 `react` 库
- 代码沙箱执行环境

## 🚀 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看应用。

### 构建生产版本

```bash
npm run build
npm start
```

## 💡 使用方法

1. **启动应用**: 在浏览器中打开应用
2. **输入问题**: 在左侧聊天区域输入数据分析需求
3. **查看图表**: AI 会在右侧生成相应的可视化图表
4. **查看洞察**: 图表下方显示数据分析结论和建议
5. **调整布局**: 拖拽中间分割线调整左右面板大小

### 支持的分析类型

#### 市场格局分析
- "显示各品牌的市场份额分布"
- "对比头部产品的销量排名" 
- "分析产品市场占有率变化"

#### 产品结构分析  
- "展示不同价格区间的产品分布"
- "分析产品细分类目构成"
- "对比各品牌的产品线矩阵"

#### 用户行为分析
- "分析用户评分趋势变化"
- "展示用户主要痛点词云"
- "统计用户偏好和应用场景"

## 📋 依赖包清单

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
  }
}
```

## 🎨 UI 设计

- **现代化界面**: 基于 shadcn/ui 的精美组件
- **响应式设计**: 适配不同屏幕尺寸  
- **交互友好**: 直观的用户操作体验
- **实时反馈**: 加载状态和错误提示
- **分栏布局**: 聊天和图表并列显示

## 🔮 扩展计划

- [ ] 集成真实的 LLM API (OpenAI, Claude 等)
- [ ] 连接Supabase数据库，访问产品分析数据
- [ ] 支持更多图表类型和自定义选项
- [ ] 实现图表导出和分享功能
- [ ] 添加图表交互和钻取功能
- [ ] 支持多维度数据分析组合

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
