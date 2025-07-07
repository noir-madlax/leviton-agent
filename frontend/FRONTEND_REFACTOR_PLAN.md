# 前端界面重构设计文档 & 项目计划

## 📋 项目概览

### 目标

将现有的 Tab-based 前端架构改造为 Page-based 架构，使用新的产品设计界面，保留所有现有功能和业务逻辑。

### 核心原则

- ✅ **保留**：所有现有业务逻辑、数据处理、API调用、状态管理
- 🎨 **更新**：UI组件、页面布局、用户体验流程
- 🔧 **适配**：路由结构、组件结构、页面跳转逻辑
- 📱 **优化**：响应式设计、交互体验

---

## 🗺️ 路由设计与页面关系

### 现有架构 (Tab-based)

```
MainLayout
├── Step 1: 数据导入 (DataImportTab)
├── Step 2: 数据范围选择 (DataConfirmationTab)
├── Step 3: 分析 (AnalysisDbTab)
└── Step 4: 聊天 (ChatInterface + ChartRenderer)
```

### 新架构 (Page-based)

```
App Router
├── / (主页)
│   ├── 项目列表
│   ├── Sidebar
│   └── 右上角按钮：[导入数据] [新建项目]
├── /import-data (数据导入页面)
│   └── 迁移 DataImportTab 组件
├── /onboarding (新建项目页面)
│   └── 迁移 DataConfirmationTab 逻辑 + 新UI
├── /project/[id] (项目Dashboard页面)
│   └── 迁移 AnalysisDbTab 组件
└── /project/[id]/chat (项目聊天页面)
    └── 迁移 ChatInterface 组件 + 新UI
```

### 页面跳转流程

```mermaid
graph TD
    A[主页 /] --> B[导入数据 /import-data]
    A --> C[新建项目 /onboarding]
    A --> D[项目详情 /project/[id]]
    D --> E[项目聊天 /project/[id]/chat]
    B --> A
    C --> D
    E --> D
```

---

## 🎯 实施计划

### 阶段1：基础架构改造 (优先级：🔴 高)

#### 目标

建立新的路由结构，确保所有现有功能可以通过新界面跳转访问。

#### 任务清单

- [ ] **1.1 创建新的路由结构**

  - [ ] 创建主页面 `app/page.tsx`
  - [ ] 创建数据导入页面 `app/import-data/page.tsx`
  - [ ] 创建项目详情页面 `app/project/[id]/page.tsx`
  - [ ] 创建项目聊天页面 `app/project/[id]/chat/page.tsx`
  - [ ] 创建新建项目页面 `app/onboarding/page.tsx`
- [ ] **1.2 复用新设计的基础组件**

  - [ ] 复制并适配 `Sidebar` 组件
  - [ ] 复制并适配 `ProjectCard` 组件
  - [ ] 复制并适配 `UserMenu` 组件（暂时简化，不包含用户认证）
  - [ ] 复制相关的 shadcn UI 组件
- [ ] **1.3 建立页面跳转逻辑**

  - [ ] 主页面集成项目列表显示（使用现有 Supabase 数据）
  - [ ] 配置所有页面间的导航链接
  - [ ] 保留现有的 MainLayout 作为备用（通过 `/legacy` 路由访问）
- [ ] **1.4 数据层适配**

  - [ ] 确保 `database-service.ts` 在新页面中正常工作
  - [ ] 项目列表数据加载逻辑（复用 Step3 的项目选择逻辑）
  - [ ] 状态管理适配（ChartContext 等）

#### 技术要点

- **路由设计**：使用 Next.js App Router
- **数据加载**：复用现有的 `getProjects()` 等 API
- **状态管理**：保留现有的 `ChartContext`，暂时不集成 `chart-pin-context`
- **样式系统**：使用 shadcn 组件 + Tailwind CSS

#### 验收标准

- ✅ 用户可以从主页跳转到所有现有功能页面
- ✅ 所有现有功能正常运行（数据导入、项目创建、分析、聊天）
- ✅ 页面间导航流畅，无死链
- ✅ 响应式设计基本可用

---

### 阶段2：页面UI改造 (优先级：🟡 中)

#### 目标

将各个功能页面的UI改造为新设计风格，提升用户体验。

#### 任务清单

- [ ] **2.1 主页面优化**

  - [ ] 实现完整的项目列表展示
  - [ ] 优化 Sidebar 功能（项目分组、搜索等）
  - [ ] 添加项目统计信息显示
  - [ ] 实现项目状态显示（进行中、已完成等）
