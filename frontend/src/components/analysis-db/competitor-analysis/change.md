# Competitor Focal Page – Page-level ASIN Filter Design

Owner: FE/BE
Scope: frontend + backend + DB config
Decision: Page-level ASIN filter; no fallback; DB fully controls default ASINs and visibility; applies to all three charts on focal page.

---

## 1. Objectives

- Use `project_filter_defaults` to配置：
  - 页面级（`chart_name = 'competitor-analysis'`）ASIN 默认列表（`filter_name = 'asins'`）。
  - 页面级 ASIN 选择器是否可见（`is_visible`）。
- 去除所有前端/服务端的写死 ASIN。
- 去除 `competitor-analysis.tsx` 中前端直连 Supabase 获取产品基础信息的逻辑，改为后端 API。
- 统一 Page-level ASIN filter 应用于 focal 页的三个图表：
  - product-comparison-dimensions（`CompetitorMatrix`）
  - product-comparison-use-cases（`MissedOpportunitiesMatrix`）
  - customer-satisfaction-overview（`CustomerSatisfactionChart`）

约束：

- 不要兜底。若项目未配置 `project_filter_defaults` 对应记录，则页面不显示 ASIN 选择器；三个图表不请求数据并呈现空态提示（或由后端返回空，保持一致 UX）。

---

## 2. Data Model

表：`project_filter_defaults`

- `project_id` TEXT
- `chart_name` TEXT：页面级使用 `'competitor-analysis'`
- `filter_name` TEXT：固定 `'asins'`
- `filter_values` JSONB：字符串数组（ASIN 列表）
- `is_visible` BOOLEAN：页面是否展示 ASIN 选择器
- `options` JSONB：预留

页面级解析规则：

- 仅读取 `chart_name = 'competitor-analysis' AND filter_name = 'asins'` 一条（如多条，以最新一条或首条为准，后端/SQL可限定唯一性）。
- `filter_values` → page-level 默认 ASIN 列表。
- `is_visible` → 是否展示选择器。

---

## 3. Backend Changes

### 3.1 已有接口复用

- GET `/api/v1/dashboard/projects/{project_id}/filter-defaults`（已存在）
  - 前端将只取页面级记录，字段：`chartName/filterName/filterValues/isVisible/options`。

### 3.2 新增接口：按 ASIN 批量取产品基础信息（替代前端直连 Supabase）

- POST `/api/v1/dashboard/projects/{project_id}/products/basic`
  - Request:
    ```json
    { "asins": ["B00NG0ELL0", "B0..."] }
    ```
  - Response:
    ```json
    {
      "products": [
        {
          "platform_id": "B00NG0ELL0",
          "title": "string",
          "brand": "string",
          "price_usd": 0,
          "reviews_count": 0,
          "category": "string",
          "product_url": "string|null",
          "rating": 0|null
        }
      ]
    }
    ```
  - 查询源：`product_wide_table`；按请求 asins 的顺序返回（ORDER BY 保序），确保展示顺序稳定。
  - 安全：按 `project_id` 限定可见范围（如果需要），但此接口已是 page-level 配置驱动，不跨项目泄露。

### 3.3 竞争对手概览（客户满意度卡片）需支持 `selected_asins`（去除写死）

- 新接口已存在：`/api/v1/dashboard/charts/competitor-analysis/summary`（当前 FE 用的 API）
- 调整：服务端根据请求体的 `selected_asins` 计算，不再内部写死默认列表；若 `selected_asins` 为空，返回空集（无兜底）。

---

## 4. Frontend Changes

### 4.1 competitor-analysis.tsx（页面容器）

- 移除/降级：
  - 删除写死常量 `DEFAULT_COMPETITOR_ASINS`。
  - 删除 `useEffect` 内前端直连 Supabase 读取默认产品信息的逻辑（`supabase.from('product_wide_table').in(...)`）。
