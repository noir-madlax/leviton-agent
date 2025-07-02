#!/usr/bin/env python3
"""
Import Amazon Categories to Database
将亚马逊1级和2级目录数据导入到数据库中

Usage:
    python import_categories_to_db.py [--dry-run] [--force]
    
Options:
    --dry-run: 仅显示将要导入的数据，不实际执行数据库操作
    --force: 强制重新导入，覆盖已存在的数据
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

# 添加项目根目录到Python路径  
# 从 backend/scraping/amazon-cat/script.py 到项目根目录需要向上3级
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.core.database.connection import get_supabase_service_client
except ImportError:
    print("无法导入backend.core.database.connection，请确保在正确的项目目录中运行脚本")
    print(f"当前项目根目录: {project_root}")
    print(f"请从项目根目录运行: python backend/scraping/amazon-cat/import_categories_to_db.py")
    sys.exit(1)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / "import_categories.log")
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class CategoryData:
    """分类数据结构"""
    category_id: str
    name: str
    parent_category_id: Optional[str]
    level: int
    full_path: str
    link: Optional[str] = None


@dataclass
class ImportStats:
    """导入统计信息"""
    total_processed: int = 0
    level1_inserted: int = 0
    level1_updated: int = 0
    level1_errors: int = 0
    level2_inserted: int = 0
    level2_updated: int = 0
    level2_errors: int = 0
    start_time: float = 0
    end_time: float = 0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time if self.end_time > 0 else 0

    @property
    def total_inserted(self) -> int:
        return self.level1_inserted + self.level2_inserted

    @property
    def total_updated(self) -> int:
        return self.level1_updated + self.level2_updated

    @property
    def total_errors(self) -> int:
        return self.level1_errors + self.level2_errors


class CategoryImporter:
    """亚马逊分类导入器"""
    
    def __init__(self, dry_run: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.stats = ImportStats()
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "scraped" / "amazon" / "categories" / "runs" / "run_com_20250701_191838"
        self.root_categories_file = self.data_dir / "root_categories.json"
        self.raw_api_dir = self.data_dir / "raw_api"
        
    def validate_data_files(self) -> bool:
        """验证数据文件是否存在"""
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return False
            
        if not self.root_categories_file.exists():
            logger.error(f"Root categories file not found: {self.root_categories_file}")
            return False
            
        if not self.raw_api_dir.exists():
            logger.error(f"Raw API directory not found: {self.raw_api_dir}")
            return False
            
        logger.info(f"✅ Data files validation passed")
        logger.info(f"   Data directory: {self.data_dir}")
        logger.info(f"   Root categories: {self.root_categories_file}")
        logger.info(f"   Raw API directory: {self.raw_api_dir}")
        
        return True
    
    def load_root_categories(self) -> List[Dict[str, Any]]:
        """加载1级目录数据"""
        try:
            with open(self.root_categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 根据实际文件结构，数据在 response_data.categories 中
            categories = data.get('response_data', {}).get('categories', [])
            logger.info(f"📋 Loaded {len(categories)} root categories")
            return categories
            
        except Exception as e:
            logger.error(f"Failed to load root categories: {e}")
            return []
    
    def load_level2_categories(self, level1_category_id: str) -> List[Dict[str, Any]]:
        """加载指定1级目录的2级子目录"""
        api_file = self.raw_api_dir / f"category_{level1_category_id}.json"
        
        if not api_file.exists():
            logger.warning(f"API file not found for category {level1_category_id}: {api_file}")
            return []
            
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 从API响应中提取子分类
            sub_categories = []
            if 'response_data' in data and 'categories' in data['response_data']:
                sub_categories = data['response_data']['categories']
            elif 'categories' in data:
                sub_categories = data['categories']
                
            logger.debug(f"   Found {len(sub_categories)} level 2 categories for {level1_category_id}")
            return sub_categories
            
        except Exception as e:
            logger.error(f"Failed to load level 2 categories for {level1_category_id}: {e}")
            return []
    
    def prepare_category_data(self) -> Tuple[List[CategoryData], List[CategoryData]]:
        """准备分类数据"""
        level1_data = []
        level2_data = []
        
        # 加载1级目录
        root_categories = self.load_root_categories()
        if not root_categories:
            logger.error("No root categories loaded")
            return level1_data, level2_data
        
        logger.info(f"🔄 Processing {len(root_categories)} level 1 categories...")
        
        for category in root_categories:
            category_id = category.get('id', '')
            name = category.get('name', '')
            link = category.get('link', '')
            
            if not category_id or not name:
                logger.warning(f"Skipping invalid level 1 category: {category}")
                continue
                
            # 添加1级目录
            level1_category = CategoryData(
                category_id=category_id,
                name=name,
                parent_category_id=None,
                level=1,
                full_path=name,
                link=link
            )
            level1_data.append(level1_category)
            
            # 加载并处理2级子目录
            level2_categories = self.load_level2_categories(category_id)
            
            for sub_category in level2_categories:
                sub_id = sub_category.get('id', '')
                sub_name = sub_category.get('name', '')
                sub_link = sub_category.get('link', '')
                
                if not sub_id or not sub_name:
                    logger.warning(f"Skipping invalid level 2 category: {sub_category}")
                    continue
                    
                level2_category = CategoryData(
                    category_id=sub_id,
                    name=sub_name,
                    parent_category_id=category_id,
                    level=2,
                    full_path=f"{name} > {sub_name}",
                    link=sub_link
                )
                level2_data.append(level2_category)
        
        logger.info(f"📊 Prepared data summary:")
        logger.info(f"   Level 1 categories: {len(level1_data)}")
        logger.info(f"   Level 2 categories: {len(level2_data)}")
        
        return level1_data, level2_data
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            client = get_supabase_service_client()
            logger.info("Successfully connected to Supabase database")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def insert_categories_batch(self, client, categories: List[CategoryData], level: int) -> Tuple[int, int, int]:
        """批量插入分类数据"""
        if not categories:
            return 0, 0, 0
            
        inserted_count = 0
        updated_count = 0
        error_count = 0
        
        # 准备批量数据
        batch_data = []
        for category in categories:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would insert/update: {category.category_id} - {category.name}")
                inserted_count += 1
                continue
                
            # 准备数据行
            current_time = datetime.utcnow().isoformat()
            row_data = {
                'category_id': category.category_id,
                'name': category.name,
                'parent_category_id': category.parent_category_id,
                'level': category.level,
                'full_path': category.full_path,
                'link': category.link,
                'created_at': current_time,
                'updated_at': current_time
            }
            batch_data.append(row_data)
        
        if self.dry_run or not batch_data:
            return inserted_count, updated_count, error_count
        
        # 执行批量UPSERT
        try:
            # Supabase的upsert方法会自动处理INSERT或UPDATE
            result = client.table('amazon_categories').upsert(
                batch_data,
                on_conflict='category_id'
            ).execute()
            
            if result.data:
                # 所有操作都成功，计为插入（Supabase不区分插入和更新的返回）
                inserted_count = len(result.data)
                logger.info(f"✅ Level {level} batch completed: {inserted_count} records processed")
                
                # 记录详细信息
                for i, category in enumerate(categories[:len(result.data)]):
                    logger.debug(f"✅ Processed level {level}: {category.name}")
            else:
                error_count = len(batch_data)
                logger.error(f"❌ No data returned from upsert for level {level}")
                
        except Exception as e:
            error_count = len(batch_data)
            logger.error(f"❌ Batch upsert failed for level {level}: {e}")
            
        return inserted_count, updated_count, error_count
    
    def run_import(self) -> ImportStats:
        """运行导入过程"""
        self.stats.start_time = time.time()
        
        logger.info("🚀 Starting Amazon categories import...")
        logger.info(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE IMPORT'}")
        logger.info(f"   Force overwrite: {self.force}")
        
        # 验证数据文件
        if not self.validate_data_files():
            return self.stats
        
        # 准备数据
        level1_data, level2_data = self.prepare_category_data()
        if not level1_data:
            logger.error("No valid level 1 categories found")
            return self.stats
        
        self.stats.total_processed = len(level1_data) + len(level2_data)
        
        if self.dry_run:
            logger.info(f"🔍 DRY RUN - Would process {self.stats.total_processed} categories")
            self.stats.level1_inserted = len(level1_data)
            self.stats.level2_inserted = len(level2_data)
            self.stats.end_time = time.time()
            return self.stats
        
        # 连接数据库并导入
        try:
            client = self.get_db_connection()
            
            # 先导入1级目录
            logger.info("📥 Importing level 1 categories...")
            l1_inserted, l1_updated, l1_errors = self.insert_categories_batch(client, level1_data, 1)
            self.stats.level1_inserted = l1_inserted
            self.stats.level1_updated = l1_updated
            self.stats.level1_errors = l1_errors
            
            # 再导入2级目录
            logger.info("📥 Importing level 2 categories...")
            l2_inserted, l2_updated, l2_errors = self.insert_categories_batch(client, level2_data, 2)
            self.stats.level2_inserted = l2_inserted
            self.stats.level2_updated = l2_updated
            self.stats.level2_errors = l2_errors
                
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            
        self.stats.end_time = time.time()
        return self.stats
    
    def print_summary(self):
        """打印导入总结"""
        print(f"\n{'='*60}")
        print(f"📊 IMPORT SUMMARY")
        print(f"{'='*60}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE IMPORT'}")
        print(f"Duration: {self.stats.duration:.2f} seconds")
        print(f"")
        print(f"📈 Level 1 Categories:")
        print(f"   Inserted: {self.stats.level1_inserted}")
        print(f"   Updated:  {self.stats.level1_updated}")
        print(f"   Errors:   {self.stats.level1_errors}")
        print(f"")
        print(f"📈 Level 2 Categories:")
        print(f"   Inserted: {self.stats.level2_inserted}")
        print(f"   Updated:  {self.stats.level2_updated}")  
        print(f"   Errors:   {self.stats.level2_errors}")
        print(f"")
        print(f"🎯 Totals:")
        print(f"   Total Processed: {self.stats.total_processed}")
        print(f"   Total Inserted:  {self.stats.total_inserted}")
        print(f"   Total Updated:   {self.stats.total_updated}")
        print(f"   Total Errors:    {self.stats.total_errors}")
        print(f"")
        
        if self.stats.total_errors == 0:
            print("🎉 Import completed successfully!")
        else:
            print(f"⚠️  Import completed with {self.stats.total_errors} errors")
        
        print(f"{'='*60}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Import Amazon categories to database")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without executing')
    parser.add_argument('--force', action='store_true', help='Force reimport, overwrite existing data')
    
    args = parser.parse_args()
    
    try:
        importer = CategoryImporter(dry_run=args.dry_run, force=args.force)
        stats = importer.run_import()
        importer.print_summary()
        
        # 返回合适的退出码
        sys.exit(0 if stats.total_errors == 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("\n❌ Import cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 