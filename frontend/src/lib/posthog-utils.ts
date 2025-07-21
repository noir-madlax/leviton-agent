// PostHog 工具函数

import { usePostHog as usePostHogOriginal } from 'posthog-js/react'

// 检查是否为localhost环境
export function isLocalhostEnvironment(): boolean {
  if (typeof window === 'undefined') return false
  
  const hostname = window.location.hostname
  return hostname === 'localhost' || 
         hostname === '127.0.0.1' || 
         hostname.startsWith('192.168.') || 
         hostname.endsWith('.local')
}

// 安全的PostHog hook - 在localhost环境下返回空操作
export function usePostHog() {
  const posthog = usePostHogOriginal()
  
  // 在localhost环境下返回一个mock对象，避免错误
  if (isLocalhostEnvironment()) {
    return {
      capture: () => {}, // 空操作
      identify: () => {}, // 空操作
      reset: () => {}, // 空操作
      isFeatureEnabled: () => false, // 默认返回false
      getFeatureFlag: () => undefined, // 默认返回undefined
    }
  }
  
  return posthog
} 