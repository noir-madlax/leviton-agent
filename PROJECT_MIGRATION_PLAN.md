# Leviton Agent 数据架构迁移项目执行计划

## 📋 项目概述

### 项目背景

当前系统存在数据范围不一致问题：

- **Step 2 (Data Scope Selection)**: 用户通过品牌、类别等条件筛选特定产品范围，生成项目
- **Step 3 (Analysis)**: 显示全量数据分析，未应用Step 2的筛选范围，导致分析结果不准确

### 核心问题

1. **数据隔离缺失**: Step 2的筛选结果没有传递给Step 3
2. **项目作用域不明确**: 项目配置未应用到后续分析
3. **查询分散**: 前端有14个独立的数据库查询，难以统一管理和过滤

### 解决目标

1. **数据一致性**: Step 3的所有分析必须基于Step 2筛选的产品范围
2. **架构迁移**: 从前端直接操作supabase迁移到后端API架构
3. **查询统一**: 通过ASIN列表过滤确保14个SQL查询100%应用项目范围
4. **扩展性**: 为后续集成product_segment工作流做准备

## 🏗️ 架构设计

### 当前前端架构问题

```typescript
// 现状：前端直接查询supabase
export class DatabaseService {
  async getBrandCategoryRevenue() {
    // 问题：直接全量查询，无项目范围过滤
    const { data } = await supabase.from('product_wide_table').select(...)
  }
  // ...其他13个查询方法，都存在同样问题
}
```

### 目标后端架构

```
backend/
├── projects/                    # 第一阶段：项目管理模块
│   ├── __init__.py
│   ├── api.py                  # FastAPI路由 (/api/v1/projects)
│   ├── models.py               # Project, ProjectConfig等数据模型
│   ├── services/
│   │   ├── __init__.py
│   │   ├── project_service.py  # 项目CRUD服务
│   │   └── workflow_service.py # 工作流集成服务（为后续扩展）
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── project_repository.py
│   └── workflows/              # 为后续product_segment集成预留
│       ├── __init__.py
│       └── project_creation_workflow.py
└── dashboard/                   # 第二阶段：仪表板数据模块
    ├── __init__.py
    ├── api.py                  # FastAPI路由 (/api/v1/dashboard)
    ├── models.py               # 响应模型定义
    ├── services/
    │   ├── __init__.py
    │   ├── base_service.py     # 统一查询构建器（核心）
    │   ├── brand_analysis_service.py      # 替代getBrandCategoryRevenue
    │   ├── product_analysis_service.py    # 替代getProductAnalysisData
    │   ├── pricing_analysis_service.py    # 替代getPricingAnalysisData
    │   ├── market_insights_service.py     # 替代getMarketInsightsData
    │   ├── package_preference_service.py  # 替代getPackagePreferenceData
    │   ├── review_insights_service.py     # 替代getReviewInsightsData
    │   ├── competitor_analysis_service.py # 替代getCompetitorAnalysisData
    │   └── review_data_service.py         # 替代getAllReviewData
    └── repositories/
        ├── __init__.py
        └── dashboard_repository.py
```

### 核心设计原则

#### 1. 统一查询构建器 (BaseDashboardService)

```python
class BaseDashboardService:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.filtered_asins = self._get_project_asins()
  
    def _query_products(self, base_query: str, params: dict = None) -> str:
        """统一的ASIN过滤查询构建器 - 防止遗漏过滤"""
        if not self.filtered_asins:
            raise ValueError("Project ASIN list is empty")
      
        # 自动添加ASIN过滤条件
        filtered_query = f"""
        WITH filtered_products AS (
            SELECT * FROM ({base_query}) 
            WHERE asin = ANY(%(filtered_asins)s)
        )
        SELECT * FROM filtered_products
        """
        return filtered_query
```

#### 2. 项目数据范围管理

```sql
-- 扩展projects表结构
ALTER TABLE projects ADD COLUMN selected_product_asins TEXT[];

-- 示例项目数据
INSERT INTO projects (name, selected_product_asins, ...) 
VALUES ('Leviton Smart Switch Analysis', 
        ARRAY['B07ABC123', 'B08DEF456', 'B09GHI789'], ...);
```

## 📈 分阶段实施计划

### 第一阶段：Projects后端模块 (优先级：HIGH)

#### 目标

替代前端直接操作supabase的项目创建逻辑

#### 实施步骤

