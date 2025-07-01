# Amazon Category Fetcher

亚马逊类别获取器 - 自动获取亚马逊所有类别数据并保存到数据库

## 功能特性

- ✅ **单类别深度优先遍历**: 每次只处理一个顶级类别，完全遍历其子类别树
- ✅ **断点续传**: 支持中断后从上次位置继续执行，不重复获取已有数据
- ✅ **直观进度跟踪**: 使用txt文件实时显示执行进度，清晰了解执行状态
- ✅ **原始数据保存**: 每次API调用的原始响应都保存到文件，便于后续分析
- ✅ **错误处理和重试**: 自动重试失败的请求，记录错误信息
- ✅ **多域名支持**: 支持全球多个亚马逊域名
- ✅ **配置灵活**: 支持自定义API延迟、最大深度、重试次数等参数

## 系统架构

```
scraping/amazon-cat/
├── models.py                 # 数据模型定义
├── config.py                 # 配置管理
├── api_client.py            # Rainforest API客户端
├── category_repository.py   # 数据库操作
├── progress_tracker.py      # 进度跟踪
├── category_fetcher.py      # 核心获取逻辑
├── orchestrator.py          # 主编排器
├── main.py                  # 命令行入口
└── README.md                # 使用说明
```

## 安装和配置

### 1. 环境要求
- Python 3.8+
- 已配置的Supabase数据库
- Rainforest API密钥

### 2. 环境变量设置
```bash
export RAINFOREST_API_KEY=your_api_key_here
```

### 3. 依赖安装
所有依赖已包含在项目的requirements.txt中，无需额外安装。

## 使用方法

### 基本命令

```bash
# 进入项目目录
cd scraping/amazon-cat

# 测试API连接
python main.py test

# 开始新的获取（所有类别）
python main.py start

# 获取特定类别
python main.py start --category "Books"

# 设置API延迟和最大深度
python main.py start --delay 2.0 --depth 5

# 恢复上次的获取
python main.py resume

# 恢复特定运行
python main.py resume --run-id run_com_20241201_143022

# 查看状态
python main.py status

# 列出所有运行
python main.py list

# 查看统计信息
python main.py stats
```

### 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--domain` | amazon.com | 亚马逊域名 |
| `--category` | None | 指定获取的顶级类别（可选） |
| `--delay` | 1.0 | API调用间隔时间（秒） |
| `--retries` | 3 | 最大重试次数 |
| `--depth` | 10 | 最大深度限制 |
| `--no-skip-existing` | False | 不跳过已存在的类别 |

### 支持的亚马逊域名

- amazon.com (美国)
- amazon.ca (加拿大)
- amazon.co.uk (英国)
- amazon.de (德国)
- amazon.fr (法国)
- amazon.es (西班牙)
- amazon.it (意大利)
- amazon.co.jp (日本)
- amazon.com.au (澳大利亚)
- amazon.in (印度)
- amazon.com.br (巴西)
- amazon.com.mx (墨西哥)

## 进度跟踪

### 数据存储结构
```
data/scraped/amazon/categories/
├── runs/                      # 执行记录
│   ├── run_com_20241201_143022/
│   │   ├── progress.txt       # 进度跟踪文件
│   │   ├── config.json        # 运行配置
│   │   ├── execution.log      # 详细日志
│   │   └── raw_api/           # 原始API响应
│   │       ├── root_categories.json
│   │       └── category_{id}.json
├── current_run -> runs/run_com_20241201_143022/  # 当前运行软链接
└── runs_summary.txt           # 历史运行摘要
```

### 进度文件格式
`progress.txt`文件提供直观的进度显示：

```
==================================================
  Amazon Category Fetch Progress
==================================================
Run ID: run_com_20241201_143022
Domain: amazon.com
Started: 2024-12-01 14:30:22
Status: RUNNING

==============================
  Overall Progress
==============================
Progress: 45.2%
Total Categories: 1,234
Processed: 558
Failed: 12
API Calls: 89

==============================
  Top Level Categories
==============================
✓ Arts & Crafts Supplies (ID: 16605011)
✓ Automotive (ID: 15684181)
✗ Baby (ID: 165796011) - Error: API timeout
○ Books (ID: 283155) - PENDING
○ Clothing, Shoes & Jewelry (ID: 7141123011) - NOT_STARTED

==============================
  Current Processing
==============================
Category: Arts & Crafts Supplies
Level: 3/10
Path: Arts & Crafts Supplies > Drawing & Painting > Brushes

==============================
  Recent Activity
==============================
  [14:35:12] Processing category: Drawing Brushes
  [14:35:10] Found 15 children for Drawing & Painting
  [14:35:08] Saved category to database: Art Supplies
```

## 数据库集成

### 使用现有表结构
系统使用现有的`amazon_categories`表：
- `category_id`: 亚马逊类别ID
- `name`: 类别名称
- `parent_category_id`: 父类别ID
- `level`: 层级深度
- `full_path`: 完整路径
- `link`: 类别链接

### 请求跟踪
所有获取请求都记录在`scraping_requests`表中，类型为`category_fetch`。

## 错误处理和恢复

### 自动重试
- API调用失败时自动重试（默认3次）
- 使用指数退避策略
- 详细记录重试过程

### 断点续传
- 每个类别处理后立即保存状态
- 中断后可从上次位置继续
- 自动跳过已处理的类别

### 错误记录
- 所有错误都记录在进度文件中
- 详细的错误消息和堆栈跟踪
- 支持查看失败类别列表

## 性能优化

### API限流
- 可配置的API调用间隔
- 自动遵守API限制
- 支持动态调整延迟时间

### 内存管理
- 使用栈进行深度优先遍历
- 及时释放不需要的数据
- 批量数据库操作

### 文件管理
- 原始API响应按运行分目录存储
- 自动清理过期的运行数据
- 压缩历史运行记录

## 监控和统计

### 实时监控
```bash
# 查看当前状态
python main.py status

# 监控进度（持续显示）
watch -n 5 "python main.py status"
```

### 统计信息
```bash
python main.py stats
```

显示内容：
- 总类别数量
- 各级别类别分布
- API调用统计
- 错误率分析

## 故障排除

### 常见问题

1. **API连接失败**
   ```bash
   # 测试连接
   python main.py test
   
   # 检查API密钥
   echo $RAINFOREST_API_KEY
   ```

2. **数据库连接问题**
   - 检查Supabase配置
   - 验证数据库权限
   - 确认表结构

3. **进度文件损坏**
   ```bash
   # 从配置文件恢复
   python main.py resume --run-id your_run_id
   ```

4. **磁盘空间不足**
   - 清理旧的运行记录
   - 压缩原始API响应文件

### 日志级别
```bash
# 详细调试信息
python main.py --log-level DEBUG start

# 只显示错误
python main.py --log-level ERROR start
```

## 最佳实践

1. **首次运行**
   - 从单个类别开始测试
   - 设置较小的深度限制
   - 监控API使用量

2. **生产环境**
   - 设置合适的API延迟（建议2-5秒）
   - 定期备份进度数据
   - 监控错误率

3. **大规模获取**
   - 分批处理多个域名
   - 在API限制内运行
   - 保留足够的磁盘空间

4. **中断恢复**
   - 使用`resume`命令而不是重新开始
   - 检查进度文件确认状态
   - 必要时手动清理损坏的数据

## 技术支持

如遇到问题，请检查：
1. 环境变量配置
2. 网络连接状态
3. 数据库权限
4. 磁盘空间
5. 日志文件内容

更多详细信息请查看执行日志和进度文件。 