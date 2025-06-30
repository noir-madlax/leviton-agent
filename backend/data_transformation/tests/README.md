# 数据转换测试套件

本目录包含了数据转换模块的完整测试套件，涵盖单元测试、集成测试和端到端测试。

## 📁 目录结构

```
tests/
├── README.md                     # 本文件 - 测试说明
├── unit/                        # 单元测试
│   ├── __init__.py
│   └── test_parsers.py         # 解析器功能测试
├── integration/                 # 集成测试
│   ├── __init__.py
│   └── test_small_batch.py     # 小批量数据转换测试
├── e2e/                        # 端到端测试
│   ├── __init__.py
│   └── test_end_to_end_flow.py # 完整流程测试
├── output/                     # 测试输出目录
└── utils/                      # 测试工具类
    ├── __init__.py
    └── test_helpers.py         # 测试辅助函数
```

## 🧪 测试分类说明

### 1. 单元测试 (Unit Tests)

#### `unit/test_parsers.py`
**测试内容**：数据解析器的核心功能  
**包含测试**：
- `SalesVolumeParser`: 销量文本解析（"20K+ bought" → 20000）
- `PackParser`: 包装数量解析（"[50 Pack]" → 50）
- `PriceCalculator`: 价格计算和单位价格估算

**运行方法**：
```bash
cd backend/data_transformation
python -m pytest tests/unit/test_parsers.py -v
```

### 2. 集成测试 (Integration Tests)

#### `integration/test_small_batch.py`
**测试内容**：小批量数据转换流程  
**测试目标**：
- 验证解析器组合使用
- 测试数据验证器
- 检查字段映射完整性
- 小批量数据处理（3-5条记录）

**运行方法**：
```bash
cd backend/data_transformation
python tests/integration/test_small_batch.py
```

### 3. 端到端测试 (E2E Tests)

#### `e2e/test_end_to_end_flow.py`
**测试内容**：完整的爬虫→转换→数据库流程  
**测试场景**：
- Leviton产品页面爬取
- 亚马逊分类页面爬取
- 调光开关专业分类爬取

**运行方法**：

1. **测试Leviton产品页面**（推荐先运行）：
```bash
cd backend/data_transformation
python tests/e2e/test_end_to_end_flow.py --test leviton
```

2. **测试通用分类页面**：
```bash
cd backend/data_transformation
python tests/e2e/test_end_to_end_flow.py --test category
```

3. **测试调光开关分类**：
```bash
cd backend/data_transformation
python tests/e2e/test_end_to_end_flow.py --test dimmer
```

4. **运行所有端到端测试**：
```bash
cd backend/data_transformation
python tests/e2e/test_end_to_end_flow.py --test all
```

## 📊 测试输出格式

所有端到端测试会在 `tests/output/` 目录下生成结构化的测试结果：

```
tests/output/e2e_flow_YYYYMMDD_HHMMSS/
├── 00_test_parameters.json     # 测试参数配置
├── 01_scraping_results.json    # 爬虫执行结果
├── 02_amazon_products_data.json  # amazon_products表数据快照
├── 03_transformation_results.json # 数据转换统计结果
├── 04_wide_table_data.json     # product_wide_table数据快照
├── 05_data_comparison.json     # 转换前后数据对比
├── 06_full_test_log.txt        # 完整执行日志
└── 07_test_summary.json        # 测试结果总结
```

## 🎯 测试用例URL

当前测试覆盖以下URL类型：

1. **产品详情页**：`https://www.amazon.com/Leviton-D26HD-2RW-Anywhere-Companions-Required/dp/B08RRM8VH5/`
2. **通用分类页**：`https://www.amazon.com/b?node=166057011`
3. **专业分类页**：`https://www.amazon.com/Dimmer-Switches/b/ref=dp_bc_5?ie=UTF8&node=507840`

## 🚀 快速开始

### 运行完整测试套件
```bash
cd backend/data_transformation

# 1. 运行单元测试
python -m pytest tests/unit/ -v

# 2. 运行集成测试
python tests/integration/test_small_batch.py

# 3. 运行端到端测试（推荐）
python tests/e2e/test_end_to_end_flow.py --test leviton
```

### 查看测试结果
```bash
# 查看最近的测试输出
ls -la tests/output/

# 查看测试总结
cat tests/output/e2e_flow_*/07_test_summary.json | jq .
```

## 🔧 测试工具类

### `utils/test_helpers.py`
提供通用的测试辅助功能：

- **`TestOutputManager`**: 管理测试输出目录和文件持久化
- **`E2ETestRunner`**: 端到端测试执行引擎

这些工具类可以被其他测试文件重复使用，确保测试输出的一致性。

## 📝 添加新测试

### 添加单元测试
1. 在 `unit/` 目录下创建新的测试文件
2. 继承 `unittest.TestCase`
3. 使用 `pytest` 或 `unittest` 运行

### 添加端到端测试
1. 在 `e2e/` 目录下创建测试文件
2. 使用 `E2ETestRunner` 类运行完整流程
3. 确保测试输出保存到 `output/` 目录

## ⚠️ 注意事项

1. **数据库访问**：端到端测试需要访问Supabase数据库
2. **API配额**：爬虫测试会消耗API配额，请适度使用
3. **测试隔离**：每次测试会生成新的batch_id，不会影响现有数据
4. **输出清理**：测试输出会累积，定期清理 `output/` 目录

## 🐛 故障排除

### 常见问题

1. **导入错误**：确保从 `backend/data_transformation` 目录运行测试
2. **数据库连接**：检查 Supabase 配置和网络连接
3. **API限制**：如果遇到403错误，可能是API配额不足

### 调试建议

1. 查看详细日志：`tests/output/*/test_execution.log`
2. 检查数据快照：比较 `02_amazon_products_data.json` 和 `04_wide_table_data.json`
3. 验证测试参数：检查 `00_test_parameters.json` 