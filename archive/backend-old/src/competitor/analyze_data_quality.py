#!/usr/bin/env python3
"""
分析竞争品数据质量和分布
检查每个产品的评论数量和分类分布
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def analyze_competitor_data():
    """分析竞争品数据质量"""
    # 读取生成的数据文件
    ts_file = Path(__file__).parent.parent.parent.parent / "frontend/lib/competitorAnalysis.ts"
    
    if not ts_file.exists():
        print("找不到数据文件")
        return
    
    with open(ts_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取数据（简单的字符串处理）
    data_start = content.find('export const competitorMatrixData: ProductPainPoint[] = [')
    data_end = content.find('];', data_start)
    data_section = content[data_start:data_end]
    
    # 解析JSON数据
    json_start = data_section.find('[')
    json_data = data_section[json_start:] + ']'
    
    try:
        # 修复JSON格式
        json_data = json_data.replace('};', '}')
        data = json.loads(json_data)
    except:
        print("JSON解析失败，使用Python AST评估...")
        # 读取原始数据进行分析
        return analyze_from_python_script()
    
    # 分析数据
    product_stats = defaultdict(lambda: {
        'total_mentions': 0,
        'total_reviews': 0,
        'categories': 0,
        'with_reviews': 0,
        'categories_list': []
    })
    
    all_categories = set()
    
    for item in data:
        product = item['product']
        mentions = item['mentions']
        total_reviews = item['totalReviews']
        category = item['category']
        
        product_stats[product]['total_mentions'] += mentions
        product_stats[product]['total_reviews'] += total_reviews
        product_stats[product]['categories'] += 1
        product_stats[product]['categories_list'].append(category)
        
        if total_reviews > 0:
            product_stats[product]['with_reviews'] += 1
            
        all_categories.add(category)
    
    print("="*80)
    print("竞争品数据分析报告")
    print("="*80)
    
    print(f"\n📊 总体概况:")
    print(f"总分类数量: {len(all_categories)}")
    print(f"总数据点: {len(data)}")
    
    print(f"\n📈 各产品数据统计:")
    print(f"{'产品名称':<20} {'分类数':<8} {'总提及':<8} {'总评论':<8} {'有评论分类':<12} {'评论覆盖率':<10}")
    print("-" * 80)
    
    for product, stats in product_stats.items():
        coverage_rate = (stats['with_reviews'] / stats['categories'] * 100) if stats['categories'] > 0 else 0
        print(f"{product:<20} {stats['categories']:<8} {stats['total_mentions']:<8} {stats['total_reviews']:<8} {stats['with_reviews']:<12} {coverage_rate:<10.1f}%")
    
    # 分析分类分布
    category_counts = defaultdict(int)
    category_reviews = defaultdict(int)
    
    for item in data:
        category = item['category']
        category_counts[category] += 1
        if item['totalReviews'] > 0:
            category_reviews[category] += item['totalReviews']
    
    print(f"\n📋 分类分析 (总共{len(all_categories)}个分类):")
    print("排序按出现产品数:")
    
    # 按产品数排序的分类
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"{'分类名称':<35} {'产品数':<8} {'总评论':<8}")
    print("-" * 60)
    
    for category, product_count in sorted_categories[:15]:  # 只显示前15个
        reviews = category_reviews[category]
        print(f"{category[:34]:<35} {product_count:<8} {reviews:<8}")
    
    if len(sorted_categories) > 15:
        print(f"... 还有 {len(sorted_categories) - 15} 个分类")
    
    # 建议
    print(f"\n💡 数据质量建议:")
    
    # 找出没有评论的产品
    no_review_products = [p for p, s in product_stats.items() if s['total_reviews'] == 0]
    if no_review_products:
        print(f"❌ 以下产品完全没有评论数据: {', '.join(no_review_products)}")
    
    # 找出评论很少的产品
    low_review_products = [p for p, s in product_stats.items() if 0 < s['total_reviews'] < 10]
    if low_review_products:
        print(f"⚠️  以下产品评论数据很少(<10): {', '.join(low_review_products)}")
    
    # 分类太多的问题
    if len(all_categories) > 20:
        print(f"⚠️  分类数量过多({len(all_categories)}个)，建议:")
        print("   1. 只显示出现在多个产品中的分类(≥3个产品)")
        print("   2. 只显示有足够评论数据的分类(≥5个评论)")
        print("   3. 将相似分类合并成大类")
    
    return product_stats, all_categories, sorted_categories

def analyze_from_python_script():
    """从Python脚本直接运行分析"""
    import os
    os.chdir(Path(__file__).parent)
    
    # 导入并运行分析器
    sys.path.append('.')
    from competitor_analysis import CompetitorAnalyzer
    
    current_dir = Path(__file__).parent.parent.parent
    data_dir = current_dir / "data/result/process_review/20250609_05"
    
    analyzer = CompetitorAnalyzer(str(data_dir))
    analyzer.load_data()
    analyzer.analyze_competitor_pain_points()
    analyzer.calculate_satisfaction_rates()
    
    # 分析结果
    print("="*80)
    print("从原始数据分析竞争品数据")
    print("="*80)
    
    product_stats = {}
    for product_name, categories in analyzer.product_pain_matrix.items():
        total_mentions = sum(data['mentions'] for data in categories.values())
        total_reviews = sum(data.get('total_reviews', 0) for data in categories.values())
        categories_with_reviews = sum(1 for data in categories.values() if data.get('total_reviews', 0) > 0)
        
        product_stats[product_name] = {
            'categories': len(categories),
            'total_mentions': total_mentions,
            'total_reviews': total_reviews,
            'with_reviews': categories_with_reviews
        }
    
    print(f"\n📈 各产品原始数据统计:")
    print(f"{'产品名称':<20} {'分类数':<8} {'总提及':<8} {'总评论':<8} {'有评论分类':<12} {'评论覆盖率':<10}")
    print("-" * 80)
    
    for product, stats in product_stats.items():
        coverage_rate = (stats['with_reviews'] / stats['categories'] * 100) if stats['categories'] > 0 else 0
        print(f"{product:<20} {stats['categories']:<8} {stats['total_mentions']:<8} {stats['total_reviews']:<8} {stats['with_reviews']:<12} {coverage_rate:<10.1f}%")

if __name__ == "__main__":
    try:
        analyze_competitor_data()
    except Exception as e:
        print(f"分析失败: {e}")
        print("尝试从原始数据分析...")
        analyze_from_python_script() 