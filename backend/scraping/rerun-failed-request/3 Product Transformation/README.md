# Failed Request Retry Tool

This tool allows you to retry failed data transformation requests without re-running the expensive scraping process.

## 背景问题

当数据抓取阶段成功完成但数据转换阶段失败时，您不需要重新运行整个抓取过程。这个工具专门用于重试失败的数据转换任务。

## 主要功能

- ✅ **安全重试**: 只重试确实失败的转换任务
- ✅ **数据验证**: 验证原始数据完整性
- ✅ **状态跟踪**: 自动更新数据库状态
- ✅ **干运行模式**: 预览操作而不实际执行
- ✅ **详细日志**: 提供完整的操作记录

## 使用方法

### 1. 基本用法

```bash
# 方法1：从项目根目录运行（推荐）
python backend/scraping/rerun-failed-request/retry_transformation.py --batch-id 74

# 方法2：从工具目录运行
cd backend/scraping/rerun-failed-request
python retry_transformation.py --batch-id 74

# 使用请求ID重试
python retry_transformation.py --request-id 74
```

### 2. 安全预检查

```bash
# 干运行模式：预览操作而不实际执行
python retry_transformation.py --batch-id 74 --dry-run

# 详细日志模式：查看详细操作过程
python retry_transformation.py --batch-id 74 --verbose

# 从项目根目录运行的方式
python backend/scraping/rerun-failed-request/retry_transformation.py --batch-id 74 --dry-run --verbose
```

### 3. 高级选项

```bash
# 自定义批次大小
python retry_transformation.py --batch-id 74 --batch-size 25

# 组合使用多个选项
python retry_transformation.py --batch-id 74 --dry-run --verbose
```

## 命令行参数

| 参数 | 描述 | 示例 |
|------|------|------|
| `--batch-id` | 指定要重试的批次ID | `--batch-id 74` |
| `--request-id` | 指定要重试的请求ID | `--request-id 74` |
| `--dry-run` | 预览模式，不实际执行 | `--dry-run` |
| `--verbose` | 启用详细日志 | `--verbose` |
| `--batch-size` | 处理批次大小 (默认50) | `--batch-size 25` |

## 工作流程

1. **状态检查**: 验证请求是否可以重试
2. **数据验证**: 确认原始数据完整性
3. **重复检查**: 检查是否已有转换后的数据
4. **状态重置**: 重置失败状态为处理中
5. **执行转换**: 调用修复后的转换服务
6. **状态更新**: 更新最终状态和元数据

## 针对批次74的具体使用

您的批次74遇到了重复`platform_id`的问题，使用以下步骤：

### 步骤1: 预检查
```bash
# 从工具目录运行
cd backend/scraping/rerun-failed-request
python retry_transformation.py --batch-id 74 --dry-run --verbose

# 或者从项目根目录运行
python backend/scraping/rerun-failed-request/retry_transformation.py --batch-id 74 --dry-run --verbose
```

### 步骤2: 执行重试
```bash
# 从工具目录运行
python retry_transformation.py --batch-id 74 --verbose

# 或者从项目根目录运行
python backend/scraping/rerun-failed-request/retry_transformation.py --batch-id 74 --verbose
```

## 输出示例

### 成功情况
```
🔄 Starting retry for batch_id: 74
🔍 Analyzing request 74 with batch 74
📋 Request state: transformation_status=failed, workflow_stage=failed
📊 Source data: 100 total records, 94 valid records
✅ Request 74 is in retryable state
✅ Source data validation passed for batch 74
🚀 Starting transformation retry for batch 74
📝 Updated request 74 status: processing
✅ Transformation retry successful for batch 74
📊 Processed 94 records in 3.45s
✅ Retry operation completed successfully
```

### 干运行模式
```
🔄 Starting retry for batch_id: 74
🔍 Analyzing request 74 with batch 74
📋 Request state: transformation_status=failed, workflow_stage=failed
📊 Source data: 100 total records, 94 valid records
✅ Request 74 is in retryable state
✅ Source data validation passed for batch 74
✅ DRY RUN: Would retry transformation for batch 74
✅ Retry operation completed successfully
```

## 错误处理

工具会检查以下条件：

- ✅ 请求状态必须是 `failed` 或 `pending`
- ✅ 必须有有效的原始数据
- ✅ 批次大小不能超过安全限制
- ✅ 数据库连接必须正常

## 安全机制

1. **状态检查**: 只处理确实失败的任务
2. **数据验证**: 确保原始数据完整
3. **重复检查**: 避免重复处理已成功的任务
4. **干运行模式**: 预检查而不实际执行
5. **详细日志**: 记录所有操作步骤

## 故障排除

### 常见错误

1. **ModuleNotFoundError: No module named 'backend'**:
   - 确保从正确的目录运行脚本
   - 推荐从项目根目录运行：`python backend/scraping/rerun-failed-request/retry_transformation.py --batch-id 74`
   - 或者确保在 `backend/scraping/rerun-failed-request` 目录中运行

2. **No request found for batch_id**: 
   - 检查批次ID是否正确
   - 确认数据库中有相应的记录

3. **Request has unsupported transformation status**:
   - 只能重试状态为 `failed` 的任务
   - 使用 `--verbose` 查看当前状态

4. **No source data found**:
   - 确认 `amazon_products` 表中有相应的数据
   - 检查批次ID是否正确

5. **Database connection failed**:
   - 确认 Supabase 配置正确
   - 检查网络连接

### 调试建议

1. 总是先使用 `--dry-run` 模式预检查
2. 使用 `--verbose` 获取详细日志
3. 检查数据库中的相关状态
4. 确认批次ID和请求ID的对应关系

## 技术细节

### 数据转换修复

工具使用修复后的 `DataTransformationService`，包含以下改进：

1. **去重逻辑**: 自动处理重复的 `platform_id`
2. **批次处理**: 智能分批处理大量数据
3. **错误恢复**: 改进的错误处理机制
4. **状态跟踪**: 精确的状态更新

### 数据库更新

工具会更新以下字段：

- `transformation_status`: 转换状态
- `workflow_stage`: 工作流阶段
- `transformation_metadata`: 转换元数据
- `products_transformed`: 转换成功的产品数量
- `updated_at`: 更新时间

## 注意事项

1. **生产环境使用**: 建议先在测试环境验证
2. **数据备份**: 工具会尝试备份原始状态
3. **并发限制**: 同时只能运行一个重试任务
4. **资源消耗**: 大批次可能需要较长时间

## 支持

如果遇到问题，请：

1. 检查日志输出
2. 确认数据库状态
3. 验证配置设置
4. 查看错误消息

## 更新日志

- v1.0.0: 初始版本，支持批次和请求ID重试 