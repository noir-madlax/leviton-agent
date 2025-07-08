'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Search, Filter, RotateCcw } from 'lucide-react';
import { databaseService } from '@/components/analysis-db/data/database-service';

interface ProductInfo {
  platform_id: string;
  title: string;
  brand: string;
  price_usd: number;
  reviews_count: number;
  category: string;
}

interface CompetitorAsinSelectorProps {
  projectId: string | null;
  onSelectionChange: (selectedAsins: string[]) => void;
  defaultSelection?: string[];
}

export function CompetitorAsinSelector({ 
  projectId, 
  onSelectionChange, 
  defaultSelection = [] 
}: CompetitorAsinSelectorProps) {
  const [availableProducts, setAvailableProducts] = useState<ProductInfo[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<ProductInfo[]>([]);
  const [selectedAsins, setSelectedAsins] = useState<string[]>(defaultSelection);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  // Load available products
  useEffect(() => {
    if (!projectId) return;
    
    const loadProducts = async () => {
      try {
        setLoading(true);
        const products = await databaseService.getAvailableAsins();
        setAvailableProducts(products);
        setFilteredProducts(products);
      } catch (error) {
        console.error('Error loading available products:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadProducts();
  }, [projectId]);

  // Filter products based on search and filters
  useEffect(() => {
    let filtered = availableProducts;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(product => 
        product.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.brand.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.platform_id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Brand filter
    if (selectedBrand) {
      filtered = filtered.filter(product => product.brand === selectedBrand);
    }

    // Category filter
    if (selectedCategory) {
      filtered = filtered.filter(product => product.category === selectedCategory);
    }

    // Sort by reviews count (descending)
    filtered.sort((a, b) => b.reviews_count - a.reviews_count);

    setFilteredProducts(filtered);
  }, [availableProducts, searchTerm, selectedBrand, selectedCategory]);

  // Handle ASIN selection
  const handleAsinToggle = (asin: string) => {
    const newSelection = selectedAsins.includes(asin)
      ? selectedAsins.filter(id => id !== asin)
      : [...selectedAsins, asin];
    
    setSelectedAsins(newSelection);
    onSelectionChange(newSelection);
  };

  // Reset filters
  const resetFilters = () => {
    setSearchTerm('');
    setSelectedBrand('');
    setSelectedCategory('');
  };

  // Get unique brands and categories
  const uniqueBrands = [...new Set(availableProducts.map(p => p.brand))].sort();
  const uniqueCategories = [...new Set(availableProducts.map(p => p.category))].sort();

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>🔍 Select Products to Compare</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Filter className="w-5 h-5" />
          🔍 Select Products to Compare ({selectedAsins.length} selected)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Search and Filter Controls */}
        <div className="space-y-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Type ASIN or product name"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              className="px-3 py-2 border rounded-md"
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
            >
              <option value="">All Brands</option>
              {uniqueBrands.map(brand => (
                <option key={brand} value={brand}>{brand}</option>
              ))}
            </select>
            <select
              className="px-3 py-2 border rounded-md"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="">All Categories</option>
              {uniqueCategories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
            <Button
              variant="outline"
              onClick={resetFilters}
              className="flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </Button>
          </div>
        </div>

        {/* Selected Products Summary */}
        {selectedAsins.length > 0 && (
          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Selected Products:</h4>
            <div className="flex flex-wrap gap-2">
              {selectedAsins.map(asin => {
                const product = availableProducts.find(p => p.platform_id === asin);
                return (
                  <Badge key={asin} variant="secondary" className="text-xs">
                    {product?.brand || 'Unknown'} - {asin}
                  </Badge>
                );
              })}
            </div>
          </div>
        )}

        {/* Product List */}
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {filteredProducts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No products found matching your criteria
            </div>
          ) : (
            filteredProducts.slice(0, 50).map((product) => (
              <div
                key={product.platform_id}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  selectedAsins.includes(product.platform_id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleAsinToggle(product.platform_id)}
              >
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={selectedAsins.includes(product.platform_id)}
                    onChange={() => handleAsinToggle(product.platform_id)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start gap-2">
                      <h4 className="font-medium text-gray-900 text-sm leading-tight">
                        {product.title}
                      </h4>
                      <div className="flex flex-col items-end text-xs text-gray-500">
                        <span>${product.price_usd}</span>
                        <span>{product.reviews_count} reviews</span>
                      </div>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                      <Badge variant="outline" className="text-xs">
                        {product.brand}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {product.category}
                      </Badge>
                      <span className="text-gray-400">ASIN: {product.platform_id}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {filteredProducts.length > 50 && (
          <div className="text-center mt-4 text-sm text-gray-500">
            Showing top 50 products. Use filters to narrow down results.
          </div>
        )}
      </CardContent>
    </Card>
  );
} 