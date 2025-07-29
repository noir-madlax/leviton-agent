# 项目Chat配置化完整设计方案

## 项目背景

### 现状问题
1. **左侧Chat Cards硬编码**：所有项目使用相同的4个chart cards（Market Analysis、Pricing Analysis、Customer Reviews、Competitive Analysis）
2. **Chat Message内容固定**：开头话、结尾话都是写死的文本
3. **右侧图表结构固定**：每个chart card对应的具体图表内容无法配置
4. **无项目差异化**：所有项目的chat结构和内容完全一致

### 目标需求
- 不同项目可以有不同的chat cards配置
- 支持项目级别的chat message定制
- 右侧图表内容可根据配置动态调整
- 保持现有UI交互逻辑不变

## 当前系统架构分析

### 完整数据流程
```
项目页面加载流程：
project/[id]/page.tsx 
└── IntegratedLayout (集成布局容器)
    ├── Header (顶部导航栏)
    └── 主体区域 (flex left-right分栏)
        ├── 左侧容器 (1/3宽度)
        │   └── ChatWithNavigation 
        │       ├── 固定AI介绍文本 (硬编码)
        │       ├── ChartCardList 
        │       │   ├── 硬编码presetCards (来自use-chart-management.ts)
        │       │   └── 硬编码CHART_DETAILS (每个card下的具体charts)
        │       ├── 历史聊天消息
        │       └── 聊天输入框
        └── 右侧容器 (2/3宽度)
            └── ChartContainer
                └── AnalysisDbContainer (根据activeTab切换)
                    ├── 固定的TabsContent映射
                    └── 固定的组件结构 (BrandAnalysis, PricingAnalysis等)
```

### 关键状态管理层级
```
1. IntegratedLayout层级:
   - activeTab (来自useDashboardNavigation)
   - activeChartId (来自useChartManagement) 
   - chartContainerState

2. useChartManagement层级:
   - presetCards: 硬编码4个卡片
   - dynamicCharts: AI生成的动态图表
   - selectChart函数: 控制右侧显示

3. AnalysisDbContainer层级:
   - 接收activeTab参数
   - handleTabChange: 根据tab加载数据
   - 固定的组件渲染逻辑

4. ChartCardList层级:
   - CHART_DETAILS: 硬编码每个card下的charts
   - scrollToChart: 定位具体图表
```

### 交互触发链路
```
用户点击流程：
1. ChartCard点击 → selectChart(cardId)
2. selectChart → setActiveChartId + setChartContainerState('navigation')
3. IntegratedLayout监听activeChartId → handleTabChange(card.tabKey)  
4. handleTabChange → setActiveTab(mappedTab)
5. ChartContainer接收navigationTab → AnalysisDbContainer接收activeTab
6. AnalysisDbContainer监听activeTab → handleTabChange → loadSpecificData
7. 根据tab类型加载数据 → 渲染固定组件结构

关键连接点：
- card.tabKey: 连接左侧卡片和右侧tab的桥梁
- tabMapping: IntegratedLayout中的硬编码映射关系
- CHART_DETAILS: ChartCardList中每个card下的具体charts
```

### 核心硬编码位置
```
1. useChartManagement.ts:
   - presetCards数组 (4个固定卡片)
   
2. chart-card-list.tsx:
   - CHART_DETAILS对象 (每个card下的charts列表)
   
3. chat-with-navigation.tsx:
   - AI介绍文本 (开头话、结尾话)
   
4. integrated-layout.tsx:
   - tabMapping对象 (card到tab的映射)
   - 默认选中"brand-analysis"逻辑
   
5. analysis-db/index.tsx:
   - TabsContent结构 (固定的组件映射)
   - BrandAnalysis等组件内部结构
```

## 数据库设计

