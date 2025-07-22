#!/usr/bin/env python3
"""
CSV数据导入Supabase脚本
Import CSV data to Supabase sales_trend_data table

使用方法:
python import_csv.py --csv-file leviton_B08SJ3Z8XD_sales_20250720_184936.csv --asin B08SJ3Z8XD
"""

import pandas as pd
import argparse
import sys
import os
from typing import Dict, List
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

from backend.core.database.connection import get_supabase_client

class SalesTrendImporter:
    """销售趋势数据导入器"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.table_name = 'sales_trend_data'
    
    def validate_csv(self, df: pd.DataFrame) -> bool:
        """验证CSV数据格式"""
        required_columns = ['date', 'estimated_units_sold', 'last_known_price']
        
        # 检查必需列
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ CSV文件缺少必需的列: {missing_columns}")
            return False
        
        # 检查数据类型
        try:
            pd.to_datetime(df['date'])
            pd.to_numeric(df['estimated_units_sold'])
            pd.to_numeric(df['last_known_price'])
        except ValueError as e:
            print(f"❌ 数据格式错误: {e}")
            return False
        
        # 检查数据范围
        if (df['estimated_units_sold'] < 0).any():
            print("❌ 销售量包含负值")
            return False
        
        if (df['last_known_price'] <= 0).any():
            print("❌ 价格包含无效值（≤0）")
            return False
        
        return True
    
    def process_csv(self, csv_file: str, asin: str) -> pd.DataFrame:
        """处理CSV文件"""
        print(f"📖 读取CSV文件: {csv_file}")
        
        # 读取CSV
        try:
            df = pd.read_csv(csv_file)
            print(f"✅ 成功读取 {len(df)} 行数据")
        except Exception as e:
            print(f"❌ 读取CSV文件失败: {e}")
            sys.exit(1)
        
        # 验证数据
        if not self.validate_csv(df):
            sys.exit(1)
        
        # 数据处理
        df = df.copy()
        
        # 添加ASIN列
        df['asin'] = asin
        
        # 确保日期格式正确
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # 确保数值类型正确
        df['estimated_units_sold'] = df['estimated_units_sold'].astype(int)
        df['last_known_price'] = df['last_known_price'].astype(float)
        
        # 计算收入（可选，数据库会自动计算）
        df['estimated_revenue'] = df['estimated_units_sold'] * df['last_known_price']
        
        # 添加时间戳
        current_time = datetime.now().isoformat()
        df['created_at'] = current_time
        df['updated_at'] = current_time
        
        print(f"✅ 数据处理完成，准备导入 {len(df)} 条记录")
        return df
    
    def check_existing_data(self, asin: str, dates: List[str]) -> List[str]:
        """检查数据库中已存在的数据"""
        try:
            result = self.supabase.table(self.table_name).select('date').eq(
                'asin', asin
            ).in_('date', dates).execute()
            
            existing_dates = [record['date'] for record in result.data]
            return existing_dates
        except Exception as e:
            print(f"⚠️  检查已存在数据时出错: {e}")
            return []
    
    def import_data(self, df: pd.DataFrame, skip_existing: bool = True) -> bool:
        """导入数据到Supabase"""
        asin = df.iloc[0]['asin']
        print(f"🚀 开始导入ASIN {asin} 的数据...")
        
        # 检查已存在的数据
        if skip_existing:
            existing_dates = self.check_existing_data(asin, df['date'].tolist())
            if existing_dates:
                print(f"⚠️  发现 {len(existing_dates)} 条已存在的记录，将跳过")
                df = df[~df['date'].isin(existing_dates)]
                print(f"📊 剩余待导入数据: {len(df)} 条")
        
        if len(df) == 0:
            print("ℹ️  没有新数据需要导入")
            return True
        
        # 分批导入（每批500条）
        batch_size = 500
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        success_count = 0
        error_count = 0
        
        for i in range(0, len(df), batch_size):
            batch_num = (i // batch_size) + 1
            batch_df = df.iloc[i:i + batch_size]
            
            print(f"📦 导入第 {batch_num}/{total_batches} 批数据 ({len(batch_df)} 条)...")
            
            try:
                # 转换为字典列表
                records = batch_df.to_dict('records')
                
                # 执行插入
                result = self.supabase.table(self.table_name).insert(records).execute()
                
                if result.data:
                    success_count += len(result.data)
                    print(f"✅ 第 {batch_num} 批导入成功: {len(result.data)} 条")
                else:
                    print(f"⚠️  第 {batch_num} 批导入结果为空")
                    
            except Exception as e:
                error_count += len(batch_df)
                print(f"❌ 第 {batch_num} 批导入失败: {e}")
        
        # 导入结果统计
        print(f"\n📈 导入完成统计:")
        print(f"   ✅ 成功导入: {success_count} 条")
        print(f"   ❌ 导入失败: {error_count} 条")
        print(f"   📊 总计处理: {success_count + error_count} 条")
        
        return error_count == 0
    
    def verify_import(self, asin: str) -> None:
        """验证导入结果"""
        try:
            # 查询统计信息
            result = self.supabase.table(self.table_name).select(
                'asin, date, estimated_units_sold, last_known_price, estimated_revenue'
            ).eq('asin', asin).order('date', desc=True).limit(5).execute()
            
            if result.data:
                print(f"\n🔍 验证结果 - ASIN {asin} 最近5条记录:")
                for record in result.data:
                    print(f"   {record['date']}: 销量={record['estimated_units_sold']}, "
                          f"价格=${record['last_known_price']}, 收入=${record['estimated_revenue']:.2f}")
            
            # 统计总数
            count_result = self.supabase.table(self.table_name).select(
                'id', count='exact'
            ).eq('asin', asin).execute()
            
            total_count = count_result.count if count_result.count else 0
            print(f"📊 ASIN {asin} 总记录数: {total_count}")
            
        except Exception as e:
            print(f"❌ 验证失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='导入销售趋势CSV数据到Supabase')
    parser.add_argument('--csv-file', required=True, help='CSV文件路径')
    parser.add_argument('--asin', required=True, help='产品ASIN')
    parser.add_argument('--skip-existing', action='store_true', default=True, 
                       help='跳过已存在的数据（默认启用）')
    parser.add_argument('--force', action='store_true', default=False,
                       help='强制导入，不跳过已存在的数据')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.csv_file):
        print(f"❌ CSV文件不存在: {args.csv_file}")
        sys.exit(1)
    
    # 创建导入器
    importer = SalesTrendImporter()
    
    # 处理CSV文件
    df = importer.process_csv(args.csv_file, args.asin)
    
    # 导入数据
    skip_existing = args.skip_existing and not args.force
    success = importer.import_data(df, skip_existing=skip_existing)
    
    # 验证导入结果
    if success:
        importer.verify_import(args.asin)
        print(f"\n🎉 数据导入成功完成!")
    else:
        print(f"\n⚠️  数据导入过程中出现错误，请检查日志")
        sys.exit(1)

if __name__ == '__main__':
    main() 