import { NextRequest } from 'next/server';

// 模拟延迟函数
function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Mock图表数据 - 遵循step6-chart-code-samples.md格式
const mockChartData = {
  // 单图表示例
  singleChart: {
    chartData: {
      code: `const salesData = [
  { month: 'Jan', sales: 4000, profit: 2400, growth: 12 },
  { month: 'Feb', sales: 3000, profit: 1398, growth: -8 },
  { month: 'Mar', sales: 2000, profit: 9800, growth: 25 },
  { month: 'Apr', sales: 2780, profit: 3908, growth: 15 },
  { month: 'May', sales: 1890, profit: 4800, growth: -20 },
  { month: 'Jun', sales: 2390, profit: 3800, growth: 8 }
];

const DynamicChart = () => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={salesData} margin={{ top: 50, right: 30, left: 40, bottom: 80 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip formatter={(value, name) => [\`$\${value}\`, name]} />
        <Legend verticalAlign="top" height={36} />
        <Line type="monotone" dataKey="sales" stroke="#8884d8" strokeWidth={2} name="销售额" />
        <Line type="monotone" dataKey="profit" stroke="#82ca9d" strokeWidth={2} name="利润" />
      </LineChart>
    </ResponsiveContainer>
  );
};`,
      explanation: "这是一个展示6个月销售和利润趋势的折线图。可以清楚地看到销售额和利润的变化情况，帮助分析业务发展趋势。",
      insights: "从数据可以看出3月份利润达到峰值9800，而销售额在1月份最高4000。利润和销售额不完全正相关，说明可能存在成本控制的优化空间。5月份销售额下滑较大，需要重点关注。"
    }
  },

  // 多图表示例 - 来自step6-chart-code-samples.md
  multiChart: {
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
      <ScatterChart data={painPointData} margin={{ top: 50, right: 30, left: 40, bottom: 80 }}>
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
        <Legend verticalAlign="top" height={36} />
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
      <ScatterChart data={marketGapData} margin={{ top: 50, right: 30, left: 40, bottom: 80 }}>
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
        <Legend verticalAlign="top" height={36} />
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
  }
};

// 根据查询内容选择合适的mock数据
function getMockResponse(query: string) {
  const lowerQuery = query.toLowerCase();
  
  // 检查是否询问多维度分析
  if (lowerQuery.includes('痛点') || lowerQuery.includes('市场') || lowerQuery.includes('竞争') || 
      lowerQuery.includes('分析') || lowerQuery.includes('对比') || lowerQuery.includes('多个')) {
    return mockChartData.multiChart;
  }
  
  // 默认返回单图表
  return mockChartData.singleChart;
}

export async function POST(request: NextRequest) {
  try {
    const { messages } = await request.json();
    
    if (!messages || messages.length === 0) {
      return new Response('Missing messages', { status: 400 });
    }

    // 获取最新的用户消息
    const latestMessage = messages[messages.length - 1];
    const query = latestMessage.content || '';

    // 创建流式响应
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // 模拟思考过程
          await delay(500);
          controller.enqueue(encoder.encode('正在分析您的数据需求...\n\n'));
          
          await delay(800);
          controller.enqueue(encoder.encode('正在查询相关数据源...\n\n'));
          
          await delay(600);
          controller.enqueue(encoder.encode('正在生成可视化图表...\n\n'));
          
          await delay(700);
          
          // 根据查询返回相应的图表数据
          const mockResponse = getMockResponse(query);
          
          // 格式化输出 - 添加图表标记
          controller.enqueue(encoder.encode('<<<CHART_START>>>\n'));
          controller.enqueue(encoder.encode('<<<CHART_TYPE:analysis>>>\n'));
          controller.enqueue(encoder.encode(JSON.stringify(mockResponse, null, 2)));
          controller.enqueue(encoder.encode('\n<<<CHART_END>>>\n\n'));
          
          await delay(300);
          controller.enqueue(encoder.encode('<<<INSIGHTS_START>>>\n'));
          
          if (mockResponse.chartData) {
            // 单图表格式
            controller.enqueue(encoder.encode(`图表说明：${mockResponse.chartData.explanation}\n\n`));
            controller.enqueue(encoder.encode(`数据洞察：${mockResponse.chartData.insights}\n`));
          } else {
            // 多图表格式
            controller.enqueue(encoder.encode('多维度分析结果已生成，包含客户痛点分析和市场机会分析两个图表。\n\n'));
            if (mockResponse.chart1) {
              controller.enqueue(encoder.encode(`图表1说明：${mockResponse.chart1.explanation}\n\n`));
              controller.enqueue(encoder.encode(`图表1洞察：${mockResponse.chart1.insights}\n\n`));
            }
            if (mockResponse.chart2) {
              controller.enqueue(encoder.encode(`图表2说明：${mockResponse.chart2.explanation}\n\n`));
              controller.enqueue(encoder.encode(`图表2洞察：${mockResponse.chart2.insights}\n`));
            }
          }
          
          controller.enqueue(encoder.encode('<<<INSIGHTS_END>>>\n'));
          controller.close();
        } catch (error) {
          controller.error(error);
        }
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('API错误:', error);
    return new Response('内部服务器错误', { status: 500 });
  }
} 