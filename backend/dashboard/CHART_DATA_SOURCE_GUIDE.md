# Chart Data Source Guide - 图表数据来源指南

## 📋 概述

本文档详细说明了Dashboard中每个图表的数据来源、运算逻辑和数据库表映射关系。所有图表数据都经过项目ASIN过滤，确保数据隔离。

## 🗄️ 核心数据表结构

### 主要数据表

**产品主表 (product_wide_table)** - 核心数据源
- platform_id: 产品ASIN，是所有图表的核心过滤字段
- brand: 品牌名称，如"Leviton"、"Lutron"等
- category: 产品类别，主要包括"Dimmer Switches"和"Light Switches"
- title: 产品标题，包含完整的产品名称
- price_usd: 产品价格，以美元为单位
- estimated_revenue: 预估收入，用于收入相关分析
- monthly_sales_volume: 月销量，用于销量分析
- reviews_count: 评论总数，用于评论相关统计
- pack_count: 包装数量，用于包装偏好分析
- product_segment: 产品细分，用于市场洞察分析
- source: 数据来源，固定为"amazon"

**评论分析表 (product_review_analysis)** - Review Insights数据源
- product_id: 产品ASIN，对应产品主表的platform_id
- standardized_aspect: 标准化的评论方面，如"installation_difficulty"、"smart_connectivity"等
- aspect_category: 方面类别，包括performance(性能)、physical(物理)、usability(可用性)等
- sentiment: 情感分析结果，包括positive(正面)、negative(负面)、neutral(中性)
- review_count: 该方面的评论数量
- use_case: 使用场景，如"bedroom"、"kitchen"、"outdoor"等

**产品评论表 (product_reviews)** - Competitor Analysis数据源
- asin: 产品ASIN
- rating: 评分，1-5星
- review_text: 评论内容文本
- review_date: 评论日期

## 📊 图表数据来源详解

### 1. Brand Analysis (品牌分析)
**API端点**: `/api/v1/dashboard/brand-analysis`  
**服务类**: `BrandAnalysisService`  
**主要数据表**: `product_wide_table`

#### 数据获取逻辑
这个图表展示各品牌在不同产品类别中的收入和销量表现。

**数据处理步骤**：
1. 从产品主表中获取brand、category、estimated_revenue、monthly_sales_volume字段
2. 只查询Amazon来源的数据，排除无类别的产品
3. 应用项目ASIN过滤，确保只显示当前项目范围内的产品
4. 按brand和category进行数据聚合：
   - 对于"Dimmer Switches"类别，累加到品牌的dimmerRevenue和dimmerVolume
   - 对于"Light Switches"类别，累加到品牌的switchRevenue和switchVolume
5. 跳过estimated_revenue为0或空值的记录

**运算逻辑**：
- 每个品牌有4个指标：dimmerRevenue、dimmerVolume、switchRevenue、switchVolume
- estimated_revenue和monthly_sales_volume都是简单的累加求和
- 如果某个产品的estimated_revenue或monthly_sales_volume为空，则按0处理

#### 返回数据结构
返回一个品牌列表，每个品牌包含：
- brand: 品牌名称
- dimmerRevenue: 调光开关总收入
- switchRevenue: 普通开关总收入  
- dimmerVolume: 调光开关总销量
- switchVolume: 普通开关总销量

### 2. Product Analysis (产品分析)
**API端点**: `/api/v1/dashboard/product-analysis`  
**服务类**: `ProductAnalysisService`  
**主要数据表**: `product_wide_table`

#### 数据获取逻辑
这个图表展示项目范围内的产品详细信息，包括价格收入分析和热门产品排名。

**数据处理步骤**：
1. 从产品主表中获取产品的完整信息：platform_id、title、brand、category、price_usd、estimated_revenue、monthly_sales_volume、reviews_count
2. 应用基础过滤和项目ASIN过滤
3. 按category分组，每个类别下包含该类别的所有产品
4. 生成estimated_revenue排名前20的产品列表，跨所有类别

