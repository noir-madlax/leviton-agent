"use client"

import { UnderservedUseCase } from '@/components/analysis-db/data/review-insights'

interface UnderservedHeatmapProps {
  data: UnderservedUseCase[]
}

export function UnderservedHeatmap({ data }: UnderservedHeatmapProps) {
  // 创建用例和产品属性的组合矩阵
  const useCases = [...new Set(data.map(item => item.useCase))]
  const productAttributes = [...new Set(data.map(item => item.productAttribute))]

  // 创建数据映射
  const dataMap = new Map()
  data.forEach(item => {
    dataMap.set(`${item.useCase}-${item.productAttribute}`, item)
  })

  // 根据缺口级别获取颜色和透明度
  const getHeatmapColor = (gapLevel: number) => {
    if (gapLevel >= 80) return 'bg-red-600 text-white'
    if (gapLevel >= 60) return 'bg-red-500 text-white'  
    if (gapLevel >= 40) return 'bg-red-400 text-white'
    if (gapLevel >= 20) return 'bg-red-300 text-gray-800'
    return 'bg-red-200 text-gray-700'
  }

  return (
    <div className="w-full">
      {/* 图例 */}
      <div className="flex items-center justify-center mb-6 space-x-4">
        <span className="text-sm text-gray-600">Gap Level:</span>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-red-200 rounded"></div>
          <span className="text-xs">20-40%</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-red-400 rounded"></div>
          <span className="text-xs">40-60%</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span className="text-xs">60-80%</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-red-600 rounded"></div>
          <span className="text-xs">80%+</span>
        </div>
      </div>

      {/* 热力图表格 */}
      <div className="overflow-x-auto">
        <div className="min-w-full">
          {/* 表头 */}
          <div className="grid grid-cols-1" style={{ gridTemplateColumns: '200px repeat(4, 1fr)' }}>
            <div className="p-3 text-sm font-semibold text-gray-700 bg-gray-100 border border-gray-200">
              Use Cases →<br/>Product Attributes ↓
            </div>
            {productAttributes.slice(0, 4).map((attr, index) => (
              <div key={index} className="p-3 text-sm font-semibold text-center text-gray-700 bg-gray-100 border border-gray-200">
                {attr}
              </div>
            ))}
          </div>

          {/* 数据行 */}
          {useCases.slice(0, 6).map((useCase, rowIndex) => (
            <div key={rowIndex} className="grid grid-cols-1" style={{ gridTemplateColumns: '200px repeat(4, 1fr)' }}>
              <div className="p-3 text-sm font-semibold text-gray-700 bg-gray-50 border border-gray-200">
                {useCase}
              </div>
              {productAttributes.slice(0, 4).map((attr, colIndex) => {
                const cellData = dataMap.get(`${useCase}-${attr}`)
                if (cellData) {
                  return (
                    <div 
                      key={colIndex}
                      className={`p-3 text-center border border-gray-200 ${getHeatmapColor(cellData.gapLevel)} transition-all hover:scale-105 cursor-pointer`}
                      title={`${useCase} - ${attr}: ${cellData.gapLevel}% gap, ${cellData.mentionCount} mentions`}
                    >
                      <div className="text-lg font-bold">
                        {cellData.gapLevel}%
                      </div>
                      <div className="text-xs opacity-80">
                        {cellData.mentionCount}
                      </div>
                    </div>
                  )
                } else {
                  return (
                    <div key={colIndex} className="p-3 text-center border border-gray-200 bg-gray-100">
                      <span className="text-gray-400 text-sm">N/A</span>
                    </div>
                  )
                }
              })}
            </div>
          ))}
        </div>
      </div>

      {/* 关键指标统计 */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        {data
          .filter(item => item.gapLevel > 80)
          .sort((a, b) => b.gapLevel - a.gapLevel)
          .slice(0, 4)
          .map((item, index) => (
            <div key={index} className="bg-red-50 border border-red-200 p-4 rounded-lg">
              <div className="text-lg font-bold text-red-600">
                {item.gapLevel}%
              </div>
              <div className="text-sm text-gray-700 font-medium truncate">
                {item.useCase}
              </div>
              <div className="text-xs text-gray-500">
                {item.mentionCount} mentions
              </div>
            </div>
          ))}
      </div>

      {/* 说明文字 */}
      <div className="mt-4 text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
        <strong>Reading the Heatmap:</strong> Red intensity indicates the level of unmet demand. 
        Percentage shows gap level, smaller number below shows mention frequency. 
        Higher percentages and frequencies indicate greater market opportunities.
      </div>
    </div>
  )
} 