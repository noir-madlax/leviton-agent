# Step2-Data2DB 数据库操作目录

本目录包含所有与Supabase数据库操作相关的脚本和配置文件。

## 📁 目录结构

### **根目录 `/step2-data2DB/`**
**通用配置和文档**
- `config.py` - 配置加载模块
- `config.env` - 实际配置文件（包含密钥）  
- `config.env.example` - 配置模板
- `test_data_import.py` - 通用测试脚本
- `README.md` - 本说明文档
- `implementation_report.md` - 项目实施总结报告
- `supabase_data_import_guide.md` - CSV+JSON数据导入指南
- `supabase_data_import_universal_prompt.md` - 通用方法论文档

### **`product-main-table/`** 
**产品主表相关操作**
- `csv_data_import.py` - 从CSV导入产品主表数据
- `supabase_wide_table_setup_optimized.sql` - 产品主表完整创建脚本
- `config.py`, `config.env`, `config.env.example` - 配置文件

### **`review-tables/`** 
**评论表相关操作**
- `import_full_reviews.py` - 导入完整评论数据到product_reviews表
- `create_reviews_table.sql` - 创建产品评论表的SQL脚本
- `review_import_report.md` - 评论数据导入完成报告
- `config.py`, `config.env`, `config.env.example` - 配置文件

### **`product-review-meta-categorization/`**
**产品评论Meta信息分类表**
- `import_review_analysis.py` - 导入评论分析结果到product_review_analysis表
- `review_analysis_data_import.py` - 全功能评论分析数据导入脚本
- `create_review_analysis_table.sql` - 创建评论分析表的SQL脚本
- `update_analysis_table.sql` - 更新分析表结构的SQL脚本  
- `review_analysis_database_design.md` - 评论分析数据库设计文档
- `config.py`, `config.env`, `config.env.example` - 配置文件

## 🗂️ 数据文件路径映射

根据新的数据目录结构，各类型数据文件位置：

- **产品数据**: `../backend/data/product-data/`
  - `combined_products_with_final_categories.csv`
  
- **评论数据**: `../backend/data/review-by-meta-structure/`
  - `expanded_review_results.json`
  - `consolidated_aspect_categorization.json`
  
- **Meta数据**: `../backend/data/product-meta-data/`
  - `aspect_category_definitions.json`

## 🔧 配置说明

每个子目录都包含独立的配置文件：
- `config.env` - 实际配置（包含密钥）
- `config.env.example` - 配置模板
- `config.py` - 配置加载模块

## 🔑 安全要求

所有数据库连接信息必须通过环境变量或配置文件加载，**严禁硬编码任何密钥信息**。

### 🛡️ **版本控制安全**

- ✅ **`.gitignore` 配置**：已添加 `.gitignore` 文件，自动忽略所有包含密钥的配置文件
- ✅ **敏感文件保护**：所有 `config.env` 文件都被忽略，不会被提交到 Git
- ✅ **模板文件保留**：`config.env.example` 文件会被保留，提供配置模板
- ⚠️ **首次配置**：每个新环境都需要根据 `config.env.example` 创建自己的 `config.env`

### 📋 **安全检查清单**

在提交代码前，请确认：
- [ ] 没有硬编码的数据库连接信息
- [ ] 所有密钥都在 `config.env` 文件中（已被 `.gitignore` 忽略）
- [ ] 更新了对应的 `config.env.example` 模板文件
- [ ] 运行 `git status` 确认没有敏感文件被暂存

## 📊 数据库表结构

1. **product_wide_table** - 产品主表（512条记录）
2. **product_review_analysis** - 产品评论分析表（11,304条记录）
3. **product_reviews** - 完整评论表（8,121条记录）

## 🚀 使用方法

1. 确保配置文件中的数据库连接信息正确
2. 根据需要进入对应的子目录
3. 运行相应的Python脚本

```bash
# 导入产品主表
cd product-main-table/
python csv_data_import.py

# 导入评论分析数据
cd ../product-review-meta-categorization/
python import_review_analysis.py

# 导入完整评论数据
cd ../review-tables/
python import_full_reviews.py
```

## 📈 项目完成状态

| 任务模块 | 状态 | 记录数 | 说明 |
|---------|------|--------|------|
| 产品主表导入 | ✅ 完成 | 512条 | 产品基础信息表 |
| 评论分析导入 | ✅ 完成 | 11,304条 | 多维度评论分析结果 |
| 完整评论导入 | ✅ 完成 | 8,121条 | 详细评论内容和评分 |
| 数据质量验证 | ✅ 完成 | - | 全面质量检查通过 |

## 🎯 快速测试

在根目录运行测试脚本验证系统状态：

```bash
# 在step2-data2DB/目录下运行
python test_data_import.py
```

## 🔒 安全检查

在提交代码前，运行安全检查脚本确保没有敏感信息泄露：

```bash
# 在step2-data2DB/目录下运行
./check_security.sh
```

这个脚本会检查：
- ✅ `.gitignore` 文件是否存在
- ✅ `config.env` 文件是否被正确忽略
- ✅ 暂存区中是否有敏感文件
- ✅ 是否有硬编码的密钥
- ✅ 配置模板文件是否安全 