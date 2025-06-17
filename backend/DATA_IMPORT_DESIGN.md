# 数据导入架构设计

## 核心设计思路

### 分层架构
```
API层 (main.py) 
  ↓
业务服务层 (ScrapingService) 
  ↓
数据导入服务层 (DataImportService) 
  ↓ 
数据处理层 (ScrapingResultProcessor) + 数据访问层 (Repository)
  ↓
数据库 (Supabase)
```

### 各层职责

1. **DataImportService**: 协调整个数据导入流程
   - 读取JSON文件
   - 调用数据处理器转换数据
   - 调用Repository保存数据库
   - 错误处理和重试

2. **ScrapingResultProcessor**: 专门处理数据转换
   - JSON结构解析
   - 数据清洗和格式化
   - 字段映射到数据库模型

3. **Repository层**: 数据访问抽象
   - ScrapingRequestRepository: 管理爬取请求记录
   - AmazonProductRepository: 管理产品数据

### JSON到数据库字段映射

#### scraping_requests表
- `request_type`: 从scraping_summary.type获取
- `search_term`: 从scraping_summary.search_term获取
- `category_id`: 从scraping_summary.category_id获取
- `request_info`: 原始request_info JSONB
- `request_parameters`: 原始request_parameters JSONB
- `scraping_summary`: 原始scraping_summary JSONB

#### amazon_products表
- `platform_id`: product.asin
- `title`: product.title
- `brand`: product.brand
- `rating`: product.rating
- `reviews_count`: product.ratings_total
- `position`: product.position
- `price_usd`: product.price.value
- `categories_flat`: product.categories_flat
- `leaf_category_id`: 最后一个category的category_id
- `scraping_request_id`: 关联爬取请求ID

### 流程设计

1. 爬虫完成 → 生成JSON文件
2. ScrapingService调用DataImportService
3. 数据导入成功 → 返回结果给前端
4. 保留JSON文件作为备份

### 优势

- **模块化**: 每个组件职责单一
- **可复用**: Repository可被其他服务使用
- **可测试**: 每层可独立测试
- **数据安全**: JSON文件作为原始数据备份 