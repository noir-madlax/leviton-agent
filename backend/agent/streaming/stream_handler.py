"""
流式响应处理器 - 支持多个脚本块处理
"""
import asyncio
import json
import logging
import re
from typing import AsyncGenerator
from config import settings
from agent.core.agent_manager import get_agent_manager
from agent.services.query_processor import get_query_processor
from agent.validators.chart_validator import is_valid_json

logger = logging.getLogger(__name__)

async def stream_agent_response(query: str) -> AsyncGenerator[str, None]:
    """
    运行 smolagents 代理并通过 SSE 流式输出结果 - 支持多个脚本块处理
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
            # 检查是否包含脚本块（RechartScript 或 insight）
            has_rechart = '[RechartScript]' in result and '[/RechartScript]' in result
            has_insight = '[insight]' in result and '[/insight]' in result
            
            if has_rechart or has_insight:
                async for chunk in process_text_with_scripts(result):
                    yield chunk
            else:
                # 按句号分割结果，更自然的分块方式
                async for chunk in send_text_chunks(result):
                    yield chunk
        else:
            # 如果结果不是字符串，直接发送
            yield f"data: {json.dumps({'status': 'streaming', 'message': str(result)}, ensure_ascii=False)}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'status': 'completed', 'message': '[DONE]'}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        logger.error(f"处理查询时出错: {e}")
        yield f"data: {json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"


async def process_text_with_scripts(text: str) -> AsyncGenerator[str, None]:
    """
    处理包含多个脚本块的文本，支持 RechartScript 和 insight 代码块
    兼容LLM可能产生的连续开始标签错误，如：[RechartScript] [RechartScript] content [/RechartScript]
    """
    # 分别查找开始标签和结束标签
    start_pattern = r'\[(RechartScript|insight)\]'
    end_pattern = r'\[/(RechartScript|insight)\]'
    
    start_matches = list(re.finditer(start_pattern, text))
    end_matches = list(re.finditer(end_pattern, text))
    
    if not start_matches or not end_matches:
        # 如果没有找到脚本块，按普通文本处理
        async for chunk in send_text_chunks(text):
            yield chunk
        return
    
    # 构建正确的标签对，优先匹配最接近的标签
    script_blocks = []
    used_starts = set()
    used_ends = set()
    
    # 对每个结束标签，找到最近的未使用的开始标签
    for end_match in end_matches:
        end_pos = end_match.start()
        end_type = end_match.group(1)
        
        # 找到此结束标签前的所有匹配类型的开始标签
        candidate_starts = []
        for i, start_match in enumerate(start_matches):
            if (i not in used_starts and 
                start_match.start() < end_pos and 
                start_match.group(1) == end_type):
                candidate_starts.append((i, start_match))
        
        if candidate_starts:
            # 选择最接近结束标签的开始标签
            closest_start_idx, closest_start = max(candidate_starts, key=lambda x: x[1].start())
            
            # 提取内容
            content_start = closest_start.end()
            content_end = end_pos
            script_content = text[content_start:content_end].strip()
            
            script_blocks.append({
                'start_pos': closest_start.start(),
                'end_pos': end_match.end(),
                'script_type': end_type,
                'content': script_content
            })
            
            # 标记为已使用
            used_starts.add(closest_start_idx)
            used_ends.add(end_matches.index(end_match))
    
    if not script_blocks:
        # 如果没有找到有效的脚本块，按普通文本处理
        async for chunk in send_text_chunks(text):
            yield chunk
        return
    
    # 按位置排序脚本块
    script_blocks.sort(key=lambda x: x['start_pos'])
    
    current_pos = 0
    script_count = 0
    
    for block in script_blocks:
        script_count += 1
        start_pos = block['start_pos']
        end_pos = block['end_pos']
        script_type = block['script_type']
        script_content = block['content']
        
        # 处理脚本块前的文本
        if start_pos > current_pos:
            text_before = text[current_pos:start_pos]
            if text_before.strip():
                async for chunk in send_text_chunks(text_before):
                    yield chunk
        
        # 发送脚本块
        if script_content:
            # 根据脚本类型设置不同的 status
            if script_type == "RechartScript":
                status = "rechart"
                logger.info(f"发送第 {script_count} 个 RechartScript 脚本块")
            elif script_type == "insight":
                status = "insight"
                logger.info(f"发送第 {script_count} 个 insight 代码块")
            
            script_data = {
                'status': status,
                'message': script_content,
                'script_index': script_count - 1,  # 添加索引便于前端识别
                'script_type': script_type  # 添加脚本类型便于前端区分
            }
            yield f"data: {json.dumps(script_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(settings.STREAM_DELAY)
        
        current_pos = end_pos
    
    # 处理最后一个脚本块后的文本
    if current_pos < len(text):
        remaining_text = text[current_pos:]
        if remaining_text.strip():
            async for chunk in send_text_chunks(remaining_text):
                yield chunk


async def send_text_chunks(text: str) -> AsyncGenerator[str, None]:
    """
    将文本按句号分割并流式发送
    """
    if not text.strip():
        return
        
    sentences = text.split('。')
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            chunk_data = {
                'status': 'streaming',
                'message': sentence.strip() + ('。' if i < len(sentences) - 1 else ''),
                'chunk_index': i
            }                 
            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(settings.STREAM_DELAY)