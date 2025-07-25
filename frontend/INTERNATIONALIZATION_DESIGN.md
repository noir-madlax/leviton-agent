# 前端国际化设计方案 - 最小化变更版本

## 📋 项目概述

本文档描述了为 Xenith 前端项目实施国际化（i18n）的**最小化变更**方案，支持中文（zh-CN）和英文（en-US）两种语言。

## 🎯 设计目标

- **最小化变更**：在现有代码基础上添加国际化，避免大规模重构
- **零路由改动**：保持现有路由结构不变
- **渐进式迁移**：可以逐步迁移现有组件，不影响现有功能
- **浏览器语言检测**：自动检测用户浏览器语言，兜底英文
- **用户体验**：提供流畅的多语言切换体验

## 🛠 技术选型对比

### 方案A：react-i18next（推荐 - 最小化变更）

- **优势**：
  - 零路由改动
  - 客户端渲染友好
  - 支持浏览器语言检测
  - 简单的Hook API
  - 修改量极小（每个组件只需1-2行改动）

### 方案B：next-intl（功能更强但改动较大）

- **优势**：
  - 原生支持 App Router
  - 类型安全的翻译API
  - 服务端渲染（SSR）支持
  - 自动代码分割
- **缺点**：
  - 需要重构所有路由结构
  - 需要迁移所有页面文件
  - 改动量巨大

## 💡 推荐方案：react-i18next

### 依赖包

```json
{
  "react-i18next": "^13.5.0",
  "i18next": "^23.7.0",
  "i18next-browser-languagedetector": "^7.2.0"
}
```

## 📁 文件结构组织 - 最小化变更

```
frontend/
├── src/
│   ├── app/                       # 保持现有路由结构，无需修改
│   │   ├── layout.tsx             # 🔄 需要添加 I18nProvider
│   │   ├── page.tsx               # 🔄 需要替换硬编码文本
│   │   ├── auth/                  # 🔄 需要替换硬编码文本
│   │   ├── chat/                  # 🔄 需要替换硬编码文本
│   │   ├── project/               # 🔄 需要替换硬编码文本
│   │   └── ...                    # 🔄 其他页面按需迁移
│   ├── i18n/                      # ✅ 新增目录
│   │   ├── config.ts              # ✅ 新增：i18next配置
│   │   ├── locales/               # ✅ 新增：翻译文件
│   │   │   ├── en.json            # ✅ 新增：英文翻译
│   │   │   └── zh.json            # ✅ 新增：中文翻译
│   │   ├── hooks.ts               # ✅ 新增：翻译Hooks
│   │   └── types.ts               # ✅ 新增：类型定义
│   └── components/
│       ├── ui/
│       │   └── language-switcher.tsx # ✅ 新增：语言切换组件
│       └── ...                    # 现有组件保持不变
```

## 🌐 路由策略 - 保持现有结构

### 无需路由重构

```
https://example.com/           # 现有首页，根据浏览器语言显示
https://example.com/auth/      # 现有认证页，根据用户选择显示
https://example.com/project/   # 现有项目页，根据用户选择显示
```

### 语言切换策略

- 使用 localStorage 保存用户语言选择（不需要实现这个）
- 自动检测浏览器语言（Accept-Language）
- 兜底策略：任何非中文情况都显示英文
- 用户手动切换后记住偏好（不需要手动切换功能）

## 📝 翻译文件结构

### 模块化组织

