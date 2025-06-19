# 产品市场分析Agent核心步骤

## 7步骤总览

1. **数据获取** - 通过爬虫API获取Amazon产品和评论数据

   以上对应前端页面的tab1- **爬虫步骤** 完成的任务**backend/scraping**
2. **业务建模** - 将原始数据转换为具有业务意义的结构化数据
3. **数据存储** - 存储到数据库供Agent访问
   **2和3这2步要交接给你做了**

   以下对应前端页面的tab4- **agent-chat步骤** 完成的任务**backend/agent**
4. **需求定义** - 定义市场分析的核心图表和维度需求
5. **数据验证** - Agent确认现有数据能否满足分析需求
6. **图表实现** - Agent生成React图表代码
7. **动态渲染** - 在Chat界面实时展示分析图表 -

## Source File Structure & Step Mapping

### Core Architecture

```
leviton-agent/
├── backend/                    # Python FastAPI backend
│   ├── scraping/              # Step 1: Data Collection
│   ├── core/                  # Steps 2-3: Business Modeling & Data Storage
│   ├── product_segmentation/  # Product Market Segmentation Engine
│   ├── agent/                 # Steps 4-6: Agent Analysis & Chart Generation
│   └── main.py               # API entry point
├── frontend/                  # React Next.js frontend
│   ├── src/components/chat/   # Step 7: Dynamic Rendering
│   ├── src/components/charts/ # Chart components
│   └── src/app/api/          # API routes
└── archive/                   # Legacy backend code
```

### Step-to-File Mapping

#### Step 1: Data Collection (数据获取)
**Primary Directory:** `backend/scraping/`
- `backend/scraping/orchestrator.py` - Main scraping coordinator
- `backend/scraping/products/scraper.py` - Amazon product scraping
- `backend/scraping/reviews/scraper.py` - Amazon review scraping
- `backend/scraping/common/amazon_api.py` - Amazon API integration
- `backend/scraping/common/result_processor.py` - Raw data processing

#### Step 2: Business Modeling (业务建模)
**Primary Directory:** `backend/core/services/` & `backend/product_segmentation/`
- `backend/core/services/data_import_service.py` - Data transformation service
- `backend/core/models/product_prompt.py` - Business data models
- `backend/product_segmentation/services/db_product_segmentation.py` - Market segmentation service
- `backend/product_segmentation/llm/product_segmentation_client.py` - LLM-driven segmentation

#### Step 3: Data Storage (数据存储)
**Primary Directory:** `backend/core/` & `backend/product_segmentation/`
- `backend/core/database/connection.py` - Database connection management
- `backend/core/repositories/amazon_product_repository.py` - Product data access
- `backend/core/repositories/amazon_review_repository.py` - Review data access
- `backend/product_segmentation/repositories/` - Segmentation data access
- `backend/product_segmentation/storage/` - LLM interaction storage

#### Step 4: Requirements Definition (需求定义)
**Primary Directory:** `backend/agent/services/`
- `backend/agent/services/product_prompt_service.py` - Analysis requirements service
- `backend/agent/prompts/agent-prompt-by-step.md` - Agent prompts
- `backend/agent/document/ai-gen-REQ/` - Analysis requirement templates

#### Step 5: Data Validation (数据验证)
**Primary Directory:** `backend/agent/tools/`
- `backend/agent/tools/product_review_tools.py` - Data validation tools
- `backend/agent/dependencies.py` - Agent dependencies and validation logic

#### Step 6: Chart Implementation (图表实现)
**Primary Directories:** `backend/agent/` & `frontend/src/components/charts/`
- `backend/agent/document/ai-gen-chartcode/` - Chart code generation prompts
- `frontend/src/components/charts/chart-renderer.tsx` - Chart rendering component
- `frontend/src/lib/chart-compiler.ts` - Chart code compilation
- `frontend/src/contexts/chart-context.tsx` - Chart state management

#### Step 7: Dynamic Rendering (动态渲染)
**Primary Directory:** `frontend/src/components/chat/`
- `frontend/src/components/chat/chat-interface.tsx` - Main chat interface
- `frontend/src/components/chat/message-list.tsx` - Message display
- `frontend/src/components/chat/message-item.tsx` - Individual message rendering
- `frontend/src/app/api/chat/route.ts` - Chat API endpoint

### Supporting Components

#### Frontend Tabs
- `frontend/src/components/tabs/data-import-tab.tsx` - Steps 1-3 UI
- `frontend/src/components/tabs/analysis-tab.tsx` - Steps 4-6 UI
- `frontend/src/components/tabs/data-confirmation-tab.tsx` - Step 5 UI

#### Configuration & Utilities
- `backend/config.py` - Backend configuration
- `frontend/src/lib/utils.ts` - Frontend utilities
- `frontend/src/lib/types.ts` - TypeScript type definitions

