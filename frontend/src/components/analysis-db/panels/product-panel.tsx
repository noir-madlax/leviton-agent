"use client"

import React, { useState, useEffect } from 'react'
import { X, ExternalLink, Filter, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useProductPanel } from '@/components/analysis-db/contexts/product-panel-context'

interface Product {
  id: string
  name: string
  brand: string
  price: number
  unitPrice: number
  revenue: number
  volume: number
  url: string
  category?: string
  productSegment?: string
  packCount?: number
}

export function ProductPanel() {
  const { isOpen, products, title, subtitle, showFilters, closePanel } = useProductPanel()
  const [filteredProducts, setFilteredProducts] = useState<Product[]>(products)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedBrand, setSelectedBrand] = useState('all')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [priceRange, setPriceRange] = useState({ min: '', max: '' })
  const [selectedPackSize, setSelectedPackSize] = useState('all')

  // Reset filters when products change
  useEffect(() => {
    setFilteredProducts(products)
    setSearchTerm('')
    setSelectedBrand('all')
    setSelectedCategory('all')
    setPriceRange({ min: '', max: '' })
    setSelectedPackSize('all')
  }, [products])

  // Apply filters
  useEffect(() => {
    let filtered = products

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(product => 
        product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.brand.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Brand filter
    if (selectedBrand !== 'all') {
      filtered = filtered.filter(product => product.brand === selectedBrand)
    }

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(product => product.category === selectedCategory)
    }

    // Price range filter
    if (priceRange.min || priceRange.max) {
      filtered = filtered.filter(product => {
        const price = product.unitPrice
        const min = priceRange.min ? parseFloat(priceRange.min) : 0
        const max = priceRange.max ? parseFloat(priceRange.max) : Infinity
        return price >= min && price <= max
      })
    }

    // Pack size filter
    if (selectedPackSize !== 'all') {
      filtered = filtered.filter(product => {
        if (!product.packCount) return selectedPackSize === '1'
        return product.packCount.toString() === selectedPackSize
      })
    }

    setFilteredProducts(filtered)
  }, [products, searchTerm, selectedBrand, selectedCategory, priceRange, selectedPackSize])

  // Get unique values for filters
  const uniqueBrands = [...new Set(products.map(p => p.brand))].sort()
  const uniqueCategories = [...new Set(products.map(p => p.category).filter(Boolean))].sort()
  const uniquePackSizes = [...new Set(products.map(p => p.packCount?.toString() || '1'))].sort((a, b) => parseInt(a) - parseInt(b))

  const handleProductClick = (url: string) => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  const formatPrice = (price: number) => `$${price.toFixed(2)}`
  const formatVolume = (volume: number) => volume.toLocaleString()
  const formatRevenue = (revenue: number) => `$${revenue.toLocaleString()}`

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={closePanel}
      />
      
      {/* Panel */}
      <div className={`fixed right-0 top-0 h-full w-full max-w-4xl bg-white shadow-xl z-50 transform transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
              {subtitle && <p className="text-gray-600 mt-1">{subtitle}</p>}
              <p className="text-sm text-gray-500 mt-2">
                Showing {filteredProducts.length} of {products.length} products
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={closePanel}
              className="flex items-center gap-2"
            >
              <X className="w-4 h-4" />
              Close
            </Button>
          </div>

          {/* Filters */}
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-4 h-4 text-gray-500" />
              <span className="font-medium text-gray-700">Filters</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {/* Search */}
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Search products..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Brand Filter */}
              {showFilters?.brand && uniqueBrands.length > 1 && (
                <select
                  value={selectedBrand}
                  onChange={(e) => setSelectedBrand(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Brands</option>
                  {uniqueBrands.map(brand => (
                    <option key={brand} value={brand}>{brand}</option>
                  ))}
                </select>
              )}

              {/* Category Filter */}
              {showFilters?.category && uniqueCategories.length > 1 && (
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Categories</option>
                  {uniqueCategories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              )}

              {/* Pack Size Filter */}
              {showFilters?.packSize && uniquePackSizes.length > 1 && (
                <select
                  value={selectedPackSize}
                  onChange={(e) => setSelectedPackSize(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Pack Sizes</option>
                  {uniquePackSizes.map(size => (
                    <option key={size} value={size}>
                      {size} Pack{size !== '1' ? 's' : ''}
                    </option>
                  ))}
                </select>
              )}

              {/* Price Range Filter */}
              {showFilters?.priceRange && (
                <div className="flex gap-2 col-span-1 md:col-span-2 lg:col-span-1">
                  <Input
                    placeholder="Min $"
                    type="number"
                    value={priceRange.min}
                    onChange={(e) => setPriceRange(prev => ({ ...prev, min: e.target.value }))}
                    className="w-full"
                  />
                  <Input
                    placeholder="Max $"
                    type="number"
                    value={priceRange.max}
                    onChange={(e) => setPriceRange(prev => ({ ...prev, max: e.target.value }))}
                    className="w-full"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Product List */}
          <div className="flex-1 overflow-y-auto p-6">
            {filteredProducts.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">No products found matching your filters.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredProducts.map((product) => (
                  <div
                    key={product.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-white"
                    onClick={() => handleProductClick(product.url)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-gray-900 line-clamp-2">
                            {product.name}
                          </h3>
                          <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        </div>
                        <p className="text-sm text-blue-600 font-medium mb-2">{product.brand}</p>
                        {product.category && (
                          <p className="text-xs text-gray-500 mb-2">{product.category}</p>
                        )}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Price:</span>
                            <p className="font-medium">{formatPrice(product.price)}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Unit Price:</span>
                            <p className="font-medium">{formatPrice(product.unitPrice)}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Volume:</span>
                            <p className="font-medium">{formatVolume(product.volume)}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Revenue:</span>
                            <p className="font-medium">{formatRevenue(product.revenue)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
} 