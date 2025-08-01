# Market Insights Category Split Design Document

## Overview
将"Top 10 Product Segments by Revenue/Volume"图表按照category拆分成多个独立charts，参考"Sales Trend of Top 10 Brands"的实现模式。

## Background & Requirements

### Current State
- **单一图表**: 显示所有segments混合在一起的Top 10
- **数据结构**: `data.segmentRevenue.segments[]` - 平铺的segment数组
- **没有category分组**: 数据没有按category维度组织

### Target State  
- **按category拆分**: 每个category一个独立图表
- **参考实现**: Sales Trend of Top 10 Brands的成功模式
- **不需要向后兼容**: 直接修改现有结构

## Technical Analysis

### Backend Code Analysis

#### Current Data Flow
```
product_wide_table -> segment assignments -> _aggregate_by_segment_category -> _format_market_response
```

#### Key Tables & Fields
1. **product_wide_table**: 
   - platform_id, category, price_usd, past_year_revenue, past_year_volume
2. **product_segment_assignments**: 
   - project_id, product_id, segment_name

#### Critical Discovery
**后端代码已经有我们需要的全部功能！**

在 `MarketInsightsService` 的 `_aggregate_by_segment_category` 方法中，数据已经完美地按 `segment + category` 两个维度聚合：

```python
# 数据结构：segment -> category -> {revenue, volume, product_count}
segment_data[segment][category] = {
    'revenue': 0,
    'volume': 0, 
    'product_count': 0
}
```

但在 `_format_market_response` 方法中，**category维度被丢弃了**，只返回了segment层面的汇总数据。

## Design Solution

### Design Principles
1. **不需要向后兼容** - 直接修改现有结构
2. **最小化改动** - 主要是修改响应格式，保留现有聚合逻辑
3. **按category拆分** - 每个category一个独立图表
4. **复用成功模式** - 采用Sales Trend相同的实现方式

### Data Structure Changes

#### Backend Response Format
```python
# Current Format (被废弃)
{
    'segmentRevenue': {
        'segments': [...],  # 平铺数组
        'segmentNames': [...],
        'dimmerSwitches': [...],
        'lightSwitches': [...]
    }
}

# New Format
{
    'segmentRevenue': {
        'byCategory': {
            'Wall Dimmer Switches': [
                {
                    'segment': 'Smart WiFi Dimmer Switches',
                    'revenue': 22000000,
                    'volume': 45000,
                    'products': 156
                },
                // ... Top 10 segments for this category
            ],
            'Slide Dimmer Switches': [...],
            // ... other categories
        },
        'categoryNames': ['Wall Dimmer Switches', 'Slide Dimmer Switches', ...]
    }
}
```

## Implementation Plan

### Step 1: Backend Changes

#### File: `backend/dashboard/services/market_insights_service.py`

**Modify**: `_format_market_response` method

```python
def _format_market_response(self, segment_data: Dict[str, Dict[str, Dict[str, Any]]], 
                    project_segments: List[str]) -> Dict[str, Any]:
    """格式化响应数据，按category返回分组的segment数据"""
    
    # 收集所有categories
    all_categories = set()
    for segment_name, categories in segment_data.items():
        all_categories.update(categories.keys())
    
    category_names = sorted(list(all_categories))
    
    # 按category组织数据
    by_category = {}
    for category in category_names:
        category_segments = []
        
        # 为每个category收集所有segments的数据
        for segment_name in project_segments:
            if segment_name in segment_data and category in segment_data[segment_name]:
                category_data = segment_data[segment_name][category]
                category_segments.append({
                    'segment': segment_name,
                    'revenue': category_data.get('revenue', 0),
                    'volume': category_data.get('volume', 0),
                    'products': category_data.get('product_count', 0)
                })
        
        # 按revenue排序，取Top 10
        category_segments.sort(key=lambda x: x['revenue'], reverse=True)
        by_category[category] = category_segments[:10]
    
    return {
        'segmentRevenue': {
            'byCategory': by_category,
            'categoryNames': category_names
        }
    }
```

#### File: `backend/dashboard/models.py`

**Modify**: Data model definition

```python
class SegmentRevenue(BaseModel):
    """Segment revenue model with category support."""
    byCategory: Dict[str, List[SegmentData]] = Field(description="Segments grouped by category")
    categoryNames: List[str] = Field(description="List of category names")
```

### Step 2: Frontend Data Service Changes

#### File: `frontend/src/components/analysis-db/data/database-service.ts`

**Modify**: `getMarketInsightsDataByProject` return type

