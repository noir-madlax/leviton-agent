# Leviton Agent Backend 部署指南

## 概述

这是一个基于 FastAPI 的 AI 代理后端服务，集成了 smolagents 和多种工具。

## 本地开发部署

### 1. 环境准备

```bash
# 复制环境变量文件
cp env.example .env

# 编辑环境变量
nano .env
```

### 2. 使用 Docker Compose 启动

```bash
# 构建并启动服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f leviton-agent-backend

# 停止服务
docker-compose down
```

## Portainer 生产部署

### 方法一：使用 Stack 部署

1. 在 Portainer 中创建新的 Stack
2. 复制 `docker-compose.prod.yml` 的内容
3. 配置环境变量：
   - `API_KEY`: OpenRouter API 密钥
   - `MCP_ACCESS_TOKEN`: Supabase MCP 访问令牌
   - `MODEL_ID`: AI 模型 ID
   - 其他可选配置参数

### 方法二：使用预构建镜像

1. 构建镜像：
```bash
docker build -t leviton-agent-backend:latest .
```

2. 推送到镜像仓库：
```bash
docker tag leviton-agent-backend:latest your-registry/leviton-agent-backend:latest
docker push your-registry/leviton-agent-backend:latest
```

3. 在 Portainer 中使用镜像部署

## 环境变量说明

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `API_KEY` | ✅ | - | OpenRouter API 密钥 |
| `MCP_ACCESS_TOKEN` | ✅ | - | Supabase MCP 访问令牌 |
| `MODEL_ID` | ❌ | `google/gemini-2.5-pro-preview` | AI 模型 ID |
| `HOST` | ❌ | `0.0.0.0` | 服务监听地址 |
| `PORT` | ❌ | `8000` | 服务端口 |
| `DEBUG` | ❌ | `false` | 调试模式 |
| `LOG_LEVEL` | ❌ | `INFO` | 日志级别 |
| `ALLOWED_ORIGINS` | ❌ | `*` | CORS 允许的源 |
| `PHOENIX_ENDPOINT` | ❌ | - | Phoenix 监控端点 |
| `PROJECT_NAME` | ❌ | `Customer-Success` | 项目名称 |
| `AGENT_TIMEOUT` | ❌ | `120.0` | Agent 超时时间（秒） |
| `MAX_ITERATIONS` | ❌ | `10` | Agent 最大迭代次数 |

## 健康检查

服务提供以下端点：

- `GET /health` - 健康检查
- `GET /` - 根路径
- `GET /agent-stream` - Agent 流式响应
- `POST /agent-query` - Agent 查询

## 监控和日志

- 容器日志会自动轮转（最大 10MB，保留 3 个文件）
- 支持 Phoenix 监控（需配置 `PHOENIX_ENDPOINT`）
- 健康检查每 30 秒执行一次

## 故障排除

### 常见问题

1. **容器启动失败**
   - 检查环境变量是否正确配置
   - 查看容器日志：`docker logs leviton-agent-backend`

2. **API 调用失败**
   - 验证 `API_KEY` 是否有效
   - 检查网络连接

3. **MCP 连接失败**
   - 验证 `MCP_ACCESS_TOKEN` 是否正确
   - 确保容器可以访问外部网络

### 日志查看

```bash
# 查看实时日志
docker-compose logs -f leviton-agent-backend

# 查看最近的日志
docker-compose logs --tail=100 leviton-agent-backend
```

## 资源要求

- **最小配置**: 0.5 CPU, 1GB RAM
- **推荐配置**: 2 CPU, 4GB RAM
- **存储**: 至少 2GB 可用空间 