```json
// messages/en.json
{
  "common": {
    "loading": "Loading...",
    "error": "Error",
    "save": "Save",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "delete": "Delete",
    "edit": "Edit",
    "search": "Search",
    "filter": "Filter",
    "export": "Export",
    "import": "Import"
  },
  "auth": {
    "login": "Login",
    "register": "Register",
    "email": "Email",
    "password": "Password",
    "confirmPassword": "Confirm Password",
    "forgotPassword": "Forgot Password?",
    "resetPassword": "Reset Password",
    "loginSuccess": "Login successful",
    "loginError": "Login failed",
    "signInWithGoogle": "Sign in with Google"
  },
  "navigation": {
    "home": "Home",
    "projects": "Projects",
    "chat": "Chat",
    "importData": "Import Data",
    "settings": "Settings",
    "profile": "Profile",
    "logout": "Logout"
  },
  "project": {
    "createProject": "Create Project",
    "projectName": "Project Name",
    "description": "Description",
    "categories": "Categories",
    "brands": "Brands",
    "segments": "Segments",
    "totalProducts": "Total Products",
    "totalBrands": "Total Brands",
    "totalReviews": "Total Reviews",
    "analysisComplete": "Analysis Complete",
    "processingData": "Processing Data...",
    "estimatedTime": "Estimated Time"
  },
  "dashboard": {
    "marketAnalysis": "Market Analysis",
    "brandAnalysis": "Brand Analysis",
    "pricingAnalysis": "Pricing Analysis",
    "reviewInsights": "Review Insights",
    "competitorAnalysis": "Competitor Analysis",
    "salesTrend": "Sales Trend",
    "customerSatisfaction": "Customer Satisfaction"
  },
  "charts": {
    "revenue": "Revenue",
    "volume": "Volume",
    "noDataAvailable": "No data available",
    "loadingChart": "Loading chart data...",
    "chartError": "Error loading chart",
    "clickToExpand": "Click to expand",
    "downloadChart": "Download Chart",
    "shareChart": "Share Chart"
  },
  "filters": {
    "applyFilters": "Apply Filters",
    "resetFilters": "Reset Filters",
    "categoryFilter": "Category Filter",
    "brandFilter": "Brand Filter",
    "priceRange": "Price Range",
    "dateRange": "Date Range",
    "showMore": "Show More",
    "showLess": "Show Less"
  },
  "errors": {
    "pageNotFound": "Page Not Found",
    "serverError": "Server Error",
    "networkError": "Network Error",
    "permissionDenied": "Permission Denied",
    "sessionExpired": "Session Expired",
    "invalidInput": "Invalid Input",
    "fileUploadError": "File Upload Error"
  },
  "meta": {
    "title": "Xenith - AI Agent for marketing data analysis",
    "description": "AI-powered data analysis and chart generation tool for marketing",
    "keywords": "AI, data analysis, marketing, charts, insights"
  }
}
```

```json
// messages/zh.json
{
  "common": {
    "loading": "加载中...",
    "error": "错误",
    "save": "保存",
    "cancel": "取消",
    "confirm": "确认",
    "delete": "删除",
    "edit": "编辑",
    "search": "搜索",
    "filter": "筛选",
    "export": "导出",
    "import": "导入"
  },
  "auth": {
    "login": "登录",
    "register": "注册",
    "email": "邮箱",
    "password": "密码",
    "confirmPassword": "确认密码",
    "forgotPassword": "忘记密码？",
    "resetPassword": "重置密码",
    "loginSuccess": "登录成功",
    "loginError": "登录失败",
    "signInWithGoogle": "使用 Google 登录"
  },
  "navigation": {
    "home": "首页",
    "projects": "项目",
    "chat": "对话",
    "importData": "数据导入",
    "settings": "设置",
    "profile": "个人资料",
    "logout": "退出"
  },
  "project": {
    "createProject": "创建项目",
    "projectName": "项目名称",
    "description": "项目描述",
    "categories": "类别",
    "brands": "品牌",
    "segments": "细分市场",
    "totalProducts": "产品总数",
    "totalBrands": "品牌总数",
    "totalReviews": "评论总数",
    "analysisComplete": "分析完成",
    "processingData": "数据处理中...",
    "estimatedTime": "预计时间"
  },
  "dashboard": {
    "marketAnalysis": "市场分析",
    "brandAnalysis": "品牌分析",
    "pricingAnalysis": "价格分析",
    "reviewInsights": "评论洞察",
    "competitorAnalysis": "竞争对手分析",
    "salesTrend": "销售趋势",
    "customerSatisfaction": "客户满意度"
  },
  "charts": {
    "revenue": "收入",
    "volume": "销量",
    "noDataAvailable": "暂无数据",
    "loadingChart": "图表加载中...",
    "chartError": "图表加载失败",
    "clickToExpand": "点击展开",
    "downloadChart": "下载图表",
    "shareChart": "分享图表"
  },
  "filters": {
    "applyFilters": "应用筛选",
    "resetFilters": "重置筛选",
    "categoryFilter": "类别筛选",
    "brandFilter": "品牌筛选",
    "priceRange": "价格区间",
    "dateRange": "日期区间",
    "showMore": "显示更多",
    "showLess": "显示较少"
  },
  "errors": {
    "pageNotFound": "页面未找到",
    "serverError": "服务器错误",
    "networkError": "网络错误",
    "permissionDenied": "权限不足",
    "sessionExpired": "会话已过期",
    "invalidInput": "输入无效",
    "fileUploadError": "文件上传失败"
  },
  "meta": {
    "title": "Xenith - 营销数据分析AI助手",
    "description": "AI驱动的营销数据分析和图表生成工具",
    "keywords": "AI, 数据分析, 营销, 图表, 洞察"
  }
}
```

