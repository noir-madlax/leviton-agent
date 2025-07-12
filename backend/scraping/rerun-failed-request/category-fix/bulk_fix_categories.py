"""
批量修复现有JSON文件的类别信息
扫描scraping/data/scraped/amazon/目录下的所有JSON文件，提取类别信息并导入数据库
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from .extract_categories_from_json import CategoryExtractor

logger = logging.getLogger(__name__)

class BulkCategoryFixer:
    """批量类别修复器"""
    
    def __init__(self):
        self.category_extractor = CategoryExtractor()
    
    def find_json_files(self, directory: str) -> List[str]:
        """查找目录下的所有JSON文件"""
        try:
            data_dir = Path(directory)
            if not data_dir.exists():
                logger.warning(f"目录不存在: {directory}")
                return []
            
            # 查找所有JSON文件
            json_files = []
            for json_file in data_dir.glob("*.json"):
                json_files.append(str(json_file))
            
            logger.info(f"找到 {len(json_files)} 个JSON文件")
            return json_files
            
        except Exception as e:
            logger.error(f"查找JSON文件时出错: {e}")
            return []
    
    async def process_all_json_files(self, directory: str) -> Dict[str, Any]:
        """处理目录下的所有JSON文件"""
        try:
            json_files = self.find_json_files(directory)
            
            if not json_files:
                return {
                    'status': 'warning',
                    'message': f'目录 {directory} 中没有找到JSON文件',
                    'total_files': 0,
                    'processed_files': 0,
                    'total_categories_inserted': 0
                }
            
            results = []
            total_categories_inserted = 0
            
            for json_file in json_files:
                logger.info(f"处理文件: {json_file}")
                result = await self.category_extractor.process_json_file(json_file)
                results.append({
                    'file': json_file,
                    'result': result
                })
                
                total_categories_inserted += result.get('categories_inserted', 0)
            
            return {
                'status': 'success',
                'message': f'成功处理 {len(json_files)} 个JSON文件',
                'total_files': len(json_files),
                'processed_files': len(results),
                'total_categories_inserted': total_categories_inserted,
                'details': results
            }
            
        except Exception as e:
            logger.error(f"批量处理JSON文件时出错: {e}")
            return {
                'status': 'error',
                'message': f'批量处理失败: {str(e)}',
                'total_files': 0,
                'processed_files': 0,
                'total_categories_inserted': 0
            }

async def main():
    """主函数 - 批量修复类别信息"""
    logging.basicConfig(level=logging.INFO)
    
    # 设置爬虫数据目录
    scraping_data_dir = Path(__file__).parent.parent.parent / "data" / "scraped" / "amazon"
    
    logger.info(f"开始批量修复类别信息，扫描目录: {scraping_data_dir}")
    
    bulk_fixer = BulkCategoryFixer()
    result = await bulk_fixer.process_all_json_files(str(scraping_data_dir))
    
    logger.info("批量修复完成")
    logger.info(f"结果: {result}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main()) 