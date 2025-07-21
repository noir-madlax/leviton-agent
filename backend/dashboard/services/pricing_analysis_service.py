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
            
            # 先应用基础的 project ASINs 过滤
            query = self._apply_base_filters(query)
            
            # 注意：这里不应用 _apply_combined_filters，因为我们需要基于所有产品创建组合，然后再根据前端的 filters 筛选这些组合
            
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
            
            # 使用交叉组合分类产品 - 按category和smart_capability组合
            all_combination_categorized_products = self._categorize_products_by_category_smart_combination(products_with_price)
            
            # 根据前端传递的 filters 筛选这些组合
            filtered_combinations = self._filter_combinations_by_request(all_combination_categorized_products)
            
            # 格式化响应 - 使用筛选后的组合数据
            response = self._format_combination_pricing_response(filtered_combinations)
            
            logger.info(f"📈 Pricing analysis completed with {len(filtered_combinations)} filtered category-smart combinations")
            return response
            
        except Exception as e:
            logger.error(f"Error in pricing analysis for project {self.project_id}: {e}")
            raise
    
    def _categorize_products_by_category_smart_combination(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将产品按category和smart_capability的交叉组合分类"""
        try:
            # 获取项目的智能属性数据
            smart_capability_data = self._get_smart_capability_data()
            
            # 创建ASIN到智能属性的映射
            asin_to_smart = {}
            for data_row in smart_capability_data:
                asin = data_row.get('asins')
                extend_data = data_row.get('extend', {})
                smart_capability = extend_data.get('smart_capability')
                if asin and smart_capability in ['Smart', 'Non-Smart']:
                    asin_to_smart[asin] = smart_capability
            
            # 创建交叉组合分类
            categorized = {}
            for product in products:
                category = product.get('category')
                platform_id = product.get('platform_id')
                smart_capability = asin_to_smart.get(platform_id, 'Unknown')
                
                if category and smart_capability in ['Smart', 'Non-Smart']:
                    # 创建组合键: "Dimmer Switches + Smart"
                    combination_key = f"{category} + {smart_capability}"
                    if combination_key not in categorized:
                        categorized[combination_key] = []
                    categorized[combination_key].append(product)
            
            logger.info(f"📊 Category-Smart combination categorization: {[(k, len(v)) for k, v in categorized.items()]}")
            return categorized
            
        except Exception as e:
            logger.error(f"Error categorizing products by category-smart combination: {e}")
            return {}
    
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
    
    def _filter_combinations_by_request(self, all_combinations: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """根据前端传递的 filters 筛选已经生成的组合"""
        
        # 从 self.filters 获取前端选择的条件
        selected_categories = self.filters.categories
        selected_extend_fields = self.filters.extend_fields or {}
        smart_filter = selected_extend_fields.get('smart_capability')
        
        # 如果没有任何筛选条件，返回所有组合
        if not selected_categories and not smart_filter:
            return all_combinations
            
        filtered_results = {}
        
        logger.info(f"Applying filters - Categories: {selected_categories}, Smart Capability: {smart_filter}")
        
        # 遍历所有组合，检查是否匹配筛选条件
        for combination_name, products in all_combinations.items():
            should_include = True
            
            # 解析组合名称: "Light Switches + Smart" -> ["Light Switches", "Smart"]
            parts = combination_name.split(' + ')
            if len(parts) != 2:
                continue  # 跳过格式不正确的组合名称
                
            combo_category = parts[0].strip()
            combo_smart_capability = parts[1].strip()
            
            # 检查 category 筛选条件
            if selected_categories:
                if combo_category not in selected_categories:
                    should_include = False
            
            # 检查 smart_capability 筛选条件
            if smart_filter:
                if combo_smart_capability != smart_filter:
                    should_include = False
            
            # 如果同时满足所有条件，包含这个组合
            if should_include:
                filtered_results[combination_name] = products
                logger.info(f"Including combination: {combination_name} with {len(products)} products")
        
        logger.info(f"Filtered combinations: {len(filtered_results)} out of {len(all_combinations)} combinations match filters")
        return filtered_results
    
    def _format_combination_pricing_response(self, combination_categorized_products: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """格式化交叉组合的定价响应数据"""
        import statistics
        
        if not combination_categorized_products:
            return self._get_empty_response()
        
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
        
        def get_price_distribution(products: List[Dict[str, Any]], combination_name: str) -> Dict[str, Any]:
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
                'category': combination_name,
                'skuPrices': sku_prices,
                'unitPrices': unit_prices,
                'productCount': len(products),
                'stats': {
                    'sku': calculate_price_stats(sku_prices),
                    'unit': calculate_price_stats(unit_prices)
                }
            }
        
        # 按收入排序组合
        combination_revenue_list = []
        for combination_name, products in combination_categorized_products.items():
            if products:  # 只包含有产品的组合
                total_revenue = sum(float(p.get('price_usd', 0) or 0) for p in products)
                combination_revenue_list.append((combination_name, total_revenue, products))
        
        combination_revenue_list.sort(key=lambda x: x[1], reverse=True)
        
        # 生成价格分布数据
        all_distributions = []
        all_segment_names = []
        
        for combination_name, total_revenue, products in combination_revenue_list:
            if products:
                all_distributions.append(get_price_distribution(products, combination_name))
                all_segment_names.append(combination_name)
        
        # 生成品牌价格分布数据
        all_brand_price_distributions = []
        for combination_name, _, products in combination_revenue_list:
            if products:
                all_brand_price_distributions.append(self._get_brand_price_distribution(products, combination_name))
        
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