import json
import logging
import os
import pandas as pd
from typing import Dict, Any, Optional, List
from smolagents import Tool

logger = logging.getLogger(__name__)

# 数据文件路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "combined_products_with_final_categories.csv")
REVIEWS_FILE = os.path.join(DATA_DIR, "expanded_review_results.json")
ASPECT_CATEGORIZATION_FILE = os.path.join(DATA_DIR, "consolidated_aspect_categorization.json")
ASPECT_DEFINITIONS_FILE = os.path.join(DATA_DIR, "aspect_category_definitions.json")


class ProductQueryTool(Tool):
    """商品信息查询工具"""
    
    name = "product_query"
    description = """查询商品信息的工具。可以根据商品ID、品牌、型号、价格范围、评分范围、分类等条件查询商品。
    
    参数:
    - product_id: 商品平台ID（如 B095X5HTLS）
    - brand: 品牌名称（如 Amazon, Leviton, ELEGRP）
    - category: 商品分类（如 Dimmer Switches, Light Switches）
    - price_min: 最低价格（美元）
    - price_max: 最高价格（美元）
    - rating_min: 最低评分（1-5）
    - limit: 返回结果数量限制（默认10）
    """
    
    inputs = {
        "product_id": {
            "type": "string", 
            "description": "商品平台ID（如 B095X5HTLS）",
            "required": False,
            "nullable": True
        },
        "brand": {
            "type": "string", 
            "description": "品牌名称（如 Amazon, Leviton, ELEGRP）",
            "required": False,
            "nullable": True
        },
        "category": {
            "type": "string", 
            "description": "商品分类（如 Dimmer Switches, Light Switches）",
            "required": False,
            "nullable": True
        },
        "price_min": {
            "type": "number", 
            "description": "最低价格（美元）",
            "required": False,
            "nullable": True
        },
        "price_max": {
            "type": "number", 
            "description": "最高价格（美元）",
            "required": False,
            "nullable": True
        },
        "rating_min": {
            "type": "number", 
            "description": "最低评分（1-5）",
            "required": False,
            "nullable": True
        },
        "limit": {
            "type": "integer", 
            "description": "返回结果数量限制（默认10）",
            "required": False,
            "nullable": True
        }
    }
    
    output_type = "string"
    
    def __init__(self):
        super().__init__()
        self.products_df = None
        self._load_data()
    
    def _load_data(self):
        """加载商品数据"""
        try:
            if os.path.exists(PRODUCTS_FILE):
                self.products_df = pd.read_csv(PRODUCTS_FILE)
                logger.info(f"已加载 {len(self.products_df)} 条商品数据")
            else:
                logger.error(f"商品数据文件不存在: {PRODUCTS_FILE}")
        except Exception as e:
            logger.error(f"加载商品数据失败: {e}")
    
    def forward(self, product_id: str = None, brand: str = None, category: str = None, 
                price_min: float = None, price_max: float = None, 
                rating_min: float = None, limit: int = 10) -> str:
        """执行商品查询"""
        if self.products_df is None:
            return json.dumps({"error": "商品数据未加载"}, ensure_ascii=False)
        
        try:
            df = self.products_df.copy()
            
            # 根据条件过滤
            if product_id:
                df = df[df['platform_id'].str.contains(product_id, case=False, na=False)]
            
            if brand:
                df = df[df['brand'].str.contains(brand, case=False, na=False)]
            
            if category:
                df = df[df['category'].str.contains(category, case=False, na=False)]
            
            if price_min is not None:
                df = df[df['price_usd'] >= price_min]
            
            if price_max is not None:
                df = df[df['price_usd'] <= price_max]
            
            if rating_min is not None:
                df = df[df['rating'] >= rating_min]
            
            # 限制结果数量
            if limit is None:
                limit = 10
            df = df.head(limit)
            
            # 选择关键字段返回
            result_columns = [
                'platform_id', 'title', 'brand', 'model_number', 'price_usd', 
                'rating', 'reviews_count', 'category', 'product_segment'
            ]
            
            results = []
            for _, row in df.iterrows():
                product_info = {}
                for col in result_columns:
                    if col in row:
                        value = row[col]
                        # 处理 NaN 值
                        if pd.isna(value):
                            product_info[col] = None
                        else:
                            product_info[col] = value
                results.append(product_info)
            
            result = {
                "total_found": len(results),
                "products": results,
                "query_params": {
                    "product_id": product_id,
                    "brand": brand,
                    "category": category,
                    "price_min": price_min,
                    "price_max": price_max,
                    "rating_min": rating_min,
                    "limit": limit
                }
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"商品查询出错: {e}")
            return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


