# 产品评论分析数据库设计方案

## 🎯 **项目背景与需求**

### 用户需求理解
用户需要将几个产品评论分析相关的数据文件导入到Supabase数据库：
1. **aspect_category_definitions.json** - 产品属性维度定义（LLM从全量评论中梳理的字典主数据）
2. **consolidated_aspect_categorization.json** - 每个产品在所有产品属性维度上的评论分析结果
3. **product_type_mapping.json** - 产品类型和细分市场映射（可合并到主表）
4. **expanded_review_results.json** - 扩展的评论分析结果

### 设计目标
- 简化表结构，避免过度设计
- 支持灵活的多维度评论分析查询
- 保持数据完整性和可扩展性
- 优化查询性能

## 📊 **数据结构分析**

### 文件关系梳理

#### 1. **product_wide_table（主表）** - 已存在
- **作用**: 产品基础信息表，包含产品的基本信息
- **核心字段**: platform_id（产品ID）、title、brand、price、rating、category等
- **现状**: 已导入，包含product_segment字段

#### 2. **aspect_category_definitions.json**
- **作用**: 标准化的产品属性维度定义系统
- **结构**: 三大类别(physical/performance/use_case)下的详细分类定义
- **特点**: 这是从实际评论中总结出的，不是预设标准
- **处理策略**: 不单独建表，通过评论分析表反推维度

#### 3. **consolidated_aspect_categorization.json**
- **作用**: 实际的产品评论方面分析结果
- **结构**: 
  ```json
  {
    "B08PKMT2DV": {
      "aspect_categorization": {
        "phy": {
          "buttons": {
            "A@button layout changed": "Button Interface"
          }
        }
      }
    }
  }
  ```
- **核心信息**: product_id → aspect_category → aspect_subcategory → review_content → standardized_aspect

#### 4. **product_type_mapping.json**
- **现状分析**: 
  - type字段可从主表category推导
  - segment字段主表已有product_segment
  - **结论**: 不需要单独表，可忽略

### 核心设计原则确认

**用户的设计思路（已确认合理）**：
1. 主表保持现状（已有product_segment字段）
2. 只用一张评论分析表，记录每个产品在不同属性维度下的评论情况
3. 不需要单独的aspect_categorization表（可以从分析表反推）

## 🗄️ **数据库表结构设计**

### 最终表结构

#### 1. **product_wide_table** - 保持现状
```sql
-- 已存在，无需修改
-- 关键字段：platform_id（主键关联字段）
```

#### 2. **product_review_analysis** - 新建核心表
```sql
CREATE TABLE product_review_analysis (
    id BIGSERIAL PRIMARY KEY,
    product_id TEXT NOT NULL,                    -- 关联product_wide_table.platform_id
    aspect_category TEXT NOT NULL,               -- physical/performance/use_case
    aspect_subcategory TEXT NOT NULL,            -- buttons/magnets/connectivity等
    review_key TEXT NOT NULL,                    -- 原始标识符(A@, B@等)
    review_content TEXT NOT NULL,               -- 评论内容
    standardized_aspect TEXT NOT NULL,          -- 标准化的方面名称
    
    -- 元数据字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 外键约束
    FOREIGN KEY (product_id) REFERENCES product_wide_table(platform_id),
    
    UNIQUE(product_id, aspect_category, aspect_subcategory, review_key)
);
```

#### 3. **索引设计**
```sql
-- 产品维度查询优化
CREATE INDEX idx_review_analysis_product ON product_review_analysis(product_id);

-- 属性维度查询优化
CREATE INDEX idx_review_analysis_aspect ON product_review_analysis(aspect_category, aspect_subcategory);

-- 复合查询优化
CREATE INDEX idx_review_analysis_product_aspect ON product_review_analysis(product_id, aspect_category);

-- 标准化方面查询优化
CREATE INDEX idx_review_analysis_standardized ON product_review_analysis(standardized_aspect);
```

## 🔄 **数据转换逻辑**

### JSON数据扁平化处理

从嵌套的JSON结构转换为关系型数据：

```python
# 示例转换逻辑
def flatten_review_data(json_data):
    rows = []
    for product_id, product_data in json_data.get("results", {}).items():
        aspect_categorization = product_data.get("aspect_categorization", {})
        
        for aspect_category, subcategories in aspect_categorization.items():
            # 处理physical/performance类别
            if isinstance(subcategories, dict):
                for subcategory, reviews in subcategories.items():
                    if isinstance(reviews, dict):
                        for review_key, standardized_aspect in reviews.items():
                            # 提取评论内容（@后的内容）
                            review_content = review_key.split('@', 1)[1] if '@' in review_key else review_key
                            
                            rows.append({
                                'product_id': product_id,
                                'aspect_category': aspect_category,
                                'aspect_subcategory': subcategory,
                                'review_key': review_key,
                                'review_content': review_content,
                                'standardized_aspect': standardized_aspect
                            })
            
            # 处理use_case类别（直接映射）
            elif aspect_category == 'use':
                for use_case, standardized_aspect in subcategories.items():
                    rows.append({
                        'product_id': product_id,
                        'aspect_category': 'use_case',
                        'aspect_subcategory': 'application',
                        'review_key': use_case,
                        'review_content': use_case.replace('_', ' '),
                        'standardized_aspect': standardized_aspect
                    })
    
    return rows
```