**运算逻辑**：
- 价格收入分析：按category分组显示，每个产品保留原始的price_usd、estimated_revenue、monthly_sales_volume数据
- 热门产品排名：将所有产品按estimated_revenue从高到低排序，取前20个
- 数据清洗：price_usd、estimated_revenue、monthly_sales_volume、reviews_count的空值都处理为0

#### 返回数据结构
返回包含两个部分的数据：
- priceVsRevenue: 按类别分组的产品列表，每个产品包含platform_id、title、brand、price_usd、estimated_revenue、monthly_sales_volume、reviews_count
- topProducts: estimated_revenue排名前20的产品列表，格式与priceVsRevenue中的产品相同

### 3. Pricing Analysis (定价分析)
**API端点**: `/api/v1/dashboard/pricing-analysis`  
**服务类**: `PricingAnalysisService`  
**主要数据表**: `product_wide_table`

#### 数据获取逻辑
这个图表分析项目范围内产品的价格分布情况，包括按类别和按品牌的价格统计。

**数据处理步骤**：
1. 从产品主表中获取brand、category、price_usd、pack_count字段
2. 应用基础过滤和项目ASIN过滤
3. 计算两种价格：
   - SKU价格：产品的原始price_usd
   - 单价：price_usd除以pack_count，得出单个产品的价格
4. 按category分组收集价格数据
5. 按brand分组收集价格数据
6. 为每组价格数据计算统计指标

**运算逻辑**：
- 单价计算：单价 = price_usd ÷ pack_count，如果pack_count为0则单价等于price_usd
- 价格统计包括6个指标：最小值、第一四分位数(25%)、中位数(50%)、平均值、第三四分位数(75%)、最大值
- 跳过price_usd为0或空值的产品
- 如果某个分组没有价格数据，所有统计指标都返回0

#### 返回数据结构
返回包含两个部分的价格分布数据：
- priceDistribution: 按category的价格分布，每个类别包含SKU价格列表、单价列表和统计指标
- brandPriceDistribution: 按brand的价格分布，格式与类别分布相同

### 4. Market Insights (市场洞察)
**API端点**: `/api/v1/dashboard/market-insights`  
**服务类**: `MarketInsightsService`  
**主要数据表**: `product_wide_table`

#### 数据获取逻辑
这个图表分析项目范围内产品按细分市场的收入分布，帮助了解不同细分市场的表现。

**数据处理步骤**：
1. 从产品主表中获取category、product_segment、estimated_revenue、monthly_sales_volume、platform_id字段
2. 应用基础过滤和项目ASIN过滤
3. 按category和product_segment进行双重分组聚合
4. 跳过estimated_revenue为0的产品，只分析有收入的产品
5. 计算每个细分的总estimated_revenue、总monthly_sales_volume、产品数量
6. 最终按主要类别(调光开关、普通开关)分组返回

**运算逻辑**：
- 细分聚合：相同category下的相同product_segment的产品，其estimated_revenue和monthly_sales_volume进行累加，产品数量计数
- 收入过滤：只包含有estimated_revenue数据的产品，estimated_revenue为0或空的产品被排除
- 分类整理：最终结果按"Dimmer Switches"和"Light Switches"两大类别组织
- 未知细分：如果product_segment为空，则标记为"Unknown"

#### 返回数据结构
返回按主要类别分组的细分收入数据：
- segmentRevenue.dimmerSwitches: 调光开关的各个细分市场数据
- segmentRevenue.lightSwitches: 普通开关的各个细分市场数据
- 每个细分包含：segment名称、总revenue、总volume、产品数量

### 5. Package Preference (包装偏好)
**API端点**: `/api/v1/dashboard/package-preference`  
**服务类**: `PackagePreferenceService`  
**主要数据表**: `product_wide_table`

#### 数据获取逻辑
这个图表分析消费者对不同包装大小的偏好，特别是同一产品不同包装选项的表现对比。

