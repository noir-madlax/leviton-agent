"""Brand analysis service for dashboard."""

import logging
from typing import List, Dict, Any
from collections import defaultdict

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class BrandAnalysisService(BaseDashboardService):
    """Service for brand analysis data.
    
    按类别分析品牌收入数据，支持Brand Revenue by Category图表。
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get brand analysis data grouped by category."""
        try:
            # 查询品牌数据
            query = self._get_base_product_table().select('''
                platform_id,
                brand,
                category,
                estimated_revenue,
                monthly_sales_volume
            ''')
            
            # Apply filters
            query = self._apply_base_filters(query)
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            if not result.data:
                logger.warning(f"No brand data found for project {self.project_id}")
                return self._get_empty_response()
            
            # 获取项目中存在的categories
            project_categories = self._get_project_categories(result.data)
            
            if not project_categories:
                logger.warning(f"No categories found for project {self.project_id}")
                return self._get_empty_response()
            
            logger.info(f"📊 Processing {len(project_categories)} categories: {project_categories}")
            
            # 按品牌和category聚合数据
            brand_category_data = self._aggregate_brand_data(result.data, project_categories)
            
            # 格式化响应
            response = self._format_brand_response(brand_category_data, project_categories)
            
            logger.info(f"📈 Brand analysis completed: {len(brand_category_data)} brands processed")
            return response
            
        except Exception as e:
            logger.error(f"Error in brand analysis for project {self.project_id}: {e}")
            raise
    
    def _get_project_categories(self, products: List[Dict[str, Any]]) -> List[str]:
        """获取项目中存在的所有categories"""
        categories = set()
        logger.info(f"🔍 Analyzing {len(products)} products for categories...")
        
        for i, product in enumerate(products):
            category = product.get('category')
            if i < 5:  # Debug first 5 products only
                logger.info(f"  Product {i+1}: {product.get('brand', 'Unknown')} - category: '{category}'")
            if category and category.strip():
                categories.add(category.strip())
        
        logger.info(f"📊 Found categories: {sorted(list(categories))}")
        # 按字母顺序排序
        return sorted(list(categories))
    
    def _aggregate_brand_data(self, products: List[Dict[str, Any]], 
                            project_categories: List[str]) -> Dict[str, Dict[str, Any]]:
        """按品牌和category聚合数据"""
        
        brand_data = defaultdict(lambda: {category: {'revenue': 0, 'volume': 0, 'product_count': 0} for category in project_categories})
        
        for product in products:
            brand = product.get('brand')
            category = product.get('category')
            
            if not brand or not category:
                continue
            
            category = category.strip()
            if category not in project_categories:
                continue
            
            # 聚合数据
            brand_data[brand][category]['revenue'] += product.get('estimated_revenue', 0) or 0
            brand_data[brand][category]['volume'] += product.get('monthly_sales_volume', 0) or 0
            brand_data[brand][category]['product_count'] += 1  # 每个产品（ASIN）计数加1
        
        return dict(brand_data)
    
    def _format_brand_response(self, brand_data: Dict[str, Dict[str, Any]], 
                             project_categories: List[str]) -> Dict[str, Any]:
        """格式化品牌分析响应数据
        
        新格式支持category分组，限制返回Top 10品牌：
        {
            "brandCategoryRevenue": [
                {
                    "brand": "Leviton",
                    "categories": {
                        "Dimmer Switches": {"revenue": 1500000, "volume": 2000},
                        "Light Switches": {"revenue": 500000, "volume": 500}
                    },
                    "dimmerRevenue": 1500000,  # 为了向后兼容，映射到最大的category
                    "switchRevenue": 500000,   # 映射到第二大的category
                    "dimmerVolume": 2000,
                    "switchVolume": 500
                }
            ],
            "categoryNames": ["Dimmer Switches", "Light Switches"],
            "categoryColors": ["#FF6B6B", "#4ECDC4"]
        }
        """
        
        # 定义颜色配色方案 - 为category使用更合适的颜色
        colors = [
            "#FF6B6B",  # 红色 - Dimmer Switches
            "#4ECDC4",  # 青色 - Light Switches  
            "#45B7D1",  # 蓝色
            "#96CEB4",  # 绿色
            "#F7B731",  # 黄色
            "#A55EEA",  # 紫色
            "#26de81",  # 薄荷绿
            "#FD79A8",  # 粉色
            "#2ECC71",  # 翠绿
            "#E74C3C"   # 深红
        ]
        
        formatted_brands = []
        
        for brand, categories in brand_data.items():
            # 计算每个category的总收入、销量和产品数量
            category_totals = []
            for category in project_categories:
                category_data = categories.get(category, {'revenue': 0, 'volume': 0, 'product_count': 0})
                category_totals.append({
                    'category': category,
                    'revenue': category_data['revenue'],
                    'volume': category_data['volume'],
                    'product_count': category_data['product_count']
                })
            
            # 按收入排序
            category_totals.sort(key=lambda x: x['revenue'], reverse=True)
            
            # 为了向后兼容，将前两个category映射到dimmer/switch字段
            dimmer_data = category_totals[0] if len(category_totals) > 0 else {'revenue': 0, 'volume': 0, 'product_count': 0}
            switch_data = category_totals[1] if len(category_totals) > 1 else {'revenue': 0, 'volume': 0, 'product_count': 0}
            
            brand_entry = {
                'brand': brand,
                'categories': {item['category']: {'revenue': item['revenue'], 'volume': item['volume'], 'product_count': item['product_count']} 
                             for item in category_totals},
                'dimmerRevenue': dimmer_data['revenue'],
                'switchRevenue': switch_data['revenue'],
                'dimmerVolume': dimmer_data['volume'],
                'switchVolume': switch_data['volume']
            }
            
            formatted_brands.append(brand_entry)
        
        # 按总收入排序
        formatted_brands.sort(key=lambda x: x['dimmerRevenue'] + x['switchRevenue'], reverse=True)
        
        # 🔄 UPDATED: 返回所有品牌，不再限制为Top 10
        # top_10_brands = formatted_brands[:10]  # 移除这行限制
        
        logger.info(f"📈 Brand analysis: returning all {len(formatted_brands)} brands")
        
        return {
            'brandCategoryRevenue': formatted_brands,  # 返回所有品牌
            'categoryNames': project_categories,
            'categoryColors': colors[:len(project_categories)]
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空的响应格式"""
        return {
            'brandCategoryRevenue': [],
            'categoryNames': [],
            'categoryColors': []
        } 