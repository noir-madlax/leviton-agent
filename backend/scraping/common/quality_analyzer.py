import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DataQualityAnalyzer:
    """数据质量分析器"""
    
    def __init__(self):
        # 定义关键字段
        self.key_fields = [
            'platform_id',  # ASIN
            'brand',
            'recent_sales', 
            'unit_price',
            'list_price_usd',
            'position',
            'is_bestseller',
            'price_usd',
            'rating',
            'reviews_count',
            'category'
        ]
    
    def analyze_products_quality(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析产品数据质量
        
        Args:
            products: 产品数据列表
            
        Returns:
            Dict: 数据质量报告
        """
        if not products:
            return {
                'total_products': 0,
                'field_coverage': {},
                'overall_quality_score': 0.0,
                'analysis_time': datetime.now().isoformat()
            }
        
        total_count = len(products)
        field_stats = {}
        
        # 分析每个字段的覆盖率
        for field in self.key_fields:
            non_empty_count = 0
            for product in products:
                value = product.get(field)
                if self._is_value_present(value):
                    non_empty_count += 1
            
            coverage_percent = (non_empty_count / total_count) * 100
            field_stats[field] = {
                'total': total_count,
                'with_value': non_empty_count,
                'coverage_percent': round(coverage_percent, 1)
            }
        
        # 计算整体质量分数
        overall_score = self._calculate_overall_score(field_stats)
        
        return {
            'total_products': total_count,
            'field_coverage': field_stats,
            'overall_quality_score': round(overall_score, 1),
            'analysis_time': datetime.now().isoformat(),
            'quality_summary': self._generate_quality_summary(field_stats)
        }
    
    def _is_value_present(self, value: Any) -> bool:
        """检查值是否存在且有意义"""
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (int, float)):
            return value != 0  # 0也算有值，但这里可能需要根据业务调整
        if isinstance(value, bool):
            return True  # 布尔值总是有意义的
        if isinstance(value, list):
            return len(value) > 0
        return bool(value)
    
    def _calculate_overall_score(self, field_stats: Dict[str, Dict]) -> float:
        """计算整体质量分数"""
        # 给不同字段分配权重
        field_weights = {
            'platform_id': 1.0,  # ASIN是必须的
            'brand': 0.9,        # 品牌很重要
            'price_usd': 0.8,    # 价格重要
            'recent_sales': 0.6, # 销量信息重要
            'unit_price': 0.5,   # 单价信息
            'list_price_usd': 0.5, # 原价信息
            'position': 0.4,     # 位置信息
            'is_bestseller': 0.4, # 畅销标志
            'rating': 0.7,       # 评分重要
            'reviews_count': 0.6, # 评论数量
            'category': 0.6      # 分类信息
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for field, stats in field_stats.items():
            weight = field_weights.get(field, 0.5)  # 默认权重0.5
            score = stats['coverage_percent']
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_quality_summary(self, field_stats: Dict[str, Dict]) -> Dict[str, Any]:
        """生成质量摘要"""
        # 找出覆盖率最高和最低的字段
        sorted_fields = sorted(
            field_stats.items(), 
            key=lambda x: x[1]['coverage_percent'], 
            reverse=True
        )
        
        best_field = sorted_fields[0] if sorted_fields else None
        worst_field = sorted_fields[-1] if sorted_fields else None
        
        # 计算关键字段的平均覆盖率
        key_fields_coverage = []
        for field in ['platform_id', 'brand', 'price_usd', 'recent_sales']:
            if field in field_stats:
                key_fields_coverage.append(field_stats[field]['coverage_percent'])
        
        avg_key_coverage = sum(key_fields_coverage) / len(key_fields_coverage) if key_fields_coverage else 0
        
        return {
            'best_field': {
                'name': best_field[0] if best_field else None,
                'coverage': best_field[1]['coverage_percent'] if best_field else 0
            },
            'worst_field': {
                'name': worst_field[0] if worst_field else None,
                'coverage': worst_field[1]['coverage_percent'] if worst_field else 0
            },
            'key_fields_avg_coverage': round(avg_key_coverage, 1),
            'recommendations': self._generate_recommendations(field_stats)
        }
    
    def _generate_recommendations(self, field_stats: Dict[str, Dict]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 检查关键字段的覆盖率
        for field, stats in field_stats.items():
            coverage = stats['coverage_percent']
            if field in ['platform_id', 'brand'] and coverage < 95:
                recommendations.append(f"{field} coverage is only {coverage}%, should be near 100%")
            elif field in ['price_usd', 'recent_sales'] and coverage < 70:
                recommendations.append(f"{field} coverage is low at {coverage}%, consider improving data extraction")
            elif coverage < 50:
                recommendations.append(f"{field} has very low coverage at {coverage}%")
        
        if not recommendations:
            recommendations.append("Data quality looks good overall!")
        
        return recommendations 