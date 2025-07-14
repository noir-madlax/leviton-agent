"""Package preference service for dashboard."""

import logging
from typing import List, Dict, Any

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class PackagePreferenceService(BaseDashboardService):
    """Service for package preference data.
    
    通用化版本：动态处理项目的所有segment类型。
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get package preference data with dynamic segment support."""
        try:
            # 获取项目segments
            project_segments = self.get_project_segments()
            
            if not project_segments:
                logger.warning(f"No segments found for project {self.project_id}")
                return self._get_empty_response()
            
            # 查询包装数据
            query = self._get_base_product_table().select('''
                platform_id,
                title,
                pack_count,
                monthly_sales_volume,
                price_usd,
                unit_price_calculated,
                estimated_revenue
            ''')
            
            # Apply filters
            query = self._apply_base_filters(query)
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            if not result.data:
                logger.warning(f"No package preference data found for project {self.project_id}")
                return self._get_empty_response()
            
            # 过滤有包装数据的产品
            products_with_pack = [item for item in result.data if item.get('pack_count') is not None]
            logger.info(f"📊 Found {len(products_with_pack)} products with pack count data")
            
            # 获取segment assignments
            segment_assignments = self._get_segment_assignments()
            
            # 分类和聚合数据
            package_data = self._aggregate_package_data(products_with_pack, segment_assignments)
            
            # 格式化响应
            response = self._format_package_response(package_data)
            
            logger.info(f"📈 Package preference analysis completed")
            return response
            
        except Exception as e:
            logger.error(f"Error in package preference analysis for project {self.project_id}: {e}")
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
    
    def _aggregate_package_data(self, products: List[Dict[str, Any]], segment_assignments: Dict[str, str]) -> List[Dict[str, Any]]:
        """按包装规格聚合数据"""
        
        def get_pack_size_label(pack_count):
            """根据pack_count生成包装规格标签"""
            if pack_count == 1:
                return "Single"
            elif pack_count == 2:
                return "Pack of 2"
            elif pack_count == 3:
                return "Pack of 3"
            elif 4 <= pack_count <= 5:
                return f"Pack of {pack_count}"
            elif 6 <= pack_count <= 10:
                return "Medium Pack (6-10)"
            elif 11 <= pack_count <= 20:
                return "Large Pack (11-20)"
            else:
                return "Bulk Pack (20+)"
        
        # 按pack_count和segment聚合
        pack_data = {}
        
        for item in products:
            platform_id = item.get('platform_id')
            pack_count = item.get('pack_count')
            
            if pack_count is None:
                continue
            
            pack_size = get_pack_size_label(pack_count)
            segment = segment_assignments.get(platform_id, 'Unknown')
            
            # 创建唯一的key，包含segment信息以区分不同segment下的相同包装规格
            pack_key = f"{pack_size}_{segment}"
            
            if pack_key not in pack_data:
                pack_data[pack_key] = {
                    'packSize': pack_size,
                    'packCount': pack_count,
                    'salesVolume': 0,
                    'salesRevenue': 0,
                    'count': 0,
                    'segment': segment,
                    'actualPackCount': pack_count  # 保存实际的pack_count用于比较
                }
            
            # 聚合数据
            pack_data[pack_key]['salesVolume'] += item.get('monthly_sales_volume', 0) or 0
            pack_data[pack_key]['salesRevenue'] += item.get('estimated_revenue', 0) or 0
            pack_data[pack_key]['count'] += 1
        
        # 转为列表并排序
        result = list(pack_data.values())
        
        # 按销售收入排序
        result.sort(key=lambda x: x['salesRevenue'], reverse=True)
        
        # 计算百分比
        total_count = sum(item['count'] for item in result)
        total_revenue = sum(item['salesRevenue'] for item in result)
        
        for item in result:
            item['percentage'] = (item['count'] / total_count * 100) if total_count > 0 else 0
            item['revenuePercentage'] = (item['salesRevenue'] / total_revenue * 100) if total_revenue > 0 else 0
        
        return result
    
    def _format_package_response(self, package_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化包装偏好响应数据，按segment分开显示"""
        
        if not package_data:
            return self._get_empty_response()
        
        # 按segment分组包装数据
        segment_packages = {}
        project_segments = self.get_project_segments()
        
        for item in package_data:
            segment = item['segment']
            if segment not in segment_packages:
                segment_packages[segment] = []
            segment_packages[segment].append(item)
        
        # 为每个segment计算包装分布
        segment_distributions = {}
        for segment in project_segments:
            if segment in segment_packages:
                items = segment_packages[segment]
                
                # 按packSize合并相同的包装类型
                pack_by_size = {}
                for item in items:
                    pack_size = item['packSize']
                    if pack_size not in pack_by_size:
                        pack_by_size[pack_size] = {
                            'packSize': pack_size,
                            'count': 0,
                            'salesVolume': 0,
                            'salesRevenue': 0,
                            'actualPackCount': item['actualPackCount']
                        }
                    
                    pack_by_size[pack_size]['count'] += item['count']
                    pack_by_size[pack_size]['salesVolume'] += item['salesVolume']
                    pack_by_size[pack_size]['salesRevenue'] += item['salesRevenue']
                
                # 计算百分比
                pack_list = list(pack_by_size.values())
                total_count = sum(p['count'] for p in pack_list)
                total_revenue = sum(p['salesRevenue'] for p in pack_list)
                
                for pack in pack_list:
                    pack['percentage'] = (pack['count'] / total_count * 100) if total_count > 0 else 0
                    pack['revenuePercentage'] = (pack['salesRevenue'] / total_revenue * 100) if total_revenue > 0 else 0
                
                # 按收入排序
                pack_list.sort(key=lambda x: x['salesRevenue'], reverse=True)
                segment_distributions[segment] = pack_list
            else:
                segment_distributions[segment] = []
        
        # 生成同产品比较数据
        same_product_comparison = []
        for i, item in enumerate(package_data[:10]):
            same_product_comparison.append({
                'productName': f"Product {i+1} ({item['segment']})",
                'packSize': item['packSize'],
                'packCount': item['actualPackCount'],
                'salesVolume': item['salesVolume'],
                'price': 0,
                'unitPrice': 0
            })
        
        # 生成整体包装分布（合并所有segments）
        overall_packs = {}
        for segment_items in segment_distributions.values():
            for item in segment_items:
                pack_size = item['packSize']
                if pack_size not in overall_packs:
                    overall_packs[pack_size] = {
                        'packSize': pack_size,
                        'count': 0,
                        'salesVolume': 0,
                        'salesRevenue': 0,
                        'actualPackCount': item['actualPackCount']
                    }
                
                overall_packs[pack_size]['count'] += item['count']
                overall_packs[pack_size]['salesVolume'] += item['salesVolume']
                overall_packs[pack_size]['salesRevenue'] += item['salesRevenue']
        
        overall_list = list(overall_packs.values())
        if overall_list:
            total_count = sum(p['count'] for p in overall_list)
            for pack in overall_list:
                pack['percentage'] = (pack['count'] / total_count * 100) if total_count > 0 else 0
            overall_list.sort(key=lambda x: x['actualPackCount'])
        
        # 为了向后兼容，也生成旧格式数据
        mid_point = len(overall_list) // 2
        dimmer_items = overall_list[:mid_point] if overall_list else []
        switch_items = overall_list[mid_point:] if overall_list else []
        
        # 生成segment colors - 与其他service保持一致
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#F7B731", 
            "#A55EEA", "#26de81", "#FD79A8", "#2ECC71", "#E74C3C",
            "#3498DB", "#9B59B6", "#F39C12", "#1ABC9C", "#E67E22"
        ]
        segment_colors = colors[:len(project_segments)]
        
        return {
            'sameProductComparison': same_product_comparison,
            'packageDistribution': overall_list,
            'segmentDistributions': segment_distributions,  # 新格式：按segment分开
            'segmentNames': project_segments,  # 新格式：segment名称列表
            'segmentColors': segment_colors,  # 新增：segment颜色列表
            'dimmerSwitches': dimmer_items,  # 旧格式兼容
            'lightSwitches': switch_items    # 旧格式兼容
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """返回空的响应格式"""
        return {
            'sameProductComparison': [],
            'packageDistribution': [],
            'segmentDistributions': {},
            'segmentNames': [],
            'segmentColors': [],
            'dimmerSwitches': [],
            'lightSwitches': []
        } 