**数据处理步骤**：
1. 从产品主表中获取title、brand、category、pack_count、estimated_revenue、monthly_sales_volume字段
2. 应用基础过滤和项目ASIN过滤
3. 通过title提取基础产品名称，移除包装相关的词汇
4. 按基础产品名称分组，收集该产品的所有包装变体
5. 筛选出有多个包装选项的产品进行对比分析
6. 按category统计整体的包装分布情况

**运算逻辑**：
- 基础产品名提取：使用正则表达式移除title中的"3-pack"、"single"、"individual"等包装相关词汇
- 包装变体分组：相同基础产品名的不同pack_count归为一组
- 同产品对比：只保留有2个或以上包装选项的产品，便于对比分析
- 包装分布统计：按pack_count(1个装、3个装、5个装等)统计产品数量和estimated_revenue分布
- 分类统计：分别统计调光开关和普通开关的包装偏好

#### 返回数据结构
返回包含多个维度的包装偏好数据：
- sameProductComparison: 同产品不同包装的对比，包含产品名称和各包装变体的estimated_revenue、monthly_sales_volume
- packageDistribution: 整体包装分布，按pack_count统计
- dimmerSwitches: 调光开关的包装分布
- lightSwitches: 普通开关的包装分布

### 6. Review Insights (评论洞察)
**API端点**: `/api/v1/dashboard/review-insights`  
**服务类**: `ReviewInsightsService`  
**主要数据表**: `product_review_analysis`

#### 数据获取逻辑
这是最复杂的图表，从评论分析数据中提取三种关键洞察：客户痛点、客户喜好、未满足需求。

**数据处理步骤**：
1. 从评论分析表中获取项目范围内产品的所有评论分析数据
2. 数据包含：product_id、standardized_aspect、aspect_category、sentiment、review_count、use_case
3. 分别处理三种不同类型的洞察分析

**运算逻辑**：

**1. 痛点分析(Pain Points)**：
- 筛选条件：只处理sentiment为negative且aspect_category属于性能、物理、可用性类别的评论
- 聚合方式：按standardized_aspect和aspect_category组合进行分组，累加review_count
- 严重程度计算：总review_count除以100并标准化到0-1范围，最大值为1
- 影响产品数：统计提到该痛点的不同product_id数量
- 排序规则：按严重程度从高到低排序，返回前15个最严重的痛点

**2. 客户喜好分析(Customer Likes)**：
- 筛选条件：只处理sentiment为positive的评论，不限aspect_category
- 聚合方式：按standardized_aspect和aspect_category组合进行分组，累加review_count
- 满意度等级：根据review_count分级，>50次为High，20-50次为Medium，<20次为Low
- 排序规则：按review_count从高到低排序，返回前10个最受欢迎的特征

**3. 未满足需求分析(Underserved Use Cases)**：
- 筛选条件：只处理有use_case的评论，排除空值和"null"
- 聚合方式：按use_case和standardized_aspect组合进行分组
- 缺口程度计算：review_count除以30并标准化到0-1范围，表示需求缺口的严重程度
- 排序规则：按缺口程度从高到低排序，返回前8个最重要的机会点

#### 返回数据结构
返回包含三个分析维度的洞察数据：
- painPoints: 痛点列表，每个痛点包含aspect、category、severity、frequency、impactedProducts、type
- customerLikes: 客户喜好列表，每个特征包含feature、category、frequency、satisfactionLevel
- underservedUseCases: 未满足需求列表，每个需求包含useCase、productAttribute、gapLevel、mentionCount

### 7. Competitor Analysis (竞争对手分析)
**API端点**: `/api/v1/dashboard/competitor-analysis`  
**服务类**: `CompetitorAnalysisService`  
**主要数据表**: `product_review_analysis`, `product_reviews`, `product_wide_table`

#### 核心产品策略
这个图表分析固定的6个核心竞争产品，不受项目ASIN过滤影响，始终显示这些重要竞品的表现。

