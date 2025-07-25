"""Customer satisfaction analysis service for competitive analysis."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from dashboard.services.base_service import BaseDashboardService
from core.models.filters import ProjectFilters

logger = logging.getLogger(__name__)

class CustomerSatisfactionService(BaseDashboardService):
    """客户满意度分析服务
    
    提供竞争对手产品的客户满意度对比分析，基于评论数据和评分
    数据来源：product_wide_table + review_analysis_aspects + review_analysis_aspect_occurrences
    """
    
    # 默认竞争对手产品ASIN列表
    DEFAULT_COMPETITOR_ASINS = [
        'B00NG0ELL0',  # Leviton DSL06 - Mid-tier brand representative
        'B0BVKZLT3B',  # Leviton D215S - Mid-tier brand representative
        'B0BVKYKKRK',  # Leviton D26HD - Mid-tier brand representative
        'B0BSHKS26L',  # Lutron Caseta Diva - Mid-tier brand representative
        'B085D8M2MR',  # Lutron Diva - Mid-tier brand representative
        'B01EZV35QU',  # TP Link Switch
    ]
    
    def __init__(self, project_id: str, filters: Optional[Dict[str, Any]] = None, 
                 date_range: Optional[Dict[str, str]] = None, selected_asins: Optional[List[str]] = None):
        """初始化服务
        
        Args:
            project_id: 项目ID 
            filters: 过滤条件（categories, brands, segments, extend_fields）
            date_range: 时间范围 {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
            selected_asins: 选中的ASIN列表，如果为空则使用默认竞争对手产品
        """
        super().__init__(project_id)
        
        # 设置筛选器
        if filters:
            project_filters = ProjectFilters.from_dict(filters)
            self.set_project_filters(project_filters)
        
        # 设置时间范围
        self.date_range = date_range or {}
        
        # 设置分析的ASIN列表
        self.selected_asins = selected_asins or self.DEFAULT_COMPETITOR_ASINS
        
        logger.info(f"CustomerSatisfactionService initialized for project {project_id} with {len(self.selected_asins)} selected ASINs")
    
    def get_data(self) -> Dict[str, Any]:
        """获取客户满意度分析数据
        
        Returns:
            Dict包含products和summary两个字段
        """
        try:
            # 1. 获取产品基础信息
            product_info = self._get_product_info()
            if not product_info:
                return self._get_empty_response()
            
            # 2. 获取评论分析数据
            review_stats = self._get_review_statistics()
            
            # 3. 处理和计算满意度数据
            products_data = self._process_satisfaction_data(product_info, review_stats)
            
            # 4. 生成汇总统计
            summary = self._generate_summary(products_data)
            
            return {
                "products": products_data,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error in CustomerSatisfactionService for project {self.project_id}: {e}")
            return self._get_empty_response()
    
    def _get_product_info(self) -> List[Dict[str, Any]]:
        """获取产品基础信息"""
        try:
            query = self.supabase.from_('product_wide_table').select(
                'platform_id, title, brand, price_usd, reviews_count, category, product_url, rating'
            ).in_('platform_id', self.selected_asins)
            
            result = query.execute()
            
            if result.data:
                logger.info(f"Retrieved {len(result.data)} product info records")
                return result.data
            else:
                logger.warning("No product information found for selected ASINs")
                return []
                
        except Exception as e:
            logger.error(f"Error getting product info: {e}")
            return []
    
    def _get_review_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取评论统计数据"""
        try:
            # 获取每个产品的评论分析统计
            review_stats = {}
            
            for asin in self.selected_asins:
                # 获取该产品的分析评论数量
                aspects_query = self.supabase.from_('review_analysis_aspects').select('aspect_pk').eq('project_id', self.project_id).eq('product_id', asin)
                aspects_result = aspects_query.execute()
                
                if aspects_result.data:
                    aspect_pks = [item['aspect_pk'] for item in aspects_result.data]
                    
                    # 获取唯一的review_ids
                    occurrences_query = self.supabase.from_('review_analysis_aspect_occurrences').select('review_id').in_('aspect_pk', aspect_pks)
                    occurrences_result = occurrences_query.execute()
                    
                    if occurrences_result.data:
                        unique_review_ids = set(item['review_id'] for item in occurrences_result.data)
                        total_reviews = len(unique_review_ids)
                    else:
                        total_reviews = 0
                else:
                    total_reviews = 0
                
                review_stats[asin] = {
                    'total_reviews': total_reviews,
                    'satisfaction_score': self._calculate_satisfaction_score(asin)
                }
            
            return review_stats
            
        except Exception as e:
            logger.error(f"Error getting review statistics: {e}")
            return {}
    
    def _calculate_satisfaction_score(self, asin: str) -> float:
        """计算产品满意度分数"""
        try:
            # 这里可以基于评论情感分析计算满意度分数
            # 暂时使用简化的计算方法，基于评分
            product_query = self.supabase.from_('product_wide_table').select('rating').eq('platform_id', asin).single()
            product_result = product_query.execute()
            
            if product_result.data and product_result.data.get('rating'):
                rating = float(product_result.data['rating'])
                # 将1-5星评分转换为0-100满意度分数
                satisfaction_score = (rating - 1) / 4 * 100
                return round(satisfaction_score, 1)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating satisfaction score for {asin}: {e}")
            return 0.0
    
    def _process_satisfaction_data(self, product_info: List[Dict[str, Any]], 
                                 review_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理满意度数据"""
        products_data = []
        
        for product in product_info:
            asin = product['platform_id']
            title = product['title'] or asin
            
            # 生成短标题（用于显示）
            short_title = title[:50] + "..." if len(title) > 50 else title
            
            # 获取评论统计
            stats = review_stats.get(asin, {'total_reviews': 0, 'satisfaction_score': 0.0})
            
            product_data = {
                'asin': asin,
                'name': short_title,
                'full_title': title,
                'brand': product.get('brand', 'Unknown'),
                'total_reviews': stats['total_reviews'],
                'average_rating': product.get('rating'),
                'satisfaction_score': stats['satisfaction_score'],
                'price_usd': product.get('price_usd'),
                'product_url': product.get('product_url'),
                'thumbnail_url': None  # 可以后续添加缩略图逻辑
            }
            
            products_data.append(product_data)
        
        # 按满意度分数排序
        products_data.sort(key=lambda x: x['satisfaction_score'], reverse=True)
        
        return products_data
    
    def _generate_summary(self, products_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成汇总统计"""
        if not products_data:
            return {
                'total_products': 0,
                'avg_satisfaction_score': 0.0,
                'total_reviews_analyzed': 0,
                'top_performer': None,
                'analysis_method': 'Based on latest 200 reviews per product',
                'last_updated': datetime.now().isoformat()
            }
        
        total_products = len(products_data)
        total_reviews = sum(p['total_reviews'] for p in products_data)
        avg_satisfaction = sum(p['satisfaction_score'] for p in products_data) / total_products
        top_performer = products_data[0]['asin'] if products_data else None
        
        return {
            'total_products': total_products,
            'avg_satisfaction_score': round(avg_satisfaction, 1),
            'total_reviews_analyzed': total_reviews,
            'top_performer': top_performer,
            'analysis_method': 'Based on latest 200 reviews per product',
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_empty_response(self) -> Dict[str, Any]:
        """获取空响应"""
        return {
            "products": [],
            "summary": {
                'total_products': 0,
                'avg_satisfaction_score': 0.0,
                'total_reviews_analyzed': 0,
                'top_performer': None,
                'analysis_method': 'Based on latest 200 reviews per product',
                'last_updated': datetime.now().isoformat()
            }
        }
