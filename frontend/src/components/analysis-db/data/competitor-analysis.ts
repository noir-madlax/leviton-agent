// Competitor Analysis Data - 6 product competitive pain point analysis (including all products)
// Data source: consolidated_aspect_categorization.json, expanded_review_results.json
// Generated: 2025-06-11 02:05:04
// Products analyzed: Leviton D26HD, D215S, Lutron Caseta Diva, TP Link Switch, Leviton DSL06, Lutron Diva (including all products)

export interface ProductPainPoint {
  product: string;                    // Product name
  category: string;                   // Category name
  categoryType: 'Physical' | 'Performance'; // Category type
  mentions: number;                   // Mention count (for bubble size)
  satisfactionRate: number;           // Satisfaction percentage (for color)
  positiveCount: number;              // Positive review count
  negativeCount: number;              // Negative review count
  totalReviews: number;               // Total review count
}

export interface ProductUseCaseData {
  product: string;
  useCase: string;
  mentions: number;
  satisfactionRate: number;
  positiveCount: number;
  negativeCount: number;
  totalReviews: number;
  gapLevel: number; // From actual analysis data
}

export interface CompetitorAnalysisData {
  summary: {
    totalProducts: number;
    totalDataPoints: number;
    totalMentions: number;
    avgSatisfactionRate: number;
    processingDate: string;
    description: string;
  };
  matrixData: ProductPainPoint[];        // Complete matrix data
  physicalData: ProductPainPoint[];     // Physical characteristics data
  performanceData: ProductPainPoint[];  // Performance characteristics data
  targetProducts: string[];             // Target product list
  productTotalReviews: Record<string, number>; // Actual total review count per product
}

// Target product list (including all 6 products)
export const targetProducts = [
  "Leviton D26HD",
  "Leviton D215S",
  "Lutron Caseta Diva",
  "TP Link Switch",
  "Leviton DSL06",
  "Lutron Diva"
];

// Actual total review count per product
export const productTotalReviews = {
  "Leviton D26HD": 19,
  "Leviton D215S": 38,
  "Lutron Caseta Diva": 50,
  "TP Link Switch": 49,
  "Lutron Diva": 42
};

// Summary statistics
export const competitorSummary = {
  "totalProducts": 6,
  "totalDataPoints": 92,
  "totalMentions": 63,
  "avgSatisfactionRate": 56.1,
  "processingDate": "2025-06-11T02:05:04.657643",
  "description": "6 product competitive pain points analysis including all target products"
};

// Complete pain point matrix data
export const competitorMatrixData: ProductPainPoint[] = [
  {
    "product": "Leviton D26HD",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 3,
    "satisfactionRate": 100.0,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4
  },
  {
    "product": "Leviton D26HD",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1
  },
  {
    "product": "Leviton D26HD",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1
  },
  {
    "product": "Leviton D26HD",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "Leviton D26HD",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3
  },
  {
    "product": "Leviton D215S",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 3,
    "satisfactionRate": 33.3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3
  },
  {
    "product": "Leviton D215S",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 100.0,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2
  },
  {
    "product": "Leviton D215S",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 1,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 3,
    "satisfactionRate": 33.3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 100.0,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4
  },
  {
    "product": "TP Link Switch",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "TP Link Switch",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1
  },
  {
    "product": "TP Link Switch",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "TP Link Switch",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 3,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3
  },
  {
    "product": "Lutron Diva",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 6,
    "satisfactionRate": 50.0,
    "positiveCount": 4,
    "negativeCount": 4,
    "totalReviews": 8
  },
  {
    "product": "Lutron Diva",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 4,
    "satisfactionRate": 100.0,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4
  },
  {
    "product": "Lutron Diva",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "Lutron Diva",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 4,
    "satisfactionRate": 40.0,
    "positiveCount": 2,
    "negativeCount": 3,
    "totalReviews": 5
  },
  {
    "product": "Lutron Diva",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  }
];

