# 继续完成爬虫任务的剩余步骤

## 📋 概述

当爬虫任务在某个步骤失败后，使用此脚本可以从失败的步骤继续执行，而不需要重新开始整个爬虫流程。

## 🎯 适用场景

- **Product Transformation 完成后**，需要继续执行 Review 相关步骤
- **Phase 1-2.5 完成**，需要执行 Phase 3-4.5：
  - Phase 3: Review Scraping (爬取评论)
  - Phase 4: Review Import (导入评论)
  - Phase 4.5: Review Transformation (转换评论数据)

## 📝 使用方法

### 基本用法
```bash
python continue_review_workflow.py --batch-id 74
```

### 带参数的完整用法
```bash
python continue_review_workflow.py --batch-id 74 --review-months 6 --verbose
```

### 参数说明
- `--batch-id`: 批次ID（必需）
- `--review-months`: 评论覆盖月数（可选，默认: 6个月）
- `--verbose`: 显示详细日志（可选）

## 🔄 工作流程

此脚本会自动执行以下步骤：

1. **📥 Review Scraping**: 从Amazon API爬取产品评论
2. **📤 Review Import**: 将评论数据导入到 `amazon_reviews` 表
3. **🔄 Review Transformation**: 将评论数据转换并存储到 `product_reviews` 表
4. **📊 Database Update**: 更新 `scraping_requests` 表的状态

## 📊 执行结果

### 成功情况
```
🎉 批次 74 的评论工作流程完成成功!
📊 详细结果:
  📥 Review Scraping: success
     - 总评论数: 1250
     - 处理产品数: 94
  📤 Review Import: success
     - 导入评论数: 1250
  🔄 Review Transformation: success
     - 转换记录数: 1250
     - 转换耗时: 45.32秒
```

### 失败情况
脚本会详细显示每个步骤的错误信息，帮助排查问题。

## 📁 日志文件

脚本会自动生成日志文件：
- 文件名格式: `continue_review_workflow_YYYYMMDD_HHMMSS.log`
- 包含完整的执行过程和结果

## 🔍 数据库状态检查

执行前后可以检查数据库状态：

```sql
-- 检查 scraping_requests 表状态
SELECT id, status, workflow_stage, transformation_status, review_status, 
       products_scraped, products_transformed, reviews_scraped 
FROM scraping_requests 
WHERE id = 74;

-- 检查评论数据
SELECT COUNT(*) as review_count FROM amazon_reviews WHERE batch_id = 74;
SELECT COUNT(*) as transformed_count FROM product_reviews WHERE batch_id = 74;
```

## ⚠️ 注意事项

1. **确保 Product Transformation 已完成**：此脚本假设前面的产品相关步骤已成功完成
2. **API 配额**：评论爬取会消耗 Rainforest API 配额
3. **执行时间**：根据产品数量，整个过程可能需要 10-30 分钟
4. **错误处理**：如果某个步骤失败，会自动更新数据库状态并记录错误信息

## 🚀 执行示例

```bash
# 切换到正确的目录
cd backend/scraping/rerun-failed-request

# 执行脚本
python continue_review_workflow.py --batch-id 74 --verbose

# 查看日志
tail -f continue_review_workflow_*.log
```

## 🔧 故障排除

如果遇到问题：

1. **检查日志文件**获取详细错误信息
2. **验证数据库连接**和权限
3. **确认 API 配额**是否充足
4. **检查网络连接**是否正常

## 📈 预期结果

执行成功后，您的爬虫任务应该完全完成：
- ✅ Products: 爬取、导入、转换完成
- ✅ Reviews: 爬取、导入、转换完成
- ✅ Database: 所有状态更新为 "completed"
- ✅ Frontend: 可以在界面上看到完整的数据分析 