class ReviewQueryTool(Tool):
    """评论信息查询工具"""
    
    name = "review_query"
    description = """查询商品评论和方面分析信息的工具。可以根据商品ID查询评论数据和分类分析。
    
    参数:
    - product_id: 商品平台ID（如 B095X5HTLS）
    - aspect_category: 方面分类（如 phy, perf, use）
    - subcategory: 子分类（如 buttons, connectivity, installation）
    """
    
    inputs = {
        "product_id": {
            "type": "string", 
            "description": "商品平台ID（如 B095X5HTLS）",
            "required": True
        },
        "aspect_category": {
            "type": "string", 
            "description": "方面分类（如 phy, perf, use）",
            "required": False,
            "nullable": True
        },
        "subcategory": {
            "type": "string", 
            "description": "子分类（如 buttons, connectivity, installation）",
            "required": False,
            "nullable": True
        }
    }
    
    output_type = "string"
    
    def __init__(self):
        super().__init__()
        self.aspect_data = None
        self.aspect_definitions = None
        self._load_data()
    
    def _load_data(self):
        """加载评论和分类数据"""
        try:
            # 加载方面分类数据
            if os.path.exists(ASPECT_CATEGORIZATION_FILE):
                with open(ASPECT_CATEGORIZATION_FILE, 'r', encoding='utf-8') as f:
                    self.aspect_data = json.load(f)
                logger.info("已加载方面分类数据")
            
            # 加载分类定义
            if os.path.exists(ASPECT_DEFINITIONS_FILE):
                with open(ASPECT_DEFINITIONS_FILE, 'r', encoding='utf-8') as f:
                    self.aspect_definitions = json.load(f)
                logger.info("已加载分类定义数据")
                
        except Exception as e:
            logger.error(f"加载评论数据失败: {e}")
    
    def forward(self, product_id: str, aspect_category: str = None, 
                subcategory: str = None) -> str:
        """执行评论查询"""
        if self.aspect_data is None:
            return json.dumps({"error": "评论数据未加载"}, ensure_ascii=False)
        
        try:
            # 查找商品的方面分类数据
            product_data = self.aspect_data.get("results", {}).get(product_id)
            
            if not product_data:
                return json.dumps({"error": f"未找到商品 {product_id} 的评论数据"}, ensure_ascii=False)
            
            aspect_categorization = product_data.get("aspect_categorization", {})
            
            result = {
                "product_id": product_id,
                "aspect_categorization": {}
            }
            
            # 如果指定了主要分类，只返回该分类
            if aspect_category:
                if aspect_category in aspect_categorization:
                    category_data = aspect_categorization[aspect_category]
                    
                    # 如果指定了子分类，只返回该子分类
                    if subcategory:
                        if subcategory in category_data:
                            result["aspect_categorization"][aspect_category] = {
                                subcategory: category_data[subcategory]
                            }
                        else:
                            return json.dumps({"error": f"未找到子分类 {subcategory}"}, ensure_ascii=False)
                    else:
                        result["aspect_categorization"][aspect_category] = category_data
                else:
                    return json.dumps({"error": f"未找到分类 {aspect_category}"}, ensure_ascii=False)
            else:
                # 返回所有分类
                result["aspect_categorization"] = aspect_categorization
            
            # 添加分类定义信息（如果有的话）
            if self.aspect_definitions:
                result["category_definitions"] = self.aspect_definitions.get("category_definitions", {})
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"评论查询出错: {e}")
            return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)


def get_data_files_status() -> Dict[str, bool]:
    """获取数据文件状态"""
    return {
        "products_csv": os.path.exists(PRODUCTS_FILE),
        "reviews_json": os.path.exists(REVIEWS_FILE),
        "aspect_categorization": os.path.exists(ASPECT_CATEGORIZATION_FILE),
        "aspect_definitions": os.path.exists(ASPECT_DEFINITIONS_FILE)
    }


def test_tools() -> Dict[str, Any]:
    """测试工具功能"""
    try:
        # 测试商品查询工具
        product_tool = ProductQueryTool()
        product_result = product_tool.forward(brand="Leviton", limit=3)
        
        # 测试评论查询工具
        review_tool = ReviewQueryTool()
        # 使用第一个找到的商品ID进行测试
        product_data = json.loads(product_result)
        if product_data.get("products"):
            test_product_id = product_data["products"][0]["platform_id"]
            review_result = review_tool.forward(product_id=test_product_id, aspect_category="phy")
        else:
            review_result = json.dumps({"error": "没有找到测试商品"}, ensure_ascii=False)
        
        return {
            "product_tool_test": json.loads(product_result),
            "review_tool_test": json.loads(review_result)
        }
    except Exception as e:
        return {"error": f"工具测试失败: {str(e)}"} 