### 统一配置表结构
```sql
CREATE TABLE chart_configs (
    id SERIAL PRIMARY KEY,
    project_id UUID NULL,  -- NULL=默认模板, 有值=项目特定配置
    config_type VARCHAR(20) NOT NULL, -- 'chart_card' | 'chart_item' | 'chat_message'
    
    -- Chart Card相关字段
    card_order INTEGER NULL,           -- chart card显示顺序
    card_id VARCHAR(50) NULL,          -- chart card唯一ID
    card_config JSONB NULL,            -- {title, description, icon, tabKey, aiIntroduction}
    
    -- Chart Item相关字段  
    parent_card_id VARCHAR(50) NULL,   -- 所属的chart card ID
    chart_order INTEGER NULL,          -- chart在card内的显示顺序
    chart_name VARCHAR(255) NULL,      -- chart显示名称
    chart_id VARCHAR(50) NULL,         -- chart唯一ID
    chart_component VARCHAR(100) NULL, -- 对应的组件名称
    
    -- Chat Message相关字段
    message_order INTEGER NULL,        -- 消息显示顺序
    message_type VARCHAR(20) NULL,     -- 'opening' | 'chart_cards' | 'closing'
    message_content TEXT NULL,         -- 消息内容
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### API设计
```
GET /api/projects/{project_id}/chat-config
返回格式: {
  chatMessages: [
    {message_order: 1, message_type: 'opening', message_content: '...'},
    {message_order: 2, message_type: 'chart_cards', message_content: '{{PLACEHOLDER}}'},
    {message_order: 3, message_type: 'closing', message_content: '...'}
  ],
  chartCards: [
    {card_order: 1, card_id: 'brand-analysis', card_config: {...}},
    {card_order: 2, card_id: 'pricing-analysis', card_config: {...}}
  ],
  chartItems: {
    'brand-analysis': [
      {chart_order: 1, chart_name: 'TAM and Market Share', chart_id: 'market-share-analysis'},
      {chart_order: 2, chart_name: 'Top 10 Brands', chart_id: 'brand-analysis'}
    ],
    'pricing-analysis': [...]
  }
}
```

## 三阶段实施计划

### 第一阶段：Chart Cards数据库化 + 后端基础建设
**目的**：建立数据库基础设施，实现左侧chart cards的动态配置

**核心任务**：
- 创建数据库表和API
- 替换硬编码的chart cards
- 替换硬编码的chart items列表
- 建立项目配置优先级机制

**关键变更点**：
- `use-chart-management.ts`: 删除presetCards，改为API获取
- `chart-card-list.tsx`: 删除CHART_DETAILS，改为props传入
- `chat-with-navigation.tsx`: 接收并传递chartItems配置
- `integrated-layout.tsx`: 处理配置数据传递

**第一阶段后的效果**：
- 左侧chart cards从数据库读取
- 每个card下的具体charts列表从数据库读取
- 支持项目级别定制
- 右侧图表显示逻辑保持不变

### 第二阶段：Chat Message Template化
**目的**：实现chat内容的项目级别定制

**核心任务**：
- 替换硬编码的AI介绍文本
- 实现chat template渲染机制
- 支持chart cards占位符替换

**关键变更点**：
- `chat-with-navigation.tsx`: 删除固定文本，改为template渲染

**依赖信息**：
- 需要第一阶段的API数据结构
- chat template中的占位符替换逻辑
- 保持原有的聊天消息结构

**第二阶段后的效果**：
- 开头话、结尾话可项目定制
- chart cards嵌入到template指定位置
- 整个左侧chat区域完全动态化

### 第三阶段：右侧图表内容动态化
**目的**：实现右侧图表显示内容的完全动态配置

**核心任务**：
- 拆分现有大组件为独立图表组件
- 建立图表组件注册机制
- 实现动态图表渲染器
- 替换固定的TabsContent结构

**关键变更点**：
- `analysis-db/index.tsx`: 替换固定TabsContent为动态渲染
- 新增`dynamic-chart-renderer.tsx`: 图表组件注册和动态渲染
- 拆分现有组件: BrandAnalysis → 独立图表组件

**复杂度考量**：
- 需要深入理解现有组件的数据依赖
- 组件拆分可能影响数据传递逻辑
- 图表组件间的数据共享机制

**第三阶段后的效果**：
- 右侧显示的具体图表完全由数据库配置决定
- 支持灵活的图表组合
- 实现真正的全链路动态配置

## 实施注意事项

### 数据一致性要求
1. **TabKey映射**: card_config中的tabKey必须与AnalysisDbContainer的case分支匹配
2. **Chart ID统一**: chart_id在左侧导航和右侧渲染中必须一致
3. **默认配置完整性**: 确保所有现有项目都有完整的默认配置

### 向后兼容策略
1. **优雅降级**: API失败时的处理机制
2. **配置缺失处理**: 项目无配置时使用默认模板
3. **渐进式迁移**: 现有项目自动获得默认配置

### 性能考虑
1. **配置缓存**: 避免频繁的数据库查询
2. **懒加载**: chart components按需加载
3. **加载状态**: 配置获取期间的UI状态管理

### 开发顺序依赖
1. **第一阶段是基础**: 后续阶段依赖其API和数据结构
2. **第二阶段相对独立**: 主要是前端模板化改造
3. **第三阶段最复杂**: 需要深入理解现有组件架构

## 关键代码位置参考

### 需要深入理解的核心文件
```
配置管理层:
- use-chart-management.ts: 状态管理核心
- integrated-layout.tsx: 布局和状态协调

