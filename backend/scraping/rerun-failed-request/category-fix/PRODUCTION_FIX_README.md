# 生产环境 Category ID 问题修复指南

## 问题概述

在生产环境中出现 `ERROR:extract_categories_from_json:提取类别信息时出错: 'category_id'` 错误。

## 修复内容

### 1. 增强的日志记录
- 添加了详细的调试日志，保存到 `extract_categories_debug.log`
- 每个步骤都有详细的状态跟踪
- 错误时会输出完整的错误堆栈和上下文信息

### 2. 修复的逻辑错误
- **原问题**: 在访问 `categories[i-1]['category_id']` 时没有检查前一个category是否有该字段
- **修复方案**: 在访问前一个category的字段之前，先检查其类型和字段存在性

### 3. 增强的错误处理
- 对每个category对象进行详细的结构检查
- 跳过无效的category对象而不是整个失败
- 记录每个跳过的原因，方便调试

## 在生产环境中使用

### 快速诊断
在生产容器中运行以下命令：

```bash
cd /app/scraping/rerun-failed-request/category-fix/
python production_debug.py
```

这会自动：
1. 检查环境和文件路径
2. 分析JSON文件结构
3. 测试类别提取功能
4. 生成详细的诊断报告

### 查看详细日志
```bash
# 查看主要调试日志
tail -f /app/scraping/rerun-failed-request/category-fix/extract_categories_debug.log

# 查看生产诊断日志  
tail -f /app/scraping/rerun-failed-request/category-fix/production_debug.log
```

### 手动测试特定文件
```python
import asyncio
from extract_categories_from_json import CategoryExtractor

async def test_specific_file():
    extractor = CategoryExtractor()
    result = await extractor.process_json_file("/path/to/your/file.json")
    print(result)

asyncio.run(test_specific_file())
```

## 问题排查步骤

### 1. 确认问题原因
运行诊断脚本会告诉你具体问题：
- JSON文件是否存在和可读
- JSON结构是否符合预期
- category对象中缺少哪些字段

### 2. 常见问题和解决方案

#### 问题A: 文件路径问题
**症状**: 找不到JSON文件
**解决**: 检查容器中的实际路径，可能需要调整路径配置

#### 问题B: category_id字段缺失
**症状**: 部分category对象没有category_id字段
**解决**: 已修复，现在会跳过无效对象并记录原因

#### 问题C: JSON结构变化
**症状**: 找不到category_results或search_results
**解决**: 检查Amazon API返回的数据格式是否发生变化

### 3. 确认修复效果
运行修复后的代码，检查：
- 是否还有KeyError异常
- 多少个category被成功提取
- 多少个category被跳过以及原因

## 日志文件说明

### extract_categories_debug.log
包含详细的执行过程，包括：
- 每个JSON文件的处理过程
- 每个产品的category分析
- 每个category对象的结构检查
- 所有错误和警告信息

### production_debug.log
包含诊断脚本的执行结果：
- 环境检查结果
- 文件查找结果
- JSON结构分析
- 测试执行结果

## 性能优化建议

1. **批量处理**: 如果有大量JSON文件需要处理，建议分批处理
2. **错误监控**: 监控日志文件大小，避免日志文件过大
3. **定期清理**: 定期清理旧的日志文件

## 联系信息

如果遇到新的问题，请：
1. 运行诊断脚本并保存输出
2. 提供相关的日志文件内容
3. 描述具体的错误现象和环境信息 