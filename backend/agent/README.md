# Agent 模块架构说明

## 最近 Git 改动记录

### 最新改动 (2f50372 - 2025/06/26)
**更新代理管理器和数据库代理，启用额外的授权导入，调整模型ID为配置文件中的设置，优化描述信息以增强可读性**
- 修改文件：
  - `backend/agent/core/agent_manager.py` - 调整模型ID配置
  - `backend/agent/core/database_agent.py` - 启用额外授权导入，优化描述信息

### 第二次改动 (49ab729 - 2025/06/25)
**更新配置文件，调整模型ID和代理超时时间；重构多代理管理器，增加数据库和图表生成代理的初始化；优化查询处理器，处理rechart消息；简化前端消息处理逻辑，移除冗余代码**
- 新增文件：
  - `backend/agent/README_multi_agent.md` - 多代理系统文档
  - `backend/agent/core/chart_generation_agent.py` - 图表生成代理
  - `backend/agent/core/database_agent.py` - 数据库查询代理
- 修改文件：
  - `backend/agent/core/agent_manager.py` - 重构多代理管理器（+261行）
  - `backend/agent/services/query_processor.py` - 优化查询处理器
  - `backend/agent/streaming/stream_handler.py` - 简化前端消息处理逻辑

### 第三次改动 (960e847 - 2025/06/23)
**step2 通过后端rest调用了，生成了projects，稍微调整一下就可以把seg步骤接进来了**
- 新增文件：
  - `backend/agent/REF:OpenAI Customer Service Agent.md` - OpenAI客服代理参考文档

---

## 基于 SmolagAgent 的多代理架构概述

本项目采用 **Hugging Face SmolagAgent** 框架构建的多代理系统，实现了智能化的数据分析和图表生成功能。系统架构遵循分层设计原则，通过专业化代理分工协作，提供高效的AI驱动分析服务。

## 核心架构设计

### 1. 分层架构模式