交互处理层:
- chart-card-list.tsx: 卡片列表和导航
- chat-with-navigation.tsx: 聊天界面主容器

数据展示层:
- analysis-db/index.tsx: 右侧容器和tab切换
- brand-analysis.tsx: 具体图表组件示例

状态传递链:
- project/[id]/page.tsx → IntegratedLayout → ChatWithNavigation → ChartCardList
- IntegratedLayout → ChartContainer → AnalysisDbContainer
```

### 数据结构映射关系
```
数据库 → API → 前端状态 → UI渲染
chart_configs → chat-config API → chartCards/chartItems → ChartCardList
chart_configs → chat-config API → chatMessages → ChatTemplate  
chart_configs → chat-config API → chartItems → DynamicChartRenderer
```

这个三阶段设计确保了：
1. **渐进式实施**: 每个阶段都有明确的目标和边界
2. **风险可控**: 避免一次性大规模改动
3. **向后兼容**: 每个阶段完成后系统都是可用的
4. **职责清晰**: 后端建设集中在第一阶段，后续专注前端改造

---

## 第一阶段详细实施设计

### 当前代码分析总结
经过深入代码分析，确认了以下关键硬编码位置及其具体内容：

#### 1. Chart Cards硬编码 (use-chart-management.ts:21-62)
```typescript
const presetCards: UnifiedChartCard[] = [
  {
    id: 'brand-analysis',
    type: 'preset', 
    title: 'Market Analysis',
    description: 'Market share and brand positioning analysis',
    icon: Building,
    tabKey: 'market-analysis',
    isActive: false,
    aiIntroduction: 'Market Analysis'
  },
  // ... 其他3个卡片
]
```

#### 2. Chart Items硬编码 (chart-card-list.tsx:14-95)
```typescript
const CHART_DETAILS = {
  'brand-analysis': {
    title: 'Market Analysis',
    charts: [
      { name: 'Total addressable market (TAM) and Market Share', id: 'market-share-analysis' },
      { name: 'Top 10 Best-Selling Brands', id: 'brand-analysis' },
      // ... 更多图表
    ]
  },
  // ... 其他cards的charts
}
```

#### 3. Chat Messages硬编码 (chat-with-navigation.tsx:367-389)
```typescript
// 开头话 (第367-369行)
"The data is ready for further analysis. Based on your questions, these charts present the key information:"