// Physical characteristics pain point data
export const physicalPainPoints: ProductPainPoint[] = [
  {
    "product": "Leviton D26HD",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 3,
    "satisfactionRate": 100.0,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4
  },
  {
    "product": "Leviton D26HD",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1
  },
  {
    "product": "Leviton D26HD",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1
  },
  {
    "product": "Leviton D26HD",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "Leviton D26HD",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D26HD",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3
  },
  {
    "product": "Leviton D215S",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 3,
    "satisfactionRate": 33.3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3
  },
  {
    "product": "Leviton D215S",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 100.0,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2
  },
  {
    "product": "Leviton D215S",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton D215S",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 1,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 3,
    "satisfactionRate": 33.3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Caseta Diva",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 100.0,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4
  },
  {
    "product": "TP Link Switch",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "TP Link Switch",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1
  },
  {
    "product": "TP Link Switch",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "TP Link Switch",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "TP Link Switch",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Leviton DSL06",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 3,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3
  },
  {
    "product": "Lutron Diva",
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 6,
    "satisfactionRate": 50.0,
    "positiveCount": 4,
    "negativeCount": 4,
    "totalReviews": 8
  },
  {
    "product": "Lutron Diva",
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 4,
    "satisfactionRate": 100.0,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4
  },
  {
    "product": "Lutron Diva",
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2
  },
  {
    "product": "Lutron Diva",
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  },
  {
    "product": "Lutron Diva",
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 4,
    "satisfactionRate": 40.0,
    "positiveCount": 2,
    "negativeCount": 3,
    "totalReviews": 5
  },
  {
    "product": "Lutron Diva",
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0
  }
];

// Performance characteristics pain point data
export const performancePainPoints: ProductPainPoint[] = [];

// Use case matrix data
export const useCaseMatrixData: ProductUseCaseData[] = [
  {
    "product": "Leviton D26HD",
    "useCase": "Scheduling and Automation",
    "mentions": 2,
    "satisfactionRate": 100.0,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "gapLevel": 0.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "Smart Home Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "Smart Home Automation",
    "mentions": 3,
    "satisfactionRate": 100.0,
    "positiveCount": 6,
    "negativeCount": 0,
    "totalReviews": 6,
    "gapLevel": 0.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "Outdoor and Security Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "Remote and Mobile Control",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "gapLevel": 0.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "Kitchen Applications",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "gapLevel": 0.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "Complex Wiring Configurations",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "Recessed and Can Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "LED Lighting Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D26HD",
    "useCase": "Outdoor Lighting Control",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "gapLevel": 0.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Scheduling and Automation",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 9,
    "negativeCount": 0,
    "totalReviews": 9,
    "gapLevel": 0.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Smart Home Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Smart Home Automation",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Outdoor and Security Lighting",
    "mentions": 2,
    "satisfactionRate": 100.0,
    "positiveCount": 3,
    "negativeCount": 0,
    "totalReviews": 3,
    "gapLevel": 0.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Remote and Mobile Control",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 5,
    "negativeCount": 0,
    "totalReviews": 5,
    "gapLevel": 0.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Kitchen Applications",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Complex Wiring Configurations",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Recessed and Can Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "LED Lighting Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton D215S",
    "useCase": "Outdoor Lighting Control",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Scheduling and Automation",
    "mentions": 1,
    "satisfactionRate": 66.7,
    "positiveCount": 2,
    "negativeCount": 1,
    "totalReviews": 3,
    "gapLevel": 33.3
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Smart Home Integration",
    "mentions": 1,
    "satisfactionRate": 83.3,
    "positiveCount": 5,
    "negativeCount": 1,
    "totalReviews": 6,
    "gapLevel": 16.7
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Smart Home Automation",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 3,
    "negativeCount": 0,
    "totalReviews": 3,
    "gapLevel": 0.0
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Outdoor and Security Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Remote and Mobile Control",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Kitchen Applications",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "gapLevel": 0.0
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Complex Wiring Configurations",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "gapLevel": 0.0
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Recessed and Can Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "LED Lighting Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Caseta Diva",
    "useCase": "Outdoor Lighting Control",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "Scheduling and Automation",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 3,
    "negativeCount": 0,
    "totalReviews": 3,
    "gapLevel": 0.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "Smart Home Integration",
    "mentions": 2,
    "satisfactionRate": 85.7,
    "positiveCount": 12,
    "negativeCount": 2,
    "totalReviews": 14,
    "gapLevel": 14.3
  },
  {
    "product": "TP Link Switch",
    "useCase": "Smart Home Automation",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "Outdoor and Security Lighting",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 3,
    "negativeCount": 0,
    "totalReviews": 3,
    "gapLevel": 0.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "Remote and Mobile Control",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 3,
    "negativeCount": 0,
    "totalReviews": 3,
    "gapLevel": 0.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "Kitchen Applications",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "Complex Wiring Configurations",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "Recessed and Can Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "LED Lighting Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "TP Link Switch",
    "useCase": "Outdoor Lighting Control",
    "mentions": 1,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "gapLevel": 50.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Scheduling and Automation",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Smart Home Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Smart Home Automation",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Outdoor and Security Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Remote and Mobile Control",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Kitchen Applications",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Complex Wiring Configurations",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Recessed and Can Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "LED Lighting Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Leviton DSL06",
    "useCase": "Outdoor Lighting Control",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Scheduling and Automation",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Smart Home Integration",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Smart Home Automation",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Outdoor and Security Lighting",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Remote and Mobile Control",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Kitchen Applications",
    "mentions": 1,
    "satisfactionRate": 100.0,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "gapLevel": 0.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Complex Wiring Configurations",
    "mentions": 1,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "gapLevel": 50.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Recessed and Can Lighting",
    "mentions": 2,
    "satisfactionRate": 100.0,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "gapLevel": 0.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "LED Lighting Integration",
    "mentions": 2,
    "satisfactionRate": 50.0,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "gapLevel": 50.0
  },
  {
    "product": "Lutron Diva",
    "useCase": "Outdoor Lighting Control",
    "mentions": 0,
    "satisfactionRate": 0.0,
    "positiveCount": 0,
    "negativeCount": 0,
    "totalReviews": 0,
    "gapLevel": 100.0
  }
];

