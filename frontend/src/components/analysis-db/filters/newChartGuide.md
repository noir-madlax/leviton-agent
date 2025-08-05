# 新建图表指南

本文档介绍如何在系统中新建一个类似 `market-share-analysis` 的图表组件。

## 📋 总体步骤概览

1. **定义图表配置**
2. **创建图表组件**
3. **配置过滤器**
4. **集成数据获取**
5. **添加到页面**
6. **配置图表显示控制**

---

## 🔧 详细实施步骤

### 1. 定义图表配置

#### 1.1 在常量文件中添加图表名称
**文件：** `frontend/src/components/analysis-db/constants/index.ts`

```typescript
export const CHART_NAMES = {
  MARKET_SHARE_ANALYSIS: 'market-share-analysis',
  BRAND_ANALYSIS: 'brand-analysis',
  YOUR_NEW_CHART: 'your-new-chart', // 🆕 添加你的图表名称
  // ... 其他图表
}
```

#### 1.2 配置图表显示控制
**文件：** `frontend/src/components/integrated-dashboard/hooks/use-chart-sections.ts`

确保你的图表名称在 `shouldShowChart` 函数中被正确处理。

### 2. 创建图表组件

#### 2.1 创建主图表组件
**文件：** `frontend/src/components/analysis-db/your-module/your-chart.tsx`

```typescript
"use client"

import React, { useState } from "react"
import { Card } from "@/components/ui/card"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useYourChartFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { useYourDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"

interface YourChartProps {
  data: any // 定义你的数据类型
  projectId?: string
  initialFilters?: ProjectFilters
}

export function YourChart({ data: initialData, projectId, initialFilters }: YourChartProps) {
  // 数据状态管理
  const {
    data: chartData,
    loading: dataLoading,
    error: dataError,
    refreshData
  } = useYourDataRefresh(projectId || '', initialData)

  // 过滤器状态管理
  const {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useYourChartFilters(
    refreshData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">
        📊 Your Chart Title
      </h2>

      <div className="mt-5">
        <div data-chart-id="your-new-chart">
          <Card className="p-6">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Your Chart Description
              </h3>
              
              {/* 过滤器组件 */}
              <FilterRenderer
                projectId={projectId || ''}
                chartName="your-new-chart"
                currentFilters={filters}
                onChange={handleFiltersChange}
                onFiltersReady={handleFiltersReady}
                disabled={dataLoading}
                className="mb-6"
              />
            </div>

            {/* 图表内容区域 */}
            <div className="p-6 bg-gray-50 rounded-lg border">
              {dataLoading ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-sm text-gray-600">正在更新图表数据...</p>
                  </div>
                </div>
              ) : !filtersReady ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-sm text-gray-600">正在更新图表数据...</p>
                  </div>
                </div>
              ) : dataError ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <p className="text-sm text-red-600 mb-3">数据加载失败: {dataError}</p>
                    <button 
                      onClick={() => refreshData(filters)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                    >
                      重新加载
                    </button>
                  </div>
                </div>
              ) : (
                // 🆕 在这里添加你的图表渲染逻辑
                chartData ? (
                  <div>
                    {/* 你的图表组件 */}
                    <YourActualChart data={chartData} />
                  </div>
                ) : (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <p className="text-center text-gray-500">No data available</p>
                  </div>
                )
              )}
            </div>
          </Card>
        </div>
      </div>
    </section>
  )
}
```

### 3. 配置过滤器

#### 3.1 创建专用的过滤器 Hook
**文件：** `frontend/src/components/analysis-db/hooks/use-chart-with-filters.ts`

```typescript
/**
 * 预设的图表 Hook - 你的新图表
 */
export function useYourChartFilters(
  refreshDataFn: (filters: ProjectFilters) => Promise<any>,
  projectId?: string,
  options?: UseChartWithFiltersOptions
) {
  return useChartWithFilters(
    CHART_NAMES.YOUR_NEW_CHART,
    refreshDataFn,
    projectId,
    options
  )
}
```

#### 3.2 创建数据刷新 Hook
**文件：** `frontend/src/components/analysis-db/hooks/use-chart-data-refresh.ts`

```typescript
// Your Chart 专用的数据刷新hook
export function useYourDataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: 'your-new-chart',
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      
      // 🆕 调用你的数据获取方法
      return await databaseService.getYourChartData(
        projectId,
        filters.categories.length > 0 ? filters.categories : undefined,
        filters.brands?.length ? filters.brands : undefined,
        filters.segments?.length ? filters.segments : undefined,
        filters.extend_fields
      )
    }
  })
}
```

### 4. 集成数据获取

#### 4.1 在数据服务中添加 API 方法
**文件：** `frontend/src/components/analysis-db/data/database-service.ts`

```typescript
class DatabaseService {
  // ... 其他方法

  async getYourChartData(projectId: string): Promise<TAMMarketShareResponse> {
    try {
      // 🆕 从过滤器状态管理器获取过滤器数据
      const filters = this.getFiltersFromState(CHART_NAMES.MARKET_SHARE_ANALYSIS)

      console.log(`🔍 [DATABASE-SERVICE] Getting TAM data with filters from state manager:`, filters)

      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

      const requestBody = {
        project_id: projectId,
        ...filters  // 🎯 直接展开 getFiltersFromState 的结果
      }

      console.log('🔍 Calling TAM Market Share API:', requestBody)

      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/market-analysis/tam-market-share`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`TAM Market Share API call failed: ${response.status}`)
      }

      const result: TAMMarketShareResponse = await response.json()
      console.log('📊 TAM Market Share API response:', result)
      
      return result
    } catch (error) {
      console.error('Error fetching TAM Market Share data:', error)
      throw error
    }
  }
```

### 5. 添加到页面

#### 5.1 在主页面中集成
**文件：** `frontend/src/components/analysis-db/index.tsx` 或相关页面文件

```typescript
import { YourChart } from "./your-module/your-chart"

// 在组件中添加
{shouldShowChart('your-new-chart') && (
  <YourChart
    data={yourChartData}
    projectId={projectId}
    initialFilters={initialFilters}
  />
)}
```

### 6. 配置图表显示控制

#### 6.1 确保图表在 shouldShowChart 中被正确处理
**文件：** `frontend/src/components/integrated-dashboard/hooks/use-chart-sections.ts`

确保你的图表名称 `'your-new-chart'` 在相关逻辑中被正确处理。

---

## 🎯 关键注意事项

### 1. **命名规范**
- 图表名称使用 kebab-case：`'your-new-chart'`
- Hook 名称使用 camelCase：`useYourChartFilters`
- 组件名称使用 PascalCase：`YourChart`

### 2. **状态管理模式**
- 使用 `filtersReady` 状态避免初始"无数据"显示
- 统一的加载动画效果
- 错误状态的友好提示

### 3. **过滤器集成**
- 使用 `FilterRenderer` 组件
- 通过 `useChartWithFilters` Hook 管理状态
- 支持全局过滤器同步

### 4. **数据流**
```
页面初始化 → 过滤器加载 → 数据获取 → 图表渲染
```

### 5. **文件结构**
```
your-module/
├── your-chart.tsx          # 主图表组件
├── components/             # 子组件
└── types.ts               # 类型定义
```

---

## 📚 参考示例

可以参考现有的 `market-share-analysis` 实现：
- `frontend/src/components/analysis-db/market-analysis/brand-analysis.tsx`
- `frontend/src/components/analysis-db/hooks/use-chart-with-filters.ts`
- `frontend/src/components/analysis-db/hooks/use-chart-data-refresh.ts`

按照这个指南，你就可以成功创建一个新的图表组件了！
