#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV数据导入脚本
根据combined_products_with_final_categories.csv文件导入产品数据
"""
import pandas as pd
import os
from supabase import create_client
from config import load_config, validate_config, get_data_file_path

def main():
    """主函数"""
    # 1. 加载配置
    config = load_config()
    if not validate_config(config):
        return
    
    # 2. 初始化Supabase客户端
    try:
        supabase = create_client(config['SUPABASE_URL'], config['SUPABASE_KEY'])
        print("✅ Supabase 连接成功")
    except Exception as e:
        print(f"❌ Supabase 连接失败: {e}")
        return

    # 3. 获取CSV文件路径
    csv_file = get_data_file_path('product', 'combined_products_with_final_categories.csv')
    
    if not os.path.exists(csv_file):
        print(f"❌ 文件不存在: {csv_file}")
        return
    
    # 读取CSV文件
    print(f"📂 读取CSV文件: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"✅ 读取到 {len(df)} 条记录")
    
    # 转换为字典列表
    records = df.to_dict('records')
    
    # 批量插入数据
    try:
        batch_size = config['BATCH_SIZE']
        success_count = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # 插入批次数据
            result = supabase.table('product_wide_table').insert(batch).execute()
            success_count += len(batch)
            print(f"✅ 批次插入成功: {len(batch)} 条记录")
        
        print(f"🎉 数据导入完成！总共插入 {success_count} 条记录")
        
    except Exception as e:
        print(f"❌ 数据插入失败: {e}")

if __name__ == "__main__":
    main() 