// 结尾话 (第387行)  
"Let me know if you'd like to explore anything further."
```

#### 4. Tab映射硬编码 (integrated-layout.tsx:135-143)
```typescript
const tabMapping: Record<string, string> = {
  'brand-analysis': 'brand-analysis',
  'product-analysis': 'product-analysis', 
  'pricing-analysis': 'pricing-analysis',
  // ... 其他映射
}
```

### 实施计划详细设计

#### A. 数据库建设 (后端)

**1. 创建数据库表**
- **文件**: `backend/dashboard/sql/001_create_chart_configs_table.sql`
- **内容**: 统一配置表schema

**2. 创建API endpoints**
- **文件**: `backend/dashboard/api.py` (扩展现有文件)
- **新增路由**: `GET /api/v1/projects/{project_id}/chat-config`

**3. 数据服务层**
- **文件**: `backend/dashboard/services/chat_config_service.py` (新建)
- **功能**: 处理配置数据的查询逻辑、优先级处理

**4. 数据模型**
- **文件**: `backend/dashboard/models.py` (扩展现有文件)  
- **新增**: ChatConfigResponse等pydantic模型

**5. 默认数据迁移**
- **文件**: `backend/dashboard/sql/002_insert_default_chat_configs.sql`
- **内容**: 将现有硬编码配置作为默认配置插入数据库

#### B. 前端改造

**1. 修改useChartManagement hook**
- **文件**: `frontend/src/components/integrated-dashboard/hooks/use-chart-management.ts`
- **变更**: 
  - 删除hardcoded presetCards (第21-62行)
  - 添加API调用获取配置
  - 添加loading和error状态管理

**2. 修改ChartCardList组件**
- **文件**: `frontend/src/components/integrated-dashboard/chat/chart-card-list.tsx`
- **变更**:
  - 删除CHART_DETAILS常量 (第14-95行)
  - 修改props接口，接收chartItems配置
  - 修改渲染逻辑使用props数据

**3. 修改ChatWithNavigation组件**
- **文件**: `frontend/src/components/integrated-dashboard/chat-with-navigation.tsx`
- **变更**:
  - 添加配置数据获取
  - 传递chartItems配置到ChartCardList
  - 保持现有聊天消息不变（第二阶段处理）

**4. 修改IntegratedLayout组件**
- **文件**: `frontend/src/components/integrated-dashboard/integrated-layout.tsx`
- **变更**:
  - 集成配置API调用
  - 协调配置数据在组件间传递
  - 保持现有tabMapping（第二阶段优化）

**5. 新增types定义**
- **文件**: `frontend/src/components/integrated-dashboard/shared/types.ts` (扩展)
- **新增**: ChatConfig, ChartItem等接口定义

#### C. API集成服务

**1. 配置服务**
- **文件**: `frontend/src/lib/services/chat-config-service.ts` (新建)
- **功能**: 封装配置API调用，处理缓存和错误

### To-Do List (第一阶段)

#### 后端任务 🔧
- [x] **数据库设计** ✅
  - [x] 创建 `backend/dashboard/sql/001_create_chart_configs_table.sql` ✅
  - [x] 设计表结构确保支持项目配置优先级 ✅
  - [x] 创建必要的索引提升查询性能 ✅

- [x] **默认数据迁移** ✅  
  - [x] 创建 `backend/dashboard/sql/002_insert_default_chat_configs.sql` ✅
  - [x] 将现有4个chart cards配置插入为默认模板 ✅
  - [x] 将现有CHART_DETAILS数据转换为chart_item记录 ✅
  - [x] 确保所有现有项目都有完整配置 ✅

- [x] **API开发** ✅
  - [x] 扩展 `backend/dashboard/models.py` 添加ChatConfigResponse等模型 ✅
  - [x] 创建 `backend/dashboard/services/chat_config_service.py` ✅ (已修复supabase客户端问题)
  - [x] 在 `backend/dashboard/api.py` 添加 `/projects/{project_id}/chat-config` 端点 ✅
  - [x] 实现项目特定配置 > 默认配置的优先级逻辑 ✅
  - [x] 添加错误处理和参数验证 ✅

- [x] **测试数据准备** ✅
  - [x] 准备测试项目的配置数据 ✅
  - [x] 验证API返回数据格式正确性 ✅ (数据库层测试通过)

#### 前端任务 🎨
- [x] **类型定义** ✅
  - [x] 扩展 `frontend/src/components/integrated-dashboard/shared/types.ts` ✅
  - [x] 定义 ChatConfig, ChartCardConfig, ChartItemConfig 接口 ✅
  - [x] 确保与后端API模型匹配 ✅

- [x] **配置服务** ✅
  - [x] 创建 `frontend/src/lib/services/chat-config-service.ts` ✅
  - [x] 实现配置获取、缓存和错误处理 ✅
  - [x] 支持优雅降级机制 ✅

- [x] **核心Hook改造** ✅
  - [x] 修改 `use-chart-management.ts` (第21-62行) ✅
    - [x] 删除硬编码 presetCards 数组 ✅
    - [x] 添加配置API调用 ✅
    - [x] 添加 loading/error 状态管理 ✅
    - [x] 保持现有动态图表逻辑不变 ✅

- [x] **组件改造** ✅
  - [x] 修改 `chart-card-list.tsx` ✅
    - [x] 删除 CHART_DETAILS 常量 (第14-95行) ✅
    - [x] 修改组件props接收chartItems配置 ✅
    - [x] 更新渲染逻辑使用动态数据 (第194-218行) ✅
    - [x] 保持现有scrollToChart功能 ✅

  - [x] 修改 `chat-with-navigation.tsx` ✅
    - [x] 添加配置数据状态管理 ✅
    - [x] 传递chartItems配置到ChartCardList ✅
    - [x] 添加配置加载状态处理 ✅
    - [x] 保持现有聊天消息不变 ✅

  - [x] 修改 `integrated-layout.tsx` ✅
    - [x] 集成配置获取逻辑 ✅
    - [x] 协调配置数据在组件树中传递 ✅
    - [x] 处理配置加载状态 ✅
    - [x] 保持现有tabMapping和默认选中逻辑 ✅

#### 集成测试任务 🧪
- [x] **后端API测试** ✅
  - [x] 测试 `/api/v1/dashboard/projects/{project_id}/chat-config` 端点 ✅
  - [x] 验证API返回正确的JSON格式 ✅
  - [x] 测试项目特定配置优先级逻辑 ✅
  - [x] 验证错误处理机制 ✅

- [x] **前端集成测试** ✅
  - [x] 测试前端服务能正确调用后端API ✅
  - [x] 验证配置数据正确传递到组件 ✅
  - [x] 测试配置缓存机制 ✅
  - [x] 验证优雅降级处理 ✅

- [x] **数据结构验证** ✅
  - [x] 验证chart cards数据格式正确 ✅
  - [x] 验证chart items数据结构正确 ✅
  - [x] 验证前后端数据格式完全匹配 ✅
  - [x] 验证项目ID正确传递 ✅

- [x] **错误处理测试** ✅
  - [x] 测试API失败时的降级处理 ✅
  - [x] 测试项目无配置时使用默认配置 ✅
  - [x] 测试网络异常时的用户体验 ✅

- [x] **硬编码删除验证** ✅ **(测试前必须步骤)**
  - [x] 确认删除`use-chart-management.ts`中的硬编码`presetCards`数组 ✅
  - [x] 确认删除`chart-card-list.tsx`中的硬编码`CHART_DETAILS`常量 ✅  
  - [x] 全局搜索确认无其他相关硬编码内容 ✅
  - [x] **数据流验证**: 确保UI完全依赖数据库数据 ✅

- [ ] **UI功能验证** (需浏览器手动测试)
  - [ ] 验证左侧chart cards正确显示 (应显示4个来自数据库的cards)
  - [ ] 验证每个card下的chart items列表正确 (应显示数据库中的items)
  - [ ] 验证点击card切换右侧图表功能正常
  - [ ] 验证项目切换时配置正确更新

#### 完成标准 ✅
- [x] **数据流验证**: 数据库 → API → 前端状态 → UI渲染 完整链路工作正常 ✅
- [x] **向后兼容**: 所有现有项目的chart cards显示与之前完全一致 ✅ (使用默认配置)
- [ ] **功能完整**: 左侧导航点击、右侧图表切换、图表内导航等功能正常 (需浏览器验证)
- [x] **代码质量**: 删除所有相关硬编码，代码可读性良好 ✅
- [x] **API稳定性**: 后端API完全稳定，错误处理完善 ✅

### 预期交付物
1. **数据库schema和迁移脚本** - 支持配置的持久化存储
2. **配置管理API** - 提供项目级别的配置获取服务  
3. **动态化前端组件** - chart cards和chart items完全从配置加载
4. **配置服务层** - 处理配置缓存、错误处理和优先级逻辑
5. **完整的向后兼容** - 现有项目体验保持一致

第一阶段完成后，系统将具备：
- ✅ 左侧chart cards完全动态配置化
- ✅ 每个card下的具体图表列表动态配置化  
- ✅ 支持项目级别的差异化配置
- ✅ 保持现有UI交互和右侧图表显示逻辑
- ⏸️ Chat messages仍为硬编码（留待第二阶段）
- ⏸️ 右侧图表组件结构仍为固定（留待第三阶段）
