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

# 设置详细的日志配置
logger = logging.getLogger(__name__)

# 创建文件日志处理器
def setup_detailed_logging():
    """设置详细的日志配置"""
    log_file = Path(__file__).parent / "extract_categories_debug.log"
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    
    return log_file

class CategoryExtractor:
    """从JSON文件提取类别信息"""
    
    def __init__(self):
        # 设置详细日志
        self.log_file = setup_detailed_logging()
        logger.info(f"=== CategoryExtractor 初始化 ===")
        logger.info(f"日志文件: {self.log_file}")
        
        try:
            CategoryImporter = _import_category_importer()
            self.category_importer = CategoryImporter()
            logger.info("✅ CategoryImporter 导入成功")
        except Exception as e:
            logger.error(f"❌ CategoryImporter 导入失败: {e}")
            raise
    
    async def extract_categories_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """从JSON文件提取类别信息"""
        logger.info(f"🚀 开始提取类别信息: {json_file_path}")
        
        try:
            # 检查文件是否存在
            file_path = Path(json_file_path)
            if not file_path.exists():
                logger.error(f"❌ 文件不存在: {json_file_path}")
                return []
            
            logger.info(f"📄 文件大小: {file_path.stat().st_size} bytes")
            
            # 读取JSON文件
            logger.debug("🔄 开始读取JSON文件...")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"✅ JSON文件读取成功")
            logger.debug(f"JSON顶级键: {list(data.keys())}")
            
            categories_to_insert = []
            products_processed = 0
            
            # 从category_results中提取
            if 'category_results' in data and isinstance(data['category_results'], list):
                logger.info(f"📊 发现 category_results，包含 {len(data['category_results'])} 个产品")
                for i, product in enumerate(data['category_results']):
                    logger.debug(f"处理 category_results 产品 {i+1}/{len(data['category_results'])}")
                    if 'categories' in product and isinstance(product['categories'], list):
                        logger.debug(f"  产品 {i+1} 有 {len(product['categories'])} 个类别")
                        categories = product['categories']
                        extracted = self._extract_category_hierarchy(categories, f"category_results[{i}]")
                        categories_to_insert.extend(extracted)
                        products_processed += 1
                    else:
                        logger.debug(f"  产品 {i+1} 没有有效的categories字段")
            
            # 从search_results中提取
            elif 'search_results' in data and isinstance(data['search_results'], list):
                logger.info(f"🔍 发现 search_results，包含 {len(data['search_results'])} 个产品")
                for i, product in enumerate(data['search_results']):
                    logger.debug(f"处理 search_results 产品 {i+1}/{len(data['search_results'])}")
                    if 'categories' in product and isinstance(product['categories'], list):
                        logger.debug(f"  产品 {i+1} 有 {len(product['categories'])} 个类别")
                        categories = product['categories']
                        extracted = self._extract_category_hierarchy(categories, f"search_results[{i}]")
                        categories_to_insert.extend(extracted)
                        products_processed += 1
                    else:
                        logger.debug(f"  产品 {i+1} 没有有效的categories字段")
            else:
                logger.warning("⚠️ 未找到 category_results 或 search_results 字段")
                logger.debug(f"可用的顶级字段: {list(data.keys())}")
            
            logger.info(f"📈 处理统计: 总产品数={products_processed}, 提取的类别数={len(categories_to_insert)}")
            
            # 去重
            logger.debug("🔄 开始去重处理...")
            unique_categories = self.category_importer.deduplicate_categories(categories_to_insert)
            
            logger.info(f"✅ 从 {json_file_path} 提取到 {len(unique_categories)} 个唯一类别")
            logger.info(f"📊 去重效果: {len(categories_to_insert)} -> {len(unique_categories)} (减少 {len(categories_to_insert) - len(unique_categories)} 个)")
            
            return unique_categories
            
        except Exception as e:
            logger.error(f"❌ 提取类别信息时出错: {type(e).__name__}: {e}")
            logger.error(f"❌ 错误发生在文件: {json_file_path}")
            import traceback
            logger.error(f"❌ 完整错误栈:\n{traceback.format_exc()}")
            return []
    
    def _extract_category_hierarchy(self, categories: List[Dict[str, Any]], context: str = "") -> List[Dict[str, Any]]:
        """提取类别层级信息"""
        logger.debug(f"🏗️ 开始提取类别层级 ({context}): {len(categories)} 个类别")
        
        if not categories:
            logger.debug(f"  空类别列表 ({context})")
            return []
        
        # 详细记录每个category的结构
        for i, category in enumerate(categories):
            logger.debug(f"  类别 {i+1}: type={type(category)}, keys={list(category.keys()) if isinstance(category, dict) else 'N/A'}")
            if isinstance(category, dict):
                logger.debug(f"    name={category.get('name', 'N/A')}, category_id={category.get('category_id', 'N/A')}")
        
        category_records = []
        
        for i, category in enumerate(categories):
            try:
                logger.debug(f"🔍 处理类别 {i+1}/{len(categories)} ({context})")
                
                # 检查当前category的基本结构
                if not isinstance(category, dict):
                    logger.warning(f"  ⚠️ 类别 {i+1} 不是字典类型: {type(category)} ({context})")
                    continue
                
                # 检查必要字段
                if 'category_id' not in category:
                    logger.warning(f"  ⚠️ 类别 {i+1} 缺少 category_id 字段 ({context})")
                    logger.debug(f"    可用字段: {list(category.keys())}")
                    continue
                    
                if 'name' not in category:
                    logger.warning(f"  ⚠️ 类别 {i+1} 缺少 name 字段 ({context})")
                    logger.debug(f"    可用字段: {list(category.keys())}")
                    continue
                
                level = i + 1
                parent_id = None
                
                # 安全地获取parent_id
                if i > 0:
                    previous_category = categories[i-1]
                    if isinstance(previous_category, dict) and 'category_id' in previous_category:
                        parent_id = previous_category['category_id']
                        logger.debug(f"  ✅ 找到父类别ID: {parent_id}")
                    else:
                        logger.warning(f"  ⚠️ 前一个类别 ({i}) 没有有效的 category_id 字段 ({context})")
                        if isinstance(previous_category, dict):
                            logger.debug(f"    前一个类别字段: {list(previous_category.keys())}")
                        else:
                            logger.debug(f"    前一个类别类型: {type(previous_category)}")
                
                # 构建完整路径
                path_parts = []
                for j in range(i + 1):
                    if j < len(categories) and isinstance(categories[j], dict) and 'name' in categories[j]:
                        path_parts.append(categories[j]['name'])
                    else:
                        logger.warning(f"  ⚠️ 路径构建时，索引 {j} 的类别无效 ({context})")
                
                full_path = ' > '.join(path_parts)
                
                category_record = {
                    'category_id': str(category['category_id']),
                    'name': category['name'],
                    'parent_category_id': str(parent_id) if parent_id else None,
                    'level': level,
                    'full_path': full_path,
                    'link': category.get('link', '')
                }
                
                logger.debug(f"  ✅ 类别记录创建成功: ID={category_record['category_id']}, 名称={category_record['name']}, 层级={level}")
                category_records.append(category_record)
                
            except Exception as e:
                logger.error(f"  ❌ 处理类别 {i+1} 时出错 ({context}): {type(e).__name__}: {e}")
                logger.error(f"  ❌ 类别数据: {category}")
                import traceback
                logger.error(f"  ❌ 错误栈:\n{traceback.format_exc()}")
                continue
        
        logger.debug(f"🏁 类别层级提取完成 ({context}): 成功提取 {len(category_records)} 个类别记录")
        return category_records
    
    async def process_json_file(self, json_file_path: str) -> Dict[str, Any]:
        """处理单个JSON文件"""
        logger.info(f"🎯 开始处理JSON文件: {json_file_path}")
        
        try:
            # 提取类别信息
            logger.debug("🔄 开始提取类别信息...")
            categories = await self.extract_categories_from_json(json_file_path)
            
            if not categories:
                result = {
                    'status': 'success',
                    'message': f'文件 {json_file_path} 中没有找到类别信息',
                    'categories_inserted': 0
                }
                logger.info(f"⚠️ {result['message']}")
                return result
            
            # 插入数据库
            logger.debug(f"💾 开始插入数据库: {len(categories)} 个类别")
            inserted_count = await self.category_importer.batch_insert_categories(categories)
            
            result = {
                'status': 'success',
                'message': f'成功从 {json_file_path} 处理 {inserted_count} 个类别',
                'categories_extracted': len(categories),
                'categories_inserted': inserted_count
            }
            
            logger.info(f"✅ 处理完成: 提取={len(categories)}, 插入={inserted_count}")
            return result
            
        except Exception as e:
            error_msg = f'处理文件 {json_file_path} 时出错: {str(e)}'
            logger.error(f"❌ {error_msg}")
            import traceback
            logger.error(f"❌ 完整错误栈:\n{traceback.format_exc()}")
            
            return {
                'status': 'error',
                'message': error_msg,
                'categories_inserted': 0
            } 