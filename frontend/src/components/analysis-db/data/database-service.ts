import { supabase } from '@/lib/supabase'

export interface ProductData {
  platform_id: string
  title: string
  brand: string
  price_usd: number
  monthly_sales_volume: number | null
  estimated_revenue: number | null
  category: string
  product_segment: string
  pack_count: number
  unit_price_calculated: number
  reviews_count: number
  rating: number | null
  product_url: string | null
}

export interface BrandCategoryData {
  brand: string
  dimmerRevenue: number
  switchRevenue: number
  dimmerVolume: number
  switchVolume: number
}

export interface ProductAnalysisData {
  priceVsRevenue: Array<{
    category: string
    products: Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>
  }>
  topProducts: Array<{
    category: string
    products: Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>
  }>
}

export class DatabaseService {
  
  // 获取品牌分类收入数据
  async getBrandCategoryRevenue(): Promise<BrandCategoryData[]> {
    const { data, error } = await supabase
      .from('product_wide_table')
      .select(`
        brand,
        category,
        monthly_sales_volume,
        estimated_revenue
      `)
      .eq('source', 'amazon')
      .neq('product_segment', 'OUT_OF_SCOPE')
      .not('product_segment', 'is', null)
      .not('brand', 'is', null)
      .not('estimated_revenue', 'is', null)

    if (error) {
      console.error('Error fetching brand category revenue:', error)
      return []
    }

    // 按品牌和类别聚合数据
    const brandData: Record<string, BrandCategoryData> = {}
    
    data.forEach((item: any) => {
      const brand = item.brand
      if (!brandData[brand]) {
        brandData[brand] = {
          brand,
          dimmerRevenue: 0,
          switchRevenue: 0,
          dimmerVolume: 0,
          switchVolume: 0
        }
      }

      const revenue = item.estimated_revenue || 0
      const volume = item.monthly_sales_volume || 0

      if (item.category === 'Dimmer Switches') {
        brandData[brand].dimmerRevenue += revenue
        brandData[brand].dimmerVolume += volume
      } else if (item.category === 'Light Switches') {
        brandData[brand].switchRevenue += revenue
        brandData[brand].switchVolume += volume
      }
    })

    return Object.values(brandData)
  }

  // 获取产品分析数据
  async getProductAnalysisData(): Promise<ProductAnalysisData> {
    const { data, error } = await supabase
      .from('product_wide_table')
      .select(`
        platform_id,
        title,
        brand,
        price_usd,
        unit_price_calculated,
        monthly_sales_volume,
        estimated_revenue,
        category,
        product_url
      `)
      .eq('source', 'amazon')
      .neq('product_segment', 'OUT_OF_SCOPE')
      .not('product_segment', 'is', null)
      .not('brand', 'is', null)
      .not('estimated_revenue', 'is', null)
      .order('estimated_revenue', { ascending: false })

    if (error) {
      console.error('Error fetching product analysis data:', error)
      return { 
        priceVsRevenue: [
          { category: 'Dimmer Switches', products: [] },
          { category: 'Light Switches', products: [] }
        ], 
        topProducts: [
          { category: 'Dimmer Switches', products: [] },
          { category: 'Light Switches', products: [] }
        ]
      }
    }

    // 转换数据格式
    const products = data.map((item: any) => ({
      id: item.platform_id,
      name: item.title,
      brand: item.brand,
      price: item.price_usd,
      unitPrice: item.unit_price_calculated || item.price_usd,
      revenue: item.estimated_revenue || 0,
      volume: item.monthly_sales_volume || 0,
      url: item.product_url || ''
    }))

    // 按类别分组
    const dimmerProducts = products.filter(p => p.name.toLowerCase().includes('dimmer') || 
      data.find((item: any) => item.platform_id === p.id)?.category === 'Dimmer Switches')
    const switchProducts = products.filter(p => !dimmerProducts.find(d => d.id === p.id))

    return {
      priceVsRevenue: [
        { category: 'Dimmer Switches', products: dimmerProducts },
        { category: 'Light Switches', products: switchProducts }
      ],
      topProducts: [
        { category: 'Dimmer Switches', products: dimmerProducts.slice(0, 20) },
        { category: 'Light Switches', products: switchProducts.slice(0, 20) }
      ]
    }
  }

