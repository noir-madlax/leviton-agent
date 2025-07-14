"""Product analysis service for dashboard."""

import logging
from typing import List, Dict, Any
from collections import defaultdict

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class ProductAnalysisService(BaseDashboardService):
    """Service for product analysis data.
    
    通用化版本：动态处理项目的所有segment类型，支持任意数量的segments。
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get product analysis data with dynamic segment support."""
        try:
            # 获取项目segments
            project_segments = self.get_project_segments()
            
            if not project_segments:
                logger.warning(f"No segments found for project {self.project_id}")
                return self._get_empty_response()
            
            logger.info(f"📊 Processing {len(project_segments)} segments: {project_segments}")
            
            # 查询产品数据
            query = self._get_base_product_table().select('''
                platform_id,
                title,
                brand,
                category,
                price_usd,
                estimated_revenue,
                monthly_sales_volume
            ''')
            
            # Apply filters
            query = self._apply_base_filters(query)
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            if not result.data:
                logger.warning(f"No product data found for project {self.project_id}")
                return self._get_empty_response()
            
            # 获取segment assignments
            segment_assignments = self._get_segment_assignments()
            
            # 按segment聚合和排序产品
            segment_products = self._categorize_and_rank_products(result.data, segment_assignments, project_segments)
            
            # 格式化响应
            response = self._format_product_response(segment_products, project_segments)
            
            logger.info(f"📈 Product analysis completed: {len(segment_products)} segments processed")
            return response
            
        except Exception as e:
            logger.error(f"Error in product analysis for project {self.project_id}: {e}")
            raise
    
    def _get_segment_assignments(self) -> Dict[str, str]:
        """获取segment分配（platform_id到segment_name的映射）"""
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
    
    def _categorize_and_rank_products(self, products: List[Dict[str, Any]], 
                                    segment_assignments: Dict[str, str], 
                                    project_segments: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """按segment分类产品并排序"""
        
        segment_products = {segment: [] for segment in project_segments}
        
        for product in products:
            platform_id = product.get('platform_id')
            segment = segment_assignments.get(platform_id)
            
            if not segment or segment not in project_segments:
                continue
            
            # 格式化产品数据
            formatted_product = {
                'title': product.get('title', 'Unknown Product'),
                'brand': product.get('brand', 'Unknown Brand'),
                'category': product.get('category', 'Unknown Category'),
                'price': product.get('price_usd', 0) or 0,
                'revenue': product.get('estimated_revenue', 0) or 0,
                'volume': product.get('monthly_sales_volume', 0) or 0,
                'platform_id': platform_id,
                'segment': segment
            }
            
            segment_products[segment].append(formatted_product)
        
        # 每个segment内按收入排序
        for segment in segment_products:
            segment_products[segment].sort(key=lambda x: x['revenue'], reverse=True)
        
        return segment_products
    
    def _format_product_response(self, segment_products: Dict[str, List[Dict[str, Any]]], 
                               project_segments: List[str]) -> Dict[str, Any]:
        """格式化产品分析响应数据
        
        增强版本：返回前端期望的完整格式，包括segmentSummary, segmentNames, segmentColors等。
        """
        
        # 准备统一的产品数据格式
        price_vs_revenue = []
        segments_dict = {}
        segment_summary = {}
        
        # 按收入排序segments，确保最重要的segment在前面
        segment_revenue_list = []
        for segment in project_segments:
            products = segment_products.get(segment, [])
            total_revenue = sum(p['revenue'] for p in products) if products else 0
            segment_revenue_list.append((segment, total_revenue, products))
        
        # 按收入排序
        segment_revenue_list.sort(key=lambda x: x[1], reverse=True)
        
        for segment, total_revenue, products in segment_revenue_list:
            if not products:
                # 即使没有产品，也要为segment创建空的summary
                segment_summary[segment] = {
                    'totalRevenue': 0,
                    'totalVolume': 0,
                    'productCount': 0,
                    'avgPrice': 0,
                    'topBrand': 'N/A'
                }
                segments_dict[segment] = []
                continue
                
            # 格式化产品数据为API期望的格式
            formatted_products = []
            for product in products[:10]:  # 每个类别最多10个产品
                formatted_product = {
                    'id': product.get('platform_id', ''),
                    'name': product.get('title', 'Unknown Product'),
                    'brand': product.get('brand', 'Unknown Brand'),
                    'price': product.get('price', 0),
                    'unitPrice': product.get('price', 0),  # 简化处理，使用相同值
                    'revenue': product.get('revenue', 0),
                    'volume': product.get('volume', 0),
                    'url': f"https://amazon.com/dp/{product.get('platform_id', '')}"
                }
                formatted_products.append(formatted_product)
            
            # 构建price vs revenue数据
            category_data = {
                'category': segment,
                'products': formatted_products
            }
            price_vs_revenue.append(category_data)
            
            # 构建segments字典
            segments_dict[segment] = formatted_products
            
            # 计算segment summary
            total_volume = sum(p['volume'] for p in products)
            avg_price = sum(p['price'] for p in products) / len(products) if products else 0
            
            # 找到该segment的top brand
            brand_counts = {}
            for p in products:
                brand = p.get('brand', 'Unknown')
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            top_brand = max(brand_counts.items(), key=lambda x: x[1])[0] if brand_counts else 'N/A'
            
            segment_summary[segment] = {
                'totalRevenue': total_revenue,
                'totalVolume': total_volume,
                'productCount': len(products),
                'avgPrice': avg_price,
                'topBrand': top_brand
            }
        
        # 获取排序后的segment names（按收入从高到低）
        sorted_segment_names = [segment for segment, _, _ in segment_revenue_list]
        
        # 生成segment colors - 增加到15个颜色
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#F7B731", 
            "#A55EEA", "#26de81", "#FD79A8", "#2ECC71", "#E74C3C",
            "#3498DB", "#9B59B6", "#F39C12", "#1ABC9C", "#E67E22"
        ]
        segment_colors = colors[:len(sorted_segment_names)]
        
        return {
            'priceVsRevenue': price_vs_revenue,
            'topProducts': {
                'segments': segments_dict,
                'dimmerSwitches': segments_dict.get('Dimmer Switches', []),  # Legacy compatibility
                'lightSwitches': segments_dict.get('Light Switches', [])     # Legacy compatibility
            },
            'segmentSummary': segment_summary,
            'segmentNames': sorted_segment_names,  # 使用排序后的segment names
            'segmentColors': segment_colors,
            'totalProducts': sum(len(products) for products in segments_dict.values())
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空的响应格式"""
        return {
            'priceVsRevenue': [],
            'topProducts': {
                'segments': {},
                'dimmerSwitches': [],
                'lightSwitches': []
            },
            'segmentSummary': {},
            'segmentNames': [],
            'segmentColors': [],
            'totalProducts': 0
        } 