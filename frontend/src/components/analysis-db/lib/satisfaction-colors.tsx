// Satisfaction Rate Color Scheme Utility
// Provides consistent color gradients and legends across all charts

import React from 'react';

export interface SatisfactionColorScheme {
  color: string;
  label: string;
  range: string;
}

// Get color based on satisfaction rate (0-100%)
export const getSatisfactionColor = (satisfactionRate: number): string => {
  if (satisfactionRate >= 85) return '#059669'; // Dark green - Excellent
  if (satisfactionRate >= 70) return '#10b981'; // Green - Very Good  
  if (satisfactionRate >= 55) return '#34d399'; // Light green - Good
  if (satisfactionRate >= 40) return '#fbbf24'; // Yellow - Average
  if (satisfactionRate >= 25) return '#f97316'; // Orange - Poor
  return '#dc2626'; // Red - Very Poor
};

// Get satisfaction level text
export const getSatisfactionLevel = (satisfactionRate: number): string => {
  if (satisfactionRate >= 85) return 'Excellent';
  if (satisfactionRate >= 70) return 'Very Good';
  if (satisfactionRate >= 55) return 'Good';
  if (satisfactionRate >= 40) return 'Average';
  if (satisfactionRate >= 25) return 'Poor';
  return 'Very Poor';
};

// Color scheme configuration for legends
export const SATISFACTION_COLOR_SCHEME: SatisfactionColorScheme[] = [
  { color: '#059669', label: 'Excellent', range: '85-100%' },
  { color: '#10b981', label: 'Very Good', range: '70-84%' },
  { color: '#34d399', label: 'Good', range: '55-69%' },
  { color: '#fbbf24', label: 'Average', range: '40-54%' },
  { color: '#f97316', label: 'Poor', range: '25-39%' },
  { color: '#dc2626', label: 'Very Poor', range: '0-24%' }
];

// Compact legend component for chart headers
interface SatisfactionLegendProps {
  className?: string;
}

export const SatisfactionLegend: React.FC<SatisfactionLegendProps> = ({ className = "" }) => (
  <div className={`flex items-center gap-2 text-sm ${className}`}>
    {SATISFACTION_COLOR_SCHEME.slice(0, 4).map((scheme, index) => (
      <div key={index} className="flex items-center gap-1">
        <div 
          className="w-3 h-3 rounded" 
          style={{ backgroundColor: scheme.color }}
        ></div>
        <span className="text-xs">{scheme.label}</span>
      </div>
    ))}
  </div>
);

// Full legend with all ranges
interface DetailedSatisfactionLegendProps {
  className?: string;
}

export const DetailedSatisfactionLegend: React.FC<DetailedSatisfactionLegendProps> = ({ className = "" }) => (
  <div className={`grid grid-cols-2 md:grid-cols-3 gap-2 text-sm ${className}`}>
    {SATISFACTION_COLOR_SCHEME.map((scheme, index) => (
      <div key={index} className="flex items-center gap-2">
        <div 
          className="w-4 h-4 rounded" 
          style={{ backgroundColor: scheme.color }}
        ></div>
        <span className="text-xs">
          {scheme.label} ({scheme.range})
        </span>
      </div>
    ))}
  </div>
); 