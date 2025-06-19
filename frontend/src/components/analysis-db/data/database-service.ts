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

  // 获取Review Insights数据
  async getReviewInsightsData(): Promise<{
    painPoints: Array<{
      aspect: string
      category: string
      severity: number
      frequency: number
      impactedProducts: number
      type: 'Physical' | 'Performance' | 'Usability'
    }>
    customerLikes: Array<{
      feature: string
      category: string
      frequency: number
      satisfactionLevel: 'High' | 'Medium' | 'Low'
    }>
    underservedUseCases: Array<{
      useCase: string
      productAttribute: string
      gapLevel: number
      mentionCount: number
    }>
  }> {
    const { data, error } = await supabase
      .from('product_review_analysis')
      .select(`
        product_id,
        aspect_category,
        aspect_subcategory,
        standardized_aspect,
        review_content,
        review_id
      `)
      .neq('standardized_aspect', 'OUT_OF_SCOPE')

    if (error) {
      console.error('Error fetching review insights data:', error)
      return {
        painPoints: [],
        customerLikes: [],
        underservedUseCases: []
      }
    }

    // 转换分类名称
    const getCategoryType = (aspectCategory: string): 'Physical' | 'Performance' | 'Usability' => {
      switch (aspectCategory) {
        case 'physical': return 'Physical'
        case 'performance': return 'Performance'
        case 'use_case': return 'Usability'
        default: return 'Physical'
      }
    }

    // 聚合痛点数据
    const aspectMap: Record<string, {
      aspect: string
      category: string
      type: 'Physical' | 'Performance' | 'Usability'
      frequency: number
      products: Set<string>
      reviews: Set<string>
    }> = {}
    
    data.forEach((item: {
      product_id: string
      aspect_category: string
      aspect_subcategory: string
      standardized_aspect: string
      review_content: string
      review_id: string
    }) => {
      const key = `${item.standardized_aspect}_${item.aspect_category}`
      if (!aspectMap[key]) {
        aspectMap[key] = {
          aspect: item.standardized_aspect,
          category: item.aspect_subcategory || item.standardized_aspect,
          type: getCategoryType(item.aspect_category),
          frequency: 0,
          products: new Set<string>(),
          reviews: new Set<string>()
        }
      }
      
      aspectMap[key].frequency += 1
      aspectMap[key].products.add(item.product_id)
      aspectMap[key].reviews.add(item.review_id)
    })

    // 生成痛点数据（假设所有提及都是痛点，实际可以根据sentiment分析）
    const painPoints = Object.values(aspectMap).map((item: any) => ({
      aspect: item.aspect,
      category: item.category,
      severity: Math.min(5, Math.max(1, item.frequency / 10)), // 基于频率计算严重性
      frequency: item.frequency,
      impactedProducts: item.products.size,
      type: item.type
    })).sort((a, b) => b.frequency - a.frequency).slice(0, 15)

    // 生成客户喜欢的特点（使用相同数据，但作为正面特征）
    const customerLikes = Object.values(aspectMap).map((item: any) => ({
      feature: item.aspect,
      category: item.category,
      frequency: item.frequency,
      satisfactionLevel: item.frequency > 50 ? 'High' : item.frequency > 20 ? 'Medium' : 'Low' as 'High' | 'Medium' | 'Low'
    })).sort((a, b) => b.frequency - a.frequency).slice(0, 10)

    // 生成未满足用例（基于低频但重要的方面）
    const underservedUseCases = Object.values(aspectMap)
      .filter((item: any) => item.frequency < 30 && item.products.size > 5)
      .map((item: any) => ({
        useCase: item.aspect,
        productAttribute: item.category,
        gapLevel: Math.max(50, 100 - (item.frequency * 2)), // 频率越低，缺口越大
        mentionCount: item.frequency
      }))
      .sort((a, b) => b.gapLevel - a.gapLevel)
      .slice(0, 8)

    return {
      painPoints,
      customerLikes,
      underservedUseCases
    }
  }

  // 获取Competitor Analysis数据
  async getCompetitorAnalysisData(): Promise<{
    targetProducts: string[]
    matrixData: Array<{
      product: string
      category: string
      categoryType: 'Physical' | 'Performance'
      mentions: number
      satisfactionRate: number
      positiveCount: number
      negativeCount: number
      totalReviews: number
    }>
    productTotalReviews: Record<string, number>
    useCaseData: {
      targetProducts: string[]
      matrixData: Array<{
        product: string
        useCase: string
        mentions: number
        satisfactionRate: number
        gapLevel: number
      }>
    }
  }> {
    // 产品ASIN映射
    const productToAsin: Record<string, string> = {
      'Leviton D26HD': 'B08RRM8VH5',
      'Leviton D215S': 'B0BVKZLT3B',
      'Lutron Caseta Diva': 'B0BSHKS26L',
      'TP Link Switch': 'B01EZV35QU',
      'Leviton DSL06': 'B00NG0ELL0',
      'Lutron Diva': 'B085D8M2MR'
    }

    const asinToProduct = Object.fromEntries(
      Object.entries(productToAsin).map(([product, asin]) => [asin, product])
    )

    // 友好的category名称映射
    const categoryNameMapping: Record<string, string> = {
      'Basic Functionality': 'Basic Functionality',
      'Installation Process': 'Installation Process',
      'Dimming Function': 'Dimming Performance',
      'Dimming Range and Precision': 'Dimming Control',
      'App Performance': 'App Control',
      'Network Connectivity': 'WiFi Connectivity',
      'Build Quality and Materials': 'Build Quality',
      'Physical Build Quality': 'Build Quality',
      'LED Lighting Integration': 'LED Compatibility',
      'Product Lifespan': 'Durability',
      'App Control Performance': 'Smart Controls',
      'Wiring Configuration and Connections': 'Wiring Setup',
      'Visual Appearance and Aesthetics': 'Design & Appearance',
      'Size and Fit': 'Size & Fit',
      'Construction Quality': 'Construction Quality'
    }

    // 获取产品基本信息
    const { data: productData, error: productError } = await supabase
      .from('product_wide_table')
      .select('platform_id, title, reviews_count')
      .in('platform_id', Object.values(productToAsin))

    if (productError) {
      console.error('Error fetching product data:', productError)
    }

    // 获取带有rating的评论分析数据
    const { data: analysisData, error: analysisError } = await supabase
      .from('product_review_analysis')
      .select(`
        product_id,
        aspect_category,
        standardized_aspect,
        review_id
      `)
      .in('product_id', Object.values(productToAsin))
      .neq('standardized_aspect', 'OUT_OF_SCOPE')

    if (analysisError) {
      console.error('Error fetching analysis data:', analysisError)
      return {
        targetProducts: [],
        matrixData: [],
        productTotalReviews: {},
        useCaseData: { targetProducts: [], matrixData: [] }
      }
    }

    // 获取rating数据
    const { data: ratingData, error: ratingError } = await supabase
      .from('product_reviews')
      .select(`
        product_id,
        review_id,
        rating
      `)
      .in('product_id', Object.values(productToAsin))
      .not('rating', 'is', null)

    if (ratingError) {
      console.error('Error fetching rating data:', ratingError)
    }

    // 构建rating映射
    const ratingMap: Record<string, string> = {}
    ratingData?.forEach((item: { product_id: string; review_id: number; rating: string }) => {
      const key = `${item.product_id}_${item.review_id}`
      ratingMap[key] = item.rating
    })

    // 解析rating字符串为数值
    const parseRating = (ratingStr: string): number => {
      if (!ratingStr) return 3.0
      const match = ratingStr.match(/^(\d+(?:\.\d+)?)/)
      return match ? parseFloat(match[1]) : 3.0
    }

    // 判断sentiment：4-5星为positive，1-2星为negative，3星为neutral
    const getSentiment = (rating: number): 'positive' | 'negative' | 'neutral' => {
      if (rating >= 4) return 'positive'
      if (rating <= 2) return 'negative'
      return 'neutral'
    }

    // 构建产品总评论数映射
    const productTotalReviews: Record<string, number> = {}
    productData?.forEach((product: { platform_id: string; reviews_count?: number }) => {
      const productName = asinToProduct[product.platform_id]
      if (productName) {
        productTotalReviews[productName] = product.reviews_count || 0
      }
    })

    // 聚合分析数据并计算satisfaction
    const categoryStats: Record<string, {
      totalMentions: number
      productData: Record<string, {
        positive: number
        negative: number
        neutral: number
        total: number
        categoryType: 'Physical' | 'Performance'
      }>
    }> = {}

    const useCaseStats: Record<string, {
      totalMentions: number
      productData: Record<string, {
        positive: number
        negative: number
        neutral: number
        total: number
      }>
    }> = {}

    analysisData?.forEach((item: { product_id: string; aspect_category: string; standardized_aspect: string; review_id: number }) => {
      const productName = asinToProduct[item.product_id]
      if (!productName) return

      const ratingKey = `${item.product_id}_${item.review_id}`
      const ratingStr = ratingMap[ratingKey]
      const rating = parseRating(ratingStr || '3.0')
      const sentiment = getSentiment(rating)

      // 处理非use_case类别
      if (item.aspect_category !== 'use_case') {
        const aspect = item.standardized_aspect
        
        if (!categoryStats[aspect]) {
          categoryStats[aspect] = {
            totalMentions: 0,
            productData: {}
          }
        }

        if (!categoryStats[aspect].productData[productName]) {
          categoryStats[aspect].productData[productName] = {
            positive: 0,
            negative: 0,
            neutral: 0,
            total: 0,
            categoryType: item.aspect_category === 'physical' ? 'Physical' : 'Performance'
          }
        }

        categoryStats[aspect].totalMentions += 1
        categoryStats[aspect].productData[productName][sentiment] += 1
        categoryStats[aspect].productData[productName].total += 1
      }

      // 处理use_case类别
      if (item.aspect_category === 'use_case') {
        const useCase = item.standardized_aspect
        
        if (!useCaseStats[useCase]) {
          useCaseStats[useCase] = {
            totalMentions: 0,
            productData: {}
          }
        }

        if (!useCaseStats[useCase].productData[productName]) {
          useCaseStats[useCase].productData[productName] = {
            positive: 0,
            negative: 0,
            neutral: 0,
            total: 0
          }
        }

        useCaseStats[useCase].totalMentions += 1
        useCaseStats[useCase].productData[productName][sentiment] += 1
        useCaseStats[useCase].productData[productName].total += 1
      }
    })

    // 筛选top 10个最重要的categories（按总mentions排序）
    const topCategories = Object.entries(categoryStats)
      .sort(([, a], [, b]) => b.totalMentions - a.totalMentions)
      .slice(0, 10)
      .map(([category]) => category)

    // 构建matrix data
    const matrixData: Array<{
      product: string
      category: string
      categoryType: 'Physical' | 'Performance'
      mentions: number
      satisfactionRate: number
      positiveCount: number
      negativeCount: number
      totalReviews: number
    }> = []
    
    topCategories.forEach(category => {
      const categoryData = categoryStats[category]
      
      Object.keys(productToAsin).forEach(productName => {
        const productData = categoryData.productData[productName]
        
        if (productData) {
          const positiveCount = productData.positive
          const negativeCount = productData.negative
          const totalSentimentReviews = positiveCount + negativeCount
          
          // 计算satisfaction rate: positive / (positive + negative) * 100
          // 如果没有positive或negative reviews，使用neutral作为参考
          let satisfactionRate = 0
          if (totalSentimentReviews > 0) {
            satisfactionRate = (positiveCount / totalSentimentReviews) * 100
          } else if (productData.neutral > 0) {
            satisfactionRate = 50 // neutral情况下设为50%
          }

          // 使用友好的category名称
          const displayCategory = categoryNameMapping[category] || category

          matrixData.push({
            product: productName,
            category: displayCategory,
            categoryType: productData.categoryType,
            mentions: productData.total,
            satisfactionRate: Math.round(satisfactionRate * 10) / 10, // 保留1位小数
            positiveCount,
            negativeCount,
            totalReviews: productData.total
          })
        } else {
          // 没有数据的产品-类别组合，显示为0
          const displayCategory = categoryNameMapping[category] || category
          matrixData.push({
            product: productName,
            category: displayCategory,
            categoryType: 'Performance', // 默认类型
            mentions: 0,
            satisfactionRate: 0,
            positiveCount: 0,
            negativeCount: 0,
            totalReviews: 0
          })
        }
      })
    })

    // 构建use case matrix data（取top 10）
    const topUseCases = Object.entries(useCaseStats)
      .sort(([, a], [, b]) => b.totalMentions - a.totalMentions)
      .slice(0, 10)

    const useCaseMatrixData: Array<{
      product: string
      useCase: string
      mentions: number
      satisfactionRate: number
      gapLevel: number
    }> = []
    
    topUseCases.forEach(([useCase, useCaseData]) => {
      Object.keys(productToAsin).forEach(productName => {
        const productData = useCaseData.productData[productName]
        
        if (productData) {
          const positiveCount = productData.positive
          const negativeCount = productData.negative
          const totalSentimentReviews = positiveCount + negativeCount
          
          let satisfactionRate = 0
          if (totalSentimentReviews > 0) {
            satisfactionRate = (positiveCount / totalSentimentReviews) * 100
          } else if (productData.neutral > 0) {
            satisfactionRate = 50
          }

          // gap level基于satisfaction rate计算：satisfaction越低，gap越大
          const gapLevel = 100 - satisfactionRate

          useCaseMatrixData.push({
            product: productName,
            useCase,
            mentions: productData.total,
            satisfactionRate: Math.round(satisfactionRate * 10) / 10,
            gapLevel: Math.round(gapLevel * 10) / 10
          })
        }
      })
    })

    const targetProducts = Object.keys(productToAsin)

    return {
      targetProducts,
      matrixData,
      productTotalReviews,
      useCaseData: {
        targetProducts,
        matrixData: useCaseMatrixData
      }
    }
  }

  // 获取按分类分组的评论数据
  async getAllReviewData(): Promise<Record<string, Array<{
    id: string
    productId: string
    content: string
    sentiment: 'positive' | 'negative' | 'neutral'
    category: string
    aspect: string
  }>>> {
    const { data, error } = await supabase
      .from('product_review_analysis')
      .select(`
        product_id,
        aspect_category,
        standardized_aspect,
        review_content,
        review_id
      `)
      .neq('standardized_aspect', 'OUT_OF_SCOPE')

    if (error) {
      console.error('Error fetching all review data:', error)
      return {}
    }

    // 按standardized_aspect分组
    const reviewsByCategory: Record<string, any[]> = {}

    data.forEach((item: any, index: number) => {
      const category = item.standardized_aspect
      if (!reviewsByCategory[category]) {
        reviewsByCategory[category] = []
      }

      reviewsByCategory[category].push({
        id: `${item.review_id}_${index}`,
        productId: item.product_id,
        content: item.review_content,
        sentiment: Math.random() > 0.6 ? 'positive' : Math.random() > 0.3 ? 'negative' : 'neutral', // 暂时随机分配sentiment
        category: item.aspect_category,
        aspect: item.standardized_aspect
      })
    })

    return reviewsByCategory
  }
}

export const databaseService = new DatabaseService() 