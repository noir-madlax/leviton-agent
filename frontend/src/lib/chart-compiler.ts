import { transform } from '@babel/standalone';
import React from 'react';
import * as Recharts from 'recharts';
import { CompilerResult } from './types';

/**
 * 动态编译JSX代码为React组件
 * @param chartCode - LLM生成的图表代码字符串
 * @returns 编译结果，包含组件或错误信息
 */
export function compileChartCode(chartCode: string): CompilerResult {
  try {
    // 第一步：预处理代码，清理转义字符
    const cleanedCode = chartCode
      .replace(/\\n/g, '\n')     // 修复换行符转义
      .replace(/\\r/g, '\r')     // 修复回车符转义
      .replace(/\\t/g, '\t')     // 修复制表符转义
      .replace(/\\"/g, '"')      // 修复双重转义的引号
      .replace(/\\'/g, "'")      // 修复双重转义的单引号
      .replace(/\\\\/g, '\\')    // 修复双重转义的反斜杠
      .trim();                   // 清理首尾空白

    // 添加调试日志
    console.log('🔧 原始代码:', chartCode.substring(0, 200) + '...');
    console.log('✨ 清理后的代码:', cleanedCode.substring(0, 200) + '...');

    // 第二步：JSX编译
    const compiledCode = transform(cleanedCode, {
      presets: ['react'],
      filename: 'dynamic-chart.jsx',
    }).code;

    if (!compiledCode) {
      throw new Error('编译后的代码为空');
    }

    // 第二步：创建执行环境
    // 提供React和Recharts作为全局变量
    const createComponent = new Function(
      'React',
      'Recharts',
      `
      const { 
        LineChart, Line, AreaChart, Area, BarChart, Bar,
        ComposedChart, PieChart, Pie, Cell, ScatterChart, Scatter,
        XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
      } = Recharts;
      
      ${compiledCode}
      
      return typeof DynamicChart !== 'undefined' ? DynamicChart : 
             typeof Chart !== 'undefined' ? Chart :
             null;
      `
    );

    // 第三步：执行代码获取组件
    const Component = createComponent(React, Recharts);

    if (!Component) {
      throw new Error('未找到有效的图表组件，请确保导出名为 DynamicChart 或 Chart 的组件');
    }

    return {
      success: true,
      component: Component,
    };

  } catch (error) {
    console.error('图表编译失败:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : '未知编译错误',
    };
  }
}

/**
 * 验证图表代码的基本安全性
 * @param code - 要验证的代码
 * @returns 是否安全
 */
export function validateChartCode(code: string): { valid: boolean; error?: string } {
  // 检查危险的JavaScript功能
  const dangerousPatterns = [
    /eval\s*\(/,
    /Function\s*\(/,
    /setTimeout/,
    /setInterval/,
    /XMLHttpRequest/,
    /fetch\s*\(/,
    /import\s*\(/,
    /require\s*\(/,
    /process\./,
    /global\./,
    /window\./,
    /document\./,
  ];

  for (const pattern of dangerousPatterns) {
    if (pattern.test(code)) {
      return {
        valid: false,
        error: `检测到不安全的代码模式: ${pattern.source}`,
      };
    }
  }

  // 检查是否有导出的组件
  if (!code.includes('export default') && !code.includes('const DynamicChart') && !code.includes('const Chart')) {
    return {
      valid: false,
      error: '代码必须包含 export default 导出或定义 DynamicChart/Chart 组件',
    };
  }

  return { valid: true };
} 