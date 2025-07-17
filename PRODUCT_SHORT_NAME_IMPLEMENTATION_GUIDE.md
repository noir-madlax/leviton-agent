# 产品短名字显示功能实施指南

## 需求描述

在竞争分析页面的3个图表中，需要实现产品短名字显示功能：

1. **目标**：对于有定义短名字的产品（如 `B0BVKYKKRK` -> `Leviton D26HD`），在图表中显示短名字而不是长标题
2. **范围**：影响3个图表区域
   - Product Comparison by Key Dimensions (CompetitorMatrix)
   - Product Comparison by Main Use Cases (MissedOpportunitiesMatrix) 
   - Customer satisfaction overview (产品卡片)
3. **用户体验**：短名字用于图表显示，完整名字用于hover tooltip

## 设计方案

### 数据流设计
```
后端 ASIN_TO_DISPLAY_NAME 映射 → API 返回 productDisplayNames → 前端优先使用短名字 → 图表显示
```

### 关键原则
- **后端主导**：短名字映射在后端定义，确保一致性
- **优雅降级**：没有短名字定义的产品使用原有截断逻辑
- **双重显示**：图表显示短名字，tooltip显示完整信息

## 详细实施步骤

### 步骤1：后端API响应扩展

**文件**：`backend/dashboard/services/competitor_analysis_service.py`

**位置**：`_process_competitor_data()` 方法

**修改内容**：
```python
# 在方法的 return 语句中添加 productDisplayNames 字段
return {
    'targetProducts': target_products,
    'matrixData': matrix_data,
    'productTotalReviews': product_total_reviews,
    'productDisplayNames': self.ASIN_TO_DISPLAY_NAME,  # 新增这一行
    'useCaseData': {
        'targetProducts': target_products,
        'matrixData': use_case_matrix_data
    }
}
```

### 步骤2：后端API响应模型更新

**文件**：查找定义 `CompetitorAnalysisResponse` 的文件（可能在 `backend/dashboard/api.py` 或相关模型文件中）

**修改内容**：在响应模型中添加新字段
```python
# 在 CompetitorAnalysisResponse 类中添加
productDisplayNames: Dict[str, str] = {}
```

如果使用 Pydantic，确保导入 `Dict` 类型：
```python
from typing import Dict
```

### 步骤3：前端数据服务更新

**文件**：`frontend/src/components/analysis-db/data/database-service.ts`

**位置**：`getCompetitorAnalysisDataByProject()` 方法的返回类型定义

**修改内容**：
```typescript
// 更新返回类型，添加 productDisplayNames 字段
async getCompetitorAnalysisDataByProject(...): Promise<{
  targetProducts: string[]
  matrixData: Array<{...}>
  productTotalReviews: Record<string, number>
  productDisplayNames: Record<string, string>  // 新增这一行
  useCaseData: {...}
}> {
  // 方法实现保持不变，API会自动返回新字段
}
```

### 步骤4：前端组件数据类型更新

**文件**：`frontend/src/components/analysis-db/competitor-analysis/competitor-analysis.tsx`

**位置**：接口定义 `CompetitorAnalysisProps`

**修改内容**：
```typescript
// 在 competitorAnalysis 对象中添加 productDisplayNames 字段
data: {
  competitorAnalysis: {
    targetProducts: string[]
    matrixData: Array<{...}>
    productTotalReviews: Record<string, number>
    productDisplayNames: Record<string, string>  // 新增这一行
    useCaseData: {...}
  }
  allReviewData: Record<string, Array<{...}>>
}
```

### 步骤5：前端映射逻辑核心修改

**文件**：`frontend/src/components/analysis-db/competitor-analysis/competitor-analysis.tsx`

**位置1**：`competitorData` 的构建（约第165行）
```typescript
// 修改 competitorData 的构建，包含 productDisplayNames
const competitorData = customCompetitorData || {
  targetProducts: data.competitorAnalysis.targetProducts,
  matrixData: data.competitorAnalysis.matrixData,
  productTotalReviews: data.competitorAnalysis.productTotalReviews,
  productDisplayNames: data.competitorAnalysis.productDisplayNames || {}  // 新增这一行
}
```

