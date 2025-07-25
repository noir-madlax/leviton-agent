"use client"

import { DataImportTab } from "@/components/tabs/data-import-tab"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { useState, useEffect } from "react"
import { useScrapingT, useCommonT } from "@/i18n/hooks"

export default function ImportDataPage() {
  const [isClient, setIsClient] = useState(false)
  
  // 翻译hooks
  const scrapingTRaw = useScrapingT()
  const commonTRaw = useCommonT()
  const t = (key: string) => isClient ? scrapingTRaw(key) : key
  const commonT = (key: string) => isClient ? commonTRaw(key) : key

  useEffect(() => {
    setIsClient(true)
  }, [])

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50/50">
        {/* Header */}
        <header className="border-b bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-4">
                <Link href="/">
                  <Button variant="ghost" size="sm">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    {commonT('backToHome')}
                  </Button>
                </Link>
                <div>
                  <h1 className="text-xl font-semibold">{t('dataScraping')}</h1>
                  <p className="text-sm text-muted-foreground">
                    {t('collectDataReviews')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <DataImportTab />
        </main>
      </div>
    </ProtectedRoute>
  )
} 