  // 获取定价分析数据
  async getPricingAnalysisData(): Promise<{
    priceDistribution: Array<{
      category: string
      skuPrices: number[]
      unitPrices: number[]
      stats: {
        sku: {
          min: number
          q1: number
          median: number
          mean: number
          q3: number
          max: number
        }
        unit: {
          min: number
          q1: number
          median: number
          mean: number
          q3: number
          max: number
        }
      }
    }>
    brandPriceDistribution: Array<{
      category: string
      brands: Array<{
        name: string
        skuPrices: number[]
        unitPrices: number[]
      }>
    }>
  }> {
    const { data, error } = await supabase
      .from('product_wide_table')
      .select(`
        platform_id,
        title,
        brand,
        price_usd,
        unit_price_calculated,
        monthly_sales_volume,
        category,
        pack_count
      `)
      .eq('source', 'amazon')
      .neq('product_segment', 'OUT_OF_SCOPE')
      .not('product_segment', 'is', null)
      .not('brand', 'is', null)
      .not('price_usd', 'is', null)

    if (error) {
      console.error('Error fetching pricing analysis data:', error)
      return {
        priceDistribution: [],
        brandPriceDistribution: []
      }
    }

    // 按类别分组数据
    const dimmerProducts = data.filter(item => item.category === 'Dimmer Switches')
    const switchProducts = data.filter(item => item.category === 'Light Switches')

    // 计算统计数据的辅助函数
    const calculateStats = (prices: number[]) => {
      if (prices.length === 0) {
        return { min: 0, q1: 0, median: 0, mean: 0, q3: 0, max: 0 }
      }
      const sorted = [...prices].sort((a, b) => a - b)
      const min = sorted[0]
      const max = sorted[sorted.length - 1]
      const q1 = sorted[Math.floor(sorted.length / 4)]
      const median = sorted[Math.floor(sorted.length / 2)]
      const q3 = sorted[Math.floor((sorted.length * 3) / 4)]
      const mean = sorted.reduce((a, b) => a + b, 0) / sorted.length
      return { min, q1, median, mean, q3, max }
    }

    // 构建价格分布数据
    const dimmerSkuPrices = dimmerProducts.map(p => p.price_usd)
    const dimmerUnitPrices = dimmerProducts.map(p => p.unit_price_calculated || p.price_usd)
    const switchSkuPrices = switchProducts.map(p => p.price_usd)
    const switchUnitPrices = switchProducts.map(p => p.unit_price_calculated || p.price_usd)

    const priceDistribution = [
      {
        category: 'Dimmer Switches',
        skuPrices: dimmerSkuPrices,
        unitPrices: dimmerUnitPrices,
        stats: {
          sku: calculateStats(dimmerSkuPrices),
          unit: calculateStats(dimmerUnitPrices)
        }
      },
      {
        category: 'Light Switches',
        skuPrices: switchSkuPrices,
        unitPrices: switchUnitPrices,
        stats: {
          sku: calculateStats(switchSkuPrices),
          unit: calculateStats(switchUnitPrices)
        }
      }
    ]

    // 构建品牌价格分布数据
    const getBrandDistribution = (products: any[], category: string) => {
      const brandMap: Record<string, { skuPrices: number[], unitPrices: number[] }> = {}
      
      products.forEach(product => {
        if (!brandMap[product.brand]) {
          brandMap[product.brand] = { skuPrices: [], unitPrices: [] }
        }
        brandMap[product.brand].skuPrices.push(product.price_usd)
        brandMap[product.brand].unitPrices.push(product.unit_price_calculated || product.price_usd)
      })

      return {
        category,
        brands: Object.entries(brandMap).map(([name, prices]) => ({
          name,
          skuPrices: prices.skuPrices,
          unitPrices: prices.unitPrices
        }))
      }
    }

    const brandPriceDistribution = [
      getBrandDistribution(dimmerProducts, 'Dimmer Switches'),
      getBrandDistribution(switchProducts, 'Light Switches')
    ]

    return {
      priceDistribution,
      brandPriceDistribution
    }
  }

  // 获取市场洞察数据
  async getMarketInsightsData(): Promise<{
    segmentRevenue: {
      dimmerSwitches: Array<{
        segment: string
        revenue: number
        volume: number
        products: number
      }>
      lightSwitches: Array<{
        segment: string
        revenue: number
        volume: number
        products: number
      }>
    }
  }> {
    const { data, error } = await supabase
      .from('product_wide_table')
      .select(`
        product_segment,
        category,
        price_usd,
        monthly_sales_volume,
        estimated_revenue
      `)
      .eq('source', 'amazon')
      .neq('product_segment', 'OUT_OF_SCOPE')
      .not('product_segment', 'is', null)
      .not('estimated_revenue', 'is', null)

    if (error) {
      console.error('Error fetching market insights data:', error)
      return {
        segmentRevenue: {
          dimmerSwitches: [],
          lightSwitches: []
        }
      }
    }

    // 按产品细分和类别聚合数据
    const segmentData: Record<string, Record<string, any>> = {}
    
    data.forEach((item: any) => {
      const segment = item.product_segment
      const category = item.category
      
      if (!segmentData[segment]) {
        segmentData[segment] = {}
      }
      
      if (!segmentData[segment][category]) {
        segmentData[segment][category] = {
          segment: `${segment} ${category}`,
          revenue: 0,
          volume: 0,
          products: 0
        }
      }

      segmentData[segment][category].revenue += item.estimated_revenue || 0
      segmentData[segment][category].volume += item.monthly_sales_volume || 0
      segmentData[segment][category].products += 1
    })

    // 分离 Dimmer 和 Light Switches 数据
    const dimmerSwitches: any[] = []
    const lightSwitches: any[] = []

    Object.values(segmentData).forEach(categoryData => {
      Object.values(categoryData).forEach((item: any) => {
        if (item.segment.includes('Dimmer Switches')) {
          dimmerSwitches.push(item)
        } else if (item.segment.includes('Light Switches')) {
          lightSwitches.push(item)
        }
      })
    })

    // 按收入排序
    dimmerSwitches.sort((a, b) => b.revenue - a.revenue)
    lightSwitches.sort((a, b) => b.revenue - a.revenue)

    return {
      segmentRevenue: {
        dimmerSwitches,
        lightSwitches
      }
    }
  }