```typescript
async getMarketInsightsDataByProject(
  projectId: string, 
  categoryFilters?: string[], 
  packagingTypeFilters?: string[], 
  segmentFilters?: string[], 
  extendFields?: Record<string, any>
): Promise<{
  segmentRevenue: {
    byCategory: Record<string, Array<{
      segment: string
      revenue: number
      volume: number
      products: number
    }>>
    categoryNames: string[]
  }
}> {
  try {
    const result = await callDashboardAPI('market-insights', projectId, {
      categoryFilters,
      packagingTypeFilters,
      segmentFilters,
      extendFields
    })
    return result
  } catch (error) {
    console.error('Error fetching market insights data by project:', error)
    throw error
  }
}
```

### Step 3: Frontend Component Changes

#### File: `frontend/src/components/analysis-db/market-analysis/segments-by-category.tsx` (NEW)

```typescript
"use client"

import { Card } from "@/components/ui/card"
import { GroupedBarChart } from "@/components/analysis-db/charts/grouped-bar-chart"
import { MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"

interface SegmentData {
  segment: string
  revenue: number
  volume: number
  products: number
}

interface SegmentsByCategoryProps {
  category: string
  segmentData: SegmentData[]
  metricType: MetricType
  projectId: string
  onBarClick: (data: any) => void
  loading?: boolean
  error?: string | null
}

// Helper function to wrap long text
const wrapLongText = (text: string, maxLength: number = 15) => {
  if (!text || text.length <= maxLength) return text || 'Unknown'
  const words = text.split(' ')
  if (words.length <= 1) return text
  const mid = Math.ceil(words.length / 2)
  return words.slice(0, mid).join(' ') + '\n' + words.slice(mid).join(' ')
}

export function SegmentsByCategoryComponent({ 
  category, 
  segmentData, 
  metricType, 
  projectId,
  onBarClick,
  loading,
  error
}: SegmentsByCategoryProps) {

  if (loading) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-lg font-medium mb-4 text-center">
          📊 {category} - Top 10 Product Segments
        </h4>
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <p className="text-sm text-yellow-700">
            Loading segment data for {category}...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-lg font-medium mb-4 text-center">
          📊 {category} - Top 10 Product Segments
        </h4>
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-sm text-red-700">
            Error loading segment data for {category}: {error}
          </p>
        </div>
      </div>
    )
  }

  if (!segmentData || segmentData.length === 0) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-lg font-medium mb-4 text-center">
          📊 {category} - Top 10 Product Segments
        </h4>
        <div className="bg-gray-100 p-4 rounded">
          <p className="text-sm text-gray-600 text-center">
            No segment data available for {category}
          </p>
        </div>
      </div>
    )
  }

  // 构建图表数据
  const chartData = segmentData.map((segment, index) => ({
    name: wrapLongText(segment.segment),
    originalName: segment.segment,
    [metricType]: segment[metricType] || 0,
    revenue: segment.revenue || 0,
    volume: segment.volume || 0,
    products: segment.products || 0,
    fill: getChartColor(index)
  }))

  const chartColors = chartData.map((_, index) => getChartColor(index))
  const yAxisLabel = metricType === "revenue" ? "Revenue ($)" : metricType === "volume" ? "Volume" : "Products"

  return (
    <div className="bg-gray-50 p-6 rounded-lg">
      <h4 className="text-lg font-medium mb-4 text-center">
        📊 {category} - Top 10 Product Segments
      </h4>
      
      <div className="h-[400px] relative">
        <GroupedBarChart
          data={chartData}
          index="name"
          categories={[metricType]}
          colors={chartColors}
          yAxisLabel={yAxisLabel}
          metricType={metricType}
          onBarClick={onBarClick}
        />
        
        {/* Loading overlay */}
        {loading && (
          <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10 rounded-lg">
            <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              <span className="text-gray-700 font-medium">Loading segments...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
```

#### File: `frontend/src/components/analysis-db/market-analysis/market-insights.tsx` (MODIFY)