## ⚙️ 核心配置文件 - 最小化变更

### 1. i18n/config.ts

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enTranslations from './locales/en.json';
import zhTranslations from './locales/zh.json';

// 支持的语言列表
export const supportedLngs = ['en', 'zh'];
export const fallbackLng = 'en'; // 兜底语言：英文

// 语言资源
const resources = {
  en: {
    translation: enTranslations
  },
  zh: {
    translation: zhTranslations
  }
};

// i18next配置
i18n
  .use(LanguageDetector) // 浏览器语言检测
  .use(initReactI18next) // React集成
  .init({
    resources,
    supportedLngs,
    fallbackLng,
  
    // 语言检测配置
    detection: {
      // 检测顺序：localStorage -> navigator -> fallback
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'i18nextLng',
      caches: ['localStorage'],
    },

    interpolation: {
      escapeValue: false, // React已经转义了
    },

    // 开发模式下显示调试信息
    debug: process.env.NODE_ENV === 'development',
  });

export default i18n;

// 语言显示配置
export const languageConfig = {
  en: {
    label: 'English',
    flag: '🇺🇸'
  },
  zh: {
    label: '中文',
    flag: '🇨🇳'
  }
} as const;
```

### 2. app/layout.tsx 修改（在现有基础上添加）

```typescript
// 在现有 layout.tsx 中添加 I18nProvider
'use client';

import { useEffect } from 'react';
import './globals.css';
import { AuthProvider } from '@/contexts/auth-context';
import { Toaster } from '@/components/ui/toaster';
import { PostHogAppProvider } from './providers';

// 🆕 新增：导入 i18n 配置
import '@/i18n/config';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // 🆕 新增：初始化 i18n
  useEffect(() => {
    // i18n 会自动初始化，无需额外代码
  }, []);

  return (
    <html lang="zh-CN"> {/* 🔄 修改：动态语言可后续优化 */}
      <body className={`${inter.variable} font-sans antialiased`}>
        <PostHogAppProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
          <Toaster />
        </PostHogAppProvider>
      </body>
    </html>
  );
}
```

## 🔧 组件实现 - 最小化变更

### 1. 语言切换组件

```typescript
// components/ui/language-switcher.tsx
'use client';

