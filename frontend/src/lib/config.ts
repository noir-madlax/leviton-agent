// 前端配置文件
export const config = {
  // 后端API URL配置
  backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'https://3po-agent.duckdns.org',
  
  // 其他配置项可以在这里添加
  // apiTimeout: 30000,
  // maxRetries: 3,
} as const;

// 导出默认配置
export default config; 