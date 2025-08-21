/**
 * Chat Configuration Service
 * 
 * Handles fetching and caching of chat configuration data from the backend API.
 * Implements error handling and graceful degradation strategies.
 */

import { ChatConfig } from '@/components/integrated-dashboard/shared/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

// Cache for configuration data
const configCache = new Map<string, { data: ChatConfig; timestamp: number }>()
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

export class ChatConfigService {
  private static instance: ChatConfigService
  
  static getInstance(): ChatConfigService {
    if (!ChatConfigService.instance) {
      ChatConfigService.instance = new ChatConfigService()
    }
    return ChatConfigService.instance
  }

  /**
   * Get chat configuration for a project
   * @param projectId - The project ID
   * @returns Promise resolving to ChatConfig
   */
  async getChatConfig(projectId: string): Promise<ChatConfig> {
    try {
      // Get current language setting
      const currentLang = (typeof window !== 'undefined' && window.localStorage.getItem('i18nextLng')) || 'en'
      const cacheKey = `${projectId}_${currentLang}`
      
      // Check cache first
      const cached = this.getCachedConfig(cacheKey)
      if (cached) {
        console.log(`📋 Using cached chat config for project: ${projectId}, lang: ${currentLang}`)
        return cached
      }

      console.log(`📋 Fetching chat config for project: ${projectId}, lang: ${currentLang}`)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/chat-config?lang=${currentLang}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const rawConfig: ChatConfig = await response.json()
      const config = this.normalizeConfig(rawConfig)
      
      // Cache the result with language-specific key
      this.setCachedConfig(cacheKey, config)
      
      console.log(`✅ Chat config loaded: ${config.chart_cards.length} cards, ${Object.keys(config.chart_items).length} item groups`)
      return config

    } catch (error) {
      console.error('Error fetching chat config:', error)
      
      // Return fallback configuration
      return this.getFallbackConfig(projectId)
    }
  }

  /**
   * Get cached configuration if available and not expired
   */
  private getCachedConfig(projectId: string): ChatConfig | null {
    const cached = configCache.get(projectId)
    if (!cached) return null

    const now = Date.now()
    if (now - cached.timestamp > CACHE_DURATION) {
      configCache.delete(projectId)
      return null
    }

    return cached.data
  }

  /**
   * Cache configuration data
   */
  private setCachedConfig(projectId: string, config: ChatConfig): void {
    configCache.set(projectId, {
      data: config,
      timestamp: Date.now()
    })
  }

  /**
   * Normalize chart ids coming from backend to match actual DOM data-chart-id
   * This prevents anchor scroll failures when legacy ids are returned.
   */
  private normalizeConfig(config: ChatConfig): ChatConfig {
    const LEGACY_ID_MAP: Record<string, string> = {
      // brand-analysis tab
      'brand-analysis': 'best-selling-brands',
      'market-insights': 'segment-analysis',
      'package-preference': 'package-sales-trend'
    }

    // Deep clone and normalize chart_items
    const normalizedItems: ChatConfig['chart_items'] = {}
    for (const [cardId, items] of Object.entries(config.chart_items || {})) {
      normalizedItems[cardId] = items.map((it) => ({
        ...it,
        chart_id: LEGACY_ID_MAP[it.chart_id] ?? it.chart_id
      }))
    }

    // Normalize chart_sections as well
    const normalizedSections: ChatConfig['chart_sections'] = {}
    for (const [tabKey, sections] of Object.entries(config.chart_sections || {})) {
      normalizedSections[tabKey] = sections.map((sec) => ({
        ...sec,
        chart_id: LEGACY_ID_MAP[sec.chart_id] ?? sec.chart_id
      }))
    }

    return {
      ...config,
      chart_items: normalizedItems,
      chart_sections: normalizedSections
    }
  }

  /**
   * Clear cache for a specific project or all projects
   */
  clearCache(projectId?: string): void {
    if (projectId) {
      // Clear cache for all languages of this project
      const keysToDelete = Array.from(configCache.keys()).filter(key => 
        key.startsWith(`${projectId}_`) || key === projectId
      )
      keysToDelete.forEach(key => configCache.delete(key))
      console.log(`🗑️ Cleared chat config cache for project: ${projectId} (${keysToDelete.length} keys)`)
    } else {
      configCache.clear()
      console.log('🗑️ Cleared all chat config cache')
    }
  }

