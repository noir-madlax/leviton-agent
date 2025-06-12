# Chart Agent - AI 数据可视化助手

一个基于 Next.js 和 AI 的智能数据分析和图表生成工具。

## 🚀 功能特性

- **智能对话**: 通过自然语言描述数据分析需求
- **动态图表生成**: AI 自动生成相应的可视化图表
- **实时渲染**: 支持动态编译和渲染 React 图表组件
- **响应式布局**: 左右分栏设计，支持拖拽调整面板大小
- **多种图表类型**: 支持折线图、柱状图、饼图等多种图表类型

## 🛠 技术栈

- **前端框架**: Next.js 14 (App Router)
- **UI 组件**: shadcn/ui + Tailwind CSS
- **图表库**: Recharts
- **状态管理**: React Context API
- **代码编译**: @babel/standalone
- **开发语言**: TypeScript

## 📦 项目结构

```
src/
├── app/                    # Next.js App Router
│   ├── api/chat/          # API 路由
│   ├── globals.css        # 全局样式
│   ├── layout.tsx         # 根布局
│   └── page.tsx           # 主页面
├── components/            # React 组件
│   ├── ui/                # shadcn/ui 基础组件
│   ├── chat/              # 聊天相关组件
│   ├── charts/            # 图表相关组件
│   └── layout/            # 布局组件
├── contexts/              # React Context
│   └── chart-context.tsx  # 图表状态管理
└── lib/                   # 工具函数
    ├── types.ts           # TypeScript 类型定义
    ├── chart-compiler.ts  # 动态图表编译器
    └── utils.ts           # 工具函数
```

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
4. **调整布局**: 拖拽中间分割线调整左右面板大小

### 示例问题

- "显示最近6个月的销售趋势"
- "对比各产品的销售表现"
- "分析用户设备类型分布"
- "展示销售额和利润的变化情况"

## 🔧 核心功能

### 动态图表编译

应用使用 `@babel/standalone` 在浏览器中动态编译 JSX 代码，将 AI 生成的图表代码转换为可执行的 React 组件。

### 安全性验证

内置代码安全性检查，防止执行危险的 JavaScript 代码：
- 禁止使用 `eval`、`Function` 等危险函数
- 限制网络请求和文件系统操作
- 只允许使用 `recharts` 和 `react` 库

### 状态管理

使用 React Context API 管理应用状态：
- 图表数据状态
- 编译状态
- 错误处理

## 🎨 UI 设计

- **现代化界面**: 基于 shadcn/ui 的精美组件
- **响应式设计**: 适配不同屏幕尺寸
- **交互友好**: 直观的用户操作体验
- **实时反馈**: 加载状态和错误提示

## 📝 开发说明

### 添加新的图表类型

1. 在 `src/app/api/chat/route.ts` 中添加新的图表模板
2. 确保图表代码符合安全性要求
3. 测试图表的渲染效果

### 自定义 UI 组件

项目使用 shadcn/ui，可以通过以下命令添加新组件：

```bash
npx shadcn@latest add [component-name]
```

### 部署到 Vercel

项目已配置好 Vercel 部署，只需：

1. 推送代码到 GitHub
2. 在 Vercel 中导入项目
3. 自动部署完成

## 🔮 未来计划

- [ ] 集成真实的 LLM API (OpenAI, Claude 等)
- [ ] 支持 CSV 文件上传和数据分析
- [ ] 添加更多图表类型和自定义选项
- [ ] 实现图表导出功能
- [ ] 添加用户认证和数据持久化
- [ ] 支持多语言界面

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
