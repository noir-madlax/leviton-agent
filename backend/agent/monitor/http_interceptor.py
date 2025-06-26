"""
HTTP请求拦截器 - 用于监控smolagents的网络请求
"""
import logging
import json
import time
from typing import Any, Dict, Optional
import httpx
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class HTTPRequestInterceptor:
    """HTTP请求拦截器，专门用于监控和记录网络请求"""
    
    def __init__(self, log_requests=True, log_responses=False, max_body_length=2000):
        """
        初始化HTTP拦截器
        
        Args:
            log_requests: 是否记录请求详情
            log_responses: 是否记录响应详情
            max_body_length: 请求/响应体最大显示长度（字符数）
        """
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.max_body_length = max_body_length
        self.setup_interceptors()
        
        config_info = []
        if self.log_requests:
            config_info.append("记录请求")
        if self.log_responses:
            config_info.append("记录响应")
        
        logger.info(f"🔍 HTTP请求拦截器已启动 - 配置: {' + '.join(config_info) if config_info else '仅记录基本信息'}")
    
    def setup_interceptors(self):
        """设置所有HTTP库的拦截器"""
        # 只要启用了请求或响应记录，就设置拦截器
        if self.log_requests or self.log_responses:
            self.setup_httpx_interceptor()
            self.setup_requests_interceptor()
    
    def setup_httpx_interceptor(self):
        """设置 httpx 库拦截器（smolagents主要使用的HTTP库）"""
        # 保存原始方法
        original_send = httpx.Client.send
        original_async_send = httpx.AsyncClient.send
        
        def intercept_httpx_sync(client, request, **kwargs):
            """拦截同步httpx请求"""
            if self.log_requests:
                self._log_request(request, "HTTPX-SYNC")
            
            start_time = time.time()
            response = original_send(client, request, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            if self.log_responses:
                self._log_response(response, duration, "HTTPX-SYNC")
            elif not self.log_requests:  # 如果都没开启详细记录，至少显示基本信息
                logger.info(f"📥 [HTTPX-SYNC] {request.method} {request.url} → {response.status_code} | 耗时: {duration:.2f}ms")
            
            return response
        
        async def intercept_httpx_async(client, request, **kwargs):
            """拦截异步httpx请求"""
            if self.log_requests:
                self._log_request(request, "HTTPX-ASYNC")
            
            start_time = time.time()
            response = await original_async_send(client, request, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            if self.log_responses:
                self._log_response(response, duration, "HTTPX-ASYNC")
            elif not self.log_requests:  # 如果都没开启详细记录，至少显示基本信息
                logger.info(f"📥 [HTTPX-ASYNC] {request.method} {request.url} → {response.status_code} | 耗时: {duration:.2f}ms")
            
            return response
        
        # 替换原方法
        httpx.Client.send = intercept_httpx_sync
        httpx.AsyncClient.send = intercept_httpx_async
    
    def setup_requests_interceptor(self):
        """设置 requests 库拦截器"""
        original_request = requests.Session.request
        
        def intercept_requests(session, method, url, **kwargs):
            """拦截requests请求"""
            # 构造请求对象用于日志记录
            class RequestProxy:
                def __init__(self, method, url, **kwargs):
                    self.method = method.upper()
                    self.url = url
                    self.headers = kwargs.get('headers', {})
                    self.content = None
                    
                    # 处理请求体
                    if 'json' in kwargs:
                        self.content = json.dumps(kwargs['json']).encode()
                        if 'content-type' not in {k.lower() for k in self.headers.keys()}:
                            self.headers['Content-Type'] = 'application/json'
                    elif 'data' in kwargs:
                        self.content = str(kwargs['data']).encode()
            
            request_proxy = RequestProxy(method, url, **kwargs)
            if self.log_requests:
                self._log_request(request_proxy, "REQUESTS")
            
            start_time = time.time()
            response = original_request(session, method, url, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            if self.log_responses:
                self._log_response(response, duration, "REQUESTS")
            elif not self.log_requests:  # 如果都没开启详细记录，至少显示基本信息
                logger.info(f"📥 [REQUESTS] {method.upper()} {url} → {response.status_code} | 耗时: {duration:.2f}ms")
            
            return response
        
        requests.Session.request = intercept_requests
    
    def _log_request(self, request, client_type):
        """记录请求详情"""
        try:
            logger.info("=" * 80)
            logger.info(f"🚀 [{client_type}] HTTP请求发送")
            logger.info(f"📍 URL: {request.url}")
            logger.info(f"🔧 方法: {request.method}")
            
            # 记录请求头
            logger.info("📋 请求头:")
            for key, value in request.headers.items():
                # 隐藏敏感信息
                if any(sensitive in key.lower() for sensitive in ['authorization', 'api-key', 'token']):
                    masked_value = f"{'*' * 8}...{str(value)[-4:]}" if len(str(value)) > 4 else "****"
                    logger.info(f"  {key}: {masked_value}")
                else:
                    logger.info(f"  {key}: {value}")
            
            # 记录请求体
            if hasattr(request, 'content') and request.content:
                try:
                    content_type = request.headers.get('content-type', '').lower()
                    if 'application/json' in content_type:
                        if isinstance(request.content, bytes):
                            content_str = request.content.decode('utf-8')
                        else:
                            content_str = str(request.content)
                        
                        content_json = json.loads(content_str)
                        logger.info("📦 请求体(JSON):")
                        logger.info(json.dumps(content_json, indent=2, ensure_ascii=False))
                    else:
                        content_preview = str(request.content)[:500]
                        logger.info(f"📦 请求体: {content_preview}...")
                except Exception as e:
                    content_preview = str(request.content)[:200] if request.content else "无内容"
                    logger.info(f"📦 请求体(解析失败): {content_preview}...")
            else:
                logger.info("📦 请求体: 无内容")
                
            logger.info("-" * 40)
            
        except Exception as e:
            logger.error(f"记录请求时出错: {e}")
    
    def _log_response(self, response, duration, client_type):
        """记录响应详情"""
        try:
            logger.info("=" * 80)
            logger.info(f"📥 [{client_type}] HTTP响应接收")
            logger.info(f"⚡ 耗时: {duration:.2f}ms")
            logger.info(f"📊 状态码: {response.status_code}")
            
            # 记录响应头
            logger.info("📋 响应头:")
            response_headers = getattr(response, 'headers', {})
            for key, value in response_headers.items():
                logger.info(f"  {key}: {value}")
            
            # 记录响应体
            self._log_response_body(response, response_headers)
            
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"记录响应时出错: {e}")
    
    def _log_response_body(self, response, headers):
        """记录响应体内容"""
        try:
            content_type = headers.get('content-type', '').lower()
            
            # 处理JSON响应
            if 'application/json' in content_type:
                self._log_json_response(response)
            
            # 处理文本响应
            elif any(text_type in content_type for text_type in ['text/', 'application/xml', 'application/javascript']):
                self._log_text_response(response)
            
            # 处理流式响应
            elif 'text/event-stream' in content_type or 'application/stream' in content_type:
                logger.info("📦 响应体: 流式数据（不显示内容）")
            
            # 处理二进制响应
            elif any(binary_type in content_type for binary_type in ['image/', 'video/', 'audio/', 'application/octet-stream']):
                content_length = headers.get('content-length', '未知')
                logger.info(f"📦 响应体: 二进制数据 (长度: {content_length} 字节)")
            
            # 其他类型
            else:
                self._log_unknown_response(response, content_type)
                
        except Exception as e:
            logger.info(f"📦 响应体解析失败: {e}")
            # 尝试显示原始内容
            try:
                if hasattr(response, 'content'):
                    raw_preview = str(response.content)[:200]
                    logger.info(f"📦 原始响应体: {raw_preview}...")
            except:
                pass
    
    def _log_json_response(self, response):
        """记录JSON格式的响应体"""
        try:
            if hasattr(response, 'json'):
                # httpx 和 requests 都有 json() 方法
                response_json = response.json()
                logger.info("📦 响应体(JSON):")
                
                # 限制JSON输出长度
                json_str = json.dumps(response_json, indent=2, ensure_ascii=False)
                if len(json_str) > self.max_body_length:
                    truncated_json = json_str[:self.max_body_length]
                    logger.info(f"{truncated_json}...")
                    logger.info(f"📏 (响应体已截断，总长度: {len(json_str)} 字符)")
                else:
                    logger.info(json_str)
            
            elif hasattr(response, 'text'):
                # 尝试解析文本内容为JSON
                text_content = response.text
                response_json = json.loads(text_content)
                logger.info("📦 响应体(JSON):")
                
                json_str = json.dumps(response_json, indent=2, ensure_ascii=False)
                if len(json_str) > self.max_body_length:
                    truncated_json = json_str[:self.max_body_length]
                    logger.info(f"{truncated_json}...")
                    logger.info(f"📏 (响应体已截断，总长度: {len(json_str)} 字符)")
                else:
                    logger.info(json_str)
            else:
                logger.info("📦 响应体: JSON格式但无法解析")
                
        except json.JSONDecodeError as e:
            logger.info(f"📦 响应体: JSON解析失败 - {e}")
            # 尝试显示原始文本
            if hasattr(response, 'text'):
                text_preview = response.text[:300]
                logger.info(f"📦 原始文本: {text_preview}...")
        except Exception as e:
            logger.info(f"📦 响应体: JSON处理失败 - {e}")
    
    def _log_text_response(self, response):
        """记录文本格式的响应体"""
        try:
            if hasattr(response, 'text'):
                text_content = response.text
                if len(text_content) > self.max_body_length:
                    truncated_text = text_content[:self.max_body_length]
                    logger.info(f"📦 响应体(Text): {truncated_text}...")
                    logger.info(f"📏 (响应体已截断，总长度: {len(text_content)} 字符)")
                else:
                    logger.info(f"📦 响应体(Text): {text_content}")
            else:
                logger.info("📦 响应体: 文本格式但无法读取")
        except Exception as e:
            logger.info(f"📦 响应体: 文本处理失败 - {e}")
    
    def _log_unknown_response(self, response, content_type):
        """记录未知格式的响应体"""
        try:
            logger.info(f"📦 响应体: 未知格式 ({content_type})")
            
            # 尝试以文本形式显示
            if hasattr(response, 'text'):
                text_preview = response.text[:200]
                logger.info(f"📦 预览: {text_preview}...")
            elif hasattr(response, 'content'):
                content_preview = str(response.content)[:200]
                logger.info(f"📦 预览: {content_preview}...")
            else:
                logger.info("📦 无法预览响应内容")
        except Exception as e:
            logger.info(f"📦 响应体: 处理失败 - {e}")

def create_interceptor(log_requests=True, log_responses=False, max_body_length=2000):
    """
    创建HTTP请求拦截器实例
    
    Args:
        log_requests: 是否记录请求详情
        log_responses: 是否记录响应详情
        max_body_length: 请求/响应体最大显示长度（字符数）
    
    Returns:
        HTTPRequestInterceptor: 拦截器实例
    """
    return HTTPRequestInterceptor(
        log_requests=log_requests, 
        log_responses=log_responses,
        max_body_length=max_body_length
    ) 