**固定分析的6个核心产品**：
- B08RRM8VH5: Leviton D26HD
- B0BVKZLT3B: Leviton D215S  
- B0BSHKS26L: Lutron Caseta Diva
- B01EZV35QU: TP Link Switch
- B00NG0ELL0: Leviton DSL06
- B085D8M2MR: Lutron Diva

#### 数据获取逻辑
这个图表通过多个数据源构建竞争对手的全面分析，包括产品-类别满意度矩阵和用例缺口分析。

**数据处理步骤**：
1. 从产品主表获取6个核心产品的基本信息：platform_id、title、reviews_count
2. 从评论分析表获取这些产品的情感分析数据：product_id、aspect_category、sentiment、review_count
3. 从原始评论表获取评分和评论文本：asin、rating、review_text
4. 构建两个分析维度：产品类别满意度矩阵、使用场景缺口分析

**运算逻辑**：

**1. 产品-类别满意度矩阵**：
- 按product_id和aspect_category分组统计positive和negative的review_count
- 满意度分数计算：positive数量 ÷ (positive数量 + negative数量)，结果在0-1之间
- 如果某产品在某类别没有评论数据，分数为0.5(中性)
- 包含的类别：performance(性能)、physical(物理)、usability(可用性)、connectivity(连接性)等

**2. 使用场景缺口分析**：
- 从review_text中提取使用场景关键词(bedroom、kitchen、bathroom、outdoor等)
- 计算每个产品在每个使用场景的平均rating
- 缺口程度 = 5.0 - 平均rating，值越高表示该场景下产品表现越差
- 只包含有足够评论数据的使用场景(至少5条评论)

#### 返回数据结构
返回包含竞争对手多维度分析的数据：
- targetProducts: 6个核心竞争产品的显示名称列表
- matrixData: 产品-类别满意度矩阵，每行是一个aspect_category，每列是一个产品的满意度分数
- productTotalReviews: 每个产品的总reviews_count，用于评估数据可靠性
- useCaseData: 使用场景缺口分析，包含产品列表和用例缺口矩阵

## 🔄 数据处理流程

### 通用数据过滤流程
所有图表服务都遵循统一的数据过滤标准：

**基础过滤条件**：
- 只查询Amazon来源的数据(source='amazon')
- 排除无产品类别的数据(category不为空)
- 应用项目ASIN过滤，确保数据隔离

**项目ASIN过滤机制**：
- 从projects表中获取当前项目的selected_product_asins列表
- 所有产品相关查询都必须通过platform_id字段过滤在项目ASIN范围内
- 这是核心的数据安全机制，防止项目间数据泄露

**数据清洗和验证**：
- 数值字段的空值处理：None、空字符串、"null"都转换为0
- 文本字段的空值处理：None、"null"转换为空字符串或默认值
- 收入数据过滤：只保留estimated_revenue > 0的记录用于收入相关分析

### 性能优化策略

**查询优化**：
- 只查询必需的字段，避免使用select('*')
- 使用索引字段(如platform_id)进行过滤
- 设置合理的查询限制，避免大数据集传输
- 避免复杂的SQL聚合操作，在Python中处理数据

**内存优化**：
- 分批处理大数据集，避免内存溢出
- 及时清理不需要的中间数据
- 使用生成器处理大量数据流

### 常见问题和解决方案

**空数据处理**：
- 当某个项目没有特定类型的数据时，返回空数组而不是错误
- 前端可以正常处理空数据并显示相应的提示信息

**数据类型不一致**：
- 统一的类型转换函数处理数据库中的None、字符串、数值混合情况
- 特别注意浮点数转换，处理"1.0"这种字符串格式

**ASIN过滤失效**：
- 在BaseDashboardService中强制检查项目ASIN配置
- 如果项目没有配置ASIN过滤，直接抛出错误而不是返回全量数据

## 📋 维护说明