- [ ] **2.2 数据导入页面改造**

  - [ ] 使用新的页面布局
  - [ ] 优化进度显示UI
  - [ ] 改进错误处理和用户反馈
  - [ ] 添加返回主页的导航
- [ ] **2.3 项目创建页面改造**

  - [ ] 整合 onboarding 页面的步骤式UI
  - [ ] 保留现有的数据选择和过滤逻辑
  - [ ] 优化项目创建流程的用户体验
  - [ ] 添加进度指示器
- [ ] **2.4 项目Dashboard页面改造**

  - [ ] 实现新的Dashboard布局
  - [ ] 优化图表展示和交互
  - [ ] 添加项目信息头部
  - [ ] 改进数据筛选和切换功能
- [ ] **2.5 聊天页面改造**

  - [ ] 实现新的聊天界面设计
  - [ ] 优化消息显示和交互
  - [ ] 改进图表生成和展示
  - [ ] 添加聊天历史和上下文管理

#### 技术要点

- **组件复用**：最大化复用现有业务逻辑组件
- **UI一致性**：统一使用新设计的视觉风格
- **交互优化**：改进用户操作流程和反馈
- **响应式设计**：确保在不同设备上的良好体验

#### 验收标准

- ✅ 所有页面视觉风格统一，符合新设计规范
- ✅ 用户体验流畅，操作直观
- ✅ 所有现有功能完整保留
- ✅ 性能无明显退化

---

### 阶段3：优化与完善 (优先级：🟢 低)

#### 目标

优化性能，完善细节，为后续功能扩展做准备。

#### 任务清单

- [ ] **3.1 性能优化**

  - [ ] 代码分割和懒加载
  - [ ] 图表渲染性能优化
  - [ ] 数据加载优化
  - [ ] 缓存策略优化
- [ ] **3.2 用户体验优化**

  - [ ] 加载状态优化
  - [ ] 错误边界处理
  - [ ] 无障碍性改进
  - [ ] 键盘导航支持
- [ ] **3.3 功能扩展准备**

  - [ ] Chart Pin 功能预留接口
  - [ ] 用户认证系统预留接口
  - [ ] 多语言支持预留
  - [ ] 主题切换预留

---

## 📁 文件结构规划

### 新增文件

```
frontend/src/
├── app/
│   ├── page.tsx                    # 主页面
│   ├── import-data/
│   │   └── page.tsx               # 数据导入页面
│   ├── onboarding/
│   │   └── page.tsx               # 新建项目页面
│   ├── project/
│   │   └── [id]/
│   │       ├── page.tsx           # 项目Dashboard页面
│   │       └── chat/
│   │           └── page.tsx       # 项目聊天页面
│   └── legacy/
│       └── page.tsx               # 备用：现有MainLayout
├── components/
│   ├── layout/
│   │   ├── sidebar.tsx            # 新：侧边栏组件
│   │   ├── project-card.tsx       # 新：项目卡片组件
│   │   └── user-menu.tsx          # 新：用户菜单组件
│   ├── pages/
│   │   ├── home-page.tsx          # 新：主页面组件
│   │   ├── import-data-page.tsx   # 新：数据导入页面组件
│   │   ├── onboarding-page.tsx    # 新：新建项目页面组件
│   │   ├── project-page.tsx       # 新：项目详情页面组件
│   │   └── chat-page.tsx          # 新：聊天页面组件
│   └── ui/
│       └── [shadcn components]    # 复用的UI组件
└── lib/
    └── project-service.ts         # 新：项目相关服务
```

### 保留文件

```
frontend/src/
├── components/
│   ├── tabs/                      # 保留：现有Tab组件
│   ├── analysis-db/               # 保留：分析相关组件
│   ├── chat/                      # 保留：聊天相关组件
│   └── charts/                    # 保留：图表相关组件
├── contexts/
│   └── chart-context.tsx          # 保留：图表上下文
└── lib/
    └── [existing files]           # 保留：所有现有库文件
```

---

## 🔧 技术实现要点

### 1. 路由实现

```typescript
// app/page.tsx - 主页面
export default function HomePage() {
  // 加载项目列表
  // 渲染 Sidebar + ProjectCard 列表
  // 处理导航到其他页面
}

// app/project/[id]/page.tsx - 项目详情页面
export default function ProjectPage({ params }: { params: { id: string } }) {
  // 复用 AnalysisDbTab 组件
  // 添加项目信息头部
  // 处理到聊天页面的导航
}
```

