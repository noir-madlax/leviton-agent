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
            
            # 🔥 新增：从category_information中提取类别信息
            if 'category_information' in data and isinstance(data['category_information'], dict):
                logger.info(f"📋 发现 category_information 字段")
                category_info = data['category_information']
                
                # 提取当前类别和父类别信息
                current_category = category_info.get('current_category', {})
                parent_category = category_info.get('parent_category', {})
                
                if isinstance(current_category, dict) and current_category.get('id') and current_category.get('name'):
                    logger.info(f"  处理当前类别: {current_category['name']} (ID: {current_category['id']})")
                    
                    # 构建类别层级：父类别 -> 当前类别
                    hierarchy = []
                    
                    # 如果有父类别信息，先添加父类别
                    if isinstance(parent_category, dict) and parent_category.get('id') and parent_category.get('name'):
                        hierarchy.append({
                            'name': parent_category['name'],
                            'category_id': parent_category['id'],
                            'link': parent_category.get('link', '')
                        })
                        logger.debug(f"    添加父类别: {parent_category['name']} (ID: {parent_category['id']})")
                    
                                         # 清理名称中的 (Current) 后缀
                    current_category_name = current_category['name'].replace('(Current)', '').strip()
                    
                    # 添加当前类别
                    hierarchy.append({
                        'name': current_category_name,
                         'category_id': current_category['id'],
                         'link': current_category.get('link', '')
                     })
                    
                    # 提取类别层级
                    if hierarchy:
                        extracted = self._extract_category_hierarchy(hierarchy, "category_information")
                        categories_to_insert.extend(extracted)
                        logger.info(f"  从 category_information 提取了 {len(extracted)} 个类别")
                else:
                    logger.warning("  ⚠️ category_information 中的 current_category 信息不完整")
                    logger.debug(f"    current_category: {current_category}")
            
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
            
            # 如果既没有category_results也没有search_results，给出警告
            if 'category_results' not in data and 'search_results' not in data:
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
        valid_categories = []  # 用于构建层级关系的有效类别列表
        
        for i, category in enumerate(categories):
            try:
                logger.debug(f"🔍 处理类别 {i+1}/{len(categories)} ({context})")
                
                # 检查当前category的基本结构
                if not isinstance(category, dict):
                    logger.warning(f"  ⚠️ 类别 {i+1} 不是字典类型: {type(category)} ({context})")
                    continue
                    
                if 'name' not in category:
                    logger.warning(f"  ⚠️ 类别 {i+1} 缺少 name 字段 ({context})")
                    logger.debug(f"    可用字段: {list(category.keys())}")
                    continue
                
                # 🔥 修改：允许没有category_id的顶级类别
                category_id = category.get('category_id')
                if not category_id:
                    # 如果是第一级类别且没有category_id，跳过但记录到valid_categories用于构建路径
                    if i == 0:
                        logger.info(f"  📌 顶级类别 '{category['name']}' 没有category_id，跳过插入但保留用于路径构建 ({context})")
                        valid_categories.append(category)
                        continue
                    else:
                        logger.warning(f"  ⚠️ 非顶级类别 {i+1} 缺少 category_id 字段，跳过 ({context})")
                        logger.debug(f"    可用字段: {list(category.keys())}")
                        continue
                
                # 添加到有效类别列表
                valid_categories.append(category)
                
                # 计算层级和父类别ID
                level = len(valid_categories)
                parent_id = None
                
                # 查找最近的有category_id的父类别
                if len(valid_categories) > 1:
                    for j in range(len(valid_categories) - 2, -1, -1):
                        parent_category = valid_categories[j]
                        if isinstance(parent_category, dict) and 'category_id' in parent_category:
                            parent_id = parent_category['category_id']
                            logger.debug(f"  ✅ 找到父类别ID: {parent_id}")
                            break
                
                # 构建完整路径（包括没有category_id的顶级类别）
                path_parts = []
                for valid_cat in valid_categories:
                    if isinstance(valid_cat, dict) and 'name' in valid_cat:
                        path_parts.append(valid_cat['name'])
                
                full_path = ' > '.join(path_parts)
                
                category_record = {
                    'category_id': str(category_id),
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