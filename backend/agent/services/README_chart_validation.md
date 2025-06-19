# 图表验证服务使用说明

## 概述

`ChartValidationService` 是一个专门用于验证 LLM 生成的 Recharts 图表代码的服务。它确保生成的代码安全且能够在前端正确渲染。

## 主要功能

### 1. 安全检查
- 检测危险的 JavaScript 函数（`eval`, `setTimeout`, `fetch` 等）
- 防止恶意代码执行

### 2. 语法验证
- 检查 JSX 语法正确性
- 验证括号匹配
- 检查 React 组件结构

### 3. Recharts 特定验证
- 验证 Recharts 组件使用
- 检查 `margin` 属性格式
- 验证数据结构

### 4. JSON 结构验证
- 支持单图表和多图表格式
- 验证必需字段（`code`, `explanation`, `insights`）

## 使用方法

### 基本使用

```python
from agent.services.chart_validation_service import validate_chart_response

# 验证图表响应
response = '{"chartData": {"code": "...", "explanation": "...", "insights": "..."}}'
result = validate_chart_response(response)

if result["overall_valid"]:
    print("✅ 验证成功")
else:
    print("❌ 验证失败")
    print(result["chart_validation"]["errors"])
```

### 在 Agent 中使用

```python
from agent.services.chart_validation_service import chart_validation_service

def check_reasoning_and_plot(final_answer, agent_memory):
    validation_result = chart_validation_service.validate_json_string(final_answer)
    return validation_result["overall_valid"]
```

## 验证规则

### 安全规则
- 不允许 `eval()`, `Function()`, `setTimeout()` 等危险函数
- 不允许访问 `window`, `document`, `process` 等全局对象

### 语法规则
- `margin` 属性必须使用双大括号格式：`margin={{ top: 20, ... }}`
- 必须包含 `DynamicChart` 组件定义
- 必须使用 `ResponsiveContainer`

### JSON 结构规则
- 支持格式：`{"chartData": {...}}` 或 `{"chart1": {...}, "chart2": {...}}`
- 每个图表必须包含：`code`, `explanation`, `insights` 字段

## 输出格式

```python
{
    "is_valid_json": bool,
    "json_data": dict | None,
    "chart_validation": {
        "valid": bool,
        "errors": list,
        "warnings": list,
        "chart_count": int,
        "chart_details": [
            {
                "key": str,
                "valid": bool,
                "errors": list,
                "warnings": list,
                "info": list
            }
        ]
    },
    "overall_valid": bool
}
```

## 示例

### 正确的代码示例

```javascript
const data = [{"name": "A", "value": 100}];
const DynamicChart = () => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 40, bottom: 120 }}>
        <XAxis dataKey="name" />
        <YAxis />
        <Bar dataKey="value" fill="#8884d8" />
      </BarChart>
    </ResponsiveContainer>
  );
};
```

### 错误的代码示例

```javascript
// ❌ margin 格式错误
<BarChart data={data} margin={ top: 20, right: 30 }>

// ❌ 包含危险代码
eval("console.log('danger')");

// ❌ 缺少 ResponsiveContainer
<BarChart data={data}>
```

## 集成到 main.py

服务已集成到 `main.py` 的 `check_reasoning_and_plot` 函数中，会在 Agent 生成最终答案时自动进行验证。 