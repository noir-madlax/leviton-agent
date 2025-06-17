from typing import Dict, Any, Optional
import logging
import asyncio
from app.repositories.scraping_request_repository import ScrapingRequestRepository
from app.repositories.amazon_product_repository import AmazonProductRepository
from app.services.scraping_result_processor import ScrapingResultProcessor
from app.database.connection import get_supabase_service_client

logger = logging.getLogger(__name__)

class DataImportService:
    """数据导入服务"""
    
    def __init__(self):
        # 获取Supabase客户端
        self.supabase_client = get_supabase_service_client()
        
        # 初始化各个组件
        self.processor = ScrapingResultProcessor()
        self.request_repository = ScrapingRequestRepository(self.supabase_client)
        self.product_repository = AmazonProductRepository(self.supabase_client)
    
    async def import_scraping_result(self, json_file_path: str, 
                                   task_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        导入爬取结果到数据库
        
        Args:
            json_file_path: JSON文件路径
            task_info: 任务信息（可选）
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        try:
            logger.info(f"开始导入爬取结果: {json_file_path}")
            
            # 步骤1: 处理JSON文件，转换为数据库格式
            request_data, products_data = await self.processor.process_scraping_result(json_file_path)
            
            if not products_data:
                logger.warning(f"JSON文件中没有产品数据: {json_file_path}")
                return {
                    "status": "warning",
                    "message": "JSON文件中没有产品数据",
                    "products_imported": 0
                }
            
            # 步骤2: 保存爬取请求记录
            logger.info("保存爬取请求记录到数据库...")
            request_id = await self.request_repository.create_scraping_request(request_data)
            
            if not request_id:
                logger.error("创建爬取请求记录失败")
                return {
                    "status": "error",
                    "message": "创建爬取请求记录失败",
                    "products_imported": 0
                }
            
            # 步骤3: 批量保存产品数据
            logger.info(f"批量保存 {len(products_data)} 个产品到数据库...")
            success = await self.product_repository.batch_insert_products(products_data, request_id)
            
            if not success:
                # 如果产品保存失败，更新请求状态为失败
                await self.request_repository.update_request_status(request_id, 'failed')
                logger.error("批量保存产品数据失败")
                return {
                    "status": "error",
                    "message": "批量保存产品数据失败",
                    "products_imported": 0,
                    "request_id": request_id
                }
            
            # 步骤4: 更新请求状态为导入完成
            await self.request_repository.update_request_status(
                request_id, 
                'imported',
                {"products_imported": len(products_data)}
            )
            
            logger.info(f"成功导入爬取结果: {len(products_data)} 个产品，请求ID: {request_id}")
            
            return {
                "status": "success",
                "message": f"成功导入 {len(products_data)} 个产品到批次 {request_id}",
                "products_imported": len(products_data),
                "request_id": request_id,
                "batch_id": request_id,  # 批次ID与请求ID相同
                "request_type": request_data.get('request_type'),
                "search_term": request_data.get('search_term'),
                "category_id": request_data.get('category_id')
            }
            
        except Exception as e:
            logger.error(f"导入爬取结果时出错: {e}")
            return {
                "status": "error",
                "message": f"导入失败: {str(e)}",
                "products_imported": 0
            }
    
    async def retry_import(self, json_file_path: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        重试导入机制
        
        Args:
            json_file_path: JSON文件路径
            max_retries: 最大重试次数
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试导入 (第 {attempt + 1} 次): {json_file_path}")
                result = await self.import_scraping_result(json_file_path)
                
                if result.get("status") == "success":
                    logger.info(f"导入成功 (第 {attempt + 1} 次尝试)")
                    return result
                else:
                    last_error = result.get("message", "未知错误")
                    logger.warning(f"导入失败 (第 {attempt + 1} 次尝试): {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"导入异常 (第 {attempt + 1} 次尝试): {e}")
            
            # 等待后重试
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        logger.error(f"导入最终失败，已重试 {max_retries} 次")
        return {
            "status": "error",
            "message": f"导入失败，已重试 {max_retries} 次。最后错误: {last_error}",
            "products_imported": 0
        }
    
    async def get_import_status(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        获取导入状态
        
        Args:
            request_id: 请求ID
            
        Returns:
            Optional[Dict[str, Any]]: 请求状态信息
        """
        try:
            request_info = await self.request_repository.get_request_by_id(request_id)
            if not request_info:
                return None
            
            products_count = len(await self.product_repository.get_products_by_batch(request_id))
            
            return {
                "request_id": request_id,
                "batch_id": request_id,  # 批次ID与请求ID相同
                "status": request_info.get('status'),
                "request_type": request_info.get('request_type'),
                "search_term": request_info.get('search_term'),
                "category_id": request_info.get('category_id'),
                "products_scraped": request_info.get('products_scraped'),
                "products_in_db": products_count,
                "created_at": request_info.get('created_at'),
                "updated_at": request_info.get('updated_at')
            }
            
        except Exception as e:
            logger.error(f"获取导入状态时出错: {e}")
            return None 