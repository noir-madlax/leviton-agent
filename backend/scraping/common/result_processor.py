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
            elif 'product_' in file_name:
                request_data['request_type'] = 'product'
            
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
            
            # 确保category_id是字符串类型（如果存在）
            if request_data.get('category_id') is not None:
                request_data['category_id'] = str(request_data['category_id'])
            
            # 确保search_term不超过数据库字段长度限制
            if request_data.get('search_term'):
                request_data['search_term'] = str(request_data['search_term'])[:500]  # 假设数据库字段限制为500字符
            
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
            
            # 验证必要字段
            if not request_data.get('request_type') or request_data['request_type'] == 'unknown':
                logger.warning(f"无法确定请求类型，使用默认值 'category'")
                request_data['request_type'] = 'category'
            
            logger.info(f"提取请求数据: 类型={request_data['request_type']}, 产品数={products_count}, 类别ID={request_data.get('category_id')}")
            
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
                'list_price_usd': self._extract_list_price(raw_product),  # 数据库字段：list_price_usd
                'rating': self._extract_rating(raw_product),
                'reviews_count': self._extract_review_count(raw_product),  # 数据库字段：reviews_count
                'position': self._extract_position(raw_product),  # 数据库字段：position
                'image_url': self._safe_strip(raw_product.get('image', '')),
                'product_url': self._safe_strip(raw_product.get('link', '')),
                'availability': self._extract_availability(raw_product),
                'recent_sales': self._safe_strip(raw_product.get('recent_sales', '')),  # 数据库字段：recent_sales
                'is_bestseller': self._extract_bestseller(raw_product),  # 数据库字段：is_bestseller
                'unit_price': self._safe_strip(raw_product.get('unit_price', '')),  # 数据库字段：unit_price
                'features': self._extract_features_as_text(raw_product),  # 数据库字段是text类型
                'description': self._safe_strip(raw_product.get('description', '')),
                'category': self._extract_category_as_text(raw_product),  # 数据库字段：category (text)
                'categories_flat': self._extract_categories_flat_as_text(raw_product),  # 数据库字段：categories_flat (text)
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
                # 只返回最下级的类别名称
                return categories[-1]  # 最后一个元素是最下级的类别
            return ''
        except:
            return ''
    
    def _extract_categories_flat_as_text(self, product: Dict[str, Any]) -> str:
        """提取产品类别完整路径（返回文本，用于数据库存储）"""
        try:
            categories = self._extract_categories(product)
            if categories:
                return ' > '.join(categories)  # 用层级分隔符连接完整路径
            return ''
        except:
            return ''
    
    def _extract_list_price(self, product: Dict[str, Any]) -> Optional[float]:
        """提取标价/原价信息"""
        try:
            # 从prices数组中查找原价 (is_rrp: true)
            if 'prices' in product and isinstance(product['prices'], list):
                for price_obj in product['prices']:
                    if isinstance(price_obj, dict):
                        # 优先查找is_rrp标记
                        if price_obj.get('is_rrp') is True:
                            return float(price_obj.get('value', 0))
                        # 备用：查找名称匹配
                        price_name = price_obj.get('name', '').lower()
                        if 'original' in price_name or 'list' in price_name or 'retail' in price_name or 'was' in price_name:
                            return float(price_obj.get('value', 0))
            
            # 直接从list_price字段获取
            if 'list_price' in product:
                list_price_value = product['list_price']
                if isinstance(list_price_value, dict) and 'value' in list_price_value:
                    return float(list_price_value['value'])
                elif isinstance(list_price_value, (int, float)):
                    return float(list_price_value)
                elif isinstance(list_price_value, str):
                    # 提取数字
                    import re
                    price_match = re.search(r'[\d,]+\.?\d*', list_price_value.replace(',', ''))
                    if price_match:
                        return float(price_match.group())
            
            # 尝试其他可能的字段
            for field in ['original_price', 'retail_price', 'msrp']:
                if field in product:
                    value = product[field]
                    if isinstance(value, (int, float)):
                        return float(value)
                    elif isinstance(value, str):
                        import re
                        price_match = re.search(r'[\d,]+\.?\d*', value.replace(',', ''))
                        if price_match:
                            return float(price_match.group())
            
            return None
        except Exception as e:
            logger.debug(f"提取标价时出错: {e}")
            return None
    
    def _extract_position(self, product: Dict[str, Any]) -> Optional[int]:
        """提取产品在搜索结果中的位置"""
        try:
            # 直接从position字段获取
            if 'position' in product:
                position_value = product['position']
                if isinstance(position_value, int):
                    return position_value
                elif isinstance(position_value, str):
                    # 提取数字
                    import re
                    position_match = re.search(r'(\d+)', position_value)
                    if position_match:
                        return int(position_match.group(1))
            
            # 从ranking字段获取
            if 'ranking' in product:
                ranking_value = product['ranking']
                if isinstance(ranking_value, int):
                    return ranking_value
                elif isinstance(ranking_value, str):
                    import re
                    ranking_match = re.search(r'(\d+)', ranking_value)
                    if ranking_match:
                        return int(ranking_match.group(1))
            
            return None
        except:
            return None
    
    def _extract_bestseller(self, product: Dict[str, Any]) -> bool:
        """提取是否为畅销产品"""
        try:
            # 检查bestseller_badge字段 (主要字段)
            if 'bestseller_badge' in product:
                bestseller_badge = product['bestseller_badge']
                if isinstance(bestseller_badge, dict):
                    # 如果有bestseller_badge对象，说明是畅销产品
                    return bool(bestseller_badge.get('category') or bestseller_badge.get('link'))
                elif bestseller_badge:  # 非空值
                    return True
            
            # 检查is_bestseller字段
            if 'is_bestseller' in product:
                return bool(product['is_bestseller'])
            
            if 'bestseller' in product:
                bestseller_value = product['bestseller']
                if isinstance(bestseller_value, bool):
                    return bestseller_value
                elif isinstance(bestseller_value, str):
                    return bestseller_value.lower() in ['true', 'yes', '1', 'bestseller']
            
            # 检查badges或标签中是否有bestseller标识
            if 'badges' in product and isinstance(product['badges'], list):
                for badge in product['badges']:
                    if isinstance(badge, str) and 'bestseller' in badge.lower():
                        return True
                    elif isinstance(badge, dict) and 'text' in badge:
                        if 'bestseller' in badge['text'].lower():
                            return True
            
            # 检查title中是否包含bestseller标识
            title = product.get('title', '').lower()
            if '#1 best seller' in title or 'bestseller' in title:
                return True
            
            return False
        except:
            return False 