**位置2**：`asinToProductNameMap` 的构建逻辑（约第255行）
```typescript
// 完全替换现有的 asinToProductNameMap 构建逻辑
const asinToProductNameMap = useMemo(() => {
  const map: Record<string, string> = {};
  defaultProducts.forEach(product => {
    // 优先使用后端定义的短名字
    const backendShortName = competitorData.productDisplayNames?.[product.platform_id];
    if (backendShortName) {
      map[product.platform_id] = backendShortName;
    } else {
      // 回退到原有的截断逻辑
      const shortTitle = product.title.length > 30 ? 
        `${product.title.substring(0, 30)}...` : 
        product.title;
      map[product.platform_id] = shortTitle;
    }
  });
  return map;
}, [defaultProducts, competitorData.productDisplayNames]);  // 添加 competitorData.productDisplayNames 依赖
```

**位置3**：`productStats` 的构建逻辑（约第228行）
```typescript
// 在 productStats 构建中使用短名字
const productStats = competitorData.targetProducts.map((productAsin: string) => {
  // ... 现有逻辑保持不变 ...
  
  // 找到产品信息
  const productInfo = defaultProducts.find(p => p.platform_id === productAsin);
  const productTitle = productInfo?.title || productAsin;
  
  // 使用后端短名字或回退到截断逻辑
  const backendShortName = competitorData.productDisplayNames?.[productAsin];
  const shortTitle = backendShortName || 
    (productTitle.length > 50 ? `${productTitle.substring(0, 50)}...` : productTitle);
  
  return {
    asin: productAsin,
    name: shortTitle,  // 使用短名字
    fullTitle: productTitle,  // 保持完整标题用于tooltip
    // ... 其他字段保持不变 ...
  }
})
```

### 步骤6：确保图表组件正确使用映射

**文件**：`frontend/src/components/analysis-db/charts/competitor-matrix.tsx`

**验证**：确保已正确使用 `asinToProductNameMap` 和 `asinToFullProductNameMap`
```typescript
// 在表头渲染中（约第147行），确保这样的代码存在：
<th key={productAsin} className={`...`}>
  <Tooltip content={fullProductName}>
    <div className="text-sm">{productName}</div>  {/* 显示短名字 */}
  </Tooltip>
</th>
```

**文件**：`frontend/src/components/analysis-db/charts/missed-opportunities-matrix.tsx`

**验证**：同样确保正确使用映射（约第143行）

### 步骤7：处理customCompetitorData的情况

**文件**：`frontend/src/components/analysis-db/competitor-analysis/competitor-analysis.tsx`

**位置**：`handleAsinSelectionChange` 方法（约第174行）

**修改内容**：确保从API获取的自定义数据包含 `productDisplayNames`
```typescript
// 在 handleAsinSelectionChange 方法中，API调用应该自动返回 productDisplayNames
// 无需修改，但需要验证 setCustomCompetitorData 设置的数据结构正确
```

## 测试验证步骤

### 1. 后端API测试
- 调用竞争分析API，验证响应中包含 `productDisplayNames` 字段
- 验证 `productDisplayNames` 包含 `B0BVKYKKRK: "Leviton D26HD"` 等映射

### 2. 前端显示测试
- 访问竞争分析页面
- 验证3个位置的产品名字显示：
  - Product Comparison by Key Dimensions 表头
  - Product Comparison by Main Use Cases 表头  
  - Customer satisfaction overview 卡片标题
- 验证有短名字定义的产品显示短名字，其他产品显示截断的长标题

### 3. Tooltip测试
- hover 各个产品名字，验证tooltip显示完整产品标题
- 验证在有短名字的情况下，tooltip仍显示完整原始标题

### 4. 产品选择功能测试
- 使用产品选择器更换产品
- 验证新选择的产品在3个图表中正确显示短名字（如果有定义）

## 注意事项

1. **类型安全**：确保所有TypeScript类型定义正确
2. **空值处理**：添加适当的空值检查（`?.` 操作符）
3. **向后兼容**：确保在没有短名字定义时正常回退
4. **依赖管理**：确保 `useMemo` 的依赖数组包含所有相关变量
5. **一致性**：确保所有3个图表使用相同的映射逻辑

## 完成标志

✅ 后端API返回包含 `productDisplayNames` 字段  
✅ 前端正确接收并使用短名字映射  
✅ 3个图表区域显示短名字（有定义时）  
✅ Tooltip显示完整产品名字  
✅ 产品选择功能正常工作  
✅ 没有TypeScript编译错误  
✅ 页面功能测试通过 