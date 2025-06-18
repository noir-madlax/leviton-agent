import { NextRequest } from 'next/server';

// 后端API配置
const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// 模拟延迟函数（保留用于错误处理时的降级）
function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 降级用的Mock图表数据（仅在后端不可用时使用）
const fallbackMockData = {
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
    explanation: "这是一个展示6个月销售和利润趋势的折线图（降级数据）。",
    insights: "后端连接失败，显示降级数据。请检查后端服务状态。"
  }
};

// 处理后端SSE流式响应
async function streamFromBackend(query: string, controller: ReadableStreamDefaultController) {
  const encoder = new TextEncoder();
  
  try {
    // 调用后端的SSE流式接口
    const response = await fetch(`${BACKEND_URL}/agent-stream?query=${encodeURIComponent(query)}`, {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    });

    if (!response.ok) {
      throw new Error(`后端响应错误: ${response.status} ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('后端响应体为空');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { value, done } = await reader.read();
        
        if (done) {
          // 处理剩余缓冲区内容
          if (buffer.trim()) {
            await processSSEMessage(buffer, controller, encoder);
          }
          break;
        }

        // 将接收到的数据添加到缓冲区
        buffer += decoder.decode(value, { stream: true });
        
        // 按行处理SSE数据
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留最后一个可能不完整的行

        for (const line of lines) {
          if (line.trim()) {
            await processSSEMessage(line, controller, encoder);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }

  } catch (error) {
    console.error('后端连接失败:', error);
    // 降级到mock数据
    controller.enqueue(encoder.encode('⚠️ 后端连接失败，使用降级数据...\n\n'));
    await delay(500);
    
    // 返回降级的mock数据
    controller.enqueue(encoder.encode('<<<CHART_START>>>\n'));
    controller.enqueue(encoder.encode('<<<CHART_TYPE:fallback>>>\n'));
    controller.enqueue(encoder.encode(JSON.stringify(fallbackMockData, null, 2)));
    controller.enqueue(encoder.encode('\n<<<CHART_END>>>\n\n'));
    
    controller.enqueue(encoder.encode(`降级说明：${fallbackMockData.chartData.explanation}\n\n`));
    controller.enqueue(encoder.encode(`系统提示：${fallbackMockData.chartData.insights}\n`));
  }
}

// 处理单个SSE消息
async function processSSEMessage(line: string, controller: ReadableStreamDefaultController, encoder: TextEncoder) {
  if (!line.trim()) return;
  
  // SSE格式：data: {json}
  if (line.startsWith('data: ')) {
    try {
      const jsonStr = line.substring(6); // 移除 "data: " 前缀
      
      // 跳过特殊标记
      if (jsonStr === '[DONE]' || jsonStr.includes('[DONE]')) {
        return;
      }
      
      const data = JSON.parse(jsonStr);
      
      // 处理不同类型的后端响应
      if (data.status === 'error') {
        controller.enqueue(encoder.encode(`❌ 错误: ${data.error}\n\n`));
      } else if (data.status === 'started') {
        controller.enqueue(encoder.encode(`🚀 ${data.message}\n\n`));
      } else if (data.status === 'processing') {
        controller.enqueue(encoder.encode(`⚙️ ${data.message}\n\n`));
      } else if (data.status === 'streaming') {
        // 检查是否包含图表数据
        if (data.message && typeof data.message === 'string') {
          // 尝试解析是否为JSON格式的图表数据
          if (data.message.startsWith('{') && (data.message.includes('chartData') || data.message.includes('chart1') || data.message.includes('chart2'))) {
            try {
              const chartData = JSON.parse(data.message);
              
              // 检查是否为有效的图表数据格式
              const isValidChartData = chartData.chartData || chartData.chart1 || chartData.chart2;
              
              if (isValidChartData) {
                console.log('🎯 检测到图表数据:', chartData);
                
                // 添加图表标记
                controller.enqueue(encoder.encode('<<<CHART_START>>>\n'));
                controller.enqueue(encoder.encode('<<<CHART_TYPE:backend>>>\n'));
                controller.enqueue(encoder.encode(JSON.stringify(chartData, null, 2)));
                controller.enqueue(encoder.encode('\n<<<CHART_END>>>\n\n'));
                
                // 添加说明文字
                if (chartData.chartData) {
                  // 单图表格式
                  controller.enqueue(encoder.encode(`📊 图表说明：${chartData.chartData.explanation || '已生成图表'}\n\n`));
                  controller.enqueue(encoder.encode(`💡 数据洞察：${chartData.chartData.insights || '数据分析完成'}\n\n`));
                } else {
                  // 多图表格式
                  controller.enqueue(encoder.encode('📊 多维度分析图表已生成\n\n'));
                  if (chartData.chart1) {
                    controller.enqueue(encoder.encode(`📈 图表1：${chartData.chart1.explanation || '图表1已生成'}\n\n`));
                    controller.enqueue(encoder.encode(`💡 洞察1：${chartData.chart1.insights || '分析完成'}\n\n`));
                  }
                  if (chartData.chart2) {
                    controller.enqueue(encoder.encode(`📈 图表2：${chartData.chart2.explanation || '图表2已生成'}\n\n`));
                    controller.enqueue(encoder.encode(`💡 洞察2：${chartData.chart2.insights || '分析完成'}\n\n`));
                  }
                }
                
                console.log('✅ 图表数据已发送到前端');
                return; // 图表数据处理完成，不再作为普通消息处理
              } else {
                console.log('⚠️ 不是有效的图表数据格式');
              }
            } catch (parseError) {
              console.error('❌ 解析图表数据失败:', parseError);
            }
          }
          
          // 普通文本消息或解析失败的消息
          controller.enqueue(encoder.encode(`${data.message}\n\n`));
        }
      } else if (data.status === 'completed') {
        controller.enqueue(encoder.encode(`✅ ${data.message}\n\n`));
      } else {
        // 其他未知格式，直接输出
        controller.enqueue(encoder.encode(`${JSON.stringify(data)}\n\n`));
      }
      
    } catch {
      // 如果不是有效JSON，可能是普通文本，直接输出
      controller.enqueue(encoder.encode(`${line}\n\n`));
    }
  } else {
    // 非SSE格式的行，直接输出
    controller.enqueue(encoder.encode(`${line}\n\n`));
  }
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

    if (!query.trim()) {
      return new Response('Empty query', { status: 400 });
    }

    // 创建流式响应
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // 调用后端流式接口
          await streamFromBackend(query, controller);
          
          // 完成流式传输
          controller.close();
        } catch (error) {
          console.error('流式传输错误:', error);
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