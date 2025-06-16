## 理解您的需求

您想要将现有的硬编码爬取系统改造为：1. 前端Web界面：用户可以输入Amazon URL

1. 参数可配置：用户可以调整爬取参数
2. 动态处理：根据URL自动识别分类和产品信息

## 项目改造方案

### 🛠️ 需要修改的现有文件

#### 1. backend/src/competitor/amazon_api.py

调整内容：* 新增方法：parse_amazon_url() - 解析各种Amazon URL格式

* 新增方法：get_category_from_node() - 从node参数获取分类信息
* 新增方法：get_category_from_product() - 从产品页面获取分类信息
* 优化方法：amazon_search() - 支持动态参数配置

#### 2. backend/src/competitor/scrape_best_sellers.py

调整内容：* 重构方法：scrape_amazon_best_sellers() - 接收动态配置参数

* 新增方法：scrape_from_url_config() - 基于URL配置的爬取入口
* 移除：硬编码的CATEGORY_MAPPING字典

#### 3. backend/src/competitor/scrape_reviews.py

调整内容：* 重构方法：scrape_all_amazon_reviews() - 接收动态ASIN列表

* 新增方法：scrape_reviews_from_config() - 基于配置的评论爬取
* 移除：硬编码的产品ASIN列表读取

### 🆕 需要新建的文件

#### 1. backend/src/api/ (新目录)

text

Apply to amazon_searc...

**├── __init__.py**

**├── main.py              # FastAPI主应用**

**├── routers/**

**│   ├── __init__.py**

**│   ├── scraping.py      # 爬取相关API路由**

**│   └── config.py        # 配置相关API路由**

**├── models/**

**│   ├── __init__.py**

**│   ├── scraping_models.py  # 爬取请求/响应模型**

**│   └── config_models.py    # 配置模型**

**└── services/**

**    ├── __init__.py**

**    ├── url_parser.py       # URL解析服务**

**    └── scraping_service.py # 爬取业务逻辑**

#### 2. backend/src/config/ (新目录)

text

Apply to amazon_searc...

**├── __init__.py**

**├── scraping_config.py   # 爬取配置管理**

**└── api_config.py        # API配置管理**


### 📋 各文件具体调整（方法级别）

#### A. 新建：backend/src/api/services/url_parser.py

python

Apply to amazon_searc...

**class** **AmazonURLParser**:

**    **def** **parse_url**(**)**          **# 主解析入口

**    **def** **extract_asin**(**)**       **# 提取产品ASIN

**    **def** **extract_node_id**(**)**    **# 提取分类node ID

**    **def** **extract_search_term**(**)** **# 提取搜索关键词

**    **def** **get_url_type**(**)**       **# 判断URL类型（产品/分类/搜索）

**    **def** **build_scraping_config**(**)** **# 构建爬取配置

#### B. 新建：backend/src/api/routers/scraping.py

python

Apply to amazon_searc...

**# API路由定义**

**@router**.**post**(**"/parse-url"**)**        **# 解析URL接口

**@router**.**post**(**"/start-scraping"**)**   **# 启动爬取任务

**@router**.**get**(**"/scraping-status"**)**   **# 查询爬取状态

**@router**.**get**(**"/scraping-results"**)**  **# 获取爬取结果

#### C. 新建：backend/src/api/models/scraping_models.py

python

Apply to amazon_searc...

**class** **URLParseRequest**:     **# URL解析请求模型**

**class** **ScrapingConfig**:      **# 爬取配置模型**

**class** **ScrapingTask**:        **# 爬取任务模型**

**class** **ScrapingResult**:      **# 爬取结果模型**


## 🌐 URL处理流程举例

### 示例1：产品URL处理

用户输入：https://www.amazon.com/dp/B0076HPM8A

处理流程：1. URL解析：提取ASIN = "B0076HPM8A"

1. 获取产品信息：调用Rainforest API获取产品详情
2. 提取分类信息：从产品信息中获取分类breadcrumbs
3. 构建爬取配置：

   json

   Apply to amazon_searc...

   **   **{

   **     **"scrape_type"**: **"similar_products"**,**

   **     **"search_term"**: **"leviton dimmer switch"**,**

   **     **"category_id"**: **"507840"**,**

   **     **"target_count"**: **100

   **   **}

### 示例2：分类URL处理

用户输入：https://www.amazon.com/b?node=166057011

处理流程：1. URL解析：提取node = "166057011"

1. 获取分类信息：调用API获取该分类的详细信息
2. 构建爬取配置：

   json

   Apply to amazon_searc...

   **   **{

   **     **"scrape_type"**: **"category_products"**, **

   **     **"category_id"**: **"166057011"**,**

   **     **"search_term"**: **"auto-generated from category"**,**

   **     **"target_count"**: **150

   **   **}

## 🔍 关于Node ID vs Category ID

### Node ID (166057011) 的含义：

* 定义：Amazon的页面节点标识符
* 用途：标识特定的浏览页面/分类页面
* 获取方式：从https://www.amazon.com/b?node=166057011等分类页面URL中提取

### 与Category ID的关系：

python

Apply to amazon_searc...

**# node 和 category_id 的关系**

**node_id** **(**166057011**)**     **# 页面级别的标识**

**    ↓ 通过API查询**

**category_id** **(**507840**)**    **# 产品搜索级别的分类ID**

**    ↓ 用于搜索API**

**search_results          **# 该分类下的产品列表

关键区别：* Node ID：用于浏览Amazon分类页面

* Category ID：用于产品搜索API的分类筛选
* 转换关系：需要通过API调用将node转换为对应的category_id

实际处理：

python

Apply to amazon_searc...

**def** **convert_node_to_category**(**node_id**)**:**

**    **# 1. 调用Amazon页面获取分类信息

**    **# 2. 解析页面中的分类结构

**    **# 3. 提取对应的category_id

**    **# 4. 返回可用于搜索API的category_id

这样的改造方案可以让用户通过Web界面灵活配置爬取任务，支持多种URL格式的智能解析。
