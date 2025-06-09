# Chart Agent 技术设计文档

## 整体架构

### 技术方案：方案3 - React组件代码动态生成
```
用户提问 → LLM生成图表代码 → 前端编译执行 → 动态渲染图表
```

### 核心优势
- 无需预定义图表类型
- 完全动态，支持任何复杂的自定义图表
- 自动化程度高，无需预知用户问题
- LLM可根据数据特点选择最合适的图表类型

## 后端API设计

### 图表生成接口
```javascript
POST /api/generate-chart

// 输入
{
  userQuery: "显示最近3个月的销售趋势"
}

// 输出
{
  chartCode: "完整的React组件代码字符串",
  explanation: "图表说明文字", 
  dataInsights: "数据洞察结论"
}
```

### 核心方法
```javascript
generateChartFromQuery(userQuery) {
  // 1. 分析用户问题
  // 2. 访问CSV数据源
  // 3. 调用LLM生成图表代码
  // 4. 返回完整的React组件代码字符串
}
```

## 前端状态管理

### 状态定义
```javascript
useChartState() {
  // 状态变量
  - currentChartCode: 当前图表代码字符串
  - chartHistory: 历史图表记录数组
  - isLoading: 图表生成状态
  - error: 错误信息
  
  // 状态更新方法
  - updateChart(newChartCode)
  - addToHistory(chartData)
  - setLoading(status)
  - clearError()
}
```

## 动态代码编译器

### 核心组件：DynamicChartCompiler
```javascript
DynamicChartCompiler {
  // 主要方法
  compileJSX(codeString) {
    // 使用 @babel/standalone 编译JSX
    // 输入: JSX字符串
    // 输出: 可执行的JavaScript代码
  }
  
  executeCode(compiledCode) {
    // 使用 new Function() 执行代码
    // 输入: 编译后的JavaScript
    // 输出: React组件
  }
  
  validateCode(codeString) {
    // 基础代码验证
    // 检查允许的导入包
  }
}
```

### 执行流程
```javascript
// 1. 接收LLM生成的代码字符串
const codeString = `
  import { LineChart, Line, XAxis, YAxis } from 'recharts';
  export default function DynamicChart() {
    const data = [...];
    return <LineChart data={data}>...</LineChart>;
  }
`;

// 2. 编译JSX
const compiledCode = compileJSX(codeString);

// 3. 执行代码获取组件
const ChartComponent = executeCode(compiledCode);

// 4. 渲染组件
<ChartComponent />
```

## 图表渲染引擎

### 核心组件：ChartRenderer
```javascript
ChartRenderer {
  // 主要方法
  renderDynamicChart(chartCode) {
    // 渲染动态生成的图表组件
    // 管理组件生命周期
  }
  
  updateChart(newChartCode) {
    // 更新图表显示
    // 处理组件切换
  }
  
  cleanupChart() {
    // 清理旧图表资源
    // 释放内存
  }
}
```

## 聊天界面集成

### 核心组件：ChatInterface
```javascript
ChatInterface {
  // 主要方法
  sendMessage(message) {
    // 发送用户消息到后端
    // 触发图表生成流程
  }
  
  receiveResponse(response) {
    // 接收LLM响应
    // 更新聊天记录
    // 触发图表更新
  }
  
  updateChatHistory(newMessage) {
    // 更新聊天历史记录
  }
  
  triggerChartGeneration(userQuery) {
    // 调用图表生成API
    // 更新图表状态
  }
}
```

## 布局管理器

### 核心组件：AgentLayout
```javascript
AgentLayout {
  // 主要方法
  initializeLayout() {
    // 初始化左右分栏布局
    // 设置响应式设计
  }
  
  syncChatAndChart() {
    // 同步聊天和图表状态
    // 确保数据一致性
  }
  
  handleResize() {
    // 处理窗口大小变化
    // 调整布局比例
  }
}
```

## 完整数据流

### Phase 1: 用户交互
```
用户在左侧输入问题 → ChatInterface.sendMessage()
```

### Phase 2: 后端处理
```
API调用 → 访问CSV数据 → 调用LLM → 返回图表代码
```

### Phase 3: 前端编译
```
接收代码字符串 → DynamicChartCompiler.compileJSX() → 生成可执行组件
```

### Phase 4: 图表渲染
```
ChartRenderer.renderDynamicChart() → 显示在右侧区域
```

### Phase 5: 状态同步
```
更新聊天历史 → 更新图表历史 → UI状态同步
```

## 技术栈

### 必需依赖包
- `@babel/standalone`: JSX编译
- `recharts`: 图表库
- `react`: React框架
- `next.js`: 项目框架

### 核心文件结构
```
components/
├── chat/
│   ├── ChatInterface.jsx
│   └── MessageList.jsx
├── charts/
│   ├── DynamicChartCompiler.jsx
│   ├── ChartRenderer.jsx
│   └── ChartErrorBoundary.jsx
├── layout/
│   ├── AgentLayout.jsx
│   └── SplitPanel.jsx
└── hooks/
    ├── useChartState.js
    └── useDynamicCompiler.js
```

## 主要方法调用链

```
用户提问
↓
ChatInterface.sendMessage()
↓
API.generateChartFromQuery()
↓
useChartState.updateChart()
↓
DynamicChartCompiler.compileJSX()
↓
ChartRenderer.renderDynamicChart()
↓
页面显示新图表
```

## 关键实现细节

### 动态代码执行原理
```javascript
// 1. 代码字符串转换
const codeString = "LLM生成的React组件代码";

// 2. JSX编译
const compiledCode = transform(codeString, {
  presets: ['react']
}).code;

// 3. 代码执行
const createComponent = new Function(
  'React', 'Recharts',
  `${compiledCode}; return DynamicChart;`
);

// 4. 获取组件
const Component = createComponent(React, require('recharts'));

// 5. 渲染组件
<Component />
```

### 状态管理模式
```javascript
// 使用Context在左右两侧共享状态
const ChartContext = createContext();

export const ChartProvider = ({ children }) => {
  const [currentChart, setCurrentChart] = useState(null);
  
  const updateChart = (newChart) => {
    setCurrentChart(newChart);
  };
  
  return (
    <ChartContext.Provider value={{ currentChart, updateChart }}>
      {children}
    </ChartContext.Provider>
  );
};
``` 