#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品评论分析数据导入脚本
功能：将consolidated_aspect_categorization.json数据扁平化后导入到Supabase
"""

import json
import os
import sys
from typing import Dict, List, Any
from datetime import datetime
import traceback
from supabase import create_client, Client
from config import load_config, validate_config, get_data_file_path

# 导入配置和Supabase客户端
try:
    from supabase import create_client, Client
    from config import load_config, validate_config
except ImportError as e:
    print(f"请先安装依赖: pip install supabase")
    print(f"导入错误: {e}")
    sys.exit(1)

class ReviewAnalysisImporter:
    """评论分析数据导入器"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """初始化Supabase客户端"""
        self.supabase = create_client(supabase_url, supabase_key)
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        """加载JSON文件"""
        print(f"正在加载文件: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"未找到文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def flatten_consolidated_aspect_data(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """扁平化consolidated_aspect_categorization.json数据"""
        print("正在扁平化consolidated_aspect_categorization数据...")
        
        rows = []
        results = json_data.get("results", {})
        
        for product_id, product_data in results.items():
            aspect_categorization = product_data.get("aspect_categorization", {})
            
            for aspect_category, subcategories in aspect_categorization.items():
                # 处理physical和performance类别（嵌套结构）
                if aspect_category in ['phy', 'perf'] and isinstance(subcategories, dict):
                    # 映射缩写到完整名称
                    category_full_name = 'physical' if aspect_category == 'phy' else 'performance'
                    
                    for subcategory, reviews in subcategories.items():
                        if isinstance(reviews, dict):
                            for review_key, standardized_aspect in reviews.items():
                                # 从review_key中提取评论内容（@后的内容）
                                if '@' in review_key:
                                    review_content = review_key.split('@', 1)[1].strip()
                                else:
                                    review_content = review_key
                                
                                rows.append({
                                    'product_id': product_id,
                                    'aspect_category': category_full_name,
                                    'aspect_subcategory': subcategory,
                                    'review_key': review_key,
                                    'review_content': review_content,
                                    'standardized_aspect': standardized_aspect
                                })
                
                # 处理use类别（直接映射）
                elif aspect_category == 'use' and isinstance(subcategories, dict):
                    for use_case, standardized_aspect in subcategories.items():
                        rows.append({
                            'product_id': product_id,
                            'aspect_category': 'use_case',
                            'aspect_subcategory': 'application',
                            'review_key': use_case,
                            'review_content': use_case.replace('_', ' ').title(),
                            'standardized_aspect': standardized_aspect
                        })
        
        print(f"扁平化完成，生成 {len(rows)} 条记录")
        return rows
    
    def clean_and_validate_data(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗和验证数据"""
        print("正在清洗和验证数据...")
        
        valid_rows = []
        
        for row in rows:
            # 检查必填字段
            if not all([
                row.get('product_id'),
                row.get('aspect_category'),
                row.get('aspect_subcategory'),
                row.get('review_key'),
                row.get('review_content'),
                row.get('standardized_aspect')
            ]):
                self.skipped_count += 1
                continue
            
            # 数据清洗
            cleaned_row = {
                'product_id': str(row['product_id']).strip(),
                'aspect_category': str(row['aspect_category']).strip().lower(),
                'aspect_subcategory': str(row['aspect_subcategory']).strip(),
                'review_key': str(row['review_key']).strip(),
                'review_content': str(row['review_content']).strip(),
                'standardized_aspect': str(row['standardized_aspect']).strip()
            }
            
            # 长度限制检查
            if len(cleaned_row['review_content']) > 2000:
                cleaned_row['review_content'] = cleaned_row['review_content'][:2000] + "..."
            
            valid_rows.append(cleaned_row)
        
        print(f"数据清洗完成，有效记录: {len(valid_rows)}, 跳过记录: {self.skipped_count}")
        return valid_rows
    
    def batch_insert_data(self, rows: List[Dict[str, Any]], batch_size: int = 50) -> bool:
        """批量插入数据"""
        print(f"开始批量插入数据，总计 {len(rows)} 条记录，批次大小: {batch_size}")
        
        total_batches = (len(rows) + batch_size - 1) // batch_size
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            try:
                print(f"插入批次 {batch_num}/{total_batches} ({len(batch)} 条记录)...")
                
                response = self.supabase.table('product_review_analysis').insert(batch).execute()
                
                if response.data:
                    self.imported_count += len(batch)
                    print(f"批次 {batch_num} 插入成功")
                else:
                    print(f"批次 {batch_num} 插入失败，无返回数据")
                    self.error_count += len(batch)
                    
            except Exception as e:
                print(f"批次 {batch_num} 插入失败: {e}")
                self.error_count += len(batch)
                
                # 尝试单条插入以找到问题记录
                if len(batch) > 1:
                    print("尝试单条插入以定位问题...")
                    for j, record in enumerate(batch):
                        try:
                            single_response = self.supabase.table('product_review_analysis').insert([record]).execute()
                            if single_response.data:
                                self.imported_count += 1
                                self.error_count -= 1
                        except Exception as single_error:
                            print(f"单条记录插入失败 {record.get('product_id', 'unknown')}: {single_error}")
        
        return self.error_count == 0
    
    def verify_import_results(self) -> Dict[str, Any]:
        """验证导入结果"""
        print("验证导入结果...")
        
        try:
            # 总数统计
            total_response = self.supabase.table('product_review_analysis').select('*', count='exact').execute()
            total_count = total_response.count
            
            # 产品覆盖统计
            product_response = self.supabase.table('product_review_analysis').select('product_id').execute()
            unique_products = len(set(record['product_id'] for record in product_response.data))
            
            results = {
                'total_records': total_count,
                'unique_products': unique_products,
                'import_summary': {
                    'imported': self.imported_count,
                    'skipped': self.skipped_count,
                    'errors': self.error_count
                }
            }
            
            print(f"导入结果验证完成:")
            print(f"  - 总记录数: {total_count}")
            print(f"  - 涉及产品数: {unique_products}")
            print(f"  - 导入成功: {self.imported_count}")
            print(f"  - 跳过记录: {self.skipped_count}")
            print(f"  - 错误记录: {self.error_count}")
            
            return results
            
        except Exception as e:
            print(f"验证导入结果时出错: {e}")
            return {'error': str(e)}

