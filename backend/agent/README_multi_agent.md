# 多 Agent 架构设计文档

## 概述

本项目基于 [Hugging Face smolagents 多 Agent 示例](https://huggingface.co/docs/smolagents/examples/multiagents) 重构了原有的单一 Agent 架构，实现了多 Agent 协作系统。

## 架构设计

```
                    +------------------+
                    |   Manager Agent  |
                    |    (CodeAgent)   |
                    +------------------+
                             |
                             |
        +--------------------+--------------------+
        |                                        |
   +------------------+                +------------------+
   | Database Agent   |                |Chart Generation  |
   | (CodeAgent)      |                |     Agent        |
   +------------------+                | (ToolCallingAgent)|
           |                           +------------------+
           |
   +-------+-------+
   |               |
Product Query   Review Query
   Tool            Tool
   +               +
   MCP Tools (Supabase)
```

## 组件说明

### 1. Manager Agent (管理 Agent)
- **类型**: `CodeAgent`
- **职责**: 
  - 接收用户查询
  - 协调和管理下级 Agent
  - 执行代码分析和可视化
  - 生成最终答案
- **特点**:
  - 具有高级推理能力
  - 支持代码执行
  - 可以进行数据分析和图表生成
- **Prompt ID**: 11

### 2. Database Agent (数据库查询 Agent)
- **类型**: `CodeAgent`
- **职责**:
  - 处理所有数据库相关操作
  - 执行 MCP 工具调用
  - 查询产品和评论数据
  - 数据检索和过滤
- **工具集**:
  - `ProductQueryTool`: 产品查询工具
  - `ReviewQueryTool`: 评论查询工具
  - `MCP Tools`: Supabase 数据库工具集
- **Prompt ID**: 8

### 3. Chart Generation Agent (图表代码生成 Agent)
- **类型**: `ToolCallingAgent`
- **职责**:
  - 专门负责生成前端 JavaScript 绘制图表的代码
  - 根据数据生成各种类型的图表代码
  - 支持 Recharts、Chart.js 等图表库
  - 生成完整的 HTML 和 JavaScript 代码
- **特点**:
  - 专注于代码生成能力
  - 支持多种图表库
  - 不需要外部工具，主要依赖模型的代码生成能力
- **Prompt ID**: 9

## 工作流程

1. **用户查询接收**: Manager Agent 接收用户查询
2. **任务分析**: Manager Agent 分析查询需求
3. **任务委托**: 
   - 如需数据库操作，委托给 Database Agent
   - 如需图表代码生成，委托给 Chart Generation Agent
4. **专业处理**: 
   - Database Agent 执行具体的数据库查询
   - Chart Generation Agent 生成图表代码
5. **结果返回**: 各专业 Agent 将结果返回给 Manager Agent
6. **数据整合**: Manager Agent 对数据进行分析、整合等处理
7. **答案生成**: 生成最终的用户答案

## 核心文件

### `agent/core/database_agent.py`
数据库查询 Agent 的实现文件：
- `DatabaseAgent` 类
- 初始化 MCP 工具集
- 数据库查询方法

### `agent/core/chart_generation_agent.py`
图表代码生成 Agent 的实现文件：
- `ChartGenerationAgent` 类
- 图表代码生成方法
- 支持多种图表库

### `agent/core/agent_manager.py`
多 Agent 管理器的重构文件：
- `AgentManager` 类重构
- 三个 Agent 系统初始化
- Agent 间协调管理

## 配置说明

### 环境变量
- `MODEL_ID`: 使用的 LLM 模型（默认：`google/gemini-2.5-pro-preview`）
- `API_KEY`: OpenRouter API 密钥
- `MCP_ACCESS_TOKEN`: Supabase MCP 访问令牌
- `MAX_ITERATIONS`: 最大迭代次数

### Agent 配置
```python
# Manager Agent 配置
manager_agent = CodeAgent(
    tools=[],  # 不直接使用工具，而是委托给下级 Agent
    model=model,
    stream_outputs=True,
    managed_agents=[
        self.database_agent.get_agent()  # 管理数据库 Agent
        # self.chart_generation_agent.get_agent()  # 管理图表代码生成 Agent (可选)
    ],
    max_steps=settings.MAX_ITERATIONS
)

# Database Agent 配置
database_agent = CodeAgent(
    tools=database_tools,  # MCP 工具集
    model=model,
    max_steps=5,
    name="database_agent",
    description="专门负责数据库查询、数据检索和MCP工具调用的代理"
)

# Chart Generation Agent 配置
chart_generation_agent = ToolCallingAgent(
    tools=[],  # 主要依赖代码生成能力
    model=model,
    max_steps=2,
    name="chart_generation_agent",
    description="专门负责生成前端 JavaScript 图表代码的代理"
)
```

## 使用示例

### 基本使用
```python
from agent.core.agent_manager import AgentManager

# 创建管理器
agent_manager = AgentManager()

# 初始化多 Agent 系统
await agent_manager.initialize_agent()

# 执行查询
result = await agent_manager.run_query("查询最新的产品数据并生成图表")
```

### 直接使用专业 Agent
```python
# 获取数据库 Agent
db_agent = agent_manager.get_database_agent()
result = await db_agent.query_database("查询产品表")

# 获取图表代码生成 Agent
chart_agent = agent_manager.get_chart_generation_agent()
chart_code = await chart_agent.generate_chart_code("生成柱状图代码")
```

## 优势

1. **职责分离**: 每个 Agent 专注于特定的任务
2. **可扩展性**: 易于添加新的专用 Agent
3. **错误隔离**: Agent 间错误不会相互影响
4. **性能优化**: 各项功能专门优化
5. **维护性**: 代码结构更清晰，易于维护
6. **专业化**: 图表代码生成独立处理，提高质量

## 测试

### 运行测试脚本验证多 Agent 架构：

#### 1. 完整系统测试
```bash
cd backend
python test_complete_agent_system.py
```

#### 2. 多 Agent 协作测试
```bash
cd backend
python test_multi_agent.py
```

#### 3. 图表代码生成 Agent 测试
```bash
cd backend
python test_chart_generation_agent.py
```

#### 4. 系统提示词功能测试
```bash
cd backend
python test_system_prompt.py
```

## 注意事项

1. **资源管理**: 确保正确清理 MCP 工具集资源
2. **错误处理**: 各 Agent 需要独立的错误处理机制
3. **并发控制**: 注意 Agent 间的并发调用
4. **配置同步**: 保持各 Agent 的配置一致性
5. **模型选择**: 不同 Agent 可使用不同模型优化性能

## 通用 System Prompt 功能

### 概述
系统提供了通用的 `append_custom_system_prompt` 方法，可以为不同的 Agent 使用不同的数据库 prompt ID。

### 核心方法

#### `append_custom_system_prompt(agent, prompt_id, additional_instructions="")`
- **agent**: 要更新的 agent 实例
- **prompt_id**: 数据库中的 prompt 记录 ID
- **additional_instructions**: 额外的指令文本（可选）

#### `reload_system_prompt_from_database(agent=None, prompt_id=1)`
- **agent**: 要更新的 agent 实例，默认为管理 Agent
- **prompt_id**: 要加载的 prompt ID，默认为 1

**注意**: 不再有专用的 `_append_custom_system_prompt` 方法，所有 Agent 都统一使用 `append_custom_system_prompt` 公共方法。

### 使用示例

```python
# 为管理 Agent 使用 ID=11 的 prompt
await agent_manager.append_custom_system_prompt(
    agent=manager_agent,
    prompt_id=11
)

# 为数据库 Agent 使用 ID=8 的 prompt
await agent_manager.append_custom_system_prompt(
    agent=database_agent.get_agent(),
    prompt_id=8
)

# 为图表代码生成 Agent 使用 ID=9 的 prompt
await agent_manager.append_custom_system_prompt(
    agent=chart_generation_agent.get_agent(),
    prompt_id=9
)

# 重新加载特定 Agent 的 prompt
await agent_manager.reload_system_prompt_from_database(
    agent=target_agent,
    prompt_id=3
)
```

### 默认配置
- **管理 Agent**: 使用 prompt ID = 11
- **数据库 Agent**: 使用 prompt ID = 8
- **图表代码生成 Agent**: 使用 prompt ID = 9

### 便捷方法
各 Agent 提供了便捷的方法：
```python
# 数据库 Agent 重新加载自己的 prompt
await database_agent.reload_system_prompt(prompt_id=8)

# 图表代码生成 Agent 重新加载自己的 prompt
await chart_generation_agent.reload_system_prompt(prompt_id=9)
```

### 测试
运行示例脚本测试 system_prompt 功能：
```bash
cd backend
python test_system_prompt.py
```

## 扩展建议

未来可以考虑添加更多专用 Agent：
- **Analysis Agent**: 专门负责数据分析 (prompt_id=4)
- **Export Agent**: 专门负责数据导出 (prompt_id=5)
- **Cache Agent**: 专门负责缓存管理 (prompt_id=6)
- **Report Agent**: 专门负责报告生成 (prompt_id=7)

每个新的 Agent 都可以使用独立的 prompt ID 来获取专门的指令配置。

## 文件结构

### 新增文件
- `agent/core/chart_generation_agent.py`: 图表代码生成 Agent 实现
- `test_chart_generation_agent.py`: 图表代码生成 Agent 测试
- `test_complete_agent_system.py`: 完整多 Agent 系统测试
- `test_multi_agent.py`: 多 Agent 协作测试
- `test_system_prompt.py`: 系统提示词功能测试

### 主要修改文件
- `agent/core/agent_manager.py`: 支持三个 Agent 的管理
- `config.py`: 更新模型配置
- `main.py`: 集成新的多 Agent 架构
- `agent/services/query_processor.py`: 查询处理器优化
- `agent/streaming/stream_handler.py`: 流式响应处理优化 