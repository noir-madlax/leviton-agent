#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
从环境变量或配置文件加载配置
"""

import os
from typing import Optional

def load_config():
    """加载配置"""
    # 尝试加载环境变量配置文件
    config_file = os.path.join(os.path.dirname(__file__), 'config.env')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    return {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
        
        # 新的数据路径配置
        'PRODUCT_DATA_DIR': os.getenv('PRODUCT_DATA_DIR', '../backend/data/product-data'),
        'REVIEW_DATA_DIR': os.getenv('REVIEW_DATA_DIR', '../backend/data/review-by-meta-structure'),
        'META_DATA_DIR': os.getenv('META_DATA_DIR', '../backend/data/product-meta-data'),
        
        # 通用配置
        'BATCH_SIZE': int(os.getenv('BATCH_SIZE', '50')),
        'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true'
    }

def get_data_file_path(file_type: str, filename: str) -> str:
    """获取数据文件的完整路径"""
    config = load_config()
    
    if file_type == 'product':
        return os.path.join(config['PRODUCT_DATA_DIR'], filename)
    elif file_type == 'review':
        return os.path.join(config['REVIEW_DATA_DIR'], filename)
    elif file_type == 'meta':
        return os.path.join(config['META_DATA_DIR'], filename)
    else:
        raise ValueError(f"未知的文件类型: {file_type}")

def validate_config(config: dict) -> bool:
    """验证配置是否完整"""
    required_fields = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        print(f"错误: 缺少必要的配置项: {', '.join(missing_fields)}")
        print("请检查环境变量或config.env文件")
        return False
    
    if 'your_supabase' in config['SUPABASE_KEY']:
        print("错误: 请设置正确的SUPABASE_KEY")
        print("使用MCP工具获取: mcp_agent-test_get_anon_key")
        return False
    
    return True 