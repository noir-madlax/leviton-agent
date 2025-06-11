# Step2-Data2DB 数据库操作目录

本目录包含所有与Supabase数据库操作相关的脚本和配置文件。

## 📁 目录结构

### `product-main-table/` 
**产品主表相关操作**
- `csv_data_import.py` - 从CSV导入产品主表数据
- `config.py`, `config.env` - 配置文件

### `review-tables/` 
**评论表相关操作**
- `import_full_reviews.py` - 导入完整评论数据到product_reviews表
- `review_analysis_data_import.py` - 全功能评论分析数据导入
- `config.py`, `config.env` - 配置文件

### `product-review-meta-categorization/`
**产品评论Meta信息分类表**
- `import_review_analysis.py` - 导入评论分析结果到product_review_analysis表
- `config.py`, `config.env` - 配置文件

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

## 📊 数据库表结构

1. **product_wide_table** - 产品主表（512条记录）
2. **product_review_analysis** - 产品评论分析表（11,304条记录）
3. **product_reviews** - 完整评论表（待导入）

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