  /**
   * Fallback configuration when API fails
   * Returns hardcoded configuration matching the original code
   */
  private getFallbackConfig(projectId: string): ChatConfig {
    console.warn('⚠️ Using fallback chat configuration due to API error')
    
    const fallback: ChatConfig = {
      chat_messages: [],
      chart_cards: [
        {
          card_order: 1,
          card_id: 'brand-analysis',
          card_config: {
            title: 'Market Analysis',
            description: 'Market share and brand positioning analysis',
            icon: 'Building',
            tabKey: 'market-analysis',
            aiIntroduction: 'Market Analysis'
          }
        },
        {
          card_order: 2,
          card_id: 'pricing-analysis',
          card_config: {
            title: 'Pricing Analysis',
            description: 'Competitive pricing and distribution analysis',
            icon: 'Target',
            tabKey: 'pricing-analysis',
            aiIntroduction: 'Pricing Analysis'
          }
        },
        {
          card_order: 3,
          card_id: 'review-insights',
          card_config: {
            title: 'Customer Reviews',
            description: 'Pain points and satisfaction analysis',
            icon: 'MessageCircle',
            tabKey: 'review-insights',
            aiIntroduction: 'Customer Insights'
          }
        },
        {
          card_order: 4,
          card_id: 'competitor-analysis',
          card_config: {
            title: 'Competitive Analysis',
            description: 'Market positioning and competitive landscape',
            icon: 'Zap',
            tabKey: 'competitor-analysis',
            aiIntroduction: 'Competitive Product Analysis'
          }
        }
      ],
      chart_items: {
        'brand-analysis': [
          { chart_order: 1, chart_name: 'Total addressable market (TAM) and Market Share', chart_id: 'market-share-analysis' },
          { chart_order: 2, chart_name: 'Top 10 Best-Selling Brands', chart_id: 'best-selling-brands' },
          { chart_order: 3, chart_name: 'Sales Trend of Top 10 Brands', chart_id: 'sales-trend-analysis' },
          { chart_order: 4, chart_name: 'Top 10 Product Segments by Revenue/Volume', chart_id: 'segment-analysis' },
          { chart_order: 5, chart_name: 'Market Share by Sales Unit', chart_id: 'package-sales-trend' }
        ],
        'pricing-analysis': [
          { chart_order: 1, chart_name: 'Price Distribution Overview', chart_id: 'price-distribution-overview' },
          { chart_order: 2, chart_name: 'Price Distribution by Product Type', chart_id: 'price-distribution-by-type' },
          { chart_order: 3, chart_name: 'Price distribution by Brands', chart_id: 'price-distribution-by-brands' },
          { chart_order: 4, chart_name: 'Price vs. Revenue Distribution of Top Selling 20 Products', chart_id: 'price-vs-revenue' }
        ],
        'review-insights': [
          { chart_order: 1, chart_name: 'Top 10 Customer Pain Points', chart_id: 'customer-pain-points' },
          { chart_order: 2, chart_name: 'Top 10 Customer Delights', chart_id: 'customer-delights' },
          { chart_order: 3, chart_name: 'Use Case Sentiment Analysis', chart_id: 'use-case-sentiment' }
        ],
        'competitor-analysis': [
          { chart_order: 1, chart_name: 'Customer Satisfaction Overview', chart_id: 'customer-satisfaction-overview' },
          { chart_order: 2, chart_name: 'Product Comparison by Key Dimensions', chart_id: 'product-comparison-dimensions' },
          { chart_order: 3, chart_name: 'Product Comparison by Main Use Cases', chart_id: 'product-comparison-use-cases' }
        ]
      },
      chart_sections: {
        'brand-analysis': [
          { chart_order: 1, chart_id: 'market-share-analysis', chart_name: 'Market Share Analysis', is_active: true },
          { chart_order: 2, chart_id: 'best-selling-brands', chart_name: 'Best Selling Brands', is_active: true },
          { chart_order: 3, chart_id: 'sales-trend-analysis', chart_name: 'Sales Trend Analysis', is_active: true },
          { chart_order: 4, chart_id: 'segment-analysis', chart_name: 'Market Insights', is_active: true },
          { chart_order: 5, chart_id: 'package-sales-trend', chart_name: 'Package Preference', is_active: true }
        ],
        'pricing-analysis': [
          { chart_order: 1, chart_id: 'price-distribution-overview', chart_name: 'Price Distribution Overview', is_active: true },
          { chart_order: 2, chart_id: 'price-distribution-by-type', chart_name: 'Price Distribution by Type', is_active: true },
          { chart_order: 3, chart_id: 'price-distribution-by-brands', chart_name: 'Price Distribution by Brands', is_active: true },
          { chart_order: 4, chart_id: 'price-vs-revenue', chart_name: 'Price vs Revenue Analysis', is_active: true }
        ],
        'competitor-analysis': [
          { chart_order: 1, chart_id: 'customer-satisfaction-overview', chart_name: 'Customer Satisfaction Overview', is_active: true },
          { chart_order: 2, chart_id: 'product-comparison-dimensions', chart_name: 'Product Comparison Dimensions', is_active: true },
          { chart_order: 3, chart_id: 'product-comparison-use-cases', chart_name: 'Product Comparison Use Cases', is_active: true }
        ]
      },
      project_id: projectId
    }

    // Ensure fallback is normalized too
    return this.normalizeConfig(fallback)
  }

  /**
   * Check if configuration is already cached and not expired
   */
  isConfigCached(projectId: string): boolean {
    const cached = configCache.get(projectId)
    if (!cached) return false

    const now = Date.now()
    return now - cached.timestamp <= CACHE_DURATION
  }

  /**
   * Preload configuration for multiple projects
   * Returns statistics about the preload operation
   */
  async preloadConfigurations(projectIds: string[]): Promise<{
    total: number
    cached: number
    loaded: number
    failed: number
  }> {
    const stats = {
      total: projectIds.length,
      cached: 0,
      loaded: 0,
      failed: 0
    }

    // Skip already cached configs
    const projectsToLoad = projectIds.filter(id => {
      if (this.isConfigCached(id)) {
        stats.cached++
        return false
      }
      return true
    })

    console.log(`📋 Preloading ${projectsToLoad.length} configs (${stats.cached} already cached)`)

    if (projectsToLoad.length === 0) {
      console.log(`✅ All ${projectIds.length} configurations already cached`)
      return stats
    }

    // Load configurations in parallel
    const promises = projectsToLoad.map(async (id) => {
      try {
        await this.getChatConfig(id)
        stats.loaded++
        console.log(`✅ Config loaded for project: ${id}`)
      } catch (error) {
        stats.failed++
        console.warn(`❌ Failed to preload config for project ${id}:`, error)
      }
    })

    await Promise.allSettled(promises)
    
    console.log(`📋 Preload completed:`, stats)
    return stats
  }
}

// Export singleton instance
export const chatConfigService = ChatConfigService.getInstance() 