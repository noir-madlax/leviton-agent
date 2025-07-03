'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Database, Users, MessageSquare, BarChart3, Loader2 } from 'lucide-react';
import { databaseService } from '@/components/analysis-db/data/database-service';

interface ProjectDataOverviewProps {
  projectId: string | null;
}

interface ProjectOverviewData {
  project_name: string;
  created_at: string;
  stats: {
    total_products: number;
    total_brands: number;
    total_reviews: number;
    segment_count: number;
  };
  distributions: {
    sources: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
    categories: Array<{
      name: string;
      count: number;
      percentage: number;
    }>;
  };
  available_categories: string[];
}

export function ProjectDataOverview({ projectId }: ProjectDataOverviewProps) {
  const [data, setData] = useState<ProjectOverviewData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) {
      setData(null);
      return;
    }

    const loadProjectOverview = async () => {
      setLoading(true);
      try {
        const overview = await databaseService.getProjectOverview(projectId);
        setData(overview);
      } catch (error) {
        console.error('Failed to load project overview:', error);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    loadProjectOverview();
  }, [projectId]);

  if (!projectId) {
    return (
      <div className="mb-6">
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
          <p className="text-sm text-gray-500">
            Please select a project to view data overview
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500 mr-2" />
              <span className="text-sm text-gray-600">Loading project overview...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="mb-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-center">
          <p className="text-sm text-red-600">
            Failed to load project overview. Please try again.
          </p>
        </div>
      </div>
    );
  }

  // Format sources distribution text
  const sourcesText = data.distributions.sources
    .map(source => `${source.name} (${source.percentage}%)`)
    .join(' • ');

  // Format categories distribution text (show top 3)
  const categoriesText = data.distributions.categories
    .slice(0, 3)
    .map(category => `${category.name} (${category.percentage}%)`)
    .join(', ');

  const moreCategoriesCount = data.distributions.categories.length - 3;

  return (
    <div className="mb-6">
      <Card className="border-blue-200">
        <CardContent className="p-4">
          {/* Main statistics cards */}
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
              <Database className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-xl font-bold text-blue-900">{data.stats.total_products.toLocaleString()}</p>
                <p className="text-xs text-blue-600">Products</p>
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
              <Users className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-xl font-bold text-green-900">{data.stats.total_brands}</p>
                <p className="text-xs text-green-600">Brands</p>
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 bg-purple-50 rounded-lg">
              <MessageSquare className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-xl font-bold text-purple-900">{data.stats.total_reviews.toLocaleString()}</p>
                <p className="text-xs text-purple-600">Reviews</p>
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 bg-orange-50 rounded-lg">
              <BarChart3 className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-xl font-bold text-orange-900">{data.stats.segment_count}</p>
                <p className="text-xs text-orange-600">Segments</p>
              </div>
            </div>
          </div>

          {/* Distribution information */}
          <div className="space-y-2 text-sm">
            {data.distributions.sources.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-700">Data Sources:</span>
                <span className="text-gray-600">{sourcesText}</span>
              </div>
            )}

            {data.distributions.categories.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-700">Categories:</span>
                <span className="text-gray-600">
                  {categoriesText}
                  {moreCategoriesCount > 0 && (
                    <Badge variant="secondary" className="ml-2 text-xs">
                      +{moreCategoriesCount} more
                    </Badge>
                  )}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 