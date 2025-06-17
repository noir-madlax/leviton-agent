#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整评论数据导入脚本
从expanded_review_results.json导入详细的评论数据到product_reviews表
"""

import json
import os
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from config import load_config, validate_config, get_data_file_path

def load_review_data(file_path: str) -> Dict[str, Any]:
    """加载评论数据"""
    print(f"📂 加载评论数据: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ 成功加载 {len(data)} 个产品的评论数据")
            return data
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析错误: {e}")
    except Exception as e:
        raise Exception(f"文件读取错误: {e}")

def extract_review_records(review_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从嵌套的JSON结构中提取评论记录"""
    print("🔄 解析评论数据结构...")
    
    records = []
    
    # 获取results部分的数据
    results_data = review_data.get('results', {})
    if not results_data:
        print("❌ 未找到results数据")
        return records
    
    for product_id, product_info in results_data.items():
        print(f"  处理产品: {product_id}")
        
        # 获取review_analysis部分
        review_analysis = product_info.get('review_analysis', {})
        if not review_analysis:
            print(f"    跳过产品 {product_id}: 无review_analysis数据")
            continue
        
        # 遍历category (phy, perf, use等)
        for category, subcategories in review_analysis.items():
            if not isinstance(subcategories, dict):
                continue
                
            # 遍历subcategory
            for subcategory, aspects in subcategories.items():
                if not isinstance(aspects, dict):
                    continue
                    
                # 遍历aspect_key
                for aspect_key, sentiment_data in aspects.items():
                    if not isinstance(sentiment_data, dict):
                        continue
                    
                    # 遍历sentiment (+, -, neutral等)
                    for sentiment_key, review_list in sentiment_data.items():
                        if not isinstance(review_list, list):
                            continue
                            
                        # 遍历具体的评论
                        for review_obj in review_list:
                            if isinstance(review_obj, dict):
                                record = {
                                    'product_id': product_id,
                                    'category': category,
                                    'subcategory': subcategory,
                                    'aspect_key': aspect_key,
                                    'sentiment': sentiment_key,
                                    'review_id': review_obj.get('review_id'),
                                    'review_text': review_obj.get('review_text'),
                                    'review_title': review_obj.get('review_title'),
                                    'rating': review_obj.get('rating'),
                                    'review_date': review_obj.get('date'),
                                    'verified': review_obj.get('verified', False),
                                    'user_name': review_obj.get('userName'),
                                    'number_of_helpful': review_obj.get('numberOfHelpful', 0)
                                }
                                
                                # 验证必要字段
                                if record['review_id'] is not None and record['review_text']:
                                    records.append(record)
    
    print(f"✅ 提取到 {len(records)} 条评论记录")
    return records

def batch_insert_reviews(supabase: Client, records: List[Dict[str, Any]], batch_size: int = 50) -> Dict[str, int]:
    """批量插入评论数据"""
    print(f"📥 开始批量插入评论数据 (批次大小: {batch_size})")
    
    stats = {
        'total_records': len(records),
        'success_count': 0,
        'error_count': 0,
        'batch_count': 0,
        'duplicate_removed': 0
    }
    
    # 按批次处理
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        stats['batch_count'] += 1
        
        try:
            # 准备批次数据并去重
            batch_data = []
            seen_keys = set()  # 用于批次内部去重
            
            for record in batch:
                # 清理数据
                clean_record = {
                    'product_id': record['product_id'],
                    'aspect_key': record['aspect_key'],
                    'review_id': int(record['review_id']) if record['review_id'] is not None else None,
                    'review_text': record['review_text'][:10000] if record['review_text'] else None,  # 限制长度
                    'review_title': record['review_title'][:500] if record['review_title'] else None,
                    'rating': record['rating'][:50] if record['rating'] else None,
                    'review_date': record['review_date'][:100] if record['review_date'] else None,
                    'verified': bool(record['verified']) if record['verified'] is not None else False,
                    'user_name': record['user_name'][:100] if record['user_name'] else None,
                    'number_of_helpful': int(record['number_of_helpful']) if record['number_of_helpful'] is not None else 0
                }
                
                # 过滤掉空的必要字段
                if clean_record['review_id'] is not None and clean_record['review_text']:
                    # 创建唯一键用于去重
                    unique_key = (clean_record['product_id'], clean_record['review_id'], clean_record['aspect_key'])
                    
                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        batch_data.append(clean_record)
                    else:
                        stats['duplicate_removed'] += 1
            
            if batch_data:
                # 执行upsert（插入或更新）
                result = supabase.table('product_reviews').upsert(
                    batch_data,
                    on_conflict='product_id,review_id,aspect_key'
                ).execute()
                
                stats['success_count'] += len(batch_data)
                print(f"  ✅ 批次 {stats['batch_count']}: 成功处理 {len(batch_data)} 条记录")
            else:
                print(f"  ⚠️ 批次 {stats['batch_count']}: 没有有效数据")
                
        except Exception as e:
            stats['error_count'] += len(batch)
            print(f"  ❌ 批次 {stats['batch_count']} 插入失败: {str(e)}")
            
            # 尝试单条插入来识别具体错误
            for record in batch:
                try:
                    clean_record = {
                        'product_id': record['product_id'],
                        'aspect_key': record['aspect_key'],
                        'review_id': int(record['review_id']) if record['review_id'] is not None else None,
                        'review_text': record['review_text'][:10000] if record['review_text'] else None,
                        'review_title': record['review_title'][:500] if record['review_title'] else None,
                        'rating': record['rating'][:50] if record['rating'] else None,
                        'review_date': record['review_date'][:100] if record['review_date'] else None,
                        'verified': bool(record['verified']) if record['verified'] is not None else False,
                        'user_name': record['user_name'][:100] if record['user_name'] else None,
                        'number_of_helpful': int(record['number_of_helpful']) if record['number_of_helpful'] is not None else 0
                    }
                    
                    if clean_record['review_id'] is not None and clean_record['review_text']:
                        supabase.table('product_reviews').upsert(
                            [clean_record],
                            on_conflict='product_id,review_id,aspect_key'
                        ).execute()
                        stats['success_count'] += 1
                        stats['error_count'] -= 1
                        
                except Exception as single_error:
                    print(f"    ❌ 单条记录插入失败 (产品: {record['product_id']}, 评论: {record['review_id']}): {str(single_error)}")
    
    return stats

