"""Package preference service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class PackagePreferenceService(BaseDashboardService):
    """Service for package preference data.
    
    Replaces frontend getPackagePreferenceData() method with server-side
    implementation that applies project ASIN filtering.
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get package preference data with ASIN filtering.
        
        Returns data in the exact same format as frontend getPackagePreferenceData()
        to ensure compatibility with existing UI components.
        """
        try:
            # Build query - replicate frontend logic exactly
            query = self._get_base_product_table().select('''
                platform_id,
                title,
                brand,
                price_usd,
                unit_price_calculated,
                monthly_sales_volume,
                estimated_revenue,
                category,
                pack_count
            ''')
            
            # Apply base filters
            query = self._apply_base_filters(query)
            
            # 🔑 CRITICAL: Apply ASIN filtering to prevent data leakage
            query = self._apply_asin_filter(query)
            
            # Execute query
            result = query.execute()
            
            logger.info(f"🔍 Package preference query returned {len(result.data) if result.data else 0} products for project {self.project_id}")
            
            if not result.data:
                logger.warning(f"No package preference data found for project {self.project_id}")
                return {
                    'sameProductComparison': [],
                    'packageDistribution': [],
                    'dimmerSwitches': [],
                    'lightSwitches': []
                }
            
            # 生成包装大小标签 - replicate frontend getPackSizeLabel exactly
            def get_pack_size_label(pack_count):
                if pack_count == 1:
                    return 'Single Pack'
                elif pack_count == 2:
                    return '2 Pack'
                elif pack_count == 3:
                    return '3 Pack'
                elif pack_count == 4:
                    return '4 Pack'
                elif pack_count == 5:
                    return '5 Pack'
                elif 6 <= pack_count <= 10:
                    return '6-10 Pack'
                else:
                    return '10+ Pack'
            
            # 准备数据 - replicate frontend mapping exactly
            products = []
            for item in result.data:
                pack_count = item.get('pack_count')
                if pack_count is None:
                    continue
                    
                product = {
                    'productName': item.get('title'),
                    'packSize': get_pack_size_label(pack_count),
                    'packCount': pack_count,
                    'salesVolume': item.get('monthly_sales_volume', 0) or 0,
                    'price': item.get('price_usd'),
                    'unitPrice': item.get('unit_price_calculated') or item.get('price_usd'),
                    'category': item.get('category'),
                    'revenue': item.get('estimated_revenue', 0) or 0
                }
                products.append(product)
            
            logger.info(f"📊 Processed {len(products)} products with pack count data")
            
            # 按类别分组 - replicate frontend logic exactly
            dimmer_products = [p for p in products if p['category'] == 'Dimmer Switches']
            switch_products = [p for p in products if p['category'] == 'Light Switches']
            
            logger.info(f"📈 Categorized: {len(dimmer_products)} dimmers, {len(switch_products)} switches")
            
            # 计算包装分布的辅助函数 - replicate frontend calculatePackageDistribution exactly
            def calculate_package_distribution(products_list):
                pack_size_map = {}
                
                for product in products_list:
                    pack_size = product['packSize']
                    if pack_size not in pack_size_map:
                        pack_size_map[pack_size] = {
                            'packSize': pack_size,
                            'count': 0,
                            'salesVolume': 0,
                            'salesRevenue': 0
                        }
                    
                    pack_size_map[pack_size]['count'] += 1
                    pack_size_map[pack_size]['salesVolume'] += product['salesVolume']
                    pack_size_map[pack_size]['salesRevenue'] += product['revenue']
                
                total = len(products_list)
                result_list = []
                for item in pack_size_map.values():
                    result_item = dict(item)
                    result_item['percentage'] = (item['count'] / total * 100) if total > 0 else 0
                    result_list.append(result_item)
                
                return result_list
            
            # 计算各类别的包装分布
            dimmer_package_distribution = calculate_package_distribution(dimmer_products)
            switch_package_distribution = calculate_package_distribution(switch_products)
            overall_package_distribution = calculate_package_distribution(products)
            
            # 同产品比较数据 - replicate frontend logic exactly (选择前10个产品)
            same_product_comparison = []
            for product in products[:10]:
                same_product_comparison.append({
                    'productName': product['productName'],
                    'packSize': product['packSize'],
                    'packCount': product['packCount'],
                    'salesVolume': product['salesVolume'],
                    'price': product['price'],
                    'unitPrice': product['unitPrice']
                })
            
            logger.info(f"📦 Package analysis completed: {len(overall_package_distribution)} overall pack sizes, {len(same_product_comparison)} sample products")
            
            return {
                'sameProductComparison': same_product_comparison,
                'packageDistribution': overall_package_distribution,
                'dimmerSwitches': dimmer_package_distribution,
                'lightSwitches': switch_package_distribution
            }
            
        except Exception as e:
            logger.error(f"Error in package preference analysis for project {self.project_id}: {e}")
            raise 