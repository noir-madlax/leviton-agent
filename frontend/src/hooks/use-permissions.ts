import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { config } from '@/lib/config'

export interface UserPermissions {
  user_id: string
  can_import_data: boolean
  can_create_project: boolean
  can_send_chat: boolean
}

export function usePermissions() {
  const { user, isAuthenticated } = useAuth()
  const [permissions, setPermissions] = useState<UserPermissions | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPermissions = async () => {
    if (!isAuthenticated || !user?.id) {
      setPermissions(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${config.backendUrl}/api/v1/permissions/${user.id}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setPermissions(data)
    } catch (err) {
      console.error('Error fetching permissions:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch permissions')
      
      // Fallback to default permissions on error
      setPermissions({
        user_id: user.id,
        can_import_data: true,
        can_create_project: true,
        can_send_chat: true
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPermissions()
  }, [isAuthenticated, user?.id])

  return {
    permissions,
    loading,
    error,
    refetch: fetchPermissions
  }
} 