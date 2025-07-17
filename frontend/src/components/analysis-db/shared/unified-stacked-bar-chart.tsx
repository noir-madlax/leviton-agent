'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface UnifiedStackedBarChartProps {
  data: Array<{
    displayName?: string;
    [key: string]: any;
  }>;
  xAxisDataKey: string;
  positiveDataKey: string;
  negativeDataKey: string;
  onBarClick?: (data: any, index: number) => void;
  CustomTooltip?: React.ComponentType<any>;
  maxLabelLength?: number; // 新增：最大标签长度
  showFromBottom?: boolean; // 新增：是否从下往上显示
}

const defaultTooltip = ({ active, payload, label }: {active?: boolean, payload?: any[], label?: string}) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg min-w-[300px]">
        <p className="font-semibold text-gray-900 mb-2">{label}</p>
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div>
            <p className="text-sm text-green-600 font-semibold">
              Positive: {data[payload.find((p: any) => p.dataKey.includes('positive') || p.dataKey.includes('Positive'))?.dataKey] || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-red-600 font-semibold">
              Negative: {data[payload.find((p: any) => p.dataKey.includes('negative') || p.dataKey.includes('Negative'))?.dataKey] || 0}
            </p>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export function UnifiedStackedBarChart({
  data,
  xAxisDataKey,
  positiveDataKey,
  negativeDataKey,
  onBarClick,
  CustomTooltip = defaultTooltip,
  maxLabelLength = 20, // 默认最大长度20字符
  showFromBottom = true // 默认从下往上显示
}: UnifiedStackedBarChartProps) {
  const handleBarClick = (data: any, index: number) => {
    if (onBarClick) {
      onBarClick(data, index);
    }
  };

  // 格式化X轴标签
  const formatXAxisLabel = (value: string) => {
    if (!value) return value;
    
    if (value.length <= maxLabelLength) {
      return value;
    }
    
    if (showFromBottom) {
      // 从下往上显示：优先显示开头的字符
      return value.substring(0, maxLabelLength - 3) + '...';
    } else {
      // 从上往下显示：优先显示结尾的字符
      return '...' + value.substring(value.length - maxLabelLength + 3);
    }
  };

  // 自定义X轴Tick组件，单行显示
  const CustomXAxisTick = (props: { x: number; y: number; payload: { value: string } }) => {
    const { x, y, payload } = props;
    const text = formatXAxisLabel(payload.value);
    
    return (
      <g transform={`translate(${x},${y})`}>
        <text
          x={0}
          y={0}
          dy={16}
          textAnchor="end" // 文本对齐方式: "start" | "middle" | "end"
          fill="#666" // 文字颜色
          fontSize="11" // 字体大小: 可调整数字
          transform="rotate(-45)" // 旋转角度: "rotate(-90)" | "rotate(-30)" | "rotate(0)" 等
          // fontWeight="normal" // 字体粗细: "normal" | "bold" | "lighter"
          // fontFamily="Arial" // 字体族: "Arial" | "sans-serif" | "monospace"
        >
          {text}
        </text>
      </g>
    );
  };

  return (
    <div className="h-[450px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{
            top: 30,
            right: 30,
            left: 20,
            bottom: 0, // 增加底部空间以容纳更长的标签
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey={xAxisDataKey}
            tick={CustomXAxisTick}
            height={120} // X轴高度，为标签预留空间
            interval={0} // 显示间隔: 0=全部显示, 1=隔一个显示, "preserveStartEnd"=只显示首尾
            fontSize={15} // 字体大小（如果不用CustomTick的话）
            axisLine={false} // 是否显示轴线: true | false
            tickLine={false} // 是否显示刻度线: true | false
            // angle={-45} // 文字旋转角度: 0, -45, -90 等（不用CustomTick时有效）
            // textAnchor="end" // 文字对齐: "start" | "middle" | "end"（不用CustomTick时有效）
            // tickMargin={10} // 刻度与标签的距离
            // minTickGap={5} // 标签间最小间距
            // tickFormatter={(value) => value} // 自定义格式化函数
          />
          <YAxis
            label={{ 
              value: 'Number of mentions', 
              angle: -90, 
              position: 'insideLeft',
              offset: 20, // 增加偏移量让标签更往下
              style: {
                textAnchor: 'middle'
              }
            }}
            fontSize={12}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="top"
            height={36}
            iconSize={12}
            wrapperStyle={{
              paddingBottom: '20px',
            }}
          />
          <Bar 
            dataKey={positiveDataKey}
            stackId="mentions"
            fill="#22c55e"
            name="Positive Mentions"
            radius={[0, 0, 0, 0]}
            style={{ cursor: 'pointer' }}
            onClick={handleBarClick}
          />
          <Bar 
            dataKey={negativeDataKey}
            stackId="mentions"
            fill="#ef4444"
            name="Negative Mentions"
            radius={[4, 4, 0, 0]}
            style={{ cursor: 'pointer' }}
            onClick={handleBarClick}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
} 