import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ScrapingResultProcessor:
    """爬取结果数据处理器"""
    
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
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理请求数据
            request_data = self._process_request_data(data, json_file_path)
            
            # 处理产品数据
            products_data = self._process_products_data(data)
            
            logger.info(f"成功处理JSON文件: {json_file_path}, 产品数量: {len(products_data)}")
            
            return request_data, products_data
            
        except Exception as e:
            logger.error(f"处理JSON文件时出错 {json_file_path}: {e}")
            raise
    
    def _process_request_data(self, data: Dict[str, Any], json_file_path: str) -> Dict[str, Any]:
        """
        处理请求数据，映射到scraping_requests表格式
        
        Args:
            data: JSON数据
            json_file_path: JSON文件路径
            
        Returns:
            Dict[str, Any]: 请求数据
        """
        scraping_summary = data.get('scraping_summary', {})
        request_parameters = data.get('request_parameters', {})
        
        request_data = {
            'request_type': scraping_summary.get('type', 'unknown'),
            'search_term': scraping_summary.get('search_term'),
            'category_id': scraping_summary.get('category_id'),
            'amazon_domain': scraping_summary.get('amazon_domain', 'amazon.com'),
            'status': 'completed',
            'total_results': data.get('search_information', {}).get('total_results'),
            'total_pages': data.get('pagination', {}).get('total_pages'),
            'products_scraped': scraping_summary.get('total_products', 0),
            'request_info': data.get('request_info', {}),
            'request_parameters': request_parameters,
            'request_metadata': data.get('request_metadata', {}),
            'search_information': data.get('search_information', {}),
            'pagination': data.get('pagination', {}),
            'scraping_summary': scraping_summary,
            'scraped_at': datetime.now().isoformat()
        }
        
        return request_data
    
    def _process_products_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理产品数据，映射到amazon_products表格式
        
        Args:
            data: JSON数据
            
        Returns:
            List[Dict[str, Any]]: 产品数据列表
        """
        products = []
        
        # 根据数据结构获取产品列表
        if 'category_results' in data:
            raw_products = data['category_results']
        elif 'search_results' in data:
            raw_products = data['search_results']
        else:
            logger.warning("未找到产品数据在JSON中")
            return products
        
        for product in raw_products:
            processed_product = self._process_single_product(product)
            if processed_product:
                products.append(processed_product)
        
        return products
    
    def _process_single_product(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理单个产品数据
        
        Args:
            product: 原始产品数据
            
        Returns:
            Optional[Dict[str, Any]]: 处理后的产品数据
        """
        try:
            # 获取价格信息
            price_value = None
            list_price_value = None
            
            if 'price' in product and product['price']:
                price_value = product['price'].get('value')
                list_price_value = self._extract_list_price(product['price'])
            elif 'prices' in product and product['prices']:
                # 取第一个价格作为主价格
                first_price = product['prices'][0]
                price_value = first_price.get('value')
                list_price_value = self._extract_list_price(first_price)
            
            # 获取分类信息
            categories = product.get('categories', [])
            leaf_category_id = None
            leaf_category_name = None
            categories_flat = product.get('categories_flat', '')
            
            if categories:
                # 取最后一个分类作为叶子分类
                leaf_category = categories[-1]
                leaf_category_id = leaf_category.get('category_id') or leaf_category.get('id')
                leaf_category_name = leaf_category.get('name')
            
            # 获取图片URL
            image_url = None
            if 'image' in product:
                image_url = product['image']
            elif 'main_image' in product and product['main_image']:
                image_url = product['main_image'].get('link')
            
            # 获取产品URL
            product_url = product.get('link')
            
            # 处理品牌信息
            brand = product.get('brand')
            if not brand and 'sub_title' in product and product['sub_title']:
                # 尝试从sub_title中提取品牌
                sub_title_text = product['sub_title'].get('text', '')
                if 'Visit the' in sub_title_text and 'Store' in sub_title_text:
                    brand = sub_title_text.replace('Visit the ', '').replace(' Store', '')
            
            # 处理库存状态
            availability = None
            if 'availability' in product and product['availability']:
                availability = product['availability'].get('raw')
            
            # 处理最近销量
            recent_sales = product.get('recent_sales')
            
            # 处理畅销商品标志
            is_bestseller = None
            if 'bestseller' in product and product['bestseller']:
                is_bestseller = product['bestseller'].get('category')
            
            processed_product = {
                'source': 'amazon',
                'platform_id': product.get('asin'),
                'title': product.get('title'),
                'brand': brand,
                'price_usd': price_value,
                'list_price_usd': list_price_value,
                'rating': product.get('rating'),
                'reviews_count': product.get('ratings_total'),
                'position': product.get('position'),
                'category': leaf_category_name,
                'image_url': image_url,
                'product_url': product_url,
                'availability': availability,
                'recent_sales': recent_sales,
                'is_bestseller': is_bestseller,
                'unit_price': product.get('unit_price'),
                'leaf_category_id': leaf_category_id,
                'leaf_category_name': leaf_category_name,
                'categories_flat': categories_flat,
                'extract_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # 不过滤None值，保持所有字段一致性，让数据库处理NULL值
            return processed_product
            
        except Exception as e:
            logger.error(f"处理单个产品数据时出错: {e}")
            logger.error(f"产品数据: {product}")
            return None
    
    def _extract_list_price(self, price_data: Dict[str, Any]) -> Optional[float]:
        """
        从价格数据中提取原价
        
        Args:
            price_data: 价格数据
            
        Returns:
            Optional[float]: 原价或None
        """
        # 尝试从list_price字段获取
        list_price_str = price_data.get('list_price')
        if list_price_str and isinstance(list_price_str, str):
            try:
                # 移除货币符号并转换为浮点数
                list_price_clean = list_price_str.replace('$', '').strip()
                return float(list_price_clean)
            except ValueError:
                pass
        
        return None 