1. **创建基础架构**

   - [ ] 创建 `backend/projects/` 目录结构
   - [ ] 添加FastAPI依赖和路由配置
   - [ ] 定义数据模型 (Project, ProjectConfig)
2. **实现核心服务**

   - [ ] ProjectService: 项目CRUD操作
   - [ ] ProjectRepository: 数据库访问层
   - [ ] 扩展projects表，添加selected_product_asins字段
3. **API接口开发**

   ```python
   POST /api/v1/projects/create
   {
       "name": "项目名称",
       "selected_categories": ["Smart Switches"],
       "selected_brands": ["Leviton", "GE"],
       "selected_sources": ["amazon"],
       "selected_product_asins": ["B07ABC123", "B08DEF456"]
   }
   ```
4. **前端集成**

   - [ ] 修改DataConfirmationTab调用后端API
   - [ ] 移除前端supabase直接操作代码
   - [ ] 保持UI交互不变

#### 验证标准

- [ ] 项目创建成功率100%
- [ ] ASIN列表正确保存到数据库
- [ ] 前端UI功能与原有完全一致

### 第二阶段：Dashboard后端模块 (优先级：HIGH)

#### 目标

将前端14个数据查询迁移到后端，实现统一的ASIN过滤

#### 当前需要迁移的查询清单

```typescript
// frontend/src/components/analysis-db/data/database-service.ts
1. getBrandCategoryRevenue()           // Line 128 - 1个查询
2. getProductAnalysisData()            // Line 179 - 1个查询  
3. getPricingAnalysisData()            // Line 276 - 1个查询
4. getMarketInsightsData()             // Line 398 - 1个查询
5. getPackagePreferenceData()          // Line 504 - 1个查询
6. getReviewInsightsData()             // Line 630 - 1个查询
7. getCompetitorAnalysisData()         // Line 792 - 3个查询
8. getAllReviewData()                  // Line 1088 - 1个查询
9. getDataConfirmationData()           // Line 1134 - 2个查询
```

#### 实施策略：逐个Chart迁移

**每个Chart迁移包含4个步骤：**

1. **后端服务开发**

   - 创建对应的Service类 (继承BaseDashboardService)
   - 复制前端SQL查询逻辑
   - 应用统一的ASIN过滤
   - 添加单元测试
2. **API接口开发**

   - 创建RESTful端点
   - 定义响应模型
   - 添加错误处理
3. **前端适配**

   - 修改数据获取逻辑调用后端API
   - 确保数据格式兼容
   - 保持UI渲染不变
4. **验证测试**

   - 对比前后端数据结果一致性
   - 确认ASIN过滤生效
   - 性能测试

#### 迁移优先级顺序

```
优先级1 (核心图表)：
- BrandAnalysisService (getBrandCategoryRevenue)
- ProductAnalysisService (getProductAnalysisData)

优先级2 (主要分析)：
- PricingAnalysisService (getPricingAnalysisData)  
- MarketInsightsService (getMarketInsightsData)
- ReviewInsightsService (getReviewInsightsData)

优先级3 (辅助功能)：
- PackagePreferenceService (getPackagePreferenceData)
- CompetitorAnalysisService (getCompetitorAnalysisData)
- ReviewDataService (getAllReviewData)
```

## 🔧 技术实现细节

### 统一过滤机制

```python
# base_service.py - 核心过滤逻辑
class BaseDashboardService:
    def _get_project_asins(self) -> List[str]:
        """从项目配置获取ASIN列表"""
        project = self.project_repo.get_by_id(self.project_id)
        if not project or not project.selected_product_asins:
            raise ValueError(f"Project {self.project_id} has no ASIN filter")
        return project.selected_product_asins
  
    def _apply_asin_filter(self, query: str) -> str:
        """自动应用ASIN过滤 - 防止遗漏"""
        return f"""
        SELECT * FROM ({query}) AS base_query 
        WHERE base_query.asin = ANY(%(filtered_asins)s)
        """
```

### API响应格式标准

```python
# 保持与前端期望的数据格式100%一致
class BrandAnalysisResponse(BaseModel):
    data: List[BrandAnalysisItem]
    metadata: dict
    total_count: int
    project_id: str
    filtered_asin_count: int  # 新增：显示过滤范围
```

### 错误处理标准

