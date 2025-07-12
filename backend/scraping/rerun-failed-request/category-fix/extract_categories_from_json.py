"""
从爬虫JSON文件中提取类别信息并写入amazon_categories表
"""
import json
import logging
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any

def _import_category_importer():
    """动态导入CategoryImporter"""
    current_dir = Path(__file__).parent
    category_importer_path = current_dir / "category_importer.py"
    spec = importlib.util.spec_from_file_location("category_importer", category_importer_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CategoryImporter

logger = logging.getLogger(__name__)

class CategoryExtractor:
    """从JSON文件提取类别信息"""
    
    def __init__(self):
        CategoryImporter = _import_category_importer()
        self.category_importer = CategoryImporter()
    
    async def extract_categories_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """从JSON文件提取类别信息"""
        try:
            logger.info(f"开始提取类别信息: {json_file_path}")
            
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            categories_to_insert = []
            
            # 从category_results中提取
            if 'category_results' in data and isinstance(data['category_results'], list):
                for product in data['category_results']:
                    if 'categories' in product and isinstance(product['categories'], list):
                        categories = product['categories']
                        categories_to_insert.extend(self._extract_category_hierarchy(categories))
            
            # 从search_results中提取
            elif 'search_results' in data and isinstance(data['search_results'], list):
                for product in data['search_results']:
                    if 'categories' in product and isinstance(product['categories'], list):
                        categories = product['categories']
                        categories_to_insert.extend(self._extract_category_hierarchy(categories))
            
            # 去重
            unique_categories = self.category_importer.deduplicate_categories(categories_to_insert)
            
            logger.info(f"从 {json_file_path} 提取到 {len(unique_categories)} 个唯一类别")
            
            return unique_categories
            
        except Exception as e:
            logger.error(f"提取类别信息时出错: {e}")
            return []
    
    def _extract_category_hierarchy(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取类别层级信息"""
        category_records = []
        
        for i, category in enumerate(categories):
            if not isinstance(category, dict) or 'category_id' not in category or 'name' not in category:
                continue
                
            level = i + 1
            parent_id = categories[i-1]['category_id'] if i > 0 else None
            
            # 构建完整路径
            path_parts = [cat['name'] for cat in categories[:i+1]]
            full_path = ' > '.join(path_parts)
            
            category_record = {
                'category_id': str(category['category_id']),
                'name': category['name'],
                'parent_category_id': str(parent_id) if parent_id else None,
                'level': level,
                'full_path': full_path,
                'link': category.get('link', '')
            }
            
            category_records.append(category_record)
        
        return category_records
    
    async def process_json_file(self, json_file_path: str) -> Dict[str, Any]:
        """处理单个JSON文件"""
        try:
            # 提取类别信息
            categories = await self.extract_categories_from_json(json_file_path)
            
            if not categories:
                return {
                    'status': 'success',
                    'message': f'文件 {json_file_path} 中没有找到类别信息',
                    'categories_inserted': 0
                }
            
            # 插入数据库
            inserted_count = await self.category_importer.batch_insert_categories(categories)
            
            return {
                'status': 'success',
                'message': f'成功从 {json_file_path} 处理 {inserted_count} 个类别',
                'categories_extracted': len(categories),
                'categories_inserted': inserted_count
            }
            
        except Exception as e:
            logger.error(f"处理JSON文件时出错: {e}")
            return {
                'status': 'error',
                'message': f'处理文件 {json_file_path} 时出错: {str(e)}',
                'categories_inserted': 0
            } 