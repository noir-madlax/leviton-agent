# OpenRouter使用指南

## 🎯 概述

**无需修改任何原有代码**，通过环境变量即可切换到OpenRouter。

## 🚀 使用方法：环境变量切换

### 步骤1：确认.env文件配置

**文件位置：** `/Users/rigel/project/leviton/leviton-switch-demo-0611/backend/.env`

**文件内容示例：**
```env
# OpenRouter配置
OPENROUTER_API_KEY=你的OpenRouter密钥
USE_OPENROUTER=true
OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514

# Apify配置（用于爬取评论）
APIFY_API_TOKEN=你的Apify密钥
```

### 步骤2：加载环境变量

```bash
# 进入backend目录
cd /Users/rigel/project/leviton/leviton-switch-demo-0611/backend

# 加载环境变量
source .env

# 验证环境变量已设置
echo $USE_OPENROUTER
echo $OPENROUTER_API_KEY
```

### 步骤3：运行脚本

```bash
# 进入脚本目录
cd /Users/rigel/project/leviton/leviton-switch-demo-0611/backend/src/competitor

# 运行脚本
python3 final_assign_aspects_only.py
```

## 🔑 API密钥申请方法

### Apify API密钥

1. 访问 [https://console.apify.com/](https://console.apify.com/)
2. 注册账户并登录
3. 进入 **Integrations** 页面
4. 找到 **API tokens** 部分，复制你的API token
5. Apify用于爬取Amazon/Home Depot的评论数据

## 🔄 让所有脚本使用OpenRouter

### 方法1：在脚本中添加导入（推荐）

在任何使用LLM的Python脚本**最顶部**添加一行：

```python
import switch_to_openrouter  # 添加这一行即可
# 然后正常导入其他模块
from utils.llm_utils import safe_llm_call
```

**适用的脚本包括：**
- `final_assign_aspects_only.py`
- `process_reviews.py`
- `scrape_reviews.py`
- `product_data_processor.py`
- 任何使用 `llm_utils` 的脚本

### 方法2：命令行运行（无需修改脚本）

```bash
# 运行任何脚本的通用格式
python3 -c "import switch_to_openrouter; import 脚本名; import asyncio; asyncio.run(脚本名.main())"

# 具体例子：
python3 -c "import switch_to_openrouter; import final_assign_aspects_only; import asyncio; asyncio.run(final_assign_aspects_only.main())"
```

## 🤖 Monkey Patching技术原理

**什么是Monkey Patching？**
- 在程序运行时动态替换函数或方法
- **无需修改原始代码**，只在运行时"偷偷替换"
- 对原代码零侵入，完全可逆

**我们的实现：**
```python
# 原来调用：llm_utils.safe_llm_call() → Claude API
# 替换后：llm_utils.safe_llm_call() → OpenRouter API
# 原代码完全不变，只是函数指向变了
```

**优势：**
- ✅ 不破坏原有代码结构
- ✅ 可以随时切换回原始API
- ✅ 对所有使用 `llm_utils` 的脚本都有效
- ✅ 一次设置，全系统生效

## ✅ 验证切换成功

运行脚本时，如果看到以下输出说明切换成功：

```
🔀 正在切换到OpenRouter...
🔀 使用OpenRouter初始化LLM: claude-sonnet-4-20250514
✅ 成功切换到OpenRouter！
🎯 使用模型: anthropic/claude-sonnet-4-20250514
```

## 🔧 通用使用模板

### 对于有main()函数的脚本：
```bash
export USE_OPENROUTER=true
export OPENROUTER_API_KEY="你的密钥"
python3 -c "import switch_to_openrouter; import 你的脚本名; import asyncio; asyncio.run(你的脚本名.main())"
```

### 对于直接执行的脚本：
```bash
export USE_OPENROUTER=true  
export OPENROUTER_API_KEY="你的密钥"
python3 -c "import switch_to_openrouter; import 你的脚本名"
```

**这样系统中所有使用LLM的脚本都会自动使用OpenRouter！**
