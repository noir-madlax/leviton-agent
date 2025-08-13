"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts"
import { useMemo } from "react"
import { getChartColors } from "../shared/chart-colors"

// 定义组件的属性接口
type ChartDatum = {
  name: string
  originalName?: string
  revenue?: number
  volume?: number
  products?: number
  [key: string]: string | number | undefined
}

interface GroupedBarChartProps {
  data: ChartDatum[]  // 图表数据数组
  index: string  // 用作X轴的数据字段名
  categories: string[]  // 分类数组
  colors?: string[]  // 自定义颜色数组，可选
  yAxisLabel?: string  // Y轴标签，可选
  xAxisLabel?: string  // X轴标签，可选
  metricType?: "revenue" | "volume" | "products"  // 指标类型：收入/数量/产品数
  onBarClick?: (data: { activeLabel?: string } & Record<string, unknown>) => void  // 柱状图点击回调函数，可选
}

export function GroupedBarChart({
  data,
  index,
  categories,
  colors = getChartColors(2),
  yAxisLabel,
  xAxisLabel,
  metricType = "revenue",
  onBarClick,
}: GroupedBarChartProps) {
  // 格式化数值显示：收入类型显示美元符号，数量类型显示纯数字
  const formatValue = (value: number) => {
    return metricType === "revenue" ? `$${value.toLocaleString()}` : value.toLocaleString()
  }

  // 获取第一个category作为dataKey，如果没有则使用"value"
  const dataKey = categories.length > 0 ? categories[0] : "value"

  // 动态计算底部边距，基于最长标签长度
  const { bottomMargin, xAxisLabelOffset } = useMemo(() => {
    if (!data.length) return { bottomMargin: 80, xAxisLabelOffset: -10 }  // 减少默认值
    
    // 找到最长的标签（考虑换行文本）
    const longestLabel = data.reduce((longest, item) => {
      const labelText = String(item[index])
      const lines = labelText.split('\n')
      const maxLineLength = Math.max(...lines.map(line => line.length))
      return maxLineLength > longest ? maxLineLength : longest
    }, 0)
    
    // 计算旋转标签所需的空间
    const estimatedLabelHeight = Math.max(25, longestLabel * 0.5 * 6) // 减少系数
    
    // 计算各部分所需空间
    const baseMargin = 30          // 基础边距：图表边框到标签的距离
    const labelSpace = Math.max(35, estimatedLabelHeight)  // 标签显示空间
    const xAxisLabelSpace = 20     // X轴标题显示空间
    
    const totalBottomSpace = baseMargin + labelSpace + xAxisLabelSpace
    
    return {
      bottomMargin: Math.min(totalBottomSpace, 65), // 减少最大值从120到85
      xAxisLabelOffset: -12,  // X轴标签向上偏移量
    }
  }, [data, index])

  // 颜色变亮函数：用于Tooltip背景色
  const lightenColor = (color: string, amount: number = 0.3) => {
    // 移除#号
    const hex = color.replace('#', '')
    
    // 解析RGB值
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    
    // 计算变亮后的颜色
    const newR = Math.min(255, Math.floor(r + (255 - r) * amount))
    const newG = Math.min(255, Math.floor(g + (255 - g) * amount))
    const newB = Math.min(255, Math.floor(b + (255 - b) * amount))
    
    // 转换回十六进制
    return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`
  }

  // 自定义X轴标签组件：支持换行和旋转
  const CustomTick = (props: { x?: number; y?: number; payload?: { value?: string } }) => {
    const { x, y, payload } = props
    const lines = String(payload?.value ?? '').split('\n')  // 按换行符分割文本
    
    return (
      <g transform={`translate(${x},${y})`}>
        {lines.map((line: string, lineIndex: number) => (
          <text
            key={lineIndex}
            x={0}
            y={lineIndex * 14}  // 行间距：14px
            dy={16}             // 文本基线偏移
            textAnchor="end"    // 文本对齐方式：右对齐
            fill="#666"         // 文本颜色：灰色
            fontSize="13"       // 字体大小
            transform="rotate(-45)"  // 旋转角度：-45度
          >
            {line}
          </text>
        ))}
      </g>
    )
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        barCategoryGap="10%"  // 柱状图组间距：10%
        margin={{
          top: 20,              // 顶部边距：20px
          right: 20,            // 右侧边距：20px  
          left: 20,             // 左侧边距：20px
          bottom: bottomMargin, // 底部边距：动态计算
        }}
      >
        {/* 网格线：虚线样式 */}
        <CartesianGrid strokeDasharray="3 3" />
        
        {/* X轴配置 */}
        <XAxis
          dataKey={index}                    // 数据字段
          interval={0}                       // 显示间隔：0表示显示所有标签
          tick={<CustomTick />}              // 自定义标签组件
          height={bottomMargin - 20}         // X轴高度：底部边距减去20px
          label={{
            value: xAxisLabel,               // X轴标题文本
            position: "insideBottom",        // 位置：底部内侧
            offset: xAxisLabelOffset,        // 偏移量
            style: { 
              textAnchor: 'middle',          // 水平居中
              fontSize: '16px',              // 字体大小
              fontWeight: 'bold'             // 字体粗细
            }
          }}
        />
        
        {/* Y轴配置 */}
        <YAxis
          label={{
            value: yAxisLabel,               // Y轴标题文本
            angle: -90,                      // 旋转角度：-90度（垂直）
            position: "insideLeft",          // 位置：左侧内部
            style: { 
              textAnchor: 'middle',          // 垂直居中
              fontSize: '16px',              // 字体大小
              fontWeight: 'bold'             // 字体粗细
            }
          }}
          tickFormatter={formatValue}        // 刻度值格式化函数
          tick={{ fontSize: 14 }}           // 刻度标签字体大小
          width={90}                        // Y轴宽度：固定90px防止重叠
        />
        
        {/* 悬浮提示框 */}
        <Tooltip 
          formatter={(value) => [formatValue(Number(value)), metricType === "revenue" ? 'Revenue' : 'Volume']}
          labelStyle={{ color: '#333', fontWeight: 'bold' }}  // 标签样式
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const dataIndex = data.findIndex(item => item.name === label)
              const itemColor = colors[dataIndex % colors.length]
              const lightColor = lightenColor(itemColor, 0.4)
              
              return (
                <div 
                  style={{ 
                    backgroundColor: lightColor,           // 背景色：变亮的柱状图颜色
                    border: `2px solid ${itemColor}`,     // 边框：柱状图原色
                    borderRadius: '6px',                  // 圆角
                    padding: '12px',                      // 内边距
                    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',  // 阴影
                    maxWidth: '400px',                    // 最大宽度
                    minWidth: '250px'                     // 最小宽度
                  }}
                >
                  <p style={{ 
                    color: '#333', 
                    fontWeight: 'bold', 
                    margin: '0 0 6px 0',
                    wordWrap: 'break-word',               // 自动换行
                    lineHeight: '1.4'                    // 行高
                  }}>
                    {label}
                  </p>
                  <p style={{ color: '#333', margin: 0 }}>
                    {metricType === "revenue" ? "Revenue" : "Volume"}: {formatValue(Number(payload[0].value))}
                  </p>
                </div>
              )
            }
            return null
          }}
        />
        
        {/* 图例配置 */}
        <Legend 
          verticalAlign="top"        // 垂直对齐：顶部
          height={80}               // 图例高度：减少从80到50px
          wrapperStyle={{ 
            paddingBottom: '10px',    // 底部内边距
            fontSize: '11px',        // 字体大小
            lineHeight: '1.2'        // 行高
          }}
          iconType="rect"            // 图标类型：矩形
          iconSize={18}              // 图标大小
          layout="horizontal"        // 布局：水平
          align="center"             // 对齐：居中
          payload={data.map((item, index) => ({
            value: String(item.name).replace(/\n/g, ' '),  // 图例文本：去掉换行符
            type: 'rect',                         // 图标类型
            color: colors[index % colors.length], // 颜色
            id: item.name                         // 唯一标识
          }))}
        />
        
        {/* 柱状图配置 */}
        <Bar 
          dataKey={dataKey}          // 数据字段
          maxBarSize={80}            // 最大柱宽：80px
          style={{ cursor: 'pointer' }}  // 鼠标样式：指针
          onClick={(barData) => {
            if (!onBarClick) return
            // 从柱子数据中提取原始名称
            const payload = (barData && typeof barData === 'object' && 'payload' in barData)
              ? (barData as { payload?: ChartDatum }).payload
              : undefined
            const name = payload?.originalName || payload?.name
            const cleaned = typeof name === 'string' ? name.replace(/\n/g, ' ') : undefined
            onBarClick({ activeLabel: cleaned })
          }}
        >
          {/* 为每个柱子设置颜色 */}
          {data.map((entry, entryIndex) => (
            <Cell key={`cell-${entryIndex}`} fill={colors[entryIndex % colors.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
