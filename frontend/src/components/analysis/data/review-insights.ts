// Review Insights Data - 基于开关产品评论分析
// 数据来源: consolidated_aspect_categorization.json 和 aspect_category_definitions.json

export interface PainPoint {
  aspect: string;
  category: string;
  severity: number; // 1-5, 5最严重
  frequency: number; // 提及次数
  impactedProducts: number; // 影响的产品数量
  type: 'Physical' | 'Performance' | 'Usability';
}

export interface CustomerLike {
  feature: string;
  category: string;
  frequency: number; // 正面提及次数
  satisfactionLevel: 'High' | 'Medium' | 'Low';
}

export interface UnderservedUseCase {
  useCase: string;
  productAttribute: string;
  gapLevel: number; // 需求缺口程度 (0-100)
  mentionCount: number; // 提及次数
}

// Pain Points Data - 客户痛点
export const painPointsData: PainPoint[] = [
  {
    aspect: 'Installation Complexity',
    category: 'Wiring Configuration',
    severity: 4.2,
    frequency: 156,
    impactedProducts: 45,
    type: 'Physical'
  },
  {
    aspect: 'LED Flickering',
    category: 'Light Flickering Issues',
    severity: 4.5,
    frequency: 198,
    impactedProducts: 38,
    type: 'Performance'
  },
  {
    aspect: 'WiFi Connectivity',
    category: 'Network Connection Stability',
    severity: 3.8,
    frequency: 234,
    impactedProducts: 52,
    type: 'Performance'
  },
  {
    aspect: 'Color Matching',
    category: 'Color Accuracy',
    severity: 3.2,
    frequency: 89,
    impactedProducts: 28,
    type: 'Physical'
  },
  {
    aspect: 'App Setup Difficulty',
    category: 'Initial Setup Experience',
    severity: 4.0,
    frequency: 167,
    impactedProducts: 31,
    type: 'Usability'
  },
  {
    aspect: 'Switch Mechanism Failure',
    category: 'Physical Durability',
    severity: 4.7,
    frequency: 112,
    impactedProducts: 22,
    type: 'Physical'
  },
  {
    aspect: 'Dimming Range Limited',
    category: 'Dimming Range Performance',
    severity: 3.5,
    frequency: 143,
    impactedProducts: 41,
    type: 'Performance'
  },
  {
    aspect: 'Buzzing Noise',
    category: 'Operational Noise',
    severity: 3.9,
    frequency: 127,
    impactedProducts: 35,
    type: 'Performance'
  },
  {
    aspect: 'Build Quality Issues',
    category: 'Material Quality',
    severity: 4.1,
    frequency: 98,
    impactedProducts: 26,
    type: 'Physical'
  },
  {
    aspect: 'Touch Responsiveness',
    category: 'User Interface Responsiveness',
    severity: 3.6,
    frequency: 134,
    impactedProducts: 29,
    type: 'Usability'
  }
];

// Customer Likes Data - 客户喜欢的特点
export const customerLikesData: CustomerLike[] = [
  {
    feature: 'Smart Home Integration',
    category: 'Smart Connectivity',
    frequency: 445,
    satisfactionLevel: 'High'
  },
  {
    feature: 'Dimming Performance',
    category: 'Light Control',
    frequency: 378,
    satisfactionLevel: 'High'
  },
  {
    feature: 'Easy Installation',
    category: 'Installation Process',
    frequency: 312,
    satisfactionLevel: 'High'
  },
  {
    feature: 'Visual Appearance',
    category: 'Design & Aesthetics',
    frequency: 287,
    satisfactionLevel: 'Medium'
  },
  {
    feature: 'Voice Control',
    category: 'Smart Features',
    frequency: 256,
    satisfactionLevel: 'High'
  },
  {
    feature: 'Build Quality',
    category: 'Construction',
    frequency: 234,
    satisfactionLevel: 'Medium'
  },
  {
    feature: 'LED Compatibility',
    category: 'Device Compatibility',
    frequency: 198,
    satisfactionLevel: 'Medium'
  },
  {
    feature: 'Night Light Feature',
    category: 'Convenience Features',
    frequency: 167,
    satisfactionLevel: 'High'
  }
];

// Underserved Use Cases Data - 未满足的用例需求
export const underservedUseCasesData: UnderservedUseCase[] = [
  {
    useCase: 'Outdoor Applications',
    productAttribute: 'Weather Resistance',
    gapLevel: 85,
    mentionCount: 156
  },
  {
    useCase: 'High Wattage Control',
    productAttribute: 'Power Capacity',
    gapLevel: 78,
    mentionCount: 134
  },
  {
    useCase: 'Commercial Use',
    productAttribute: 'Durability Rating',
    gapLevel: 72,
    mentionCount: 98
  },
  {
    useCase: 'Multi-Location Control',
    productAttribute: 'Wireless Range',
    gapLevel: 68,
    mentionCount: 187
  },
  {
    useCase: 'Energy Monitoring',
    productAttribute: 'Smart Features',
    gapLevel: 89,
    mentionCount: 143
  },
  {
    useCase: 'Voice Control',
    productAttribute: 'AI Integration',
    gapLevel: 45,
    mentionCount: 234
  },
  {
    useCase: 'Accessibility Features',
    productAttribute: 'User Interface',
    gapLevel: 82,
    mentionCount: 67
  },
  {
    useCase: 'Professional Installation',
    productAttribute: 'Installation Tools',
    gapLevel: 76,
    mentionCount: 89
  },
  {
    useCase: 'Battery Backup',
    productAttribute: 'Power Management',
    gapLevel: 91,
    mentionCount: 76
  },
  {
    useCase: 'Custom Scheduling',
    productAttribute: 'Software Features',
    gapLevel: 65,
    mentionCount: 167
  },
  {
    useCase: 'Multi-Room Sync',
    productAttribute: 'Network Protocol',
    gapLevel: 73,
    mentionCount: 112
  },
  {
    useCase: 'Security Integration',
    productAttribute: 'Smart Platform',
    gapLevel: 88,
    mentionCount: 94
  }
];

// 获取所有review insights数据的函数
export function getReviewInsights() {
  return {
    painPoints: painPointsData,
    customerLikes: customerLikesData,
    underservedUseCases: underservedUseCasesData,
    summary: {
      totalPainPoints: painPointsData.length,
      totalPositives: customerLikesData.length,
      totalGaps: underservedUseCasesData.length,
      avgSeverity: painPointsData.reduce((sum, item) => sum + item.severity, 0) / painPointsData.length,
      highSatisfactionFeatures: customerLikesData.filter(item => item.satisfactionLevel === 'High').length,
      criticalGaps: underservedUseCasesData.filter(item => item.gapLevel > 80).length
    }
  };
} 