```
┌─────────────────────────────────────────────────────────────┐
│                    管理层 (AgentManager)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │  Manager Agent  │  │   Monitoring   │  │ Query Proc.  │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                      代理层 (Agents)                         │
│  ┌─────────────────┐                    ┌─────────────────┐  │
│  │ Database Agent  │◄──────────────────►│Chart Gen Agent │  │
│  │   (数据查询)      │                    │   (图表生成)      │  │
│  └─────────────────┘                    └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     工具层 (Tools)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ MCP Supabase │  │Product Tools │  │Chart Validation │    │
│  │    Tools     │  │              │  │    Service      │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心组件

#### 2.1 AgentManager - 多代理管理器
**位置**: `backend/agent/core/agent_manager.py`

- **职责**: 统一管理所有代理的生命周期，协调代理间通信
- **核心功能**:
  - 初始化和配置所有子代理
  - 管理系统级 system_prompt 
  - 处理代理间消息路由
  - 监控系统状态和错误处理
- **架构特点**: 采用 Hugging Face SmolagAgent 的 `managed_agents` 模式

#### 2.2 DatabaseAgent - 数据库查询代理
**位置**: `backend/agent/core/database_agent.py`

- **职责**: 专门负责数据库查询和 MCP 工具调用
- **核心功能**:
  - 通过 MCP Supabase Server 执行数据库查询
  - 产品信息和评论数据检索
  - 复杂数据分析和聚合操作
- **技术栈**: `CodeAgent` + MCP ToolCollection
- **工具集成**: Supabase MCP Server (`@supabase/mcp-server-supabase`)

#### 2.3 ChartGenerationAgent - 图表代码生成代理
**位置**: `backend/agent/core/chart_generation_agent.py`

- **职责**: 生成前端 JavaScript 图表代码
- **核心功能**:
  - 基于数据生成 Recharts 图表代码
  - 图表类型自动识别和优化
  - 响应式图表布局生成
- **技术栈**: `ToolCallingAgent` + Claude Sonnet 4
- **代码验证**: 集成 Chart Validation Service

### 3. 服务层组件

#### 3.1 QueryProcessor - 查询处理器
**位置**: `backend/agent/services/query_processor.py`

- **功能**: 预处理用户查询，拼接系统提示词
- **状态**: ⚠️ 已废弃 (DeprecationWarning)
- **替代方案**: 功能已集成到 AgentManager 的 `append_custom_system_prompt` 方法

#### 3.2 ProductPromptService - 提示词服务
**位置**: `backend/agent/services/product_prompt_service.py`

- **功能**: 从数据库动态加载和管理 AI 提示词
- **数据源**: Supabase `product_prompts` 表
- **集成**: 支持多代理系统的提示词个性化配置

#### 3.3 ChartValidationService - 图表验证服务
**位置**: `backend/agent/services/chart_validation_service.py`

- **功能**: 验证生成的图表代码语法和安全性
- **验证范围**: JSX 语法、属性值、标签结构
- **错误处理**: 提供详细的语法错误诊断和修复建议

### 4. 工具层

#### 4.1 MCP 工具集成
- **Supabase MCP Server**: 提供数据库查询能力
- **认证管理**: 通过 `MCP_ACCESS_TOKEN` 进行安全认证
- **工具信任**: `trust_remote_code=True` 启用远程代码信任

#### 4.2 产品分析工具
**位置**: `backend/agent/tools/product_review_tools.py`

- **ProductQueryTool**: 产品信息查询
- **ReviewQueryTool**: 评论数据分析
- **集成方式**: 通过 SmolagAgent 工具系统注册

### 5. 流式处理

#### 5.1 StreamHandler - 流式响应处理器
**位置**: `backend/agent/streaming/stream_handler.py`

- **功能**: 处理 AI 代理的流式输出
- **特性**: 支持实时数据流传输和前端渲染
- **协议**: Server-Sent Events (SSE)

### 6. 验证器层

#### 6.1 ChartValidator - 图表验证器
**位置**: `backend/agent/validators/chart_validator.py`

- **功能**: 
  - JSON 格式验证 (`is_valid_json`)
  - 推理和绘图逻辑检查 (`check_reasoning_and_plot`)
- **集成**: 作为 `final_answer_checks` 集成到代理工作流

### 7. 配置和依赖管理

#### 7.1 配置管理
- **模型配置**: OpenAI/Anthropic 模型通过 OpenRouter API
- **超时设置**: `MAX_ITERATIONS` 控制代理最大执行步数
- **API密钥**: 统一的环境变量管理

#### 7.2 依赖注入
**位置**: `backend/agent/dependencies.py`

- **ProductPromptService** 依赖注入
- **Repository** 层解耦
- **数据库连接** 统一管理

## 技术特性

### 1. 多代理协作模式
- **管理代理**: 统筹全局，负责任务分发和结果整合
- **专业代理**: 各司其职，专注特定领域的任务处理
- **工具共享**: 通过 ToolCollection 实现工具资源共享

### 2. 动态提示词管理
- **数据库驱动**: 提示词存储在 Supabase 中，支持热更新
- **个性化配置**: 不同代理可使用不同的提示词ID
- **版本控制**: 支持提示词的版本化管理

### 3. 安全性保障
- **代码验证**: 多层次的代码安全检查
- **沙箱执行**: SmolagAgent 提供的代码执行隔离
- **权限控制**: 通过 `additional_authorized_imports` 限制导入范围

### 4. 监控和错误处理
- **实时监控**: 集成 monitoring 模块
- **错误追踪**: 详细的错误日志和堆栈跟踪
- **优雅降级**: 代理初始化失败时的降级处理机制

## 使用示例

```python
# 初始化多代理系统
agent_manager = AgentManager()
await agent_manager.initialize_agent()

# 执行查询
result = await agent_manager.run_query("分析产品销售趋势并生成图表")

# 获取特定代理
db_agent = agent_manager.get_database_agent()
chart_agent = agent_manager.get_chart_generation_agent()
```

## 扩展性设计

本架构具有良好的扩展性，支持：

1. **新增代理类型**: 继承基础代理类，实现特定功能
2. **工具插件化**: 通过 ToolCollection 动态加载新工具
3. **模型切换**: 支持不同 LLM 模型的无缝切换
4. **自定义验证器**: 扩展验证逻辑以适应新的业务需求

## 总结

该多代理系统基于 SmolagAgent 框架，实现了高度模块化和专业化的AI分析服务。通过合理的架构分层和职责分离，系统具备了良好的可维护性、扩展性和稳定性，为复杂的数据分析和可视化任务提供了强大的技术支撑。 