"""
流式响应处理器 - 保持原有逻辑完全不变
"""
import asyncio
import json
import logging
from typing import AsyncGenerator
from config import settings
from agent.core.agent_manager import get_agent_manager
from agent.services.query_processor import get_query_processor
from agent.validators.chart_validator import is_valid_json

logger = logging.getLogger(__name__)

async def stream_agent_response(query: str) -> AsyncGenerator[str, None]:
    """
    运行 smolagents 代理并通过 SSE 流式输出结果 - 保持原有逻辑完全不变
    """
    agent_manager = get_agent_manager()
    query_processor = get_query_processor()
    
    if not agent_manager.is_ready():
        if agent_manager.get_init_error():
            yield f"data: {json.dumps({'error': f'Agent 初始化失败: {agent_manager.get_init_error()}'}, ensure_ascii=False)}\n\n"
        else:
            yield f"data: {json.dumps({'error': 'Agent 未初始化'}, ensure_ascii=False)}\n\n"
        return
    
    try:
        logger.info(f"开始处理查询: {query}")
        
        # 发送开始信号
        yield f"data: {json.dumps({'status': 'started', 'message': '开始处理查询...'}, ensure_ascii=False)}\n\n"
        
        try:
            
            # 运行代理任务，设置超时
            logger.info("正在调用 agent.run...")
            agent = agent_manager.get_agent()
            result = await asyncio.wait_for(
                asyncio.to_thread(agent.run, query),
                timeout=settings.AGENT_TIMEOUT
            )
            logger.info(f"agent.run 执行完成，结果类型: {type(result)}")
            
            # 发送调试信息
            yield f"data: {json.dumps({'status': 'debug', 'message': f'agent.run 执行完成，结果类型: {type(result).__name__}'}, ensure_ascii=False)}\n\n"
            
        except asyncio.TimeoutError:
            logger.error(f"agent.run 执行超时 ({settings.AGENT_TIMEOUT}秒)")
            yield f"data: {json.dumps({'status': 'error', 'error': f'Agent 执行超时 ({settings.AGENT_TIMEOUT}秒)'}, ensure_ascii=False)}\n\n"
            return
        except Exception as agent_error:
            logger.error(f"agent.run 执行失败: {agent_error}")
            yield f"data: {json.dumps({'status': 'error', 'error': f'Agent 执行失败: {str(agent_error)}'}, ensure_ascii=False)}\n\n"
            return
        
        # 将结果分块发送
        if is_valid_json(result):
            logger.info("结果成功解析为 JSON 格式！，直接发送结果")
            # 直接发送 JSON 字符串，不要再次序列化
            yield f"data: {json.dumps({'status': 'streaming', 'message': result}, ensure_ascii=False)}\n\n"
        elif isinstance(result, str):
            # 检查是否包含 RechartScript 脚本块
            if '[RechartScript]' in result and '[/RechartScript]' in result:
                # 分割文本，提取脚本块
                parts = result.split('[RechartScript]')
                
                # 处理脚本块之前的文本
                if parts[0].strip():
                    sentences = parts[0].split('。')
                    for i, sentence in enumerate(sentences):
                        if sentence.strip():
                            chunk_data = {
                                'status': 'streaming',
                                'message': sentence.strip() + ('。' if i < len(sentences) - 1 else ''),
                                'chunk_index': i
                            }                 
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(settings.STREAM_DELAY)
                
                # 处理脚本块
                script_part = parts[1].split('[/RechartScript]')[0]
                if script_part.strip():
                    script_data = {
                        'status': 'rechart',
                        'message': script_part.strip()
                    }
                    yield f"data: {json.dumps(script_data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(settings.STREAM_DELAY)
                
                # 处理脚本块之后的文本
                remaining_text = parts[1].split('[/RechartScript]')[1] if '[/RechartScript]' in parts[1] else ''
                if remaining_text.strip():
                    sentences = remaining_text.split('。')
                    for i, sentence in enumerate(sentences):
                        if sentence.strip():
                            chunk_data = {
                                'status': 'streaming',
                                'message': sentence.strip() + ('。' if i < len(sentences) - 1 else ''),
                                'chunk_index': i
                            }                 
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(settings.STREAM_DELAY)
            else:
                # 按句号分割结果，更自然的分块方式
                sentences = result.split('。')
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        chunk_data = {
                            'status': 'streaming',
                            'message': sentence.strip() + ('。' if i < len(sentences) - 1 else ''),
                            'chunk_index': i
                        }                 
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(settings.STREAM_DELAY)  # 控制流速
        else:
            # 如果结果不是字符串，直接发送
            yield f"data: {json.dumps({'status': 'streaming', 'message': str(result)}, ensure_ascii=False)}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'status': 'completed', 'message': '[DONE]'}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        logger.error(f"处理查询时出错: {e}")
        yield f"data: {json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n" 