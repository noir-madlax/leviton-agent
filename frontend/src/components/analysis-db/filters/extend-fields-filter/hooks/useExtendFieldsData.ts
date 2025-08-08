import { useState, useEffect } from 'react'
import { ExtendFieldDefinition } from '../types'

// 项目数据类型定义
interface ProjectData {
  distributions?: {
    extend_fields?: Record<string, Array<{
      name: string
      count: number
      percentage: number
    }>>
  }
}

// 全局缓存存储，避免重复调用接口
const extendFieldsCache = new Map<string, {
  fieldDefinitions: ExtendFieldDefinition[]
  projectData: ProjectData | null
  timestamp: number
  loading: boolean
}>()

// 全局加载状态跟踪，防止同一项目的并发请求
const loadingPromises = new Map<string, Promise<{ fieldDefinitions: ExtendFieldDefinition[], projectData: ProjectData | null }>>()

// 🆕 全局重渲染通知回调存储
const rerenderCallbacks = new Set<() => void>()

interface UseExtendFieldsDataReturn {
  fieldDefinitions: ExtendFieldDefinition[]
  projectData: ProjectData | null
  loading: boolean
  error: string | null
}

// 🆕 注册重渲染回调
export function registerExtendFieldsRerenderCallback(callback: () => void): () => void {
  rerenderCallbacks.add(callback)
  return () => {
    rerenderCallbacks.delete(callback)
  }
}

// 🆕 通知所有注册的组件重渲染
function notifyExtendFieldsRerender() {
  console.log('🔄 [EXTEND-FIELDS-HOOK] Notifying all components to rerender, callbacks count:', rerenderCallbacks.size)
  rerenderCallbacks.forEach(callback => {
    try {
      callback()
    } catch (error) {
      console.error('🚨 [EXTEND-FIELDS-HOOK] Error in rerender callback:', error)
    }
  })
}

// 🆕 手动触发重渲染（用于测试或手动调用）
export function triggerExtendFieldsRerender() {
  console.log('🔄 [EXTEND-FIELDS-HOOK] Manual trigger for extend fields rerender')
  notifyExtendFieldsRerender()
}

