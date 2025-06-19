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
- 箭头函数参数不应该有引号：`({name, percent})` 而不是 `({'name, percent'})`
- 模板字符串中不应该有多余的引号和括号：`${(percent * 100).toFixed(0)}` 而不是 `${'(percent * 100).toFixed(0)'}`
- JSX 属性值的语法必须正确

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

// ❌ 箭头函数参数有引号
label={({'name, percent'}) => `${name} ${percent}%`}

// ❌ 模板字符串中有多余的引号和括号
label={({name, percent}) => `${name} ${'(percent * 100).toFixed(0)'}%`}

// ❌ JSX 属性语法错误
<Pie label={({'value'}) => value} />
```

## 集成到 main.py

服务已集成到 `main.py` 的 `check_reasoning_and_plot` 函数中，会在 Agent 生成最终答案时自动进行验证。

### 验证失败处理机制

当验证失败时，`check_reasoning_and_plot` 函数会**抛出异常**而不是返回 `False`。这种设计有以下优势：

1. **详细错误信息**：异常消息包含具体的验证错误和改进建议
2. **Agent 自动改进**：smolagents 框架会捕获异常并将错误信息提供给 Agent
3. **迭代优化**：Agent 可以根据错误信息自动调整和改进代码

#### 异常处理流程

```python
def check_reasoning_and_plot(final_answer, agent_memory):
    try:
        # 执行验证
        validation_result = validate_chart_response(final_answer)
        
        # 如果验证失败，抛出详细的异常信息
        if not validation_result["overall_valid"]:
            errors = chart_validation.get("errors", [])
            error_details = [f"{i+1}. {error}" for i, error in enumerate(errors)]
            
            error_msg = f"图表验证失败，发现 {len(errors)} 个错误:\n"
            error_msg += "\n".join(error_details)
            error_msg += "\n\n请检查以下问题:"
            error_msg += "\n- JSX 语法是否正确（特别是箭头函数参数格式）"
            error_msg += "\n- 模板字符串中的引号是否正确"
            error_msg += "\n- Recharts 组件属性格式是否正确（如 margin={{...}}）"
            error_msg += "\n- 数据结构是否符合组件要求"
            
            raise Exception(error_msg)
            
        return True
    except Exception as e:
        # 重新抛出，供 Agent 获取错误信息
        raise
```

#### 好处说明

- **精确定位问题**：Agent 能够获得具体的语法错误位置和类型
- **自动修复**：Agent 可以根据错误信息自动修正代码
- **学习改进**：通过反复的错误反馈，Agent 能逐步提高代码质量
- **调试友好**：开发者也能从日志中看到详细的验证过程

这种设计确保了 Agent 能够持续改进，直到生成完全正确的 Recharts 代码。 