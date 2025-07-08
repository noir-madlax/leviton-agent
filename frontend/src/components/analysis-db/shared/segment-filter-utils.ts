/**
 * Segment filtering utilities to ensure consistency across analysis components
 */

// Type definitions for different data structures
interface BrandSegmentData {
  revenue: number;
  volume: number;
}

interface PackageSegmentItem {
  packSize: string;
  count: number;
  percentage: number;
  salesVolume: number;
  salesRevenue: number;
}

/**
 * Filter segments for Brand Analysis based on data quality
 * Only keeps segments that have brands with revenue > 0 or volume > 0
 */
export function filterValidBrandSegments(
  segmentNames: string[],
  brandCategoryRevenue: Array<{
    brand: string;
    segments: Record<string, BrandSegmentData>;
  }>,
  metricType: 'revenue' | 'volume'
): string[] {
  return segmentNames.filter(segment => {
    // Check if this segment has any brands with valid data
    const hasValidBrands = brandCategoryRevenue.some(item => {
      const segmentData = item.segments[segment] || { revenue: 0, volume: 0 };
      const value = metricType === "revenue" ? segmentData.revenue : segmentData.volume;
      return value > 0;
    });
    
    return hasValidBrands;
  });
}

/**
 * Filter segments for Package Preference Analysis based on data quality and metric type
 * For revenue mode: only keeps segments with salesRevenue > 0
 * For volume mode: only keeps segments with salesVolume > 0
 */
export function filterValidPackageSegments(
  segmentNames: string[],
  segmentDistributions: Record<string, PackageSegmentItem[]>,
  metricType: 'revenue' | 'volume'
): string[] {
  return segmentNames.filter(segment => {
    const items = segmentDistributions[segment] || [];
    
    // Filter based on the selected metric type
    const hasValidData = items.some(item => {
      if (metricType === 'revenue') {
        return item.salesRevenue > 0;
      } else {
        return item.salesVolume > 0;
      }
    });
    
    return hasValidData;
  });
}

/**
 * Filter segments for Product Analysis based on segment summary data
 * Only keeps segments that have totalRevenue > 0 or totalVolume > 0
 */
export function filterValidProductSegments(
  segmentNames: string[],
  segmentSummary: Record<string, {
    totalRevenue: number;
    totalVolume: number;
    productCount: number;
    avgPrice: number;
    topBrand: string;
  }>
): string[] {
  return segmentNames.filter(segment => {
    const summary = segmentSummary[segment];
    if (!summary) return false;
    
    // Only keep segments with revenue > 0 (consistent with revenue-focused analysis)
    return summary.totalRevenue > 0;
  });
}

/**
 * Generic segment filter that can be extended for other analysis types
 * Filters segments based on whether they have any meaningful data
 */
export function filterSegmentsWithData<T>(
  segmentNames: string[],
  dataCheckFn: (segment: string) => boolean
): string[] {
  return segmentNames.filter(dataCheckFn);
} 