## 前期数据准备阶段

### 第一步：数据获取

**目标**：获取Amazon产品数据

**流程**：

- 输入：Amazon产品链接
- 输出：产品基本信息、销量数据、评论情况
- 扩展：根据产品类目获取该类目TOP 10/100/200产品数据

**成本**：200个产品/月全量数据约$1

**难点**：

- 找到稳定可靠的爬虫平台
- 确保数据完整性和实时性
- 产品分类粒度要细化准确

### 第二步：业务化数据建模

**目标**：将原始数据转换为具有业务意义的结构化数据

**输入**：第一步API返回的JSON数据
**核心输出**：

- 产品基础信息表（产品主表）
- 评论方面分类标准定义（统一分类字典）
- 产品类型细分映射（精确产品分类）
- 评论智能分析结果（非结构化评论→结构化洞察）
- 产品综合视图（基础信息+分类结果合并）

**业务价值**：

- 建立评论的三维分析体系（物理属性/性能表现/使用场景）
- 构建产品的细分市场分类体系
- 将海量评论文本转化为可分析的结构化洞察

**难点**：

- AI驱动的评论语义理解和分类准确性
- 建立通用且细致的评论分析维度体系
- 产品细分类别的准确识别和映射
- 多数据源的业务逻辑关联和一致性保证

### 第三步：数据存储

**目标**：将结构化数据存储到数据库，让Agent能够访问

**输入**：第二步的结构化数据文件
**输出**：3个Supabase数据库表

- 产品基础信息宽表
- 原始产品评论详情表
- 按产品meta分类的产品评论表

**考虑**：是否在第二步直接输出到数据库关系，而非中间文件

**难点**：

- 数据库表结构设计
- 数据关系建模
- 批量导入性能优化

## 实时分析阶段

### 第四步：分析需求定义

**目标**：给出核心的市场分析产品需求

**输入**：产品链接
**输出**：

- 图表举例和定义
- **数据需求清单**（第五步验证用）

**核心分析维度**：

#### 市场格局分析

- **品牌市场份额**：按销量/销售额统计
- **头部产品排名**：按销量/销售额/价格排序
- **产品市场占有率**：单品在类目中的份额

#### 产品结构分析

- **产品细分构成**：类目下各子品类占比
- **价格区间分布**：不同价格段的产品分布
- **品牌产品矩阵**：各品牌的产品线分析

#### 用户行为分析

- **购买模式**：复购vs一次性购买
- **用户痛点**：基于评论的问题分析
- **用户偏好**：正面反馈和主要应用场景
- **市场空白**：未满足的用户需求

#### 图表需求定义

| 分析维度     | 图表类型    | X轴      | Y轴         | 数据来源       |
| ------------ | ----------- | -------- | ----------- | -------------- |
| 品牌市场份额 | 饼图/柱状图 | 品牌名称 | 市场份额%   | 品牌销量汇总表 |
| 头部产品排名 | 横向柱状图  | 产品名称 | 销量/销售额 | 产品销量排序表 |
| 价格分布     | 直方图      | 价格区间 | 产品数量    | 产品价格统计表 |
| 产品细分构成 | 堆叠柱状图  | 子类目   | 销量占比    | 类目销量汇总表 |
| 用户评分趋势 | 折线图      | 时间     | 平均评分    | 评论时间序列表 |
| 痛点词云     | 词云图      | 关键词   | 频次        | 负面评论分析表 |

**难点**：

- 维度标准化和通用性设计
- 图表类型与数据的最佳匹配
- 动态维度扩展能力

### 第五步：数据验证Agent

**目标**：确认数据是否满足实现需求

**核心功能**：

- 数据可用性检查
- 数据分布特征分析
- 数据预处理逻辑
- 多表关联查询
- 数据聚合计算

**输出方案**：

- 预构建数据表（考虑存储成本）
- 实时查询+缓存机制
- 索引映射关系存储

**难点**：

- 复杂SQL查询的自动生成
- 数据一致性保证
- 查询性能优化
- 存储空间vs查询速度权衡

### 第六步：图表实现Agent

**目标**：具体实现图表需求

**输入**：

- 第四步的图表制作要求
- 第五步的数据集

**输出**：包装在JSON中的React Chart组件代码

**技术栈**：React + Chart.js/D3.js/Recharts

**难点**：

- 代码模板的标准化
- 图表样式的一致性
- 动态数据绑定
- 错误处理和兜底方案

### 第七步：动态渲染

**目标**：在Chat中动态渲染图表，让用户看到分析结果

**功能**：

- 动态组件加载
- 图表交互功能
- 数据刷新机制
- 导出和分享功能

**难点**：

- 动态代码执行的安全性
- 组件间的数据联动
- 页面性能优化
- 移动端适配
