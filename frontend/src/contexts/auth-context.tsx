"use client"

import { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { useToast } from '@/hooks/use-toast'

interface AuthContextType {
  user: User | null
  session: Session | null
  isLoading: boolean
  isAuthenticated: boolean
  signIn: (email: string, password: string) => Promise<void>
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setIsLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setIsLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    try {
      console.log('Attempting to sign in...')
      
      // 首先检查是否已经有有效的session
      const { data: sessionData } = await supabase.auth.getSession()
      if (sessionData.session) {
        console.log('Valid session already exists, user is authenticated')
        return
      }
      
      // Try to sign in first
      const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (signInError) {
        console.error('Sign in error:', signInError)
        
        // 如果是登录凭证错误，尝试注册
        if (signInError.message.includes('Invalid login credentials')) {
          console.log('Invalid credentials, attempting sign up...')
          const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
            email,
            password,
          })

          if (signUpError) {
            console.error('Sign up error:', signUpError)
            if (signUpError.message.includes('User already registered')) {
              // 用户已注册但密码错误
              throw new Error('Invalid login credentials. Please check your password.')
            } else {
              throw new Error(`Sign up failed: ${signUpError.message}`)
            }
          }

          if (signUpData.user) {
            console.log('Sign up successful')
            // 注册成功，等待确认邮件
            if (!signUpData.session) {
              throw new Error('Registration successful! Please check your email for confirmation.')
            }
          }
        } else {
          // 其他登录错误
          throw new Error(`Sign in failed: ${signInError.message}`)
        }
      }

      if (signInData.user) {
        console.log('Sign in successful')
      }
    } catch (error) {
      console.error('Authentication error:', error)
      // 只有在真正出错时才抛出错误
      if (error instanceof Error) {
        throw error
      } else {
        throw new Error('An unexpected error occurred during authentication')
      }
    }
  }

  const signInWithGoogle = async () => {
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      })

      if (error) {
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        })
        throw error
      }
    } catch (error) {
      console.error('Google sign in error:', error)
      throw error
    }
  }

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        })
        throw error
      }
      
      toast({
        title: "Success",
        description: "Successfully signed out!",
      })
    } catch (error) {
      console.error('Sign out error:', error)
      throw error
    }
  }

  const resetPassword = async (email: string) => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      })

      if (error) {
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        })
        throw error
      }

      toast({
        title: "Success",
        description: "Password reset link has been sent to your email",
      })
    } catch (error) {
      console.error('Reset password error:', error)
      throw error
    }
  }

  const value = {
    user,
    session,
    isLoading,
    isAuthenticated: !!user,
    signIn,
    signInWithGoogle,
    signOut,
    resetPassword,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 