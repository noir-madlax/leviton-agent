/**
 * 产品浮窗使用示例
 * 
 * 展示如何在各种图表组件中使用新的产品浮窗功能
 */

import React from 'react'
import { useProductPanelQuery } from '@/components/analysis-db/hooks/use-product-panel-query'
import { useProductPanel } from '@/components/analysis-db/contexts/product-panel-context'

// 示例1：小提琴图点击处理
export function ViolinChartExample({ projectId }: { projectId: string }) {
  const { handleViolinClick } = useProductPanelQuery()

  const handleCategoryClick = async (category: string) => {
    await handleViolinClick(
      projectId,
      category,
      `${category} Products`,
      `All products in ${category} category`
    )
  }

  return (
    <div>
      {/* 你的小提琴图组件 */}
      <div onClick={() => handleCategoryClick('Light Switches')}>
        Light Switches Violin
      </div>
    </div>
  )
}

// 示例2：品牌小提琴图点击处理
export function BrandViolinChartExample({ projectId }: { projectId: string }) {
  const { handleBrandViolinClick } = useProductPanelQuery()

  const handleBrandClick = async (brand: string, category?: string) => {
    await handleBrandViolinClick(
      projectId,
      brand,
      category,
      `${brand} Products`,
      category ? `${brand} products in ${category}` : `All ${brand} products`
    )
  }

  return (
    <div>
      {/* 你的品牌小提琴图组件 */}
      <div onClick={() => handleBrandClick('Leviton', 'Light Switches')}>
        Leviton Brand Violin
      </div>
    </div>
  )
}

// 示例3：柱状图点击处理
export function BarChartExample({ projectId }: { projectId: string }) {
  const { handleBarClick } = useProductPanelQuery()

  const handleSegmentClick = async (segment: string) => {
    await handleBarClick(
      projectId,
      segment,
      `${segment} Segment`,
      `All products in ${segment} segment`
    )
  }

  return (
    <div>
      {/* 你的柱状图组件 */}
      <div onClick={() => handleSegmentClick('Premium')}>
        Premium Segment Bar
      </div>
    </div>
  )
}

// 示例4：复杂筛选条件
export function ComplexFilterExample({ projectId }: { projectId: string }) {
  const { handleMultipleFiltersClick } = useProductPanelQuery()

  const handleComplexClick = async () => {
    await handleMultipleFiltersClick(
      projectId,
      {
        categories: ['Light Switches', 'Dimmer Switches'],
        brands: ['Leviton'],
        segments: ['Premium', 'Standard']
      },
      'Leviton Switches',
      'Premium and Standard Leviton switches',
      {
        brand: false,  // 不显示品牌筛选器（因为已经筛选了Leviton）
        category: true,
        priceRange: true,
        packSize: true
      }
    )
  }

  return (
    <div>
      <button onClick={handleComplexClick}>
        Show Leviton Switches
      </button>
    </div>
  )
}



// 示例5：在现有图表组件中集成
export function IntegratedChartExample({ 
  projectId, 
  chartData 
}: { 
  projectId: string
  chartData: Array<{ category: string, value: number }>
}) {
  const { handleCategoryClick, loading, error } = useProductPanelQuery()

  const handleChartClick = async (dataPoint: { category: string, value: number }) => {
    if (loading) return // 防止重复点击
    
    try {
      await handleCategoryClick(
        projectId,
        dataPoint.category,
        `${dataPoint.category} Analysis`,
        `${dataPoint.value} total value • Click to see products`
      )
    } catch (err) {
      console.error('Failed to open product panel:', err)
    }
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>
  }

  return (
    <div className="relative">
      {loading && (
        <div className="absolute inset-0 bg-white/50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
      )}
      
      <div className="grid grid-cols-2 gap-4">
        {chartData.map((item, index) => (
          <div
            key={index}
            className="p-4 border rounded cursor-pointer hover:bg-gray-50"
            onClick={() => handleChartClick(item)}
          >
            <h3 className="font-medium">{item.category}</h3>
            <p className="text-gray-600">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// 使用说明：
/*
1. 在你的图表组件中导入相应的Hook：
   import { useProductPanelQuery } from '@/components/analysis-db/hooks/use-product-panel-query'

2. 在组件中使用Hook：
   const { handleViolinClick, handleBarClick, loading, error } = useProductPanelQuery()

3. 在图表点击事件中调用相应的处理器：
   onClick={() => handleViolinClick(projectId, category)}

4. 确保你的页面包含了ProductPanelProvider：
   <ProductPanelProvider>
     <YourPageContent />
     <ProductPanel />
   </ProductPanelProvider>

5. 新方式的优势：
   - 自动根据筛选条件查询产品
   - 支持加载状态和错误处理
   - 统一的API接口
   - 更准确的产品数据
*/
