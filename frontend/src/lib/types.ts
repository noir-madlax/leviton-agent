// 单个图表数据结构
export interface SingleChart {
  code: string;
  explanation: string;
  insights: string;
}

// 图表数据类型定义 - 支持单图表和多图表格式
export interface ChartData {
  // 单图表格式 (向后兼容) - 对应step6的 { chartData: {...} } 格式
  chartData?: SingleChart;
  
  // 多图表格式 - 对应step6的 { chart1: {...}, chart2: {...} } 格式
  chart1?: SingleChart;
  chart2?: SingleChart;
  chart3?: SingleChart;
  
  // 元数据
  timestamp: number;
  type: 'single' | 'multiple';
  chartType?: string; // 用于标识图表类型，如 'analysis', 'comparison' 等
}

// 聊天消息类型
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  chartData?: ChartData;
}

// 动态编译器类型
export interface CompilerResult {
  success: boolean;
  component?: React.ComponentType;
  error?: string;
}

// UI状态类型
export interface AppState {
  leftPanelWidth: number;
  rightPanelCollapsed: boolean;
} 