## 📈 **查询优化与业务场景**

### 核心查询场景

#### 1. **产品维度分析**
```sql
-- 查看某产品在所有维度的评论分析
SELECT 
    aspect_category,
    aspect_subcategory,
    standardized_aspect,
    COUNT(*) as review_count
FROM product_review_analysis 
WHERE product_id = 'B08PKMT2DV'
GROUP BY aspect_category, aspect_subcategory, standardized_aspect
ORDER BY aspect_category, review_count DESC;
```

#### 2. **维度横向对比**
```sql
-- 对比多个产品在某个维度的表现
SELECT 
    p.title,
    r.standardized_aspect,
    COUNT(*) as mention_count
FROM product_review_analysis r
JOIN product_wide_table p ON r.product_id = p.platform_id
WHERE r.aspect_category = 'physical' 
    AND r.aspect_subcategory = 'buttons'
    AND r.product_id IN ('B08PKMT2DV', 'B0D7GR3CKW')
GROUP BY p.title, r.standardized_aspect
ORDER BY mention_count DESC;
```

#### 3. **维度统计分析**
```sql
-- 获取所有可用的产品属性维度（反推字典）
SELECT 
    aspect_category,
    aspect_subcategory,
    COUNT(DISTINCT product_id) as product_count,
    COUNT(*) as total_reviews
FROM product_review_analysis
GROUP BY aspect_category, aspect_subcategory
ORDER BY product_count DESC, total_reviews DESC;
```

#### 4. **产品细分与评论特征**
```sql
-- 结合产品细分和评论维度分析
SELECT 
    p.product_segment,
    r.aspect_category,
    r.standardized_aspect,
    COUNT(*) as frequency
FROM product_review_analysis r
JOIN product_wide_table p ON r.product_id = p.platform_id
GROUP BY p.product_segment, r.aspect_category, r.standardized_aspect
HAVING COUNT(*) >= 5  -- 过滤低频项
ORDER BY p.product_segment, frequency DESC;
```

## ⚡ **实施计划**

### 阶段1：表结构创建
- [ ] 创建product_review_analysis表
- [ ] 创建必要的索引
- [ ] 验证表结构和约束

### 阶段2：数据处理脚本开发
- [ ] 开发JSON数据扁平化脚本
- [ ] 实现数据清洗和验证逻辑
- [ ] 批量导入功能实现

### 阶段3：数据导入与验证
- [ ] 小批量测试导入
- [ ] 全量数据导入
- [ ] 数据质量验证
- [ ] 查询性能测试

### 阶段4：业务查询测试
- [ ] 核心查询场景测试
- [ ] 性能优化调整
- [ ] 生成数据统计报告

## 🛡️ **质量保证策略**

### 数据完整性验证
1. **源数据统计**：统计JSON中的产品数量和评论条数
2. **导入后验证**：确认数据库中的记录数与源数据匹配
3. **产品覆盖率**：验证所有产品都有评论分析数据
4. **维度完整性**：确认三大类别的数据都正确导入

### 数据质量检查
1. **必填字段检查**：确保所有核心字段都有值
2. **数据类型验证**：确认字段类型符合预期
3. **重复数据检查**：基于唯一约束检查重复记录
4. **关联完整性**：验证外键关系正确

### 查询性能验证
1. **索引有效性**：验证查询计划使用了正确的索引
2. **响应时间测试**：核心查询响应时间<2秒
3. **并发处理能力**：多用户查询场景测试

## 🎯 **预期成果**

### 数据规模预估
- **预期产品数量**：约260个产品
- **预期评论分析记录**：约5000-10000条记录
- **维度覆盖**：physical、performance、use_case三大类别
- **细分维度**：约50-100个不同的aspect_subcategory

### 业务价值
1. **产品对比分析**：支持多维度产品特性对比
2. **市场洞察**：了解用户关注的产品属性重点
3. **产品优化指导**：基于评论分析指导产品改进方向
4. **竞品分析**：横向对比不同产品在各维度的表现

### 技术价值
1. **查询灵活性**：支持任意维度的组合查询
2. **扩展性**：新增评论分析数据只需插入记录
3. **维护简便性**：单表结构，减少复杂关联
4. **性能优化**：通过索引优化保证查询效率

---

## 📝 **执行检查清单**

### 准备阶段
- [ ] 确认数据文件路径和格式
- [ ] 验证Supabase连接和权限
- [ ] 确认产品主表数据完整性

### 实施阶段
- [ ] 表结构创建完成
- [ ] 数据处理脚本测试通过
- [ ] 小批量数据导入验证
- [ ] 全量数据导入成功
- [ ] 所有索引创建完成

### 验证阶段
- [ ] 数据完整性验证通过
- [ ] 查询功能测试通过
- [ ] 性能指标达标
- [ ] 业务场景验证完成

### 交付阶段
- [ ] 生成数据统计报告
- [ ] 编写查询使用文档
- [ ] 完成知识转移 