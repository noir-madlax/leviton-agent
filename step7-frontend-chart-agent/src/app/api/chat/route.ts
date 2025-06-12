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

// 多图表示例 - 产品市场分析
const mockMultiChartExample = {
  chart1: {
    code: `const painPointData = [
  { category: '安装困难', reviewCount: 45, severity: 4.2, affectedCustomers: 180 },
  { category: '产品耐用性', reviewCount: 38, severity: 4.8, affectedCustomers: 150 },
  { category: '用户体验', reviewCount: 67, severity: 3.5, affectedCustomers: 280 },
  { category: '性能参数', reviewCount: 23, severity: 4.0, affectedCustomers: 90 },
  { category: '外观设计', reviewCount: 15, severity: 2.8, affectedCustomers: 60 }
];

const DynamicChart = () => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart data={painPointData} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="reviewCount" 
          name="评论数量"
          label={{ value: '评论数量', position: 'insideBottom', offset: -10 }}
        />
        <YAxis 
          dataKey="severity"
          name="严重程度"
          domain={[1, 5]}
          label={{ value: '严重程度评分', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip 
          formatter={(value, name) => {
            if (name === 'affectedCustomers') return [\`\${value}人\`, '影响客户数'];
            if (name === 'severity') return [\`\${value}分\`, '严重程度'];
            if (name === 'reviewCount') return [\`\${value}条\`, '评论数量'];
            return [value, name];
          }}
          labelFormatter={(label) => \`痛点类别: \${label}\`}
        />
        <Legend />
        <Scatter 
          dataKey="severity" 
          fill="#ff6b6b"
          name="严重程度评分"
        >
          {painPointData.map((entry, index) => (
            <Cell key={\`cell-\${index}\`} 
              fill={entry.severity > 4 ? '#ff4757' : entry.severity > 3 ? '#ffa502' : '#7bed9f'} 
            />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
};`,
    explanation: "该散点图展示了客户痛点的严重程度与评论数量的关系。X轴表示每个痛点的评论数量，Y轴表示严重程度评分(1-5分)，点的颜色表示严重程度级别：红色(高严重度>4分)、橙色(中等严重度3-4分)、绿色(低严重度<3分)。",
    insights: "从图表可以看出：用户体验问题虽然严重程度中等(3.5分)，但评论数量最多(67条)，影响客户最广泛，需要优先关注。产品耐用性问题严重程度最高(4.8分)且评论数量较多，是最需要立即解决的核心痛点。安装困难也是高严重度问题，建议改进安装指导或设计。"
  },
  chart2: {
    code: `const marketGapData = [
  { opportunity: '智能控制功能', demandIntensity: 85, gapLevel: 4.2, marketValue: 95 },
  { opportunity: '能耗优化', demandIntensity: 72, gapLevel: 3.8, marketValue: 80 },
  { opportunity: '多场景适配', demandIntensity: 68, gapLevel: 4.5, marketValue: 75 },
  { opportunity: '简化安装', demandIntensity: 90, gapLevel: 3.2, marketValue: 88 },
  { opportunity: '耐用性提升', demandIntensity: 78, gapLevel: 4.8, marketValue: 92 }
];

const DynamicChart = () => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart data={marketGapData} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="demandIntensity" 
          name="市场需求强度"
          domain={[0, 100]}
          label={{ value: '市场需求强度', position: 'insideBottom', offset: -10 }}
        />
        <YAxis 
          dataKey="gapLevel"
          name="解决方案缺口"
          domain={[1, 5]}
          label={{ value: '解决方案缺口程度', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip 
          cursor={{ strokeDasharray: '3 3' }}
          formatter={(value, name) => {
            if (name === 'marketValue') return [\`\${value}%\`, '市场价值'];
            if (name === 'gapLevel') return [\`\${value}分\`, '缺口程度'];
            if (name === 'demandIntensity') return [\`\${value}分\`, '需求强度'];
            return [value, name];
          }}
          labelFormatter={(label) => \`机会点: \${label}\`}
        />
        <Legend />
        <Scatter dataKey="gapLevel" fill="#3742fa" name="解决方案缺口程度">
          {marketGapData.map((entry, index) => (
            <Cell 
              key={\`cell-\${index}\`} 
              fill={entry.marketValue > 80 ? '#2ed573' : entry.marketValue > 60 ? '#ffa502' : '#ff6348'}
            />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
};`,
    explanation: "该市场机会优先级矩阵展示了不同优化机会的市场需求强度与当前解决方案缺口的关系。X轴表示市场需求强度(0-100分)，Y轴表示当前解决方案缺口程度(1-5分)，气泡颜色表示潜在市场价值：绿色(高价值>80%)、橙色(中等价值60-80%)、红色(低价值<60%)。",
    insights: "右上角的高价值机会点最值得投资：多场景适配(需求68分，缺口4.5分)和耐用性提升(需求78分，缺口4.8分)是最有潜力的优化方向。价格竞争力虽然需求最高(95分)，但缺口适中且市场价值相对较低，可能竞争激烈。简化安装需求很高但缺口较小，说明市场已有较好解决方案。"
  }
};

export async function POST(request: NextRequest) {
  try {
    const { messages } = await request.json();
    const lastMessage = messages[messages.length - 1];
    
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const message = lastMessage.content.toLowerCase();
    
    // 检查是否需要生成多图表（产品市场分析）
    const needsMultiChart = message.includes('产品市场分析') || 
                           message.includes('痛点分析') || 
                           message.includes('市场机会') ||
                           message.includes('竞争分析') ||
                           (message.includes('分析') && (message.includes('多个') || message.includes('维度')));
    
    if (needsMultiChart) {
      // 返回多图表响应
      const response = {
        role: 'assistant',
        content: '我已经为您生成了产品市场分析报告，包含客户痛点分析和市场机会分析两个维度的图表。',
        chartData: {
          ...mockMultiChartExample,
          timestamp: Date.now(),
          type: 'multiple'
        }
      };
      
      return NextResponse.json(response);
      
    } else {
      // 返回单图表响应（原有逻辑）
      let chartExample;
      
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
          timestamp: Date.now(),
          type: 'single'
        }
      };
      
      return NextResponse.json(response);
    }
    
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: '生成图表时出现错误，请稍后重试' },
      { status: 500 }
    );
  }
} 