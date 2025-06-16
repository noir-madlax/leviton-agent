# Step1 数据爬取功能实施设计

## 总体目标

将backend-old中稳定运行的Amazon爬虫功能集成到新的agent程序中，并通过前端界面控制。

## 核心原则

- **最小修改**：老代码尽量不改，保证稳定性
- **功能完整**：完全复用老程序的爬取逻辑
- **接口简洁**：前端只需一个URL输入接口

## 技术架构

### 后端设计

#### 目录结构

```
backend/
├── main.py                    # 添加爬虫API接口
├── scraping/                  # 复制的老代码
│   ├── __init__.py
│   ├── amazon_api.py         # 复制自backend-old
│   ├── scrape_best_sellers.py # 复制自backend-old
│   └── scrape_reviews.py     # 复制自backend-old
└── services/                  # 新增功能
    ├── __init__.py
    └── url_parser.py         # URL解析服务
```

#### 环境变量要求

```
APIFY_API_TOKEN=your_apify_token
RAINFOREST_API_KEY=your_rainforest_key
```

#### API接口设计

```
POST /api/scraping/process-url
Request: {
  "url": "https://amazon.com/...",
  "max_products": 100,
  "max_reviews": 50
}
Response: {
  "task_id": "xxx",
  "status": "started"
}
```

### 前端设计

#### 页面结构

- 重构现有页面，添加Tab导航
- Tab1: 数据导入
- Tab2: 数据确认（预留）
- Tab3: 通用维度分析（预留）
- Tab4: 后续问答（现有chat界面）

#### Tab1界面元素

- Amazon URL输入框
- 参数配置区域
  - 最大产品数量（默认100）
  - 最大评论数量/产品（默认50）
- 爬取规则说明
- 启动按钮和进度显示
- 结果预览区域

## 实施流程

### 阶段1：后端开发

1. 复制老代码到新目录
2. 创建URL解析服务
3. 在main.py中添加API接口
4. 测试爬虫功能

### 阶段2：前端开发

1. 重构页面结构，添加Tab导航
2. 实现Tab1的数据导入界面
3. 集成API调用和状态显示
4. 测试完整流程

## 调用流程

### 用户操作流程

1. 用户在Tab1输入Amazon URL
2. 设置爬取参数（产品数、评论数）
3. 点击开始爬取
4. 显示进度和状态
5. 完成后显示结果摘要

### 系统处理流程

```
前端提交URL + 参数
    ↓
POST /api/scraping/process-url
    ↓
url_parser.py 解析URL
    ├── 提取ASIN/关键词/分类信息
    └── 构建爬取配置
    ↓
调用老代码爬取
    ├── scrape_best_sellers.py 获取产品列表
    └── scrape_reviews.py 获取每个产品的评论
    ↓
保存CSV文件到data/目录
    ↓
返回结果给前端
```

## URL支持类型

### 产品页面URL

- 格式：`https://www.amazon.com/dp/B0076HPM8A`
- 处理：提取ASIN，获取产品信息，基于产品信息爬取同类产品

### 分类页面URL

- 格式：`https://www.amazon.com/b?node=166057011`
- 处理：提取node ID，转换为category ID，爬取该分类产品

### 搜索结果URL

- 格式：`https://www.amazon.com/s?k=dimmer+switch`
- 处理：提取搜索关键词，直接搜索相关产品

## 数据输出格式

保持与老程序完全一致的CSV格式：

- 产品数据：保存到 `data/scraped/amazon/`
- 评论数据：保存到 `data/scraped/amazon/review/`

## 错误处理

- API调用失败：记录错误，继续处理其他项目
- 网络超时：重试机制
- 数据解析错误：跳过异常数据，记录日志
- 前端状态管理：显示具体错误信息

## 性能考虑

- 异步处理：避免长时间阻塞前端
- 批量处理：分批爬取，避免API限制
- 进度反馈：实时显示处理进度
- 缓存机制：避免重复爬取相同数据

## 测试验证

### 后端测试

- 测试各种URL格式的解析
- 测试API调用的稳定性
- 验证数据保存格式

### 前端测试

- 测试界面交互流程
- 验证参数配置功能
- 测试错误处理显示

### 集成测试

- 完整的端到端流程测试
- 各种异常情况的处理测试
