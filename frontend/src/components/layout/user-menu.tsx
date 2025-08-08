"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { User, Settings, LogOut, CreditCard, Globe } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useNavT } from "@/i18n/hooks"
import { useTranslation } from 'react-i18next'

export function UserMenu() {
  const { user, signOut } = useAuth()
  const [isClient, setIsClient] = useState(false)
  const { i18n } = useTranslation()
  
  // 总是调用hooks，但在客户端渲染前返回fallback
  const navTRaw = useNavT()
  const t = (key: string) => isClient ? navTRaw(key) : key

  useEffect(() => {
    setIsClient(true)
  }, [])

  const handleLogout = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  const handleLanguageSwitch = () => {
    const currentLang = i18n.language
    const newLang = currentLang === 'zh' ? 'en' : 'zh'
    i18n.changeLanguage(newLang)
  }

  const getCurrentLanguageDisplay = () => {
    const currentLang = i18n.language
    return currentLang === 'zh' ? '中文 → English' : 'English → 中文'
  }

  // Get user display information
  const displayName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'
  const avatarUrl = user?.user_metadata?.avatar_url
  const email = user?.email

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarImage src={avatarUrl || ""} alt={displayName} />
            <AvatarFallback className="bg-blue-600 text-white">
              {displayName.slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{displayName}</p>
            <p className="text-xs leading-none text-muted-foreground">{email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <User className="mr-2 h-4 w-4" />
          <span>{t('profile')}</span>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <CreditCard className="mr-2 h-4 w-4" />
          <span>{t('billing')}</span>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleLanguageSwitch}>
          <Globe className="mr-2 h-4 w-4" />
          <span>{isClient ? getCurrentLanguageDisplay() : 'Language'}</span>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <Settings className="mr-2 h-4 w-4" />
          <span>{t('settings')}</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          <span>{t('logout')}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 