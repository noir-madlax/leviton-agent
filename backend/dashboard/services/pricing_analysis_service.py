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
        """Get pricing analysis data with dynamic segment support."""
        try:
            # 获取项目segments
            project_segments = self.get_project_segments()
            
            if not project_segments:
                logger.warning(f"No segments found for project {self.project_id}")
                return self._get_empty_response()
            
            # 查询定价数据
            query = self._get_base_product_table().select('''
                platform_id,
                title,
                brand,
                price_usd,
                unit_price_calculated
            ''')
            
            # Apply filters
            query = self._apply_base_filters(query)
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            if not result.data:
                logger.warning(f"No pricing analysis data found for project {self.project_id}")
                return self._get_empty_response()
            
            # 过滤有价格数据的产品
            products_with_price = [item for item in result.data if item.get('price_usd')]
            logger.info(f"📊 Found {len(products_with_price)} products with pricing data")
            
            # 获取segment assignments
            segment_assignments = self._get_segment_assignments()
            
            # 分类产品
            categorized_products = self._categorize_products(products_with_price, segment_assignments)
            
            # 格式化响应
            response = self._format_pricing_response(categorized_products, project_segments)
            
            logger.info(f"📈 Pricing analysis completed")
            return response
            
        except Exception as e:
            logger.error(f"Error in pricing analysis for project {self.project_id}: {e}")
            raise
    
    def _get_segment_assignments(self) -> Dict[str, str]:
        """获取segment分配（复用逻辑）"""
        try:
            if not self.project_asins:
                return {}
            
            # 查询ASINs在product_wide_table中的记录
            wide_table_result = self.supabase.table('product_wide_table')\
                .select('id, platform_id')\
                .in_('platform_id', self.project_asins)\
                .execute()
            
            if not wide_table_result.data:
                return {}
            
            # 建立映射
            platform_to_wide_id = {item['platform_id']: item['id'] for item in wide_table_result.data}
            
            # 查询segment assignments
            wide_table_ids = list(platform_to_wide_id.values())
            assignments_result = self.supabase.table('product_segment_assignments')\
                .select('product_id, segment_name')\
                .eq('project_id', self.project_id)\
                .in_('product_id', wide_table_ids)\
                .neq('segment_name', None)\
                .neq('segment_name', 'OUT_OF_SCOPE')\
                .execute()
            
            if not assignments_result.data:
                return {}
            
            # 建立映射
            wide_id_to_segment = {item['product_id']: item['segment_name'] for item in assignments_result.data}
            
            # 转换为platform_id到segment的映射
            platform_to_segment = {}
            for platform_id, wide_id in platform_to_wide_id.items():
                if wide_id in wide_id_to_segment:
                    platform_to_segment[platform_id] = wide_id_to_segment[wide_id]
            
            return platform_to_segment
            
        except Exception as e:
            logger.error(f"Error getting segment assignments: {e}")
            return {}
    
    def _categorize_products(self, products: List[Dict[str, Any]], segment_assignments: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """将产品按segment分类"""
        project_segments = self.get_project_segments()
        categorized = {segment: [] for segment in project_segments}
        
        for product in products:
            platform_id = product.get('platform_id')
            segment = segment_assignments.get(platform_id)
            
            if segment and segment in categorized:
                categorized[segment].append(product)
        
        return categorized
    
    def _format_pricing_response(self, categorized_products: Dict[str, List[Dict[str, Any]]], project_segments: List[str]) -> Dict[str, Any]:
        """格式化定价响应数据，返回真实的segment-based格式"""
        import statistics
        
        if not categorized_products:
            return self._get_empty_response()
        
        # 按收入排序segments
        segment_revenue_list = []
        for segment, products in categorized_products.items():
            if products:  # 只包含有产品的segments
                total_revenue = sum(float(p.get('price_usd', 0) or 0) for p in products)
                segment_revenue_list.append((segment, total_revenue, products))
        
        segment_revenue_list.sort(key=lambda x: x[1], reverse=True)
        
        # 显示所有有数据的segments，不限制数量
        main_segments = segment_revenue_list
        
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
        
        for segment_name, total_revenue, products in main_segments:
            if products:
                price_distributions.append(get_price_distribution(products, segment_name))
                brand_price_distributions.append(get_brand_price_distribution(products, segment_name))
        
        return {
            'priceDistribution': price_distributions,
            'brandPriceDistribution': brand_price_distributions
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空的响应格式"""
        return {
            'priceDistribution': [],
            'brandPriceDistribution': []
        } 