```python
# 统一的错误响应
class APIError(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None

# 例如：ASIN过滤失败
{
    "error_code": "INVALID_PROJECT_SCOPE", 
    "message": "Project has no product ASIN filter defined",
    "details": {"project_id": "proj_123"}
}
```

## 📝 进度追踪

### 当前状态: ✅ 第一阶段完成

- ✅ 需求分析完成
- ✅ 架构设计完成
- ✅ 实施计划制定完成
- ✅ **第一阶段完成**: Projects后端模块开发完成
- ⏳ **下一步**: 开始第二阶段 - Dashboard后端模块开发

## 📈 最新进度 (更新日期: 2024-12-23)

### 第一阶段已完成 ✅
- ✅ Projects后端模块架构搭建
- ✅ ProjectService和ProjectRepository实现
- ✅ FastAPI路由配置 (/api/v1/projects)
- ✅ 前端API调用迁移 (DataConfirmationTab)
- ✅ 环境变量配置优化
- ✅ 项目创建功能验证通过
- ✅ 项目表中已有数据

### 第一阶段技术实现详情

#### 后端实现
1. **Projects模块结构**
   ```
   backend/projects/
   ├── __init__.py
   ├── api.py                  # FastAPI路由
   ├── models.py               # 数据模型
   └── services/
       ├── __init__.py
       └── project_service.py  # 核心业务逻辑
   ```

2. **核心API端点**
   ```python
   GET  /api/v1/projects/data-confirmation  # 获取数据确认信息
   POST /api/v1/projects/create             # 创建项目
   GET  /api/v1/projects/                   # 列出项目
   GET  /api/v1/projects/{project_id}       # 获取项目详情
   ```

3. **关键实现细节**
   - 修复了Supabase Python客户端查询语法：`not_('category', 'is', None)` → `neq('category', None)`
   - 实现了完整的项目CRUD操作
   - 添加了项目过滤器配置保存

#### 前端适配
1. **API调用迁移**
   - 从直接Supabase调用迁移到后端API调用
   - 使用环境变量 `NEXT_PUBLIC_BACKEND_URL` 配置API基础URL
   - 保持原有UI和交互逻辑不变

2. **具体修改文件**
   ```
   frontend/src/components/tabs/data-confirmation-tab.tsx
   - loadInitialData(): 使用 ${API_BASE_URL}/api/v1/projects/data-confirmation
   - handleFilterData(): 使用 ${API_BASE_URL}/api/v1/projects/data-confirmation?params
   - handleConfirmSelection(): 使用 ${API_BASE_URL}/api/v1/projects/create
   ```

3. **环境变量配置**
   ```
   frontend/.env.local
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

#### 验证结果
- ✅ API返回正确数据：512个产品，2个类别，81个品牌
- ✅ 前端HTTP 404错误已解决
- ✅ 项目创建功能正常，数据已保存到数据库
- ✅ Step 2数据范围选择功能完全正常

### 发现的问题及解决方案
- 🐛 **Supabase查询语法错误**: `not_()` 方法语法不正确
  - 解决方案：使用 `neq()` 方法替代
- 🐛 **前端API代理缺失**: Next.js没有配置后端代理
  - 解决方案：使用环境变量配置完整API URL，避免代理复杂性
- 🐛 **路由注册冲突**: FastAPI路由前缀重复
  - 解决方案：统一路由前缀配置

### 技术笔记
- **关键架构决策**: 选择环境变量方案而非Next.js代理，提高部署灵活性
- **Supabase客户端**: Python客户端语法与JavaScript客户端有差异，需要注意
- **API设计**: 保持与前端期望的数据格式100%兼容，降低迁移风险

### 下一步计划
- ⏳ **第二阶段启动**: Dashboard后端模块开发
- ⏳ **优先迁移**: BrandAnalysisService (getBrandCategoryRevenue)
- ⏳ **架构搭建**: 创建BaseDashboardService统一过滤机制

### 进度更新模板

```markdown
## 📈 最新进度 (更新日期: YYYY-MM-DD)

### 已完成
- ✅ 任务描述

### 进行中  
- 🔄 任务描述 (完成度: XX%)

### 下一步
- ⏳ 任务描述

### 发现的问题
- 🐛 问题描述及解决方案

