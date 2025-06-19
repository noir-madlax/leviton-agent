"use client"

import React, { useState } from 'react'
import { X, Star, Shield, Filter, Search, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from '@/components/ui/pagination'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { useReviewPanel } from '@/components/analysis-db/contexts/review-panel-context'
import { Review } from '@/components/analysis-db/data/review-data'

interface ReviewPanelProps {
  showFilters?: {
    sentiment?: boolean
    brand?: boolean
    rating?: boolean
    verified?: boolean
  }
}

export function ReviewPanel({ 
  showFilters = { sentiment: true, brand: true, rating: true, verified: true }
}: ReviewPanelProps) {
  const { isOpen, reviews, title, subtitle, closePanel } = useReviewPanel()
  
  const [filteredReviews, setFilteredReviews] = useState<Review[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [sentimentFilter, setSentimentFilter] = useState<string>('all')
  const [brandFilter, setBrandFilter] = useState<string>('all')
  const [ratingFilter, setRatingFilter] = useState<string>('all')
  const [verifiedFilter, setVerifiedFilter] = useState<string>('all')
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10
  
  // Brand filter search state
  const [brandSearchOpen, setBrandSearchOpen] = useState(false)
  const [brandSearchTerm, setBrandSearchTerm] = useState('')

  // Apply filters
  React.useEffect(() => {
    if (!reviews || reviews.length === 0) {
      setFilteredReviews([])
      return
    }

    let filtered = [...reviews]

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(review => {
        const content = review.text || ''
        return content.toLowerCase().includes(searchTerm.toLowerCase())
      })
    }

    // Sentiment filter
    if (sentimentFilter !== 'all') {
      filtered = filtered.filter(review => review.sentiment === sentimentFilter)
    }

    // Brand filter
    if (brandFilter !== 'all') {
      filtered = filtered.filter(review => {
        const brand = review.brand || ''
        return brand === brandFilter
      })
    }

    // Rating filter
    if (ratingFilter !== 'all') {
      filtered = filtered.filter(review => {
        const rating = getStarRating(review.rating || 0)
        if (ratingFilter === 'high') {
          return rating >= 4
        } else if (ratingFilter === 'low') {
          return rating <= 2
        } else if (ratingFilter === 'mid') {
          return rating === 3
        }
        return true
      })
    }

    // Verified filter
    if (verifiedFilter !== 'all') {
      filtered = filtered.filter(review => 
        verifiedFilter === 'verified' ? review.verified : !review.verified
      )
    }

    setFilteredReviews(filtered)
    setCurrentPage(1) // Reset to first page when filters change
  }, [reviews, searchTerm, sentimentFilter, brandFilter, ratingFilter, verifiedFilter])

  // Get unique values for filters
  const uniqueBrands = React.useMemo(() => {
    if (!reviews || reviews.length === 0) return []
    return [...new Set(reviews.map(r => r.brand || '').filter(Boolean))].sort()
  }, [reviews])
  
  // Filter brands based on search term
  const filteredBrands = uniqueBrands.filter(brand => 
    brand && brand.toLowerCase().includes(brandSearchTerm.toLowerCase())
  )

  // Pagination calculations
  const totalPages = Math.ceil(filteredReviews.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentReviews = filteredReviews.slice(startIndex, endIndex)

  // Helper functions
  const getStarRating = (rating: number | string | undefined) => {
    if (typeof rating === 'number') {
      return rating;
    }
    if (typeof rating === 'string') {
      const match = rating.match(/(\d+\.?\d*)/);
      return match ? parseFloat(match[1]) : 0;
    }
    return 0;
  }

  const getSentimentBadgeColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'bg-green-100 text-green-800'
      case 'negative': return 'bg-red-100 text-red-800'
      default: return 'bg-yellow-100 text-yellow-800'
    }
  }

  const clearFilters = () => {
    setSearchTerm('')
    setSentimentFilter('all')
    setBrandFilter('all')
    setRatingFilter('all')
    setVerifiedFilter('all')
    setBrandSearchTerm('')
  }

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black/20" onClick={closePanel} />
      <div className="absolute right-0 top-0 h-full w-full max-w-4xl bg-white shadow-xl">
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="border-b bg-gray-50 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{title || 'Reviews'}</h2>
                {subtitle && (
                  <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
                )}
                <p className="text-sm text-gray-500 mt-1">
                  Showing {startIndex + 1}-{Math.min(endIndex, filteredReviews.length)} of {filteredReviews.length} reviews
                  {filteredReviews.length !== (reviews?.length || 0) && ` (${reviews?.length || 0} total)`}
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={closePanel}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Filters */}
          <div className="border-b bg-white px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search reviews..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Sentiment Filter */}
              {showFilters?.sentiment && (
                <Select value={sentimentFilter} onValueChange={setSentimentFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sentiment" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sentiments</SelectItem>
                    <SelectItem value="positive">Positive</SelectItem>
                    <SelectItem value="negative">Negative</SelectItem>
                    <SelectItem value="neutral">Neutral</SelectItem>
                  </SelectContent>
                </Select>
              )}

              {/* Brand Filter - Searchable */}
              {showFilters?.brand && uniqueBrands.length > 0 && (
                <Popover open={brandSearchOpen} onOpenChange={setBrandSearchOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      role="combobox"
                      aria-expanded={brandSearchOpen}
                      className="justify-between"
                    >
                      {brandFilter === 'all' ? 'All Brands' : brandFilter}
                      <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[300px] p-0">
                    <Command>
                      <CommandInput 
                        placeholder="Search brands..." 
                        value={brandSearchTerm}
                        onValueChange={setBrandSearchTerm}
                      />
                      <CommandList>
                        <CommandEmpty>No brands found.</CommandEmpty>
                        <CommandGroup>
                          <CommandItem
                            onSelect={() => {
                              setBrandFilter('all')
                              setBrandSearchTerm('')
                              setBrandSearchOpen(false)
                            }}
                          >
                            All Brands
                          </CommandItem>
                          {filteredBrands.map((brand) => (
                            <CommandItem
                              key={brand}
                              onSelect={() => {
                                setBrandFilter(brand)
                                setBrandSearchTerm('')
                                setBrandSearchOpen(false)
                              }}
                            >
                              {brand}
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              )}

              {/* Rating Filter */}
              {showFilters?.rating && (
                <Select value={ratingFilter} onValueChange={setRatingFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Rating" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Ratings</SelectItem>
                    <SelectItem value="high">High (4-5 stars)</SelectItem>
                    <SelectItem value="mid">Medium (3 stars)</SelectItem>
                    <SelectItem value="low">Low (1-2 stars)</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Clear Filters */}
            <div className="mt-3 flex justify-between items-center">
              <Button variant="outline" size="sm" onClick={clearFilters}>
                <Filter className="h-4 w-4 mr-2" />
                Clear Filters
              </Button>
              
              {/* Filter summary */}
              <div className="flex gap-2">
                {sentimentFilter !== 'all' && (
                  <Badge variant="outline" className={getSentimentBadgeColor(sentimentFilter)}>
                    {sentimentFilter}
                  </Badge>
                )}
                {brandFilter !== 'all' && (
                  <Badge variant="outline">{brandFilter}</Badge>
                )}
                {ratingFilter !== 'all' && (
                  <Badge variant="outline">{ratingFilter} rating</Badge>
                )}
              </div>
            </div>
          </div>

          {/* Reviews List */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {currentReviews.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">No reviews found matching your filters.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {currentReviews.map((review, index) => (
                  <Card key={`${review.id}-${index}`} className="border-l-4 border-l-blue-200">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-base font-medium mb-1">
                            Review #{startIndex + index + 1}
                          </CardTitle>
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            {/* Star Rating */}
                            {review.rating && (
                              <div className="flex items-center">
                                {[...Array(5)].map((_, i) => (
                                  <Star
                                    key={i}
                                    className={`h-4 w-4 ${
                                      i < getStarRating(review.rating)
                                        ? 'text-yellow-400 fill-current'
                                        : 'text-gray-300'
                                    }`}
                                  />
                                ))}
                                <span className="ml-1">({review.rating})</span>
                              </div>
                            )}
                            
                            {/* Verified Badge */}
                            {review.verified && (
                              <div className="flex items-center text-green-600">
                                <Shield className="h-4 w-4 mr-1" />
                                <span className="text-xs">Verified</span>
                              </div>
                            )}
                            
                            {/* Sentiment Badge */}
                            <Badge variant="outline" className={getSentimentBadgeColor(review.sentiment)}>
                              {review.sentiment}
                            </Badge>
                            
                            {/* Brand */}
                            {review.brand && (
                              <Badge variant="outline" className="bg-blue-50 text-blue-700">
                                {review.brand}
                              </Badge>
                            )}
                            
                            {/* Category */}
                            {review.category && (
                              <Badge variant="outline" className="bg-purple-50 text-purple-700">
                                {review.category}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <p className="text-gray-700 leading-relaxed">
                        {review.text || 'No content available'}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="border-t bg-gray-50 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </div>
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious 
                        onClick={() => goToPage(currentPage - 1)}
                        className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                      />
                    </PaginationItem>
                    
                    {/* Show page numbers */}
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum = i + 1
                      if (totalPages > 5) {
                        if (currentPage <= 3) {
                          pageNum = i + 1
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i
                        } else {
                          pageNum = currentPage - 2 + i
                        }
                      }
                      
                      return (
                        <PaginationItem key={pageNum}>
                          <PaginationLink
                            onClick={() => goToPage(pageNum)}
                            isActive={pageNum === currentPage}
                            className="cursor-pointer"
                          >
                            {pageNum}
                          </PaginationLink>
                        </PaginationItem>
                      )
                    })}
                    
                    <PaginationItem>
                      <PaginationNext 
                        onClick={() => goToPage(currentPage + 1)}
                        className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 