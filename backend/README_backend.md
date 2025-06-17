# Backend 模块设计说明

## 概述

Backend 是整个后端应用的主入口模块，基于 FastAPI 框架构建，负责统一对外提供 API 服务。

## 核心职责

- **应用启动管理**: 管理 FastAPI 应用的生命周期，包括启动时的 Agent 初始化和关闭时的资源清理
- **API 路由管理**: 提供完整的 REST API 接口，包括 Agent 对话、提示词管理、数据爬取等
- **跨域支持**: 配置 CORS 中间件，支持前端跨域访问
- **监控集成**: 集成 Phoenix 监控系统，支持 AI Agent 调用链路追踪

## 主要文件

- `main.py`: FastAPI 应用主文件，包含所有 API 路由和应用配置
- `config.py`: 全局配置文件，管理环境变量和应用设置
- `requirements.txt`: Python 项目依赖清单
- `Dockerfile`: Docker 容器化配置
- `docker-compose.yml`: Docker Compose 编排配置

## 对web-rest层的API 接口分类

1. **Agent 对话接口**: `/agent-stream`, `/agent-query` - 支持流式和标准对话
2. **提示词管理**: `/agent/prompts/*` - agent的提示词
3. **数据爬取**: `/api/scraping/*` - 支持商品和评论数据爬取
4. **系统监控**: `/health`, `/init-agent` - 健康检查和状态管理

## 技术栈

- **Web 框架**: FastAPI (异步高性能)
- **AI Agent**: smolagents (支持工具调用)
- **数据库**: Supabase (通过 MCP 协议集成)
- **监控**: Phoenix + OpenInference
- **部署**: Docker + Docker Compose

## 启动流程

1. 加载环境配置
2. 初始化数据库连接
3. 创建 AI Agent 和工具集
4. 启动 FastAPI 服务
5. 建立监控连接