export function useExtendFieldsData(projectId: string): UseExtendFieldsDataReturn {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldDefinitions, setFieldDefinitions] = useState<ExtendFieldDefinition[]>([])
  const [projectData, setProjectData] = useState<ProjectData | null>(null)

  // 从缓存中获取数据并更新状态
  useEffect(() => {
    const cached = extendFieldsCache.get(projectId)
    if (cached && cached.fieldDefinitions) {
      console.log('🔧 [EXTEND-FIELDS-HOOK] Updating state from cache:', cached.fieldDefinitions.length, 'fields')
      setFieldDefinitions(cached.fieldDefinitions)
      setProjectData(cached.projectData)
    } else {
      setFieldDefinitions([])
      setProjectData(null)
    }
  }, [projectId])

  // 加载 extend fields 数据
  useEffect(() => {
    const loadExtendFields = async () => {
      if (!projectId) return

      // 检查缓存是否有效（30分钟内）
      const cached = extendFieldsCache.get(projectId)
      if (cached && cached.fieldDefinitions.length > 0 && cached.timestamp) {
        const cacheAge = Date.now() - cached.timestamp
        if (cacheAge < 30 * 60 * 1000) { // 30分钟缓存有效
          console.log('🔧 [EXTEND-FIELDS-HOOK] Using cached data for project:', projectId)
          return
        }
      }

      // 检查是否已有正在进行的请求
      const existingPromise = loadingPromises.get(projectId)
      if (existingPromise) {
        console.log('🔧 [EXTEND-FIELDS-HOOK] Waiting for existing request for project:', projectId)
        try {
          await existingPromise
        } catch (error) {
          console.error('🔧 [EXTEND-FIELDS-HOOK] Existing request failed:', error)
        }
        return
      }

      // 开始加载
      setLoading(true)
      setError(null)

      // 更新缓存状态为加载中
      extendFieldsCache.set(projectId, {
        fieldDefinitions: cached?.fieldDefinitions || [],
        projectData: cached?.projectData || null,
        timestamp: cached?.timestamp || 0,
        loading: true
      })

      // 创建加载 Promise
      const loadingPromise = (async () => {
        try {
          console.log('🔧 [EXTEND-FIELDS-HOOK] Starting API requests for project:', projectId)

          const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

          // 并行获取 extend fields 和项目数据
          const [extendFieldsResponse, projectDataResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/extend-fields`),
            fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/overview`)
          ])

          if (!extendFieldsResponse.ok) {
            throw new Error(`Extend fields API error! status: ${extendFieldsResponse.status}`)
          }

          const extendFieldsResult = await extendFieldsResponse.json()
          const fieldDefinitions = extendFieldsResult.extend_fields || []

          let projectData: ProjectData | null = null
          if (projectDataResponse.ok) {
            const projectDataResult = await projectDataResponse.json()
            projectData = {
              distributions: {
                extend_fields: projectDataResult.distributions?.extend_fields || {}
              }
            }
          }

          // 更新缓存
          extendFieldsCache.set(projectId, {
            fieldDefinitions,
            projectData,
            timestamp: Date.now(),
            loading: false
          })

          // 立即更新组件状态
          setFieldDefinitions(fieldDefinitions)
          setProjectData(projectData)

          console.log('🔧 [EXTEND-FIELDS-HOOK] Loaded from API:', fieldDefinitions.map((f: ExtendFieldDefinition) => f.field_name))

          // 🆕 通知所有组件重渲染
          notifyExtendFieldsRerender()

          return { fieldDefinitions, projectData }
        } catch (error) {
          console.error('🔧 [EXTEND-FIELDS-HOOK] Error loading data:', error)

          // 更新缓存状态
          extendFieldsCache.set(projectId, {
            fieldDefinitions: cached?.fieldDefinitions || [],
            projectData: cached?.projectData || null,
            timestamp: cached?.timestamp || 0,
            loading: false
          })

          throw error
        }
      })()

      // 存储 Promise
      loadingPromises.set(projectId, loadingPromise)

      try {
        await loadingPromise
        setError(null)
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to load extend fields')
      } finally {
        setLoading(false)
        loadingPromises.delete(projectId)
      }
    }

    loadExtendFields()
  }, [projectId])

  return {
    fieldDefinitions,
    projectData,
    loading,
    error
  }
}

// 预加载指定项目的 extend fields 数据
export function preloadExtendFields(projectId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const loadFields = async () => {
      try {
        // 检查缓存是否已经存在且有效
        const cached = extendFieldsCache.get(projectId)
        if (cached && cached.fieldDefinitions.length > 0 && cached.timestamp) {
          const cacheAge = Date.now() - cached.timestamp
          if (cacheAge < 30 * 60 * 1000) { // 30分钟缓存有效
            console.log(`Extend fields already cached for project ${projectId}`)
            resolve()
            return
          }
        }

        console.log(`Preloading extend fields for project ${projectId}`)

        const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

        // 并行获取数据
        const [extendFieldsResponse, projectDataResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/extend-fields`),
          fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/overview`)
        ])

        if (!extendFieldsResponse.ok) {
          throw new Error(`HTTP error! status: ${extendFieldsResponse.status}`)
        }

        const extendFieldsResult = await extendFieldsResponse.json()
        const fieldDefinitions = extendFieldsResult.extend_fields || []

        let projectData: ProjectData | null = null
        if (projectDataResponse.ok) {
          const projectDataResult = await projectDataResponse.json()
          projectData = {
            distributions: {
              extend_fields: projectDataResult.distributions?.extend_fields || {}
            }
          }
        }

        // 更新缓存
        extendFieldsCache.set(projectId, {
          fieldDefinitions,
          projectData,
          timestamp: Date.now(),
          loading: false
        })

        console.log(`Preloaded extend fields for project ${projectId}: ${fieldDefinitions.length} fields`)

        // 🆕 通知所有组件重渲染
        notifyExtendFieldsRerender()

        resolve()
      } catch (error) {
        console.error(`Failed to preload extend fields for project ${projectId}:`, error)
        reject(error)
      }
    }

    loadFields()
  })
}

// 清除指定项目的缓存
export function clearExtendFieldsCache(projectId?: string) {
  if (projectId) {
    extendFieldsCache.delete(projectId)
    loadingPromises.delete(projectId)
  } else {
    extendFieldsCache.clear()
    loadingPromises.clear()
  }
}