// Get competitor analysis data
export function getCompetitorAnalysisData(): CompetitorAnalysisData {
  return {
    summary: competitorSummary,
    matrixData: competitorMatrixData,
    physicalData: physicalPainPoints,
    performanceData: performancePainPoints,
    targetProducts: targetProducts,
    productTotalReviews: productTotalReviews
  };
}

// Get use case analysis data
export function getUseCaseAnalysisData(): {
  matrixData: ProductUseCaseData[];
  targetProducts: string[];
  productTotalReviews: Record<string, number>;
} {
  return {
    matrixData: useCaseMatrixData,
    targetProducts: targetProducts,
    productTotalReviews: productTotalReviews
  };
}

// Get pain point data for specified product
export function getProductPainPoints(productName: string): ProductPainPoint[] {
  return competitorMatrixData.filter(item => item.product === productName);
}

// Get all product data for specified category
export function getCategoryComparisonData(categoryName: string): ProductPainPoint[] {
  return competitorMatrixData.filter(item => item.category === categoryName);
}

// Get all category list
export function getAllCategories(): string[] {
  const categories = new Set(competitorMatrixData.map(item => item.category));
  return Array.from(categories).sort();
}

// Get data filtered by category type
export function getDataByType(categoryType: 'Physical' | 'Performance'): ProductPainPoint[] {
  return competitorMatrixData.filter(item => item.categoryType === categoryType);
}

// Calculate satisfaction color mapping (for matrix display)
export function getSatisfactionColor(satisfactionRate: number): string {
  if (satisfactionRate >= 85) return '#22c55e';      // Green - high satisfaction
  else if (satisfactionRate >= 70) return '#eab308'; // Yellow - medium satisfaction
  else if (satisfactionRate >= 60) return '#f97316'; // Orange - lower satisfaction
  else return '#ef4444';                              // Red - low satisfaction
}

// Calculate bubble size mapping
export function getBubbleSize(mentions: number, maxMentions: number): number {
  const minSize = 10;
  const maxSize = 50;
  const normalizedSize = (mentions / maxMentions) * (maxSize - minSize) + minSize;
  return Math.max(minSize, Math.min(maxSize, normalizedSize));
}