### 添加新图表时的注意事项
1. 继承BaseDashboardService类，确保统一的过滤逻辑
2. 必须调用_apply_asin_filter方法进行项目数据隔离
3. 处理数据时考虑空值和异常情况
4. 返回数据结构要与前端组件匹配
5. 添加相应的API端点和数据模型

### 修改现有图表时的注意事项
1. 不要破坏现有的数据结构，保持向后兼容
2. 修改查询逻辑时要考虑性能影响
3. 更新文档说明新的数据处理逻辑
4. 测试项目ASIN过滤是否正常工作
5. 验证前端显示是否正常

### 数据库表结构变更
1. 如果数据库表结构发生变化，需要更新对应的服务类
2. 考虑字段名称变更对现有查询的影响
3. 添加新字段时要处理历史数据的兼容性
4. 更新本文档中的表结构说明

## 🖱️ Chart 交互逻辑 - 点击查看具体 Review

### Review Panel 交互机制
所有图表支持点击查看相关的具体 review 数据，通过统一的 Review Panel 系统实现。

#### 核心交互组件
**ReviewPanelContext** - 全局状态管理
- 管理 Review Panel 的开闭状态
- 存储当前显示的 review 数据和标题
- 提供 `openPanel()` 和 `closePanel()` 方法

**Review 数据关联映射**：
- **数据来源**: `getAllReviewDataByProject(projectId)` - 获取项目范围内所有产品的详细 review 数据
- **关联字段**: `productId` (对应产品主表的 platform_id/asin)
- **数据结构**: 每条 review 包含 `id`、`productId`、`text`、`sentiment`、`category`、`aspect`、`rating`、`verified`、`date`、`brand`

#### 不同图表的点击映射逻辑

**1. Review Insights 图表**
- **Pain Points Bar**: 点击某个痛点(如"installation_difficulty") → 筛选出 sentiment="negative" 且 aspect="installation_difficulty" 的所有 review
- **Customer Likes Bar**: 点击某个喜好特征 → 筛选出 sentiment="positive" 且 aspect 匹配的 review
- **Underserved Use Cases Bar**: 点击某个用例缺口 → 筛选出包含该用例关键词的 review

**2. Competitor Analysis 图表**
- **Product-Category Matrix**: 点击某个产品+类别的单元格 → 筛选出该产品(productId匹配)且 category 匹配的 review
- **Use Case Gap Matrix**: 点击某个产品+用例的单元格 → 筛选出该产品的包含用例关键词的 review

**3. 其他图表的潜在交互**
- **Brand Analysis**: 可点击品牌查看该品牌所有产品的 review
- **Product Analysis**: 可点击具体产品查看该产品的所有 review
- **Pricing Analysis**: 可点击价格区间查看该价格范围产品的 review

#### Review 过滤和搜索逻辑
**多维度过滤**：
- **按情感**: `sentiment: positive/negative/neutral`
- **按评分**: `rating: 1-5星`
- **按品牌**: `brand: Leviton/Lutron/等`
- **按验证状态**: `verified: true/false`
- **按产品**: `productId: 具体的ASIN`
- **按方面**: `aspect: 如installation_difficulty、smart_connectivity等`
- **按类别**: `category: Performance/Physical/Usability等`

**文本搜索**：
- 在 `review_text` 字段中进行关键词搜索
- 支持用例关键词搜索(如"bedroom"、"kitchen"、"outdoor"等)
- 支持产品特征关键词搜索

#### 数据加载和缓存策略
**一次性加载**：
- 在 dashboard 初始化时调用 `getAllReviewDataByProject()` 获取项目所有 review 数据
- 数据缓存在前端内存中，避免重复API调用
- 所有图表的点击交互都基于这个缓存的数据集进行过滤

**性能优化**：
- Review 数据按产品ID建立索引，快速定位
- 使用前端过滤而非实时API查询，提升响应速度
- 延迟加载 Review Panel，只在首次点击时初始化组件

这个文档应该定期更新，确保与实际的代码实现保持一致。 