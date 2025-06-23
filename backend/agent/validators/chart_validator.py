"""
Agent 响应验证器 - 保持原有逻辑完全不变
"""
import json
import logging
from agent.services.chart_validation_service import validate_chart_response, chart_validation_service

logger = logging.getLogger(__name__)

def is_valid_json(text: str) -> bool:
    """检查文本是否为有效的 JSON 格式 - 保持原有逻辑不变"""
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False

def check_reasoning_and_plot(final_answer, agent_memory):
    """
    检查推理过程和图表是否正确 - 保持原有逻辑完全不变
    
    Args:
        final_answer: LLM 生成的最终答案
        agent_memory: Agent 的内存状态
        
    Raises:
        Exception: 当验证失败时抛出具体错误信息，供 Agent 改进
        
    Returns:
        bool: 验证通过时返回 True
    """
    logger.info("🔍 开始检查推理过程和图表是否正确")
    
    # 检查是否为 JSON 格式
    if not is_valid_json(final_answer):
        logger.info("📝 结果不是有效的 JSON 格式，将作为普通字符串处理")
        return True
    
    logger.info("📄 结果成功解析为 JSON 格式，开始进行图表验证")
    
    try:
        # 使用图表验证服务进行全面验证
        validation_result = validate_chart_response(final_answer)
        
        # 首先检查 JSON 格式是否有效
        if not validation_result["is_valid_json"]:
            error_msg = "JSON 格式验证失败"
            if "json_error" in validation_result:
                error_msg += f": {validation_result['json_error']}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        logger.info("✅ JSON 格式验证通过")
        
        # 检查图表验证结果
        chart_validation = validation_result.get("chart_validation")
        if not chart_validation:
            error_msg = "图表验证过程中出现异常，无法获取验证结果"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        chart_count = chart_validation.get("chart_count", 0)
        logger.info(f"📊 发现 {chart_count} 个图表")
        
        # 如果发现图表但验证失败，抛出详细错误信息
        if chart_count > 0 and not chart_validation["valid"]:
            errors = chart_validation.get("errors", [])
            if errors:
                # 构建详细的错误信息
                error_details = []
                for i, error in enumerate(errors, 1):
                    error_details.append(f"{i}. {error}")
                
                error_msg = f"图表验证失败，发现 {len(errors)} 个错误:\n" + "\n".join(error_details)
                
                # 添加改进建议
                error_msg += "\n\n请检查以下问题:"
                error_msg += "\n- JSX 语法是否正确（特别是箭头函数参数格式）"
                error_msg += "\n- 模板字符串中的引号是否正确"
                error_msg += "\n- Recharts 组件属性格式是否正确（如 margin={{...}}）"
                error_msg += "\n- 数据结构是否符合组件要求"
                
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
        
        # 记录成功验证的详细信息
        if chart_validation["valid"]:
            logger.info("✅ 所有图表验证通过")
            
            # 记录每个图表的验证详情
            for chart_detail in chart_validation.get("chart_details", []):
                chart_key = chart_detail["key"]
                if chart_detail["valid"]:
                    logger.info(f"✅ {chart_key} 验证通过")
                    if chart_detail.get("info"):
                        for info in chart_detail["info"]:
                            logger.info(f"  📈 {chart_key}: {info}")
                else:
                    logger.warning(f"⚠️ {chart_key} 验证存在问题，但不影响整体通过")
        
        # 记录警告信息（不影响通过状态）
        warnings = chart_validation.get("warnings", [])
        if warnings:
            logger.warning(f"⚠️ 发现 {len(warnings)} 个警告（不影响验证通过）:")
            for i, warning in enumerate(warnings, 1):
                logger.warning(f"  {i}. {warning}")
        
        # 生成并记录验证摘要
        summary = chart_validation_service.get_validation_summary(validation_result)
        logger.info(f"📋 验证摘要: {summary}")
        
        # 最终检查整体验证结果
        if not validation_result["overall_valid"]:
            error_msg = "整体验证失败，虽然单个组件可能通过，但整体结构存在问题"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        logger.info("🎉 所有验证检查通过")
        return True
        
    except Exception as e:
        # 如果是我们主动抛出的异常，直接重新抛出
        if "图表验证失败" in str(e) or "JSON 格式验证失败" in str(e) or "整体验证失败" in str(e):
            raise
        
        # 如果是其他异常，包装后抛出
        error_msg = f"图表验证过程中出现异常: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        raise Exception(error_msg) 