```typescript
"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { SegmentsByCategoryComponent } from "./segments-by-category"

interface SegmentData {
  segment: string
  revenue: number
  volume: number
  products: number
}

interface MarketInsightsProps {
  data: {
    segmentRevenue: {
      byCategory: Record<string, SegmentData[]>
      categoryNames: string[]
    }
  }
  productLists: {
    byBrand: Record<string, any[]>
    bySegment: Record<string, any[]>
    byPackageSize: Record<string, any[]>
  }
  projectId?: string
  initialFilters?: ProjectFilters
}

export function MarketInsights({ data, projectId, initialFilters }: MarketInsightsProps) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")
  const { openPanel, loading } = useProductPanel()

  const categoryNames = data.segmentRevenue?.categoryNames || []

  const handleBarClick = (data: any) => {
    if (data?.activeLabel) {
      // 查找原始segment名称
      const clickedDisplayName = data.activeLabel
      // Note: 可能需要根据具体的chart数据结构调整查找逻辑
      const segmentName = clickedDisplayName.replace('\n', ' ') // 处理换行的segment名称
      
      openPanel({
        projectId: projectId || '',
        filters: { segments: [segmentName] },
        title: `${segmentName} Products`,
        subtitle: `All products in ${segmentName}`,
        showFilters: { brand: true, category: true, priceRange: true, packSize: true }
      })
    }
  }

  if (categoryNames.length === 0) {
    return (
      <section className="mb-10">
        <ChartWithFilters
          chartId="market-insights"
          chartType="bar"
          projectId={projectId || ''}
          title="Top 10 Product Segments by Revenue/Volume"
          projectFilters={initialFilters}
        >
          <Card className="p-6 bg-gray-50">
            <p className="text-center text-gray-500">No segment data available for this project.</p>
          </Card>
        </ChartWithFilters>
      </section>
    )
  }

  return (
    <section className="mb-10">
      <ChartWithFilters
        chartId="market-insights"
        chartType="bar"
        projectId={projectId || ''}
        title="Top 10 Product Segments by Revenue/Volume"
        projectFilters={initialFilters}
      >
        <Card className="p-6 bg-gray-50">
          <MetricTypeSelector onChange={setMetricType} value={metricType} />
          
          {/* Summary for all categories */}
          <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-6">
            <p className="text-sm text-blue-700">
              <strong>Market Insights Analysis:</strong> Showing top 10 product segments by {metricType} for each category. 
              Data aggregated by segment and ranked within each category.
            </p>
          </div>
          
          {/* Category Charts */}
          <div className="space-y-8">
            {categoryNames.map((category) => (
              <SegmentsByCategoryComponent
                key={category}
                category={category}
                segmentData={data.segmentRevenue.byCategory[category] || []}
                metricType={metricType}
                projectId={projectId || ''}
                onBarClick={handleBarClick}
                loading={loading}
              />
            ))}
          </div>
        </Card>
      </ChartWithFilters>
    </section>
  )
}
```

## Expected Results

### Final Data Flow
1. **获取项目segments** → `get_project_segments()`
2. **获取产品数据** → `product_wide_table` (platform_id, category, revenue, volume)
3. **获取segment assignments** → `product_segment_assignments` (platform_id → segment_name)
4. **按segment+category聚合** → `_aggregate_by_segment_category()` (已存在，不变)
5. **格式化按category分组** → 修改后的 `_format_market_response()` 
6. **前端按category渲染** → 每个category一个独立图表

### UI Changes
- **替代单一图表** → 每个category（如"Wall Dimmer Switches"、"Slide Dimmer Switches"）一个独立图表
- **每个图表显示** → 该category下的Top 10 segments by revenue/volume
- **UI布局** → 垂直排列，类似Sales Trend的实现
- **交互保持** → 点击segment bar仍然打开产品面板

### Technical Benefits
- **零破坏性** - 后端聚合逻辑完全不变
- **最小改动** - 主要是响应格式和前端组件结构调整
- **完美复用** - 采用与Sales Trend完全相同的模式
- **数据完整** - 充分利用现有的category聚合能力

## File Changes Summary

### Modified Files
1. `backend/dashboard/services/market_insights_service.py` - 修改响应格式
2. `backend/dashboard/models.py` - 更新数据模型
3. `frontend/src/components/analysis-db/data/database-service.ts` - 更新类型定义
4. `frontend/src/components/analysis-db/market-analysis/market-insights.tsx` - 重构主组件

### New Files
1. `frontend/src/components/analysis-db/market-analysis/segments-by-category.tsx` - 新建category组件

## Testing Considerations

### Test Cases
1. **多category场景** - 验证每个category都能正确显示独立图表
2. **空数据处理** - 某个category没有segment数据时的展示
3. **单category场景** - 只有一个category时的布局
4. **数据排序** - 确保每个category内的segments按revenue/volume正确排序  
5. **交互功能** - 点击segment bar打开产品面板功能正常

### Backend Testing
- 验证 `_format_market_response` 返回正确的按category分组数据
- 确认数据聚合逻辑不受影响
- 测试不同项目的category和segment组合

### Frontend Testing  
- 验证每个category图表独立渲染
- 测试MetricTypeSelector在所有category图表中同步
- 确认loading和error状态正确处理

---

**Document Version**: 1.0  
**Last Updated**: 2024-12-19  
**Status**: Ready for Implementation