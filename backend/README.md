# Leviton Agent Backend

基于 FastAPI 和 smolagents 的智能代理后端服务。

## 功能特性

- 🚀 基于 FastAPI 的高性能 Web API
- 🤖 集成 smolagents 智能代理
- 📡 支持服务器发送事件 (SSE) 流式响应
- 🔍 集成 DuckDuckGo 搜索工具
- 🌐 CORS 支持
- 📝 完整的 API 文档

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

创建 `.env` 文件并根据需要修改配置：

```bash
# 复制示例配置
# 注意：不提供 .env.example，直接在代码中设置默认值

# 示例环境变量：
# HOST=0.0.0.0
# PORT=8000
# DEBUG=true
# MODEL_ID=mistralai/Mistral-7B-Instruct-v0.3
# HF_TOKEN=your_huggingface_token_here
```

### 3. 运行服务

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API 端点

### GET /
- 描述：根路径，返回 API 基本信息
- 响应：JSON 格式的 API 信息

### GET /health
- 描述：健康检查端点
- 响应：服务状态信息

### GET /agent-stream
- 描述：流式查询端点，通过 SSE 返回实时结果
- 参数：
  - `query` (string, required): 查询内容
- 响应：text/event-stream 格式的流式数据

### POST /agent-query
- 描述：标准查询端点，返回完整结果
- 请求体：
  ```json
  {
    "query": "你的查询内容"
  }
  ```
- 响应：JSON 格式的查询结果

## 使用示例

### 流式查询 (SSE)

```javascript
const eventSource = new EventSource('http://localhost:8000/agent-stream?query=你好');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log(data);
};

eventSource.onerror = function(event) {
    console.error('连接错误:', event);
};
```

### 标准查询

```bash
curl -X POST "http://localhost:8000/agent-query" \
     -H "Content-Type: application/json" \
     -d '{"query": "什么是人工智能?"}'
```

## 项目结构

```
backend/
├── main.py              # 主应用文件
├── config.py            # 配置设置
├── requirements.txt     # 依赖列表
├── .gitignore          # Git 忽略文件
└── README.md           # 项目说明
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| HOST | 0.0.0.0 | 服务主机地址 |
| PORT | 8000 | 服务端口 |
| DEBUG | False | 调试模式 |
| MODEL_ID | mistralai/Mistral-7B-Instruct-v0.3 | 模型 ID |
| HF_TOKEN | - | Hugging Face 访问令牌 |
| ALLOWED_ORIGINS | * | 允许的跨域来源 |
| LOG_LEVEL | INFO | 日志级别 |

## 依赖说明

本项目使用了以下主要依赖：

- **FastAPI**: 现代、快速的 Web 框架
- **smolagents**: 智能代理框架
- **duckduckgo-search**: DuckDuckGo 搜索工具
- **transformers**: Hugging Face 模型库
- **torch**: PyTorch 深度学习框架

## 开发说明

1. 确保已安装 Python 3.8+
2. 建议使用虚拟环境
3. 如需使用私有模型，请设置 `HF_TOKEN`
4. 生产环境中请修改 CORS 设置

## 故障排除

### 模型加载失败
- 检查网络连接
- 验证 HF_TOKEN 是否正确
- 确认模型 ID 是否存在

### 依赖安装问题
- 升级 pip: `pip install --upgrade pip`
- 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/`

### DuckDuckGo 搜索工具错误
- 确保安装了 `duckduckgo-search` 包
- 检查网络连接是否正常

## API 文档

启动服务后，访问以下地址查看自动生成的 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 