import { useTranslation } from 'react-i18next';
import { supportedLngs, languageConfig } from '@/i18n/config';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Globe } from 'lucide-react';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const currentLang = i18n.language;

  const switchLanguage = (newLang: string) => {
    i18n.changeLanguage(newLang);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm">
          <Globe className="h-4 w-4 mr-2" />
          {languageConfig[currentLang as keyof typeof languageConfig]?.label || 'English'}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {supportedLngs.map((lang) => (
          <DropdownMenuItem
            key={lang}
            onClick={() => switchLanguage(lang)}
            className={currentLang === lang ? 'bg-accent' : ''}
          >
            <span className="mr-2">
              {languageConfig[lang as keyof typeof languageConfig]?.flag}
            </span>
            {languageConfig[lang as keyof typeof languageConfig]?.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

### 2. 简化的翻译Hooks

```typescript
// i18n/hooks.ts
import { useTranslation } from 'react-i18next';

// 通用翻译Hook - 最常用
export function useCommonT() {
  const { t } = useTranslation();
  return (key: string) => t(`common.${key}`);
}

// 认证翻译Hook
export function useAuthT() {
  const { t } = useTranslation();
  return (key: string) => t(`auth.${key}`);
}

// 项目翻译Hook
export function useProjectT() {
  const { t } = useTranslation();
  return (key: string) => t(`project.${key}`);
}

// 仪表板翻译Hook
export function useDashboardT() {
  const { t } = useTranslation();
  return (key: string) => t(`dashboard.${key}`);
}

// 图表翻译Hook
export function useChartsT() {
  const { t } = useTranslation();
  return (key: string) => t(`charts.${key}`);
}

// 通用翻译Hook - 完整版本
export function useT() {
  const { t } = useTranslation();
  return t;
}
```

### 3. 使用示例 - 如何替换硬编码文本

```typescript
// 原来的代码（硬编码）
export function LoginForm() {
  return (
    <form>
      <h1>Login</h1>
      <input placeholder="Email" />
      <input placeholder="Password" />
      <button>Sign In</button>
    </form>
  );
}

// 国际化后的代码（最小修改）
import { useAuthT } from '@/i18n/hooks';

export function LoginForm() {
  const t = useAuthT(); // 🆕 添加这一行
  
  return (
    <form>
      <h1>{t('login')}</h1> {/* 🔄 修改 */}
      <input placeholder={t('email')} /> {/* 🔄 修改 */}
      <input placeholder={t('password')} /> {/* 🔄 修改 */}
      <button>{t('login')}</button> {/* 🔄 修改 */}
    </form>
  );
}
```

## 📋 详细修改清单 - 最小化变更实施计划

### 🔧 阶段1：基础设施搭建（预计1-2天）

#### 📦 依赖安装

```bash
npm install react-i18next i18next i18next-browser-languagedetector
npm install -D @types/react-i18next
```

#### 📁 新建文件（6个文件）

- [ ] **`src/i18n/config.ts`** - i18next配置文件
- [ ] **`src/i18n/hooks.ts`** - 翻译Hooks工具
- [ ] **`src/i18n/types.ts`** - TypeScript类型定义
- [ ] **`src/i18n/locales/en.json`** - 英文翻译文件
- [ ] **`src/i18n/locales/zh.json`** - 中文翻译文件
- [ ] **`src/components/ui/language-switcher.tsx`** - 语言切换组件

#### 🔄 修改现有文件（1个文件）

- [ ] **`src/app/layout.tsx`** - 添加i18n初始化
  - **变更**：添加 `import '@/i18n/config'`（仅1行代码）

### 🏗️ 阶段2：核心组件国际化（预计2-3天）

#### 🔐 认证模块（4个文件）

- [ ] **`src/app/auth/callback/page.tsx`** - 认证回调页面

  - **需要替换**：`"Completing authentication..."`, `"Authentication successful!"`
  - **修改内容**：添加 `const t = useCommonT()` + 替换2-3个硬编码文本
- [ ] **`src/app/auth/reset-password/page.tsx`** - 密码重置页面

  - **需要替换**：`"Reset Password"`, `"Enter your new password"`, 表单标签
  - **修改内容**：添加 `const t = useAuthT()` + 替换4-5个硬编码文本
- [ ] **`src/components/auth/login-modal.tsx`** - 登录模态框

  - **需要替换**：登录表单的所有文本
  - **修改内容**：添加 `const t = useAuthT()` + 替换5-6个硬编码文本
- [ ] **`src/components/auth/protected-route.tsx`** - 权限路由组件

  - **需要替换**：权限提示文本
  - **修改内容**：添加 `const t = useCommonT()` + 替换1-2个硬编码文本

#### 🏠 主页和布局（3个文件）

- [ ] **`src/app/page.tsx`** - 首页

  - **需要替换**：`"Xenith"`, `"Create Project"`, `"Import Data"`, 项目状态文本
  - **修改内容**：添加 `const t = useProjectT()` + 替换6-8个硬编码文本
- [ ] **`src/components/layout/sidebar.tsx`** - 侧边栏

  - **需要替换**：导航菜单项文本
  - **修改内容**：添加 `const t = useCommonT()` + 替换3-4个硬编码文本
- [ ] **`src/components/layout/project-card.tsx`** - 项目卡片

  - **需要替换**：项目状态、按钮文本
  - **修改内容**：添加 `const t = useProjectT()` + 替换3-4个硬编码文本

#### 📊 项目管理模块（4个文件）

- [ ] **`src/app/onboarding/page.tsx`** - 项目创建页面

  - **需要替换**：`"Create New Project"`, `"Select project data scope"`等
  - **修改内容**：添加 `const t = useProjectT()` + 替换8-10个硬编码文本
- [ ] **`src/app/import-data/page.tsx`** - 数据导入页面

  - **需要替换**：`"Data Scraping"`, `"Collect product data"`等
  - **修改内容**：添加 `const t = useProjectT()` + 替换6-8个硬编码文本
- [ ] **`src/app/project/[id]/page.tsx`** - 项目详情页

  - **需要替换**：项目概览文本
  - **修改内容**：添加 `const t = useProjectT()` + 替换4-5个硬编码文本
- [ ] **`src/app/project/[id]/progress/page.tsx`** - 项目进度页

  - **需要替换**：进度状态文本
  - **修改内容**：添加 `const t = useProjectT()` + 替换5-6个硬编码文本

### 📊 阶段3：分析和图表组件（预计3-4天）

#### 🎯 分析面板核心（2个文件）

- [ ] **`src/components/analysis-db/index.tsx`** - 主要分析容器

  - **需要替换**：tab标题、加载状态文本
  - **修改内容**：添加 `const t = useDashboardT()` + 替换4-5个硬编码文本
- [ ] **`src/components/analysis-db/market-analysis/brand-analysis.tsx`** - 品牌分析

  - **需要替换**：图表标题、指标名称
  - **修改内容**：添加 `const t = useDashboardT()` + 替换3-4个硬编码文本

#### 📈 图表组件（3个文件）

- [ ] **`src/app/chat/charts/customer_satisfaction/components/customer-satisfaction-chart.tsx`**

  - **需要替换**：`"Loading chart data..."`, `"No Data Available"`等
  - **修改内容**：添加 `const t = useChartsT()` + 替换3-4个硬编码文本
- [ ] **`src/app/chat/charts/sales_trend/components/sales-trend-chart.tsx`**

  - **需要替换**：图表标题、轴标签
  - **修改内容**：添加 `const t = useChartsT()` + 替换3-4个硬编码文本
- [ ] **`src/components/analysis-db/charts/bar-chart.tsx`** - 柱状图组件

  - **需要替换**：Tooltip文本
  - **修改内容**：添加 `const t = useChartsT()` + 替换2-3个硬编码文本

#### 🔍 筛选器组件（1个文件）

- [ ] **`src/components/analysis-db/shared/universal-filter-component.tsx`**
  - **需要替换**：`"Apply Filters"`, `"Reset Filters"`等按钮文本
  - **修改内容**：添加 `const t = useCommonT()` + 替换4-5个硬编码文本

### 💬 阶段4：聊天和交互功能（预计2-3天）

#### 💬 聊天模块（2个文件）

- [ ] **`src/app/chat/page.tsx`** - 聊天页面

  - **需要替换**：`"Sales Analytics Chat"`, 控制面板文本
  - **修改内容**：添加 `const t = useChartsT()` + 替换5-6个硬编码文本
- [ ] **`src/app/project/[id]/chat/page.tsx`** - 项目聊天页

  - **需要替换**：聊天界面文本
  - **修改内容**：添加 `const t = useChartsT()` + 替换3-4个硬编码文本

#### 📋 数据和表单组件（2个文件）

- [ ] **`src/components/tabs/data-confirmation-tab.tsx`** - 数据确认标签

  - **需要替换**：大量表单文本和状态提示
  - **修改内容**：添加 `const t = useProjectT()` + 替换10-12个硬编码文本
- [ ] **`src/components/tabs/data-import-tab.tsx`** - 数据导入标签

  - **需要替换**：导入状态和进度文本
  - **修改内容**：添加 `const t = useProjectT()` + 替换8-10个硬编码文本

### 🧪 阶段5：测试和优化（预计1-2天）

#### ✅ 功能测试

- [ ] **测试语言切换功能** - 确保所有页面都能正确切换
- [ ] **测试浏览器语言检测** - 验证初次访问的语言选择
- [ ] **测试localStorage持久化** - 确保用户选择被记住
- [ ] **回归测试现有功能** - 确保国际化不影响原有功能

#### 🔧 优化和完善

- [ ] **添加语言切换组件到导航栏** - 在适当位置添加语言切换器
- [ ] **完善翻译文本** - 检查所有翻译的准确性和一致性
- [ ] **TypeScript类型优化** - 确保类型安全

## 📊 变更量统计

### 📈 总体变更评估

- **新增文件**: 6个（配置、翻译、组件）
- **修改文件**: 约25-30个（主要是替换硬编码文本）
- **路由重构**: 0个（保持现有结构）
- **大型重构**: 0个（最小化变更原则）

### 📝 修改类型分布

- **一行导入添加**: ~25个文件
- **硬编码文本替换**: ~25个文件
- **新增翻译Hook调用**: ~25个文件
- **大量逻辑修改**: 0个文件

## 🔧 开发时注意事项

### 翻译键命名规范

```typescript
// ✅ 好的命名
t('auth.login')
t('project.createProject')
t('dashboard.marketAnalysis')

// ❌ 避免的命名
t('button1')
t('text')
t('label')
```

### 动态内容处理

```typescript
// ✅ 正确处理动态内容
t('project.productsCount', { count: 123 })
// 翻译文件: "products": "{{count}} products"

// ❌ 避免字符串拼接
`${count} products`
```

### 类型安全

```typescript
// i18n/types.ts
import type en from './locales/en.json';

declare module 'react-i18next' {
  interface CustomTypeOptions {
    defaultNS: 'translation';
    resources: {
      translation: typeof en;
    };
  }
}
```

## 📋
