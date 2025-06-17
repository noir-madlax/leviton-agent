# Agent 模块设计说明

## 概述
Agent 模块是 AI 智能代理的核心实现，基于 smolagents 框架构建，负责处理用户查询并调用相应的工具执行任务。

## 核心职责
- **工具定义**: 定义产品查询、评论分析等专业工具
- **服务封装**: 提供提示词管理等业务服务
- **依赖注入**: 管理服务间的依赖关系
- **Agent 集成**: 与 smolagents 框架集成，支持自然语言处理

## 目录结构
```
agent/
├── tools/              # 工具定义
│   └── product_review_tools.py
├── services/           # 业务服务层
│   └── product_prompt_service.py
├── dependencies.py     # 依赖注入配置
├── monitors/          # 监控相关
├── prompts/           # 提示词模板
└── document/          # 文档资料
```

## 主要组件

### 工具系统 (Tools)
- **ProductQueryTool**: 商品信息查询工具
  - 支持按 ID、品牌、分类、价格、评分等条件筛选
  - 返回结构化的商品数据
- **ReviewQueryTool**: 评论分析工具
  - 根据商品ID查询评论数据
  - 支持按方面分类(physical/performance/usage)筛选

### 服务层 (Services)
- **ProductPromptService**: 提示词管理服务
  - 提供 CRUD 操作
  - 支持搜索和分页
  - 与数据库层解耦

### 依赖管理 (Dependencies)
- 使用 FastAPI 的依赖注入系统
- 统一管理服务实例的创建和生命周期
- 支持测试时的依赖替换

## 工具集成方式
1. **本地工具**: 直接继承 smolagents.Tool 基类
2. **远程工具**: 通过 MCP (Model Context Protocol) 集成 Supabase 工具
3. **工具组合**: 在 main.py 中统一注册到 CodeAgent

## 数据流程
1. 用户输入自然语言查询
2. Agent 解析并选择合适的工具
3. 工具执行具体的数据查询或分析
4. 返回结构化结果给用户

## 扩展说明
- 新增工具: 继承 Tool 基类，实现 forward 方法
- 新增服务: 在 services 目录创建，通过 dependencies.py 注册
- 集成外部工具: 通过 MCP 协议或直接 API 调用 