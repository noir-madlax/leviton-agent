'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Filter, RotateCcw, X } from 'lucide-react';
import { databaseService } from '@/components/analysis-db/data/database-service';

interface ProjectFiltersProps {
  projectId: string | null;
  onFiltersChange?: (filters: ProjectFilters) => void;
}

interface ProjectFilters {
  categories: string[];
  asins: string[];
}

export function ProjectFilters({ projectId, onFiltersChange }: ProjectFiltersProps) {
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) {
      setAvailableCategories([]);
      setSelectedCategories([]);
      return;
    }

    const loadFilterOptions = async () => {
      setLoading(true);
      try {
        const overview = await databaseService.getProjectOverview(projectId);
        setAvailableCategories(overview.available_categories);
      } catch (error) {
        console.error('Failed to load filter options:', error);
        setAvailableCategories([]);
      } finally {
        setLoading(false);
      }
    };

    loadFilterOptions();
  }, [projectId]);

  const handleCategorySelect = (category: string) => {
    if (!selectedCategories.includes(category)) {
      const newCategories = [...selectedCategories, category];
      setSelectedCategories(newCategories);
      
      // Call onFiltersChange if provided (for future implementation)
      if (onFiltersChange) {
        onFiltersChange({
          categories: newCategories,
          asins: [] // ASIN filtering to be implemented later
        });
      }
    }
  };

  const handleCategoryRemove = (category: string) => {
    const newCategories = selectedCategories.filter(c => c !== category);
    setSelectedCategories(newCategories);
    
    if (onFiltersChange) {
      onFiltersChange({
        categories: newCategories,
        asins: []
      });
    }
  };

  const handleReset = () => {
    setSelectedCategories([]);
    
    if (onFiltersChange) {
      onFiltersChange({
        categories: [],
        asins: []
      });
    }
  };

  const hasActiveFilters = selectedCategories.length > 0;

  if (!projectId) {
    return null;
  }

  return (
    <div className="mb-6">
      <Card className="border-gray-200">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            {/* Filter icon and title */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Quick Filters:</span>
            </div>

            {/* Category selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Category:</span>
              <Select onValueChange={handleCategorySelect} disabled={loading}>
                <SelectTrigger className="w-48 h-8">
                  <SelectValue placeholder="Select category..." />
                </SelectTrigger>
                <SelectContent>
                  {availableCategories
                    .filter(category => !selectedCategories.includes(category))
                    .map((category) => (
                      <SelectItem key={category} value={category}>
                        {category}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            {/* Reset button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={!hasActiveFilters}
              className="h-8"
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              Reset
            </Button>

            {/* Active filters count */}
            {hasActiveFilters && (
              <div className="text-xs text-gray-500">
                {selectedCategories.length} filter{selectedCategories.length > 1 ? 's' : ''} active
              </div>
            )}
          </div>

          {/* Selected filters display */}
          {selectedCategories.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-gray-600">Active filters:</span>
                {selectedCategories.map((category) => (
                  <Badge
                    key={category}
                    variant="secondary"
                    className="text-xs flex items-center gap-1"
                  >
                    {category}
                    <X
                      className="w-3 h-3 cursor-pointer hover:text-red-500"
                      onClick={() => handleCategoryRemove(category)}
                    />
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Note about filter application */}
          {hasActiveFilters && (
            <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
              <strong>Note:</strong> Filter application to analysis charts will be implemented in the next phase.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 