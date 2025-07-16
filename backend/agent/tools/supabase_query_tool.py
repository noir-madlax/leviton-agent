"""
Supabase 数据库查询工具 - 专门用于安全的数据库查询操作
只允许 SELECT 查询，禁止任何修改操作（INSERT、UPDATE、DELETE、DROP 等）
使用 RPC 函数直接执行 SQL 查询，支持完整的 SQL 功能
"""
import logging
import json
import re
import time
from typing import Dict, Any, Optional, List, Union
from smolagents import Tool
from core.database.connection import get_supabase_service_client
from supabase import Client

logger = logging.getLogger(__name__)

class SupabaseQueryTool(Tool):
    """Supabase 数据库查询工具 - 只读查询专用，使用 RPC 直接执行 SQL"""
    
    name = "supabase_query"
    description = """执行 Supabase 数据库 SELECT 查询的工具。专门用于数据分析和 BI 查询。
    
    ⚠️ 安全限制：
    - 只允许 SELECT 查询操作
    - 禁止任何修改操作（INSERT、UPDATE、DELETE、DROP 等）
    - 禁止 DDL 操作（CREATE、ALTER、DROP 等）
    
    使用方法：
    直接传入 SELECT SQL 语句即可，工具会验证安全性并执行查询。
    支持完整的 SQL 功能，包括：
    - 复杂 JOIN 查询
    - 子查询和 CTE
    - 窗口函数
    - 聚合函数
    - 所有 PostgreSQL SELECT 功能
    
    示例 SQL：
    - SELECT * FROM projects LIMIT 10
    - SELECT platform_id, title, price_usd FROM product_wide_table WHERE price_usd > 50 ORDER BY price_usd DESC LIMIT 20
    - SELECT category, COUNT(*) as count FROM product_wide_table GROUP BY category
    - SELECT AVG(price_usd), MAX(price_usd) FROM product_wide_table WHERE category = 'Electronics'
    - SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.table1_id
    - WITH ranked_products AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY price_usd DESC) as rn FROM product_wide_table) SELECT * FROM ranked_products WHERE rn <= 5
    """
    
    inputs = {
        "sql_query": {
            "type": "string", 
            "description": "要执行的 SELECT SQL 查询语句。必须是有效的 PostgreSQL SELECT 语句。"
        }
    }
    
    output_type = "string"
    
    def __init__(self):
        super().__init__()
        self.supabase_client: Optional[Client] = None
        self._init_client()
    
    def _init_client(self):
        """初始化 Supabase 客户端"""
        try:
            self.supabase_client = get_supabase_service_client()
            logger.info("✅ Supabase 客户端初始化成功")
        except Exception as e:
            logger.error(f"❌ Supabase 客户端初始化失败: {e}")
            self.supabase_client = None
    
    def _validate_sql_security(self, sql: str) -> bool:
        """验证 SQL 查询的安全性 - 客户端侧基础验证"""
        if not sql or not sql.strip():
            return False
        
        # 转换为小写进行检查
        sql_lower = sql.lower().strip()
        
        # 检查是否以 SELECT 开头
        if not sql_lower.startswith('select'):
            logger.warning(f"❌ 非 SELECT 语句被拒绝: {sql[:50]}...")
            return False
        
        # 危险关键词黑名单（基础检查，主要验证在 RPC 函数中）
        dangerous_keywords = [
            'insert', 'update', 'delete', 'drop', 'create', 'alter', 
            'truncate', 'replace', 'merge', 'grant', 'revoke',
            'exec', 'execute', 'call', 'declare', 'set',
            'begin', 'commit', 'rollback', 'savepoint',
            'copy', 'bulk', 'load', 'import', 'export'
        ]
        
        # 检查是否包含危险关键词
        for keyword in dangerous_keywords:
            # 使用单词边界检查，避免误报
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, sql_lower):
                logger.warning(f"❌ 包含危险关键词 '{keyword}' 的查询被拒绝: {sql[:50]}...")
                return False
        
        # 检查是否包含分号后的其他语句（防止 SQL 注入）
        semicolon_parts = sql.split(';')
        if len(semicolon_parts) > 2:  # 允许最后有一个空的分号
            logger.warning(f"❌ 包含多条语句的查询被拒绝: {sql[:50]}...")
            return False
        
        if len(semicolon_parts) == 2 and semicolon_parts[1].strip():
            logger.warning(f"❌ 分号后包含其他语句的查询被拒绝: {sql[:50]}...")
            return False
        
        return True
    
    def _execute_sql_via_rpc(self, sql_query: str) -> Dict[str, Any]:
        """通过 RPC 函数执行 SQL 查询"""
        try:
            # 清理 SQL 查询
            cleaned_sql = sql_query.strip()
            if cleaned_sql.endswith(';'):
                cleaned_sql = cleaned_sql[:-1]
            
            # 调用 RPC 函数
            response = self.supabase_client.rpc('execute_safe_query', {
                'query_text': cleaned_sql
            }).execute()
            
            # 处理响应
            if hasattr(response, 'data') and response.data is not None:
                # 提取结果数据
                results = []
                for row in response.data:
                    if 'result' in row and row['result'] is not None:
                        results.append(row['result'])
                
                return {
                    'success': True,
                    'data': results,
                    'record_count': len(results),
                    'raw_response': response.data
                }
            else:
                return {
                    'success': True,
                    'data': [],
                    'record_count': 0,
                    'raw_response': response.data
                }
                
        except Exception as e:
            logger.error(f"RPC 执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'record_count': 0
            }
    
    def _format_query_result(self, data: Any, query: str, success: bool = True, 
                           error: str = None, execution_time: float = None) -> str:
        """格式化查询结果为 JSON 字符串"""
        from datetime import datetime
        
        result = {
            "success": success,
            "query": query[:500] + "..." if len(query) > 500 else query,
            "timestamp": datetime.now().isoformat() + "Z",
        }
        
        if success:
            result.update({
                "data": data,
                "record_count": len(data) if isinstance(data, list) else 1,
                "execution_time_ms": round(execution_time * 1000, 2) if execution_time else None
            })
        else:
            result.update({
                "error": error,
                "data": None,
                "record_count": 0
            })
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def forward(self, sql_query: str) -> str:
        """执行 SQL 查询 - 使用 RPC 函数直接执行"""
        if not self.supabase_client:
            logger.error("❌ Supabase 客户端未初始化")
            return self._format_query_result(
                None, sql_query, False, 
                "Supabase 客户端未初始化，请检查数据库连接配置"
            )
        
        # 客户端侧基础安全验证
        if not self._validate_sql_security(sql_query):
            return self._format_query_result(
                None, sql_query, False,
                "SQL 查询不符合安全要求，只允许 SELECT 查询"
            )
        
        try:
            logger.info(f"🔍 执行 SQL 查询: {sql_query}")
            start_time = time.time()
            
            # 通过 RPC 函数执行查询
            result = self._execute_sql_via_rpc(sql_query)
            
            execution_time = time.time() - start_time
            
            if result['success']:
                logger.info(f"✅ 查询成功，返回 {result['record_count']} 条记录")
                return self._format_query_result(
                    result['data'], sql_query, True, None, execution_time
                )
            else:
                logger.error(f"❌ 查询执行失败: {result['error']}")
                
                # 尝试提供更友好的错误信息
                error_message = result['error']
                if "relation" in error_message and "does not exist" in error_message:
                    error_message = "表或视图不存在，请检查表名是否正确"
                elif "syntax error" in error_message.lower():
                    error_message = "SQL 语法错误，请检查查询语句"
                elif "permission" in error_message.lower():
                    error_message = "权限不足，无法访问指定的数据"
                elif "dangerous keyword" in error_message.lower():
                    error_message = "查询包含不安全的关键词，只允许 SELECT 查询"
                elif "multiple statements" in error_message.lower():
                    error_message = "不允许多条语句，只能执行单个 SELECT 查询"
                
                return self._format_query_result(None, sql_query, False, error_message)
        
        except Exception as e:
            logger.error(f"❌ 查询执行异常: {e}")
            return self._format_query_result(None, sql_query, False, f"系统错误: {str(e)}")

# 导出工具
__all__ = ['SupabaseQueryTool'] 