- 新增：
  - 首次加载时调用 `databaseService.getProjectFilterDefaultsNew(projectId)` 并读取页面级记录：
    - `defaultAsins = record.filterValues || []`
    - `isSelectorVisible = !!record.isVisible`
  - 若 `defaultAsins.length === 0`：不触发任何数据请求，三图表空态；选择器展示与否取决于 `isSelectorVisible`。
  - 若 `defaultAsins.length > 0`：
    - 初始化 `selectedAsins = defaultAsins`
    - 调用 `databaseService.getProductsBasic(projectId, selectedAsins)` 获取卡片展示所需基础信息（品牌/价格/评分等）
    - 调用 `databaseService.getCompetitorMatrixViewData(projectId, selectedAsins, 'phy_perf'|'use')` 拉取两张矩阵
    - 为 `CustomerSatisfactionChart` 通过 props 传入 `selectedAsins`（详见 4.3）
- UI 显隐：
  - 原来的 `<section className="hidden">` 改为条件渲染：`isSelectorVisible ? <section>...</section> : null`
- 交互：
  - 选择器 Apply → 更新 `selectedAsins` → 重新调用上述三个数据请求。

### 4.2 competitor-asin-selector.tsx（选择器）

- 作为展示控件保留，不改业务逻辑：
  - 初始值由父组件通过 `defaultSelection` 传入。
  - 仅在 `isSelectorVisible` 为真时由父组件渲染本组件。
  - 保持 `databaseService.getAvailableAsins(projectId)` 供列表展示（该方法已走后端，不直连）。

### 4.3 CustomerSatisfactionChart（第三张图，之前未使用选中 ASIN）

- 现状：`customer-satisfaction-api.ts` 中 `getCustomerSatisfactionData(...)` 写死使用 `DEFAULT_COMPETITOR_ASINS`。
- 改造：
  - 将 `CustomerSatisfactionChartProps` 扩展，增加 `selectedAsins: string[]`。
  - `useCustomerSatisfactionData` → 透传 `selectedAsins` 到 `customer-satisfaction-api.getCustomerSatisfactionData(projectId, { selected_asins })`。
  - API 请求体内不再写死默认；用传入的 `selected_asins`。
  - 当 `selectedAsins.length === 0` 时，不请求，展示空态（与页面策略一致）。

### 4.4 database-service.ts

- 新增：
  - `getProductsBasic(projectId: string, asins: string[])` → POST `/projects/{project_id}/products/basic`
- 复用：
  - `getProjectFilterDefaultsNew(projectId)`（已存在）
  - `getCompetitorMatrixViewData(projectId, selectedAsins, aspectType)`（已存在）

---

## 5. Request Flow

Page load:

1) GET `/projects/{project_id}/filter-defaults` → 读取页面级记录
2) 若 `filter_values` 非空：
   - `selectedAsins = filter_values`
   - POST `/projects/{project_id}/products/basic` with `asins`
   - POST `/competitor-analysis/matrix-view` x2 with `selected_asins`
   - POST `/charts/competitor-analysis/summary` with `selected_asins`
3) 若 `filter_values` 为空：
   - 不发上述数据请求；三图空态
4) 根据 `is_visible` 决定是否渲染选择器

Apply:

- 更新 `selectedAsins`，重复步骤 2 或展示空态（若变为空）。

---

## 6. Files to Change

