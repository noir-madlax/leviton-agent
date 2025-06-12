// 图表数据类型定义
export interface ChartData {
  code: string;
  explanation: string;
  insights: string;
  timestamp: number;
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