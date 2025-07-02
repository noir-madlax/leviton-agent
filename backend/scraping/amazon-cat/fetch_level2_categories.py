#!/usr/bin/env python3
"""
Fetch Level 2 Categories for Amazon
获取亚马逊所有一级目录的二级子目录
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Set

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api_client import RainforestCategoryAPI
from category_config import CategoryFetcherConfig


# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(current_dir / "fetch_level2.log")
    ]
)
logger = logging.getLogger(__name__)


class Level2CategoryFetcher:
    """二级类目获取器"""
    
    def __init__(self, run_id: str = "run_com_20250701_191838"):
        """
        初始化
        
        Args:
            run_id: 使用的运行ID，默认使用现有的
        """
        self.run_id = run_id
        self.api_client = RainforestCategoryAPI(delay_seconds=1.5)
        
        # 设置路径
        self.data_root = CategoryFetcherConfig.DATA_ROOT
        self.run_dir = self.data_root / "runs" / self.run_id
        self.raw_api_dir = self.run_dir / "raw_api"
        self.root_categories_file = self.run_dir / "root_categories.json"
        
        # 确保目录存在
        self.raw_api_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized Level2CategoryFetcher for run: {self.run_id}")
        logger.info(f"Raw API dir: {self.raw_api_dir}")
    
    def load_root_categories(self) -> List[Dict[str, Any]]:
        """加载一级目录列表"""
        try:
            with open(self.root_categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            categories = data.get('response_data', {}).get('categories', [])
            logger.info(f"Loaded {len(categories)} root categories")
            
            return categories
        except Exception as e:
            logger.error(f"Failed to load root categories: {e}")
            return []
    
    def get_existing_category_files(self) -> Set[str]:
        """获取已存在的类目文件对应的category_id"""
        existing_ids = set()
        
        for file_path in self.raw_api_dir.glob("category_*.json"):
            # 从文件名提取category_id (去掉 "category_" 前缀和 ".json" 后缀)
            category_id = file_path.stem.replace("category_", "")
            existing_ids.add(category_id)
        
        logger.info(f"Found {len(existing_ids)} existing category files")
        return existing_ids
    
    def get_missing_level1_categories(self) -> List[Dict[str, Any]]:
        """获取缺失的一级目录（还没有API响应文件的）"""
        root_categories = self.load_root_categories()
        existing_ids = self.get_existing_category_files()
        
        missing_categories = []
        existing_level1_categories = []
        
        for category in root_categories:
            category_id = category.get('id', '')
            if category_id not in existing_ids:
                missing_categories.append(category)
                logger.info(f"Missing level 1 category: {category_id} - {category.get('name', 'Unknown')}")
            else:
                existing_level1_categories.append(category)
                logger.debug(f"Found existing level 1 category: {category_id} - {category.get('name', 'Unknown')}")
        
        logger.info(f"Found {len(existing_level1_categories)} existing level 1 categories")
        logger.info(f"Found {len(missing_categories)} missing level 1 categories")
        return missing_categories
    
    async def fetch_category_children(self, category: Dict[str, Any]) -> bool:
        """
        获取指定类目的子类目
        
        Args:
            category: 类目信息
            
        Returns:
            bool: 是否成功
        """
        category_id = category.get('id', '')
        category_name = category.get('name', 'Unknown')
        
        logger.info(f"Fetching children for category: {category_id} - {category_name}")
        
        try:
            # 调用API获取子类目
            api_response = self.api_client.get_category_children(
                parent_id=category_id, 
                domain="amazon.com"
            )
            
            # 保存到文件
            file_path = self.raw_api_dir / f"category_{category_id}.json"
            success = self.api_client.save_response_to_file(api_response, file_path)
            
            if success and api_response.success:
                # 检查响应中的子类目数量
                children_count = 0
                if api_response.response_data and 'categories' in api_response.response_data:
                    children_count = len(api_response.response_data['categories'])
                
                logger.info(f"✅ Successfully fetched {children_count} children for {category_name} (ID: {category_id})")
                return True
            else:
                logger.error(f"❌ Failed to fetch children for {category_name} (ID: {category_id}): {api_response.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception while fetching children for {category_name} (ID: {category_id}): {e}")
            return False
    
    async def fetch_all_missing_level2(self) -> Dict[str, Any]:
        """获取所有缺失的二级目录"""
        start_time = time.time()
        missing_categories = self.get_missing_level1_categories()
        
        if not missing_categories:
            logger.info("🎉 No missing level 1 categories found. All are already fetched!")
            return {
                "success": True,
                "message": "All level 1 categories already have API responses",
                "processed": 0,
                "failed": 0,
                "duration": 0
            }
        
        logger.info(f"🚀 Starting to fetch {len(missing_categories)} missing level 1 categories...")
        
        processed = 0
        failed = 0
        
        for i, category in enumerate(missing_categories, 1):
            category_id = category.get('id', '')
            category_name = category.get('name', 'Unknown')
            
            logger.info(f"📊 Progress: {i}/{len(missing_categories)} - Processing {category_name}")
            
            success = await self.fetch_category_children(category)
            
            if success:
                processed += 1
            else:
                failed += 1
            
            # 显示进度
            percentage = (i / len(missing_categories)) * 100
            logger.info(f"📈 Progress: {percentage:.1f}% ({i}/{len(missing_categories)}) - Success: {processed}, Failed: {failed}")
        
        duration = time.time() - start_time
        
        logger.info(f"🏁 Completed! Processed: {processed}, Failed: {failed}, Duration: {duration:.2f}s")
        
        return {
            "success": True,
            "message": f"Fetch completed. Processed: {processed}, Failed: {failed}",
            "processed": processed,
            "failed": failed,
            "duration": duration,
            "total_categories": len(missing_categories)
        }
    
    def analyze_existing_data(self) -> Dict[str, Any]:
        """分析现有数据的状况"""
        root_categories = self.load_root_categories()
        existing_ids = self.get_existing_category_files()
        
        total_root = len(root_categories)
        
        # 找出已存在的和缺失的一级目录
        existing_categories = []
        missing_categories = []
        
        for category in root_categories:
            category_id = category.get('id', '')
            if category_id in existing_ids:
                existing_categories.append(category)
            else:
                missing_categories.append(category)
        
        existing_level1_count = len(existing_categories)
        missing_level1_count = len(missing_categories)
        total_files_count = len(existing_ids)
        
        analysis = {
            "total_root_categories": total_root,
            "existing_level1_count": existing_level1_count,
            "missing_level1_count": missing_level1_count,
            "total_files_in_raw_api": total_files_count,
            "completion_percentage": (existing_level1_count / total_root) * 100 if total_root > 0 else 0,
            "existing_categories": [
                {"id": cat.get("id"), "name": cat.get("name")} 
                for cat in existing_categories
            ],
            "missing_categories": [
                {"id": cat.get("id"), "name": cat.get("name")} 
                for cat in missing_categories
            ]
        }
        
        logger.info(f"📊 Data Analysis:")
        logger.info(f"   Total root categories: {total_root}")
        logger.info(f"   Existing level 1 API responses: {existing_level1_count}")
        logger.info(f"   Missing level 1 API responses: {missing_level1_count}")
        logger.info(f"   Total files in raw_api: {total_files_count}")
        logger.info(f"   Level 1 completion: {analysis['completion_percentage']:.1f}%")
        
        return analysis


async def main():
    """主函数"""
    print("🔍 Amazon Level 2 Category Fetcher")
    print("=" * 50)
    
    # 创建获取器
    fetcher = Level2CategoryFetcher()
    
    # 先分析现有数据
    print("\n📊 Analyzing existing data...")
    analysis = fetcher.analyze_existing_data()
    
    print(f"\n📋 Analysis Results:")
    print(f"   Total root categories: {analysis['total_root_categories']}")
    print(f"   Level 1 already fetched: {analysis['existing_level1_count']}")
    print(f"   Level 1 missing: {analysis['missing_level1_count']}")
    print(f"   Total files in raw_api: {analysis['total_files_in_raw_api']}")
    print(f"   Level 1 completion: {analysis['completion_percentage']:.1f}%")
    
    if analysis['missing_level1_count'] == 0:
        print("\n🎉 All level 1 categories already have API responses!")
        return
    
    print(f"\n📝 Missing categories:")
    for cat in analysis['missing_categories'][:10]:  # 显示前10个
        print(f"   - {cat['id']}: {cat['name']}")
    
    if len(analysis['missing_categories']) > 10:
        print(f"   ... and {len(analysis['missing_categories']) - 10} more")
    
    # 询问是否继续
    response = input(f"\n❓ Do you want to fetch {analysis['missing_level1_count']} missing level 1 categories? (y/N): ")
    
    if response.lower() not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        return
    
    # 开始获取
    print(f"\n🚀 Starting to fetch {analysis['missing_level1_count']} missing level 1 categories...")
    print("⏳ This may take a while due to API rate limiting...")
    
    result = await fetcher.fetch_all_missing_level2()
    
    print(f"\n✅ Fetch completed!")
    print(f"   Processed: {result['processed']}")
    print(f"   Failed: {result['failed']}")
    print(f"   Duration: {result['duration']:.2f} seconds")
    
    if result['failed'] > 0:
        print(f"\n⚠️  Some categories failed to fetch. Check the logs for details.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation interrupted by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        sys.exit(1) 