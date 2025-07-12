#!/usr/bin/env python3
"""
生产环境调试脚本
快速诊断 category_id 提取问题
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入增强的CategoryExtractor
from extract_categories_from_json import CategoryExtractor

class ProductionDebugger:
    """生产环境调试器"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """设置调试日志"""
        log_file = Path(__file__).parent / "production_debug.log"
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='a', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        print(f"🔍 调试日志文件: {log_file}")
    
    def find_json_files_in_production(self) -> List[str]:
        """在生产环境中查找JSON文件"""
        possible_paths = [
            "/app/scraping/data/scraped/amazon/",  # 容器中的路径
            "/root/scraping/data/scraped/amazon/",  # 另一个可能的路径
            str(Path(__file__).parent.parent.parent / "data" / "scraped" / "amazon"),  # 相对路径
        ]
        
        found_files = []
        
        for base_path in possible_paths:
            path = Path(base_path)
            if path.exists():
                self.logger.info(f"✅ 找到目录: {path}")
                # 查找最近的JSON文件
                json_files = sorted(path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
                for json_file in json_files[:5]:  # 只取最近的5个文件
                    found_files.append(str(json_file))
                    self.logger.info(f"📄 发现JSON文件: {json_file.name} (大小: {json_file.stat().st_size} bytes)")
            else:
                self.logger.debug(f"❌ 目录不存在: {path}")
        
        return found_files
    
    def analyze_json_structure(self, json_file_path: str) -> Dict[str, Any]:
        """分析JSON文件结构"""
        self.logger.info(f"🔍 分析JSON文件结构: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            analysis = {
                'file_path': json_file_path,
                'file_size': Path(json_file_path).stat().st_size,
                'top_level_keys': list(data.keys()),
                'has_category_results': 'category_results' in data,
                'has_search_results': 'search_results' in data,
                'category_results_count': 0,
                'search_results_count': 0,
                'category_structures': [],
                'issues_found': []
            }
            
            # 分析category_results
            if 'category_results' in data and isinstance(data['category_results'], list):
                analysis['category_results_count'] = len(data['category_results'])
                self.logger.info(f"📊 category_results: {len(data['category_results'])} 个产品")
                
                # 分析前几个产品的类别结构
                for i, product in enumerate(data['category_results'][:3]):
                    if 'categories' in product:
                        structure = self._analyze_categories_structure(product['categories'], f"category_results[{i}]")
                        analysis['category_structures'].append(structure)
            
            # 分析search_results
            if 'search_results' in data and isinstance(data['search_results'], list):
                analysis['search_results_count'] = len(data['search_results'])
                self.logger.info(f"🔍 search_results: {len(data['search_results'])} 个产品")
                
                # 分析前几个产品的类别结构
                for i, product in enumerate(data['search_results'][:3]):
                    if 'categories' in product:
                        structure = self._analyze_categories_structure(product['categories'], f"search_results[{i}]")
                        analysis['category_structures'].append(structure)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ 分析JSON文件时出错: {e}")
            return {'error': str(e)}
    
    def _analyze_categories_structure(self, categories: List[Any], context: str) -> Dict[str, Any]:
        """分析单个产品的categories结构"""
        structure = {
            'context': context,
            'count': len(categories) if isinstance(categories, list) else 0,
            'types': [],
            'valid_categories': 0,
            'missing_category_id': 0,
            'missing_name': 0,
            'sample_categories': []
        }
        
        if not isinstance(categories, list):
            structure['error'] = f"categories不是列表类型: {type(categories)}"
            return structure
        
        for i, category in enumerate(categories):
            cat_info = {
                'index': i,
                'type': str(type(category)),
                'has_category_id': False,
                'has_name': False,
                'keys': []
            }
            
            if isinstance(category, dict):
                cat_info['keys'] = list(category.keys())
                cat_info['has_category_id'] = 'category_id' in category
                cat_info['has_name'] = 'name' in category
                
                if cat_info['has_category_id'] and cat_info['has_name']:
                    structure['valid_categories'] += 1
                else:
                    if not cat_info['has_category_id']:
                        structure['missing_category_id'] += 1
                    if not cat_info['has_name']:
                        structure['missing_name'] += 1
            
            # 只保存前3个作为样本
            if i < 3:
                structure['sample_categories'].append(cat_info)
        
        return structure
    
    async def test_extract_categories(self, json_file_path: str) -> Dict[str, Any]:
        """测试类别提取功能"""
        self.logger.info(f"🧪 测试类别提取: {json_file_path}")
        
        try:
            extractor = CategoryExtractor()
            result = await extractor.process_json_file(json_file_path)
            
            self.logger.info(f"✅ 测试完成")
            self.logger.info(f"  状态: {result['status']}")
            self.logger.info(f"  消息: {result['message']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 测试失败: {e}")
            self.logger.error(f"❌ 错误栈:\n{traceback.format_exc()}")
            return {'status': 'error', 'message': str(e)}
    
    def check_environment(self) -> Dict[str, Any]:
        """检查生产环境状态"""
        self.logger.info("🔧 检查生产环境状态...")
        
        env_info = {
            'python_version': sys.version,
            'current_directory': str(Path.cwd()),
            'script_directory': str(Path(__file__).parent),
            'paths_checked': [],
            'permissions': {}
        }
        
        # 检查各种可能的路径
        possible_paths = [
            "/app/scraping/data/scraped/amazon/",
            "/root/scraping/data/scraped/amazon/",
            str(Path(__file__).parent.parent.parent / "data" / "scraped" / "amazon"),
        ]
        
        for path_str in possible_paths:
            path = Path(path_str)
            path_info = {
                'exists': path.exists(),
                'is_dir': path.is_dir() if path.exists() else False,
                'readable': False,
                'writable': False
            }
            
            if path.exists():
                try:
                    # 测试读权限
                    list(path.iterdir())
                    path_info['readable'] = True
                except PermissionError:
                    pass
                
                try:
                    # 测试写权限（创建临时文件）
                    temp_file = path / "temp_test_file"
                    temp_file.touch()
                    temp_file.unlink()
                    path_info['writable'] = True
                except (PermissionError, OSError):
                    pass
            
            env_info['paths_checked'].append({
                'path': path_str,
                'info': path_info
            })
        
        return env_info
    
    async def run_full_diagnosis(self):
        """运行完整诊断"""
        self.logger.info("🚀 开始完整诊断...")
        
        # 1. 检查环境
        env_info = self.check_environment()
        self.logger.info("✅ 环境检查完成")
        
        # 2. 查找JSON文件
        json_files = self.find_json_files_in_production()
        if not json_files:
            self.logger.error("❌ 未找到任何JSON文件")
            return
        
        self.logger.info(f"✅ 找到 {len(json_files)} 个JSON文件")
        
        # 3. 分析第一个JSON文件的结构
        if json_files:
            analysis = self.analyze_json_structure(json_files[0])
            self.logger.info("✅ JSON结构分析完成")
            
            # 4. 测试类别提取
            test_result = await self.test_extract_categories(json_files[0])
            self.logger.info("✅ 类别提取测试完成")
            
            # 5. 输出汇总报告
            self._print_summary_report(env_info, json_files, analysis, test_result)
    
    def _print_summary_report(self, env_info, json_files, analysis, test_result):
        """打印汇总报告"""
        print("\n" + "="*60)
        print("📋 生产环境诊断报告")
        print("="*60)
        
        print(f"\n🔧 环境信息:")
        print(f"  当前目录: {env_info['current_directory']}")
        print(f"  Python版本: {env_info['python_version'][:20]}...")
        
        print(f"\n📁 路径检查:")
        for path_check in env_info['paths_checked']:
            path = path_check['path']
            info = path_check['info']
            status = "✅" if info['exists'] else "❌"
            print(f"  {status} {path}")
            if info['exists']:
                print(f"    - 可读: {'✅' if info['readable'] else '❌'}")
                print(f"    - 可写: {'✅' if info['writable'] else '❌'}")
        
        print(f"\n📄 JSON文件:")
        print(f"  找到文件数: {len(json_files)}")
        if json_files:
            print(f"  测试文件: {Path(json_files[0]).name}")
        
        if 'error' not in analysis:
            print(f"\n📊 JSON结构分析:")
            print(f"  文件大小: {analysis['file_size']} bytes")
            print(f"  顶级键: {analysis['top_level_keys']}")
            print(f"  category_results: {analysis['category_results_count']} 个")
            print(f"  search_results: {analysis['search_results_count']} 个")
            
            print(f"\n🏗️ 类别结构分析:")
            for struct in analysis['category_structures']:
                print(f"  {struct['context']}:")
                print(f"    - 类别数量: {struct['count']}")
                print(f"    - 有效类别: {struct['valid_categories']}")
                print(f"    - 缺少category_id: {struct['missing_category_id']}")
                print(f"    - 缺少name: {struct['missing_name']}")
        
        print(f"\n🧪 提取测试结果:")
        print(f"  状态: {test_result['status']}")
        print(f"  消息: {test_result['message']}")
        if 'categories_extracted' in test_result:
            print(f"  提取类别数: {test_result['categories_extracted']}")
        if 'categories_inserted' in test_result:
            print(f"  插入类别数: {test_result['categories_inserted']}")
        
        print("\n" + "="*60)
        print("📝 建议:")
        if test_result['status'] == 'error':
            print("  ❌ 检查详细日志文件以了解具体错误原因")
        else:
            print("  ✅ 类别提取功能正常工作")
        
        print(f"  📁 查看详细日志: {Path(__file__).parent / 'extract_categories_debug.log'}")
        print(f"  📁 查看调试日志: {Path(__file__).parent / 'production_debug.log'}")

async def main():
    """主函数"""
    debugger = ProductionDebugger()
    await debugger.run_full_diagnosis()

if __name__ == "__main__":
    asyncio.run(main()) 