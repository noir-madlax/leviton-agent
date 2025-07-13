// 埋点功能

'use client'

import { useEffect, Suspense } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'
import posthog from 'posthog-js'
import { PostHogProvider } from 'posthog-js/react'

// PostHog 初始化
if (typeof window !== 'undefined') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: "/ingest",
    ui_host: "https://us.posthog.com",
    defaults: '2025-05-24',
    capture_exceptions: true,
    debug: process.env.NODE_ENV === "development",
    capture_pageview: false, // 禁用自动页面浏览量，我们将手动捕获
    person_profiles: 'identified_only', // 只为已识别用户创建配置文件
  })
}

// 页面浏览量追踪组件
function PostHogPageView() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    if (pathname) {
      let url = window.origin + pathname
      if (searchParams.toString()) {
        url = url + `?${searchParams.toString()}`
      }
      posthog.capture('$pageview', {
        $current_url: url,
      })
    }
  }, [pathname, searchParams])

  return null
}

// 用户识别组件 - 仅在客户端渲染且 AuthProvider 可用时运行
function PostHogUserIdentify() {
  useEffect(() => {
    // 仅在客户端运行
    if (typeof window === 'undefined') return

    // 监听 auth 状态变化
    const handleAuthChange = () => {
      try {
        // 尝试从 Supabase 获取当前用户信息
        import('@/lib/supabase').then(({ supabase }) => {
          supabase.auth.getUser().then(({ data: { user } }) => {
            if (user) {
              posthog.identify(user.id, {
                email: user.email,
                name: user.user_metadata?.name || user.email,
              })
            } else {
              posthog.reset()
            }
          })
        })
      } catch {
        console.log('Auth not ready yet')
      }
    }

    // 立即检查一次
    handleAuthChange()

    // 监听认证状态变化
    let unsubscribe: (() => void) | undefined
    import('@/lib/supabase').then(({ supabase }) => {
      unsubscribe = supabase.auth.onAuthStateChange(handleAuthChange).data.subscription.unsubscribe
    })

    return () => {
      if (unsubscribe) unsubscribe()
    }
  }, [])

  return null
}

// 主要的 PostHog Provider 组件
export function PostHogAppProvider({ children }: { children: React.ReactNode }) {
  return (
    <PostHogProvider client={posthog}>
      <Suspense fallback={null}>
        <PostHogPageView />
      </Suspense>
      <PostHogUserIdentify />
      {children}
    </PostHogProvider>
  )
} 