| File                                                                                           | Change Type | Purpose                                                                                                        | Key Edits                                                                                                                                                                            |
| ---------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `backend/dashboard/api.py`                                                                   | Add         | 新增 `POST /api/v1/dashboard/projects/{project_id}/products/basic`                                           | 按 ASIN 批量查 `product_wide_table`，返回基础字段；保序；可加 project 限定                                                                                                         |
| `frontend/src/components/analysis-db/competitor-analysis/competitor-analysis.tsx`            | Modify      | Page-level 解析与数据驱动；移除写死与 Supabase 直连；条件渲染选择器；三图统一使用 page-level `selectedAsins` | - 删除 `DEFAULT_COMPETITOR_ASINS` 与相关 `supabase` 调用 - 引入 `getProjectFilterDefaultsNew` + `getProductsBasic` - 将 `CustomerSatisfactionChart` 传入 `selectedAsins` |
| `frontend/src/components/analysis-db/competitor-analysis/competitor-asin-selector.tsx`       | Keep        | 展示控件                                                                                                       | 无业务变更                                                                                                                                                                           |
| `frontend/src/components/analysis-db/data/database-service.ts`                               | Add/Modify  | 新增 `getProductsBasic`；保留现有 matrix API；不改其他chart                                                  | -`getProductsBasic(projectId, asins)` - 统一错误处理                                                                                                                               |
| `frontend/src/app/chat/charts/customer_satisfaction/types/customer-satisfaction.types.ts`    | Modify      | 扩展 props                                                                                                     | `CustomerSatisfactionChartProps` 增加 `selectedAsins: string[]`                                                                                                                  |
| `frontend/src/app/chat/charts/customer_satisfaction/hooks/use-customer-satisfaction-data.ts` | Modify      | 传递 `selected_asins`                                                                                        | Hook 接收并透传，依赖 keys 增加 `selectedAsins`                                                                                                                                    |
| `frontend/src/app/chat/charts/customer_satisfaction/services/customer-satisfaction-api.ts`   | Modify      | 去除写死默认 ASIN；使用传入的 `selected_asins`                                                               | requestBody:`{ project_id, selected_asins }`；删除 `DEFAULT_COMPETITOR_ASINS`                                                                                                    |

---

## 7. Conflict & Coverage Check

- competitor-analysis.tsx 当前用 `supabase.from('product_wide_table')...in(DEFAULT_COMPETITOR_ASINS)`：会被删除，改为后端 `getProductsBasic`。无残留 Supabase 直连。
- `DEFAULT_COMPETITOR_ASINS` 在页面和 `customer-satisfaction-api.ts` 内均有存在：两处都会移除，且统一由 page-level `selectedAsins` 驱动。
- 选择器所在 `<section className="hidden">`：将改为条件渲染，确保 `is_visible` 生效。
- 两个矩阵图已由 `selectedAsins` 驱动，无需改 API；仅保证页面初始化时 `selectedAsins` 来源来自 DB。
- 第三个图（CustomerSatisfactionChart）之前不使用 `selectedAsins`，此次将接入，API 服务去写死、用 `selected_asins` 请求。
- “不要兜底”要求：当 DB `filter_values` 为空或未配置 → 页面不加载数据、组件空态；选择器是否显示仅看 `is_visible`。此逻辑在页面实现。
- 其他页面不受影响：改动限定在 focal 页与该页用到的 API 客户端。

---

## 8. Empty/No-config Behaviors

- 无任意 fallback。
- 当 `filter_values = []` 或找不到页面级记录：
  - `selectedAsins = []`
  - 三图不请求，空态提示
  - 选择器是否显示 = `is_visible`（若无记录，视为 false）

---

## 9. Testing Checklist

- 配置：`chart_name='competitor-analysis'`, `filter_name='asins'`, `filter_values=["A","B","C"]`, `is_visible=true`
  - 页面加载：选择器显示，默认选中 A/B/C；三图均加载且数据一致。
- 配置：同上但 `is_visible=false`
  - 页面加载：选择器不显示，但三图加载 A/B/C。
- 配置：`filter_values=[]`, `is_visible=true`
  - 页面加载：选择器显示、无默认选中；三图不请求，空态。
  - 用户在选择器选中后 Apply：三图加载选择结果。
- 移除全部配置
  - 页面加载：不显示选择器；三图空态。

---

## 10. Rollout Plan

1) 后端新增 `/products/basic`。
2) 前端实现页面解析和三图统一驱动；移除 Supabase 直连和写死常量。
3) 本地/测试环境验证上述用例。
4) 配置目标项目的 `project_filter_defaults`（页面级）；发布。

---

## 11. Security

- 前端不再直连 Supabase；所有数据走后端 API。
- 后端可在 `/products/basic` 内根据 `project_id` 限制可见范围（如需要）。

---
