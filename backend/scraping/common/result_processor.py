import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ScrapingResultProcessor:
    """
    爬取结果处理器
    负责处理和转换爬取结果数据
    """
    
    def __init__(self):
        pass
    
    async def process_scraping_result(self, json_file_path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        处理爬取结果JSON文件，转换为数据库格式
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: (请求数据, 产品数据列表)
        """
        try:
            logger.info(f"开始处理爬取结果文件: {json_file_path}")
            
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                logger.warning(f"JSON文件为空: {json_file_path}")
                return {}, []
            
            # 提取请求信息
            request_data = await self._extract_request_data(data, json_file_path)
            
            # 提取产品数据
            products_data = await self._extract_products_data(data)
            
            logger.info(f"处理完成: {len(products_data)} 个产品")
            
            return request_data, products_data
            
        except Exception as e:
            logger.error(f"处理爬取结果时出错: {e}")
            raise
    
    async def _extract_request_data(self, data: Dict[str, Any], json_file_path: str) -> Dict[str, Any]:
        """
        从JSON数据中提取请求信息
        
        Args:
            data: JSON数据
            json_file_path: JSON文件路径
            
        Returns:
            Dict[str, Any]: 请求数据
        """
        request_data = {
            'request_type': 'unknown',
            'search_term': None,
            'category_id': None,
            'amazon_domain': 'amazon.com',
            'products_scraped': 0,
            'request_metadata': {},
            'status': 'pending'
        }
        
        try:
            # 从文件名推断请求类型
            file_name = Path(json_file_path).name
            if 'search_' in file_name:
                request_data['request_type'] = 'search'
            elif 'category_' in file_name or 'bestseller' in file_name:
                request_data['request_type'] = 'category'
            
            # 从scraping_summary获取信息（如果存在）
            if 'scraping_summary' in data:
                summary = data['scraping_summary']
                request_data.update({
                    'request_type': summary.get('type', request_data['request_type']),
                    'search_term': summary.get('search_term'),
                    'category_id': summary.get('category_id'),
                    'amazon_domain': summary.get('amazon_domain', 'amazon.com')
                })
            
            # 从request_parameters获取信息（如果存在）
            if 'request_parameters' in data:
                params = data['request_parameters']
                if not request_data.get('search_term'):
                    request_data['search_term'] = params.get('query')
                if not request_data.get('category_id'):
                    request_data['category_id'] = params.get('category_id')
                if not request_data.get('amazon_domain'):
                    request_data['amazon_domain'] = params.get('amazon_domain', 'amazon.com')
            
            # 计算实际产品数量
            products_count = 0
            if 'search_results' in data and isinstance(data['search_results'], list):
                products_count = len(data['search_results'])
            elif 'category_results' in data and isinstance(data['category_results'], list):
                products_count = len(data['category_results'])
            elif 'bestsellers_results' in data and isinstance(data['bestsellers_results'], list):
                products_count = len(data['bestsellers_results'])
            elif isinstance(data, list):
                products_count = len(data)
            
            request_data['products_scraped'] = products_count
            
            # 保存原始元数据
            request_data['request_metadata'] = {
                'request_info': data.get('request_info', {}),
                'request_parameters': data.get('request_parameters', {}),
                'request_metadata': data.get('request_metadata', {}),
                'search_information': data.get('search_information', {}),
                'category_information': data.get('category_information', {}),
                'pagination': data.get('pagination', {}),
                'file_name': Path(json_file_path).name,
                'file_path': json_file_path,  # 将文件路径存储在metadata中
                'processed_at': datetime.now().isoformat()
            }
            
            logger.info(f"提取请求数据: 类型={request_data['request_type']}, 产品数={products_count}")
            
        except Exception as e:
            logger.error(f"提取请求数据时出错: {e}")
            # 使用默认值
            pass
        
        return request_data
    
    async def _extract_products_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从JSON数据中提取产品信息
        
        Args:
            data: JSON数据
            
        Returns:
            List[Dict[str, Any]]: 产品数据列表
        """
        products = []
        
        try:
            # 获取产品列表
            raw_products = []
            
            if 'search_results' in data and isinstance(data['search_results'], list):
                raw_products = data['search_results']
            elif 'category_results' in data and isinstance(data['category_results'], list):
                raw_products = data['category_results']
            elif 'bestsellers_results' in data and isinstance(data['bestsellers_results'], list):
                raw_products = data['bestsellers_results']
            elif isinstance(data, list):
                raw_products = data
            
            # 转换每个产品
            for raw_product in raw_products:
                if not isinstance(raw_product, dict):
                    continue
                
                processed_product = await self._process_single_product(raw_product)
                if processed_product:
                    products.append(processed_product)
            
            logger.info(f"成功处理 {len(products)} 个产品")
            
        except Exception as e:
            logger.error(f"提取产品数据时出错: {e}")
        
        return products
    
    async def _process_single_product(self, raw_product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理单个产品数据
        
        Args:
            raw_product: 原始产品数据
            
        Returns:
            Dict[str, Any]: 处理后的产品数据
        """
        try:
            # 必须有ASIN
            asin = raw_product.get('asin')
            if not asin:
                logger.warning("产品缺少ASIN，跳过")
                return None
            
            # 提取基本信息，映射到数据库字段名
            product = {
                'source': 'amazon_api',  # 数据库字段：source
                'platform_id': asin,     # 数据库字段：platform_id (存储ASIN)
                'title': self._safe_strip(raw_product.get('title', '')),
                'brand': self._safe_strip(raw_product.get('brand', '')),
                'price_usd': self._extract_price(raw_product),  # 数据库字段：price_usd
                'rating': self._extract_rating(raw_product),
                'reviews_count': self._extract_review_count(raw_product),  # 数据库字段：reviews_count
                'image_url': self._safe_strip(raw_product.get('image', '')),
                'product_url': self._safe_strip(raw_product.get('link', '')),
                'availability': self._extract_availability(raw_product),
                'features': self._extract_features_as_text(raw_product),  # 数据库字段是text类型
                'description': self._safe_strip(raw_product.get('description', '')),
                'category': self._extract_category_as_text(raw_product),  # 数据库字段：category (text)
                'extract_date': datetime.now().strftime('%Y-%m-%d')  # 数据库字段：extract_date
            }
            
            return product
            
        except Exception as e:
            logger.error(f"处理单个产品时出错: {e}")
            return None
    
    def _safe_strip(self, value: Any) -> str:
        """安全地对值执行strip操作"""
        if isinstance(value, str):
            return value.strip()
        elif value is None:
            return ''
        else:
            return str(value).strip()
    
    def _extract_availability(self, product: Dict[str, Any]) -> str:
        """提取可用性信息"""
        try:
            availability = product.get('availability', '')
            
            # 如果是字典类型，提取raw字段
            if isinstance(availability, dict):
                raw_availability = availability.get('raw', '')
                if raw_availability:
                    return str(raw_availability).strip()
                else:
                    return 'Available'  # 默认值
            elif isinstance(availability, str):
                return availability.strip()
            else:
                return 'Available'  # 默认值
                
        except Exception:
            return 'Available'  # 默认值
    
    def _extract_price(self, product: Dict[str, Any]) -> Optional[float]:
        """提取价格信息"""
        try:
            # 首先尝试从price字段获取
            if 'price' in product:
                price_value = product['price']
                if isinstance(price_value, dict) and 'value' in price_value:
                    return float(price_value['value'])
                elif isinstance(price_value, (int, float)):
                    return float(price_value)
            
            # 然后尝试从prices数组获取主要价格
            if 'prices' in product and isinstance(product['prices'], list):
                for price_obj in product['prices']:
                    if isinstance(price_obj, dict):
                        if price_obj.get('is_primary', False) or price_obj.get('name') == 'Primary':
                            return float(price_obj.get('value', 0))
                
                # 如果没有主要价格，取第一个价格
                if product['prices']:
                    first_price = product['prices'][0]
                    if isinstance(first_price, dict) and 'value' in first_price:
                        return float(first_price['value'])
            
            # 兜底：尝试其他价格字段
            price_fields = ['current_price', 'list_price', 'price_current']
            
            for field in price_fields:
                if field in product:
                    price_value = product[field]
                    if isinstance(price_value, (int, float)):
                        return float(price_value)
                    elif isinstance(price_value, str):
                        # 提取数字
                        import re
                        price_match = re.search(r'[\d,]+\.?\d*', price_value.replace(',', ''))
                        if price_match:
                            return float(price_match.group())
            
            return None
        except Exception as e:
            logger.debug(f"提取价格时出错: {e}")
            return None
    
    def _extract_rating(self, product: Dict[str, Any]) -> Optional[float]:
        """提取评分信息"""
        try:
            rating_fields = ['rating', 'ratings', 'average_rating', 'stars']
            
            for field in rating_fields:
                if field in product:
                    rating_value = product[field]
                    if isinstance(rating_value, (int, float)):
                        return float(rating_value)
                    elif isinstance(rating_value, str):
                        # 提取数字
                        import re
                        rating_match = re.search(r'(\d+\.?\d*)', rating_value)
                        if rating_match:
                            return float(rating_match.group(1))
            
            return None
        except:
            return None
    
    def _extract_review_count(self, product: Dict[str, Any]) -> Optional[int]:
        """提取评论数量"""
        try:
            review_fields = ['reviews_count', 'review_count', 'ratings_total', 'total_reviews']
            
            for field in review_fields:
                if field in product:
                    review_value = product[field]
                    if isinstance(review_value, int):
                        return review_value
                    elif isinstance(review_value, str):
                        # 提取数字
                        import re
                        review_match = re.search(r'([\d,]+)', review_value.replace(',', ''))
                        if review_match:
                            return int(review_match.group(1))
            
            return None
        except:
            return None
    
    def _extract_categories(self, product: Dict[str, Any]) -> List[str]:
        """提取分类信息"""
        try:
            categories = []
            
            if 'categories' in product:
                cat_data = product['categories']
                if isinstance(cat_data, list):
                    for cat in cat_data:
                        if isinstance(cat, dict) and 'name' in cat:
                            categories.append(cat['name'])
                        elif isinstance(cat, str):
                            categories.append(cat)
                elif isinstance(cat_data, str):
                    categories.append(cat_data)
            
            return categories
        except:
            return []
    
    def _extract_features(self, product: Dict[str, Any]) -> List[str]:
        """提取产品特性"""
        try:
            features = []
            
            if 'features' in product:
                feat_data = product['features']
                if isinstance(feat_data, list):
                    features.extend([str(f) for f in feat_data if f])
                elif isinstance(feat_data, str):
                    features.append(feat_data)
            
            if 'bullet_points' in product:
                bp_data = product['bullet_points']
                if isinstance(bp_data, list):
                    features.extend([str(bp) for bp in bp_data if bp])
            
            return features
        except:
            return []
    
    def _extract_features_as_text(self, product: Dict[str, Any]) -> str:
        """提取产品特性（返回文本，用于数据库存储）"""
        try:
            features_list = self._extract_features(product)
            if features_list:
                return ' | '.join(features_list)  # 用分隔符连接
            return ''
        except:
            return ''
    
    def _extract_category_as_text(self, product: Dict[str, Any]) -> str:
        """提取产品类别（返回文本，用于数据库存储）"""
        try:
            categories = self._extract_categories(product)
            if categories:
                return ' > '.join(categories)  # 用层级分隔符连接
            return ''
        except:
            return '' 