/**
 * 全局图表颜色配置
 * 用于所有图表组件的统一颜色管理
 */

// 50个高区分度颜色的全局调色板，确保50+个segment都有独特颜色
export const CHART_COLORS = [
  "#E74C3C", // 1. 红色
  "#3498DB", // 2. 蓝色  
  "#9B59B6", // 3. 紫色
  "#2ECC71", // 4. 绿色
  "#F39C12", // 5. 黄色
  "#1ABC9C", // 6. 青色
  "#34495E", // 7. 深蓝灰
  "#FF69B4", // 8. 热粉
  "#00CED1", // 9. 深青色
  "#FFD700", // 11. 金色
  "#DC143C", // 12. 深红
  "#32CD32", // 13. 酸橙绿
  "#4169E1", // 14. 皇家蓝
  "#FF4500", // 15. 橙红
  "#8A2BE2", // 16. 蓝紫
  "#00FF7F", // 17. 春绿
  "#FF1493", // 18. 深粉
  "#1E90FF", // 19. 天蓝
  "#FF6347", // 20. 番茄红
  "#40E0D0", // 21. 绿松石
  "#DA70D6", // 22. 兰花紫
  "#98FB98", // 23. 浅绿
  "#F0E68C", // 24. 卡其色
  "#DDA0DD", // 25. 李子色
  "#87CEEB", // 26. 天空蓝
  "#F4A460", // 27. 沙棕色
  "#20B2AA", // 28. 浅海绿
  "#B22222", // 29. 火砖红
  "#4682B4", // 30. 钢蓝
  "#D2691E", // 31. 巧克力色
  "#6495ED", // 32. 矢车菊蓝
  "#CD853F", // 33. 秘鲁色
  "#FF7F50", // 34. 珊瑚色
  "#6B8E23", // 35. 橄榄绿
  "#FF20B0", // 36. 鲜粉
  "#008B8B", // 37. 深青
  "#B8860B", // 38. 深金杆色
  "#A0522D", // 39. 黄褐色
  "#2F4F4F", // 40. 深石板灰
  "#8FBC8F", // 41. 深海绿
  "#483D8B", // 42. 深石板蓝
  "#CD5C5C", // 43. 印度红
  "#4FD0E7", // 44. 天蓝色
  "#3CB371", // 45. 中海绿
  "#D3D3D3", // 46. 浅灰
  "#A9A9A9", // 47. 深灰
  "#696969", // 48. 暗灰
  "#778899", // 49. 浅石板灰
  "#2E8B57"  // 50. 海绿色
]

// 品牌颜色映射（用于散点图等需要品牌特定颜色的场景）
export const BRAND_COLORS: Record<string, string> = {
  Kasa: "#8DD1E1",
  Leviton: "#9B59B6", 
  Lutron: "#E67E22",
  GE: "#3498DB",
  ELEGRP: "#80B1D3",
  BESTTEN: "#FDB462",
  "ENERLITES Store": "#B3DE69",
  Amazon: "#FCCDE5",
  TREATLIFE: "#FF6B6B",
  "TP-Link": "#4ECDC4",
  Other: "#D3D3D3"
}

// 获取颜色的辅助函数
export const getChartColor = (index: number): string => {
  return CHART_COLORS[index % CHART_COLORS.length]
}

// 获取品牌颜色的辅助函数
export const getBrandColor = (brand: string): string => {
  return BRAND_COLORS[brand] || BRAND_COLORS.Other
}

// 获取颜色数组（用于需要传递colors数组的组件）
export const getChartColors = (count?: number): string[] => {
  if (count) {
    return Array.from({ length: count }, (_, i) => getChartColor(i))
  }
  return CHART_COLORS
} 