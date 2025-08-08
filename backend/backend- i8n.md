# 后端透明国际化设计方案

## 设计目标

- **前端零改动**：前端代码无需任何修改，根据locale自动获得对应语言内容
- **透明化翻译**：后端根据Accept-Language头智能返回中英文内容
- **统一管理**：所有翻译内容集中在一个配置文件中维护
- **字段值翻译**：不改变字段名，只翻译字段值中的文字部分

## 核心机制

### 原理说明

```json
// 当 Accept-Language: en 时
{
  "positiveCount": 150,
  "satisfactionRate": "85.7% satisfaction",
  "description": "Total Amazon Categories"
}

// 当 Accept-Language: zh 时  
{
  "positiveCount": 150,
  "satisfactionRate": "85.7% 满意度", 
  "description": "亚马逊类别总数"
}
```

**字段名不变，只有包含文字的字段值被翻译。**

## 技术架构

### 1. 翻译配置文件

**位置**: `backend/core/translations.py`

```python
# 统一翻译词典
TRANSLATIONS = {
    # 数值后缀翻译
    'suffixes': {
        'satisfaction': {'en': 'satisfaction', 'zh': '满意度'},
        'reviews': {'en': 'reviews', 'zh': '评论'},
        'products': {'en': 'products', 'zh': '产品'},
        'categories': {'en': 'categories', 'zh': '类别'}
    },
  
    # 完整文本翻译
    'texts': {
        'Total Amazon Categories': {'en': 'Total Amazon Categories', 'zh': '亚马逊类别总数'},
        'Avg Negative Rate': {'en': 'Avg Negative Rate', 'zh': '平均负面率'},
        'Revenue ($)': {'en': 'Revenue ($)', 'zh': '收入 ($)'},
        'Loading products...': {'en': 'Loading products...', 'zh': '加载产品中...'}
    },
  
    # 图表描述翻译
    'descriptions': {
        'satisfaction_color_legend': {
            'en': 'Color indicates satisfaction rate (positive mentions / total mentions)',
            'zh': '颜色表示满意度（正面提及/总提及）'
        }
    }
}
```

### 2. 自动翻译装饰器

**位置**: `backend/core/i18n_decorator.py`

- 从请求头提取locale
- 递归扫描响应数据中的文本字段
- 自动翻译匹配的文本内容
- 保持数据结构完全不变

### 3. 中间件集成

**位置**: `backend/dashboard/middleware.py`

- 拦截所有API响应
- 自动应用翻译装饰器
- 对前端完全透明

#### 中间件变更详细说明

```python
# 需要在middleware中实现的核心功能：

class I18nMiddleware:
    def __init__(self):
        # 1. 初始化翻译词典缓存
        self.translations = load_translations()
  
    def process_response(self, request, response):
        # 2. 提取Accept-Language请求头
        locale = extract_locale_from_request(request)
    
        # 3. 解析JSON响应体
        if is_json_response(response):
            data = parse_response_data(response)
        
            # 4. 递归翻译数据中的文本字段
            translated_data = translate_response_data(data, locale)
        
            # 5. 重新包装响应
            response.content = json.dumps(translated_data)
    
        return response

# 关键处理逻辑：
# - 只处理JSON响应
# - 保持HTTP状态码和头部不变
# - 深度递归处理嵌套对象和数组
# - 缓存翻译结果提升性能
```

## 需要修改的文件清单

### 核心基础设施 (新建)

#### 1. `backend/core/translations.py` ✨ **新建**

- **用途**: 统一翻译词典配置文件
- **内容**: 所有需要翻译的文字映射表
- **维护**: 新增翻译内容时在此文件添加

#### 2. `backend/core/i18n_decorator.py` ✨ **新建**

- **用途**: 自动翻译装饰器和工具函数
- **功能**:
  - 递归翻译响应数据中的文本
  - 智能识别需要翻译的字段
  - 保持数据结构不变

#### 3. `backend/dashboard/middleware.py` ✨ **新建**

- **用途**: API响应拦截中间件
- **功能**:
  - 提取Accept-Language请求头
  - 自动应用翻译装饰器
  - 透明处理所有API响应

### API路由配置

#### 4. `backend/dashboard/api.py`

- **修改点**: 添加i18n中间件到API路由
- **变更**: 1行代码，启用翻译中间件
- **影响**: 所有dashboard API自动支持国际化

**具体配置方法：**

```python
# 在现有的API路由配置中添加：
from .middleware import I18nMiddleware

# 方法1：作为FastAPI中间件
app.add_middleware(I18nMiddleware)

# 方法2：或者作为Flask装饰器（如果用Flask）
@app.before_request
def setup_i18n():
    # 设置locale上下文

@app.after_request  
def apply_i18n(response):
    # 应用翻译中间件
    return I18nMiddleware().process_response(request, response)
```

#### 5. `backend/main.py` 或 `backend/app.py`

- **修改点**: 注册全局中间件
- **变更**: 2-3行代码配置
- **影响**: 整个应用支持国际化

**全局中间件注册：**

```python
# 在应用启动时添加：
from core.i18n_middleware import I18nMiddleware

# FastAPI方式
app.add_middleware(I18nMiddleware)

# 或者Django方式（如果使用Django）
MIDDLEWARE = [
    # ... 其他中间件
    'core.i18n_middleware.I18nMiddleware',
    # ... 其他中间件
]

# 确保中间件顺序：I18n中间件应该在最后执行，以处理最终响应
```