def main():
    """主函数"""
    print("=== 产品评论分析数据导入工具 ===")
    print(f"开始时间: {datetime.now()}")
    
    # 加载配置
    config = load_config()
    if not validate_config(config):
        print("❌ 配置验证失败，请检查环境变量或config.env文件")
        return False
    
    try:
        # 初始化导入器
        importer = ReviewAnalysisImporter(config['SUPABASE_URL'], config['SUPABASE_KEY'])
        
        # 1. 加载和处理consolidated数据
        consolidated_file = get_data_file_path('review', 'consolidated_aspect_categorization.json')
        try:
            consolidated_data = importer.load_json_file(consolidated_file)
            consolidated_rows = importer.flatten_consolidated_aspect_data(consolidated_data)
        except Exception as e:
            print(f"处理consolidated数据时出错: {e}")
            return False
        
        if not consolidated_rows:
            print("没有数据需要导入")
            return False
        
        # 2. 清洗和验证数据
        clean_rows = importer.clean_and_validate_data(consolidated_rows)
        
        if not clean_rows:
            print("没有有效数据需要导入")
            return False
        
        # 3. 批量导入数据
        success = importer.batch_insert_data(clean_rows, batch_size=50)
        
        # 4. 验证导入结果
        results = importer.verify_import_results()
        
        print(f"\n=== 导入完成 ===")
        print(f"结束时间: {datetime.now()}")
        print(f"导入状态: {'成功' if success else '部分成功'}")
        
        return success
        
    except Exception as e:
        print(f"导入过程中发生错误: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 