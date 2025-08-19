"use client"

import { useEffect, useMemo, useState } from 'react'
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Search } from "lucide-react"
import { useT } from '@/i18n/hooks'
import { BaseFilterProps } from '../common/types'
import { databaseService } from '@/components/analysis-db/data/database-service'
import { useParams } from 'next/navigation'
import { useUnifiedFilter } from '@/components/analysis-db/contexts/unified-filter-context'

interface AsinFilterProps extends BaseFilterProps {
  // 受控值：选中的 ASIN 列表
  value: string[]
  // 变化回调（即时生效，Apply 按钮由外层 FilterRenderer 负责）
  onChange: (asins: string[]) => void
  // 图表名称（保持签名一致，当前实现不依赖它获取 options）
  chartName: string
}

interface ProductInfo {
  platform_id: string
  title: string
  brand: string
  price_usd?: number
  reviews_count?: number
  category?: string
}

/**
 * ASIN 多选 + 搜索（紧凑内联样式）
 * - 数据源：databaseService.getAvailableAsins(projectId)（与 competitor-asin-selector 一致）
 * - 无按钮：选中即触发 onChange；上层 FilterRenderer 统一处理 Apply
 * - 入参/出参保持不变
 */
export function AsinFilter({ value, onChange, chartName, disabled = false, loading = false, className = "" }: AsinFilterProps) {
  const t = useT()
  const params = useParams() as { id?: string }
  const projectId = params?.id
  const { getChartConfig } = useUnifiedFilter()
  const chartConfig = getChartConfig(chartName)
  const defaultValues = useMemo<string[]>(() => { // 来自 filter_values，作为默认选中
    const vals = chartConfig?.filters?.asins?.values
    return Array.isArray(vals) ? vals as string[] : []
  }, [chartConfig?.filters?.asins?.values])

  // 数据源：可选产品（含品牌/标题等，便于展示与搜索）
  const [products, setProducts] = useState<ProductInfo[]>([])
  const [fetching, setFetching] = useState(false)

  useEffect(() => {
    let mounted = true

    // 1) 在首次渲染时应用默认选中（filter_values）
    if (value.length === 0 && defaultValues.length > 0) {
      onChange(defaultValues)
    }

    const load = async () => {
      try {
        setFetching(true)
        const list = await databaseService.getAvailableAsins(projectId)
        if (!mounted) return
        setProducts(list || [])
      } catch (e) {
        console.warn('ASIN options load failed:', e)
        if (!mounted) return
        setProducts([])
      } finally {
        if (mounted) setFetching(false)
      }
    }
    // 即使没有 projectId 也调用（会走 fallback），确保有选项
    load()
    return () => { mounted = false }
  }, [projectId])

  // 搜索词
  const [query, setQuery] = useState('')

  // 品牌/类目筛选
  const uniqueBrands = useMemo(() => Array.from(new Set(products.map(p => p.brand))).sort(), [products])
  const uniqueCategories = useMemo(() => Array.from(new Set(products.map(p => p.category))).sort(), [products])
  const [selectedBrand, setSelectedBrand] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')

  // 过滤后的产品
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    let list = products

    // 文本搜索
    if (q) {
      list = list.filter(p =>
        p.title?.toLowerCase().includes(q) ||
        p.brand?.toLowerCase().includes(q) ||
        p.platform_id?.toLowerCase().includes(q)
      )
    }

    // 品牌筛选
    if (selectedBrand) {
      list = list.filter(p => p.brand === selectedBrand)
    }

    // 类目筛选
    if (selectedCategory) {
      list = list.filter(p => p.category === selectedCategory)
    }

    // 按评论数降序（与 CompetitorAsinSelector 对齐）
    return [...list].sort((a, b) => (b.reviews_count || 0) - (a.reviews_count || 0))
  }, [products, query, selectedBrand, selectedCategory])

  // 切换选中
  const toggle = (asin: string) => {
    if (disabled || loading) return
    if (value.includes(asin)) {
      onChange(value.filter(a => a !== asin))
    } else {
      onChange([...value, asin])
    }
  }

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <div className="text-sm text-gray-600">ASIN</div>

      {/* 搜索框 + 筛选框（一行布局） */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type ASIN or product name"
            className="pl-10"
            disabled={disabled || loading || fetching}
          />
        </div>
        <select
          className="px-3 py-2 border rounded-md"
          value={selectedBrand}
          onChange={(e) => setSelectedBrand(e.target.value)}
        >
          <option value="">All Brands</option>
          {uniqueBrands.map(b => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
        <select
          className="px-3 py-2 border rounded-md"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          {uniqueCategories.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div className="w-full mt-2 p-2 bg-blue-50 rounded">
        <div className="text-xs text-gray-700 mb-1">{t('filters.selectedItems', { count: value.length })}</div>
        {value.length > 0 && (
          <div className="flex flex-wrap gap-1 w-full">
            {value.map((asin) => (
              <button
                type="button"
                key={asin}
                onClick={() => toggle(asin)}
                className="px-2 py-0.5 text-[10px] leading-4 rounded bg-white text-gray-700 border hover:bg-gray-100"
                title="Click to remove"
              >
                {asin}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 固定产品列表面板（不使用浮窗） */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No products found matching your criteria
          </div>
        ) : (
          filtered.slice(0, 50).map((p) => {
            const asin = p.platform_id
            const checked = value.includes(asin)
            return (
              <div
                key={asin}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  checked
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => toggle(asin)}
              >
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={checked}
                    onChange={() => toggle(asin)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start gap-2">
                      <h4 className="font-medium text-gray-900 text-sm leading-tight">
                        {p.title}
                      </h4>
                      <div className="flex flex-col items-end text-xs text-gray-500">
                        {p.price_usd !== undefined && <span>${p.price_usd}</span>}
                        {p.reviews_count !== undefined && <span>{p.reviews_count} reviews</span>}
                      </div>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                      <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                        {p.brand}
                      </span>
                      <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                        {p.category}
                      </span>
                      <span className="text-gray-400">ASIN: {asin}</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        )}
        {filtered.length > 50 && (
          <div className="text-center py-4 text-sm text-gray-500 border-t">
            Showing top 50 products. Use filters to narrow down results.
          </div>
        )}
      </div>

      {/* 已选数量 + 右侧已选展示（独立区域） */}

    </div>
  )
}