### 技术笔记
- 重要的实现细节或决策记录
```

## 🎯 验收标准

### 第一阶段验收 (Projects模块) ✅

- [x] 项目创建API功能正常
- [x] ASIN列表正确保存和获取
- [x] 前端项目创建流程无变化
- [x] 数据库schema扩展成功

### 第二阶段验收 (Dashboard模块)

- [ ] 所有14个查询都迁移到后端
- [ ] 每个查询都应用了ASIN过滤
- [ ] 前端数据展示与原有100%一致
- [ ] API响应性能满足要求 (<2s)
- [ ] 错误处理覆盖所有异常场景

### 最终验收

- [ ] Step 2筛选的产品范围完全应用到Step 3分析
- [ ] 无数据泄露：分析结果只基于筛选范围
- [ ] 系统性能无明显下降
- [ ] 代码质量：测试覆盖率>80%

## 🚨 风险与注意事项

### 技术风险

1. **查询性能**: ASIN IN条件可能影响大量数据查询性能
2. **数据一致性**: 前后端数据格式必须完全匹配
3. **并发控制**: 多用户同时访问同一项目的处理

### 实施风险

1. **功能回归**: 迁移过程可能影响现有功能
2. **上下文丢失**: 跨session开发可能丢失技术细节
3. **测试覆盖**: 14个查询的回归测试工作量大

### 缓解措施

1. **分阶段上线**: 每个阶段独立验收后再进行下一阶段
2. **详细文档**: 记录所有实现细节和决策原因
3. **全面测试**: 建立自动化测试确保数据一致性

## 📚 相关文档链接

- `frontend/src/components/analysis-db/data/database-service.ts` - 需要迁移的查询源码
- `frontend/src/components/tabs/data-confirmation-tab.tsx` - 项目创建前端逻辑
- `backend/core/database/connection.py` - 数据库连接配置
- `backend/requirements.txt` - 后端依赖管理
- `backend/main.py` - FastAPI应用入口，需要添加新的路由
- `backend/product_segment/` - 后续需要集成的产品细分模块
- `backend/product_segmentation/` - 后续需要集成的产品分段模块

## 🗃️ 数据库结构信息

### 当前projects表结构
```sql
-- 现有字段（需要确认）
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    selected_categories TEXT[],
    selected_brands TEXT[],
    selected_sources TEXT[]
);

-- 需要添加的字段
ALTER TABLE projects ADD COLUMN selected_product_asins TEXT[];
```

### 核心数据表关系
```sql
-- 产品数据主表
product_wide_table (
    asin VARCHAR PRIMARY KEY,  -- 核心过滤字段
    brand VARCHAR,
    category VARCHAR,
    source VARCHAR,
    ...
)

-- 评论数据表  
amazon_reviews (
    asin VARCHAR,  -- 关联产品
    review_id VARCHAR,
    ...
)
```

## 🔍 关键技术决策记录

### 1. 为什么选择ASIN作为过滤字段？
- **唯一性**: ASIN是Amazon产品的唯一标识符
- **覆盖性**: 所有相关数据表都包含asin字段
- **精确性**: 比品牌+类别组合更精确，避免边界情况

### 2. 为什么使用统一查询构建器？
- **防遗漏**: 从架构层面确保所有查询都应用过滤
- **维护性**: 过滤逻辑集中管理，便于调试和优化
- **扩展性**: 未来可以支持更复杂的过滤条件

### 3. 为什么分两个阶段？
- **风险控制**: 分阶段上线降低影响范围
- **资源分配**: 可以并行开发，提高效率
- **验证充分**: 每个阶段独立验收，确保质量

---

## 💬 开发者交接说明

### 给后续开发者的重要提醒

1. **必须阅读**: 这个文档包含完整的需求背景和技术方案
2. **验证步骤**: 每个Chart迁移后都要对比前后端数据结果
3. **测试重点**: ASIN过滤是核心，必须确保100%生效
4. **代码复用**: 优先使用BaseDashboardService统一过滤逻辑
5. **进度更新**: 每次工作后更新本文档的进度追踪部分

### 快速开始指令

```bash
# 1. 查看当前项目状态
cd /Users/rigel/project/leviton/leviton-agent
git status

# 2. 开始第一阶段开发
mkdir -p backend/projects/{services,repositories,workflows}
touch backend/projects/{__init__.py,api.py,models.py}