### 2. 数据加载策略

```typescript
// 复用现有的 database-service.ts
import { DatabaseService } from '@/components/analysis-db/data/database-service';

// 项目列表加载
const databaseService = new DatabaseService();
const projects = await databaseService.getProjects();

// 项目详情加载
const project = await databaseService.getProject(projectId);
```

### 3. 状态管理

```typescript
// 保留现有的 ChartContext
// 在新页面中正确使用
<ChartProvider>
  <NewPageComponent />
</ChartProvider>
```

### 4. 组件复用

```typescript
// 复用现有业务逻辑组件
import { DataImportTab } from '@/components/tabs/data-import-tab';
import { AnalysisDbTab } from '@/components/tabs/analysis-db-tab';
import { ChatInterface } from '@/components/chat/chat-interface';

// 在新页面中使用
export default function ImportDataPage() {
  return (
    <div className="new-page-layout">
      <DataImportTab />
    </div>
  );
}
```

---

## 📊 进度跟踪

### 阶段1进度

- [ ] **基础架构改造** (预计：3-4天)
  - [ ] 路由结构创建 - 📅 计划开始：[日期]
  - [ ] 基础组件复用 - 📅 计划开始：[日期]
  - [ ] 页面跳转逻辑 - 📅 计划开始：[日期]
  - [ ] 数据层适配 - 📅 计划开始：[日期]

### 阶段2进度

- [ ] **页面UI改造** (预计：5-6天)
  - [ ] 主页面优化 - 📅 计划开始：[日期]
  - [ ] 数据导入页面改造 - 📅 计划开始：[日期]
  - [ ] 项目创建页面改造 - 📅 计划开始：[日期]
  - [ ] 项目Dashboard页面改造 - 📅 计划开始：[日期]
  - [ ] 聊天页面改造 - 📅 计划开始：[日期]

### 阶段3进度

- [ ] **优化与完善** (预计：2-3天)
  - [ ] 性能优化 - 📅 计划开始：[日期]
  - [ ] 用户体验优化 - 📅 计划开始：[日期]
  - [ ] 功能扩展准备 - 📅 计划开始：[日期]

---

## 🎯 关键决策记录

### 已确认决策

1. **Chart Pin功能**：第一阶段不实现，后续可扩展
2. **项目数据加载**：使用现有Supabase + database-service.ts
3. **数据导入入口**：主页右上角，新建项目按钮左侧
4. **用户认证**：后续添加，当前不实现
5. **UI组件**：使用shadcn实现新UI样式
6. **实施策略**：分阶段实施，第一阶段优先路由和基础功能

### 待决策事项

- [ ] 是否需要保留 `/legacy` 路由作为备用
  - [ ] 不需要
- [ ] Chart Pin 功能的具体实现方式
  - [ ] 暂时不实现
- [ ] 用户认证系统的集成方案
  - [ ] 用supabse自带的auth，以上都完成后实现
- [ ] 性能优化的具体目标
  - [ ] 暂时不实施

---

## 🔍 风险评估

### 高风险项

1. **状态管理兼容性**：ChartContext 在新页面架构中的兼容性
2. **数据加载性能**：从Tab切换到页面跳转可能影响数据加载体验
3. **路由参数传递**：确保所有必要的状态在页面间正确传递

### 风险缓解策略

1. **逐步迁移**：保留现有功能作为备用
2. **充分测试**：每个阶段完成后进行全面测试
3. **回滚计划**：保留现有代码，确保可以快速回滚

---

## 📝 后续TODO

### 立即需要

- [ ] 开始阶段1的实施
- [ ] 设置开发环境和构建流程
- [ ] 创建测试计划

### 中期计划

- [ ] 用户反馈收集
- [ ] 性能监控设置
- [ ] 文档更新

### 长期计划

- [ ] Chart Pin 功能设计
- [ ] 用户认证系统集成
- [ ] 多语言支持

---

## 💡 补充说明

### 为其他AI提供的上下文

本文档是前端重构项目的主要参考文档，包含了：

- 完整的技术架构设计
- 详细的实施计划
- 进度跟踪机制
- 关键决策记录

在后续的对话中，请参考此文档的内容，确保实施方案的一致性。

### 更新机制

- 每完成一个阶段，更新对应的进度标记
- 有新的决策时，更新"关键决策记录"部分
- 遇到问题时，更新"风险评估"部分

---

**文档版本**：v1.0
**创建时间**：[当前日期]
**最后更新**：[当前日期]
**责任人**：Frontend Team
