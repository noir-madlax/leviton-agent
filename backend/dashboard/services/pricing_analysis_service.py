"""Pricing analysis service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class PricingAnalysisService(BaseDashboardService):
    """Service for pricing analysis data.
    
    通用化版本：动态处理项目的所有segment类型。
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get pricing analysis data with dynamic category support."""
        try:
            # 查询定价数据 - 添加category字段
            query = self._get_base_product_table().select('''
                platform_id,
                title,
                brand,
                price_usd,
                unit_price_calculated,
                category
            ''')
            
            # Apply filters
            query = self._apply_base_filters(query)
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            if not result.data:
                logger.warning(f"No pricing analysis data found for project {self.project_id}")
                return self._get_empty_response()
            
            # 过滤有价格数据和类别数据的产品
            products_with_price = [item for item in result.data if item.get('price_usd') and item.get('category')]
            logger.info(f"📊 Found {len(products_with_price)} products with pricing and category data")
            
            # 获取所有产品的类别
            categories = list(set(item.get('category') for item in products_with_price if item.get('category')))
            
            if not categories:
                logger.warning(f"No categories found for project {self.project_id}")
                return self._get_empty_response()
            
            # 分类产品 - 按category维度
            categorized_products = self._categorize_products_by_category(products_with_price)
            
            # 获取smart_capability数据并按智能属性分类产品
            smart_categorized_products = self._categorize_products_by_smart_capability(products_with_price)
            
            # 格式化响应 - 合并category和smart维度数据
            response = self._format_combined_pricing_response(categorized_products, smart_categorized_products, categories)
            
            logger.info(f"📈 Pricing analysis completed with {len(categories)} categories and smart/non-smart dimensions")
            return response
            
        except Exception as e:
            logger.error(f"Error in pricing analysis for project {self.project_id}: {e}")
            raise
    
    def _categorize_products_by_category(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将产品按类别分类"""
        categorized = {}
        for product in products:
            category = product.get('category')
            if category:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(product)
        return categorized
    
    def _categorize_products_by_smart_capability(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将产品按智能属性分类"""
        try:
            # 获取项目的智能属性数据
            smart_capability_data = self._get_smart_capability_data()
            
            # 创建ASIN到智能属性的映射
            asin_to_smart = {}
            for data_row in smart_capability_data:
                asin = data_row.get('asins')
                extend_data = data_row.get('extend', {})
                smart_capability = extend_data.get('smart_capability')
                if asin and smart_capability:
                    asin_to_smart[asin] = smart_capability
            
            # 按智能属性分类产品
            smart_categorized = {'Smart': [], 'Non-Smart': []}
            
            for product in products:
                platform_id = product.get('platform_id')
                smart_capability = asin_to_smart.get(platform_id, 'Unknown')
                
                if smart_capability in ['Smart', 'Non-Smart']:
                    smart_categorized[smart_capability].append(product)
            
            logger.info(f"📊 Smart capability categorization: Smart={len(smart_categorized['Smart'])}, Non-Smart={len(smart_categorized['Non-Smart'])}")
            return smart_categorized
            
        except Exception as e:
            logger.error(f"Error categorizing products by smart capability: {e}")
            return {'Smart': [], 'Non-Smart': []}
    
    def _get_smart_capability_data(self) -> List[Dict[str, Any]]:
        """获取项目的智能属性数据"""
        try:
            query = self.supabase.table('project_extend_data')\
                .select('asins, extend')\
                .eq('project_id', self.project_id)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching smart capability data: {e}")
            return []
    
    def _format_pricing_response(self, categorized_products: Dict[str, List[Dict[str, Any]]], categories: List[str]) -> Dict[str, Any]:
        """格式化定价响应数据，返回真实的segment-based格式"""
        import statistics
        
        if not categorized_products:
            return self._get_empty_response()
        
        # 按收入排序segments
        category_revenue_list = []
        for category, products in categorized_products.items():
            if products:  # 只包含有产品的segments
                total_revenue = sum(float(p.get('price_usd', 0) or 0) for p in products)
                category_revenue_list.append((category, total_revenue, products))
        
        category_revenue_list.sort(key=lambda x: x[1], reverse=True)
        
        # 显示所有有数据的segments，不限制数量
        main_categories = category_revenue_list
        
        def calculate_price_stats(prices: List[float]) -> Dict[str, float]:
            """计算价格统计信息"""
            if not prices:
                return {
                    'min': 0, 'q1': 0, 'median': 0, 
                    'mean': 0, 'q3': 0, 'max': 0
                }
            
            sorted_prices = sorted(prices)
            n = len(sorted_prices)
            
            return {
                'min': float(sorted_prices[0]),
                'q1': float(sorted_prices[n//4]) if n > 3 else float(sorted_prices[0]),
                'median': float(statistics.median(sorted_prices)),
                'mean': float(statistics.mean(sorted_prices)),
                'q3': float(sorted_prices[3*n//4]) if n > 3 else float(sorted_prices[-1]),
                'max': float(sorted_prices[-1])
            }
        
        def get_price_distribution(products: List[Dict[str, Any]], category_name: str) -> Dict[str, Any]:
            """获取价格分布数据"""
            sku_prices = []
            unit_prices = []
            
            for product in products:
                sku_price = product.get('price_usd', 0) or 0
                unit_price = product.get('unit_price_calculated', 0) or 0
                
                if sku_price > 0:
                    sku_prices.append(float(sku_price))
                if unit_price > 0:
                    unit_prices.append(float(unit_price))
            
            return {
                'category': category_name,
                'skuPrices': sku_prices,
                'unitPrices': unit_prices,
                'productCount': len(products),
                'stats': {
                    'sku': calculate_price_stats(sku_prices),
                    'unit': calculate_price_stats(unit_prices)
                }
            }
        
        def get_brand_price_distribution(products: List[Dict[str, Any]], category_name: str) -> Dict[str, Any]:
            """获取品牌价格分布数据"""
            brand_data = {}
            
            for product in products:
                brand = product.get('brand', 'Unknown')
                sku_price = product.get('price_usd', 0) or 0
                unit_price = product.get('unit_price_calculated', 0) or 0
                
                if brand not in brand_data:
                    brand_data[brand] = {'sku_prices': [], 'unit_prices': []}
                
                if sku_price > 0:
                    brand_data[brand]['sku_prices'].append(float(sku_price))
                if unit_price > 0:
                    brand_data[brand]['unit_prices'].append(float(unit_price))
            
            brands = []
            for brand_name, prices in brand_data.items():
                brands.append({
                    'name': brand_name,
                    'skuPrices': prices['sku_prices'],
                    'unitPrices': prices['unit_prices']
                })
            
            return {
                'category': category_name,
                'brands': brands
            }
        
        # 生成真实的segment-based价格分布数据
        price_distributions = []
        brand_price_distributions = []
        
        for category_name, total_revenue, products in main_categories:
            if products:
                price_distributions.append(get_price_distribution(products, category_name))
                brand_price_distributions.append(get_brand_price_distribution(products, category_name))
        
        # 生成segmentNames和segmentColors
        category_names = [category_name for category_name, _, _ in main_categories]
        
        # 定义颜色配色方案 - 与其他服务保持一致
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#F7B731", 
            "#A55EEA", "#26de81", "#FD79A8", "#2ECC71", "#E74C3C",
            "#3498DB", "#9B59B6", "#F39C12", "#1ABC9C", "#E67E22"
        ]
        category_colors = colors[:len(category_names)]
        
        return {
            'priceDistribution': price_distributions,
            'brandPriceDistribution': brand_price_distributions,
            'categoryNames': category_names,
            'categoryColors': category_colors,
            'totalProducts': sum(len(products) for _, _, products in main_categories)
        }
    
    def _format_combined_pricing_response(self, categorized_products: Dict[str, List[Dict[str, Any]]], 
                                        smart_categorized_products: Dict[str, List[Dict[str, Any]]], 
                                        categories: List[str]) -> Dict[str, Any]:
        """格式化合并的定价响应数据，包含category和smart维度"""
        import statistics
        
        # 复用原有的统计计算函数
        def calculate_price_stats(prices: List[float]) -> Dict[str, float]:
            """计算价格统计信息"""
            if not prices:
                return {
                    'min': 0, 'q1': 0, 'median': 0, 
                    'mean': 0, 'q3': 0, 'max': 0
                }
            
            sorted_prices = sorted(prices)
            n = len(sorted_prices)
            
            return {
                'min': float(sorted_prices[0]),
                'q1': float(sorted_prices[n//4]) if n > 3 else float(sorted_prices[0]),
                'median': float(statistics.median(sorted_prices)),
                'mean': float(statistics.mean(sorted_prices)),
                'q3': float(sorted_prices[3*n//4]) if n > 3 else float(sorted_prices[-1]),
                'max': float(sorted_prices[-1])
            }
        
        def get_price_distribution(products: List[Dict[str, Any]], segment_name: str) -> Dict[str, Any]:
            """获取价格分布数据"""
            sku_prices = []
            unit_prices = []
            
            for product in products:
                sku_price = product.get('price_usd', 0) or 0
                unit_price = product.get('unit_price_calculated', 0) or 0
                
                if sku_price > 0:
                    sku_prices.append(float(sku_price))
                if unit_price > 0:
                    unit_prices.append(float(unit_price))
            
            return {
                'category': segment_name,
                'skuPrices': sku_prices,
                'unitPrices': unit_prices,
                'productCount': len(products),
                'stats': {
                    'sku': calculate_price_stats(sku_prices),
                    'unit': calculate_price_stats(unit_prices)
                }
            }
        
        # 合并所有产品数据到一个列表中
        all_distributions = []
        all_segment_names = []
        
        # 按收入排序categories
        if categorized_products:
            category_revenue_list = []
            for category, products in categorized_products.items():
                if products:  # 只包含有产品的segments
                    total_revenue = sum(float(p.get('price_usd', 0) or 0) for p in products)
                    category_revenue_list.append((category, total_revenue, products))
            
            category_revenue_list.sort(key=lambda x: x[1], reverse=True)
            
            # 添加category数据到分布列表
            for category_name, total_revenue, products in category_revenue_list:
                if products:
                    all_distributions.append(get_price_distribution(products, category_name))
                    all_segment_names.append(category_name)
        
        # 添加smart capability数据到分布列表
        smart_order = ['Smart', 'Non-Smart']  # 固定顺序
        for smart_type in smart_order:
            products = smart_categorized_products.get(smart_type, [])
            if products:  # 只包含有产品的smart类型
                all_distributions.append(get_price_distribution(products, smart_type))
                all_segment_names.append(smart_type)
        
        # 生成品牌价格分布数据（保持原有逻辑，但合并所有维度）
        all_brand_price_distributions = []
        
        # Category维度的品牌分布
        for category_name, _, products in (category_revenue_list if categorized_products else []):
            if products:
                all_brand_price_distributions.append(self._get_brand_price_distribution(products, category_name))
        
        # Smart维度的品牌分布
        for smart_type in smart_order:
            products = smart_categorized_products.get(smart_type, [])
            if products:
                all_brand_price_distributions.append(self._get_brand_price_distribution(products, smart_type))
        
        # 生成颜色配色方案
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#F7B731", 
            "#A55EEA", "#26de81", "#FD79A8", "#2ECC71", "#E74C3C",
            "#3498DB", "#9B59B6", "#F39C12", "#1ABC9C", "#E67E22"
        ]
        segment_colors = colors[:len(all_segment_names)]
        
        total_products = sum(len(item['skuPrices']) for item in all_distributions)
        
        return {
            'priceDistribution': all_distributions,
            'brandPriceDistribution': all_brand_price_distributions,
            'categoryNames': all_segment_names,
            'categoryColors': segment_colors,
            'totalProducts': total_products
        }
    
    def _get_brand_price_distribution(self, products: List[Dict[str, Any]], segment_name: str) -> Dict[str, Any]:
        """获取品牌价格分布数据"""
        brand_data = {}
        
        for product in products:
            brand = product.get('brand', 'Unknown')
            sku_price = product.get('price_usd', 0) or 0
            unit_price = product.get('unit_price_calculated', 0) or 0
            
            if brand not in brand_data:
                brand_data[brand] = {'sku_prices': [], 'unit_prices': []}
            
            if sku_price > 0:
                brand_data[brand]['sku_prices'].append(float(sku_price))
            if unit_price > 0:
                brand_data[brand]['unit_prices'].append(float(unit_price))
        
        brands = []
        for brand_name, prices in brand_data.items():
            brands.append({
                'name': brand_name,
                'skuPrices': prices['sku_prices'],
                'unitPrices': prices['unit_prices']
            })
        
        return {
            'category': segment_name,
            'brands': brands
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空的响应格式"""
        return {
            'priceDistribution': [],
            'brandPriceDistribution': [],
            'categoryNames': [],
            'categoryColors': [],
            'totalProducts': 0
        } 