import { NextRequest, NextResponse } from 'next/server';

// Mock的图表代码示例
const mockChartExamples = [
  {
    type: "line",
    code: `
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import React from 'react';

export default function DynamicChart() {
  const data = [
    { name: 'Jan', sales: 4000, profit: 2400 },
    { name: 'Feb', sales: 3000, profit: 1398 },
    { name: 'Mar', sales: 2000, profit: 9800 },
    { name: 'Apr', sales: 2780, profit: 3908 },
    { name: 'May', sales: 1890, profit: 4800 },
    { name: 'Jun', sales: 2390, profit: 3800 }
  ];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="sales" stroke="#8884d8" strokeWidth={2} />
        <Line type="monotone" dataKey="profit" stroke="#82ca9d" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}`,
    explanation: "这是一个展示6个月销售和利润趋势的折线图。可以清楚地看到销售额和利润的变化情况。",
    insights: "3月份利润达到峰值，而销售额在1月份最高。利润和销售额不完全正相关，说明可能存在成本控制的优化空间。"
  },
  {
    type: "bar",
    code: `
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import React from 'react';

export default function DynamicChart() {
  const data = [
    { name: '产品A', sales: 4000, target: 3500 },
    { name: '产品B', sales: 3000, target: 3200 },
    { name: '产品C', sales: 2000, target: 2800 },
    { name: '产品D', sales: 2780, target: 2500 },
    { name: '产品E', sales: 1890, target: 2000 }
  ];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="sales" fill="#8884d8" name="实际销售" />
        <Bar dataKey="target" fill="#82ca9d" name="目标销售" />
      </BarChart>
    </ResponsiveContainer>
  );
}`,
    explanation: "这是一个对比各产品实际销售与目标销售的柱状图，帮助了解各产品的表现情况。",
    insights: "产品A和产品D超额完成销售目标，产品C表现不佳需要重点关注。整体来看，大部分产品都接近或超过了预期目标。"
  },
  {
    type: "pie",
    code: `
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import React from 'react';

export default function DynamicChart() {
  const data = [
    { name: '桌面端', value: 65, count: 6500 },
    { name: '移动端', value: 25, count: 2500 },
    { name: '平板端', value: 10, count: 1000 }
  ];

  const colors = ['#8884d8', '#82ca9d', '#ffc658'];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({name, percent}) => \`\${name} \${(percent * 100).toFixed(0)}%\`}
          outerRadius={120}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={\`cell-\${index}\`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value, name) => [value + '%', name]} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}`,
    explanation: "这是一个展示用户设备类型分布的饼图，显示了不同平台的用户占比情况。",
    insights: "桌面端用户占主导地位，约占65%的用户量。移动端用户占25%，显示出移动化趋势。平板端用户相对较少，仅占10%。"
  }
];

export async function POST(request: NextRequest) {
  try {
    const { messages } = await request.json();
    const lastMessage = messages[messages.length - 1];
    
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // 根据用户消息简单选择图表类型
    let chartExample;
    const message = lastMessage.content.toLowerCase();
    
    if (message.includes('趋势') || message.includes('变化') || message.includes('时间')) {
      chartExample = mockChartExamples[0]; // 折线图
    } else if (message.includes('对比') || message.includes('比较') || message.includes('产品')) {
      chartExample = mockChartExamples[1]; // 柱状图
    } else if (message.includes('占比') || message.includes('分布') || message.includes('比例')) {
      chartExample = mockChartExamples[2]; // 饼图
    } else {
      // 随机选择一个
      chartExample = mockChartExamples[Math.floor(Math.random() * mockChartExamples.length)];
    }
    
    const response = {
      role: 'assistant',
      content: `我已经根据您的需求生成了一个${chartExample.type === 'line' ? '折线' : chartExample.type === 'bar' ? '柱状' : '饼状'}图表。`,
      chartData: {
        code: chartExample.code,
        explanation: chartExample.explanation,
        insights: chartExample.insights,
        timestamp: Date.now()
      }
    };
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: '生成图表时出现错误，请稍后重试' },
      { status: 500 }
    );
  }
} 