### 业务逻辑 (现有文件，微调)

#### Service修改示例：`backend/dashboard/services/review_insights_service.py`

**修改前的代码：**

```python
def get_satisfaction_data(self, project_id):
    # 业务逻辑处理...
  
    return {
        "positiveCount": positive_count,
        "negativeCount": negative_count,
        "satisfactionRate": f"{rate:.1f}% satisfaction",  # 需要翻译
        "description": "Total Amazon Categories",         # 需要翻译
        "loadingMessage": "Loading products...",          # 需要翻译
        "chart_config": {
            "yAxisLabel": "Revenue ($)",                  # 需要翻译
            "tooltipSuffix": " products"                  # 需要翻译
        }
    }
```

**修改后的代码：**

```python
from core.translations import mark_for_translation as _t

def get_satisfaction_data(self, project_id):
    # 业务逻辑处理...（完全不变）
  
    return {
        "positiveCount": positive_count,                   # 纯数字，不翻译
        "negativeCount": negative_count,                   # 纯数字，不翻译
        "satisfactionRate": _t(f"{rate:.1f}% satisfaction"),  # 标记翻译
        "description": _t("Total Amazon Categories"),         # 标记翻译
        "loadingMessage": _t("Loading products..."),          # 标记翻译
        "chart_config": {
            "yAxisLabel": _t("Revenue ($)"),                  # 标记翻译
            "tooltipSuffix": _t(" products")                  # 标记翻译
        }
    }
```

**标记翻译的核心原则：**

- 只在返回给前端的文本字段上添加 `_t()` 标记
- 不改变任何业务逻辑代码
- 不改变数据结构和字段名
- 纯数字、ID、品牌名等不需要标记

#### 其他Service文件修改要点：

#### 7. `backend/dashboard/services/competitor_analysis_service.py`

- **涉及字段**: 矩阵图颜色说明文字
- **标记内容**: `"Color indicates satisfaction rate (positive mentions / total mentions)"`
- **修改方式**: 在描述文字上添加 `_t()` 标记

#### 8. `backend/dashboard/services/brand_analysis_service.py`

- **涉及字段**: TAM市场描述
- **标记内容**: `"Total addressable market"`, `"Market penetration"`
- **修改方式**: 在市场分析文字上添加 `_t()` 标记

#### 9. `backend/dashboard/services/market_insights_service.py`

- **涉及字段**: 图表轴标签和单位
- **标记内容**: `"Revenue ($)"`, `"Volume"`, `"Market Share (%)"`
- **修改方式**: 在图表配置的标签文字上添加 `_t()` 标记

#### 10. `backend/dashboard/services/pricing_analysis_service.py`

- **涉及字段**: 价格范围描述和选择器标签
- **标记内容**: `"Price Range"`, `"Average Price"`, `"Price Distribution"`
- **修改方式**: 在价格分析相关描述上添加 `_t()` 标记

### 前端文件 (完全无需修改)

#### ✅ `frontend/src/**/*.tsx`

- **修改点**: **无需任何修改**
- **原因**: 后端透明返回对应语言内容
- **效果**: 自动显示中文内容

## 翻译字段识别规则

### 需要翻译的字段类型

1. **描述性文字**: 包含说明文本的字段
2. **百分比后缀**: "85.7% satisfaction" → "85.7% 满意度"
3. **数量单位**: "150 products" → "150 产品"
4. **图表标签**: "Revenue ($)" → "收入 ($)"
5. **状态文字**: "Loading..." → "加载中..."

### 不翻译的字段类型

1. **纯数值**: 150, 85.7 等数字
2. **技术标识**: API字段名、ID等
3. **品牌名称**: "Leviton", "Lutron" 等
4. **产品型号**: "DSL06-1LZ" 等

## 实施步骤

### Phase 1: 基础设施搭建

1. 创建 `translations.py` 翻译配置文件
2. 开发 `i18n_decorator.py` 自动翻译工具
3. 创建 `middleware.py` API拦截中间件

### Phase 2: 核心API集成

4. 配置 `api.py` 启用中间件
5. 测试主要API的翻译效果
6. 完善翻译词典配置

### Phase 3: 业务字段标记

7. 标记各service中需要翻译的字段
8. 补充遗漏的翻译内容
9. 全面测试验证

## 预期效果

### 开发体验

- **前端开发**: 无感知，代码零修改
- **后端开发**: 只需在翻译文件中添加词条
- **维护成本**: 集中管理，易于维护

### 用户体验

- **语言切换**: 浏览器设置自动生效
- **内容一致性**: 同一数据的中英文完全对应
- **性能影响**: 几乎无影响，翻译在内存中完成

### 技术优势

- **API稳定性**: 字段名完全不变
- **扩展性**: 新增语言只需扩展翻译文件
- **兼容性**: 不影响现有前端代码
- **透明性**: 对业务逻辑完全透明

## 示例对比

### 修改前

```json
{
  "satisfactionRate": 85.7,
  "description": "Total Amazon Categories",
  "loadingText": "Loading products..."
}
```

### 修改后 (locale=zh)

```json
{
  "satisfactionRate": "85.7% 满意度",
  "description": "亚马逊类别总数", 
  "loadingText": "加载产品中..."
}
```

**前端代码无需任何修改，自动显示中文内容！**
