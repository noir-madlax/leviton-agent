"""
图表验证服务模块

提供对 LLM 生成的 Recharts 图表代码进行验证的功能，
确保生成的代码安全且能够在前端正确渲染。
"""

import json
import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ChartValidationService:
    """图表验证服务类"""
    
    def __init__(self):
        self.dangerous_patterns = [
            (r'eval\s*\(', 'eval() 函数'),
            (r'Function\s*\(', 'Function() 构造函数'),
            (r'setTimeout', 'setTimeout 函数'),
            (r'setInterval', 'setInterval 函数'),
            (r'XMLHttpRequest', 'XMLHttpRequest'),
            (r'fetch\s*\(', 'fetch API'),
            (r'import\s*\(', 'dynamic import'),
            (r'require\s*\(', 'require 函数'),
            (r'process\.', 'process 对象'),
            (r'global\.', 'global 对象'),
            (r'window\.', 'window 对象'),
            (r'document\.', 'document 对象'),
        ]
        
        self.jsx_checks = [
            (r'const\s+DynamicChart\s*=', "必须定义 DynamicChart 组件"),
            (r'<ResponsiveContainer', "必须使用 ResponsiveContainer"),
            (r'return\s*\(', "组件必须有 return 语句"),
        ]
        
        self.recharts_components = [
            'BarChart', 'LineChart', 'PieChart', 'AreaChart', 'ScatterChart',
            'XAxis', 'YAxis', 'CartesianGrid', 'Tooltip', 'Legend', 
            'Bar', 'Line', 'Pie', 'Area', 'Cell', 'Scatter'
        ]

    def validate_recharts_code(self, code: str) -> Dict[str, Any]:
        """
        验证 Recharts 代码的基本语法和安全性
        
        Args:
            code: JavaScript/JSX 代码字符串
            
        Returns:
            dict: 包含验证结果的字典
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        if not code or not code.strip():
            validation_result["valid"] = False
            validation_result["errors"].append("代码不能为空")
            return validation_result
        
        # 检查危险的JavaScript功能
        for pattern, description in self.dangerous_patterns:
            if re.search(pattern, code):
                validation_result["valid"] = False
                validation_result["errors"].append(f"检测到不安全的代码: {description}")
        
        # 检查基本的 React/JSX 语法
        for pattern, error_msg in self.jsx_checks:
            if not re.search(pattern, code):
                validation_result["warnings"].append(error_msg)
        
        # 检查括号匹配
        bracket_checks = [
            ('(', ')', "括号"),
            ('{', '}', "大括号"),
            ('[', ']', "方括号")
        ]
        
        for open_bracket, close_bracket, bracket_name in bracket_checks:
            if code.count(open_bracket) != code.count(close_bracket):
                validation_result["valid"] = False
                validation_result["errors"].append(f"{bracket_name}不匹配")
        
        # 检查常见的 Recharts 组件
        found_components = []
        for component in self.recharts_components:
            if f'<{component}' in code:
                found_components.append(component)
        
        if not found_components:
            validation_result["warnings"].append("未检测到常见的 Recharts 组件")
        else:
            validation_result["info"].append(f"检测到组件: {', '.join(found_components)}")
        
        # 检查数据定义
        if not re.search(r'const\s+data\s*=\s*\[', code):
            validation_result["warnings"].append("未检测到数据定义 (const data = [...])")
        
        # 检查 margin 属性格式
        if 'margin=' in code:
            if not re.search(r'margin=\{\{[^}]*\}\}', code):
                validation_result["valid"] = False
                validation_result["errors"].append("margin 属性必须使用双大括号格式: margin={{ ... }}")
        
        # 检查常见的语法错误
        common_errors = [
            (r'margin=\s*\{[^{]', "margin 属性缺少内层大括号"),
            (r'dataKey=\s*[^"\'][\w]+[^"\']', "dataKey 属性值应该用引号包围"),
            (r'fill=\s*[^"\'][#\w]+[^"\']', "fill 属性值应该用引号包围"),
        ]
        
        for pattern, error_msg in common_errors:
            if re.search(pattern, code):
                validation_result["warnings"].append(error_msg)
        
        return validation_result

    def validate_chart_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证图表 JSON 数据的结构和内容
        
        Args:
            json_data: 解析后的 JSON 数据
            
        Returns:
            dict: 验证结果
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "chart_count": 0,
            "chart_details": []
        }
        
        # 检查是否包含图表数据
        chart_keys = []
        
        # 检查单图表格式
        if "chartData" in json_data:
            chart_keys.append("chartData")
            validation_result["chart_count"] += 1
        
        # 检查多图表格式
        for i in range(1, 4):  # chart1, chart2, chart3
            chart_key = f"chart{i}"
            if chart_key in json_data:
                chart_keys.append(chart_key)
                validation_result["chart_count"] += 1
        
        if not chart_keys:
            validation_result["valid"] = False
            validation_result["errors"].append("JSON 中未找到图表数据 (chartData 或 chart1/chart2/chart3)")
            return validation_result
        
        # 验证每个图表的结构
        for chart_key in chart_keys:
            chart_detail = {
                "key": chart_key,
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            chart_data = json_data[chart_key]
            
            if not isinstance(chart_data, dict):
                validation_result["valid"] = False
                error_msg = f"{chart_key} 必须是一个对象"
                validation_result["errors"].append(error_msg)
                chart_detail["valid"] = False
                chart_detail["errors"].append(error_msg)
                validation_result["chart_details"].append(chart_detail)
                continue
            
            # 检查必需字段
            required_fields = ["code", "explanation", "insights"]
            for field in required_fields:
                if field not in chart_data:
                    validation_result["valid"] = False
                    error_msg = f"{chart_key} 缺少必需字段: {field}"
                    validation_result["errors"].append(error_msg)
                    chart_detail["valid"] = False
                    chart_detail["errors"].append(error_msg)
                elif not chart_data[field] or not str(chart_data[field]).strip():
                    validation_result["valid"] = False
                    error_msg = f"{chart_key} 的 {field} 字段不能为空"
                    validation_result["errors"].append(error_msg)
                    chart_detail["valid"] = False
                    chart_detail["errors"].append(error_msg)
            
            # 验证代码内容
            if "code" in chart_data and chart_data["code"]:
                code_validation = self.validate_recharts_code(chart_data["code"])
                if not code_validation["valid"]:
                    validation_result["valid"] = False
                    for error in code_validation["errors"]:
                        error_msg = f"{chart_key} 代码验证失败: {error}"
                        validation_result["errors"].append(error_msg)
                        chart_detail["valid"] = False
                        chart_detail["errors"].append(error_msg)
                
                # 添加警告信息
                if code_validation["warnings"]:
                    for warning in code_validation["warnings"]:
                        warning_msg = f"{chart_key}: {warning}"
                        validation_result["warnings"].append(warning_msg)
                        chart_detail["warnings"].append(warning_msg)
                
                # 添加信息
                if code_validation.get("info"):
                    chart_detail["info"] = code_validation["info"]
            
            validation_result["chart_details"].append(chart_detail)
        
        return validation_result

    def validate_json_string(self, json_string: str) -> Dict[str, Any]:
        """
        验证 JSON 字符串并返回完整的验证结果
        
        Args:
            json_string: JSON 字符串
            
        Returns:
            dict: 完整的验证结果
        """
        result = {
            "is_valid_json": False,
            "json_data": None,
            "chart_validation": None,
            "overall_valid": False
        }
        
        # 首先验证是否为有效 JSON
        try:
            json_data = json.loads(json_string)
            result["is_valid_json"] = True
            result["json_data"] = json_data
            
            # 然后验证图表结构和代码
            chart_validation = self.validate_chart_json(json_data)
            result["chart_validation"] = chart_validation
            result["overall_valid"] = chart_validation["valid"]
            
        except json.JSONDecodeError as e:
            result["json_error"] = str(e)
            logger.error(f"JSON 解析失败: {e}")
        except Exception as e:
            result["validation_error"] = str(e)
            logger.error(f"图表验证过程中出错: {e}")
        
        return result

    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """
        生成验证结果的摘要信息
        
        Args:
            validation_result: 验证结果字典
            
        Returns:
            str: 验证摘要信息
        """
        if not validation_result["is_valid_json"]:
            return "❌ 不是有效的 JSON 格式"
        
        chart_validation = validation_result["chart_validation"]
        if not chart_validation:
            return "❌ 图表验证失败"
        
        if chart_validation["valid"]:
            summary = f"✅ 图表验证成功! 发现 {chart_validation['chart_count']} 个图表"
            if chart_validation["warnings"]:
                summary += f"\n⚠️ 警告: {len(chart_validation['warnings'])} 个"
            return summary
        else:
            summary = f"❌ 图表验证失败: {len(chart_validation['errors'])} 个错误"
            if chart_validation["warnings"]:
                summary += f", {len(chart_validation['warnings'])} 个警告"
            return summary


# 创建全局实例
chart_validation_service = ChartValidationService()


# 便捷函数
def validate_chart_response(response: str) -> Dict[str, Any]:
    """
    验证图表响应的便捷函数
    
    Args:
        response: 响应字符串
        
    Returns:
        dict: 验证结果
    """
    return chart_validation_service.validate_json_string(response)


def is_valid_chart_json(response: str) -> bool:
    """
    检查响应是否为有效的图表 JSON
    
    Args:
        response: 响应字符串
        
    Returns:
        bool: 是否有效
    """
    result = chart_validation_service.validate_json_string(response)
    return result["overall_valid"] 