  // 获取包装偏好数据
  async getPackagePreferenceData(): Promise<{
    sameProductComparison: Array<{
      productName: string
      packSize: string
      packCount: number
      salesVolume: number
      price: number
      unitPrice: number
    }>
    packageDistribution: Array<{
      packSize: string
      count: number
      percentage: number
      salesVolume: number
    }>
    dimmerSwitches: Array<{
      packSize: string
      count: number
      percentage: number
      salesVolume: number
      salesRevenue: number
    }>
    lightSwitches: Array<{
      packSize: string
      count: number
      percentage: number
      salesVolume: number
      salesRevenue: number
    }>
  }> {
    const { data, error } = await supabase
      .from('product_wide_table')
      .select(`
        platform_id,
        title,
        brand,
        price_usd,
        unit_price_calculated,
        monthly_sales_volume,
        estimated_revenue,
        category,
        pack_count
      `)
      .eq('source', 'amazon')
      .neq('product_segment', 'OUT_OF_SCOPE')
      .not('product_segment', 'is', null)
      .not('pack_count', 'is', null)

    if (error) {
      console.error('Error fetching package preference data:', error)
      return {
        sameProductComparison: [],
        packageDistribution: [],
        dimmerSwitches: [],
        lightSwitches: []
      }
    }

    // 生成包装大小标签
    const getPackSizeLabel = (packCount: number) => {
      if (packCount === 1) return 'Single Pack'
      if (packCount === 2) return '2 Pack'
      if (packCount === 3) return '3 Pack'
      if (packCount === 4) return '4 Pack'
      if (packCount === 5) return '5 Pack'
      if (packCount >= 6 && packCount <= 10) return '6-10 Pack'
      return '10+ Pack'
    }

    // 准备数据
    const products = data.map((item: any) => ({
      productName: item.title,
      packSize: getPackSizeLabel(item.pack_count),
      packCount: item.pack_count,
      salesVolume: item.monthly_sales_volume || 0,
      price: item.price_usd,
      unitPrice: item.unit_price_calculated || item.price_usd,
      category: item.category,
      revenue: item.estimated_revenue || 0
    }))

    // 按类别分组
    const dimmerProducts = products.filter(p => p.category === 'Dimmer Switches')
    const switchProducts = products.filter(p => p.category === 'Light Switches')

    // 计算包装分布的辅助函数
    const calculatePackageDistribution = (products: any[]) => {
      const packSizeMap: Record<string, any> = {}
      
      products.forEach(product => {
        if (!packSizeMap[product.packSize]) {
          packSizeMap[product.packSize] = {
            packSize: product.packSize,
            count: 0,
            salesVolume: 0,
            salesRevenue: 0
          }
        }
        packSizeMap[product.packSize].count += 1
        packSizeMap[product.packSize].salesVolume += product.salesVolume
        packSizeMap[product.packSize].salesRevenue += product.revenue
      })

      const total = products.length
      return Object.values(packSizeMap).map((item: any) => ({
        ...item,
        percentage: total > 0 ? (item.count / total) * 100 : 0
      }))
    }

    // 计算各类别的包装分布
    const dimmerPackageDistribution = calculatePackageDistribution(dimmerProducts)
    const switchPackageDistribution = calculatePackageDistribution(switchProducts)
    const overallPackageDistribution = calculatePackageDistribution(products)

    // 同产品比较数据（选择一些有多个包装的产品）
    const sameProductComparison = products.slice(0, 10).map(product => ({
      productName: product.productName,
      packSize: product.packSize,
      packCount: product.packCount,
      salesVolume: product.salesVolume,
      price: product.price,
      unitPrice: product.unitPrice
    }))

    return {
      sameProductComparison,
      packageDistribution: overallPackageDistribution,
      dimmerSwitches: dimmerPackageDistribution,
      lightSwitches: switchPackageDistribution
    }
  }
}

export const databaseService = new DatabaseService() 