def get_import_statistics(supabase: Client) -> Dict[str, Any]:
    """获取导入统计信息"""
    try:
        # 总记录数
        total_result = supabase.table('product_reviews').select('count', count='exact').execute()
        total_count = total_result.count
        
        # 按产品统计
        product_stats = supabase.table('product_reviews').select(
            'product_id', 
            count='exact'
        ).execute()
        
        # 按评分统计
        rating_stats = supabase.rpc('get_rating_distribution', {}).execute()
        
        # 验证用户统计
        verified_result = supabase.table('product_reviews').select(
            'count', 
            count='exact'
        ).eq('verified', True).execute()
        verified_count = verified_result.count
        
        return {
            'total_reviews': total_count,
            'unique_products': len(set(row['product_id'] for row in product_stats.data)) if product_stats.data else 0,
            'verified_reviews': verified_count,
            'verification_rate': f"{(verified_count / total_count * 100):.1f}%" if total_count > 0 else "0%"
        }
        
    except Exception as e:
        print(f"⚠️ 统计信息获取失败: {e}")
        return {}

def main():
    """主函数"""
    print("🚀 开始导入完整评论数据")
    
    # 1. 加载配置
    config = load_config()
    if not validate_config(config):
        return
    
    # 2. 初始化Supabase客户端
    try:
        supabase: Client = create_client(config['SUPABASE_URL'], config['SUPABASE_KEY'])
        print("✅ Supabase 连接成功")
    except Exception as e:
        print(f"❌ Supabase 连接失败: {e}")
        return
    
    # 3. 构建数据文件路径
    data_file_path = get_data_file_path('review', 'expanded_review_results.json')
    
    try:
        # 4. 加载评论数据
        review_data = load_review_data(data_file_path)
        
        # 5. 提取评论记录
        records = extract_review_records(review_data)
        
        if not records:
            print("❌ 没有找到有效的评论记录")
            return
        
        # 6. 批量插入数据
        print(f"\n📊 准备插入 {len(records)} 条评论记录")
        stats = batch_insert_reviews(supabase, records, config['BATCH_SIZE'])
        
        # 7. 显示导入结果
        print(f"\n📈 导入完成统计:")
        print(f"  总记录数: {stats['total_records']}")
        print(f"  成功导入: {stats['success_count']}")
        print(f"  失败记录: {stats['error_count']}")
        print(f"  批次内重复去除: {stats['duplicate_removed']}")
        print(f"  处理批次: {stats['batch_count']}")
        print(f"  成功率: {(stats['success_count'] / stats['total_records'] * 100):.1f}%")
        
        # 8. 获取数据库统计
        print(f"\n📊 数据库当前状态:")
        db_stats = get_import_statistics(supabase)
        for key, value in db_stats.items():
            print(f"  {key}: {value}")
        
        print("\n✅ 评论数据导入完成!")
        
    except Exception as e:
        print(f"❌ 导入过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 