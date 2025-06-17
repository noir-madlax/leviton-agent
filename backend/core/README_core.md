# Core 模块设计说明

## 概述
Core 模块是应用的核心业务层，采用分层架构设计，负责数据访问、业务逻辑处理和数据模型定义。

## 核心职责
- **数据库管理**: 统一管理 Supabase 数据库连接
- **数据模型**: 定义应用的数据结构和验证规则
- **仓库模式**: 封装数据访问逻辑，提供统一的数据操作接口
- **业务服务**: 实现核心业务逻辑，协调多个仓库完成复杂操作

## 目录结构
```
core/
├── database/           # 数据库连接管理
│   └── connection.py
├── models/            # 数据模型定义
│   └── product_prompt.py
├── repositories/      # 数据访问层
│   ├── amazon_product_repository.py
│   ├── amazon_review_repository.py
│   ├── product_prompt_repository.py
│   └── scraping_request_repository.py
└── services/          # 业务服务层
    └── data_import_service.py
```

## 分层架构

### 数据库层 (Database)
- **SupabaseManager**: 单例模式管理数据库连接
- **连接池管理**: 自动管理连接生命周期
- **服务客户端**: 提供具有完整权限的服务端连接

### 模型层 (Models)
- **Pydantic 模型**: 使用 Pydantic 进行数据验证
- **ProductPrompt**: 提示词数据模型
  - 支持创建、更新、响应等不同场景
  - 自动处理时间戳和验证

### 仓库层 (Repositories)
- **AmazonProductRepository**: Amazon 商品数据访问
  - 批量插入商品数据
  - 商品查询和筛选
- **AmazonReviewRepository**: Amazon 评论数据访问
  - 评论批量导入
  - 评论统计和分析
- **ProductPromptRepository**: 提示词数据访问
  - CRUD 操作
  - 搜索和分页
- **ScrapingRequestRepository**: 爬取请求管理
  - 批次状态跟踪
  - 请求历史记录

### 服务层 (Services)
- **DataImportService**: 数据导入业务逻辑
  - 协调多个仓库完成复杂导入
  - 事务管理和错误处理

## 设计原则
1. **单一职责**: 每个类只负责一个特定功能
2. **依赖注入**: 通过构造函数注入依赖，便于测试
3. **接口隔离**: 仓库层提供明确的数据访问接口
4. **错误处理**: 统一的异常处理和日志记录

## 数据访问模式
```
API层 → 服务层 → 仓库层 → 数据库层
```

## 扩展指南
- **新增模型**: 在 models 目录创建 Pydantic 模型
- **新增仓库**: 继承基础仓库模式，实现特定数据访问
- **新增服务**: 在 services 目录创建，组合多个仓库实现业务逻辑 