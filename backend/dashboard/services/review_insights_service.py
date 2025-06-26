"""Review insights service for dashboard."""

import logging
from typing import List, Dict, Any, Set

from .base_service import BaseDashboardService

logger = logging.getLogger(__name__)


class ReviewInsightsService(BaseDashboardService):
    """Service for review insights data.
    
    Replaces frontend getReviewInsightsData() method with server-side
    implementation that applies project ASIN filtering.
    """
    
    def get_data(self) -> Dict[str, Any]:
        """Get review insights data with ASIN filtering.
        
        Returns data in the exact same format as frontend getReviewInsightsData()
        to ensure compatibility with existing UI components.
        """
        try:
            # Build query - replicate frontend logic exactly
            query = self.supabase.table('product_review_analysis').select('''
                product_id,
                aspect_category,
                aspect_subcategory,
                standardized_aspect,
                review_content,
                review_id
            ''')
            
            # Apply base filter
            query = query.neq('standardized_aspect', 'OUT_OF_SCOPE')
            
            # 🔑 CRITICAL: Apply ASIN filtering to prevent data leakage
            # Note: Review analysis table uses product_id which stores ASINs directly
            if not self.project_asins:
                logger.warning(f"No ASINs found for project {self.project_id}")
                return {
                    'painPoints': [],
                    'customerLikes': [],
                    'underservedUseCases': []
                }
            
            query = query.in_('product_id', self.project_asins)
            
            # Execute query
            result = query.execute()
            
            logger.info(f"🔍 Review insights query returned {len(result.data) if result.data else 0} reviews for project {self.project_id}")
            
            if not result.data:
                logger.warning(f"No review insights data found for project {self.project_id}")
                return {
                    'painPoints': [],
                    'customerLikes': [],
                    'underservedUseCases': []
                }
            
            # Process data - replicate frontend logic exactly
            return self._process_review_data(result.data)
            
        except Exception as e:
            logger.error(f"Error getting review insights data for project {self.project_id}: {e}")
            raise
    

    
    def _process_review_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process review data - replicate frontend logic exactly."""
        
        # 转换分类名称
        def get_category_type(aspect_category: str) -> str:
            switch_map = {
                'physical': 'Physical',
                'performance': 'Performance', 
                'use_case': 'Usability'
            }
            return switch_map.get(aspect_category, 'Physical')
        
        # 聚合痛点数据
        aspect_map: Dict[str, Dict[str, Any]] = {}
        
        for item in data:
            key = f"{item['standardized_aspect']}_{item['aspect_category']}"
            if key not in aspect_map:
                aspect_map[key] = {
                    'aspect': item['standardized_aspect'],
                    'category': item['aspect_subcategory'] or item['standardized_aspect'],
                    'type': get_category_type(item['aspect_category']),
                    'frequency': 0,
                    'products': set(),
                    'reviews': set()
                }
            
            aspect_map[key]['frequency'] += 1
            aspect_map[key]['products'].add(item['product_id'])
            aspect_map[key]['reviews'].add(item['review_id'])
        
        # 生成痛点数据（假设所有提及都是痛点，实际可以根据sentiment分析）
        pain_points = []
        for item in aspect_map.values():
            severity = min(5, max(1, item['frequency'] / 10))  # 基于频率计算严重性
            pain_points.append({
                'aspect': item['aspect'],
                'category': item['category'],
                'severity': severity,
                'frequency': item['frequency'],
                'impactedProducts': len(item['products']),
                'type': item['type']
            })
        
        # 按频率排序并取前15个
        pain_points.sort(key=lambda x: x['frequency'], reverse=True)
        pain_points = pain_points[:15]
        
        # 生成客户喜欢的特点（使用相同数据，但作为正面特征）
        customer_likes = []
        for item in aspect_map.values():
            if item['frequency'] > 50:
                satisfaction_level = 'High'
            elif item['frequency'] > 20:
                satisfaction_level = 'Medium'
            else:
                satisfaction_level = 'Low'
                
            customer_likes.append({
                'feature': item['aspect'],
                'category': item['category'],
                'frequency': item['frequency'],
                'satisfactionLevel': satisfaction_level
            })
        
        # 按频率排序并取前10个
        customer_likes.sort(key=lambda x: x['frequency'], reverse=True)
        customer_likes = customer_likes[:10]
        
        # 生成未满足用例（基于低频但重要的方面）
        underserved_use_cases = []
        for item in aspect_map.values():
            if item['frequency'] < 30 and len(item['products']) > 5:
                gap_level = max(50, 100 - (item['frequency'] * 2))  # 频率越低，缺口越大
                underserved_use_cases.append({
                    'useCase': item['aspect'],
                    'productAttribute': item['category'],
                    'gapLevel': gap_level,
                    'mentionCount': item['frequency']
                })
        
        # 按缺口级别排序并取前8个
        underserved_use_cases.sort(key=lambda x: x['gapLevel'], reverse=True)
        underserved_use_cases = underserved_use_cases[:8]
        
        return {
            'painPoints': pain_points,
            'customerLikes': customer_likes,
            'underservedUseCases': underserved_use_cases
        } 