# 3. 运行现有测试确保基线稳定  
cd backend && python -m pytest test_structure_only.py
```

## 🚀 具体实施检查清单

### 第一阶段开发检查清单

#### 环境准备
- [ ] 确认FastAPI和相关依赖已安装
- [ ] 确认数据库连接正常
- [ ] 确认现有projects表结构

#### 后端开发
- [ ] 创建`backend/projects/`目录结构
- [ ] 实现ProjectService和ProjectRepository
- [ ] 添加数据库schema扩展脚本
- [ ] 创建FastAPI路由和模型
- [ ] 编写单元测试

#### 前端适配
- [ ] 修改DataConfirmationTab的supabase调用
- [ ] 添加API调用逻辑
- [ ] 保持现有UI和交互不变
- [ ] 测试项目创建流程

#### 验证测试
- [ ] 对比前后端项目创建结果
- [ ] 确认ASIN列表正确保存
- [ ] 性能测试：项目创建响应时间
- [ ] 错误处理测试

### 第二阶段开发检查清单（按Chart优先级）

#### 优先级1：核心图表
- [ ] BrandAnalysisService开发和测试
- [ ] ProductAnalysisService开发和测试
- [ ] 前端API调用适配
- [ ] 数据一致性验证

#### 优先级2：主要分析
- [ ] PricingAnalysisService开发和测试
- [ ] MarketInsightsService开发和测试
- [ ] ReviewInsightsService开发和测试
- [ ] 前端API调用适配
- [ ] 数据一致性验证

#### 优先级3：辅助功能
- [ ] 其余Service开发和测试
- [ ] 前端API调用适配
- [ ] 完整的端到端测试

---

**文档版本**: v1.1
**创建时间**: 2024-12-23
**最后更新**: 2024-12-23
**负责人**: Leviton Agent Project Team

---

## 🎯 第二阶段开始指南

### 立即开始第二阶段的建议

基于第一阶段的成功经验，建议按以下顺序开始第二阶段：

#### 1. 创建Dashboard模块基础架构 (优先级：CRITICAL)

```bash
# 创建目录结构
mkdir -p backend/dashboard/{services,repositories}
touch backend/dashboard/{__init__.py,api.py,models.py}
touch backend/dashboard/services/{__init__.py,base_service.py}
touch backend/dashboard/repositories/{__init__.py,dashboard_repository.py}
```

#### 2. 实现BaseDashboardService (优先级：HIGH)

这是整个第二阶段的核心，必须先实现：

```python
# backend/dashboard/services/base_service.py
class BaseDashboardService:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.filtered_asins = self._get_project_asins()
    
    def _get_project_asins(self) -> List[str]:
        """从项目配置获取ASIN列表 - 核心过滤逻辑"""
        # 调用ProjectService获取项目的selected_product_asins
        
    def _apply_asin_filter(self, query: str) -> str:
        """自动应用ASIN过滤 - 防止遗漏"""
        # 确保所有查询都包含 WHERE asin = ANY(%(filtered_asins)s)
```

#### 3. 优先迁移核心图表 (优先级：HIGH)

按照文档中的优先级顺序：

1. **BrandAnalysisService** - 替代 `getBrandCategoryRevenue()`
2. **ProductAnalysisService** - 替代 `getProductAnalysisData()`

#### 4. 每个Service的标准开发流程

```
1. 复制前端SQL查询逻辑到后端Service
2. 继承BaseDashboardService确保ASIN过滤
3. 创建对应的API端点
4. 修改前端调用后端API
5. 验证数据一致性
```

### 关键成功因素

1. **复用第一阶段经验**：环境变量配置、API调用模式已验证有效
2. **统一过滤机制**：BaseDashboardService是核心，必须先实现
3. **逐个验证**：每迁移一个图表就验证数据一致性
4. **保持UI不变**：前端只改API调用，UI逻辑保持不变

### 下一个Chat的快速启动命令

```bash
# 1. 检查当前状态
cd /Users/rigel/project/leviton/leviton-agent
git status

# 2. 查看需要迁移的前端查询
cat frontend/src/components/analysis-db/data/database-service.ts | grep -n "async get"

# 3. 开始Dashboard模块开发
mkdir -p backend/dashboard/{services,repositories}

# 4. 检查项目表数据
# 通过Supabase或直接SQL查询确认项目数据结构
```

### 重要提醒

- 📋 **必读文档**：下一个Chat开始时先阅读这个文档的第二阶段部分
- 🔍 **数据验证**：每个Service都要对比前后端返回的数据格式
- 🚀 **渐进式迁移**：一次只迁移一个图表，确保稳定性
- 📊 **ASIN过滤验证**：这是核心功能，必须确保100%生效
