// Category Feedback Analysis Data - Generated from actual review analysis
// Data source: /Users/maoc/MIT Dropbox/Chengfeng Mao/JMP/leviton-switch/backend/data/result/process_review/20250609_05
// Generated: 2025-06-10 17:44:03
// Products analyzed: Dimmer=244, Light=268

export interface CategoryFeedback {
  category: string;
  categoryType: 'Physical' | 'Performance';
  mentions: number;
  satisfactionRate: number;
  negativeRate: number;
  positiveCount: number;
  negativeCount: number;
  totalReviews: number;
  averageRating: number;
  topNegativeAspects: string[];
  topPositiveAspects: string[];
  topNegativeReasons: string[];
  topPositiveReasons: string[];
}

export interface UseCaseFeedback {
  useCase: string;
  totalMentions: number;
  positiveCount: number;
  negativeCount: number;
  satisfactionRate: number;
  categoryType: 'Physical' | 'Performance';
  topSatisfactionReasons: string[];
  topGapReasons: string[];
  relatedCategories: string[];
}

export interface CategoryFeedbackData {
  summary: {
    totalCategories: number;
    physicalCategories: number;
    performanceCategories: number;
    avgSatisfactionRate: number;
    processingDate: string;
    productType: string;
  };
  topNegativeCategories: CategoryFeedback[];
  topPositiveCategories: CategoryFeedback[];
  topUseCases: UseCaseFeedback[];
  allCategories: CategoryFeedback[];
}

export type ProductType = 'dimmer' | 'light';

// Dimmer Switches Data
export const dimmerSwitchesSummary = {
  "totalCategories": 231,
  "physicalCategories": 82,
  "performanceCategories": 149,
  "avgSatisfactionRate": 58.6,
  "processingDate": "2025-06-10 17:44:03",
  "productType": "Dimmer Switches"
};
export const topNegativeDimmerCategories: CategoryFeedback[] = [
  {
    "category": "Product Lifespan",
    "categoryType": "Performance",
    "mentions": 167,
    "positiveCount": 29,
    "negativeCount": 138,
    "totalReviews": 167,
    "satisfactionRate": 17.4,
    "negativeRate": 82.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "lasted less than a year (2x)",
      "didn't last 3 months (2x)",
      "lasted all of 2 months",
      "switch lasted 3 days until completely stopped working",
      "had two fail in two years"
    ],
    "topPositiveAspects": [
      "Old push click lasted 32 years",
      "First one lasted 6 years",
      "First one lasted 5 years",
      "Old switch lasted 40+ years",
      "works after 28 years of previous dimmer use"
    ],
    "topNegativeReasons": [
      "feel cheap (2x)",
      "delay when turning on far too long (2x)",
      "very poor quality",
      "barley dims the light",
      "Air gap plug under paddle that spontaneously pops out and cannot be reinserted"
    ],
    "topPositiveReasons": [
      "IP44 weather resistance rating"
    ]
  },
  {
    "category": "Network Connection Stability",
    "categoryType": "Performance",
    "mentions": 119,
    "positiveCount": 21,
    "negativeCount": 98,
    "totalReviews": 119,
    "satisfactionRate": 17.6,
    "negativeRate": 82.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "disconnect from network frequently",
      "WiFi feature stops working after couple months",
      "difficult to connect to app",
      "Frequent WiFi disconnections",
      "Complete connectivity failure"
    ],
    "topPositiveAspects": [
      "no issues with connectivity (2x)",
      "connects to WiFi effectively",
      "connects to Tapo app successfully",
      "no connection issues experienced",
      "Easy WiFi connection setup"
    ],
    "topNegativeReasons": [
      "Red blinking LED status (2x)",
      "Settings change back to full brightness automatically (2x)",
      "ESP8266 boards",
      "relay failed after about 2 years",
      "screen becomes blank and unresponsive"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Product Reliability",
    "categoryType": "Performance",
    "mentions": 122,
    "positiveCount": 32,
    "negativeCount": 90,
    "totalReviews": 122,
    "satisfactionRate": 26.2,
    "negativeRate": 73.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Switch stays on full and will not dim or shut off after 2 years",
      "Malfunctions after a while",
      "One stopped working and cannot be configured or connect to wifi",
      "Randomly blinks green and turns lights on at full at night",
      "Switch does not work when clicked and clicks off/on by itself after 3 years"
    ],
    "topPositiveAspects": [
      "Consistently reliable",
      "Flawless performance for years",
      "Never had an issue",
      "Most stable automation products",
      "Incredibly reliable with 60+ devices"
    ],
    "topNegativeReasons": [
      "Falls apart after installation (3x)",
      "Sensitivity is not fully linear nor particularly good (3x)",
      "very thin cables (2x)",
      "poor_overall_quality (2x)",
      "switches_fail_within_short_time (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Control Performance",
    "categoryType": "Performance",
    "mentions": 176,
    "positiveCount": 92,
    "negativeCount": 84,
    "totalReviews": 176,
    "satisfactionRate": 52.3,
    "negativeRate": 47.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "poor at lower levels of light and never takes intensity to zero",
      "flickers when turned up until partially turned up",
      "doesn't dim over full range, stops when lights still bright",
      "hums when dimmed to 50% or less",
      "Dimming failure"
    ],
    "topPositiveAspects": [
      "provides smooth dimming action",
      "provides fine dimming control",
      "takes lights down to lowest possible bit of light",
      "Proper dimming functionality",
      "Smooth fade effect"
    ],
    "topNegativeReasons": [
      "Dimmer slide moves too easily without resistance",
      "Broke after little over 1 year",
      "cheap_internal_parts",
      "all_fail_in_less_than_a_year_some_in_two_weeks",
      "Physical +/- buttons for dimming"
    ],
    "topPositiveReasons": [
      "Slider for dimming control (2x)",
      "Quick installation process (2x)",
      "acts as both switch and dimmer",
      "main unit and satellite unit configuration",
      "easy to integrate with Kasa app"
    ]
  },
  {
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 123,
    "positiveCount": 55,
    "negativeCount": 68,
    "totalReviews": 123,
    "satisfactionRate": 44.7,
    "negativeRate": 55.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Either I have a smaller-than-standard electrical box, or this thing is too big",
      "Large size leaves no room for wire connections",
      "deeper than regular switches",
      "housing too large to fit two in one box",
      "tiny remote size"
    ],
    "topPositiveAspects": [
      "Perfect fit with standard boxes and gang plates",
      "smallest form factor",
      "Compact size for installation",
      "standard size",
      "small enough to fit into standard single-gang box"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Longevity",
    "categoryType": "Performance",
    "mentions": 66,
    "positiveCount": 2,
    "negativeCount": 64,
    "totalReviews": 66,
    "satisfactionRate": 3.0,
    "negativeRate": 97.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Failed after two years (2x)",
      "Stopped functioning after 1 month",
      "3 out of 4 will not re-pair in less than a year",
      "One switch stops working after couple of days",
      "Dies within months - had 3 die in a year"
    ],
    "topPositiveAspects": [
      "long-term durability",
      "Lasted 9 years before going out"
    ],
    "topNegativeReasons": [
      "internal switch mechanism (2x)",
      "prone to polarity reversal causing failure",
      "failed after few months",
      "All plastic plate that attaches to the box",
      "plastic flip switch falls out"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 165,
    "positiveCount": 106,
    "negativeCount": 59,
    "totalReviews": 165,
    "satisfactionRate": 64.2,
    "negativeRate": 35.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Has wire connections instead of preferred screw clamp terminals",
      "Wire labeling and connection points",
      "pigtails that take up a lot of room",
      "permanently installed lead wires, not lugs",
      "wires substantially thinner than 14AWG Romex"
    ],
    "topPositiveAspects": [
      "requires neutral wire (5x)",
      "does not require neutral wire (2x)",
      "Requires neutral wire (2x)",
      "no neutral wire required (2x)",
      "back-connect screw-type connections"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "LED Flickering Issues",
    "categoryType": "Performance",
    "mentions": 99,
    "positiveCount": 42,
    "negativeCount": 57,
    "totalReviews": 99,
    "satisfactionRate": 42.4,
    "negativeRate": 57.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "bulbs flash 5 times at full brightness when dimmed",
      "lights flicker when dimming",
      "Light flickering issues",
      "flickering at intermediate intensity",
      "blinks light when turned down"
    ],
    "topPositiveAspects": [
      "no flickering with LED lights (2x)",
      "flicker free LED dimming",
      "Light flickering issues",
      "works great with LED lights without flickering",
      "solves LED light flickering issue"
    ],
    "topNegativeReasons": [
      "Dimmer slider with adjustable positions",
      "Slider with halfway position",
      "Dims only about 30% of light output"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Reliability",
    "categoryType": "Performance",
    "mentions": 99,
    "positiveCount": 46,
    "negativeCount": 53,
    "totalReviews": 99,
    "satisfactionRate": 46.5,
    "negativeRate": 53.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "switches have been dying (2x)",
      "have to hit buttons a few times before they work when first entering room",
      "doesn't work on outlet",
      "Works well initially then fails",
      "turn on randomly at full or partial brightness"
    ],
    "topPositiveAspects": [
      "works perfectly (3x)",
      "works every time (2x)",
      "always works",
      "never have operational problems",
      "consistent performance"
    ],
    "topNegativeReasons": [
      "seem cheaply made",
      "doesn't dim far enough"
    ],
    "topPositiveReasons": [
      "slim profile",
      "always works"
    ]
  },
  {
    "category": "Dimming Performance",
    "categoryType": "Performance",
    "mentions": 122,
    "positiveCount": 75,
    "negativeCount": 47,
    "totalReviews": 122,
    "satisfactionRate": 61.5,
    "negativeRate": 38.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "limited dimming range",
      "no dimming functionality",
      "dimmer function does not work while light works",
      "Barely dimmed with flickering on low",
      "Does not dim at all"
    ],
    "topPositiveAspects": [
      "works great as dimmer (2x)",
      "Smooth dimming operation (2x)",
      "dims perfectly",
      "dims nicely",
      "being able to easily dim lights is massive plus"
    ],
    "topNegativeReasons": [
      "has turning knob with zero resistance (2x)",
      "doesn't dim at all, just turns on (2x)",
      "Light flickers when set to dim"
    ],
    "topPositiveReasons": [
      "smooth and responsive slider (14x)",
      "supports multiple bulb types (14x)",
      "touch-activated button interface",
      "requires training and time to get used to sensitivity",
      "Has thumbwheel dial under cover for adjustment"
    ]
  }
];
export const topPositiveDimmerCategories: CategoryFeedback[] = [
  {
    "category": "Installation Process",
    "categoryType": "Performance",
    "mentions": 456,
    "positiveCount": 440,
    "negativeCount": 16,
    "totalReviews": 456,
    "satisfactionRate": 96.5,
    "negativeRate": 3.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "confusing wiring diagram",
      "Installation can be tough",
      "Unable to pull some switches out of housing",
      "challenging to fit 2 units in double gang box",
      "hard to fit in junction box due to size"
    ],
    "topPositiveAspects": [
      "easy to install (49x)",
      "Easy to install (15x)",
      "easy installation (6x)",
      "installation was straightforward (3x)",
      "easy_to_install (3x)"
    ],
    "topNegativeReasons": [
      "only one traveler wire terminal instead of standard two (3x)",
      "stops responding to Alexa for days every few weeks (3x)",
      "takes up lot of space in junction box (2x)",
      "only dims about 50% of light output (2x)",
      "quite large and challenging to fit in tight wall boxes (2x)"
    ],
    "topPositiveReasons": [
      "Easy to install (16x)",
      "requires neutral wire (7x)",
      "back-connect screw-type connections (5x)",
      "rear-screw ground (5x)",
      "neutral pigtail included (5x)"
    ]
  },
  {
    "category": "Overall Reliability",
    "categoryType": "Performance",
    "mentions": 184,
    "positiveCount": 146,
    "negativeCount": 38,
    "totalReviews": 184,
    "satisfactionRate": 79.3,
    "negativeRate": 20.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "unreliable (2x)",
      "quality has gone down",
      "Failed to work completely",
      "Inconsistent light control",
      "Killed LED bulbs"
    ],
    "topPositiveAspects": [
      "works as advertised (11x)",
      "works great (5x)",
      "works flawlessly (3x)",
      "works reliably (2x)",
      "accurate"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "mounting and finishing screws are high-quality",
      "switch feels sturdy and well-made",
      "Metal plate instead of plastic for mounting",
      "Multiple dimming levels available",
      "Screw terminals instead of wire leads"
    ]
  },
  {
    "category": "Installation Ease",
    "categoryType": "Performance",
    "mentions": 164,
    "positiveCount": 144,
    "negativeCount": 20,
    "totalReviews": 164,
    "satisfactionRate": 87.8,
    "negativeRate": 12.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "installation complicated",
      "not easy to install",
      "Ease of installation process",
      "Cannot install due to screw design",
      "Instructions lacking for inexperienced users"
    ],
    "topPositiveAspects": [
      "easy install (5x)",
      "very easy to install (4x)",
      "fairly easy to install (4x)",
      "easy to install (3x)",
      "Easy install (2x)"
    ],
    "topNegativeReasons": [
      "large physical dimensions that barely fit in electrical box (3x)",
      "very finicky operation with inconsistent light response (3x)",
      "need a deeper box for installation (2x)",
      "deeper than regular switches",
      "go offline regularly requiring power cycle"
    ],
    "topPositiveReasons": [
      "Three or four wire capability for 3-way or single pole install (2x)",
      "no neutral wire required (2x)",
      "never had a device disconnect (2x)",
      "Smaller than most dimmers",
      "No flickering or noise"
    ]
  },
  {
    "category": "Basic Functionality",
    "categoryType": "Performance",
    "mentions": 177,
    "positiveCount": 140,
    "negativeCount": 37,
    "totalReviews": 177,
    "satisfactionRate": 79.1,
    "negativeRate": 20.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "No longer switches",
      "On off switch does not work",
      "Did not work when installed",
      "Does not work",
      "Don't work well"
    ],
    "topPositiveAspects": [
      "works great (11x)",
      "works perfectly (9x)",
      "works as expected (6x)",
      "Works great (5x)",
      "works like a charm (4x)"
    ],
    "topNegativeReasons": [
      "Physically coming apart",
      "Barely dimmed with flickering on low",
      "one of the packs was used",
      "looked like they'd been shorted out",
      "absolute garbage"
    ],
    "topPositiveReasons": [
      "toggle functionality"
    ]
  },
  {
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 150,
    "positiveCount": 130,
    "negativeCount": 20,
    "totalReviews": 150,
    "satisfactionRate": 86.7,
    "negativeRate": 13.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Paint on the switch",
      "Color not as pictured",
      "Hard to find color in brick and mortar stores",
      "not the prettiest design",
      "ugly appearance"
    ],
    "topPositiveAspects": [
      "looks nice (5x)",
      "beautiful design (3x)",
      "nice design (3x)",
      "nice looking (2x)",
      "Sleek appearance (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 165,
    "positiveCount": 106,
    "negativeCount": 59,
    "totalReviews": 165,
    "satisfactionRate": 64.2,
    "negativeRate": 35.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Has wire connections instead of preferred screw clamp terminals",
      "Wire labeling and connection points",
      "pigtails that take up a lot of room",
      "permanently installed lead wires, not lugs",
      "wires substantially thinner than 14AWG Romex"
    ],
    "topPositiveAspects": [
      "requires neutral wire (5x)",
      "does not require neutral wire (2x)",
      "Requires neutral wire (2x)",
      "no neutral wire required (2x)",
      "back-connect screw-type connections"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Control Performance",
    "categoryType": "Performance",
    "mentions": 176,
    "positiveCount": 92,
    "negativeCount": 84,
    "totalReviews": 176,
    "satisfactionRate": 52.3,
    "negativeRate": 47.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "poor at lower levels of light and never takes intensity to zero",
      "flickers when turned up until partially turned up",
      "doesn't dim over full range, stops when lights still bright",
      "hums when dimmed to 50% or less",
      "Dimming failure"
    ],
    "topPositiveAspects": [
      "provides smooth dimming action",
      "provides fine dimming control",
      "takes lights down to lowest possible bit of light",
      "Proper dimming functionality",
      "Smooth fade effect"
    ],
    "topNegativeReasons": [
      "Dimmer slide moves too easily without resistance",
      "Broke after little over 1 year",
      "cheap_internal_parts",
      "all_fail_in_less_than_a_year_some_in_two_weeks",
      "Physical +/- buttons for dimming"
    ],
    "topPositiveReasons": [
      "Slider for dimming control (2x)",
      "Quick installation process (2x)",
      "acts as both switch and dimmer",
      "main unit and satellite unit configuration",
      "easy to integrate with Kasa app"
    ]
  },
  {
    "category": "Dimming Range Control",
    "categoryType": "Performance",
    "mentions": 118,
    "positiveCount": 78,
    "negativeCount": 40,
    "totalReviews": 118,
    "satisfactionRate": 66.1,
    "negativeRate": 33.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Not 1-100 percent dimming as advertised - LED light still insanely bright at lowest setting",
      "Dimmest setting not particularly dim - still quite bright",
      "Don't dim lights far enough down",
      "minimum dim level not low enough",
      "Dimming range and control"
    ],
    "topPositiveAspects": [
      "smooth dimming without flickering (2x)",
      "Allows dimming to 6% which is excellent",
      "Very adjustable - can turn brightness up or down by as little as 1%",
      "Full range of dimming capability",
      "Excellent dimming regulation"
    ],
    "topNegativeReasons": [
      "slider with loose at bottom to tight at top feel (2x)",
      "rocker switch broke in 3 months (2x)",
      "Touch sensor interface for dimming control",
      "Durability over time",
      "sensitive in the middle range"
    ],
    "topPositiveReasons": [
      "blue adjustment range toggle (5x)",
      "Touch sensor interface for dimming control (4x)",
      "Durability over time (4x)",
      "Capacitive touch strip for dimming (2x)",
      "Straightforward installation (2x)"
    ]
  },
  {
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 80,
    "positiveCount": 78,
    "negativeCount": 2,
    "totalReviews": 80,
    "satisfactionRate": 97.5,
    "negativeRate": 2.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "looks cheap",
      "looks bad"
    ],
    "topPositiveAspects": [
      "Sleek and modern appearance (2x)",
      "1970's rotary look",
      "Classic style ideal for traditional homes",
      "clean and modern looking",
      "sleek appearance"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Function",
    "categoryType": "Performance",
    "mentions": 108,
    "positiveCount": 76,
    "negativeCount": 32,
    "totalReviews": 108,
    "satisfactionRate": 70.4,
    "negativeRate": 29.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Unable to dim",
      "won't turn on unless dimmer is set high",
      "don't turn on when set to low light position",
      "light doesn't stay same dimness",
      "doesn't turn on when set below 80%"
    ],
    "topPositiveAspects": [
      "dims beautifully",
      "smooth dimming of lights",
      "snappy to turn on the lights and dim",
      "control is smooth and even",
      "work smoothly to dim all fixtures with no flickering"
    ],
    "topNegativeReasons": [
      "Slider jams and cannot be moved",
      "Flicker even when adjusted",
      "adjustment wheel component",
      "does not maintain set position",
      "has short in wiring"
    ],
    "topPositiveReasons": [
      "adjustable setting on internal face (2x)",
      "LED dimming-range adjustment lever",
      "lever style activation with bottom push and touch slider in middle",
      "setup to get connected to app is simple"
    ]
  }
];
export const topUseCasesDimmer: UseCaseFeedback[] = [
  {
    "useCase": "Smart Home Integration",
    "totalMentions": 325,
    "positiveCount": 198,
    "negativeCount": 65,
    "satisfactionRate": 60.9,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "works flawlessly with Apple HomeKit (19x)",
      "looks nice (15x)",
      "work pretty well (15x)",
      "Integrates flawlessly with smart home systems (13x)",
      "Easy to connect to Alexa (12x)"
    ],
    "topGapReasons": [
      "Thick build causing installation issues with multi-switch outlets (8x)",
      "Frequent WiFi disconnections (8x)",
      "not recognized by Philips Hue Hub (4x)",
      "Wire labeling and connection points (4x)",
      "App functionality and control (4x)"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Room Specific Lighting",
    "totalMentions": 167,
    "positiveCount": 105,
    "negativeCount": 42,
    "satisfactionRate": 62.9,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "Nice looking appearance (11x)",
      "Clicky button feel (11x)",
      "Works with Alexa integration (11x)",
      "Works with Google Home integration (11x)",
      "Voice control works well (11x)"
    ],
    "topGapReasons": [
      "Touch sensor interface for dimming control (9x)",
      "Durability over time (9x)",
      "Overall functionality reliability (4x)",
      "Light flickering issues (3x)",
      "smooth dimming without flickering (2x)"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Led Compatibility Applications",
    "totalMentions": 163,
    "positiveCount": 87,
    "negativeCount": 63,
    "satisfactionRate": 53.4,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "works with LED bulbs (14x)",
      "works great with LED lights without flickering (8x)",
      "solves LED light flickering issue (8x)",
      "good match for led under cabinet lighting (5x)",
      "work great with dimmable LED bulbs (5x)"
    ],
    "topGapReasons": [
      "bulbs flash 5 times at full brightness when dimmed (8x)",
      "lights flicker when dimming (8x)",
      "poor LED compatibility (8x)",
      "defective slider mechanism (8x)",
      "flickers with LED lights (8x)"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Room Specific Applications",
    "totalMentions": 142,
    "positiveCount": 76,
    "negativeCount": 38,
    "satisfactionRate": 53.5,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "Well-made plastic that doesn't feel cheap or brittle (25x)",
      "Easy installation process (25x)",
      "Compact size (23x)",
      "Standard decorator switch size (23x)",
      "Better build quality than some competitors (23x)"
    ],
    "topGapReasons": [
      "cheap_internal_parts (15x)",
      "switch_breaks_at_pivot_point (15x)",
      "switch_physically_fails_to_work (15x)",
      "switch_feels_cheap (15x)",
      "all_fail_in_less_than_a_year_some_in_two_weeks (15x)"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Smart Home Automation",
    "totalMentions": 128,
    "positiveCount": 82,
    "negativeCount": 24,
    "satisfactionRate": 64.1,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "works great (10x)",
      "works as intended (10x)",
      "works very well (9x)",
      "works without issue (9x)",
      "works perfectly (9x)"
    ],
    "topGapReasons": [
      "missing screws and wire caps in used condition (6x)",
      "connection issues with Kasa app on phones (6x)",
      "won't pair with Android or iPhone (6x)",
      "faulty products don't work (6x)",
      "defective and don't work (6x)"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Led Lighting Integration",
    "totalMentions": 82,
    "positiveCount": 47,
    "negativeCount": 20,
    "satisfactionRate": 57.3,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "eliminates buzzing/humming from LED lights (14x)",
      "works with low voltage LED fixtures (5x)",
      "slides smoothly (2x)",
      "works as intended (2x)",
      "Works with 14 LED pot lights with no hum"
    ],
    "topGapReasons": [
      "does not eliminate buzzing (2x)",
      "Not compatible with LED lights",
      "does not dim G4 LED bulbs",
      "aluminum sides",
      "only 15% light reduction before stopping"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Smart Home Automation Integration",
    "totalMentions": 79,
    "positiveCount": 60,
    "negativeCount": 12,
    "satisfactionRate": 75.9,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "works with multiple smart home platforms (12x)",
      "has external wires rather than wiring into screws (12x)",
      "works great with Alexa and Google Assistant (12x)",
      "works 100% of the time (6x)",
      "bullet-proof connection and consistent performance (6x)"
    ],
    "topGapReasons": [
      "only one traveler wire terminal instead of standard two (3x)",
      "stops responding to Alexa for days every few weeks (3x)",
      "Alexa won't recognize switch (3x)",
      "doesn't dim on verbal commands well (3x)",
      "few switches started to disconnect after over 1 year"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Remote And Mobile Control",
    "totalMentions": 69,
    "positiveCount": 39,
    "negativeCount": 10,
    "satisfactionRate": 56.5,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "hub connected to router super quickly (6x)",
      "quickest and easiest smart home app setup (6x)",
      "smart bridge installed quickly and easily (6x)",
      "hub and mobile app easy to set up (6x)",
      "Magnetizes to wall holder (5x)"
    ],
    "topGapReasons": [
      "Bulky build not fitting small junction boxes (3x)",
      "Complete connectivity failure (3x)",
      "Thick build causing installation issues with multi-switch outlets (2x)",
      "Frequent WiFi disconnections (2x)",
      "pico remote working only 35-40% of the time"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Multi Location Switching",
    "totalMentions": 64,
    "positiveCount": 43,
    "negativeCount": 12,
    "satisfactionRate": 67.2,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "works reliably (8x)",
      "works perfectly (7x)",
      "main unit and satellite unit configuration (5x)",
      "very clear instructions (5x)",
      "easy to integrate with Kasa app (5x)"
    ],
    "topGapReasons": [
      "not compatible with standard 3-way configuration (2x)",
      "will not work with existing 3-way configuration (2x)",
      "hard to install if line and load in same junction box",
      "cannot change dimmer brightness from accessory switch",
      "single tap turns on to main dimmer level"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Led Lighting Control",
    "totalMentions": 59,
    "positiveCount": 43,
    "negativeCount": 14,
    "satisfactionRate": 72.9,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "comes with multiple color knobs (10x)",
      "works well with LED lighting (10x)",
      "high end appearance (4x)",
      "works with LED bulbs without flickering (4x)",
      "fully adjustable (3x)"
    ],
    "topGapReasons": [
      "at low settings lights flicker sometimes (2x)",
      "causes buzzing when fixture is lit (2x)",
      "LED bulb compatibility issues",
      "Dimmest setting not particularly dim - still quite bright",
      "stopped working after 4 years, can't reach full power"
    ],
    "relatedCategories": []
  }
];
export const allDimmerCategories: CategoryFeedback[] = [
  {
    "category": "Electrical Safety",
    "categoryType": "Performance",
    "mentions": 24,
    "positiveCount": 0,
    "negativeCount": 24,
    "totalReviews": 24,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "overheats and becomes very hot to touch",
      "Switch exploded",
      "Switch causes internal arcing",
      "trips breaker every time",
      "Wi-Fi smart switches get hot"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Has red and one black wire that does not conform to residential wiring",
      "Flickers even when turned all the way up",
      "Pivot of the rocker broke on one side",
      "Lights flickering without adjusting dimmer",
      "USB leads poorly soldered with bad wire stripping"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Response Speed",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 0,
    "negativeCount": 7,
    "totalReviews": 7,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Delay before turning on or off when pressing physical button",
      "toggling physical switch has random delays to turn on/off light",
      "Delay when turning on light"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Surface Characteristics",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "dimmer and plate were scratched and sticky",
      "Leviton printed into the face collects dirt"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Software Experience",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "terrible software and install experience",
      "worst install experience for any smart home device",
      "showing countless errors with zero real guidance"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Defect Rate",
    "categoryType": "Performance",
    "mentions": 17,
    "positiveCount": 0,
    "negativeCount": 17,
    "totalReviews": 17,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "at least 25% failure rate",
      "50% failure rate",
      "One switch was defective right out of box",
      "3 of 4 don't work",
      "only 2 of 3 pack worked"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Power Sensitivity",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "do not like being played with, fluctuations in power will kill them"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Power Control Accuracy",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Switch fails to turn off completely"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Condition Issues",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "damaged wires"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Manufacturing Quality",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 0,
    "negativeCount": 19,
    "totalReviews": 19,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "one was defective",
      "Received used switches with paint and cut wires",
      "Some units broken out of box",
      "Some units don't work out of box",
      "Some were open and previously used"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Slider for dimmer",
      "Switch won't stay on/off"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Setup Complexity",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 0,
    "negativeCount": 5,
    "totalReviews": 5,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "z-wave configuration options",
      "parameter 16 functionality",
      "complicated_and_finicky",
      "programming_requires_appropriate_sized_tool"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "requires_separate_neutral_wire",
      "cal_button_requires_firm_press"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Color Matching",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "White color doesn't match standard white switches",
      "White color much brighter than typical switches"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Toggle Operation",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "toggle feels like it's going to fall off"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Complexity",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 0,
    "negativeCount": 5,
    "totalReviews": 5,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "very hard to install",
      "very frustrating to install",
      "sometimes a little hard to install",
      "not so easy to install",
      "more complicated than expected"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "terminals inset into body with too much gap (2x)",
      "push-in connection hole too small for 12-gauge wire (2x)",
      "dimmer function died after six weeks (2x)",
      "neutral wire requirement"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Position Stability",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not maintain set position"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "adjustment wheel component",
      "does not maintain set position"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Audible Noise Problems",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 0,
    "negativeCount": 9,
    "totalReviews": 9,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "High-pitched whining noise",
      "Hissing sound emission",
      "make a low buzzing sound",
      "makes an audible humming noise when power is on",
      "switches buzz while turned on"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Current Leakage",
    "categoryType": "Performance",
    "mentions": 11,
    "positiveCount": 0,
    "negativeCount": 11,
    "totalReviews": 11,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Current leakage causing LED glow when off",
      "high amount of leakage on common line",
      "lights still glow when turned off",
      "leaks energy",
      "lights very faintly lit when in off position"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Defects",
    "categoryType": "Performance",
    "mentions": 13,
    "positiveCount": 0,
    "negativeCount": 13,
    "totalReviews": 13,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Product was defective",
      "delivered_as_broken_and_not_functional",
      "manufacturing defect",
      "did not work from day 1",
      "didn't work when wired up"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color Accuracy",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "brighter white borders that don't match regular switches"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Batch Failure Rates",
    "categoryType": "Performance",
    "mentions": 18,
    "positiveCount": 0,
    "negativeCount": 18,
    "totalReviews": 18,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "25% failure rate",
      "all_fail_in_less_than_a_year_some_in_two_weeks",
      "one_falls_apart_during_installation",
      "all_5_failed_within_3_years",
      "3_out_of_6_broken_after_4_years"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "cheap_internal_parts",
      "all_fail_in_less_than_a_year_some_in_two_weeks",
      "little_tab_breaks_during_installation",
      "one_falls_apart_during_installation",
      "switch_breaks_at_pivot_point"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Magnetic Attachment",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Remote keeps getting bumped and knocked out",
      "Repels magnet causing it to turn at angle"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Magnet is terrible",
      "No magnets, only adhesive strips",
      "Battery does not last more than few weeks"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Surface Durability",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "scratched surface"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Short Term Reliability",
    "categoryType": "Performance",
    "mentions": 13,
    "positiveCount": 0,
    "negativeCount": 13,
    "totalReviews": 13,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "only 3 out of 8 devices still working after 4 years",
      "2 died in the first year",
      "worked fine last night but dead today after 3 months",
      "never worked again after blinking blue",
      "worked for a day and then died"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "started blinking blue after 3 years",
      "2 died in the first year"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Requirements",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Requires 4 wires at the box"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Internal Mechanical Parts",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 0,
    "negativeCount": 7,
    "totalReviews": 7,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "internal switch mechanism",
      "paddle pins",
      "aluminum sides",
      "cheap_internal_parts",
      "switch_breaks_at_pivot_point"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Operation Feel",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Rocker switch feels flimsy/cheap"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Light Output Control",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 0,
    "negativeCount": 10,
    "totalReviews": 10,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Will not completely shut off",
      "leaves small amount of voltage on lights when turned off",
      "lights stayed on and never fully shut off",
      "does not completely shut off LED lights",
      "Does not turn LED lights completely off"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Behavior Issues",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 0,
    "negativeCount": 7,
    "totalReviews": 7,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "both travelers powered in ON state, both off in OFF state",
      "dumps up to 120V with mass current briefly on neutral line when powering on",
      "causes voltage leak into neutral of other smart switches",
      "send signals through electrical system causing issues with LED bulbs",
      "remains powered on lowest setting on one traveler when switch restarts"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Space Requirements",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 0,
    "negativeCount": 5,
    "totalReviews": 5,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "bulky and pain to fit everything in box",
      "takes up valuable space in existing box making pushing wires challenging",
      "very hard to get switches back in electrical housing box",
      "takes up more space than original switches",
      "may require additional work for tight spaces"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "larger than basic switch (2x)",
      "deeper than standard rocker switches (2x)",
      "doesn't work (2x)",
      "massive box size",
      "pre-attached wires instead of using existing wall cables"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Multi-Circuit Control",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "second switch cannot be powered switch"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Brand and Device Compatibility",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not compatible with kasa switches",
      "only works with regular mechanical switch"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Deterioration",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "broke from pressure of wires in multi-gang box",
      "they crack"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "very cheap plastic",
      "fails after a while"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Surface Condition and Finish",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 0,
    "negativeCount": 5,
    "totalReviews": 5,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "gunk and grime all over it",
      "label is old, worn and falling off",
      "very scratched",
      "dry wall plaster all over it",
      "used condition appearance"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Component Reliability",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 0,
    "negativeCount": 5,
    "totalReviews": 5,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "spring in the on off snapped",
      "Screws do not stay set",
      "Screw lugs collapse into body of switch",
      "mounting screws strip almost immediately",
      "phillips screws instead of robertson screws"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Settings Memory",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not return to selected dimming setting when switched on",
      "no dim level memory or way to set default dim level"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "top button goes to full brightness (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Switch Reliability",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stopped working on manual press after only a month"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Touch Responsiveness",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "very sensitive and cuts off",
      "too sensitive - dimmer adjusts when waving near it"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Cross Talk Issues",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 0,
    "negativeCount": 4,
    "totalReviews": 4,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "communication between switches is crossed",
      "when dimming in living room they dimmed all lights in house",
      "will start to glitch early on if more than 1 treatlife switch on same breaker",
      "always dimming on its own"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wall Plate Fit and Alignment",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "face is not recessed so cover plate sits proud of wall",
      "wall plate moves around when bumped"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wire Connection Issues",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "difficult to install due to wire connection"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "has bolts on side and bottom to attach wires",
      "very narrow brightness range with LEDs and buzzing"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Physical Feel",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Has loose, cheap feel",
      "Switch action feels low quality"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Feels cheap and flimsy with poor construction quality"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Mechanism Reliability",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 0,
    "negativeCount": 9,
    "totalReviews": 9,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "on off toggle fails frequently",
      "had to press on-off button several times to make it work",
      "stopped working completely couldn't turn lights off",
      "stopped reliably turning on and off",
      "to turn on or off would take 3-10 pushes"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Internal Mounting Components",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Plastic carrier can be pulled in too far if over-tightened"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Build Quality Perception",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 0,
    "negativeCount": 6,
    "totalReviews": 6,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "feel_very_cheap",
      "very_low_quality",
      "feel_terrible",
      "cheaply_made",
      "could be more refined"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "soft_mushy_switches_after_installing",
      "dimmer_doesnt_work_smoothly_after_installation",
      "noisy operation",
      "button breaks off",
      "don't last"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Remote Control Functionality",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "becomes non-responsive to Alexa commands"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Feedback",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "creaks when button pressed"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Safety Concerns",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "smelled like burning"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Reliability",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "loss of continuity between terminals"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "wire connection terminals",
      "works with LED bulbs"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Design Integration",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Does not match other white Lutron dimmers"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Has yellow tint instead of pure white"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Housing",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "susceptible_to_pressure_from_wires_or_materials"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Power Handling",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cannot handle switched outlets"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Flickering Issues",
    "categoryType": "Performance",
    "mentions": 37,
    "positiveCount": 1,
    "negativeCount": 36,
    "totalReviews": 37,
    "satisfactionRate": 2.7,
    "negativeRate": 97.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Light flickering and delay issues",
      "Flickers even when turned all the way up",
      "Lights flickering without adjusting dimmer",
      "Started causing flickering in lights",
      "Lights flicker every now and then despite adjustment"
    ],
    "topPositiveAspects": [
      "doesn't make the lights flicker"
    ],
    "topNegativeReasons": [
      "Cheaply made",
      "adjustment wheel can only be accessed after taking cover plate off"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Product Longevity",
    "categoryType": "Performance",
    "mentions": 66,
    "positiveCount": 2,
    "negativeCount": 64,
    "totalReviews": 66,
    "satisfactionRate": 3.0,
    "negativeRate": 97.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Failed after two years (2x)",
      "Stopped functioning after 1 month",
      "3 out of 4 will not re-pair in less than a year",
      "One switch stops working after couple of days",
      "Dies within months - had 3 die in a year"
    ],
    "topPositiveAspects": [
      "long-term durability",
      "Lasted 9 years before going out"
    ],
    "topNegativeReasons": [
      "internal switch mechanism (2x)",
      "prone to polarity reversal causing failure",
      "failed after few months",
      "All plastic plate that attaches to the box",
      "plastic flip switch falls out"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Switch Controls",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 1,
    "negativeCount": 18,
    "totalReviews": 19,
    "satisfactionRate": 5.3,
    "negativeRate": 94.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "manual switches would sometimes work and sometimes not after few months",
      "manual switches do not work at all and light turns off half minute later",
      "lights_still_turn_on_and_off_but_dimmer_fails",
      "switch_becomes_very_hard_to_use_after_installation",
      "rocker_takes_little_effort_to_mistakenly_switch_off_when_trying_to_switch_on"
    ],
    "topPositiveAspects": [
      "Consistent manual operation"
    ],
    "topNegativeReasons": [
      "cheap_internal_parts",
      "all_fail_in_less_than_a_year_some_in_two_weeks",
      "rocker_is_very_loose_and_finicky",
      "one_worked_for_week_another_6_months_two_made_it_over_year",
      "soft_mushy_switches_after_installing"
    ],
    "topPositiveReasons": [
      "Proper dimming functionality"
    ]
  },
  {
    "category": "Electrical Interference",
    "categoryType": "Performance",
    "mentions": 14,
    "positiveCount": 1,
    "negativeCount": 13,
    "totalReviews": 14,
    "satisfactionRate": 7.1,
    "negativeRate": 92.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "can interfere with harmonics of each other or other dimmers if not enough current draw",
      "shuts down other lights and outlets on same circuit",
      "other lights on circuit not at full brightness when dimmer off",
      "Interference between WiFi switch and WiFi bulbs",
      "2.4GHz module causing WiFi interference"
    ],
    "topPositiveAspects": [
      "No Radio Frequency Interference beyond 18 inches"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Safety Performance",
    "categoryType": "Performance",
    "mentions": 11,
    "positiveCount": 1,
    "negativeCount": 10,
    "totalReviews": 11,
    "satisfactionRate": 9.1,
    "negativeRate": 90.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "main switch popped and smelled like burning electric",
      "very dangerous to sell something electrical as \"new\" that's used and faulty",
      "ESP8266 boards burned out and became very hot when powered",
      "unit with failed relay became hot to touch",
      "sparked_when_turning_on"
    ],
    "topPositiveAspects": [
      "no self shut down from over heating"
    ],
    "topNegativeReasons": [
      "one of the packs was used",
      "looked like they'd been shorted out",
      "absolute garbage",
      "ESP8266 boards",
      "relay failed after about 2 years"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Range",
    "categoryType": "Performance",
    "mentions": 42,
    "positiveCount": 4,
    "negativeCount": 38,
    "totalReviews": 42,
    "satisfactionRate": 9.5,
    "negativeRate": 90.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "limited dimming range with 25% minimum",
      "fades to off halfway down",
      "light dims quickly and is off half way down",
      "barely changes brightness of bulb",
      "worst dimming range with only two settings dim and full on"
    ],
    "topPositiveAspects": [
      "excellent dimming range",
      "wide dimming range",
      "Dims from 99% down to 1% with compatible fixtures"
    ],
    "topNegativeReasons": [
      "slide is too short",
      "bulbs don't dim as much",
      "round dial on right side with no luck adjusting",
      "LED light stays on at very low illumination at lowest setting"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Terminal Connections",
    "categoryType": "Physical",
    "mentions": 10,
    "positiveCount": 1,
    "negativeCount": 9,
    "totalReviews": 10,
    "satisfactionRate": 10.0,
    "negativeRate": 90.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "set screw was fused and would not tighten",
      "stripped screw complicates installation",
      "brass screw on Y terminal was stripped",
      "unable to loosen screws that secure wires",
      "factory torqued screws to excessive tightness"
    ],
    "topPositiveAspects": [
      "wires can be removed by loosening side screw"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Response Time",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 1,
    "negativeCount": 9,
    "totalReviews": 10,
    "satisfactionRate": 10.0,
    "negativeRate": 90.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "have a delay when lighting, anywhere from a couple of seconds to 5 or 6 seconds",
      "noticeable delay between flipping switch and lights coming on",
      "turn off response delay",
      "ramp up/down times",
      "1_to_2_second_delay_turning_on"
    ],
    "topPositiveAspects": [
      "switches on and off smoothly"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Packaging Quality",
    "categoryType": "Physical",
    "mentions": 39,
    "positiveCount": 4,
    "negativeCount": 35,
    "totalReviews": 39,
    "satisfactionRate": 10.3,
    "negativeRate": 89.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Package arrived ripped up",
      "opened box",
      "small box not matching picture",
      "switch box falling apart",
      "appeared previously used with loose wire nuts"
    ],
    "topPositiveAspects": [
      "Packaging is new with improved quality",
      "arrived on time well packed",
      "nicely packaged",
      "has clear window in packaging"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Material Composition",
    "categoryType": "Physical",
    "mentions": 18,
    "positiveCount": 2,
    "negativeCount": 16,
    "totalReviews": 18,
    "satisfactionRate": 11.1,
    "negativeRate": 88.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cheap plastic",
      "Material feels low quality",
      "lower grade plastic material compared to name brand switches",
      "flimsy plastic construction",
      "very cheap plastic"
    ],
    "topPositiveAspects": [
      "metal housing",
      "Premium material quality"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Basic Switching Operation",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 1,
    "negativeCount": 8,
    "totalReviews": 9,
    "satisfactionRate": 11.1,
    "negativeRate": 88.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stopped working (2x)",
      "impossible to turn on or off",
      "upside down operation",
      "intermittent functionality",
      "often does not turn on/off without precise pressing"
    ],
    "topPositiveAspects": [
      "turns lights on and off as expected"
    ],
    "topNegativeReasons": [
      "upside down orientation marking (2x)",
      "breaks under normal use",
      "not durable",
      "requires precise square pressing in middle to function",
      "will not connect to WiFi"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Rocker Switch Mechanisms",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 1,
    "negativeCount": 7,
    "totalReviews": 8,
    "satisfactionRate": 12.5,
    "negativeRate": 87.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "rocker is stiff to turn on/off",
      "Small ball with spring allowing toggling of metal contactor rocker comes loose with normal use",
      "Rocker switch mechanism is poorly designed",
      "Rocker pivots on two small points (1/8\" or less)",
      "Plastic rocker construction prone to breaking"
    ],
    "topPositiveAspects": [
      "switch is flush on the front"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Light Fixture Compatibility",
    "categoryType": "Performance",
    "mentions": 15,
    "positiveCount": 2,
    "negativeCount": 13,
    "totalReviews": 15,
    "satisfactionRate": 13.3,
    "negativeRate": 86.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Causes dim glow when set to off with certain LED fixtures",
      "Not compatible with some LED recessed lights",
      "Causes wild noises with non-dimmable bulbs",
      "Need to swap out some bulbs in multiple bulb fixtures",
      "Light flickering issues"
    ],
    "topPositiveAspects": [
      "Compatible with various LED bulbs and fixtures",
      "Works with dimmable and non-dimmable bulbs"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Light Flickering",
    "categoryType": "Performance",
    "mentions": 29,
    "positiveCount": 4,
    "negativeCount": 25,
    "totalReviews": 29,
    "satisfactionRate": 13.8,
    "negativeRate": 86.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "causes lights to flicker",
      "flickers intensely at highest brightness",
      "Makes the bulbs flicker and sometimes they won't come on",
      "You have to move the dimmer in order to make them work",
      "The light flickers with all three, even on full power"
    ],
    "topPositiveAspects": [
      "Least likely to cause flickering issues in LED bulbs and panels",
      "Flicker free operation",
      "flicker free",
      "small amount of flickering but improved from previous switches"
    ],
    "topNegativeReasons": [
      "Dimmer adjuster is not built well"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Product Value",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 1,
    "negativeCount": 6,
    "totalReviews": 7,
    "satisfactionRate": 14.3,
    "negativeRate": 85.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Expensive for features offered"
    ],
    "topPositiveAspects": [
      "Good quality for price"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Controls",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 1,
    "negativeCount": 6,
    "totalReviews": 7,
    "satisfactionRate": 14.3,
    "negativeRate": 85.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "On/off button responsiveness",
      "requires multiple presses to work since first press usually isn't hard enough",
      "Finger brushes dimmer when turning off, changing brightness",
      "Gets stuck on minimum position when adjusting",
      "click but light doesn't turn on if not pressed hard enough"
    ],
    "topPositiveAspects": [
      "On/off button responsiveness"
    ],
    "topNegativeReasons": [
      "Physical button for on/off operation (2x)",
      "Wi-Fi connectivity stability (2x)",
      "buttons require much firmer push than other switches",
      "worked fine with everything except LEDs",
      "Dimmer slide button stands too prominent from switch face"
    ],
    "topPositiveReasons": [
      "Physical button for on/off operation",
      "Wi-Fi connectivity stability"
    ]
  },
  {
    "category": "Status Accuracy",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 1,
    "negativeCount": 6,
    "totalReviews": 7,
    "satisfactionRate": 14.3,
    "negativeRate": 85.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Doesn't show correct status in application, shows on when it's off",
      "Fails to turn on via Z-Wave but reports it did turn on",
      "Fails to turn off but reports it did turn off",
      "Fails to report updated status when turned on or off with paddle",
      "On/off status inconsistent with SmartThings status"
    ],
    "topPositiveAspects": [
      "both switches show current dimming level"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Response Time",
    "categoryType": "Performance",
    "mentions": 26,
    "positiveCount": 4,
    "negativeCount": 22,
    "totalReviews": 26,
    "satisfactionRate": 15.4,
    "negativeRate": 84.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Second or two delay from clicking switch to light turning on",
      "delayed response when turning light on",
      "lights are delayed coming on after switch is flipped",
      "hesitates when turning on",
      "slow response time"
    ],
    "topPositiveAspects": [
      "Very responsive, no lag",
      "responsive switch operation",
      "responsive",
      "instant response time"
    ],
    "topNegativeReasons": [
      "Light flickers when set to dim",
      "clicks",
      "does not dim low enough"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Button and Switch Operation",
    "categoryType": "Physical",
    "mentions": 18,
    "positiveCount": 3,
    "negativeCount": 15,
    "totalReviews": 18,
    "satisfactionRate": 16.7,
    "negativeRate": 83.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "buttons failed after 3 years",
      "buttons require much firmer push than other switches",
      "manual operation uses only bottom half of switch for both on and off",
      "buttons require pressing to dim up or down",
      "on/off switch could be a little larger"
    ],
    "topPositiveAspects": [
      "button layout with brightness buttons easy to press and on/off big enough",
      "separate on/off switch",
      "toggle switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Lifespan",
    "categoryType": "Performance",
    "mentions": 167,
    "positiveCount": 29,
    "negativeCount": 138,
    "totalReviews": 167,
    "satisfactionRate": 17.4,
    "negativeRate": 82.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "lasted less than a year (2x)",
      "didn't last 3 months (2x)",
      "lasted all of 2 months",
      "switch lasted 3 days until completely stopped working",
      "had two fail in two years"
    ],
    "topPositiveAspects": [
      "Old push click lasted 32 years",
      "First one lasted 6 years",
      "First one lasted 5 years",
      "Old switch lasted 40+ years",
      "works after 28 years of previous dimmer use"
    ],
    "topNegativeReasons": [
      "feel cheap (2x)",
      "delay when turning on far too long (2x)",
      "very poor quality",
      "barley dims the light",
      "Air gap plug under paddle that spontaneously pops out and cannot be reinserted"
    ],
    "topPositiveReasons": [
      "IP44 weather resistance rating"
    ]
  },
  {
    "category": "Network Connection Stability",
    "categoryType": "Performance",
    "mentions": 119,
    "positiveCount": 21,
    "negativeCount": 98,
    "totalReviews": 119,
    "satisfactionRate": 17.6,
    "negativeRate": 82.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "disconnect from network frequently",
      "WiFi feature stops working after couple months",
      "difficult to connect to app",
      "Frequent WiFi disconnections",
      "Complete connectivity failure"
    ],
    "topPositiveAspects": [
      "no issues with connectivity (2x)",
      "connects to WiFi effectively",
      "connects to Tapo app successfully",
      "no connection issues experienced",
      "Easy WiFi connection setup"
    ],
    "topNegativeReasons": [
      "Red blinking LED status (2x)",
      "Settings change back to full brightness automatically (2x)",
      "ESP8266 boards",
      "relay failed after about 2 years",
      "screen becomes blank and unresponsive"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Dimmer Controls",
    "categoryType": "Physical",
    "mentions": 11,
    "positiveCount": 2,
    "negativeCount": 9,
    "totalReviews": 11,
    "satisfactionRate": 18.2,
    "negativeRate": 81.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Sharp slider dial that can hurt when touched",
      "Dimmer slider with adjustable positions",
      "Dimmer gets stuck slightly on minimum position",
      "Dimmer slide button stands too prominent from switch face",
      "Dimmer bar with halfway position"
    ],
    "topPositiveAspects": [
      "Tiny slider at the bottom of the switch paddle",
      "Easy slide mechanism"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Durability",
    "categoryType": "Performance",
    "mentions": 27,
    "positiveCount": 5,
    "negativeCount": 22,
    "totalReviews": 27,
    "satisfactionRate": 18.5,
    "negativeRate": 81.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Fall apart during installation",
      "Rocker switch mechanism failed with very little use",
      "ON/OFF function defeated with normal use",
      "Cracked plastic insert and missing retainers",
      "Rocker side breaks off after 3-4 months"
    ],
    "topPositiveAspects": [
      "sturdy (2x)",
      "long service life if not abused",
      "well built",
      "Still work and feel same after half year"
    ],
    "topNegativeReasons": [
      "Small ball with spring allowing toggling of metal contactor rocker comes loose with normal use (2x)",
      "Plastic rocker construction prone to breaking (2x)",
      "Doesn't dim up or down, stays dim (2x)",
      "Extremely low quality construction",
      "Rocker pivots on two small points (1/8\" or less)"
    ],
    "topPositiveReasons": [
      "robust ON/OFF switch with positive snap",
      "no flickering and 3-way works",
      "quality wiring",
      "switch is working perfectly",
      "Satisfying snap mechanism"
    ]
  },
  {
    "category": "Light Flickering Issues",
    "categoryType": "Performance",
    "mentions": 36,
    "positiveCount": 7,
    "negativeCount": 29,
    "totalReviews": 36,
    "satisfactionRate": 19.4,
    "negativeRate": 80.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "causes lights to blink",
      "causes flickering",
      "causes periodic light flickering",
      "creates flicker",
      "causes light to flicker"
    ],
    "topPositiveAspects": [
      "eliminates flickering",
      "no flickering issues",
      "stops flickering at lowest or highest setting",
      "reduced flickering performance"
    ],
    "topNegativeReasons": [
      "low quality construction",
      "most dimmers did not work"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Product Packaging",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 1,
    "negativeCount": 4,
    "totalReviews": 5,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "damaged/opened packaging"
    ],
    "topPositiveAspects": [
      "packaged properly"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Heat Management",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 1,
    "negativeCount": 4,
    "totalReviews": 5,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Keeps turning off after 15 min when dimmed 100% due to overheating",
      "gets quite hot during use",
      "gets a little warm occasionally"
    ],
    "topPositiveAspects": [
      "doesn't produce heat"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "sturdy metal construction",
      "brings lights from bright down to whisper"
    ]
  },
  {
    "category": "Remote Control Performance",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 1,
    "negativeCount": 4,
    "totalReviews": 5,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "pico remote working only 35-40% of the time",
      "remote is useless",
      "repeaters have limited range",
      "remotes only work occasionally"
    ],
    "topPositiveAspects": [
      "very surprising range in 2,200 sq ft home"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Plug Configuration",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 1,
    "negativeCount": 4,
    "totalReviews": 5,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "non polarized plug",
      "plug orientation reversed by manufacturer"
    ],
    "topPositiveAspects": [
      "90 degree plug design"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Device Programming",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 1,
    "negativeCount": 4,
    "totalReviews": 5,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "programming was often a problem or impossibility",
      "could not be programmed without internet access",
      "pairing was challenging but manageable",
      "app is poor and difficult to program"
    ],
    "topPositiveAspects": [
      "programming is fairly simple"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Basic Power Control",
    "categoryType": "Performance",
    "mentions": 34,
    "positiveCount": 7,
    "negativeCount": 27,
    "totalReviews": 34,
    "satisfactionRate": 20.6,
    "negativeRate": 79.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "switch only works when dimmer is on low",
      "not sending power to the light despite WiFi connection",
      "one switch won't turn lights all the way off",
      "Light does not come on when dimmed to desired level",
      "When dimmed to 30-35% brightness, lights will not come on next time"
    ],
    "topPositiveAspects": [
      "Works 100% as intended with correct bulbs",
      "Proper power switching",
      "relay cuts power to device when turning off",
      "reliably turns lights on every time"
    ],
    "topNegativeReasons": [
      "Internal relay component",
      "Powers on but doesn't turn on light"
    ],
    "topPositiveReasons": [
      "has built in relay (2x)",
      "requires fast cadence triple press for pairing (2x)"
    ]
  },
  {
    "category": "System Response Speed",
    "categoryType": "Performance",
    "mentions": 29,
    "positiveCount": 6,
    "negativeCount": 23,
    "totalReviews": 29,
    "satisfactionRate": 20.7,
    "negativeRate": 79.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "significant lag before coming on sometimes",
      "second delay when turning on",
      "has a delay",
      "half second delay not instant on",
      "very slow to turn on light with 1-2 second lag"
    ],
    "topPositiveAspects": [
      "Responds quickly and reliably",
      "Very responsive with no connection issues",
      "HomeKit requests are fast and reliable",
      "switch is responsive",
      "no delay when using"
    ],
    "topNegativeReasons": [
      "cannot dim less than 50% without strobing (8x)"
    ],
    "topPositiveReasons": [
      "touchscreen is responsive"
    ]
  },
  {
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 28,
    "positiveCount": 6,
    "negativeCount": 22,
    "totalReviews": 28,
    "satisfactionRate": 21.4,
    "negativeRate": 78.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "came with no mounting screws",
      "Missing mounting screws",
      "included yellow wire nuts too big for box",
      "Missing load screw and internal screw plate",
      "Tiny screws included for installation are inconvenient"
    ],
    "topPositiveAspects": [
      "mounting and finishing screws are high-quality",
      "Metal plate instead of plastic for mounting",
      "Screw holes are standard size",
      "No screws on mounting plate",
      "breakable wings on sides for fitting"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Cover Plates",
    "categoryType": "Physical",
    "mentions": 18,
    "positiveCount": 4,
    "negativeCount": 14,
    "totalReviews": 18,
    "satisfactionRate": 22.2,
    "negativeRate": 77.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "no faceplate included (2x)",
      "cover plate difficult to snap on",
      "enclosed cover wouldn't stay on",
      "No cover included",
      "Face plate has broken off from the switch"
    ],
    "topPositiveAspects": [
      "screw-secured cover",
      "snap-on cover plate without screws for cleaner look"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 13,
    "positiveCount": 3,
    "negativeCount": 10,
    "totalReviews": 13,
    "satisfactionRate": 23.1,
    "negativeRate": 76.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "loud clicks",
      "bad tactile feel",
      "lacks tactile feel of normal switches",
      "would prefer more click feedback when pressed but still gives fair amount",
      "tactile feeling feels mushy and cheap"
    ],
    "topPositiveAspects": [
      "solid click sound",
      "tactile quality feel",
      "satisfying positive click better than springy higher pitch click"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Software Updates",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 1,
    "negativeCount": 3,
    "totalReviews": 4,
    "satisfactionRate": 25.0,
    "negativeRate": 75.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Firmware update crashes",
      "Frequent unnecessary updates",
      "No firmware support for WiFi issues"
    ],
    "topPositiveAspects": [
      "receives frequent software updates with new features"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Indicator Lights and Visual Feedback",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 1,
    "negativeCount": 3,
    "totalReviews": 4,
    "satisfactionRate": 25.0,
    "negativeRate": 75.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "LED indicator color changing not supported",
      "blue light too bright",
      "started blinking blue after 3 years"
    ],
    "topPositiveAspects": [
      "blue indicator light goes on and off to indicate switch cycling"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Reliability",
    "categoryType": "Performance",
    "mentions": 122,
    "positiveCount": 32,
    "negativeCount": 90,
    "totalReviews": 122,
    "satisfactionRate": 26.2,
    "negativeRate": 73.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Switch stays on full and will not dim or shut off after 2 years",
      "Malfunctions after a while",
      "One stopped working and cannot be configured or connect to wifi",
      "Randomly blinks green and turns lights on at full at night",
      "Switch does not work when clicked and clicks off/on by itself after 3 years"
    ],
    "topPositiveAspects": [
      "Consistently reliable",
      "Flawless performance for years",
      "Never had an issue",
      "Most stable automation products",
      "Incredibly reliable with 60+ devices"
    ],
    "topNegativeReasons": [
      "Falls apart after installation (3x)",
      "Sensitivity is not fully linear nor particularly good (3x)",
      "very thin cables (2x)",
      "poor_overall_quality (2x)",
      "switches_fail_within_short_time (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Noise",
    "categoryType": "Performance",
    "mentions": 11,
    "positiveCount": 3,
    "negativeCount": 8,
    "totalReviews": 11,
    "satisfactionRate": 27.3,
    "negativeRate": 72.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "makes electric buzzing sound",
      "Buzzing noise during operation",
      "electrical hum",
      "buzzing noise",
      "continuous noise"
    ],
    "topPositiveAspects": [
      "no buzzing experienced",
      "No buzz or hum",
      "Silent dimming with no humming noises"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Experience",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 2,
    "negativeCount": 5,
    "totalReviews": 7,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Installation was very difficult",
      "difficult to install",
      "wiring instructions incorrect"
    ],
    "topPositiveAspects": [
      "Electrician installed without issue",
      "Easy push in install"
    ],
    "topNegativeReasons": [
      "wire labels mislabeled on device (3x)",
      "brightness range not adjustable, too dim at full power (3x)",
      "Either I have a smaller-than-standard electrical box, or this thing is too big",
      "Failed after two years",
      "wire leads instead of screw terminals"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Power Management",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 2,
    "negativeCount": 5,
    "totalReviews": 7,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "poor voltage control causing startup issues",
      "Power spike or draw gets back into dimmer when used with fan/light combo",
      "as soon as load applied dropped to 34v",
      "only dim lights available",
      "power vampire device"
    ],
    "topPositiveAspects": [
      "did not heat up much during 300w test",
      "Very rarely necessary to reset dimmer by air-gapping power"
    ],
    "topNegativeReasons": [
      "hollow sounding and feels cheap (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Light Flickering Control",
    "categoryType": "Performance",
    "mentions": 49,
    "positiveCount": 14,
    "negativeCount": 35,
    "totalReviews": 49,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Causes lights to flicker (2x)",
      "flickers once every 4 or 5 minutes",
      "loads of flickering with remote sockets",
      "Makes other LEDs from same electrical box flicker",
      "Impossible to eliminate flicker on multiple fixtures"
    ],
    "topPositiveAspects": [
      "no flickering (2x)",
      "some lights flicker, some don't",
      "LED flickering prevention",
      "No flickering experienced",
      "does not flicker"
    ],
    "topNegativeReasons": [
      "Flimsy and imprecise flicker control"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Included Components",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 2,
    "negativeCount": 5,
    "totalReviews": 7,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "missing screws for wall plate",
      "missing all screws in used unit",
      "small hole on lower left front with no LED light",
      "recessed potentiometer on bottom that does nothing",
      "missing wire connectors"
    ],
    "topPositiveAspects": [
      "wire nuts, screws, and screwless faceplate included",
      "comes complete with wall plates"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Audio Feedback",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 2,
    "negativeCount": 5,
    "totalReviews": 7,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Produces loud clicking sounds during operation",
      "noisy operation",
      "loud noticeable click from inside when turned on",
      "Louder click than normal switches"
    ],
    "topPositiveAspects": [
      "quiet_operation",
      "soft click on/off"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "fancy futuristic look",
      "soft click on/off"
    ]
  },
  {
    "category": "Multi Way Configuration",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 6,
    "negativeCount": 14,
    "totalReviews": 20,
    "satisfactionRate": 30.0,
    "negativeRate": 70.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Defective for 3-way switching",
      "standard switch must be toggled twice below 75% brightness",
      "remote switch hit and miss",
      "did not work properly from beginning",
      "never able to get switch to function as designed"
    ],
    "topPositiveAspects": [
      "Works for 3-way switching",
      "works perfectly once wiring sorted",
      "functions well for most things",
      "wiring was tricky but works perfectly after setup",
      "functions for either single pole or 3 way"
    ],
    "topNegativeReasons": [
      "only one traveler wire terminal instead of standard two (2x)",
      "stops responding to Alexa for days every few weeks (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Device Reliability",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 3,
    "negativeCount": 7,
    "totalReviews": 10,
    "satisfactionRate": 30.0,
    "negativeRate": 70.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "only one out of two worked",
      "one doesn't work at all",
      "need to reset dongle after couple months",
      "didn't work right out the box",
      "completely unreliable"
    ],
    "topPositiveAspects": [
      "works well (2x)"
    ],
    "topNegativeReasons": [
      "connection is not reliable"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Product Durability",
    "categoryType": "Performance",
    "mentions": 33,
    "positiveCount": 10,
    "negativeCount": 23,
    "totalReviews": 33,
    "satisfactionRate": 30.3,
    "negativeRate": 69.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "keep knocking it off the wall",
      "worked for only 3 hours before failure",
      "worked for few minutes then stopped",
      "died within one day of use",
      "blue light went out after 3 weeks"
    ],
    "topPositiveAspects": [
      "made to last (2x)",
      "continues to work after blue light failure",
      "Long-term durability",
      "More reliable than rotary type",
      "no plastic track parts to wear or break"
    ],
    "topNegativeReasons": [
      "magnet holding to housing not as good as v1",
      "design puts features before usability",
      "blue LED indicator light on button",
      "complete failure to work",
      "Physically coming apart"
    ],
    "topPositiveReasons": [
      "feels well built and solid",
      "well made construction",
      "works with dimmable LED bulbs"
    ]
  },
  {
    "category": "Light Quality Issues",
    "categoryType": "Performance",
    "mentions": 56,
    "positiveCount": 18,
    "negativeCount": 38,
    "totalReviews": 56,
    "satisfactionRate": 32.1,
    "negativeRate": 67.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "flickers at high and low settings",
      "flicker at one location on slider near top",
      "flickered and buzzed at all dimming levels",
      "causes flickering with LED lights",
      "causes lights to flicker even at full power"
    ],
    "topPositiveAspects": [
      "no flicker (3x)",
      "no flicker when dimming",
      "fixed LED ghosting",
      "no flickering at all",
      "eliminates flickering"
    ],
    "topNegativeReasons": [
      "breaks under normal use",
      "not durable"
    ],
    "topPositiveReasons": [
      "regulator inside, little blue tab on the left",
      "feels as good as expensive name-brand dimmers",
      "smooth continuous touch dimming"
    ]
  },
  {
    "category": "Button Operation",
    "categoryType": "Physical",
    "mentions": 15,
    "positiveCount": 5,
    "negativeCount": 10,
    "totalReviews": 15,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Click of the switch is more masculine than it should be",
      "cheaply made buttons",
      "Tactile feedback quality",
      "difficult to press in just the right way",
      "feels like thin plastic with almost no resistance"
    ],
    "topPositiveAspects": [
      "Click feel is awesome, snappy and responsive",
      "good feel buttons",
      "robust ON/OFF switch with positive snap",
      "easy to use switch",
      "smooth switch push operation"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Structural Mounting Features",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 2,
    "negativeCount": 4,
    "totalReviews": 6,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "three tabs on the right side were broken off",
      "mounting plate wing breakaways don't break away",
      "little_tab_breaks_during_installation",
      "large_ears_stick_out_on_both_sides_preventing_installation_of_two_next_to_each_other"
    ],
    "topPositiveAspects": [
      "has removable side wings for multi-gang installation",
      "has breakable side tab for mounting flexibility"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color Matching and Consistency",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "color is off - not true white, looks almost gray",
      "yellowish tone compared to other white products"
    ],
    "topPositiveAspects": [
      "color matches adjacent traditional switches perfectly"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Battery Performance",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Battery does not last more than few weeks",
      "Quickly dying battery even after changing"
    ],
    "topPositiveAspects": [
      "Battery lasts a long time"
    ],
    "topNegativeReasons": [
      "Stopped working consistently after few weeks (2x)"
    ],
    "topPositiveReasons": [
      "Battery powered"
    ]
  },
  {
    "category": "Face Plates",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Small size plate that doesn't cover original switch area",
      "Switch plate cover with poor plastic finish"
    ],
    "topPositiveAspects": [
      "Includes faceplate"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "WiFi Connectivity",
    "categoryType": "Performance",
    "mentions": 38,
    "positiveCount": 13,
    "negativeCount": 25,
    "totalReviews": 38,
    "satisfactionRate": 34.2,
    "negativeRate": 65.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "can't connect to WiFi out of the box",
      "switches drop network connection everyday",
      "connectivity issues with some switches unable to connect to WiFi",
      "Goes offline and cannot reconnect",
      "WiFi password change causes permanent connection issues"
    ],
    "topPositiveAspects": [
      "stays connected to wifi and reconnects automatically when network reboots",
      "connectivity was usually great with occasional need to reconnect to WiFi",
      "Works with 2.4 GHz WiFi only",
      "connects to house Wi-Fi perfectly",
      "connects well to WiFi"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Noise Level",
    "categoryType": "Performance",
    "mentions": 17,
    "positiveCount": 6,
    "negativeCount": 11,
    "totalReviews": 17,
    "satisfactionRate": 35.3,
    "negativeRate": 64.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Dimmable CFL bulbs are a bit noisy",
      "buzzing sound",
      "humming noise with ceiling fan",
      "Makes a lot of noise",
      "Buzzing noise"
    ],
    "topPositiveAspects": [
      "No buzz with LEDs or incandescents",
      "No buzzing",
      "no buzz",
      "operates silently without humming",
      "very stable and quiet"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Cover Plates and Faceplates",
    "categoryType": "Physical",
    "mentions": 17,
    "positiveCount": 6,
    "negativeCount": 11,
    "totalReviews": 17,
    "satisfactionRate": 35.3,
    "negativeRate": 64.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Special cover plate required",
      "Does not come with wall plate as advertised",
      "some plates won't work well in multigang box",
      "Missing cover/faceplate",
      "no_plate_included"
    ],
    "topPositiveAspects": [
      "uses standard old-fashioned switch plate",
      "face can be easily changed by snapping together",
      "Comes with finishing plate/screwless faceplate",
      "can use standard deco wall plate",
      "interchangeable faceplates"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Long Term Durability",
    "categoryType": "Performance",
    "mentions": 36,
    "positiveCount": 13,
    "negativeCount": 23,
    "totalReviews": 36,
    "satisfactionRate": 36.1,
    "negativeRate": 63.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stopped working after 1 year (2x)",
      "failed after six months",
      "stopped responding after 3 months",
      "worked for months then blinks nonstop",
      "Durability over time"
    ],
    "topPositiveAspects": [
      "lasted 5 years",
      "Durable construction",
      "trouble free",
      "rock solid system",
      "works for 3 years"
    ],
    "topNegativeReasons": [
      "Hardware quality is very poor with cheap plastic materials"
    ],
    "topPositiveReasons": [
      "well-constructed"
    ]
  },
  {
    "category": "LED Bulb Compatibility",
    "categoryType": "Performance",
    "mentions": 36,
    "positiveCount": 13,
    "negativeCount": 23,
    "totalReviews": 36,
    "satisfactionRate": 36.1,
    "negativeRate": 63.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "buzzes loudly and doesn't adjust properly with LEDs",
      "LED compatibility is iffy",
      "Does not work with many dimmable bulbs",
      "not compatible with LED lighting",
      "Does not work with most dimmable LED bulbs - needs trailing edge dimmer"
    ],
    "topPositiveAspects": [
      "works with CFL and LED lights",
      "installation compatibility with LED lights",
      "work with LED lights",
      "work great with new can built in ceiling lights",
      "Works with various bulb types"
    ],
    "topNegativeReasons": [
      "Leaks tiny bit of electricity when powered off",
      "analog design"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Fit",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 3,
    "negativeCount": 5,
    "totalReviews": 8,
    "satisfactionRate": 37.5,
    "negativeRate": 62.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Plastic tabs that hold switch are too thick causing plate not to sit flush",
      "Not flush like other model",
      "does not sit flush to wall",
      "not flush and tight fit",
      "knob will not sit flush with backplates"
    ],
    "topPositiveAspects": [
      "Switch sits flush to wall",
      "fits with standard switch cover"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi Switch Coordination",
    "categoryType": "Performance",
    "mentions": 13,
    "positiveCount": 5,
    "negativeCount": 8,
    "totalReviews": 13,
    "satisfactionRate": 38.5,
    "negativeRate": 61.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not 3 way compatible as described",
      "doesn't respond to 3-way dumb switch",
      "3-way installation doesn't function",
      "cannot support multi switch set up for hallways",
      "does not function well as 3-way dimmer"
    ],
    "topPositiveAspects": [
      "Works well in 3-way setup",
      "3-way functionality is great",
      "works with dumb switch as real 3-way",
      "can be wired with standard non-smart switches",
      "works fine in 3-way setup"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Configuration",
    "categoryType": "Physical",
    "mentions": 20,
    "positiveCount": 8,
    "negativeCount": 12,
    "totalReviews": 20,
    "satisfactionRate": 40.0,
    "negativeRate": 60.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "load wires same color without proper marking",
      "stiff and hard to route wires",
      "heat shrink wrapper that is bulky",
      "disconnected wire upon arrival",
      "Hot wire connection difficulty"
    ],
    "topPositiveAspects": [
      "4-wire configuration",
      "Requires neutral wire",
      "wire terminations",
      "plug in wire connections",
      "Labeled wires for easy installation"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Cord Design",
    "categoryType": "Physical",
    "mentions": 10,
    "positiveCount": 4,
    "negativeCount": 6,
    "totalReviews": 10,
    "satisfactionRate": 40.0,
    "negativeRate": 60.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cord length could be longer",
      "two cords required (lamp cord to outlet, dimmer cord back)",
      "very thin cables",
      "short cord length",
      "exposed wire end"
    ],
    "topPositiveAspects": [
      "cord is quite long",
      "extra long cord on controller",
      "touch pad on cord for flexible placement",
      "heavy cord leads"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Control Precision",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 2,
    "negativeCount": 3,
    "totalReviews": 5,
    "satisfactionRate": 40.0,
    "negativeRate": 60.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "percentages not accurate with incorrect light output",
      "could not change intensity high or low",
      "work OK but very sensitive with not much play in the dim"
    ],
    "topPositiveAspects": [
      "easy tap operation for on/off",
      "touch control for dimming adjustment"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Sound During Operation",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 2,
    "negativeCount": 3,
    "totalReviews": 5,
    "satisfactionRate": 40.0,
    "negativeRate": 60.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Audible click when switched",
      "produces noise during operation"
    ],
    "topPositiveAspects": [
      "Silent rocker operation",
      "Quiet operation"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Mounting and Installation",
    "categoryType": "Physical",
    "mentions": 10,
    "positiveCount": 4,
    "negativeCount": 6,
    "totalReviews": 10,
    "satisfactionRate": 40.0,
    "negativeRate": 60.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not physically mount well with other switches creating ugly or unsafe mount",
      "doesn't stay attached to switch toggle well",
      "easy to pull off wall",
      "trouble with screws to secure to light switch",
      "finicky mounting with tape that floats away from wall"
    ],
    "topPositiveAspects": [
      "screw system is reassuring",
      "provides slight wiggle room for adjustment",
      "pops on over regular light switch",
      "clamps over light switch non-destructively"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Noise Levels",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 2,
    "negativeCount": 3,
    "totalReviews": 5,
    "satisfactionRate": 40.0,
    "negativeRate": 60.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "buzzes, especially loud when brightness is lower",
      "audible click surprisingly loud",
      "makes high pitch buzzing noise"
    ],
    "topPositiveAspects": [
      "no noise",
      "zero hum or noise when dimming LEDs"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Quality",
    "categoryType": "Performance",
    "mentions": 57,
    "positiveCount": 23,
    "negativeCount": 34,
    "totalReviews": 57,
    "satisfactionRate": 40.4,
    "negativeRate": 59.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "no dimming at all, only bright to off",
      "reduces brightness by half with erratic slider",
      "not much difference between lowest and highest settings",
      "uneven brightness control",
      "The dimmer would not stay at full brightness"
    ],
    "topPositiveAspects": [
      "smooth dimming with no flickering",
      "works perfectly for dimming",
      "smooth dimming without flickering",
      "dimming range capability",
      "dimmer_worked_normally_despite_switch_reversal"
    ],
    "topNegativeReasons": [
      "slider movement smoothness (2x)",
      "dimming range capability (2x)",
      "doesn't work - light remains same when pushed up or pulled down"
    ],
    "topPositiveReasons": [
      "slider control mechanism (3x)",
      "smooth dimming without flickering (3x)",
      "adjustment_lever_on_body_for_minimum_dim_setting",
      "no_buzzing_with_recessed_lights",
      "slider works smoothly"
    ]
  },
  {
    "category": "Wireless Connectivity",
    "categoryType": "Performance",
    "mentions": 44,
    "positiveCount": 18,
    "negativeCount": 26,
    "totalReviews": 44,
    "satisfactionRate": 40.9,
    "negativeRate": 59.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Lost Wi-Fi connection",
      "Had trouble registering to simultaneous dual band wifi until using dedicated 2.4GHz band",
      "go offline regularly requiring power cycle",
      "zigbee will fail and not pair again",
      "disconnects frequently"
    ],
    "topPositiveAspects": [
      "paired flawlessly",
      "connected easily",
      "flawless wireless connection",
      "Wi-Fi connectivity stability",
      "Reliable Wi-Fi connection"
    ],
    "topNegativeReasons": [
      "requires ground wire",
      "unresponsive"
    ],
    "topPositiveReasons": [
      "dongle bridges protocol to wifi",
      "works without neutral wire",
      "works pretty good"
    ]
  },
  {
    "category": "Light Control Performance",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 5,
    "negativeCount": 7,
    "totalReviews": 12,
    "satisfactionRate": 41.7,
    "negativeRate": 58.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "LED lights fade up and down with no on-off control",
      "Light turns off when fan is on",
      "Light pops on randomly",
      "does not make lights as bright as wanted"
    ],
    "topPositiveAspects": [
      "Light dimming works properly",
      "Maintains brightness level",
      "maintains same brightness level when turned on/off"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Memory and Recovery Features",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 8,
    "negativeCount": 11,
    "totalReviews": 19,
    "satisfactionRate": 42.1,
    "negativeRate": 57.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "doesn't remember last dimming setting",
      "won't remember last dimmer setting, only switches back to full setting",
      "hub takes upwards of 5 minutes to come back online after power loss",
      "dimming setting retention",
      "defaults to ON after power outage"
    ],
    "topPositiveAspects": [
      "customizable favorite setting",
      "normally OFF if main power switch is turned OFF and ON again",
      "Stores last brightness setting",
      "Recovery state options available",
      "Remembers light level after power cycle"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "good feel buttons",
      "rock solid system"
    ]
  },
  {
    "category": "LED Flickering Issues",
    "categoryType": "Performance",
    "mentions": 99,
    "positiveCount": 42,
    "negativeCount": 57,
    "totalReviews": 99,
    "satisfactionRate": 42.4,
    "negativeRate": 57.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "bulbs flash 5 times at full brightness when dimmed",
      "lights flicker when dimming",
      "Light flickering issues",
      "flickering at intermediate intensity",
      "blinks light when turned down"
    ],
    "topPositiveAspects": [
      "no flickering with LED lights (2x)",
      "flicker free LED dimming",
      "Light flickering issues",
      "works great with LED lights without flickering",
      "solves LED light flickering issue"
    ],
    "topNegativeReasons": [
      "Dimmer slider with adjustable positions",
      "Slider with halfway position",
      "Dims only about 30% of light output"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Material Quality",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 3,
    "negativeCount": 4,
    "totalReviews": 7,
    "satisfactionRate": 42.9,
    "negativeRate": 57.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cheap plastic construction",
      "Made with plastic components"
    ],
    "topPositiveAspects": [
      "good quality material",
      "Made with metal components"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Indicator Lighting",
    "categoryType": "Physical",
    "mentions": 14,
    "positiveCount": 6,
    "negativeCount": 8,
    "totalReviews": 14,
    "satisfactionRate": 42.9,
    "negativeRate": 57.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "blue LED indicator light on button",
      "Light on switch symbol should be brighter when light is on",
      "Status light won't turn on when switch is dead",
      "Green indicator light stays on even when switch stops working",
      "red indicator light removed from newer versions"
    ],
    "topPositiveAspects": [
      "blue LED indicator light on button",
      "Small LED indicators for each control"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Fan Control Performance",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 3,
    "negativeCount": 4,
    "totalReviews": 7,
    "satisfactionRate": 42.9,
    "negativeRate": 57.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Fan works occasionally",
      "Fan ramps up to high and won't shut off",
      "Fan makes whining noise and barely spins",
      "fan made weird noise when controlled"
    ],
    "topPositiveAspects": [
      "Fan speed control works well",
      "Power on/off without changing speed"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Internal Electronics and Components",
    "categoryType": "Physical",
    "mentions": 30,
    "positiveCount": 13,
    "negativeCount": 17,
    "totalReviews": 30,
    "satisfactionRate": 43.3,
    "negativeRate": 56.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Defective units with faulty remote switch functionality",
      "Interior guts of the switch",
      "Internal plastic switch that snaps into assembly",
      "Button component",
      "ESP8266 boards"
    ],
    "topPositiveAspects": [
      "has built in relay",
      "PCB looks decent",
      "well made circuit board",
      "ESP32-C3 chip inside",
      "aluminum cover on back to cool power electronics"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Button Interface",
    "categoryType": "Physical",
    "mentions": 16,
    "positiveCount": 7,
    "negativeCount": 9,
    "totalReviews": 16,
    "satisfactionRate": 43.8,
    "negativeRate": 56.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "button layout changed between v1 and v2 versions",
      "top button for on/off",
      "bottom button changed from off to hue function",
      "physical buttons",
      "paddle button"
    ],
    "topPositiveAspects": [
      "one button for on/off",
      "center rocker for dimming",
      "button for scene selection",
      "big buttons",
      "Side controls for fan speed and dimmer"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Mechanism Feel",
    "categoryType": "Physical",
    "mentions": 9,
    "positiveCount": 4,
    "negativeCount": 5,
    "totalReviews": 9,
    "satisfactionRate": 44.4,
    "negativeRate": 55.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "has no resistance when pushed and feels mushy",
      "doesn't snap like a normal switch to on/off",
      "can be easily put in between on/off position",
      "rocker switch component that can break",
      "lacks crisp tactile click when switching"
    ],
    "topPositiveAspects": [
      "has good positive feel when switching on and off",
      "huge rocker paddle for on/off control",
      "high quality feel of physical switch and dimmer",
      "gentle tap operation for on/off and brightness control"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 123,
    "positiveCount": 55,
    "negativeCount": 68,
    "totalReviews": 123,
    "satisfactionRate": 44.7,
    "negativeRate": 55.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Either I have a smaller-than-standard electrical box, or this thing is too big",
      "Large size leaves no room for wire connections",
      "deeper than regular switches",
      "housing too large to fit two in one box",
      "tiny remote size"
    ],
    "topPositiveAspects": [
      "Perfect fit with standard boxes and gang plates",
      "smallest form factor",
      "Compact size for installation",
      "standard size",
      "small enough to fit into standard single-gang box"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "User Interface Experience",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 9,
    "negativeCount": 11,
    "totalReviews": 20,
    "satisfactionRate": 45.0,
    "negativeRate": 55.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "programming is tremendous pain",
      "horrible connectivity and app, disconnects/goes offline",
      "confusing multiple software apps",
      "Cync app is not great",
      "app is terrible"
    ],
    "topPositiveAspects": [
      "app is intuitive with decent customization including fade speed control and LED indicator settings",
      "app seems better than Kasa app",
      "app detected dimmer via Bluetooth and added without issue",
      "app has additional controls like max/min bulb intensity",
      "software allows for lot of adjustment and customization"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wire Configuration",
    "categoryType": "Physical",
    "mentions": 20,
    "positiveCount": 9,
    "negativeCount": 11,
    "totalReviews": 20,
    "satisfactionRate": 45.0,
    "negativeRate": 55.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "wire color coding keeps changing",
      "markings on back of unit are nonsensical",
      "Pre-stripped traveler wire not capped",
      "pre-attached wires instead of using existing wall cables",
      "wires are stripped and worn"
    ],
    "topPositiveAspects": [
      "Different colors wire for HOT",
      "gray black and purple wiring harness pigtail",
      "violet and purple (0-10 vdc) wires",
      "0-10v (5 wires to the fixture) design",
      "six wires including two red, black, blue, white, and green"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Structural Durability",
    "categoryType": "Physical",
    "mentions": 11,
    "positiveCount": 5,
    "negativeCount": 6,
    "totalReviews": 11,
    "satisfactionRate": 45.5,
    "negativeRate": 54.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "All plastic plate that attaches to the box",
      "Cheaply built and can easily break",
      "Extremely low quality construction",
      "Poor quality construction",
      "Component quality and materials"
    ],
    "topPositiveAspects": [
      "Switch seems sturdy",
      "High quality construction",
      "well-constructed",
      "feels solid and not cheap",
      "well constructed"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Device Pairing",
    "categoryType": "Performance",
    "mentions": 22,
    "positiveCount": 10,
    "negativeCount": 12,
    "totalReviews": 22,
    "satisfactionRate": 45.5,
    "negativeRate": 54.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Setup and pairing process",
      "pairing implementation is horribly botched",
      "takes multiple tries to add device to app",
      "some switches almost impossible to pair with Apple HomeKit",
      "Hard to set up with Gosund app"
    ],
    "topPositiveAspects": [
      "programming takes less than 1 minute",
      "Setup and pairing process",
      "Easy pairing with apps",
      "doesn't need any setup since it communicates with other switch",
      "easy to set up and pair"
    ],
    "topNegativeReasons": [
      "no flashing lights in setup mode",
      "frequent connectivity issues"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Reliability",
    "categoryType": "Performance",
    "mentions": 99,
    "positiveCount": 46,
    "negativeCount": 53,
    "totalReviews": 99,
    "satisfactionRate": 46.5,
    "negativeRate": 53.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "switches have been dying (2x)",
      "have to hit buttons a few times before they work when first entering room",
      "doesn't work on outlet",
      "Works well initially then fails",
      "turn on randomly at full or partial brightness"
    ],
    "topPositiveAspects": [
      "works perfectly (3x)",
      "works every time (2x)",
      "always works",
      "never have operational problems",
      "consistent performance"
    ],
    "topNegativeReasons": [
      "seem cheaply made",
      "doesn't dim far enough"
    ],
    "topPositiveReasons": [
      "slim profile",
      "always works"
    ]
  },
  {
    "category": "App Performance",
    "categoryType": "Performance",
    "mentions": 15,
    "positiveCount": 7,
    "negativeCount": 8,
    "totalReviews": 15,
    "satisfactionRate": 46.7,
    "negativeRate": 53.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "app can be glitchy at times",
      "unstable apps",
      "settings for dimmers reset themselves",
      "missing fade rate on schedule feature",
      "white version has fade rate feature but black version doesn't"
    ],
    "topPositiveAspects": [
      "easy download of phone app",
      "provides additional customization options",
      "automatically found the switches",
      "grouping ability is top notch",
      "can control other switches remotely from one switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Noise Issues",
    "categoryType": "Performance",
    "mentions": 23,
    "positiveCount": 11,
    "negativeCount": 12,
    "totalReviews": 23,
    "satisfactionRate": 47.8,
    "negativeRate": 52.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Extremely loud buzzing noise",
      "Constant buzzing/humming sound",
      "Buzzing noise occurred after about a month",
      "still buzzes",
      "buzz when switched on"
    ],
    "topPositiveAspects": [
      "silent operation without flicker",
      "No buzzing with LED bulbs",
      "No buzzing at any speed",
      "No noise from switch",
      "Easy slide and quiet"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Cleanability",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "gets very dirty during operation"
    ],
    "topPositiveAspects": [
      "Easy to clean"
    ],
    "topNegativeReasons": [
      "gets very dirty when pulling up and down"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Wireless Range",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "30 feet max distance from hub",
      "hub has extremely poor range"
    ],
    "topPositiveAspects": [
      "works through wall",
      "works 30 yards distance"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Power Capacity",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 3,
    "negativeCount": 3,
    "totalReviews": 6,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "could not handle 480 watts despite 600w rating",
      "cannot handle even 50 watts of LED bulbs",
      "will shut off at max brightness due to overloading"
    ],
    "topPositiveAspects": [
      "supports up to 300w for LED lighting",
      "works_flawlessly_with_high_wattage",
      "600 watts rated"
    ],
    "topNegativeReasons": [
      "heat up with high wattage loads"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Packaging Condition",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "heavily used switch with missing cover, screws, wiring nuts, and instructions"
    ],
    "topPositiveAspects": [
      "packaged well in mint condition"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Device Connectivity",
    "categoryType": "Performance",
    "mentions": 28,
    "positiveCount": 14,
    "negativeCount": 14,
    "totalReviews": 28,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "QR code tells to contact homeowner, gives up after extended time",
      "disconnected and will not reconnect",
      "kept disconnecting from Alexa in Matter mode",
      "forgets programming, loses connectivity",
      "disconnect from internet and randomly turn lights on and off"
    ],
    "topPositiveAspects": [
      "bluetooth operation is flawless",
      "gained Matter support through simple app-based firmware update",
      "added to Apple HomeKit on first try",
      "works great with Apple HomeKit",
      "connected perfectly to Alexa and Google Nest app"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Usability",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "dimming is more difficult than other dimmers"
    ],
    "topPositiveAspects": [
      "easy to operate and toggle on/off"
    ],
    "topNegativeReasons": [
      "very tiny dimmer slider (2x)",
      "switch only works when dimmer is on low (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Operation Mechanism",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 3,
    "negativeCount": 3,
    "totalReviews": 6,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "lacks satisfying click action compared to traditional switches",
      "rocker loose, didn't click on/off",
      "bottom of rocker sticks out past dimmer slider"
    ],
    "topPositiveAspects": [
      "not a rocker switch, it's a simple pressure switch with no up for on, down for off",
      "paddle switch design",
      "detachable to select type of lights used"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi Switch Configuration",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 3,
    "negativeCount": 3,
    "totalReviews": 6,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "master control programmed to work with mechanical switch causing companion switch issues",
      "doesn't work for 3-way dimming",
      "cannot increase light past first switch setting"
    ],
    "topPositiveAspects": [
      "can be used in 4 way configuration up to 9 locations",
      "ability to dim from 10 locations with additional secondary switches",
      "maintains setting in 3-way applications"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wire Connection Mechanisms",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 3,
    "negativeCount": 3,
    "totalReviews": 6,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "wires not secure in plug-in connectors",
      "only one traveler wire terminal instead of standard two"
    ],
    "topPositiveAspects": [
      "easy push in design to eliminate wire nuts",
      "premium wire screw downs",
      "wire clamps already open and ready"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Safety Certifications",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 3,
    "negativeCount": 3,
    "totalReviews": 6,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "ETL listed but not UL listed",
      "zero safety certifications (no UL, ETL, CE)",
      "only FCC certification"
    ],
    "topPositiveAspects": [
      "UL Listed dimmer switches",
      "UL tested/certified",
      "independently tested for safety by nationally recognized testing laboratory"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Connections",
    "categoryType": "Physical",
    "mentions": 14,
    "positiveCount": 7,
    "negativeCount": 7,
    "totalReviews": 14,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "terminals inset into body with too much gap",
      "push-in connection hole too small for 12-gauge wire",
      "can't get wires on screw",
      "Clamps that fail to open to accept wires",
      "Stripped screws on neutral wire connection"
    ],
    "topPositiveAspects": [
      "Three or four wire capability for 3-way or single pole install",
      "Includes plastic tie off caps",
      "connections did not look like they had ever been connected",
      "Two straight conductors can be inserted with internal clamp",
      "Line and load terminals take 2 conductors, ground terminal takes one"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Sound Level",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "buzzing/humming noise from lights"
    ],
    "topPositiveAspects": [
      "silent operation",
      "no humming noise"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Long Term Reliability",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Stopped working consistently after few weeks",
      "Stopped working entirely after few months"
    ],
    "topPositiveAspects": [
      "Works the same after a year",
      "worked great for a year"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Connectivity",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 10,
    "negativeCount": 10,
    "totalReviews": 20,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not recognized in app and cannot be programmed",
      "doesn't work with Alexa",
      "keeps dropping off Alexa connection",
      "only works with Alexa, not other apps",
      "doesn't support 5G despite claims"
    ],
    "topPositiveAspects": [
      "no problems with connection to base or app",
      "integrates well with Alexa",
      "easy integration with Google Assistant",
      "pairs immediately and works great",
      "works with 2.4GHz reliably"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Speed",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 3,
    "negativeCount": 3,
    "totalReviews": 6,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "slow dimming with no instant on/off",
      "fades slowly to off with no option to change",
      "default dimming speed very slow and unchangeable"
    ],
    "topPositiveAspects": [
      "fast dimming speed",
      "no delay during adjustments"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Operation",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Switch paddle with poor plastic finish that scratches easily"
    ],
    "topPositiveAspects": [
      "Switch paddle component"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color Quality",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Very bright white color compared to existing switches",
      "Has yellow tint instead of pure white"
    ],
    "topPositiveAspects": [
      "Nice bright white color",
      "Bright white color as expected"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "User Interface Responsiveness",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Noticeably slower with delayed responsiveness"
    ],
    "topPositiveAspects": [
      "Very responsive operation"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Sound",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "little noisy with clicking"
    ],
    "topPositiveAspects": [
      "no humming or flickering"
    ],
    "topNegativeReasons": [
      "loud clicks"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "LED Indicator Design",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cannot change LED color unlike other brands"
    ],
    "topPositiveAspects": [
      "soft LED indicator light not too bright or distracting"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Noise Generation",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 6,
    "negativeCount": 6,
    "totalReviews": 12,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Produces loud electrical whine with lamps",
      "makes click when turning on and off even through Alexa",
      "makes persistent clicking noise when secondary switch turned off",
      "produces very slight buzz in mid dimming range",
      "mild buzzing sound from couple of dimmers"
    ],
    "topPositiveAspects": [
      "no buzzing with proper LED bulbs",
      "Switch is silent",
      "does not whine when at full or dimmed",
      "does not emit hardly any noise",
      "silent"
    ],
    "topNegativeReasons": [
      "Produces loud electrical whine with lamps",
      "causes rapid blinking at 2/3 position"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Device Durability",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 5,
    "negativeCount": 5,
    "totalReviews": 10,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not durable (2x)",
      "fails after a while",
      "durability and lifespan"
    ],
    "topPositiveAspects": [
      "durable",
      "won't crap out fast",
      "durability and lifespan"
    ],
    "topNegativeReasons": [
      "breaks under normal use",
      "not durable"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Wall Plate Design and Aesthetics",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "dual front panel is annoying"
    ],
    "topPositiveAspects": [
      "good dimmer plates"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Initial Setup Experience",
    "categoryType": "Performance",
    "mentions": 14,
    "positiveCount": 7,
    "negativeCount": 7,
    "totalReviews": 14,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "setup a bit tricky, needed to try twice to add to existing Smart Home network",
      "total pain to setup",
      "very challenging to set up using Matter or HomeKit",
      "difficult setup",
      "little tricky setting up but worth it"
    ],
    "topPositiveAspects": [
      "setup was simple and straightforward",
      "set up was simple and quick",
      "easy set up",
      "entire setup completed in 30 minutes"
    ],
    "topNegativeReasons": [
      "no flashing lights in setup mode",
      "frequent connectivity issues"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Mobile App Experience",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "app says switches not connected",
      "switches will not respond to app commands"
    ],
    "topPositiveAspects": [
      "Leviton app always works well",
      "My Leviton app made setup easy"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 37,
    "positiveCount": 19,
    "negativeCount": 18,
    "totalReviews": 37,
    "satisfactionRate": 51.4,
    "negativeRate": 48.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cheaply made construction",
      "weighs close to nothing and feels cheap",
      "Poor manufacturing quality",
      "Overheating and burning plastic smell",
      "Loose and rattly parts in non-smart version"
    ],
    "topPositiveAspects": [
      "Higher construction quality than non-smart version",
      "build quality seems fine",
      "well-made construction",
      "durable casing",
      "well made construction"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Dimensions",
    "categoryType": "Physical",
    "mentions": 27,
    "positiveCount": 14,
    "negativeCount": 13,
    "totalReviews": 27,
    "satisfactionRate": 51.9,
    "negativeRate": 48.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "shape not compatible between versions",
      "Deeper than regular switch",
      "Switch base is really big making connections difficult to fit in electrical box",
      "Electronics box is oversized",
      "Deep profile requiring deep electrical boxes"
    ],
    "topPositiveAspects": [
      "optimal depth for wall box",
      "fits existing box easily",
      "compact and small form factor",
      "narrower than most other switches",
      "smaller than other brands"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Range Performance",
    "categoryType": "Performance",
    "mentions": 23,
    "positiveCount": 12,
    "negativeCount": 11,
    "totalReviews": 23,
    "satisfactionRate": 52.2,
    "negativeRate": 47.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "trouble keeping same low level setting",
      "light levels not stable with fine oscillation",
      "Doesn't dim up or down, stays dim",
      "Low setting not as low as desired but reasonable",
      "Narrow dimming range"
    ],
    "topPositiveAspects": [
      "dims lights from bright to completely off",
      "brings lights from bright down to whisper",
      "transitions smoothly to different brightnesses",
      "dims lights smoothly",
      "manual dimming functionality"
    ],
    "topNegativeReasons": [
      "Slider catches and has spots that don't adjust smoothly",
      "Jumpy dimming transition"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Packaging and Documentation",
    "categoryType": "Physical",
    "mentions": 44,
    "positiveCount": 23,
    "negativeCount": 21,
    "totalReviews": 44,
    "satisfactionRate": 52.3,
    "negativeRate": 47.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "included wall plate may not be to taste",
      "programming instructions not intuitive",
      "no English instructions provided",
      "missing instructions",
      "instructions leave out critical network connection steps"
    ],
    "topPositiveAspects": [
      "Come with matching plate covers and hardware",
      "Include plates which is cost-effective",
      "quality hardware",
      "good quality",
      "cover plate included"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Control Performance",
    "categoryType": "Performance",
    "mentions": 176,
    "positiveCount": 92,
    "negativeCount": 84,
    "totalReviews": 176,
    "satisfactionRate": 52.3,
    "negativeRate": 47.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "poor at lower levels of light and never takes intensity to zero",
      "flickers when turned up until partially turned up",
      "doesn't dim over full range, stops when lights still bright",
      "hums when dimmed to 50% or less",
      "Dimming failure"
    ],
    "topPositiveAspects": [
      "provides smooth dimming action",
      "provides fine dimming control",
      "takes lights down to lowest possible bit of light",
      "Proper dimming functionality",
      "Smooth fade effect"
    ],
    "topNegativeReasons": [
      "Dimmer slide moves too easily without resistance",
      "Broke after little over 1 year",
      "cheap_internal_parts",
      "all_fail_in_less_than_a_year_some_in_two_weeks",
      "Physical +/- buttons for dimming"
    ],
    "topPositiveReasons": [
      "Slider for dimming control (2x)",
      "Quick installation process (2x)",
      "acts as both switch and dimmer",
      "main unit and satellite unit configuration",
      "easy to integrate with Kasa app"
    ]
  },
  {
    "category": "Heat Generation",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 10,
    "negativeCount": 9,
    "totalReviews": 19,
    "satisfactionRate": 52.6,
    "negativeRate": 47.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "getting very hot",
      "metal housing got really hot",
      "got even hotter almost couldn't touch it",
      "heat up with high wattage loads",
      "overheating with lesser wattage dimmer"
    ],
    "topPositiveAspects": [
      "generates almost no heat",
      "not running as hot but warm",
      "mild warmth as expected",
      "handles 900w well in terms of dissipating heat",
      "no longer have overheating problem"
    ],
    "topNegativeReasons": [
      "make a low buzzing sound (2x)"
    ],
    "topPositiveReasons": [
      "1000w capacity (2x)",
      "handles 900w well in terms of dissipating heat (2x)",
      "works as advertised"
    ]
  },
  {
    "category": "Button and Control Interface",
    "categoryType": "Physical",
    "mentions": 53,
    "positiveCount": 28,
    "negativeCount": 25,
    "totalReviews": 53,
    "satisfactionRate": 52.8,
    "negativeRate": 47.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "touch sensor may fail or not respond",
      "flimsy, wobbly, squishy button gear",
      "4 buttons with only brightest or lowest settings option",
      "separate on and off button",
      "button feels loose and cheap"
    ],
    "topPositiveAspects": [
      "touch-sensitive control panel",
      "Capacitive touch strip for dimming",
      "Clicky button feel",
      "punch on-off design rather than turn clockwise to turn on design",
      "has push button on/off"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color and Finish Options",
    "categoryType": "Physical",
    "mentions": 17,
    "positiveCount": 9,
    "negativeCount": 8,
    "totalReviews": 17,
    "satisfactionRate": 52.9,
    "negativeRate": 47.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Only comes in white color",
      "color is ivory, not white",
      "only white not other colors described",
      "no light almond covers in package",
      "brighter white color than other switches"
    ],
    "topPositiveAspects": [
      "color exactly as in pictures",
      "good match for other wall switches",
      "comes with different colors to choose from",
      "liked the different colors you could use depending on your needs",
      "comes in ivory color"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Power Specifications",
    "categoryType": "Physical",
    "mentions": 13,
    "positiveCount": 7,
    "negativeCount": 6,
    "totalReviews": 13,
    "satisfactionRate": 53.8,
    "negativeRate": 46.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "only rated to 6amps",
      "only good for 2 lamps or bulbs with less than 15amp",
      "250W rated capacity",
      "UL rated 250W but performance verified 150W",
      "Labeled 450W but buzzes over 200W LED"
    ],
    "topPositiveAspects": [
      "400 watt capacity",
      "1000w capacity",
      "600w capacity",
      "higher wattage capacity compared to standard 650w",
      "high wattage capacity"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color and Finish",
    "categoryType": "Physical",
    "mentions": 11,
    "positiveCount": 6,
    "negativeCount": 5,
    "totalReviews": 11,
    "satisfactionRate": 54.5,
    "negativeRate": 45.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "received white instead of light almond",
      "very bright white plastic color that doesn't match common white",
      "Ivory color is actually almond and almond is really ivory",
      "Neither ivory nor almond colors match existing switches",
      "Brass finish has look and texture of brass spray paint"
    ],
    "topPositiveAspects": [
      "perfect color match",
      "light almond model color accurate",
      "midnight satin (matte) black finish",
      "available in many different colors",
      "Gold detail"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Consistency",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 5,
    "negativeCount": 4,
    "totalReviews": 9,
    "satisfactionRate": 55.6,
    "negativeRate": 44.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "sometimes does not turn on lights",
      "stopped working completely",
      "does not always turn on when switched",
      "works inconsistently"
    ],
    "topPositiveAspects": [
      "works as expected",
      "switches work fine",
      "worked as it should",
      "works properly"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Bulb Type Compatibility",
    "categoryType": "Performance",
    "mentions": 41,
    "positiveCount": 23,
    "negativeCount": 18,
    "totalReviews": 41,
    "satisfactionRate": 56.1,
    "negativeRate": 43.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "poor LED compatibility",
      "doesn't work with non-dimmable LED bulbs",
      "Compatibility with LED bulbs",
      "restricts to single type bulb",
      "does not work with LED bulbs"
    ],
    "topPositiveAspects": [
      "works well with LED lighting (2x)",
      "works with LED bulbs (2x)",
      "Compatibility with LED bulbs",
      "works with some LEDs",
      "works perfect with GE LED lightbulbs"
    ],
    "topNegativeReasons": [
      "fan switch side has 3 specific speeds",
      "non-dimmable switch was automatically on"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Compatibility",
    "categoryType": "Physical",
    "mentions": 16,
    "positiveCount": 9,
    "negativeCount": 7,
    "totalReviews": 16,
    "satisfactionRate": 56.2,
    "negativeRate": 43.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Cannot gang 2 side by side, not to U.S.A. standards",
      "switch plate smaller than standard",
      "sits higher than switch leaving it recessed",
      "Thick build causing installation issues with multi-switch outlets",
      "Bulky build not fitting small junction boxes"
    ],
    "topPositiveAspects": [
      "fits in standard switch plate",
      "fits under normal switch cover",
      "fits in single-gang box with standard toggle switch",
      "fits in existing switch boxes without space issues",
      "fits in normal switch plate"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Magnetic Mounting",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 4,
    "negativeCount": 3,
    "totalReviews": 7,
    "satisfactionRate": 57.1,
    "negativeRate": 42.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "magnet holding to housing not as good as v1",
      "Magnet is terrible",
      "No magnets, only adhesive strips"
    ],
    "topPositiveAspects": [
      "magnets hold remote to mount with perfect strength",
      "Magnetizes to wall holder",
      "magnetic attachment capability"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Noise",
    "categoryType": "Performance",
    "mentions": 56,
    "positiveCount": 32,
    "negativeCount": 24,
    "totalReviews": 56,
    "satisfactionRate": 57.1,
    "negativeRate": 42.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "buzzing at brightness below 100%",
      "switches hum",
      "lights still buzz when turned on",
      "Causes LEDs to buzz in 3k to 1k hertz range when dimmed",
      "makes dimmable LED bulbs hum when below 50%"
    ],
    "topPositiveAspects": [
      "no buzzing (2x)",
      "no buzzing with LED bulbs",
      "Works with 14 LED pot lights with no hum",
      "buzzing goes away when dimmer is at low",
      "eliminates_LED_buzzing_in_reverse_phase_mode"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Knob Characteristics",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 4,
    "negativeCount": 3,
    "totalReviews": 7,
    "satisfactionRate": 57.1,
    "negativeRate": 42.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "knob sticks out from wall plate more than old dimmer",
      "knob does not snap on or lock in and can fall off easily",
      "knob post is D shaped instead of circular"
    ],
    "topPositiveAspects": [
      "comes with multiple color knobs"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Features",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 7,
    "negativeCount": 5,
    "totalReviews": 12,
    "satisfactionRate": 58.3,
    "negativeRate": 41.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "App functionality and control",
      "programming capability"
    ],
    "topPositiveAspects": [
      "App functionality and control",
      "programming capability",
      "Can change Z-Wave parameters per dimmer",
      "easy to use the app"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Slider Mechanisms",
    "categoryType": "Physical",
    "mentions": 48,
    "positiveCount": 28,
    "negativeCount": 20,
    "totalReviews": 48,
    "satisfactionRate": 58.3,
    "negativeRate": 41.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "slider has small travel length",
      "gets very dirty when pulling up and down",
      "slide is too short",
      "slider with loose tension at bottom 2-3mm",
      "slider made from flimsy plastic"
    ],
    "topPositiveAspects": [
      "dimmer slide",
      "dimmer slide stays put at setting",
      "slider doesn't move to full on when light is turned off",
      "dimmable slide component",
      "very smooth"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Basic Operation",
    "categoryType": "Performance",
    "mentions": 17,
    "positiveCount": 10,
    "negativeCount": 7,
    "totalReviews": 17,
    "satisfactionRate": 58.8,
    "negativeRate": 41.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "brightness changes on its own if you accidentally bump anything",
      "often have to stop and push it again when walking by and hitting it",
      "did not work for one light switch where old dimmer was working fine",
      "unusable",
      "didn't turn on LED lights"
    ],
    "topPositiveAspects": [
      "works in turning lights on/off",
      "works as described and as expected",
      "controls device properly",
      "dimmer switch can also be on/off"
    ],
    "topNegativeReasons": [
      "difficult to press in just the right way",
      "feels like thin plastic with almost no resistance",
      "frayed wires attached from previous owner"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Hardware Components",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 3,
    "negativeCount": 2,
    "totalReviews": 5,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "missing parts/screws"
    ],
    "topPositiveAspects": [
      "hidden screws",
      "Supplied wire nuts and screws",
      "Pull tab cutoff at bottom"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Click and Button Feel",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 3,
    "negativeCount": 2,
    "totalReviews": 5,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "loosey-goosey click, not solid",
      "switches are noisy"
    ],
    "topPositiveAspects": [
      "crisp actuation and quality feel",
      "nice click sound",
      "good push feel"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Home Connectivity",
    "categoryType": "Performance",
    "mentions": 15,
    "positiveCount": 9,
    "negativeCount": 6,
    "totalReviews": 15,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "z-wave hub connection",
      "SmartThings hub connection",
      "home automation system sync",
      "backward compatibility",
      "buggy experience with Home Assistant"
    ],
    "topPositiveAspects": [
      "z-wave hub connection",
      "SmartThings hub connection",
      "connection consistency",
      "z-wave 700 series performance",
      "network repeater functionality"
    ],
    "topNegativeReasons": [
      "blue tooth reset button",
      "ramp up/down times"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "System Integration",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 12,
    "negativeCount": 8,
    "totalReviews": 20,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Requires hub for smart features",
      "Unable to pair with hue bulbs",
      "Flakey when connected through zwave - improperly reports status",
      "No HomeKit support despite logo on product image"
    ],
    "topPositiveAspects": [
      "Hub makes it more reliable",
      "Does not require internet access",
      "Synced easily",
      "No issues connecting",
      "Easy to pair"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Button Responsiveness",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 3,
    "negativeCount": 2,
    "totalReviews": 5,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Sometimes need to double press button",
      "Frequent latency from button click to action"
    ],
    "topPositiveAspects": [
      "Very responsive",
      "Flawless responsiveness",
      "Fast button response"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Memory Function",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 3,
    "negativeCount": 2,
    "totalReviews": 5,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "defaults to OFF when power is applied",
      "lights will not come back on when used with timer"
    ],
    "topPositiveAspects": [
      "remembers last dimmer setting",
      "remembers last dimming state"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Build Durability",
    "categoryType": "Physical",
    "mentions": 10,
    "positiveCount": 6,
    "negativeCount": 4,
    "totalReviews": 10,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Switch cracks/breaks after 8 months to a year",
      "Switches broke in half",
      "Switch broke mechanically from normal use",
      "Broke after 3 months with minimal use"
    ],
    "topPositiveAspects": [
      "Light construction but with some durability",
      "Very well made construction",
      "feels like it will last many flips",
      "durable with six children banging on them",
      "on par with other comparable switches in the market"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Performance",
    "categoryType": "Performance",
    "mentions": 122,
    "positiveCount": 75,
    "negativeCount": 47,
    "totalReviews": 122,
    "satisfactionRate": 61.5,
    "negativeRate": 38.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "limited dimming range",
      "no dimming functionality",
      "dimmer function does not work while light works",
      "Barely dimmed with flickering on low",
      "Does not dim at all"
    ],
    "topPositiveAspects": [
      "works great as dimmer (2x)",
      "Smooth dimming operation (2x)",
      "dims perfectly",
      "dims nicely",
      "being able to easily dim lights is massive plus"
    ],
    "topNegativeReasons": [
      "has turning knob with zero resistance (2x)",
      "doesn't dim at all, just turns on (2x)",
      "Light flickers when set to dim"
    ],
    "topPositiveReasons": [
      "smooth and responsive slider (14x)",
      "supports multiple bulb types (14x)",
      "touch-activated button interface",
      "requires training and time to get used to sensitivity",
      "Has thumbwheel dial under cover for adjustment"
    ]
  },
  {
    "category": "Switch Mechanism",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 5,
    "negativeCount": 3,
    "totalReviews": 8,
    "satisfactionRate": 62.5,
    "negativeRate": 37.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Pivot of the rocker broke on one side",
      "Toggle switch fell apart when tried to use",
      "plastic flip switch falls out"
    ],
    "topPositiveAspects": [
      "Rocker switches for on/off",
      "positive click when turned fully off",
      "switch operation feel",
      "smooth mechanism",
      "makes slight audible click when switched"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi-Way Switching",
    "categoryType": "Performance",
    "mentions": 16,
    "positiveCount": 10,
    "negativeCount": 6,
    "totalReviews": 16,
    "satisfactionRate": 62.5,
    "negativeRate": 37.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not compatible with standard 3-way configuration",
      "status changed but switch did not turn on lights in multi-way setup",
      "will not work with existing 3-way configuration",
      "did not work as expected in three way configuration",
      "doesn't work exactly like a 3-way switch"
    ],
    "topPositiveAspects": [
      "good job handling 3-way 4-way configurations with add-on",
      "switches do sync with each other",
      "can control the dimmer from either switch",
      "Works perfectly as 3-way switch without requiring accessory device",
      "works fine in single pole setup"
    ],
    "topNegativeReasons": [
      "only 2 wires on received switches"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Rotary Controls",
    "categoryType": "Physical",
    "mentions": 24,
    "positiveCount": 15,
    "negativeCount": 9,
    "totalReviews": 24,
    "satisfactionRate": 62.5,
    "negativeRate": 37.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Large knob sticking out far",
      "No push function at all, rotate to turn on and off",
      "has turning knob with zero resistance",
      "dial is very large and bulky",
      "whole dimmer wheel assembly is oversized"
    ],
    "topPositiveAspects": [
      "White, clean appearance",
      "Twist on, NOT a push knob",
      "Comes with three interchangeable knob colors (white, light almond, ivory)",
      "Rotary knob covers the hole in the plate beautifully",
      "Turn to off functionality"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Dimensions and Fit",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 5,
    "negativeCount": 3,
    "totalReviews": 8,
    "satisfactionRate": 62.5,
    "negativeRate": 37.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "switch covers are smaller than hole in the wall",
      "takes up a lot more space in wall box than standard switches",
      "width and depth are considerable"
    ],
    "topPositiveAspects": [
      "not too deep, fit in electrical box",
      "compacted switch body made it easier to stuff back into crowded switch box",
      "short depth less than an inch behind mounting plate",
      "fits right into normal switch spot",
      "standard size"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 105,
    "positiveCount": 66,
    "negativeCount": 39,
    "totalReviews": 105,
    "satisfactionRate": 62.9,
    "negativeRate": 37.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "poor overall construction quality (2x)",
      "cheap construction (2x)",
      "feel cheap (2x)",
      "feels cheaply made with brittle plastic",
      "interchangeable color face plates make unit flimsy"
    ],
    "topPositiveAspects": [
      "well made (2x)",
      "well built (2x)",
      "product material of plastics and metal is very good",
      "good material good quality",
      "feels well built and solid"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 165,
    "positiveCount": 106,
    "negativeCount": 59,
    "totalReviews": 165,
    "satisfactionRate": 64.2,
    "negativeRate": 35.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Has wire connections instead of preferred screw clamp terminals",
      "Wire labeling and connection points",
      "pigtails that take up a lot of room",
      "permanently installed lead wires, not lugs",
      "wires substantially thinner than 14AWG Romex"
    ],
    "topPositiveAspects": [
      "requires neutral wire (5x)",
      "does not require neutral wire (2x)",
      "Requires neutral wire (2x)",
      "no neutral wire required (2x)",
      "back-connect screw-type connections"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Build Quality and Construction",
    "categoryType": "Physical",
    "mentions": 14,
    "positiveCount": 9,
    "negativeCount": 5,
    "totalReviews": 14,
    "satisfactionRate": 64.3,
    "negativeRate": 35.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Flimsy construction compared to older switches",
      "Loose connectors",
      "Left-handed screws not extending far enough",
      "Low quality switch",
      "Cheaply made"
    ],
    "topPositiveAspects": [
      "high build quality",
      "Solid construction",
      "Well made",
      "Seems sturdier than previous switch",
      "well made"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Response Performance",
    "categoryType": "Performance",
    "mentions": 17,
    "positiveCount": 11,
    "negativeCount": 6,
    "totalReviews": 17,
    "satisfactionRate": 64.7,
    "negativeRate": 35.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "two-second delay for LED lights to come on",
      "Switch became unresponsive physically",
      "Unresponsive to both paddle presses or Z-Wave commands until power reset",
      "Slow response with definite lag compared to GE switches",
      "dimming feature slow to respond"
    ],
    "topPositiveAspects": [
      "instant to brighten or dim after initial delay",
      "Quick and responsive operation",
      "Responsive app control",
      "almost no lag when using app, remotes, and voice control",
      "lights turn on/off instantly whether at home or remotely"
    ],
    "topNegativeReasons": [
      "Pushing the paddles only works every other time or requires pushing really hard"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Control",
    "categoryType": "Performance",
    "mentions": 17,
    "positiveCount": 11,
    "negativeCount": 6,
    "totalReviews": 17,
    "satisfactionRate": 64.7,
    "negativeRate": 35.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cannot change dimmer brightness from accessory switch",
      "single tap turns on to main dimmer level",
      "no manual dimming by holding switch",
      "missing dimmer functionality compared to Pico remote",
      "one unit did not dim except periodically with long delay"
    ],
    "topPositiveAspects": [
      "works great (2x)",
      "double tap goes to full brightness",
      "dims",
      "works perfectly with dimmable LEDs"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Range and Precision",
    "categoryType": "Performance",
    "mentions": 75,
    "positiveCount": 49,
    "negativeCount": 26,
    "totalReviews": 75,
    "satisfactionRate": 65.3,
    "negativeRate": 34.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "requires softest touches and several tries for intermediate settings",
      "dimmer adjustment doesn't do good job of dimming",
      "doesn't get as bright as it should",
      "glitches at highest brightness",
      "bulbs dimly light when dimmer turned all way up"
    ],
    "topPositiveAspects": [
      "trim dimmer activation range",
      "works perfectly with dimming",
      "brightness range from 30-40% to 100%",
      "dims to very low level around 10%",
      "smooth and customizable turning on and off with no flickering"
    ],
    "topNegativeReasons": [
      "sensitive in the middle range",
      "doesn't work with LED 300 watts despite 450W rating"
    ],
    "topPositiveReasons": [
      "Calibration button for adjusting dimming range (2x)",
      "adjustment wheel on top right",
      "separate on/off switch",
      "no flickering at all",
      "trimmer potentiometer on PCB for dimming range adjustment"
    ]
  },
  {
    "category": "Dimming Range Control",
    "categoryType": "Performance",
    "mentions": 118,
    "positiveCount": 78,
    "negativeCount": 40,
    "totalReviews": 118,
    "satisfactionRate": 66.1,
    "negativeRate": 33.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Not 1-100 percent dimming as advertised - LED light still insanely bright at lowest setting",
      "Dimmest setting not particularly dim - still quite bright",
      "Don't dim lights far enough down",
      "minimum dim level not low enough",
      "Dimming range and control"
    ],
    "topPositiveAspects": [
      "smooth dimming without flickering (2x)",
      "Allows dimming to 6% which is excellent",
      "Very adjustable - can turn brightness up or down by as little as 1%",
      "Full range of dimming capability",
      "Excellent dimming regulation"
    ],
    "topNegativeReasons": [
      "slider with loose at bottom to tight at top feel (2x)",
      "rocker switch broke in 3 months (2x)",
      "Touch sensor interface for dimming control",
      "Durability over time",
      "sensitive in the middle range"
    ],
    "topPositiveReasons": [
      "blue adjustment range toggle (5x)",
      "Touch sensor interface for dimming control (4x)",
      "Durability over time (4x)",
      "Capacitive touch strip for dimming (2x)",
      "Straightforward installation (2x)"
    ]
  },
  {
    "category": "Core Functionality",
    "categoryType": "Performance",
    "mentions": 69,
    "positiveCount": 46,
    "negativeCount": 23,
    "totalReviews": 69,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not work at all (2x)",
      "complete failure to work",
      "cannot shut off, stays on all the time",
      "stops working properly under higher current loads",
      "only blue circle light works, no dimming or turn off"
    ],
    "topPositiveAspects": [
      "works well (7x)",
      "works very well (3x)",
      "works well and as expected (2x)",
      "works beautifully for intended purpose",
      "works great with proper electrical knowledge"
    ],
    "topNegativeReasons": [
      "blue LED indicator light on button (2x)",
      "complete failure to work (2x)",
      "cannot handle 2 amps or higher current",
      "worked for only 3 hours before failure",
      "came obviously used with burn mark and wire nut marks"
    ],
    "topPositiveReasons": [
      "4-wire configuration",
      "heavy duty switch",
      "easy install",
      "meets expected build standards",
      "works on LEDs and other bulbs"
    ]
  },
  {
    "category": "Adjustment Wheels",
    "categoryType": "Physical",
    "mentions": 12,
    "positiveCount": 8,
    "negativeCount": 4,
    "totalReviews": 12,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "adjustment wheel doesn't change much",
      "calibration adjustment requires switch plate removal",
      "missing dimming range lever despite being advertised",
      "internal dimmer adjustment immovable and factory set"
    ],
    "topPositiveAspects": [
      "small adjustment wheel for calibration",
      "Low limit adjustment wheel allows setting lowest level for custom range",
      "Second adjustment helps with dimming range",
      "Fine tuning adjustment on top of brightness adjustment",
      "Adjustable minimum brightness setting"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Capacity",
    "categoryType": "Performance",
    "mentions": 15,
    "positiveCount": 10,
    "negativeCount": 5,
    "totalReviews": 15,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "can't handle three light bulbs",
      "could handle more watts",
      "cannot handle 1000w at all",
      "can't handle high inrush current from halogen lamps",
      "Buzzing noise over 200W LED load"
    ],
    "topPositiveAspects": [
      "can handle high LED watts",
      "450w max rating effective for 380w LED lighting",
      "healthy load handling capacity 430W incandescent, 250W LED/CFL",
      "works great with 1000 watts",
      "works great powering 1000 watt waterfall pump"
    ],
    "topNegativeReasons": [
      "Labeled 450W but buzzes over 200W LED",
      "Switch works opposite if wired incorrectly"
    ],
    "topPositiveReasons": [
      "works as advertised"
    ]
  },
  {
    "category": "Included Components and Accessories",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 2,
    "negativeCount": 1,
    "totalReviews": 3,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Did not come with plate screws"
    ],
    "topPositiveAspects": [
      "Comes with dimmer plate",
      "Comes with all wireless connectors needed"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Internal Components",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 4,
    "negativeCount": 2,
    "totalReviews": 6,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "plastic toggle and slider is thin",
      "missing part internally"
    ],
    "topPositiveAspects": [
      "has switch underneath face plate to change INC to LED",
      "switch had four small screws that allowed access to internal parts",
      "adjustable setting on internal face",
      "little plastic clip at bottom"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Customization Options",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 6,
    "negativeCount": 3,
    "totalReviews": 9,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Lacks advanced options like regular switches",
      "Cannot trim the light",
      "can't turn off dimming indicator"
    ],
    "topPositiveAspects": [
      "so many functions and you can program it in so many ways",
      "Extremely customizable with many configuration options",
      "Astounding number of parameters to configure",
      "easy to change the color",
      "can adjust maximum light setting and dim to percentage"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Specialized Features",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 2,
    "negativeCount": 1,
    "totalReviews": 3,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Flimsy and imprecise flicker control"
    ],
    "topPositiveAspects": [
      "Adjustable wheel for configuration",
      "Adjustment dial functionality"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Tactile Feedback",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 4,
    "negativeCount": 2,
    "totalReviews": 6,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "clicks",
      "pronounced click when snapping into position between off and on"
    ],
    "topPositiveAspects": [
      "crisp and satisfying tactile feel",
      "Has tactile and positive switch operation",
      "definite click sound for OFF setting",
      "Positive click feel"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Customer Support Quality",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 2,
    "negativeCount": 1,
    "totalReviews": 3,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Unable to reach support, emails ignored, calls not returned"
    ],
    "topPositiveAspects": [
      "Great support with timely responses",
      "Fantastic customer service with custom wiring diagrams"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Switch Quality",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 2,
    "negativeCount": 1,
    "totalReviews": 3,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "moves easily when bumped or slightly touched"
    ],
    "topPositiveAspects": [
      "operates smoothly and feels solid",
      "smooth and crisp operation"
    ],
    "topNegativeReasons": [
      "has turning knob with zero resistance",
      "doesn't dim at all, just turns on"
    ],
    "topPositiveReasons": [
      "feels solid and high quality"
    ]
  },
  {
    "category": "Physical Fit",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 4,
    "negativeCount": 2,
    "totalReviews": 6,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Does not work with US junction boxes",
      "Will not work in United States"
    ],
    "topPositiveAspects": [
      "Fits in crowded/limited space junction box"
    ],
    "topNegativeReasons": [
      "European build design incompatible with US junction boxes (2x)",
      "Does not work with US junction boxes (2x)"
    ],
    "topPositiveReasons": [
      "Slim/thin profile (4x)",
      "Easy to install (4x)"
    ]
  },
  {
    "category": "Setup Instructions",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 13,
    "negativeCount": 6,
    "totalReviews": 19,
    "satisfactionRate": 68.4,
    "negativeRate": 31.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "installation_directions_lacking_color_codes",
      "clear installation instructions",
      "instructions are inaccurate",
      "instructions aren't great",
      "instructions are lacking detail"
    ],
    "topPositiveAspects": [
      "clear and easy to use instructions",
      "instruction quality",
      "Really clear instructions for various setups",
      "Great piece of documentation/instruction",
      "Very good instructions"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "QR code for installation video (2x)"
    ]
  },
  {
    "category": "Faceplate and Cover Components",
    "categoryType": "Physical",
    "mentions": 38,
    "positiveCount": 26,
    "negativeCount": 12,
    "totalReviews": 38,
    "satisfactionRate": 68.4,
    "negativeRate": 31.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "visible 2-piece design",
      "cover comes off easily",
      "face plates slightly flimsy",
      "trim plate may be narrow for older homes",
      "Forced to use ugly oversized plate"
    ],
    "topPositiveAspects": [
      "screwless wall plate design",
      "comes with wall plate included",
      "snap-on design without visible screws",
      "works well for single gang box but may not suit multi-gang boxes",
      "Base plate slightly larger than V1"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Slider Controls",
    "categoryType": "Physical",
    "mentions": 35,
    "positiveCount": 24,
    "negativeCount": 11,
    "totalReviews": 35,
    "satisfactionRate": 68.6,
    "negativeRate": 31.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stiff slider movement",
      "slider motion feels like grinding",
      "detent has harder slide feel compared to older versions",
      "detent used to have smooth feel in older versions",
      "very tiny dimmer slider"
    ],
    "topPositiveAspects": [
      "smooth and responsive slider",
      "easy to move slide bar",
      "Has thumbwheel dial under cover for adjustment",
      "Has wheel adjustment on inside to help adjust lowest dimmer setting",
      "slider control sits nicely on lamp table"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Specialized Components",
    "categoryType": "Physical",
    "mentions": 16,
    "positiveCount": 11,
    "negativeCount": 5,
    "totalReviews": 16,
    "satisfactionRate": 68.8,
    "negativeRate": 31.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Batteries dead on arrival",
      "pull plug under paddle is longer in new model compared to older ones",
      "Air gap plug under paddle that spontaneously pops out and cannot be reinserted",
      "dimmer installed upside down with high at bottom and low at top",
      "has little metal heat sink fins on the sides"
    ],
    "topPositiveAspects": [
      "Air gap reset feature",
      "Battery powered",
      "IP44 weather resistance rating",
      "better cooling profile than metal fin switches",
      "Protective film on switch paddle"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Hub Connectivity",
    "categoryType": "Performance",
    "mentions": 16,
    "positiveCount": 11,
    "negativeCount": 5,
    "totalReviews": 16,
    "satisfactionRate": 68.8,
    "negativeRate": 31.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "will not connect to SmartThings hub",
      "stopped talking to Z-wave hub",
      "requires factory reset before pairing"
    ],
    "topPositiveAspects": [
      "works great with SmartThings hub",
      "works well with Hubitat",
      "connects to WINK as z-wave device",
      "works well with ADT Z-Wave Hub"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Touch Interface Responsiveness",
    "categoryType": "Performance",
    "mentions": 13,
    "positiveCount": 9,
    "negativeCount": 4,
    "totalReviews": 13,
    "satisfactionRate": 69.2,
    "negativeRate": 30.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "takes practice to get used to touch operation",
      "not as easy to finely control as slider",
      "touch functionality spotty",
      "dimming can be jumpy"
    ],
    "topPositiveAspects": [
      "very responsive to touch",
      "can be turned on by simply touching",
      "Very responsive to touch",
      "touch sensitivity responsive",
      "smooth continuous touch dimming"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "touch-sensitive control panel (2x)",
      "works great every time (2x)"
    ]
  },
  {
    "category": "Switch Actuation Mechanism",
    "categoryType": "Physical",
    "mentions": 79,
    "positiveCount": 55,
    "negativeCount": 24,
    "totalReviews": 79,
    "satisfactionRate": 69.6,
    "negativeRate": 30.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Touch sensor interface for dimming control",
      "Physical button for on/off operation",
      "horizontal toggle can be confusing",
      "both ends are just clicking buttons, not real switching",
      "toggle feels soft with no solid clicking"
    ],
    "topPositiveAspects": [
      "slider control mechanism (2x)",
      "Touch sensor interface for dimming control",
      "Physical button for on/off operation",
      "separate controls for on-off and slide",
      "adjustment wheel on top right"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Functional Reliability",
    "categoryType": "Performance",
    "mentions": 97,
    "positiveCount": 68,
    "negativeCount": 29,
    "totalReviews": 97,
    "satisfactionRate": 70.1,
    "negativeRate": 29.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "defective, does not operate properly",
      "two worked, one did not",
      "flickered off and on same day after installation",
      "light flashes then comes on when motion detected",
      "poor performance"
    ],
    "topPositiveAspects": [
      "does the job (3x)",
      "Rock solid performance (3x)",
      "reliable (3x)",
      "very functional (2x)",
      "easy to use (2x)"
    ],
    "topNegativeReasons": [
      "defective units out of box",
      "intermittent functionality"
    ],
    "topPositiveReasons": [
      "provides visibility in low-light conditions",
      "compatible with various lighting types including dimmable LEDs and halogen bulbs",
      "compact and small",
      "works great for dimming",
      "Rock solid construction"
    ]
  },
  {
    "category": "Electrical Compatibility",
    "categoryType": "Performance",
    "mentions": 64,
    "positiveCount": 45,
    "negativeCount": 19,
    "totalReviews": 64,
    "satisfactionRate": 70.3,
    "negativeRate": 29.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Do not work with Amico lights",
      "not meant for tubular fluorescent bulbs",
      "works marginally better with incandescent than LED",
      "Incompatible with integral LED fixtures",
      "Doesn't work with non-dimmable bulbs"
    ],
    "topPositiveAspects": [
      "Compatible with most bulbs including CFL, incandescent and LED",
      "Made for incandescent bulbs",
      "works well with LED lights and older incandescent bulbs",
      "works great with LEDs",
      "control common Sylvania LEDs quite well with no flickering"
    ],
    "topNegativeReasons": [
      "wire gauge limitations not specified in description",
      "250W rated capacity"
    ],
    "topPositiveReasons": [
      "can handle SPST, 3 Way and 4 way wiring (2x)",
      "red wire used as signal wire between switches"
    ]
  },
  {
    "category": "Dimming Function",
    "categoryType": "Performance",
    "mentions": 108,
    "positiveCount": 76,
    "negativeCount": 32,
    "totalReviews": 108,
    "satisfactionRate": 70.4,
    "negativeRate": 29.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Unable to dim",
      "won't turn on unless dimmer is set high",
      "don't turn on when set to low light position",
      "light doesn't stay same dimness",
      "doesn't turn on when set below 80%"
    ],
    "topPositiveAspects": [
      "dims beautifully",
      "smooth dimming of lights",
      "snappy to turn on the lights and dim",
      "control is smooth and even",
      "work smoothly to dim all fixtures with no flickering"
    ],
    "topNegativeReasons": [
      "Slider jams and cannot be moved",
      "Flicker even when adjusted",
      "adjustment wheel component",
      "does not maintain set position",
      "has short in wiring"
    ],
    "topPositiveReasons": [
      "adjustable setting on internal face (2x)",
      "LED dimming-range adjustment lever",
      "lever style activation with bottom push and touch slider in middle",
      "setup to get connected to app is simple"
    ]
  },
  {
    "category": "Smart Home Integration",
    "categoryType": "Performance",
    "mentions": 76,
    "positiveCount": 54,
    "negativeCount": 22,
    "totalReviews": 76,
    "satisfactionRate": 71.1,
    "negativeRate": 28.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "impossible to sync with hue bridge",
      "switch doesn't install despite following instructions",
      "No smart connectivity",
      "it is hard to get it to connect",
      "even harder when you change the network"
    ],
    "topPositiveAspects": [
      "easy to connect to Philips Hue app",
      "pairs easy and shows up in Hue app and Apple HomeKit",
      "works without bridge by pairing remote close to light",
      "very easy to set up in HUE app and HomeKit",
      "easy to pair and setup"
    ],
    "topNegativeReasons": [
      "burned-out ESP8266 boards"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Build Construction",
    "categoryType": "Physical",
    "mentions": 35,
    "positiveCount": 25,
    "negativeCount": 10,
    "totalReviews": 35,
    "satisfactionRate": 71.4,
    "negativeRate": 28.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Poor build quality with gaps developing",
      "Feels very low quality",
      "Cheaply made",
      "Physically coming apart",
      "feels cheap"
    ],
    "topPositiveAspects": [
      "solidly built (2x)",
      "seems well-made",
      "well made and sturdy construction",
      "not flimsy",
      "appears nicely made"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Touch Interface",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 5,
    "negativeCount": 2,
    "totalReviews": 7,
    "satisfactionRate": 71.4,
    "negativeRate": 28.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Touch plate for dimming seems awkward - causes unintended dimming level changes",
      "Physical dimmer feature is hit or miss - sometimes registers touch, sometimes doesn't"
    ],
    "topPositiveAspects": [
      "touch-activated button interface",
      "Can slide finger instead of clicking for dimming",
      "Switch responds well to touch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Slider Functionality",
    "categoryType": "Physical",
    "mentions": 28,
    "positiveCount": 20,
    "negativeCount": 8,
    "totalReviews": 28,
    "satisfactionRate": 71.4,
    "negativeRate": 28.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Sliders stick and are very difficult to move",
      "Slider jams and cannot be moved",
      "Dimmer adjuster is not built well",
      "sensitive in the middle range",
      "not uniform in brightness application"
    ],
    "topPositiveAspects": [
      "Smooth slider operation (2x)",
      "Slider is smooth",
      "Broader slide",
      "Dimmer Slider is sturdy with no play, very precise",
      "large slider"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Fade Transition Effects",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 5,
    "negativeCount": 2,
    "totalReviews": 7,
    "satisfactionRate": 71.4,
    "negativeRate": 28.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "no fade on/fade off",
      "reduced light when shutting off"
    ],
    "topPositiveAspects": [
      "soft ramp to on and soft ramp to off",
      "nice fade out at turn-off",
      "ramps down when turning off",
      "delayed shut off is a nice feature"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi-Way Configuration",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 5,
    "negativeCount": 2,
    "totalReviews": 7,
    "satisfactionRate": 71.4,
    "negativeRate": 28.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Turns 3-way circuit into 2-way with bypassed switch",
      "Requires both switches to be Feit brand"
    ],
    "topPositiveAspects": [
      "Works fine in 3-way when properly wired"
    ],
    "topNegativeReasons": [
      "Red/yellow terminal always hot after correct wiring",
      "Defective units with faulty remote switch functionality"
    ],
    "topPositiveReasons": [
      "Requires neutral wire connection",
      "Works with 2.4 GHz WiFi only",
      "Motion sensor integration capability"
    ]
  },
  {
    "category": "Bulb Compatibility",
    "categoryType": "Performance",
    "mentions": 52,
    "positiveCount": 38,
    "negativeCount": 14,
    "totalReviews": 52,
    "satisfactionRate": 73.1,
    "negativeRate": 26.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Dimmer wouldn't dim with existing non-dimmable lightbulbs",
      "does not work with compact fluorescent bulbs",
      "doesn't work well with LED Christmas lights",
      "Was not compatible with my smart bulbs (HUE)",
      "Turn off completely when LED dimmed more than half"
    ],
    "topPositiveAspects": [
      "works with dimmable LED bulbs (3x)",
      "works with incandescent bulbs (3x)",
      "Works with dimmable LED bulbs (2x)",
      "works with LEDs",
      "works with LED Christmas lights"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Size and Fit",
    "categoryType": "Physical",
    "mentions": 15,
    "positiveCount": 11,
    "negativeCount": 4,
    "totalReviews": 15,
    "satisfactionRate": 73.3,
    "negativeRate": 26.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "smaller than existing plate showing drywall gap",
      "takes up a lot of space in the outlet box",
      "large size making it difficult to fit in boxes with many wires",
      "hard to install in regular wall box especially with multiple switches"
    ],
    "topPositiveAspects": [
      "not too bulky, easy to fit into box",
      "doesn't take up much space inside switch box",
      "Shallow depth fitting in one inch box",
      "Low profile design",
      "Compact size fitting well in junction box"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Component Accessories",
    "categoryType": "Physical",
    "mentions": 49,
    "positiveCount": 36,
    "negativeCount": 13,
    "totalReviews": 49,
    "satisfactionRate": 73.5,
    "negativeRate": 26.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "came with no wire nuts",
      "Bulb adapter requirement for generic LED bulbs",
      "no_wire_nuts_included",
      "kit lacks bracket required to mount Pico remote",
      "included cheap wire nuts"
    ],
    "topPositiveAspects": [
      "comes with 3 different color face plates (white, almond, beige)",
      "includes all three color faceplates (white, almond, ivory)",
      "multiple color options with swappable parts in the box",
      "Snap-on cover plate included",
      "Wire nuts provided"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Features Setup",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 14,
    "negativeCount": 5,
    "totalReviews": 19,
    "satisfactionRate": 73.7,
    "negativeRate": 26.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Does not pair properly without hub",
      "wall switches are challenging to pair most of the time",
      "set up is a pain and can be difficult to pair",
      "setup with Kasa App kind of tricky",
      "short window for Google Home setup connection"
    ],
    "topPositiveAspects": [
      "Easy app setup and device detection",
      "Easy pairing with hub",
      "very easy to hook up to smart home",
      "connections very simple and fast",
      "less than a minute to set up in app"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Installation Process",
    "categoryType": "Performance",
    "mentions": 54,
    "positiveCount": 40,
    "negativeCount": 14,
    "totalReviews": 54,
    "satisfactionRate": 74.1,
    "negativeRate": 25.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Installation issues without neutral and ground",
      "Cover fitting problems",
      "extremely difficult to place wire ends under screws",
      "bit complicated to install",
      "couldn't get working with professional help"
    ],
    "topPositiveAspects": [
      "Easy installation process (2x)",
      "easy to install (2x)",
      "Quick installation process",
      "super easy install following directions",
      "installation process is straightforward"
    ],
    "topNegativeReasons": [
      "switch is huge behind the faceplate, like 4 times the size of a simple switch (2x)",
      "not easy to get into the wall box (2x)",
      "Brightness limitation to 85%",
      "Thick build causing installation issues with multi-switch outlets",
      "Frequent WiFi disconnections"
    ],
    "topPositiveReasons": [
      "Standard switch with three screws for 2-way and 3-way use (16x)",
      "No pigtails, uses screw terminals (16x)",
      "Combo backstab and clamp wire connections (16x)",
      "Works in 3-way configuration (16x)",
      "Maintains slider position independent of on/off (16x)"
    ]
  },
  {
    "category": "Visual Design",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 3,
    "negativeCount": 1,
    "totalReviews": 4,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "color doesn't quite match other switches or wall plate"
    ],
    "topPositiveAspects": [
      "push top to turn on, bottom to turn off switch with dimmer adjustment on the right",
      "face plate makes the product look amazing",
      "homekit code on the switch"
    ],
    "topNegativeReasons": [
      "made of very low quality plastic that can be felt by touch"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Manufacturing Origin",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 3,
    "negativeCount": 1,
    "totalReviews": 4,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Chinese garbage, not made in North America"
    ],
    "topPositiveAspects": [
      "made in Mexico",
      "labeled \"Assembled in Mexico\"",
      "labeled \"Made in China\""
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Touchscreen Interface",
    "categoryType": "Physical",
    "mentions": 16,
    "positiveCount": 12,
    "negativeCount": 4,
    "totalReviews": 16,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "screen becomes blank and unresponsive",
      "screen is frozen but still works via app",
      "screen is laggy and unacceptable",
      "touchscreen button stopped working"
    ],
    "topPositiveAspects": [
      "Touch screen interface",
      "display quality is great",
      "display shows time and weather",
      "touchscreen is responsive",
      "display is clear and bright"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Device Compatibility",
    "categoryType": "Performance",
    "mentions": 80,
    "positiveCount": 60,
    "negativeCount": 20,
    "totalReviews": 80,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stopped working with Alexa",
      "did not respond to Alexa",
      "white version gets homekit option but black one doesn't",
      "Not compatible with Smartlife",
      "Three pack not Matter compatible while single pack is"
    ],
    "topPositiveAspects": [
      "works great with Alexa (3x)",
      "easy integration with Google Home (2x)",
      "Compatible with SmartLife app",
      "Alexa integration and voice control",
      "Google Home integration"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Acoustic Performance",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 3,
    "negativeCount": 1,
    "totalReviews": 4,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Dimmers buzz"
    ],
    "topPositiveAspects": [
      "No humming noticed",
      "no_buzzing_with_recessed_lights"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Manufacturing Consistency",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 3,
    "negativeCount": 1,
    "totalReviews": 4,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "absolute garbage"
    ],
    "topPositiveAspects": [
      "quality product from a proven company",
      "very high quality switches",
      "best quality one you will find"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Configuration Options",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 3,
    "negativeCount": 1,
    "totalReviews": 4,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "limited configuration options"
    ],
    "topPositiveAspects": [
      "good configuration options for blue light",
      "supports pre-staging on-level programming",
      "allows_predetermined_brightness_setting"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Indicator Lights",
    "categoryType": "Physical",
    "mentions": 33,
    "positiveCount": 25,
    "negativeCount": 8,
    "totalReviews": 33,
    "satisfactionRate": 75.8,
    "negativeRate": 24.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Light ring indicator",
      "satellite switch lacks dimmer indicator lights",
      "Green LEDs are configurable but can't change the color",
      "LED status light is not as bright on Amazon switches",
      "Tiny white lights"
    ],
    "topPositiveAspects": [
      "small and not intrusive for dark rooms",
      "LED light indicator on dimmer slide",
      "Customizable LED color and brightness",
      "blue LEDs that indicate light level and fade out after adjustments",
      "dim circle icon on switch when light is off for visibility in dark"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "LED Light Compatibility",
    "categoryType": "Performance",
    "mentions": 60,
    "positiveCount": 46,
    "negativeCount": 14,
    "totalReviews": 60,
    "satisfactionRate": 76.7,
    "negativeRate": 23.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "works with LEDs kind of",
      "not compatible with certain bulbs",
      "doesn't work well with certain LED bulbs",
      "works with recessed LEDs but not track lights",
      "doesn't work with LED 300 watts despite 450W rating"
    ],
    "topPositiveAspects": [
      "works great with LED lights (3x)",
      "works with LED lights (2x)",
      "works perfectly with multiple LEDs where other switches failed",
      "compatible with HALO HLB6 recessed canless lights",
      "works with LED under counter lighting"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "Calibration button for adjusting dimming range (3x)"
    ]
  },
  {
    "category": "Physical Installation Fit",
    "categoryType": "Performance",
    "mentions": 13,
    "positiveCount": 10,
    "negativeCount": 3,
    "totalReviews": 13,
    "satisfactionRate": 76.9,
    "negativeRate": 23.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "fits but barely with tight space",
      "faceplate won't fit in double gang boxes requiring loosening other switches",
      "need extra deep box or it won't work"
    ],
    "topPositiveAspects": [
      "fits in existing switch box",
      "can be tight in boxes but normal for dimmer switches",
      "fits easily into multiple wall switch box",
      "fit in box nicely",
      "fits better"
    ],
    "topNegativeReasons": [
      "big back section",
      "limited dimming range with 25% minimum",
      "lack slotted mounting adjustments",
      "does not always turn on when switched",
      "extremely deep and wide with heat sinks"
    ],
    "topPositiveReasons": [
      "large size typical of dimmer switches",
      "dims properly",
      "narrower than most other switches",
      "smaller than other brands"
    ]
  },
  {
    "category": "Electrical Performance",
    "categoryType": "Performance",
    "mentions": 26,
    "positiveCount": 20,
    "negativeCount": 6,
    "totalReviews": 26,
    "satisfactionRate": 76.9,
    "negativeRate": 23.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "lights flash full-brightness then cycle",
      "quit working first day",
      "causes flash of light when turning on",
      "audible buzzing but 50% less than other dimmer",
      "voltage drop over 10%"
    ],
    "topPositiveAspects": [
      "no hum/buzzing, no flickering",
      "smooth dimming",
      "no noise",
      "works well",
      "no buzzing and smooth dimming"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "dimmer slide",
      "works well"
    ]
  },
  {
    "category": "Smart Integration",
    "categoryType": "Performance",
    "mentions": 66,
    "positiveCount": 51,
    "negativeCount": 15,
    "totalReviews": 66,
    "satisfactionRate": 77.3,
    "negativeRate": 22.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "None would program to work remotely",
      "No longer works with Alexa as of 2023",
      "only exposes on/off events not tap events",
      "doesn't support double-tap automations",
      "no way to read back state"
    ],
    "topPositiveAspects": [
      "Easy to connect to Alexa",
      "Works well with Google",
      "works with SmartThings Hub",
      "expands Zigbee mesh network",
      "Voice control integration"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 67,
    "positiveCount": 52,
    "negativeCount": 15,
    "totalReviews": 67,
    "satisfactionRate": 77.6,
    "negativeRate": 22.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "blue indicator light",
      "Built-in LEDs are very bright in dark room",
      "LED indicator off setting does not turn off brightness level LEDs",
      "Only shows tiny white LED at brightness setting when off",
      "Light on switch is really bright and irritating in dark room"
    ],
    "topPositiveAspects": [
      "LED makes it easy to find at night/in the dark",
      "blue indicator light",
      "LED indicators on switch",
      "LED light bar illuminates for easy to find switch in darkness",
      "LED light bar shows dimness level set"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Three Way Switch Function",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 7,
    "negativeCount": 2,
    "totalReviews": 9,
    "satisfactionRate": 77.8,
    "negativeRate": 22.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "no longer functions as 3-way",
      "did not function as 3-way"
    ],
    "topPositiveAspects": [
      "works as 3-way",
      "handles_3_way_switch_with_no_issue"
    ],
    "topNegativeReasons": [
      "missing part internally",
      "1 of 9 switches failed after 3 years"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Remote Control Range",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 7,
    "negativeCount": 2,
    "totalReviews": 9,
    "satisfactionRate": 77.8,
    "negativeRate": 22.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "short range",
      "remote fails to connect frequently"
    ],
    "topPositiveAspects": [
      "remote works great",
      "works 20 feet through concrete wall"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "LED Compatibility",
    "categoryType": "Performance",
    "mentions": 64,
    "positiveCount": 50,
    "negativeCount": 14,
    "totalReviews": 64,
    "satisfactionRate": 78.1,
    "negativeRate": 21.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Does not work on dimmable LED bulbs",
      "Didn't work to keep LED bulbs from flickering",
      "Not compatible with high quality wifi color LEDs",
      "Made LED bulbs strobe",
      "Both dimmers flicker with LED bulbs"
    ],
    "topPositiveAspects": [
      "LED technology compatibility with house wiring",
      "works with various LED bulb types",
      "Works well with LED lights",
      "Doesn't cause LED lights to flicker",
      "No flicker in LED lights"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "adjustment_lever_on_body_for_minimum_dim_setting",
      "no_buzzing_with_recessed_lights"
    ]
  },
  {
    "category": "Device Compatibility",
    "categoryType": "Performance",
    "mentions": 87,
    "positiveCount": 68,
    "negativeCount": 19,
    "totalReviews": 87,
    "satisfactionRate": 78.2,
    "negativeRate": 21.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not work with multi-colored LEDs",
      "Compatibility issues with certain fans",
      "LED bulb compatibility issues",
      "may not be perfectly compatible with all dimmable lights",
      "Doesn't work well with certain LED lights"
    ],
    "topPositiveAspects": [
      "works great with dimmable LED lights (2x)",
      "works great with LED bulbs (2x)",
      "works with LED bulbs without flickering",
      "supports multiple bulb types",
      "600 watt rating"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "4-wire configuration",
      "has leakage current through the device even when off to power control logic",
      "fan timer works great",
      "both switches operate from the same supply",
      "timer functions properly"
    ]
  },
  {
    "category": "Installation Process Difficulty",
    "categoryType": "Performance",
    "mentions": 52,
    "positiveCount": 41,
    "negativeCount": 11,
    "totalReviews": 52,
    "satisfactionRate": 78.8,
    "negativeRate": 21.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Slightly difficult to install",
      "Can be pain to align",
      "Not easy to install once doors already in",
      "challenging due to different design than advertised",
      "connecting 3-way toggle was tricky"
    ],
    "topPositiveAspects": [
      "easy to setup (2x)",
      "quick install (2x)",
      "super easy install and set up",
      "very easy to install with thorough instructions",
      "easiest install ever, pretty much plug and play"
    ],
    "topNegativeReasons": [
      "requires special plates (3x)",
      "Slightly larger than regular switch (2x)",
      "About as wide as typical GFI (2x)",
      "does not have wire leads attached",
      "causes flickering all the time with LEDs"
    ],
    "topPositiveReasons": [
      "wiring in the back",
      "works with LED puck lights",
      "has relatively shallow depth",
      "operates efficiently",
      "does not require neutral wire"
    ]
  },
  {
    "category": "Voice Control Integration",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 15,
    "negativeCount": 4,
    "totalReviews": 19,
    "satisfactionRate": 78.9,
    "negativeRate": 21.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Will not dim by voice command - only manually",
      "Does not work with Alexa toggle function",
      "not working with Alexa in Mexico",
      "Alexa was unable to connect"
    ],
    "topPositiveAspects": [
      "Voice control works well",
      "Works well with Alexa",
      "works with Hey Google",
      "responds to voice commands for on/off and brightness",
      "compatible with Alexa"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Basic Functionality",
    "categoryType": "Performance",
    "mentions": 177,
    "positiveCount": 140,
    "negativeCount": 37,
    "totalReviews": 177,
    "satisfactionRate": 79.1,
    "negativeRate": 20.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "No longer switches",
      "On off switch does not work",
      "Did not work when installed",
      "Does not work",
      "Don't work well"
    ],
    "topPositiveAspects": [
      "works great (11x)",
      "works perfectly (9x)",
      "works as expected (6x)",
      "Works great (5x)",
      "works like a charm (4x)"
    ],
    "topNegativeReasons": [
      "Physically coming apart",
      "Barely dimmed with flickering on low",
      "one of the packs was used",
      "looked like they'd been shorted out",
      "absolute garbage"
    ],
    "topPositiveReasons": [
      "toggle functionality"
    ]
  },
  {
    "category": "Overall Reliability",
    "categoryType": "Performance",
    "mentions": 184,
    "positiveCount": 146,
    "negativeCount": 38,
    "totalReviews": 184,
    "satisfactionRate": 79.3,
    "negativeRate": 20.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "unreliable (2x)",
      "quality has gone down",
      "Failed to work completely",
      "Inconsistent light control",
      "Killed LED bulbs"
    ],
    "topPositiveAspects": [
      "works as advertised (11x)",
      "works great (5x)",
      "works flawlessly (3x)",
      "works reliably (2x)",
      "accurate"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "mounting and finishing screws are high-quality",
      "switch feels sturdy and well-made",
      "Metal plate instead of plastic for mounting",
      "Multiple dimming levels available",
      "Screw terminals instead of wire leads"
    ]
  },
  {
    "category": "Specialized Controls",
    "categoryType": "Physical",
    "mentions": 49,
    "positiveCount": 39,
    "negativeCount": 10,
    "totalReviews": 49,
    "satisfactionRate": 79.6,
    "negativeRate": 20.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "don't like having to remove cover to dial up or down",
      "adjustment wheel does nothing",
      "small wheel to set lowest setting does not appear to do much",
      "round dial on right side with no luck adjusting",
      "dimmer range control not visible or accessible after installing cover plate"
    ],
    "topPositiveAspects": [
      "Adjustment wheel at the bottom for lowest dim level",
      "dial to determine level of brightness is nice",
      "dial allows setting minimum brightness",
      "adjustable control on the side",
      "only one adjustment for minimum brightness"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color Options",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 4,
    "negativeCount": 1,
    "totalReviews": 5,
    "satisfactionRate": 80.0,
    "negativeRate": 20.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "only comes with white switch cover/faceplate"
    ],
    "topPositiveAspects": [
      "three different faceplate color options",
      "Home Depot packaging includes color change plates"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Build Quality",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 16,
    "negativeCount": 4,
    "totalReviews": 20,
    "satisfactionRate": 80.0,
    "negativeRate": 20.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "absolute crap quality",
      "flimsy but okay if used gently",
      "slide bar is delicate",
      "Switch comes apart easily"
    ],
    "topPositiveAspects": [
      "good quality",
      "great quality product",
      "build quality",
      "exceptional quality",
      "quality switch"
    ],
    "topNegativeReasons": [
      "set screw was fused and would not tighten",
      "face plates slightly flimsy",
      "plastic toggle and slider is thin",
      "lights flash full-brightness then cycle",
      "slide bar"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Adjustment Controls",
    "categoryType": "Physical",
    "mentions": 10,
    "positiveCount": 8,
    "negativeCount": 2,
    "totalReviews": 10,
    "satisfactionRate": 80.0,
    "negativeRate": 20.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "adjustment wheel component"
    ],
    "topPositiveAspects": [
      "little dial inside the cover to set minimum brightness",
      "dimmer adjustment is on the bottom",
      "adjustment wheel component",
      "blue adjustment range toggle"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Switch Operation",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 4,
    "negativeCount": 1,
    "totalReviews": 5,
    "satisfactionRate": 80.0,
    "negativeRate": 20.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stops_sliding_and_breaks_under_pressure"
    ],
    "topPositiveAspects": [
      "smooth_slide_control",
      "unique_but_intuitive_operation",
      "soft_ramp_up_time_eliminates_flickering",
      "very_smooth_operation"
    ],
    "topNegativeReasons": [
      "breaks_with_minimal_pressure",
      "susceptible_to_pressure_from_wires_or_materials"
    ],
    "topPositiveReasons": [
      "smooth_operation",
      "has_capacitor_for_current_dampening"
    ]
  },
  {
    "category": "User Experience",
    "categoryType": "Performance",
    "mentions": 26,
    "positiveCount": 21,
    "negativeCount": 5,
    "totalReviews": 26,
    "satisfactionRate": 80.8,
    "negativeRate": 19.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "have to look at it and aim for button in dark room",
      "requires moving slider to maximum to turn on",
      "Must press hard to turn on"
    ],
    "topPositiveAspects": [
      "easy to use (4x)",
      "exceeded expectations",
      "works fine",
      "requires training and time to get used to sensitivity",
      "one touch on/off and dimming by holding finger"
    ],
    "topNegativeReasons": [
      "top button for on/off"
    ],
    "topPositiveReasons": [
      "touch-activated button interface (3x)",
      "requires training and time to get used to sensitivity (3x)",
      "touch pad on cord for flexible placement",
      "works great"
    ]
  },
  {
    "category": "Electrical Wiring",
    "categoryType": "Physical",
    "mentions": 37,
    "positiveCount": 30,
    "negativeCount": 7,
    "totalReviews": 37,
    "satisfactionRate": 81.1,
    "negativeRate": 18.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "requires both hot and neutral wires",
      "requires ground wire",
      "Pre-wired braided copper pigtails",
      "Five wire nuts and leads to make fit in box",
      "Wire leads instead of wire terminals"
    ],
    "topPositiveAspects": [
      "works without neutral wire (2x)",
      "can handle SPST, 3 Way and 4 way wiring",
      "has colored wires for matching",
      "No neutral wire requirement",
      "Two-wire compatibility"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Adjustability Features",
    "categoryType": "Performance",
    "mentions": 30,
    "positiveCount": 25,
    "negativeCount": 5,
    "totalReviews": 30,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "brightness control setup not well described",
      "dimming limiting feature doesn't work",
      "wheel adjustments have little impact on performance",
      "have to adjust dimmer to turn on",
      "require constant adjustment"
    ],
    "topPositiveAspects": [
      "adjustable minimum level trimmer",
      "fully adjustable",
      "Adjustable minimum brightness level",
      "has adjustable minimum brightness threshold",
      "Can lock minimum brightness at 100%"
    ],
    "topNegativeReasons": [
      "adjustment wheel component",
      "does not maintain set position"
    ],
    "topPositiveReasons": [
      "has adjustment screw for tuning dimmer (3x)",
      "adjustable control on the side (2x)",
      "Adjustable wheel for configuration",
      "Easy to set up minimum threshold",
      "little dial inside the cover to set minimum brightness"
    ]
  },
  {
    "category": "Timer Functionality",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 5,
    "negativeCount": 1,
    "totalReviews": 6,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Timer doesn't allow dimming"
    ],
    "topPositiveAspects": [
      "bottom switch is a separate non-dimming timer",
      "fan timer works great",
      "timer functions properly",
      "runs fan with the timer or on button",
      "bathroom fan timer is great"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Value Proposition",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 5,
    "negativeCount": 1,
    "totalReviews": 6,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "1000w was pricey compared to 600w"
    ],
    "topPositiveAspects": [
      "exceeded expectations for the price compared to other more expensive ones",
      "Energy-saving with LED bulbs",
      "reasonably priced",
      "far better price than big box stores",
      "really good value"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "sleek design",
      "smooth slider operation",
      "smooth switch push operation",
      "works perfect",
      "functions well"
    ]
  },
  {
    "category": "Smart Connectivity Performance",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 5,
    "negativeCount": 1,
    "totalReviews": 6,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "sometimes tricky to connect to WiFi"
    ],
    "topPositiveAspects": [
      "works flawlessly with Caseta system",
      "integrates seamlessly with Lutron Smart Hub",
      "great integration with Apple HomeKit",
      "great integration with Home Assistant",
      "works through WiFi Bridge"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "works without neutral wire",
      "works great"
    ]
  },
  {
    "category": "Initial Setup",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 5,
    "negativeCount": 1,
    "totalReviews": 6,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "pairing with pico remote not straightforward"
    ],
    "topPositiveAspects": [
      "hub connected to router super quickly",
      "quickest and easiest smart home app setup",
      "smart bridge installed quickly and easily",
      "hub and mobile app easy to set up",
      "syncing with google was a breeze"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Circuit Configuration Support",
    "categoryType": "Performance",
    "mentions": 31,
    "positiveCount": 26,
    "negativeCount": 5,
    "totalReviews": 31,
    "satisfactionRate": 83.9,
    "negativeRate": 16.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not code compliant for 3-ways",
      "only works on hot power end of 3-way circuit, can't use on load side",
      "cannot be used with 3-way presence sensor",
      "two switches on same circuit turn each other on/off",
      "3-way control didn't work"
    ],
    "topPositiveAspects": [
      "works in both single switch or 3-way applications",
      "functions as 3-way switch",
      "no flickering and 3-way works",
      "works with single-pole or 3-way configuration",
      "requires proper wiring configuration for 3-way setup"
    ],
    "topNegativeReasons": [
      "both travelers powered in ON state, both off in OFF state",
      "only works on hot power end of 3-way circuit, can't use on load side"
    ],
    "topPositiveReasons": [
      "Standard switch with three screws for 2-way and 3-way use (14x)",
      "Works in 3-way configuration (14x)",
      "requires neutral wire"
    ]
  },
  {
    "category": "Physical Installation",
    "categoryType": "Performance",
    "mentions": 33,
    "positiveCount": 28,
    "negativeCount": 5,
    "totalReviews": 33,
    "satisfactionRate": 84.8,
    "negativeRate": 15.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "difficulty of installation",
      "Difficult to install in anything less than deep box",
      "No way to position wires and push switch all the way in",
      "does not install like standard dimmer switch",
      "Install becomes difficult/impossible unless inverted"
    ],
    "topPositiveAspects": [
      "straightforward installation (4x)",
      "simple to install (3x)",
      "Straightforward installation (2x)",
      "easy to install/wire and replace",
      "installed in minutes"
    ],
    "topNegativeReasons": [
      "Wire positioning and location inconvenient for installation",
      "Rocker side breaks off after 3-4 months",
      "Electronics box is oversized",
      "Deep profile requiring deep electrical boxes",
      "Causes lights to flicker"
    ],
    "topPositiveReasons": [
      "Does not require neutral wire (2x)",
      "Voice command compatibility with Alexa and Google (2x)",
      "requires neutral wire (2x)",
      "prewired pigtail thin wires",
      "installed in minutes"
    ]
  },
  {
    "category": "Setup and Configuration",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 17,
    "negativeCount": 3,
    "totalReviews": 20,
    "satisfactionRate": 85.0,
    "negativeRate": 15.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "sometimes challenging to program",
      "Requires firmware flash right out of the box",
      "Firmware update takes over 7 hours"
    ],
    "topPositiveAspects": [
      "Easy setup (2x)",
      "very easy to set up (2x)",
      "Setup to Alexa and Gosund app is simple and fast",
      "Quick to set up with Alexa",
      "Easy to install and integrate into wifi system"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Terminals",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 6,
    "negativeCount": 1,
    "totalReviews": 7,
    "satisfactionRate": 85.7,
    "negativeRate": 14.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "twist-wire connections with no push-in wiring option"
    ],
    "topPositiveAspects": [
      "screw terminals instead of wire connections",
      "back-wiring capability",
      "has wires not screw in",
      "uses pigtails compared to screw terminals",
      "Comes with wires attached"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Transformer Compatibility",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 6,
    "negativeCount": 1,
    "totalReviews": 7,
    "satisfactionRate": 85.7,
    "negativeRate": 14.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not work well with magnetic transformers"
    ],
    "topPositiveAspects": [
      "works with electronic transformers",
      "works with low voltage LED fixtures"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 150,
    "positiveCount": 130,
    "negativeCount": 20,
    "totalReviews": 150,
    "satisfactionRate": 86.7,
    "negativeRate": 13.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Paint on the switch",
      "Color not as pictured",
      "Hard to find color in brick and mortar stores",
      "not the prettiest design",
      "ugly appearance"
    ],
    "topPositiveAspects": [
      "looks nice (5x)",
      "beautiful design (3x)",
      "nice design (3x)",
      "nice looking (2x)",
      "Sleek appearance (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Operation Feel",
    "categoryType": "Performance",
    "mentions": 15,
    "positiveCount": 13,
    "negativeCount": 2,
    "totalReviews": 15,
    "satisfactionRate": 86.7,
    "negativeRate": 13.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Must be rotated to activate, not switchable at any position",
      "No tactile click response"
    ],
    "topPositiveAspects": [
      "smooth operation (3x)",
      "Nice and smooth operation",
      "Works without force",
      "Smooth operation",
      "Very smooth"
    ],
    "topNegativeReasons": [
      "No push function at all, rotate to turn on and off"
    ],
    "topPositiveReasons": [
      "smooth slider operation",
      "smooth switch push operation",
      "functions well",
      "simple dial design",
      "sleek shallow profile"
    ]
  },
  {
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 16,
    "positiveCount": 14,
    "negativeCount": 2,
    "totalReviews": 16,
    "satisfactionRate": 87.5,
    "negativeRate": 12.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "upside down orientation marking"
    ],
    "topPositiveAspects": [
      "Classic paddle design with soft-glow light bar",
      "Traditional rocker switch appearance",
      "full width rocker switch",
      "paddle switch design preferred over button style",
      "Paddle style matches other switches in house"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Ease",
    "categoryType": "Performance",
    "mentions": 164,
    "positiveCount": 144,
    "negativeCount": 20,
    "totalReviews": 164,
    "satisfactionRate": 87.8,
    "negativeRate": 12.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "installation complicated",
      "not easy to install",
      "Ease of installation process",
      "Cannot install due to screw design",
      "Instructions lacking for inexperienced users"
    ],
    "topPositiveAspects": [
      "easy install (5x)",
      "very easy to install (4x)",
      "fairly easy to install (4x)",
      "easy to install (3x)",
      "Easy install (2x)"
    ],
    "topNegativeReasons": [
      "large physical dimensions that barely fit in electrical box (3x)",
      "very finicky operation with inconsistent light response (3x)",
      "need a deeper box for installation (2x)",
      "deeper than regular switches",
      "go offline regularly requiring power cycle"
    ],
    "topPositiveReasons": [
      "Three or four wire capability for 3-way or single pole install (2x)",
      "no neutral wire required (2x)",
      "never had a device disconnect (2x)",
      "Smaller than most dimmers",
      "No flickering or noise"
    ]
  },
  {
    "category": "App Control Performance",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 9,
    "negativeCount": 1,
    "totalReviews": 10,
    "satisfactionRate": 90.0,
    "negativeRate": 10.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Glitchy with automations"
    ],
    "topPositiveAspects": [
      "Seamless app control",
      "Schedule and scene setting capability",
      "Smart Away feature",
      "High and low trim control from app",
      "Physical slide dimmer locks in tap brightness"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "Slider for dimming control",
      "Quick installation process"
    ]
  },
  {
    "category": "Advanced Features",
    "categoryType": "Performance",
    "mentions": 21,
    "positiveCount": 19,
    "negativeCount": 2,
    "totalReviews": 21,
    "satisfactionRate": 90.5,
    "negativeRate": 9.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "No WiFi capabilities"
    ],
    "topPositiveAspects": [
      "remembers last brightness setting",
      "Remembers settings",
      "High range of brightness",
      "Hold button for timed shutoff",
      "Gradual on feature"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "dimmer adjustment is on the bottom",
      "stays to whatever was previously set to"
    ]
  },
  {
    "category": "Physical Build Quality",
    "categoryType": "Performance",
    "mentions": 11,
    "positiveCount": 10,
    "negativeCount": 1,
    "totalReviews": 11,
    "satisfactionRate": 90.9,
    "negativeRate": 9.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "can feel the difference in quality compared to other switches"
    ],
    "topPositiveAspects": [
      "solid dimmers with excellent quality and smart features",
      "good product with good quality",
      "quality seems very good",
      "excellent quality and features",
      "high quality software and instructions"
    ],
    "topNegativeReasons": [
      "weighs close to nothing and feels cheap",
      "only dims to about 40-50%"
    ],
    "topPositiveReasons": [
      "has good positive feel when switching on and off",
      "very smooth",
      "only one adjustment for minimum brightness",
      "switches work fine",
      "worked as it should"
    ]
  },
  {
    "category": "Load Compatibility",
    "categoryType": "Performance",
    "mentions": 13,
    "positiveCount": 12,
    "negativeCount": 1,
    "totalReviews": 13,
    "satisfactionRate": 92.3,
    "negativeRate": 7.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Will not work as dimmer for LED array"
    ],
    "topPositiveAspects": [
      "low-voltage compatible",
      "compatibility with compact fluorescent and LED",
      "universal switch compatibility",
      "handles heavy loads",
      "handles 450 LED watts"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi-Switch Configuration",
    "categoryType": "Physical",
    "mentions": 25,
    "positiveCount": 24,
    "negativeCount": 1,
    "totalReviews": 25,
    "satisfactionRate": 96.0,
    "negativeRate": 4.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "fan switch side has 3 specific speeds"
    ],
    "topPositiveAspects": [
      "has large on/off switch and dimmer for accessibility",
      "separate on/off switch from dimmer",
      "main unit and satellite unit configuration",
      "orientation requires satellite to have load going to light",
      "upper switch is dimmer and lower is on/off switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Appearance",
    "categoryType": "Physical",
    "mentions": 77,
    "positiveCount": 74,
    "negativeCount": 3,
    "totalReviews": 77,
    "satisfactionRate": 96.1,
    "negativeRate": 3.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "design puts features before usability",
      "Looks off to the rear of the switches",
      "plain jane variety with no soft on/off or led display"
    ],
    "topPositiveAspects": [
      "looks great (9x)",
      "looks good (7x)",
      "stylish (2x)",
      "sleek and stylish design (2x)",
      "slim profile"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "midnight satin (matte) black finish",
      "works with CFL/LED bulbs"
    ]
  },
  {
    "category": "Installation Process",
    "categoryType": "Performance",
    "mentions": 456,
    "positiveCount": 440,
    "negativeCount": 16,
    "totalReviews": 456,
    "satisfactionRate": 96.5,
    "negativeRate": 3.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "confusing wiring diagram",
      "Installation can be tough",
      "Unable to pull some switches out of housing",
      "challenging to fit 2 units in double gang box",
      "hard to fit in junction box due to size"
    ],
    "topPositiveAspects": [
      "easy to install (49x)",
      "Easy to install (15x)",
      "easy installation (6x)",
      "installation was straightforward (3x)",
      "easy_to_install (3x)"
    ],
    "topNegativeReasons": [
      "only one traveler wire terminal instead of standard two (3x)",
      "stops responding to Alexa for days every few weeks (3x)",
      "takes up lot of space in junction box (2x)",
      "only dims about 50% of light output (2x)",
      "quite large and challenging to fit in tight wall boxes (2x)"
    ],
    "topPositiveReasons": [
      "Easy to install (16x)",
      "requires neutral wire (7x)",
      "back-connect screw-type connections (5x)",
      "rear-screw ground (5x)",
      "neutral pigtail included (5x)"
    ]
  },
  {
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 80,
    "positiveCount": 78,
    "negativeCount": 2,
    "totalReviews": 80,
    "satisfactionRate": 97.5,
    "negativeRate": 2.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "looks cheap",
      "looks bad"
    ],
    "topPositiveAspects": [
      "Sleek and modern appearance (2x)",
      "1970's rotary look",
      "Classic style ideal for traditional homes",
      "clean and modern looking",
      "sleek appearance"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Mounting Hardware",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "wall mount with screw option or 3M adhesive",
      "stick on plate for convenient install"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Customization Capabilities",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "easy connectivity and customizability with near-infinite variations",
      "can really customize what each button does",
      "can create automations to turn lights on/off in different parts of house",
      "set up with 5 different scenes accessible by tapping button"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Memory and Timer Features",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 6,
    "negativeCount": 0,
    "totalReviews": 6,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Remember settings and return to last used level",
      "Timer and schedule functionality works great",
      "Countdown timer function"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "LED Indicators",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 6,
    "negativeCount": 0,
    "totalReviews": 6,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "small LED indicator dot",
      "pinpoint LED light to illuminate switch location",
      "LED bright enough to see in dark but not eyesore",
      "locator light when switch is turned off is very dim",
      "small circle light that illuminates when switch is off for visibility in dark"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi Location Control",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "compatible with three-way and four-way circuits",
      "3-way switch capability",
      "works well with counterpart devices for multiple locations"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Remote Control Operation",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 8,
    "negativeCount": 0,
    "totalReviews": 8,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Remote control capability",
      "remote works great with long range",
      "remote operates as expected",
      "remote control works great",
      "remote works great for on/off control"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "wireless remote with 100ft range (2x)"
    ]
  },
  {
    "category": "Advanced Smart Features",
    "categoryType": "Performance",
    "mentions": 11,
    "positiveCount": 11,
    "negativeCount": 0,
    "totalReviews": 11,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Scheduling and automation features",
      "Motion sensor integration capability",
      "Soft on and off feature",
      "Fade off feature",
      "Double tap, triple tap, and long hold actions"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi-Way Switch Operation",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "3-way capability available",
      "Works in single and dual pole locations"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "Labeled wires for easy installation"
    ]
  },
  {
    "category": "Tactile Operation",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 9,
    "negativeCount": 0,
    "totalReviews": 9,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Low force needed to activate with significant breakaway",
      "Small force to keep depressed",
      "quick and easy to operate",
      "easiest to operate compared to other dimmers",
      "easy to control"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "rotary style (2x)",
      "provides fine dimming control (2x)",
      "dimmer has smooth glide",
      "no flicker when adjusting brightness",
      "rocker is light and crisp"
    ]
  },
  {
    "category": "Illumination Features",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "has locator light",
      "has_locator_light_for_dark_visibility"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Advanced Configuration Options",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 7,
    "negativeCount": 0,
    "totalReviews": 7,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "very adjustable settings",
      "Easy to adjust minimum point with adjustment button",
      "allows programming min and max levels",
      "allows programming 5 presets",
      "can set to super low light level"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Device Pairing",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 7,
    "negativeCount": 0,
    "totalReviews": 7,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "requires fast cadence triple press for pairing",
      "pairing was easy",
      "Easy to pair",
      "Network add is a walk in the park",
      "Takes no time to pair and control"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "has pair button for setup",
      "pairing was easy"
    ]
  },
  {
    "category": "Electrical Stability",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "works with no flickering or noise (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Signal Range",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 6,
    "negativeCount": 0,
    "totalReviews": 6,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "very good RF performance",
      "good range connecting 60 ft from house",
      "excellent connectivity and range without direct pointing",
      "works well from 12 feet distance",
      "good range for reasonable distance control"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "magnetic attachment capability",
      "easy to install"
    ]
  },
  {
    "category": "Touch and Capacitive Features",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "touch sensor requires bare skin contact",
      "capacitive touch feature",
      "feels like phone touchscreen when adjusting light",
      "vertical touch sensor in the middle of the switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Screw Quality and Fit",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "screws firmly attached"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Shape Design",
    "categoryType": "Physical",
    "mentions": 10,
    "positiveCount": 10,
    "negativeCount": 0,
    "totalReviews": 10,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Slim/thin profile",
      "Lightweight construction",
      "has hourglass shape",
      "has paddle shape that is unusual but not unattractive",
      "has large switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "LED Illumination",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "small built in LED night light",
      "provides visibility in low-light conditions"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "User Interface Design",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "clear and intuitive interface",
      "user-friendly design",
      "easy to navigate",
      "easier to reach light level"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "dimmable slider (2x)",
      "perfect ability to control lights from 0-100% brightness (2x)",
      "slider on the front (2x)"
    ]
  },
  {
    "category": "Product Certification",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "UL approved",
      "has UL rating printed on metal part"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Memory Functions",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 5,
    "negativeCount": 0,
    "totalReviews": 5,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "dimmer settings holds up well and retrieves original settings",
      "program feature returns to setting when powered off and back on",
      "remembers dimming setting when turned back on",
      "remembers last dimmer setting",
      "returns to previous dimmed level"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Tactile Operation Feel",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "feels better when you turn the knob",
      "clicks very smoothly when turned on or off"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Construction Quality",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Great quality and function"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Appeal",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "look_great",
      "dimmers_look_great"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Network Integration",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "easy to connect with Alexa"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Night Visibility",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "night light allows switch to be seen in dark"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  }
];

// Light Switches Data  
export const lightSwitchesSummary = {
  "totalCategories": 186,
  "physicalCategories": 73,
  "performanceCategories": 113,
  "avgSatisfactionRate": 60.8,
  "processingDate": "2025-06-10 17:44:03",
  "productType": "Light Switches"
};
export const topNegativeLightCategories: CategoryFeedback[] = [
  {
    "category": "Product Lifespan",
    "categoryType": "Performance",
    "mentions": 131,
    "positiveCount": 9,
    "negativeCount": 122,
    "totalReviews": 131,
    "satisfactionRate": 6.9,
    "negativeRate": 93.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stopped working after 2 months (2x)",
      "need replacement within 2 weeks",
      "poor long-term reliability",
      "Don't appear to last",
      "Only got a year's use"
    ],
    "topPositiveAspects": [
      "reliable after extended use",
      "lasts forever",
      "long-lasting for many years",
      "Will still work in ten years",
      "Quality and durability"
    ],
    "topNegativeReasons": [
      "Cracks after couple years (2x)",
      "Really hard to turn off after 6 months (2x)",
      "cheap materials used (2x)",
      "paddle pops out completely after 8 months (2x)",
      "diodes stopped working (2x)"
    ],
    "topPositiveReasons": [
      "high-quality materials",
      "smooth switching",
      "Quality construction",
      "Quality and durability",
      "easy installation"
    ]
  },
  {
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 223,
    "positiveCount": 118,
    "negativeCount": 105,
    "totalReviews": 223,
    "satisfactionRate": 52.9,
    "negativeRate": 47.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "narrow slit design",
      "neon light technology",
      "blue center light indicator",
      "blue LED lights on switch buttons",
      "very dim and barely visible"
    ],
    "topPositiveAspects": [
      "red color",
      "blue LED indicates transmitter functioning",
      "has blue light",
      "LED indicators present",
      "bright red light"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Basic Functionality",
    "categoryType": "Performance",
    "mentions": 379,
    "positiveCount": 315,
    "negativeCount": 64,
    "totalReviews": 379,
    "satisfactionRate": 83.1,
    "negativeRate": 16.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "did not work at all (2x)",
      "doesn't work (2x)",
      "failed",
      "no funciona",
      "worked 50% of the time"
    ],
    "topPositiveAspects": [
      "works great (20x)",
      "works fine (12x)",
      "works as expected (10x)",
      "works perfectly (7x)",
      "works as intended (6x)"
    ],
    "topNegativeReasons": [
      "flimsy and breaks easily (2x)",
      "small print, hard to read instructions",
      "switch stays in the middle position",
      "flick down turns off lights and returns to middle",
      "not the same as the button it tries to imitate"
    ],
    "topPositiveReasons": [
      "removable tabs on both sides (3x)",
      "easy installation process (3x)",
      "Solid construction",
      "rugged design",
      "Solid construction, not flimsy"
    ]
  },
  {
    "category": "Long Term Durability",
    "categoryType": "Performance",
    "mentions": 81,
    "positiveCount": 31,
    "negativeCount": 50,
    "totalReviews": 81,
    "satisfactionRate": 38.3,
    "negativeRate": 61.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "uncertain about long-term durability (2x)",
      "engineered to fail after warranty expires (2x)",
      "failed in May after September purchase",
      "device dies after 2 months with unresponsive buttons",
      "stops functioning after few weeks"
    ],
    "topPositiveAspects": [
      "great durability (2x)",
      "so far so good",
      "works great so far",
      "expected to last for several lives of future home owners",
      "keep working over time"
    ],
    "topNegativeReasons": [
      "fails after 2 years",
      "internal switch component",
      "works for 3.5 years then breaks with clicking",
      "thin plastic section across center as weak support",
      "top rocker tab"
    ],
    "topPositiveReasons": [
      "feels sturdy",
      "just works",
      "sturdy build quality",
      "Heavier weight 76g vs residential 47g",
      "quality design"
    ]
  },
  {
    "category": "Network Connection Stability",
    "categoryType": "Performance",
    "mentions": 70,
    "positiveCount": 20,
    "negativeCount": 50,
    "totalReviews": 70,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "difficult to pair with zwave system",
      "keeps dropping connection",
      "very kludgy procedure for adding to SmartThings",
      "extremely tricky connecting to Ring Alarm",
      "constantly disconnects from Z wave system"
    ],
    "topPositiveAspects": [
      "easy with Smart Things",
      "connects up first time every time",
      "much easier to include and adapt",
      "integrated perfectly in Ring Alarm z-wave setup",
      "Works with Home Assistant via Zigbee correctly for on/off commands"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 150,
    "positiveCount": 101,
    "negativeCount": 49,
    "totalReviews": 150,
    "satisfactionRate": 67.3,
    "negativeRate": 32.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "color does not match other BESTTEN switches",
      "appears gray instead of white",
      "looks slightly different from other switches",
      "Wrong color",
      "Vendor name stamped into the plate"
    ],
    "topPositiveAspects": [
      "nice looking (5x)",
      "good appearance (3x)",
      "modern look (3x)",
      "attractive appearance (2x)",
      "modern looking (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "WiFi Connectivity",
    "categoryType": "Performance",
    "mentions": 71,
    "positiveCount": 23,
    "negativeCount": 48,
    "totalReviews": 71,
    "satisfactionRate": 32.4,
    "negativeRate": 67.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "fails to connect to wifi",
      "loses connection with WiFi after some time",
      "connection to Alexa worked for a day then would not stay connected",
      "wifi connection fails after 5 months",
      "wifi connectivity constantly disconnects"
    ],
    "topPositiveAspects": [
      "connects to wifi with no problems",
      "connects up with no issues",
      "wifi connectivity is great",
      "really easy to connect to phone",
      "only works on 2.4GHz band"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 121,
    "positiveCount": 74,
    "negativeCount": 47,
    "totalReviews": 121,
    "satisfactionRate": 61.2,
    "negativeRate": 38.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "requires neutral wire (2x)",
      "short wire length",
      "thin wire gauge",
      "16 gauge wires on transmitter",
      "wire connectors not up to code"
    ],
    "topPositiveAspects": [
      "requires neutral wire (3x)",
      "Requires neutral wire connection (2x)",
      "requires neutral wire connection",
      "levers on back to secure wires",
      "push in connectors with lever lock"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Durability",
    "categoryType": "Performance",
    "mentions": 50,
    "positiveCount": 7,
    "negativeCount": 43,
    "totalReviews": 50,
    "satisfactionRate": 14.0,
    "negativeRate": 86.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "buttons break easily",
      "rocker switch stuck to on position",
      "switches broken and flopped in seat",
      "bottom switch broke and fell off after few months with top one cracked",
      "center rocker switch only lasted 11 months with normal usage"
    ],
    "topPositiveAspects": [
      "sturdy",
      "made sturdy to last",
      "sturdy and reliable",
      "long-lasting construction",
      "withstand heavy use from children"
    ],
    "topNegativeReasons": [
      "buttons break easily",
      "rocker switch stuck to on position",
      "switches broken and flopped in seat",
      "screws strip easily",
      "Cheaply made"
    ],
    "topPositiveReasons": [
      "sturdy construction",
      "well made construction",
      "consistent quality across multiple units",
      "sturdy build quality",
      "look nice/great on wall"
    ]
  },
  {
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 185,
    "positiveCount": 144,
    "negativeCount": 41,
    "totalReviews": 185,
    "satisfactionRate": 77.8,
    "negativeRate": 22.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Cheaply made (2x)",
      "cheaply built (2x)",
      "Cheap circuitry that doesn't hold up",
      "cheap appearance",
      "doesn't scream high-quality"
    ],
    "topPositiveAspects": [
      "well made (6x)",
      "good quality (4x)",
      "well made construction (3x)",
      "Good quality construction (3x)",
      "heavy duty construction (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  }
];
export const topPositiveLightCategories: CategoryFeedback[] = [
  {
    "category": "Installation Process",
    "categoryType": "Performance",
    "mentions": 467,
    "positiveCount": 457,
    "negativeCount": 10,
    "totalReviews": 467,
    "satisfactionRate": 97.9,
    "negativeRate": 2.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Back holes don't work for hookup",
      "mounting screws strip easily in plastic boxes",
      "Difficult to push wires into place for screw down",
      "limited to 14 gauge wire, cannot accommodate 12 gauge",
      "More difficult installation than anticipated"
    ],
    "topPositiveAspects": [
      "easy to install (56x)",
      "Easy to install (15x)",
      "easy installation (10x)",
      "Easy installation (3x)",
      "easy to wire (2x)"
    ],
    "topNegativeReasons": [
      "Has holes on the back for hookup",
      "cheap mounting screws that strip easily",
      "lighter weight screws with low quality metal",
      "accepts 14 gauge wire only",
      "too small for 12 gauge wire"
    ],
    "topPositiveReasons": [
      "easy to install (15x)",
      "wires are easy to terminate (10x)",
      "press-in connections are really nice (9x)",
      "easy to install terminals (9x)",
      "1 gang standard size matching US household switches (7x)"
    ]
  },
  {
    "category": "Basic Functionality",
    "categoryType": "Performance",
    "mentions": 379,
    "positiveCount": 315,
    "negativeCount": 64,
    "totalReviews": 379,
    "satisfactionRate": 83.1,
    "negativeRate": 16.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "did not work at all (2x)",
      "doesn't work (2x)",
      "failed",
      "no funciona",
      "worked 50% of the time"
    ],
    "topPositiveAspects": [
      "works great (20x)",
      "works fine (12x)",
      "works as expected (10x)",
      "works perfectly (7x)",
      "works as intended (6x)"
    ],
    "topNegativeReasons": [
      "flimsy and breaks easily (2x)",
      "small print, hard to read instructions",
      "switch stays in the middle position",
      "flick down turns off lights and returns to middle",
      "not the same as the button it tries to imitate"
    ],
    "topPositiveReasons": [
      "removable tabs on both sides (3x)",
      "easy installation process (3x)",
      "Solid construction",
      "rugged design",
      "Solid construction, not flimsy"
    ]
  },
  {
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 185,
    "positiveCount": 144,
    "negativeCount": 41,
    "totalReviews": 185,
    "satisfactionRate": 77.8,
    "negativeRate": 22.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Cheaply made (2x)",
      "cheaply built (2x)",
      "Cheap circuitry that doesn't hold up",
      "cheap appearance",
      "doesn't scream high-quality"
    ],
    "topPositiveAspects": [
      "well made (6x)",
      "good quality (4x)",
      "well made construction (3x)",
      "Good quality construction (3x)",
      "heavy duty construction (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Overall Reliability",
    "categoryType": "Performance",
    "mentions": 170,
    "positiveCount": 140,
    "negativeCount": 30,
    "totalReviews": 170,
    "satisfactionRate": 82.4,
    "negativeRate": 17.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "did not work (2x)",
      "only worked 10% of time initially",
      "sometimes doesn't seem to work",
      "one remote works, other doesn't",
      "sometimes works to turn on/off, other times doesn't"
    ],
    "topPositiveAspects": [
      "works as advertised (6x)",
      "works great (4x)",
      "works flawlessly (3x)",
      "Works as advertised (2x)",
      "works perfectly (2x)"
    ],
    "topNegativeReasons": [
      "burn marks appear on switch when turned on",
      "Internal relay"
    ],
    "topPositiveReasons": [
      "relay component",
      "lever action wire connection",
      "breeze to install",
      "SO easy to install"
    ]
  },
  {
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 128,
    "positiveCount": 124,
    "negativeCount": 4,
    "totalReviews": 128,
    "satisfactionRate": 96.9,
    "negativeRate": 3.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "company name impressed into plastic",
      "look-and-feel of original Caseta dimmers",
      "Lacks metallic quality"
    ],
    "topPositiveAspects": [
      "clean look (5x)",
      "sleek design (3x)",
      "look great (2x)",
      "modern appearance (2x)",
      "Clean look (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Ease",
    "categoryType": "Performance",
    "mentions": 131,
    "positiveCount": 120,
    "negativeCount": 11,
    "totalReviews": 131,
    "satisfactionRate": 91.6,
    "negativeRate": 8.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "makes it difficult to tie into romex",
      "hard to wire",
      "tricky to hook up lighted switch",
      "install/removal takes longer due to wire configuration",
      "not easy to install"
    ],
    "topPositiveAspects": [
      "easy to install (5x)",
      "super easy to install (2x)",
      "very easy to install (2x)",
      "easy to change out (2x)",
      "quick and easy installation"
    ],
    "topNegativeReasons": [
      "short wire length (2x)",
      "makes junction box tight (2x)",
      "extremely complex installation (2x)",
      "has 5 stranded wires with wire nuts",
      "both light and fan switches die simultaneously"
    ],
    "topPositiveReasons": [
      "levers on back to secure wires (2x)",
      "rock solid connection that withstands pulling (2x)",
      "can hook up line and load wires any way (2x)",
      "switch is intelligent enough to determine which is line and which is load (2x)",
      "super easy install (2x)"
    ]
  },
  {
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 223,
    "positiveCount": 118,
    "negativeCount": 105,
    "totalReviews": 223,
    "satisfactionRate": 52.9,
    "negativeRate": 47.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "narrow slit design",
      "neon light technology",
      "blue center light indicator",
      "blue LED lights on switch buttons",
      "very dim and barely visible"
    ],
    "topPositiveAspects": [
      "red color",
      "blue LED indicates transmitter functioning",
      "has blue light",
      "LED indicators present",
      "bright red light"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 150,
    "positiveCount": 101,
    "negativeCount": 49,
    "totalReviews": 150,
    "satisfactionRate": 67.3,
    "negativeRate": 32.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "color does not match other BESTTEN switches",
      "appears gray instead of white",
      "looks slightly different from other switches",
      "Wrong color",
      "Vendor name stamped into the plate"
    ],
    "topPositiveAspects": [
      "nice looking (5x)",
      "good appearance (3x)",
      "modern look (3x)",
      "attractive appearance (2x)",
      "modern looking (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Functional Reliability",
    "categoryType": "Performance",
    "mentions": 122,
    "positiveCount": 88,
    "negativeCount": 34,
    "totalReviews": 122,
    "satisfactionRate": 72.1,
    "negativeRate": 27.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "switch did not work (2x)",
      "didn't work (2x)",
      "stopped working properly after a couple months",
      "work correctly only sometimes",
      "become unavailable multiple times daily"
    ],
    "topPositiveAspects": [
      "worked perfectly (7x)",
      "easy to use (3x)",
      "working fine (2x)",
      "held up to description and worked flawlessly",
      "functions as expected"
    ],
    "topNegativeReasons": [
      "rocker switch breaks",
      "will not stay on",
      "rocker function is broken",
      "four of the ten don't work",
      "cheap plastic feel"
    ],
    "topPositiveReasons": [
      "paddle design is smooth (2x)",
      "easy operation (2x)",
      "paddle rocker design",
      "single power input with three outputs",
      "well made"
    ]
  },
  {
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 121,
    "positiveCount": 74,
    "negativeCount": 47,
    "totalReviews": 121,
    "satisfactionRate": 61.2,
    "negativeRate": 38.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "requires neutral wire (2x)",
      "short wire length",
      "thin wire gauge",
      "16 gauge wires on transmitter",
      "wire connectors not up to code"
    ],
    "topPositiveAspects": [
      "requires neutral wire (3x)",
      "Requires neutral wire connection (2x)",
      "requires neutral wire connection",
      "levers on back to secure wires",
      "push in connectors with lever lock"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  }
];
export const topUseCasesLight: UseCaseFeedback[] = [
  {
    "useCase": "Smart Home Integration",
    "totalMentions": 188,
    "positiveCount": 104,
    "negativeCount": 55,
    "satisfactionRate": 55.3,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "responsive and works with app and voice commands (13x)",
      "responsive (9x)",
      "voice assistant compatibility (8x)",
      "sturdy and well-made construction (8x)",
      "responsive touch buttons with satisfying tactile experience (8x)"
    ],
    "topGapReasons": [
      "WiFi connection stability (16x)",
      "manual switches (4x)",
      "physical switch (4x)",
      "wall switch (4x)",
      "hard time connecting to wifi (4x)"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Smart Home Automation",
    "totalMentions": 85,
    "positiveCount": 50,
    "negativeCount": 24,
    "satisfactionRate": 58.8,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "Works great as designed (9x)",
      "works with Alexa (7x)",
      "works with Google Home (7x)",
      "works with Siri (7x)",
      "responsive and works with app and voice commands (6x)"
    ],
    "topGapReasons": [
      "poor homekit integration with updating issues (4x)",
      "missing homekit code on switch (2x)",
      "Does not work with Alexa routines (2x)",
      "Voice commands disabled when using different switches (2x)",
      "uses stranded wire leads requiring wire nuts or crimp connectors"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Room Specific Lighting",
    "totalMentions": 78,
    "positiveCount": 55,
    "negativeCount": 10,
    "satisfactionRate": 70.5,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "white light (9x)",
      "faint glow (9x)",
      "nice build quality (9x)",
      "perfect for hallways (9x)",
      "not bright but easy to see in dark hall (9x)"
    ],
    "topGapReasons": [
      "wifi connectivity constantly disconnects (2x)",
      "cannot connect to wifi network (2x)",
      "switches barely work after 6 months",
      "on/off is very erratic, takes 10-15 tries",
      "wifi connection fails after 5 months"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Dark Area Navigation",
    "totalMentions": 78,
    "positiveCount": 65,
    "negativeCount": 6,
    "satisfactionRate": 83.3,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "glows in the dark when in off position (13x)",
      "standard size (13x)",
      "works as intended (13x)",
      "perfect brightness level (13x)",
      "Brightness level varies from very bright to extremely dim (12x)"
    ],
    "topGapReasons": [
      "small size (2x)",
      "barely visible in dark (2x)",
      "Difficult to see in daylight",
      "too dim",
      "LED behind the bezel"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Replacement And Upgrade",
    "totalMentions": 74,
    "positiveCount": 48,
    "negativeCount": 6,
    "satisfactionRate": 64.9,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "easy to install (16x)",
      "works great (7x)",
      "high quality material (4x)",
      "cover plate good quality (4x)",
      "good quality (4x)"
    ],
    "topGapReasons": [
      "don't match other brand switches",
      "requires neutral wire",
      "fails to connect to router",
      "cannot be wired due to missing ground connection",
      "audible click on relay"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Switch Replacement And Upgrade",
    "totalMentions": 68,
    "positiveCount": 49,
    "negativeCount": 5,
    "satisfactionRate": 72.1,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "Easy to install (8x)",
      "easy to install (6x)",
      "looks great and modern style (4x)",
      "work perfectly and control lights perfectly (4x)",
      "Plastic material (4x)"
    ],
    "topGapReasons": [
      "manual switches don't respond reliably after 10 months (4x)",
      "physical switch stopped working after 1 year (4x)",
      "stopped working after 3 months (4x)",
      "long term reliability issues (4x)",
      "Gap at top of switch"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Installation And Renovation",
    "totalMentions": 67,
    "positiveCount": 56,
    "negativeCount": 4,
    "satisfactionRate": 83.6,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "easy to install (15x)",
      "Easy to install (11x)",
      "clean look (9x)",
      "sleek decorator-style design (5x)",
      "modern appearance (5x)"
    ],
    "topGapReasons": [
      "fails to function (2x)",
      "not true white, more off-white or slightly almond",
      "over half of switches broke within 2 years",
      "Not true white but light gray/off-white color",
      "Mix of glossy and matte white finishes in same box"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Switch Replacement And Upgrades",
    "totalMentions": 67,
    "positiveCount": 45,
    "negativeCount": 5,
    "satisfactionRate": 67.2,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "Easy to install (9x)",
      "Works as intended/expected (7x)",
      "works as expected (4x)",
      "easy installation (4x)",
      "worked perfectly (3x)"
    ],
    "topGapReasons": [
      "causes LED ghosting with 1-2 lights",
      "would not turn on the light despite app control working",
      "worked as regular switch but not as smart switch",
      "did not work",
      "doesn't work 5 feet from light"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Room-Specific Lighting Control",
    "totalMentions": 53,
    "positiveCount": 34,
    "negativeCount": 12,
    "satisfactionRate": 64.2,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "LED produces cool white light (6x)",
      "Perfect brightness level (6x)",
      "manual control works (6x)",
      "automation features (6x)",
      "easy to install (4x)"
    ],
    "topGapReasons": [
      "white LED may not be suitable for sleeping areas",
      "very little light output",
      "centered position on paddle",
      "not visible from side angle",
      "loud clicking noise when switching"
    ],
    "relatedCategories": []
  },
  {
    "useCase": "Home Renovation And Modernization",
    "totalMentions": 50,
    "positiveCount": 41,
    "negativeCount": 1,
    "satisfactionRate": 82.0,
    "categoryType": "Physical",
    "topSatisfactionReasons": [
      "easy to install (14x)",
      "cover plate good quality (7x)",
      "good quality (7x)",
      "look nice/great on wall (5x)",
      "great audible click with authority (5x)"
    ],
    "topGapReasons": [
      "feels mushy and sometimes gets stuck where none of outputs are energized"
    ],
    "relatedCategories": []
  }
];
export const allLightCategories: CategoryFeedback[] = [
  {
    "category": "Color Matching",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 0,
    "negativeCount": 8,
    "totalReviews": 8,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Off-white color instead of white",
      "Gloss ivory color instead of gloss white",
      "off-white color that looks dirty rather than true white"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Manufacturing Quality",
    "categoryType": "Performance",
    "mentions": 17,
    "positiveCount": 0,
    "negativeCount": 17,
    "totalReviews": 17,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "defective unit",
      "extremely_inconsistent_quality_control",
      "high_defect_rate",
      "poor quality control",
      "one out of three switches defective"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "wire attachment plates that deform and slide out of place",
      "always dropping wifi",
      "earth connection at different places on different switches",
      "overall performance not very good"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Safety",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 0,
    "negativeCount": 6,
    "totalReviews": 6,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "two switches didn't work and caused power outage",
      "wire_arcing_risk_when_screw_loosened",
      "metal around unit could cause short in metal box",
      "Could potentially cause fires due to misadvertised amperage",
      "Creates fire danger with fans due to voltage leakage"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "terminal_screw_tightening_affects_switch_operation",
      "switches_will_not_toggle_into_place",
      "Actual product part number rated for 15 amps despite 20 amp advertising",
      "Switches leak voltage when off",
      "LED lights flicker"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Surface Quality",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "one switch was smudged and dirty",
      "black smudge stain that cannot be cleaned",
      "burn marks appear on switch when turned on"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Signal Quality",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "metal wall box interferes with signals",
      "receiver orientation affects performance"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "metal wall box interferes with wireless signals"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Tactile Operation",
    "categoryType": "Performance",
    "mentions": 14,
    "positiveCount": 0,
    "negativeCount": 14,
    "totalReviews": 14,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "hard to push",
      "different feedback force",
      "function is not good, have to push hard",
      "requires more effort to flip",
      "takes about 2 lbs pressure vs 4 oz for normal switch"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "very stiff toggle (2x)",
      "loud clicking action (2x)",
      "scrapes against housing",
      "causes lights to flicker",
      "excessive pressure required to flip"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Light Quality Issues",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 0,
    "negativeCount": 4,
    "totalReviews": 4,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "causes lights to flicker",
      "lights started flickering after installation",
      "LED light occasionally flicker",
      "engaging fan makes LED shut off then come back on"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Safety Concerns",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "turns on randomly and sparks",
      "causes internal arcing",
      "sparked when turned on"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "has internal design issues"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Product Defects",
    "categoryType": "Performance",
    "mentions": 27,
    "positiveCount": 0,
    "negativeCount": 27,
    "totalReviews": 27,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "defective switches",
      "high defective rate",
      "high rate of defective units in packaging",
      "some switches defective out of box",
      "2 out of 6 were defective"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "plastic hinge breaks off easily",
      "does not match other brand products",
      "shorted travelers with silver screws"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Position Stability",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 0,
    "negativeCount": 8,
    "totalReviews": 8,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "switches_do_not_stay_in_set_position",
      "switches_automatically_flip_back_to_off",
      "switches_randomly_turn_themselves_off",
      "switches_teeter_back_and_forth",
      "stuck in on position"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "poor_construction_quality (6x)",
      "switches_do_not_stay_in_set_position (6x)",
      "overly_sensitive_spring_loaded_mechanism",
      "switches_teeter_back_and_forth"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Switch Operation",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 0,
    "negativeCount": 8,
    "totalReviews": 8,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "switches_will_not_toggle_into_place",
      "switches_will_not_toggle_on",
      "switches_will_not_toggle_off",
      "switches_do_not_click_fully_into_on_position",
      "switches_will_not_fully_seat_in_off_position"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "poor_construction_quality (5x)",
      "switches_do_not_stay_in_set_position (5x)",
      "lack_of_resistance_in_switching_mechanism",
      "switches_randomly_turn_themselves_off",
      "terminal_screw_tightening_affects_switch_operation"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Face Plates",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "snap on cover plate",
      "Snap in mechanisms are not the same for switches and receptacles"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wire Connection Compatibility",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 0,
    "negativeCount": 4,
    "totalReviews": 4,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "accepts only small gauge wire",
      "accepts 14 gauge wire only",
      "too small for 12 gauge wire",
      "Back holes won't admit 12 gauge wire"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Power Sensitivity",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 0,
    "negativeCount": 4,
    "totalReviews": 4,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Get confused if power returns before WiFi",
      "power cutoff/surge can kill switches",
      "burns out easily from surges",
      "several failed after storm"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Power Control Accuracy",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Contacts close but no power applied"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Requirements",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cannot be wired due to missing ground connection"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "lacks ground wire connection",
      "app cannot find device"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Privacy and Data",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "requires invasive app permissions",
      "stores data in China"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Setup Instructions",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "instructions are in Chinese"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Component Reliability",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 0,
    "negativeCount": 8,
    "totalReviews": 8,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "terminal screws are poor quality and do not engage straight blade screw drivers securely",
      "one terminal screw stripped while securing wire",
      "one of the sockets was loose",
      "Grounding screws aren't locked in, backing fumbles around when undone",
      "Side screws can become disconnected from internal nut if backed out too far"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Control Precision",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "dimmer steps are not equal"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Condition Issues",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "burnt wire in used product",
      "crooked alignment"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Light Control Performance",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 0,
    "negativeCount": 6,
    "totalReviews": 6,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "light is manual only with no occupancy detection",
      "dims then brightens lights every 10-15 seconds",
      "randomly turns lights on",
      "randomly turns lights off",
      "comes on at random times"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Mounting Tabs and Hardware",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Heavy gauge metal tabs",
      "Snap-off ears don't fit curved edge utility box covers properly"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Toggle Operation",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "toggle does not move full to up or down position"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Screw Quality and Fit",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 0,
    "negativeCount": 8,
    "totalReviews": 8,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "One of the screws had been forced into the wrong hole and took a great deal of trouble to remove",
      "A bit tough getting the screws to tighten",
      "screws strip easily",
      "Always 1/4 inch too short for North American homes",
      "One cover without screws"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Housing",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 0,
    "negativeCount": 4,
    "totalReviews": 4,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "screws go inside housing under pressure",
      "switch casing slightly skewed, making it hard to fit into standard plate",
      "plastic housing with retaining bracket",
      "plastic cover that can separate easily"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Complexity",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 0,
    "negativeCount": 7,
    "totalReviews": 7,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "finicky to hook up",
      "A little finicky to install",
      "Hard to install",
      "A little more frustrating than needed",
      "difficult and dangerous to install"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Push in quick wire slots not tightening down (2x)",
      "screws go inside housing under pressure",
      "Push-in wire slots not holding, slipping back out",
      "Has to be pushed down really hard beyond normal end-position to turn off",
      "flimsy terminals that never tighten up properly"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Product Defect Rate",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "has quality control issues with some units being defective"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color Accuracy",
    "categoryType": "Physical",
    "mentions": 18,
    "positiveCount": 0,
    "negativeCount": 18,
    "totalReviews": 18,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not white like they should be",
      "bone color instead of white",
      "not snow white but off-white",
      "light cream color",
      "off-white/cream color"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Deterioration",
    "categoryType": "Performance",
    "mentions": 22,
    "positiveCount": 0,
    "negativeCount": 22,
    "totalReviews": 22,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "popping out of the wall after a couple of years",
      "switch cracked shortly after install",
      "switch falling apart",
      "2 of them fell apart after 5 months",
      "two switches broken off the wall after a month"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Fragile plastic housing that can snap or disintegrate (3x)",
      "Shorts out when defective (3x)",
      "cheaply made (2x)",
      "paddle pops out within few months (2x)",
      "brittle plastic that breaks over time"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "False Activation Control",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 0,
    "negativeCount": 8,
    "totalReviews": 8,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "registers perfectly timed coughs and turns on/off unexpectedly",
      "goes off when TV is playing",
      "odd things like closing drawer or knock on wall or door will turn it on or off",
      "turns on when opening end table drawer",
      "spontaneously turned on and off"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Load Compatibility",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "doesn't work for items that have to be turned on/off with buttons like oscillating fan",
      "doesn't work for any stand lights"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wall Plate Fit and Alignment",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Stick out a bit from wall",
      "Pretty thin and don't align correctly, leave a slight gap"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Mechanism Reliability",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 0,
    "negativeCount": 12,
    "totalReviews": 12,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "One switch wouldn't stay engaged",
      "Don't click well, one doesn't click in one direction",
      "Has to be pushed down really hard beyond normal end-position to turn off",
      "sometimes stuck in on position requiring multiple toggles",
      "Switch fails to hold in on position"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Switch breaks or fails mechanically (5x)",
      "Switch would not toggle properly (5x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Surface Condition and Finish",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 0,
    "negativeCount": 5,
    "totalReviews": 5,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "scratches and dings on visible parts",
      "scuffs and scratches"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Sound During Operation",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "makes loud sound when switching"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Behavior Issues",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 0,
    "negativeCount": 8,
    "totalReviews": 8,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Current passing through switch in off position",
      "causes LED lights to blink due to current leakage",
      "causes arcing inside",
      "neon bulb flickers in off position with LED lights",
      "controlled lights flicker when off"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "causes arcing inside"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Structural Mounting Features",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 0,
    "negativeCount": 6,
    "totalReviews": 6,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "extended tabs above and below the box",
      "plastic at the top and bottom like tabs",
      "thick plastic tabs for box attachment",
      "thick plastic mounting ears",
      "riveted retaining bracket in rear center"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Housing Fit",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "clearance between housing and bolt heads is too narrow",
      "front case won't close unless held together"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Slider Mechanisms",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Only works in 1/4 of the stroke"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Device Reliability",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 0,
    "negativeCount": 6,
    "totalReviews": 6,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Switch mechanism fails",
      "Nightlight function does not work",
      "LED light turns on/off randomly"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Performance",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Dimming range too sensitive"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "Only works in 1/4 of the stroke"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Surface Characteristics",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 0,
    "negativeCount": 5,
    "totalReviews": 5,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "\"Leviton\" embossing on the switch appears to serve no purpose other than to attract dust and create a sense of dirtiness",
      "Has scuff marks when used",
      "smudges and black stuff on surface",
      "Embossed name on switch harbors bacteria and viruses",
      "No longer perfectly smooth for cleaning"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Batch Failure Rates",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 0,
    "negativeCount": 5,
    "totalReviews": 5,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "100% failure rate within 60 days",
      "all failed within a month",
      "2 of 4 stopped working after one month",
      "only 5 of 10 switches working properly",
      "2 not working after 2 months"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Light Flickering",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Causes lights to flicker rapidly in constant on/off mode"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Status Accuracy",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 0,
    "negativeCount": 3,
    "totalReviews": 3,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "app shows incorrect status on 3-way circuits",
      "needs to be polled to get status"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Device Status and Communication",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "green light stays on but won't function",
      "device shows offline in app"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Brand and Device Compatibility",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 0,
    "negativeCount": 2,
    "totalReviews": 2,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "only works with other Enbrighten smart switches",
      "does not work with smart switches from other manufacturers"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Position Clarity",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 0,
    "negativeCount": 1,
    "totalReviews": 1,
    "satisfactionRate": 0.0,
    "negativeRate": 100.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "difficult to realize switch is on or off"
    ],
    "topPositiveAspects": [],
    "topNegativeReasons": [
      "switch position flip is very light"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Product Longevity",
    "categoryType": "Performance",
    "mentions": 41,
    "positiveCount": 1,
    "negativeCount": 40,
    "totalReviews": 41,
    "satisfactionRate": 2.4,
    "negativeRate": 97.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stopped working after a year",
      "quit working after 1 day",
      "replacement lasted 2 days",
      "one switch module drains battery and is bad",
      "lasts 6 months exactly then becomes unresponsive"
    ],
    "topPositiveAspects": [
      "expected to last a long time"
    ],
    "topNegativeReasons": [
      "physical button becomes unresponsive after 1 year (8x)",
      "Illumination fails after short period of use (3x)",
      "Provides some area illumination (3x)",
      "drains battery in minutes",
      "only worked 10% of time initially"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Wire Connection Issues",
    "categoryType": "Performance",
    "mentions": 18,
    "positiveCount": 1,
    "negativeCount": 17,
    "totalReviews": 18,
    "satisfactionRate": 5.6,
    "negativeRate": 94.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "takes good push to get wire in",
      "extra time to relocate ground wires",
      "braided wire frustrating to insert",
      "does not fit #12AWG copper wire without a lot of work",
      "14AWG or larger doesn't fit into holes"
    ],
    "topPositiveAspects": [
      "made to fit #14AWG copper wire"
    ],
    "topNegativeReasons": [
      "square nut obstructs wire holes (2x)",
      "screw spins without tightening to retain wire (2x)",
      "wire insertion holes very difficult (2x)",
      "attaching wires very frustrating (2x)",
      "takes good push to get wire in"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Sound Detection Accuracy",
    "categoryType": "Performance",
    "mentions": 16,
    "positiveCount": 1,
    "negativeCount": 15,
    "totalReviews": 16,
    "satisfactionRate": 6.2,
    "negativeRate": 93.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "doesn't detect noises well",
      "doesn't detect noises well especially when near furniture",
      "requires multiple claps to make it work",
      "must clap at exact right speed and volume to get it to work",
      "very loud clap is needed"
    ],
    "topPositiveAspects": [
      "picks up clapping noise easily"
    ],
    "topNegativeReasons": [
      "requires multiple claps to make it work"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Mounting and Installation Hardware",
    "categoryType": "Physical",
    "mentions": 15,
    "positiveCount": 1,
    "negativeCount": 14,
    "totalReviews": 15,
    "satisfactionRate": 6.7,
    "negativeRate": 93.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cheap mounting screws that strip easily",
      "lighter weight screws with low quality metal",
      "screw holes cause misalignment in multi gang boxes",
      "drive is not standard Phillips head but appears to be square",
      "bolts are too short by just a mm"
    ],
    "topPositiveAspects": [
      "cover screws are in the correct area"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Lifespan",
    "categoryType": "Performance",
    "mentions": 131,
    "positiveCount": 9,
    "negativeCount": 122,
    "totalReviews": 131,
    "satisfactionRate": 6.9,
    "negativeRate": 93.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stopped working after 2 months (2x)",
      "need replacement within 2 weeks",
      "poor long-term reliability",
      "Don't appear to last",
      "Only got a year's use"
    ],
    "topPositiveAspects": [
      "reliable after extended use",
      "lasts forever",
      "long-lasting for many years",
      "Will still work in ten years",
      "Quality and durability"
    ],
    "topNegativeReasons": [
      "Cracks after couple years (2x)",
      "Really hard to turn off after 6 months (2x)",
      "cheap materials used (2x)",
      "paddle pops out completely after 8 months (2x)",
      "diodes stopped working (2x)"
    ],
    "topPositiveReasons": [
      "high-quality materials",
      "smooth switching",
      "Quality construction",
      "Quality and durability",
      "easy installation"
    ]
  },
  {
    "category": "Current Leakage",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 1,
    "negativeCount": 9,
    "totalReviews": 10,
    "satisfactionRate": 10.0,
    "negativeRate": 90.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Sends energy to fixture when switched off",
      "LED fixtures receive enough power to flicker when off",
      "leaked voltage with LED bulb",
      "delivers small amount of power to LED lights when off",
      "Current leakage when off"
    ],
    "topPositiveAspects": [
      "no light leakage with LEDs"
    ],
    "topNegativeReasons": [
      "high resistance path to ground"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Basic Power Control",
    "categoryType": "Performance",
    "mentions": 17,
    "positiveCount": 2,
    "negativeCount": 15,
    "totalReviews": 17,
    "satisfactionRate": 11.8,
    "negativeRate": 88.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "only one of the two switches worked",
      "switches did not work - light wouldn't come on",
      "one switch did not work at all",
      "manual control doesn't work",
      "light won't stay on"
    ],
    "topPositiveAspects": [
      "manual control works",
      "on button works fine"
    ],
    "topNegativeReasons": [
      "defective internal mechanism",
      "switch doesn't click smoothly",
      "doesn't turn off right away most of the time",
      "not a really positive click off and on",
      "poor performance turning off lights"
    ],
    "topPositiveReasons": [
      "satisfying click",
      "simple installation"
    ]
  },
  {
    "category": "Smart Home Integration",
    "categoryType": "Performance",
    "mentions": 22,
    "positiveCount": 3,
    "negativeCount": 19,
    "totalReviews": 22,
    "satisfactionRate": 13.6,
    "negativeRate": 86.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "randomly disconnect from WiFi",
      "randomly lose WiFi settings requiring re-setup",
      "lose connection to Internet frequently",
      "always dropping wifi",
      "disconnects then requires deletion and reinstall"
    ],
    "topPositiveAspects": [
      "connects immediately/very easily",
      "seamless wireless and Alexa connection",
      "works with HomeSeer"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Durability",
    "categoryType": "Performance",
    "mentions": 50,
    "positiveCount": 7,
    "negativeCount": 43,
    "totalReviews": 50,
    "satisfactionRate": 14.0,
    "negativeRate": 86.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "buttons break easily",
      "rocker switch stuck to on position",
      "switches broken and flopped in seat",
      "bottom switch broke and fell off after few months with top one cracked",
      "center rocker switch only lasted 11 months with normal usage"
    ],
    "topPositiveAspects": [
      "sturdy",
      "made sturdy to last",
      "sturdy and reliable",
      "long-lasting construction",
      "withstand heavy use from children"
    ],
    "topNegativeReasons": [
      "buttons break easily",
      "rocker switch stuck to on position",
      "switches broken and flopped in seat",
      "screws strip easily",
      "Cheaply made"
    ],
    "topPositiveReasons": [
      "sturdy construction",
      "well made construction",
      "consistent quality across multiple units",
      "sturdy build quality",
      "look nice/great on wall"
    ]
  },
  {
    "category": "LED Flickering Issues",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 1,
    "negativeCount": 6,
    "totalReviews": 7,
    "satisfactionRate": 14.3,
    "negativeRate": 85.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "causes_lights_to_flicker",
      "light flickering"
    ],
    "topPositiveAspects": [
      "light flickering"
    ],
    "topNegativeReasons": [
      "included bulb adapter (4x)",
      "Bluetooth mesh connectivity (4x)",
      "poor_construction_quality (2x)",
      "switches_do_not_stay_in_set_position (2x)"
    ],
    "topPositiveReasons": [
      "included bulb adapter",
      "Bluetooth mesh connectivity"
    ]
  },
  {
    "category": "Cover Plates",
    "categoryType": "Physical",
    "mentions": 19,
    "positiveCount": 3,
    "negativeCount": 16,
    "totalReviews": 19,
    "satisfactionRate": 15.8,
    "negativeRate": 84.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Tab on switch cover breaks off",
      "cheap cover",
      "faceplate color doesn't match the switch",
      "cover plates not included",
      "too thin and flexes during installation"
    ],
    "topPositiveAspects": [
      "wall plate is included",
      "comes with its own wall plate",
      "provides clean finished look"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Indicator Lights",
    "categoryType": "Physical",
    "mentions": 18,
    "positiveCount": 3,
    "negativeCount": 15,
    "totalReviews": 18,
    "satisfactionRate": 16.7,
    "negativeRate": 83.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not bright",
      "light points up against wall",
      "led lamps do not light up",
      "flickering lights"
    ],
    "topPositiveAspects": [
      "very sufficient illumination",
      "bright but not eye-hurting",
      "light illuminates area above switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Material Composition",
    "categoryType": "Physical",
    "mentions": 18,
    "positiveCount": 3,
    "negativeCount": 15,
    "totalReviews": 18,
    "satisfactionRate": 16.7,
    "negativeRate": 83.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "brittle plastic that breaks over time",
      "back black plastic broken",
      "cheaply made and feel it",
      "feel a little cheap",
      "plastic feels good but lighter than expected on paddles"
    ],
    "topPositiveAspects": [
      "Made of quality material",
      "feel like high quality materials",
      "Plastic material"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Operation Mechanism",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 1,
    "negativeCount": 5,
    "totalReviews": 6,
    "satisfactionRate": 16.7,
    "negativeRate": 83.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "rocker rocks in the frame before engaging",
      "rocker function is broken",
      "rocker too firm to push",
      "play in rocker before activation with inconsistent feel",
      "very small up-and-down switch operating range"
    ],
    "topPositiveAspects": [
      "completely silent"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Space Requirements",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 1,
    "negativeCount": 5,
    "totalReviews": 6,
    "satisfactionRate": 16.7,
    "negativeRate": 83.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "won't sit flush",
      "screwless wall plates will NOT fit flush",
      "faceplate doesn't fit",
      "screwless faceplates did not work well",
      "Difficult to fit in small switch boxes"
    ],
    "topPositiveAspects": [
      "Requires careful wire management due to thick construction"
    ],
    "topNegativeReasons": [
      "extended tabs above and below the box (2x)",
      "plastic at the top and bottom like tabs",
      "Snaps in half while tightening screws"
    ],
    "topPositiveReasons": [
      "Thick rear piece"
    ]
  },
  {
    "category": "Physical Switch Controls",
    "categoryType": "Performance",
    "mentions": 11,
    "positiveCount": 2,
    "negativeCount": 9,
    "totalReviews": 11,
    "satisfactionRate": 18.2,
    "negativeRate": 81.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "have to push hard on the top to get it to work",
      "physical switch stopped responding while app still works",
      "will not work manually",
      "fail manual operation",
      "pressing switch has no effect"
    ],
    "topPositiveAspects": [
      "can control manually like normal switch even without internet",
      "works manually but lost smart connectivity"
    ],
    "topNegativeReasons": [
      "stopped working after 2 months",
      "manual switches",
      "hard time connecting to wifi",
      "physical switch",
      "not connecting to WiFi"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Button Operation",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 1,
    "negativeCount": 4,
    "totalReviews": 5,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "mushy buttons that click down but soft when pressed up",
      "difficult to activate buttons requiring multiple touches",
      "button snaps on but soft-closes off without sharp snap",
      "much harder to depress, sometimes needs a thump"
    ],
    "topPositiveAspects": [
      "good sensitivity of push button"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wireless Connectivity",
    "categoryType": "Performance",
    "mentions": 15,
    "positiveCount": 3,
    "negativeCount": 12,
    "totalReviews": 15,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "some switches fail to connect to WiFi system",
      "constantly shows no internet connection despite multiple WiFi networks available",
      "had trouble staying connected",
      "does not work with HomeHub or voice control",
      "frequently drops connections"
    ],
    "topPositiveAspects": [
      "easy to connect to WiFi",
      "easy to connect to wifi",
      "connects without any issues to Alexa"
    ],
    "topNegativeReasons": [
      "model number differences affect compatibility",
      "starts turning on/off continuously after about a year",
      "Button gets stuck at certain angles",
      "Once in a while goes offline"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Switch Reliability",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 1,
    "negativeCount": 4,
    "totalReviews": 5,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "no or intermittent connection",
      "have to flick the switch multiple times to turn light on/off",
      "gets stuck in middle position",
      "not very responsive, sometimes button doesn't work"
    ],
    "topPositiveAspects": [
      "works fine when squeezed"
    ],
    "topNegativeReasons": [
      "lower right corner connection issues",
      "plastic is thin and brittle",
      "high rate of defective units in packaging"
    ],
    "topPositiveReasons": [
      "sturdy"
    ]
  },
  {
    "category": "Cleanability",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 2,
    "negativeCount": 8,
    "totalReviews": 10,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "collects dirt and grime",
      "Difficult to clean",
      "Collects dirt and grime",
      "logo catches dust and grime"
    ],
    "topPositiveAspects": [
      "easy to wipe and keep clean",
      "Much easier to clean"
    ],
    "topNegativeReasons": [
      "Vendor name stamped into the plate (4x)",
      "embossed LEVITON logo on bottom left corner (3x)",
      "raised LEVITON letters on face (3x)",
      "broken plastic parts after a year (3x)",
      "company name impressed into plastic"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Feedback",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 1,
    "negativeCount": 4,
    "totalReviews": 5,
    "satisfactionRate": 20.0,
    "negativeRate": 80.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "produces clicking or slapping noise when operated",
      "Switching mechanism not smooth or easy",
      "Sharp plastic click sound"
    ],
    "topPositiveAspects": [
      "not too loud when used"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Bulb Compatibility",
    "categoryType": "Performance",
    "mentions": 14,
    "positiveCount": 3,
    "negativeCount": 11,
    "totalReviews": 14,
    "satisfactionRate": 21.4,
    "negativeRate": 78.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Does not work with Matter",
      "Requires cloud-based apps",
      "Does not work with lights on GFCI circuit",
      "Causes issues in 4-way switch circuits",
      "requires iPhone for installation"
    ],
    "topPositiveAspects": [
      "Works with standard 3-way switch at other end",
      "bulb compatibility"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Remote Control Range",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 2,
    "negativeCount": 7,
    "totalReviews": 9,
    "satisfactionRate": 22.2,
    "negativeRate": 77.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "only works intermittently at 80 feet",
      "functional distance less than 20 feet",
      "hard time working at 5 feet",
      "range has to be very close at 15 feet",
      "spotty signal at 10 feet"
    ],
    "topPositiveAspects": [
      "works usually at 20 feet with line of sight",
      "works at 30-40 feet but lossy"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Mounting and Installation",
    "categoryType": "Physical",
    "mentions": 18,
    "positiveCount": 4,
    "negativeCount": 14,
    "totalReviews": 18,
    "satisfactionRate": 22.2,
    "negativeRate": 77.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "thick tabs preventing switch plate covers from laying flat",
      "flimsy tabs that are too weak to force outlets flat",
      "tabs that must be snapped off for traditional plates",
      "plastic on tabs interfering with screw tightening",
      "extra plastic on mounting plate causing issues with screwless cover plates"
    ],
    "topPositiveAspects": [
      "Switch can be installed upside down"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Internal Electronics and Components",
    "categoryType": "Physical",
    "mentions": 13,
    "positiveCount": 3,
    "negativeCount": 10,
    "totalReviews": 13,
    "satisfactionRate": 23.1,
    "negativeRate": 76.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Internal relay",
      "overheating issues",
      "internal switch component",
      "battery contact issues",
      "internal connector was bad"
    ],
    "topPositiveAspects": [
      "relay component",
      "Plug cover on the inside",
      "TYWE3S chip in 2021 models"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Button and Switch Operation",
    "categoryType": "Physical",
    "mentions": 13,
    "positiveCount": 3,
    "negativeCount": 10,
    "totalReviews": 13,
    "satisfactionRate": 23.1,
    "negativeRate": 76.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Very short button travel, doesn't feel like quality switch",
      "Large toggle is flimsy feeling",
      "Button gets stuck at certain angles",
      "Both paddles are stiff and require more pressure to turn off",
      "paddle switch"
    ],
    "topPositiveAspects": [
      "superior sound and feel when physically pressed",
      "Nice feel when operated",
      "responsive touch buttons with satisfying tactile experience"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Build Quality Perception",
    "categoryType": "Performance",
    "mentions": 16,
    "positiveCount": 4,
    "negativeCount": 12,
    "totalReviews": 16,
    "satisfactionRate": 25.0,
    "negativeRate": 75.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not contractor-grade",
      "low quality/flimsy design",
      "quality not there",
      "feels cheap",
      "switches have pretty cheap feel compared to other slightly more expensive switches"
    ],
    "topPositiveAspects": [
      "high quality (2x)",
      "leviton quality",
      "higher quality"
    ],
    "topNegativeReasons": [
      "rough and clunky feel",
      "low quality construction",
      "immediate failure",
      "plastic joint in middle erodes and pops out",
      "two terminal bolts installed at an angle, threads stripped when backed out"
    ],
    "topPositiveReasons": [
      "paddle switch design",
      "fits into existing space"
    ]
  },
  {
    "category": "Switch Shape Design",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 1,
    "negativeCount": 3,
    "totalReviews": 4,
    "satisfactionRate": 25.0,
    "negativeRate": 75.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "raised rectangular area around switch",
      "square and sharp switch edges",
      "low profile corners"
    ],
    "topPositiveAspects": [
      "Perfect slim design"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi Switch Coordination",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 1,
    "negativeCount": 3,
    "totalReviews": 4,
    "satisfactionRate": 25.0,
    "negativeRate": 75.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not operate like conventional 3-way switch",
      "main switch must be on for slave switch to function",
      "both switches turn both lights on with no separation of function"
    ],
    "topPositiveAspects": [
      "Does exactly what 3-way switch should do"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Initial Setup Experience",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 5,
    "negativeCount": 14,
    "totalReviews": 19,
    "satisfactionRate": 26.3,
    "negativeRate": 73.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "difficult initial setup process",
      "app kept disconnecting during setup",
      "setup was nightmare",
      "setup challenging despite simple instructions",
      "awfully hard to setup"
    ],
    "topPositiveAspects": [
      "easy to install and connect",
      "easy setup process"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "clear wiring directions and labeling (4x)",
      "four connection wires pre-installed with plenty of slack"
    ]
  },
  {
    "category": "Product Reliability",
    "categoryType": "Performance",
    "mentions": 52,
    "positiveCount": 14,
    "negativeCount": 38,
    "totalReviews": 52,
    "satisfactionRate": 26.9,
    "negativeRate": 73.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "one did not work",
      "immediate failure",
      "couldn't get it to work - immediately trips circuit",
      "Product didn't work",
      "One switch was defective"
    ],
    "topPositiveAspects": [
      "work well (2x)",
      "all switches worked properly",
      "switches worked out wonderfully",
      "good function",
      "work like they should"
    ],
    "topNegativeReasons": [
      "sketchy feel and quality",
      "internal connector was bad",
      "a little loud",
      "defective internal mechanism",
      "low quality capacitor that fails"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Packaging and Documentation",
    "categoryType": "Physical",
    "mentions": 36,
    "positiveCount": 10,
    "negativeCount": 26,
    "totalReviews": 36,
    "satisfactionRate": 27.8,
    "negativeRate": 72.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "no instructions included (2x)",
      "sub-standard quality",
      "do not make neutral wire requirement clear",
      "wiring diagrams done without proper knowledge",
      "covers come together as one unit instead of separate individual covers"
    ],
    "topPositiveAspects": [
      "wire lever nuts included",
      "high quality packaging",
      "impressed with packaging",
      "easy to understand instructions",
      "has wiring diagram right on transmitter"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Sound Level",
    "categoryType": "Performance",
    "mentions": 36,
    "positiveCount": 10,
    "negativeCount": 26,
    "totalReviews": 36,
    "satisfactionRate": 27.8,
    "negativeRate": 72.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Not silent",
      "Loud click, louder than residential version",
      "Very loud clicking sound",
      "Not quiet operation despite product description",
      "makes noise when pressed, sorta makes a loud click sound"
    ],
    "topPositiveAspects": [
      "Quiet operation",
      "No clicking sound",
      "great audible click with authority"
    ],
    "topNegativeReasons": [
      "Very light plastic, does not feel solid",
      "Two switches stopped working",
      "cheap plastic construction"
    ],
    "topPositiveReasons": [
      "Solid construction (8x)"
    ]
  },
  {
    "category": "Installation Experience",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 2,
    "negativeCount": 5,
    "totalReviews": 7,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Frustrating to install",
      "Very difficult to set up",
      "Requires extra space in switch boxes",
      "difficult to install"
    ],
    "topPositiveAspects": [
      "installation is quick",
      "wired up fine with no problems"
    ],
    "topNegativeReasons": [
      "Bulky on the backside (3x)",
      "Lasted about 2 months then died completely (3x)",
      "difficult to plug in thicker wires"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Aesthetic Integration",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 2,
    "negativeCount": 5,
    "totalReviews": 7,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "don't stick out far from switch plate",
      "feel and look low quality",
      "look off when combined with other switches",
      "don't match other brand switches",
      "does not match other brand products"
    ],
    "topPositiveAspects": [
      "look good"
    ],
    "topNegativeReasons": [
      "shorter toggle than standard switches (2x)",
      "shorter and wider than other brands",
      "off-white or bone color rather than pure white"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Network Connection Stability",
    "categoryType": "Performance",
    "mentions": 70,
    "positiveCount": 20,
    "negativeCount": 50,
    "totalReviews": 70,
    "satisfactionRate": 28.6,
    "negativeRate": 71.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "difficult to pair with zwave system",
      "keeps dropping connection",
      "very kludgy procedure for adding to SmartThings",
      "extremely tricky connecting to Ring Alarm",
      "constantly disconnects from Z wave system"
    ],
    "topPositiveAspects": [
      "easy with Smart Things",
      "connects up first time every time",
      "much easier to include and adapt",
      "integrated perfectly in Ring Alarm z-wave setup",
      "Works with Home Assistant via Zigbee correctly for on/off commands"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Audio Feedback",
    "categoryType": "Performance",
    "mentions": 33,
    "positiveCount": 10,
    "negativeCount": 23,
    "totalReviews": 33,
    "satisfactionRate": 30.3,
    "negativeRate": 69.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "loud clicking noise",
      "inconsistent sound levels between units",
      "makes loud click sound",
      "Internal relay clicks pretty loud",
      "Relay click is annoying"
    ],
    "topPositiveAspects": [
      "makes click sound",
      "very secure click",
      "audible click when switching on/off",
      "Clear and loud switching sound",
      "Definitive click sound"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Indicator Lighting",
    "categoryType": "Physical",
    "mentions": 29,
    "positiveCount": 9,
    "negativeCount": 20,
    "totalReviews": 29,
    "satisfactionRate": 31.0,
    "negativeRate": 69.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "indicator light is very dim and hard to see when room lights are on",
      "indicator lights have inconsistent brightness between switches",
      "led not illuminated when dead",
      "blue LED indicator light",
      "courtesy light needs improvements"
    ],
    "topPositiveAspects": [
      "green led light comes on when fan kicks in",
      "blue LED indicator light",
      "moodlight ring can be programmed to come on at sunset and turn off at sunrise",
      "light goes off when you turn the light on",
      "Excellent lighting"
    ],
    "topNegativeReasons": [
      "Very dim brightness (11x)",
      "incorrect and incomplete documentation"
    ],
    "topPositiveReasons": [
      "LED produces white light (4x)",
      "has moodlight ring",
      "fun to change the buttons"
    ]
  },
  {
    "category": "Operational Sound",
    "categoryType": "Physical",
    "mentions": 22,
    "positiveCount": 7,
    "negativeCount": 15,
    "totalReviews": 22,
    "satisfactionRate": 31.8,
    "negativeRate": 68.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "loud click sound",
      "some sound louder than others when turning on/off",
      "click noise when turned on or off",
      "slightly too loud and tinny sounding",
      "noisier than Leviton switches"
    ],
    "topPositiveAspects": [
      "quiet operation",
      "noiselessly",
      "quiet switch tap",
      "Medium click sound level",
      "very quiet when operated"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "high quality, robust, strong",
      "turn lights on and off properly"
    ]
  },
  {
    "category": "WiFi Connectivity",
    "categoryType": "Performance",
    "mentions": 71,
    "positiveCount": 23,
    "negativeCount": 48,
    "totalReviews": 71,
    "satisfactionRate": 32.4,
    "negativeRate": 67.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "fails to connect to wifi",
      "loses connection with WiFi after some time",
      "connection to Alexa worked for a day then would not stay connected",
      "wifi connection fails after 5 months",
      "wifi connectivity constantly disconnects"
    ],
    "topPositiveAspects": [
      "connects to wifi with no problems",
      "connects up with no issues",
      "wifi connectivity is great",
      "really easy to connect to phone",
      "only works on 2.4GHz band"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Hardware Components",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "screws strip easily",
      "overtightened screw ruins item"
    ],
    "topPositiveAspects": [
      "use standard screws and decora plates"
    ],
    "topNegativeReasons": [
      "soft screw heads (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Button Interface",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 2,
    "negativeCount": 4,
    "totalReviews": 6,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "finicky button press location",
      "off button is finicky",
      "buttons lack illumination",
      "pushing button is more annoying than flipping traditional switch"
    ],
    "topPositiveAspects": [
      "tactile feedback and audible click",
      "push button switch design"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Toggle Mechanisms",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 2,
    "negativeCount": 4,
    "totalReviews": 6,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not toggle smoothly",
      "lacks on/off labeling",
      "has clear ring around toggle"
    ],
    "topPositiveAspects": [
      "has solid white toggle",
      "has clear ring around toggle"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Switch Quality",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 4,
    "negativeCount": 8,
    "totalReviews": 12,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "feel of switch action is different in ON vs OFF positions requiring more force to switch off",
      "button action feels cheap and yucky",
      "feeling of rocker switch is a little soft",
      "sliding dimmer-like feel when turning off",
      "rough switching function"
    ],
    "topPositiveAspects": [
      "smooth switching",
      "positive click switching on",
      "positive on/off without loud click",
      "toggle switches work fine"
    ],
    "topNegativeReasons": [
      "plastic paddle switches do not fit well with visible gap in OFF position"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "LED Bulb Compatibility",
    "categoryType": "Performance",
    "mentions": 15,
    "positiveCount": 5,
    "negativeCount": 10,
    "totalReviews": 15,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "causes LED ghosting with 1-2 lights",
      "lights pulsated",
      "does not work with LED bulbs",
      "not compatible with LED bulbs",
      "LED bulbs nearby can cause interference"
    ],
    "topPositiveAspects": [
      "works fine with 4+ LED lights",
      "no flicker at all on LED bulbs",
      "LED compatible",
      "LED load compatibility",
      "works reliably with dimmable LED bulbs"
    ],
    "topNegativeReasons": [
      "delivers small amount of power to LED lights when off"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Multi Switch Configuration",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 4,
    "negativeCount": 8,
    "totalReviews": 12,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "every 3-way in house did not work",
      "can't work with conventional 3-way switch",
      "can be permanently damaged if used with conventional 3-way",
      "inconsistent 3way operation with dumb switch",
      "3-way smart switches don't work with other 3-way smart switches"
    ],
    "topPositiveAspects": [
      "works well in 3way configuration"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Noise Generation",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 4,
    "negativeCount": 8,
    "totalReviews": 12,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "clicks are very loud",
      "very noisy when toggling switch",
      "turning switches on is mechanical hassle and noisier",
      "Bit noisy when pushed by finger",
      "Very loud"
    ],
    "topPositiveAspects": [
      "turning switches off is normal and quiet",
      "Makes slight click when pressed",
      "Switches are quiet",
      "Nice satisfying click"
    ],
    "topNegativeReasons": [
      "Switch operation noise level",
      "Wire connection difficulty",
      "Sharp plastic click sound",
      "Switch flashing on momentarily then going out"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Connectivity Performance",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 2,
    "negativeCount": 4,
    "totalReviews": 6,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "poor homekit integration with updating issues",
      "depends on internet connection and Smartlife services"
    ],
    "topPositiveAspects": [
      "excellent homekit integration"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Button Responsiveness",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 1,
    "negativeCount": 2,
    "totalReviews": 3,
    "satisfactionRate": 33.3,
    "negativeRate": 66.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "hard to turn on, need to press very hard and hold",
      "need to press power button about 10 times"
    ],
    "topPositiveAspects": [
      "easy to turn off once turned on"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Signal Range",
    "categoryType": "Performance",
    "mentions": 23,
    "positiveCount": 8,
    "negativeCount": 15,
    "totalReviews": 23,
    "satisfactionRate": 34.8,
    "negativeRate": 65.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "range doesn't seem as good as Enbrighten",
      "had to move hub to install them",
      "too far away for Hub to pick it up",
      "needs clear path between light and switch",
      "doesn't work 15 feet away near window frame"
    ],
    "topPositiveAspects": [
      "works with no issue at 50 feet range",
      "works well through exterior walls from house 25ft away",
      "works while standing in driveway 100ft away",
      "strong 200FT RF range",
      "remote has good range"
    ],
    "topNegativeReasons": [
      "housing is cumbersome and takes too much space",
      "did not work at all"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Connections",
    "categoryType": "Physical",
    "mentions": 25,
    "positiveCount": 9,
    "negativeCount": 16,
    "totalReviews": 25,
    "satisfactionRate": 36.0,
    "negativeRate": 64.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "identical to three-way version with paper plug",
      "retains common terminal label",
      "bad contact problem",
      "Wire clamps could be designed better as solid core wires can be tricky to be well held",
      "removed screw terminals"
    ],
    "topPositiveAspects": [
      "has side screws and quick hookup options",
      "ground connection is on the top",
      "2 separate Common terminals and a commoning bar",
      "long wire leads",
      "quickwire push-in connection"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Terminals",
    "categoryType": "Physical",
    "mentions": 11,
    "positiveCount": 4,
    "negativeCount": 7,
    "totalReviews": 11,
    "satisfactionRate": 36.4,
    "negativeRate": 63.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "no push-in back wire option, screw terminals only",
      "lower right corner connection issues",
      "difficult to use with 12 gauge wire",
      "terminal_screw_tightening_affects_switch_operation"
    ],
    "topPositiveAspects": [
      "ground screw at bottom",
      "has all the terminals",
      "has a ground screw",
      "easy with 14 gauge wire"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Indicator Light Performance",
    "categoryType": "Performance",
    "mentions": 16,
    "positiveCount": 6,
    "negativeCount": 10,
    "totalReviews": 16,
    "satisfactionRate": 37.5,
    "negativeRate": 62.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "pilot light only lights when load is off",
      "locator light fails to work",
      "barely visible in dark",
      "not visible from side angle"
    ],
    "topPositiveAspects": [
      "bright enough to see in light or dark",
      "bright enough for 110v purposes",
      "lights up brightly",
      "bright enough to be noticeable",
      "provides adequate wayfinding"
    ],
    "topNegativeReasons": [
      "small size (8x)",
      "barely visible in dark (8x)",
      "very dim brightness (7x)",
      "locator light fails to work (7x)"
    ],
    "topPositiveReasons": [
      "bright red light"
    ]
  },
  {
    "category": "Cover Plates and Faceplates",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 3,
    "negativeCount": 5,
    "totalReviews": 8,
    "satisfactionRate": 37.5,
    "negativeRate": 62.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Extremely difficult to snap in place",
      "Thick and extends beyond the switch",
      "cover plate wouldn't snap on due to recessed switches",
      "face plate keeps falling off",
      "cover plates do not fit properly"
    ],
    "topPositiveAspects": [
      "work with other/different wall plates",
      "high quality plate",
      "specialty cover plate ensures perfect alignment"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Operation Feel",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 3,
    "negativeCount": 5,
    "totalReviews": 8,
    "satisfactionRate": 37.5,
    "negativeRate": 62.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "spongy feel in down position",
      "rocker has resistance when pushing",
      "Rocker switch in opposite direction than norm",
      "Switches opposite of typical design",
      "On position like normal switch but light illuminates ceiling"
    ],
    "topPositiveAspects": [
      "good feel in up position with locking",
      "satisfying toggle feel",
      "nice feel flipping on and off"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Long Term Durability",
    "categoryType": "Performance",
    "mentions": 81,
    "positiveCount": 31,
    "negativeCount": 50,
    "totalReviews": 81,
    "satisfactionRate": 38.3,
    "negativeRate": 61.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "uncertain about long-term durability (2x)",
      "engineered to fail after warranty expires (2x)",
      "failed in May after September purchase",
      "device dies after 2 months with unresponsive buttons",
      "stops functioning after few weeks"
    ],
    "topPositiveAspects": [
      "great durability (2x)",
      "so far so good",
      "works great so far",
      "expected to last for several lives of future home owners",
      "keep working over time"
    ],
    "topNegativeReasons": [
      "fails after 2 years",
      "internal switch component",
      "works for 3.5 years then breaks with clicking",
      "thin plastic section across center as weak support",
      "top rocker tab"
    ],
    "topPositiveReasons": [
      "feels sturdy",
      "just works",
      "sturdy build quality",
      "Heavier weight 76g vs residential 47g",
      "quality design"
    ]
  },
  {
    "category": "Indicator Visibility",
    "categoryType": "Performance",
    "mentions": 18,
    "positiveCount": 7,
    "negativeCount": 11,
    "totalReviews": 18,
    "satisfactionRate": 38.9,
    "negativeRate": 61.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "light stays on all the time when wired incorrectly",
      "indicator light hard to see in daylight",
      "pilot light is really dim",
      "signal light so dim not noticeable from distance",
      "not easy to locate in dark room"
    ],
    "topPositiveAspects": [
      "light illuminates only when switch is on when wired correctly",
      "brighter more visible light in newer version",
      "can see the light switch in basement",
      "works well in the dark",
      "can be easily seen in the dark"
    ],
    "topNegativeReasons": [
      "neon light technology",
      "pilot light is really dim",
      "narrow slit design",
      "indicator light hard to see in daylight",
      "toggle is not illuminated"
    ],
    "topPositiveReasons": [
      "lighted surround (2x)",
      "switch works as it should (2x)"
    ]
  },
  {
    "category": "Smart Connectivity",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 4,
    "negativeCount": 6,
    "totalReviews": 10,
    "satisfactionRate": 40.0,
    "negativeRate": 60.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Could not find signal even when other switches connected",
      "Does not reliably report status to app",
      "Disconnects from WiFi frequently",
      "Does not work with Alexa routines",
      "Voice commands disabled when using different switches"
    ],
    "topPositiveAspects": [
      "Works perfectly on MacBook Air",
      "Connects to network easily",
      "Reconnects automatically after power outages",
      "WiFi connection setup issues resolved by changing settings"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wire Connection Mechanisms",
    "categoryType": "Physical",
    "mentions": 42,
    "positiveCount": 17,
    "negativeCount": 25,
    "totalReviews": 42,
    "satisfactionRate": 40.5,
    "negativeRate": 59.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "tight plug insertion requiring force",
      "Screws do not go back in once removed",
      "Only accommodates one wire per connection",
      "Push-in wire slots not holding, slipping back out",
      "Push in quick wire slots not tightening down"
    ],
    "topPositiveAspects": [
      "Made for back wiring",
      "14 AWG wires slide into back easily",
      "12 AWG wires need to be screwed to side mount screws",
      "screw terminals available",
      "push-in holes rated for 14 gauge wire"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Terminal Connections",
    "categoryType": "Physical",
    "mentions": 17,
    "positiveCount": 7,
    "negativeCount": 10,
    "totalReviews": 17,
    "satisfactionRate": 41.2,
    "negativeRate": 58.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "missing ground connection on some switches",
      "earth connection at different places on different switches",
      "top brass term screw missing",
      "top black terminal screw missing",
      "two terminal bolts installed at an angle, threads stripped when backed out"
    ],
    "topPositiveAspects": [
      "screws that are strong and hold wires well",
      "easy grounding screw attachment that clamps down",
      "clearly marked terminals on the back",
      "side screws are easy to turn and tighten",
      "terminal posts with additional guard"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Mechanism",
    "categoryType": "Physical",
    "mentions": 12,
    "positiveCount": 5,
    "negativeCount": 7,
    "totalReviews": 12,
    "satisfactionRate": 41.7,
    "negativeRate": 58.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "squeaks when pushed",
      "spring inside is loud",
      "rocker clicks quite loudly when pressing on/off",
      "three way switch works as single pole",
      "lack_of_resistance_in_switching_mechanism"
    ],
    "topPositiveAspects": [
      "Has satisfying click",
      "good \"click\" as they switch",
      "nice feel to the switch",
      "nice soft operation that is smooth and quiet",
      "nice feeling switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Indicator Lights",
    "categoryType": "Physical",
    "mentions": 12,
    "positiveCount": 5,
    "negativeCount": 7,
    "totalReviews": 12,
    "satisfactionRate": 41.7,
    "negativeRate": 58.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "no status LED",
      "doesn't illuminate when off",
      "not backlit on switch",
      "WiFi indicator light",
      "green light when off and red light when on"
    ],
    "topPositiveAspects": [
      "lighted switch when on",
      "LED indicators can be toggled and aren't too bright",
      "flashing green light during setup",
      "locator/indicator LED",
      "Small light bar on side"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Durability",
    "categoryType": "Performance",
    "mentions": 31,
    "positiveCount": 13,
    "negativeCount": 18,
    "totalReviews": 31,
    "satisfactionRate": 41.9,
    "negativeRate": 58.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Breaks easily and won't last more than 6 months",
      "Cracks develop in paddles within 2 years",
      "Tab breaks off causing switch cover to fly",
      "Handles breaking over time",
      "broke after 2 weeks"
    ],
    "topPositiveAspects": [
      "seems durable (2x)",
      "Used regularly for a year without issues",
      "constant on/off switching without failure",
      "reduced risk of damage over time",
      "adequate for the price"
    ],
    "topNegativeReasons": [
      "plastic parts (3x)",
      "switch has to be slowly pushed to work (3x)",
      "Made of polycarbonate that cracks",
      "Cracks develop in paddles within 2 years",
      "Tab on switch cover breaks off"
    ],
    "topPositiveReasons": [
      "solid construction",
      "constant on/off switching without failure",
      "heavy duty construction",
      "easy to install",
      "rocker switches"
    ]
  },
  {
    "category": "Mobile App Experience",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 8,
    "negativeCount": 11,
    "totalReviews": 19,
    "satisfactionRate": 42.1,
    "negativeRate": 57.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "inferior app with multiple issues",
      "app won't help connect to new Wi-Fi network",
      "app's add-device function won't find the switch",
      "no search function to find device",
      "app is trash, use SmartLife instead"
    ],
    "topPositiveAspects": [
      "easy app & configuration",
      "app setup was quick and simple",
      "easy to add to App",
      "easy setup and use in app",
      "app is easy to use"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Packaging Quality",
    "categoryType": "Physical",
    "mentions": 33,
    "positiveCount": 14,
    "negativeCount": 19,
    "totalReviews": 33,
    "satisfactionRate": 42.4,
    "negativeRate": 57.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Missing small screws for cover plate",
      "box crushed",
      "appears to have been previously used",
      "packaging came busted open",
      "Cracked upon arrival"
    ],
    "topPositiveAspects": [
      "Switch was packaged well and protected",
      "come individually wrapped",
      "well packaged",
      "packaged well",
      "individually packaged"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Consistency",
    "categoryType": "Performance",
    "mentions": 40,
    "positiveCount": 17,
    "negativeCount": 23,
    "totalReviews": 40,
    "satisfactionRate": 42.5,
    "negativeRate": 57.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Only sometimes makes outlet come on",
      "Turns back off after few seconds",
      "Switch continually turns lights on",
      "Turns lights immediately back on when turned off",
      "One of the switches didn't work"
    ],
    "topPositiveAspects": [
      "Operates well",
      "Both switches work independently and as expected",
      "works well with installation",
      "will not randomly toggle",
      "works properly"
    ],
    "topNegativeReasons": [
      "paddle switch (3x)",
      "will not turn on at random times (3x)",
      "wall switch",
      "super hard to pair"
    ],
    "topPositiveReasons": [
      "Well constructed",
      "Nice positive snap when it turns on and off",
      "smooth tactile feel",
      "will not randomly toggle"
    ]
  },
  {
    "category": "Physical Size and Fit",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 3,
    "negativeCount": 4,
    "totalReviews": 7,
    "satisfactionRate": 42.9,
    "negativeRate": 57.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "shorter toggle than standard switches",
      "shorter and wider than other brands",
      "will not fit standard cover plates"
    ],
    "topPositiveAspects": [
      "bigger box size",
      "switch not as long as old switches",
      "little wider than typical standard switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Safety Certifications",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 3,
    "negativeCount": 4,
    "totalReviews": 7,
    "satisfactionRate": 42.9,
    "negativeRate": 57.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not UL approved, only CE approved for European use",
      "Not UL Listed",
      "No safety approvals or certifications"
    ],
    "topPositiveAspects": [
      "UL listing (2x)",
      "UL listed"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Actuation Mechanism",
    "categoryType": "Physical",
    "mentions": 32,
    "positiveCount": 14,
    "negativeCount": 18,
    "totalReviews": 32,
    "satisfactionRate": 43.8,
    "negativeRate": 56.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "operates left and right instead of up and down",
      "scrapes against housing",
      "switch stays in the middle position",
      "flick down turns off lights and returns to middle",
      "not the same as the button it tries to imitate"
    ],
    "topPositiveAspects": [
      "solid switch that isn't loose",
      "Not roller type switch",
      "design forces finger use to flip switch rather than wall slapping",
      "good quality switching mechanisms",
      "has normal size switches rather than thick switches"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "LED Indicator Design",
    "categoryType": "Physical",
    "mentions": 29,
    "positiveCount": 13,
    "negativeCount": 16,
    "totalReviews": 29,
    "satisfactionRate": 44.8,
    "negativeRate": 55.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "tiny pinpoint size",
      "pencil point size",
      "status light on when switch is on, off when switch is off",
      "Light shines from top not bottom"
    ],
    "topPositiveAspects": [
      "white color",
      "green color",
      "positioned above switch",
      "positioned at switch edge",
      "pinhole sized"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Core Switch Operation",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 9,
    "negativeCount": 10,
    "totalReviews": 19,
    "satisfactionRate": 47.4,
    "negativeRate": 52.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "upside down switch operation",
      "can be iffy after a few years",
      "breaker keeps tripping",
      "switch does not turn light on",
      "switches stopped working"
    ],
    "topPositiveAspects": [
      "works as described",
      "solid switching action",
      "good toggle action with appropriate resistance",
      "no doubt when switch is flipped",
      "making better contact than old switches"
    ],
    "topNegativeReasons": [
      "light points up against wall (2x)",
      "defective switches (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Material Quality",
    "categoryType": "Physical",
    "mentions": 10,
    "positiveCount": 5,
    "negativeCount": 5,
    "totalReviews": 10,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "overpriced plastic construction (2x)",
      "Made of cheap plastic",
      "Made of polycarbonate that cracks",
      "cheap plastic construction"
    ],
    "topPositiveAspects": [
      "feels sturdy",
      "good material quality",
      "high quality material",
      "Top quality materials"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Compatibility",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 4,
    "negativeCount": 4,
    "totalReviews": 8,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "makes junction box tight",
      "too recessed in older 2-gang electrical boxes",
      "Switch housing prevents installation in steel boxes",
      "difficult to fit in smaller electrical boxes"
    ],
    "topPositiveAspects": [
      "interlocking design for ideal spacing",
      "alignment feature for side-by-side installation",
      "easily line up with each other when installing",
      "fit together perfectly when using 2 or more side-by-side"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "User Experience",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "difficult plug insertion for weak users"
    ],
    "topPositiveAspects": [
      "easy to use"
    ],
    "topNegativeReasons": [
      "tight plug insertion requiring force"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Build Quality and Construction",
    "categoryType": "Physical",
    "mentions": 14,
    "positiveCount": 7,
    "negativeCount": 7,
    "totalReviews": 14,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "cheaply made",
      "break easily when bumped",
      "poor_construction_quality"
    ],
    "topPositiveAspects": [
      "clean and sharp plastic molding",
      "clear metal work",
      "feels good in hand",
      "heavy_duty_construction",
      "heavy enough to suggest durability"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Physical Feel",
    "categoryType": "Performance",
    "mentions": 22,
    "positiveCount": 11,
    "negativeCount": 11,
    "totalReviews": 22,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "very clicky action feel and sound",
      "feel awkward when flipped",
      "cheap feeling operation",
      "switching action could be smoother",
      "rocker feel could be better due to inconsistent activation"
    ],
    "topPositiveAspects": [
      "crisp switch action, not sloppy",
      "firm and positive toggle action without snap sound",
      "quiet snap on and off, no loud clicking",
      "smooth and quick switch operation",
      "easy to switch on and off smoothly"
    ],
    "topNegativeReasons": [
      "squishy with lot of give before click (2x)",
      "switch and accessories don't match each other (2x)",
      "actuators look and feel cheap with cheaper/weaker plastic and sharp corners (2x)",
      "shorter toggle than standard switches",
      "rocker too firm to push"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Performance",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "weak connections with old switches"
    ],
    "topPositiveAspects": [
      "improved flickering lights"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "screw connections for securing wires"
    ]
  },
  {
    "category": "LED Indicator Function",
    "categoryType": "Performance",
    "mentions": 28,
    "positiveCount": 14,
    "negativeCount": 14,
    "totalReviews": 28,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "center blue light never lights up",
      "LED stopped working after 4 years",
      "LED indicator goes out after few minutes",
      "LED indicator does not work",
      "LED failed after a year"
    ],
    "topPositiveAspects": [
      "LED works in off position",
      "LED provides location in darkness",
      "LED brightness adequate for close range"
    ],
    "topNegativeReasons": [
      "tiny pinpoint size (5x)",
      "LED stopped working after 4 years (5x)",
      "blue center light indicator",
      "manual activation requires multiple attempts"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "LED Compatibility",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 3,
    "negativeCount": 3,
    "totalReviews": 6,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not work with LED lighting",
      "doesn't work well with LED bulbs",
      "LED lights produce interference blocking RF signal"
    ],
    "topPositiveAspects": [
      "Doesn't make Hue lights flash like disco when off",
      "works well with LED lights",
      "Works with LED lights"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Audible Feedback",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not quiet switches",
      "audible click on relay"
    ],
    "topPositiveAspects": [
      "satisfying click when flipped",
      "nice hefty click"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Component Accessories",
    "categoryType": "Physical",
    "mentions": 12,
    "positiveCount": 6,
    "negativeCount": 6,
    "totalReviews": 12,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "missing ceiling piece attached to actual light",
      "included bulb adapter"
    ],
    "topPositiveAspects": [
      "Comes with all screws and wire nuts necessary",
      "included bulb adapter",
      "three separate pieces",
      "comes with ivory paddles"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Light Flickering Issues",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Very noticeable flickering of light",
      "light flickers horribly"
    ],
    "topPositiveAspects": [
      "no flickering",
      "Prevents light flickering"
    ],
    "topNegativeReasons": [
      "flickers",
      "switch stopped staying on after one year"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Wall Plate Design and Aesthetics",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Sandwich style design"
    ],
    "topPositiveAspects": [
      "Clean and modern appearance",
      "Clean look with screws under faceplate"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color Matching and Consistency",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "White does not match other Bestten white products"
    ],
    "topPositiveAspects": [
      "Color matches other switches"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Device Compatibility",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Compatible with LED lights"
    ],
    "topPositiveAspects": [
      "Compatible with LED lights"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Quality",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not dim as claimed"
    ],
    "topPositiveAspects": [
      "dimming feature works flawlessly"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Dimensions and Fit",
    "categoryType": "Physical",
    "mentions": 8,
    "positiveCount": 4,
    "negativeCount": 4,
    "totalReviews": 8,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "thinner than standard white switches",
      "thicker than normal switches",
      "plate smaller than standard size",
      "irregular plate sizes"
    ],
    "topPositiveAspects": [
      "standard size",
      "Larger surface area",
      "fits on a single gang box",
      "compact size"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Memory and Recovery Features",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Firmware update is difficult and unreliable"
    ],
    "topPositiveAspects": [
      "More stable after firmware update"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Noise",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not quiet operation"
    ],
    "topPositiveAspects": [
      "silent switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Response Time",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "slow response taking 30 seconds"
    ],
    "topPositiveAspects": [
      "fast response with Alexa commands"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Reliability",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Contacts not consistent"
    ],
    "topPositiveAspects": [
      "voltage and amp resistance working perfectly"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "User Interface Experience",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 2,
    "negativeCount": 2,
    "totalReviews": 4,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "app uses Asian characters after setup",
      "nothing in app makes sense"
    ],
    "topPositiveAspects": [
      "intuitive and user-friendly app",
      "easy to use app"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "User Interface Design",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 1,
    "negativeCount": 1,
    "totalReviews": 2,
    "satisfactionRate": 50.0,
    "negativeRate": 50.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not easy to operate"
    ],
    "topPositiveAspects": [
      "Easy to use"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Advanced Smart Features",
    "categoryType": "Performance",
    "mentions": 19,
    "positiveCount": 10,
    "negativeCount": 9,
    "totalReviews": 19,
    "satisfactionRate": 52.6,
    "negativeRate": 47.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "only reports on or off",
      "unable to turn off blue LED",
      "does not sense double/triple taps",
      "does not report long holds",
      "voice control disabled"
    ],
    "topPositiveAspects": [
      "function as zigbee routers",
      "work well as zigbee router/repeater",
      "acts as zigbee radio/repeater",
      "provide basic power monitoring",
      "measures wattage"
    ],
    "topNegativeReasons": [
      "blue LED indicator light"
    ],
    "topPositiveReasons": [
      "blue LED indicator light (2x)",
      "pairing easy (2x)"
    ]
  },
  {
    "category": "LED Indicator and Lighting Features",
    "categoryType": "Physical",
    "mentions": 223,
    "positiveCount": 118,
    "negativeCount": 105,
    "totalReviews": 223,
    "satisfactionRate": 52.9,
    "negativeRate": 47.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "narrow slit design",
      "neon light technology",
      "blue center light indicator",
      "blue LED lights on switch buttons",
      "very dim and barely visible"
    ],
    "topPositiveAspects": [
      "red color",
      "blue LED indicates transmitter functioning",
      "has blue light",
      "LED indicators present",
      "bright red light"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Fit",
    "categoryType": "Physical",
    "mentions": 15,
    "positiveCount": 8,
    "negativeCount": 7,
    "totalReviews": 15,
    "satisfactionRate": 53.3,
    "negativeRate": 46.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "plastic paddle switches do not fit well with visible gap in OFF position",
      "switch doesn't sit flush on bottom with wiggle room",
      "gaps at the top",
      "plastic on the switch sticks out and is not flush",
      "doesn't sit flush against wall"
    ],
    "topPositiveAspects": [
      "slim profile and proper fit",
      "perfect alignment and flush finish with specialty cover plate",
      "fits perfectly",
      "good fit",
      "Fits very well"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Material Quality and Durability",
    "categoryType": "Physical",
    "mentions": 26,
    "positiveCount": 14,
    "negativeCount": 12,
    "totalReviews": 26,
    "satisfactionRate": 53.8,
    "negativeRate": 46.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Very light plastic, does not feel solid",
      "Cracks after couple years",
      "lower-grade plastic",
      "made of flimsy cheap plastic",
      "all plastic construction"
    ],
    "topPositiveAspects": [
      "Quality materials (2x)",
      "Great quality plastic",
      "high-quality materials",
      "Made of durable material",
      "made of durable and sturdy solid steel"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Sensor Performance",
    "categoryType": "Performance",
    "mentions": 13,
    "positiveCount": 7,
    "negativeCount": 6,
    "totalReviews": 13,
    "satisfactionRate": 53.8,
    "negativeRate": 46.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Sometimes walking past makes light come on",
      "Light sensor not good, turns on at 3pm",
      "Motion detectors not working",
      "Sensors not working",
      "sensor sometimes activates from walking past"
    ],
    "topPositiveAspects": [
      "Photocell works well",
      "Day/night sensor is sensitive",
      "ambient light sensor minimizes unnecessary operation",
      "sensor shuts off when light pointed at it",
      "LED light direction affects behavior"
    ],
    "topNegativeReasons": [
      "light flickers horribly",
      "Switch fails to hold in on position"
    ],
    "topPositiveReasons": [
      "day/night sensor (tiny hole) is sensitive (2x)",
      "Has LED indicator light (2x)",
      "User and installer friendly (2x)",
      "Little hole for photocell sensor",
      "Perfect brightness"
    ]
  },
  {
    "category": "LED Illumination Performance",
    "categoryType": "Physical",
    "mentions": 42,
    "positiveCount": 23,
    "negativeCount": 19,
    "totalReviews": 42,
    "satisfactionRate": 54.8,
    "negativeRate": 45.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Not bright enough/dim illumination",
      "Non-uniform light distribution with shadows",
      "Always illuminated without adjustment",
      "Does not illuminate at all",
      "Brightness level varies from very bright to extremely dim"
    ],
    "topPositiveAspects": [
      "White LED color instead of orange",
      "Gentle/appropriate brightness level",
      "Brightness level varies from very bright to extremely dim",
      "Cool white/6000K color temperature",
      "Minimal flickering present"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Rocker Switch Mechanisms",
    "categoryType": "Physical",
    "mentions": 9,
    "positiveCount": 5,
    "negativeCount": 4,
    "totalReviews": 9,
    "satisfactionRate": 55.6,
    "negativeRate": 44.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "plastic is thin and brittle",
      "plastic hinge breaks off easily",
      "squishy with lot of give before click",
      "rocker switch breaks"
    ],
    "topPositiveAspects": [
      "wider switch paddle",
      "Thick/fat switch levers",
      "Spring function for the two rocker switches are very good"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Tactile and Audio Feedback",
    "categoryType": "Physical",
    "mentions": 9,
    "positiveCount": 5,
    "negativeCount": 4,
    "totalReviews": 9,
    "satisfactionRate": 55.6,
    "negativeRate": 44.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "hollow click sound during operation",
      "high resistance when toggling",
      "Switch operation noise level",
      "click sound"
    ],
    "topPositiveAspects": [
      "has audible click",
      "satisfying click",
      "very good springy pop in up or down position",
      "definite tactile feedback when operating",
      "smooth switch operation"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Noise Issues",
    "categoryType": "Performance",
    "mentions": 21,
    "positiveCount": 12,
    "negativeCount": 9,
    "totalReviews": 21,
    "satisfactionRate": 57.1,
    "negativeRate": 42.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Makes loud clicking/snapping sounds",
      "makes loud noise when pushing",
      "makes too much noise when pushing",
      "Not quiet, clicks",
      "Gross soft clump sound"
    ],
    "topPositiveAspects": [
      "quiet operation (2x)",
      "low noise when clicked",
      "Audible click sound but acceptable",
      "Strong/solid snap action",
      "silent operation"
    ],
    "topNegativeReasons": [
      "Soft bump feeling instead of click",
      "Soft clump sound and wet cardboard thud when activated"
    ],
    "topPositiveReasons": [
      "Thick/fat switch levers (3x)"
    ]
  },
  {
    "category": "Power Management",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 4,
    "negativeCount": 3,
    "totalReviews": 7,
    "satisfactionRate": 57.1,
    "negativeRate": 42.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "very sensitive to voltage fluctuations",
      "does not work after power outage",
      "switches become dead after internet outage"
    ],
    "topPositiveAspects": [
      "Draw very low vampire power",
      "good power outage recovery",
      "Handled amperage that previous switch couldn't without getting warm",
      "No overheating issues"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "20 amp switch capability",
      "No overheating issues",
      "Simple yet positive wire connections to screw/plates"
    ]
  },
  {
    "category": "Tactile Feedback",
    "categoryType": "Performance",
    "mentions": 31,
    "positiveCount": 18,
    "negativeCount": 13,
    "totalReviews": 31,
    "satisfactionRate": 58.1,
    "negativeRate": 41.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Clicked weird",
      "Soft switch feel",
      "No distinct click feedback",
      "Requires firm press",
      "Mushy feel"
    ],
    "topPositiveAspects": [
      "Solid and quiet feel when pushed",
      "Nice positive snap when it turns on and off",
      "Feels good",
      "Solid feeling",
      "Softer solid sounding click"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "Spring function for the two rocker switches are very good",
      "Well constructed",
      "Nice positive snap when it turns on and off",
      "Good construction",
      "Feels good"
    ]
  },
  {
    "category": "Light Output Quality",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 7,
    "negativeCount": 5,
    "totalReviews": 12,
    "satisfactionRate": 58.3,
    "negativeRate": 41.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Light blinds when illuminating ceiling",
      "Does not illuminate space in wide angle",
      "Functions only as switch locator not nightlight"
    ],
    "topPositiveAspects": [
      "Shines up or down",
      "Projects light up wall and reflects off ceiling",
      "Light illuminates ground when mounted upside down",
      "Provides enough light for navigation in dark",
      "Provides subtle lighting for small room"
    ],
    "topNegativeReasons": [
      "LED lights are not very bright (4x)"
    ],
    "topPositiveReasons": [
      "LED lights provide illumination when switch is off (4x)",
      "LEDs located in top of switch toggle (2x)",
      "Light mounted on top edge of switch",
      "LEDs not too bright at night but visible in dark"
    ]
  },
  {
    "category": "Illumination Performance",
    "categoryType": "Performance",
    "mentions": 53,
    "positiveCount": 31,
    "negativeCount": 22,
    "totalReviews": 53,
    "satisfactionRate": 58.5,
    "negativeRate": 41.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "too bright for bedrooms",
      "way too bright for sleeping areas",
      "not as bright as expected",
      "barely visible in dark",
      "extremely low illumination"
    ],
    "topPositiveAspects": [
      "perfect for hallways",
      "nicely lit",
      "not bright but easy to see in dark hall",
      "not bright at all and shouldn't be",
      "bright enough to easily see from across room"
    ],
    "topNegativeReasons": [
      "illumination is barely visible (7x)",
      "has tiny dot of light behind switch (7x)",
      "light barely shows around switch (7x)",
      "dim uneven light that pulses/flickers (7x)",
      "light portion is very dim (7x)"
    ],
    "topPositiveReasons": [
      "LED produces white light (10x)",
      "glows in the dark when in off position (3x)",
      "works as intended (3x)",
      "soft dim glow (2x)",
      "neon bulb light (2x)"
    ]
  },
  {
    "category": "Physical Dimensions",
    "categoryType": "Physical",
    "mentions": 10,
    "positiveCount": 6,
    "negativeCount": 4,
    "totalReviews": 10,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "sticks out 3/4 inch from wall",
      "mounting/housing needs to be wider to fully cover existing box",
      "chunky size requiring big switch box",
      "will not fit in super shallow wall box"
    ],
    "topPositiveAspects": [
      "Lightweight",
      "Compact size that doesn't take much space in electrical box",
      "perfect fit",
      "perfect size",
      "fits in average sized electrical box"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Response Performance",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 3,
    "negativeCount": 2,
    "totalReviews": 5,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Alexa may say okay but nothing happens until later maybe",
      "Smartthings app tries to turn switch on or off and sometimes does eventually"
    ],
    "topPositiveAspects": [
      "works flawless every time with hubitat",
      "state is controllable via Alexa",
      "on/off time is almost instant"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Power Capacity",
    "categoryType": "Performance",
    "mentions": 10,
    "positiveCount": 6,
    "negativeCount": 4,
    "totalReviews": 10,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "bogus 15a rating performance",
      "suitable only for LEDs, not heavy load",
      "only 120 watts for ceiling fans",
      "fine for lighting but not strong enough for motors or appliances"
    ],
    "topPositiveAspects": [
      "works well on 15 amp circuit",
      "works well in 220V areas",
      "handles high-amp bathroom fan/heater load",
      "handles large loads at 120 volts",
      "handles 16 amp infrared heater"
    ],
    "topNegativeReasons": [
      "15a current rating",
      "burns out after 4 years",
      "lacks sturdiness in build",
      "requires extra pressure to overcome the detent"
    ],
    "topPositiveReasons": [
      "20 amp rating (4x)"
    ]
  },
  {
    "category": "Safety Performance",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 12,
    "negativeCount": 8,
    "totalReviews": 20,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Vulnerable to static electricity",
      "Shorted out and tripped breaker after three weeks",
      "fire hazard",
      "Internal arcing/sparking",
      "arcing after install with pop and flash"
    ],
    "topPositiveAspects": [
      "UL certified",
      "safer installation",
      "safer by not exposing hot contacts",
      "definitely faster and safer",
      "safety features with no exposed wires or screws"
    ],
    "topNegativeReasons": [
      "drive is not standard Phillips head but appears to be square"
    ],
    "topPositiveReasons": [
      "UL listing"
    ]
  },
  {
    "category": "Switch Mechanism Feel",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 3,
    "negativeCount": 2,
    "totalReviews": 5,
    "satisfactionRate": 60.0,
    "negativeRate": 40.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "rough and clunky feel",
      "Stiffer operation compared to 3-way switches"
    ],
    "topPositiveAspects": [
      "smooth tactile feel",
      "clean feel",
      "Sturdy feel when switching"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wiring Configuration and Connections",
    "categoryType": "Physical",
    "mentions": 121,
    "positiveCount": 74,
    "negativeCount": 47,
    "totalReviews": 121,
    "satisfactionRate": 61.2,
    "negativeRate": 38.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "requires neutral wire (2x)",
      "short wire length",
      "thin wire gauge",
      "16 gauge wires on transmitter",
      "wire connectors not up to code"
    ],
    "topPositiveAspects": [
      "requires neutral wire (3x)",
      "Requires neutral wire connection (2x)",
      "requires neutral wire connection",
      "levers on back to secure wires",
      "push in connectors with lever lock"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Size and Fit",
    "categoryType": "Physical",
    "mentions": 78,
    "positiveCount": 48,
    "negativeCount": 30,
    "totalReviews": 78,
    "satisfactionRate": 61.5,
    "negativeRate": 38.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "bulky and sometimes tight fit",
      "huge size requiring wallplate compatibility check",
      "too big for standard wall plates to cover",
      "Larger than standard non-smart switch",
      "Big to set in a crowded box"
    ],
    "topPositiveAspects": [
      "perfect fit (2x)",
      "small size",
      "compact design",
      "very small footprint for both parts",
      "extremely compact design"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color and Finish",
    "categoryType": "Physical",
    "mentions": 21,
    "positiveCount": 13,
    "negativeCount": 8,
    "totalReviews": 21,
    "satisfactionRate": 61.9,
    "negativeRate": 38.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "stark white color vs off-white decor",
      "off-white or bone color rather than pure white",
      "almond color instead of advertised white",
      "cream color",
      "ivory paddle slightly lighter shade than other switches"
    ],
    "topPositiveAspects": [
      "white toggle with ivory body",
      "color matches nicely",
      "available in black color",
      "ivory switch paddle included",
      "bone/white switches included"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Fit",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 5,
    "negativeCount": 3,
    "totalReviews": 8,
    "satisfactionRate": 62.5,
    "negativeRate": 37.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "prevents switch plate covers from laying flat",
      "causes gap with screwless face plates",
      "standard wall plates won't cover properly"
    ],
    "topPositiveAspects": [
      "works with screwless wall plates after breaking tabs",
      "saves space in switch box",
      "receiver fits in existing canopy",
      "fits perfectly into wall plate"
    ],
    "topNegativeReasons": [
      "thick tabs preventing switch plate covers from laying flat",
      "extra plastic on mounting plate causing issues with screwless cover plates",
      "concern about push-in connection reliability over time",
      "too big for standard wall plates to cover"
    ],
    "topPositiveReasons": [
      "no exposed wires or contacts",
      "extremely compact design",
      "worked line a charm"
    ]
  },
  {
    "category": "Physical Controls",
    "categoryType": "Performance",
    "mentions": 24,
    "positiveCount": 15,
    "negativeCount": 9,
    "totalReviews": 24,
    "satisfactionRate": 62.5,
    "negativeRate": 37.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not great feedback",
      "Stiff operation initially",
      "doesn't feel as premium as single switches",
      "need to press very hard",
      "switch has to be slowly pushed to work"
    ],
    "topPositiveAspects": [
      "prevents accidental operation",
      "tight positive action",
      "nice tight action",
      "good feeling throw when flipping on and off",
      "operation is easier and smoother"
    ],
    "topNegativeReasons": [
      "hollow click sound during operation",
      "high resistance when toggling",
      "installation challenges in older boxes",
      "doesn't feel as premium as single switches"
    ],
    "topPositiveReasons": [
      "heavy-duty build (2x)",
      "very quiet when operated (2x)",
      "audible click when switching on/off (2x)",
      "definite tactile feedback when operating",
      "prevents accidental operation"
    ]
  },
  {
    "category": "Wire Connection",
    "categoryType": "Performance",
    "mentions": 14,
    "positiveCount": 9,
    "negativeCount": 5,
    "totalReviews": 14,
    "satisfactionRate": 64.3,
    "negativeRate": 35.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "concern about push-in connection reliability over time",
      "shark bite connections are pain to take apart",
      "more time to configure with screw terminals",
      "12 AWG installation more cumbersome"
    ],
    "topPositiveAspects": [
      "secure wire connection",
      "no exposed wires or contacts",
      "eliminates need for wire bending and j-hooks",
      "rock solid connection that withstands pulling",
      "makes connection secure and easier to wire"
    ],
    "topNegativeReasons": [
      "only supports 14 AWG push-in, not 12 AWG",
      "makes loud noise when pushing"
    ],
    "topPositiveReasons": [
      "push in connectors with lever lock",
      "locking levers to grasp copper",
      "terminal posts with additional guard"
    ]
  },
  {
    "category": "System Response Speed",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 13,
    "negativeCount": 7,
    "totalReviews": 20,
    "satisfactionRate": 65.0,
    "negativeRate": 35.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "wifi switches slower to respond",
      "Not as fast as other switches, takes half second to react",
      "slow response to voice commands",
      "slow speed to respond to remote clicks",
      "slight delay in turning on"
    ],
    "topPositiveAspects": [
      "react instantly",
      "super responsive",
      "responsive and quick",
      "instantaneous response",
      "much quicker switching"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Installation Fit",
    "categoryType": "Performance",
    "mentions": 26,
    "positiveCount": 17,
    "negativeCount": 9,
    "totalReviews": 26,
    "satisfactionRate": 65.4,
    "negativeRate": 34.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "doesn't fit in 2-3 1 gang fittings",
      "gets fairly tight in the box with extra length of wire",
      "fitting into electrical box is challenging",
      "hardest task is fitting back into electrical box",
      "installation challenges in older boxes"
    ],
    "topPositiveAspects": [
      "fits perfectly (2x)",
      "fits perfectly in box",
      "fit well",
      "fits great in existing setup",
      "Good fit"
    ],
    "topNegativeReasons": [
      "large back/housing that is difficult to fit in electrical boxes (2x)",
      "randomly disconnect from WiFi (2x)",
      "thicker than normal switches (2x)",
      "removed screw terminals",
      "takes up a lot of room in the box"
    ],
    "topPositiveReasons": [
      "small size makes it easy to fit into electrical box (2x)",
      "works really well (2x)",
      "standard dimensions (2x)",
      "compact size",
      "compact body size"
    ]
  },
  {
    "category": "Installation Process Difficulty",
    "categoryType": "Performance",
    "mentions": 32,
    "positiveCount": 21,
    "negativeCount": 11,
    "totalReviews": 32,
    "satisfactionRate": 65.6,
    "negativeRate": 34.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "50/50 chance of correct orientation",
      "requires upside down installation for proper operation",
      "difficult to screw straight into plate covers",
      "requires some skill to install receiver",
      "installation was an issue because learn button gets bumped"
    ],
    "topPositiveAspects": [
      "simple wire setup",
      "Requires attention to wiring configuration differences",
      "installing was super easy",
      "wired in easily",
      "installation simple"
    ],
    "topNegativeReasons": [
      "lacks on/off labeling (2x)",
      "identical to three-way version with paper plug (2x)",
      "learn button can easily get bumped by wires",
      "defective from origin",
      "TOP engraved in metal in tiny print"
    ],
    "topPositiveReasons": [
      "Inputs on left side, outputs on right side",
      "Different wiring than standard switches",
      "back terminals very easy to use",
      "switch is very smooth with definitive click",
      "flip down wire clamps for installation"
    ]
  },
  {
    "category": "Wiring Configuration",
    "categoryType": "Physical",
    "mentions": 9,
    "positiveCount": 6,
    "negativeCount": 3,
    "totalReviews": 9,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Has holes on the back for hookup",
      "Ground terminal is hard to work with",
      "has 5 stranded wires with wire nuts"
    ],
    "topPositiveAspects": [
      "both screws and push-in connections on the back",
      "requires neutral wire for installation",
      "Metal tab for different switching arrangements",
      "Slightly different wiring configuration than other brands",
      "requires neutral wire"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Response Speed",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 2,
    "negativeCount": 1,
    "totalReviews": 3,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "delayed response"
    ],
    "topPositiveAspects": [
      "light turns on instantly without delay",
      "quickly turns light off/on"
    ],
    "topNegativeReasons": [
      "couldn't handle 30 inches distance"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Device Compatibility",
    "categoryType": "Performance",
    "mentions": 15,
    "positiveCount": 10,
    "negativeCount": 5,
    "totalReviews": 15,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Not compatible with SmartThings",
      "fails to connect to Alexa",
      "not compatible with anything",
      "requires re-installing on hub every time power is lost"
    ],
    "topPositiveAspects": [
      "Works with voice control",
      "Integrates with Alexa easily",
      "Works with Alexa and Google",
      "Support matter",
      "works with SmartThings"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "has normal size switches rather than thick switches",
      "works as expected"
    ]
  },
  {
    "category": "Specialized Components",
    "categoryType": "Physical",
    "mentions": 12,
    "positiveCount": 8,
    "negativeCount": 4,
    "totalReviews": 12,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "doesn't take 3 prong plugs",
      "No strain relief feature",
      "Clear switch bat material",
      "learn button can easily get bumped by wires"
    ],
    "topPositiveAspects": [
      "has two outlets",
      "second and third sockets function differently",
      "away mode will trigger with any noise",
      "Little hole for photocell sensor",
      "Day/night sensor tiny hole in switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Wire Configuration",
    "categoryType": "Physical",
    "mentions": 9,
    "positiveCount": 6,
    "negativeCount": 3,
    "totalReviews": 9,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "six inch braided aluminum wire for neutral",
      "Screw colors don't match standard",
      "All wires on same side when flipped"
    ],
    "topPositiveAspects": [
      "requires four wires",
      "Inputs on left side, outputs on right side",
      "Different wiring than standard switches",
      "direction of wires labels with different colors are clear"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Internal Components",
    "categoryType": "Physical",
    "mentions": 15,
    "positiveCount": 10,
    "negativeCount": 5,
    "totalReviews": 15,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "has a lot of pieces inside",
      "thin plastic section across center as weak support",
      "rocker tab inside held by center plastic",
      "top rocker tab",
      "Toggle component"
    ],
    "topPositiveAspects": [
      "has side pieces that need to be snipped to separate switches",
      "posts are offset on opposite sides",
      "rocks side to side",
      "metal tab connecting the two switches",
      "opposite ON positions for top and bottom switches"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Light Sensor Functionality",
    "categoryType": "Physical",
    "mentions": 6,
    "positiveCount": 4,
    "negativeCount": 2,
    "totalReviews": 6,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Sensor requires a lot of light to keep nightlight off",
      "Sensor sensitivity cannot be adjusted"
    ],
    "topPositiveAspects": [
      "Has light sensor that turns off nightlight during day",
      "day/night sensor (tiny hole) is sensitive"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Home Connectivity",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 2,
    "negativeCount": 1,
    "totalReviews": 3,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Bluetooth mesh connectivity"
    ],
    "topPositiveAspects": [
      "is mesh WiFi booster and integrates well with eero WiFi mesh system",
      "Bluetooth mesh connectivity"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Remote Control Functionality",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 2,
    "negativeCount": 1,
    "totalReviews": 3,
    "satisfactionRate": 66.7,
    "negativeRate": 33.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "inconsistent response to voice commands"
    ],
    "topPositiveAspects": [
      "can control with Alexa when manual switches fail",
      "WiFi control still works when physical switch fails"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Appearance and Aesthetics",
    "categoryType": "Physical",
    "mentions": 150,
    "positiveCount": 101,
    "negativeCount": 49,
    "totalReviews": 150,
    "satisfactionRate": 67.3,
    "negativeRate": 32.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "color does not match other BESTTEN switches",
      "appears gray instead of white",
      "looks slightly different from other switches",
      "Wrong color",
      "Vendor name stamped into the plate"
    ],
    "topPositiveAspects": [
      "nice looking (5x)",
      "good appearance (3x)",
      "modern look (3x)",
      "attractive appearance (2x)",
      "modern looking (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Build Quality",
    "categoryType": "Performance",
    "mentions": 37,
    "positiveCount": 25,
    "negativeCount": 12,
    "totalReviews": 37,
    "satisfactionRate": 67.6,
    "negativeRate": 32.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Not sturdy",
      "Low quality",
      "built so poorly, concerned about breaking",
      "terminal contacts break when tightening screws",
      "contact broke off during installation"
    ],
    "topPositiveAspects": [
      "good quality (2x)",
      "Well built",
      "Built well",
      "High quality",
      "Great quality"
    ],
    "topNegativeReasons": [
      "flimsy terminals that never tighten up properly (2x)",
      "disconnects then requires deletion and reinstall (2x)",
      "Made of cheap plastic",
      "Breaks easily and won't last more than 6 months",
      "wire attachment plates that deform and slide out of place"
    ],
    "topPositiveReasons": [
      "spot on build quality",
      "Plug cover on the inside",
      "solid and well-made construction",
      "top quality",
      "satisfying click"
    ]
  },
  {
    "category": "Physical Installation",
    "categoryType": "Performance",
    "mentions": 22,
    "positiveCount": 15,
    "negativeCount": 7,
    "totalReviews": 22,
    "satisfactionRate": 68.2,
    "negativeRate": 31.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "more pain to install due to no back wire option",
      "need to make loop and use screw for wires",
      "difficult to handle for beginners",
      "incredibly frustrating to install",
      "installation was a bit of a struggle with wiring"
    ],
    "topPositiveAspects": [
      "straightforward installation (4x)",
      "easy to put on",
      "simple to install",
      "easy installation",
      "simple to wire up"
    ],
    "topNegativeReasons": [
      "no push-in back wire option, screw terminals only (2x)",
      "very clicky action feel and sound (2x)",
      "LED light way too dark, unable to see anything (2x)",
      "screws recede into housing",
      "wire insertion holes very difficult"
    ],
    "topPositiveReasons": [
      "well manufactured",
      "switches worked out wonderfully",
      "works flawlessly",
      "clearly marked terminals on the back",
      "straightforward installation"
    ]
  },
  {
    "category": "Color and Finish Options",
    "categoryType": "Physical",
    "mentions": 65,
    "positiveCount": 45,
    "negativeCount": 20,
    "totalReviews": 65,
    "satisfactionRate": 69.2,
    "negativeRate": 30.8,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "doesn't match existing switches",
      "Matte finish looks and feels like unfinished plastic",
      "not real white",
      "light almond instead of white",
      "brown switches"
    ],
    "topPositiveAspects": [
      "bright white color (2x)",
      "black color",
      "gloss black finish",
      "true white color",
      "glossy white finish adds clean, modern touch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Reliability",
    "categoryType": "Performance",
    "mentions": 24,
    "positiveCount": 17,
    "negativeCount": 7,
    "totalReviews": 24,
    "satisfactionRate": 70.8,
    "negativeRate": 29.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "not dependable when out of town",
      "making clicking sound, light going on and off",
      "started to click and went bad",
      "turn off by themselves, flickering on and off",
      "light no longer turns off, only dims"
    ],
    "topPositiveAspects": [
      "function very well",
      "operates well",
      "all worked just fine",
      "solid operation without turning on/off by barely a touch",
      "works perfectly"
    ],
    "topNegativeReasons": [
      "large back/housing that is difficult to fit in electrical boxes",
      "randomly disconnect from WiFi"
    ],
    "topPositiveReasons": [
      "solid switch that isn't loose"
    ]
  },
  {
    "category": "Device Pairing",
    "categoryType": "Performance",
    "mentions": 28,
    "positiveCount": 20,
    "negativeCount": 8,
    "totalReviews": 28,
    "satisfactionRate": 71.4,
    "negativeRate": 28.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "pairing is extremely difficult",
      "very hard to get controller to pair",
      "don't want to pair",
      "took a couple of retries due to odd Z-Wave security failure",
      "discovery with Alexa difficult"
    ],
    "topPositiveAspects": [
      "paired straight away",
      "switch synced quickly",
      "pairing was easy and straightforward",
      "pairs up fast",
      "easy to connect to smart home system"
    ],
    "topNegativeReasons": [
      "terrible instructions provided",
      "don't want to pair"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Responsiveness",
    "categoryType": "Performance",
    "mentions": 14,
    "positiveCount": 10,
    "negativeCount": 4,
    "totalReviews": 14,
    "satisfactionRate": 71.4,
    "negativeRate": 28.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "makes loud clicking sound and motion is gritty",
      "possible to leave in partially-on position",
      "little stiff but assuming because it's new",
      "Switch direction feels weird"
    ],
    "topPositiveAspects": [
      "switch is very smooth with definitive click",
      "very audibly clicks and crisp action",
      "nice positive click",
      "rocker function clicks well when pressed",
      "normal switch sound when pushed"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "Definitive click sound (2x)",
      "lever terminals for quiet and smooth operation",
      "ease of installing switches"
    ]
  },
  {
    "category": "Functional Reliability",
    "categoryType": "Performance",
    "mentions": 122,
    "positiveCount": 88,
    "negativeCount": 34,
    "totalReviews": 122,
    "satisfactionRate": 72.1,
    "negativeRate": 27.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "switch did not work (2x)",
      "didn't work (2x)",
      "stopped working properly after a couple months",
      "work correctly only sometimes",
      "become unavailable multiple times daily"
    ],
    "topPositiveAspects": [
      "worked perfectly (7x)",
      "easy to use (3x)",
      "working fine (2x)",
      "held up to description and worked flawlessly",
      "functions as expected"
    ],
    "topNegativeReasons": [
      "rocker switch breaks",
      "will not stay on",
      "rocker function is broken",
      "four of the ten don't work",
      "cheap plastic feel"
    ],
    "topPositiveReasons": [
      "paddle design is smooth (2x)",
      "easy operation (2x)",
      "paddle rocker design",
      "single power input with three outputs",
      "well made"
    ]
  },
  {
    "category": "Night Light Features",
    "categoryType": "Physical",
    "mentions": 22,
    "positiveCount": 16,
    "negativeCount": 6,
    "totalReviews": 22,
    "satisfactionRate": 72.7,
    "negativeRate": 27.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "light brightness appropriate for nighttime",
      "light always stays on",
      "light color is green",
      "only upper left corner lights up",
      "light is very dim when toggle is off"
    ],
    "topPositiveAspects": [
      "has illuminated border/surround",
      "provides white light",
      "light brightness appropriate for nighttime"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Installation Process",
    "categoryType": "Performance",
    "mentions": 44,
    "positiveCount": 32,
    "negativeCount": 12,
    "totalReviews": 44,
    "satisfactionRate": 72.7,
    "negativeRate": 27.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "installation lacks clear markings and instructions",
      "switch plate cover doesn't sit flat",
      "tricky to install if wall box already full",
      "could not fit into metal single gang boxes",
      "installation more complicated due to neutral wire requirement"
    ],
    "topPositiveAspects": [
      "great fit",
      "made for ease of accurate and safe installation",
      "easy to install",
      "super easy to install",
      "quick replacement in less than 10 minutes"
    ],
    "topNegativeReasons": [
      "deep/large size requiring spacious wall boxes (2x)",
      "100% failure rate within 60 days (2x)",
      "plastic housing with retaining bracket (2x)",
      "riveted retaining bracket in rear center (2x)",
      "plastic retaining clips for top and bottom bindings (2x)"
    ],
    "topPositiveReasons": [
      "single power input with three outputs",
      "Decora style design",
      "Works perfectly"
    ]
  },
  {
    "category": "Network Connectivity",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 6,
    "negativeCount": 2,
    "totalReviews": 8,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Could not connect to app or HomeKit",
      "fails to connect to router"
    ],
    "topPositiveAspects": [
      "Easy pairing with dual band router at 2.4GHz",
      "WiFi connection seamless to establish",
      "WiFi connection remarkably stable without drops",
      "Easy to connect to internet",
      "Easily connects with wifi system"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "Leviton brand",
      "Easy pairing with dual band router at 2.4GHz"
    ]
  },
  {
    "category": "App Performance",
    "categoryType": "Performance",
    "mentions": 20,
    "positiveCount": 15,
    "negativeCount": 5,
    "totalReviews": 20,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Ads added to app",
      "slow on app",
      "app functionality",
      "doesn't work with Smart Life",
      "requires Tapo app for firmware updates"
    ],
    "topPositiveAspects": [
      "App works great",
      "App very easy to use",
      "App works well",
      "app functionality",
      "works well with Tapo app"
    ],
    "topNegativeReasons": [
      "Cync app interface",
      "bulb compatibility"
    ],
    "topPositiveReasons": [
      "Cync app interface",
      "bulb compatibility"
    ]
  },
  {
    "category": "Sensor Functionality",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 3,
    "negativeCount": 1,
    "totalReviews": 4,
    "satisfactionRate": 75.0,
    "negativeRate": 25.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Sensor activates with slight shading"
    ],
    "topPositiveAspects": [
      "Light turns off when main light is on",
      "Light sensor activates properly in dark conditions"
    ],
    "topNegativeReasons": [
      "Sensor requires a lot of light to keep nightlight off"
    ],
    "topPositiveReasons": [
      "Has light sensor that turns off nightlight during day (2x)"
    ]
  },
  {
    "category": "Build Quality and Materials",
    "categoryType": "Physical",
    "mentions": 185,
    "positiveCount": 144,
    "negativeCount": 41,
    "totalReviews": 185,
    "satisfactionRate": 77.8,
    "negativeRate": 22.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Cheaply made (2x)",
      "cheaply built (2x)",
      "Cheap circuitry that doesn't hold up",
      "cheap appearance",
      "doesn't scream high-quality"
    ],
    "topPositiveAspects": [
      "well made (6x)",
      "good quality (4x)",
      "well made construction (3x)",
      "Good quality construction (3x)",
      "heavy duty construction (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Setup and Configuration",
    "categoryType": "Performance",
    "mentions": 18,
    "positiveCount": 14,
    "negativeCount": 4,
    "totalReviews": 18,
    "satisfactionRate": 77.8,
    "negativeRate": 22.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "app cannot find device during setup",
      "difficult to program with Alexa",
      "loses setup mode during pairing",
      "Setup was a little clunky, had to repeat steps"
    ],
    "topPositiveAspects": [
      "easy and fast setup process",
      "Easy to connect to Aqara app",
      "Easy setup",
      "Easy to pair and setup",
      "easy to setup"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Humidity Detection Accuracy",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 7,
    "negativeCount": 2,
    "totalReviews": 9,
    "satisfactionRate": 77.8,
    "negativeRate": 22.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "humidity sensor never worked",
      "stops turning fan on after humidity detection failure"
    ],
    "topPositiveAspects": [
      "accurately detects humidity levels and turns fan on around 65%",
      "turns on automatically about 1-3 minutes into shower",
      "works well with default sensitivity settings",
      "no false triggering"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Setup Complexity",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 7,
    "negativeCount": 2,
    "totalReviews": 9,
    "satisfactionRate": 77.8,
    "negativeRate": 22.2,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "setup process"
    ],
    "topPositiveAspects": [
      "easy to program and set up",
      "programming instructions are easy to understand",
      "setup process"
    ],
    "topNegativeReasons": [
      "Cync app interface (2x)",
      "bulb compatibility (2x)"
    ],
    "topPositiveReasons": []
  },
  {
    "category": "Visual Design",
    "categoryType": "Physical",
    "mentions": 14,
    "positiveCount": 11,
    "negativeCount": 3,
    "totalReviews": 14,
    "satisfactionRate": 78.6,
    "negativeRate": 21.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "small border around the switch",
      "switch and accessories don't match each other",
      "Doesn't match brass cover plates"
    ],
    "topPositiveAspects": [
      "no on/off words on toggle",
      "provides modern appearance to house",
      "face plate makes the product look amazing",
      "blends seamlessly with other switches",
      "matched other switches in house perfectly"
    ],
    "topNegativeReasons": [
      "off-white or bone color rather than pure white",
      "Yellow appearance instead of gold"
    ],
    "topPositiveReasons": [
      "Gold color appearance (3x)",
      "standard white color",
      "wired up fine with no problems",
      "screw-less bezel",
      "high quality"
    ]
  },
  {
    "category": "Wireless Range",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 4,
    "negativeCount": 1,
    "totalReviews": 5,
    "satisfactionRate": 80.0,
    "negativeRate": 20.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "barely made it to house"
    ],
    "topPositiveAspects": [
      "works 200 feet away",
      "works at 150 feet",
      "excellent range",
      "works 450ft away"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "external antenna on receiver",
      "works like a charm"
    ]
  },
  {
    "category": "System Integration",
    "categoryType": "Performance",
    "mentions": 30,
    "positiveCount": 24,
    "negativeCount": 6,
    "totalReviews": 30,
    "satisfactionRate": 80.0,
    "negativeRate": 20.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Will not connect directly to HomeKit",
      "pairing is very fiddly with Smartthings",
      "unreliable connection",
      "can't connect to Canada telus Adt",
      "doesn't support Matter network"
    ],
    "topPositiveAspects": [
      "Easy to pair and setup with Home Assistant",
      "works well with Z-wave system",
      "easy to connect with z wave system",
      "integrates perfectly with Smartthings",
      "works well with HomeKit"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color Quality",
    "categoryType": "Physical",
    "mentions": 5,
    "positiveCount": 4,
    "negativeCount": 1,
    "totalReviews": 5,
    "satisfactionRate": 80.0,
    "negativeRate": 20.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "off white color rather than pure white"
    ],
    "topPositiveAspects": [
      "good color",
      "white color that matches other switches",
      "white color",
      "nice clean bright white not off white"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Integration",
    "categoryType": "Performance",
    "mentions": 39,
    "positiveCount": 32,
    "negativeCount": 7,
    "totalReviews": 39,
    "satisfactionRate": 82.1,
    "negativeRate": 17.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Google Home only recognizes one switch instead of two",
      "needs a hub or else it won't work",
      "would not connect to Alexa",
      "does not stay connected to Alexa",
      "will not work with Alexa"
    ],
    "topPositiveAspects": [
      "integrates with Alexa",
      "works with Google Home",
      "automatically connects to Alexa",
      "works with alexa and google assistant",
      "integration with google home"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Overall Reliability",
    "categoryType": "Performance",
    "mentions": 170,
    "positiveCount": 140,
    "negativeCount": 30,
    "totalReviews": 170,
    "satisfactionRate": 82.4,
    "negativeRate": 17.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "did not work (2x)",
      "only worked 10% of time initially",
      "sometimes doesn't seem to work",
      "one remote works, other doesn't",
      "sometimes works to turn on/off, other times doesn't"
    ],
    "topPositiveAspects": [
      "works as advertised (6x)",
      "works great (4x)",
      "works flawlessly (3x)",
      "Works as advertised (2x)",
      "works perfectly (2x)"
    ],
    "topNegativeReasons": [
      "burn marks appear on switch when turned on",
      "Internal relay"
    ],
    "topPositiveReasons": [
      "relay component",
      "lever action wire connection",
      "breeze to install",
      "SO easy to install"
    ]
  },
  {
    "category": "Visual Indicators",
    "categoryType": "Performance",
    "mentions": 46,
    "positiveCount": 38,
    "negativeCount": 8,
    "totalReviews": 46,
    "satisfactionRate": 82.6,
    "negativeRate": 17.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Difficult to see in daylight",
      "Provides some area illumination",
      "Difficult to determine light on/off status",
      "Not as bright as expected",
      "Too bright for bedrooms"
    ],
    "topPositiveAspects": [
      "Easy to find in dark conditions",
      "White illumination visible regardless of switch position",
      "Easy to locate switch in darkness",
      "Provides some area illumination",
      "Lights when switch is off, dims when on"
    ],
    "topNegativeReasons": [
      "Brightness level varies from very bright to extremely dim (4x)"
    ],
    "topPositiveReasons": [
      "Brightness level varies from very bright to extremely dim (18x)",
      "Easy to locate switch in darkness (18x)",
      "Two LED lights provide illumination (15x)",
      "Provides perfect amount of light (15x)",
      "White LED color instead of orange (5x)"
    ]
  },
  {
    "category": "Basic Functionality",
    "categoryType": "Performance",
    "mentions": 379,
    "positiveCount": 315,
    "negativeCount": 64,
    "totalReviews": 379,
    "satisfactionRate": 83.1,
    "negativeRate": 16.9,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "did not work at all (2x)",
      "doesn't work (2x)",
      "failed",
      "no funciona",
      "worked 50% of the time"
    ],
    "topPositiveAspects": [
      "works great (20x)",
      "works fine (12x)",
      "works as expected (10x)",
      "works perfectly (7x)",
      "works as intended (6x)"
    ],
    "topNegativeReasons": [
      "flimsy and breaks easily (2x)",
      "small print, hard to read instructions",
      "switch stays in the middle position",
      "flick down turns off lights and returns to middle",
      "not the same as the button it tries to imitate"
    ],
    "topPositiveReasons": [
      "removable tabs on both sides (3x)",
      "easy installation process (3x)",
      "Solid construction",
      "rugged design",
      "Solid construction, not flimsy"
    ]
  },
  {
    "category": "Smart Features",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 5,
    "negativeCount": 1,
    "totalReviews": 6,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "phone app is buggy"
    ],
    "topPositiveAspects": [
      "easy to connect to Smart Life app",
      "works with Smart Life app",
      "app works great",
      "IFTTT integration very responsive"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Physical Operation Feel",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 5,
    "negativeCount": 1,
    "totalReviews": 6,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "manual activation requires multiple attempts"
    ],
    "topPositiveAspects": [
      "feels right during operation",
      "positive clicks and proper positioning",
      "smooth action, not too easily toggled",
      "smooth operation"
    ],
    "topNegativeReasons": [
      "physical switch button"
    ],
    "topPositiveReasons": [
      "nice positive click (2x)"
    ]
  },
  {
    "category": "Faceplate and Cover Components",
    "categoryType": "Physical",
    "mentions": 12,
    "positiveCount": 10,
    "negativeCount": 2,
    "totalReviews": 12,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Missing plates in order",
      "face plate smaller than expected"
    ],
    "topPositiveAspects": [
      "Comes with screwless wall plate",
      "Includes the cover plate",
      "Matched light switch cover",
      "comes with cover plates",
      "cover plate good quality"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Features Setup",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 5,
    "negativeCount": 1,
    "totalReviews": 6,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "app cannot find device"
    ],
    "topPositiveAspects": [
      "easy to configure",
      "connected to app immediately without hassle",
      "very easy pairing to WiFi",
      "very easy to connect to app"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Compatibility",
    "categoryType": "Performance",
    "mentions": 12,
    "positiveCount": 10,
    "negativeCount": 2,
    "totalReviews": 12,
    "satisfactionRate": 83.3,
    "negativeRate": 16.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "does not work with generator power",
      "issues with longer wiring circuits"
    ],
    "topPositiveAspects": [
      "various wiring configurations available",
      "Works even without neutral wire",
      "works fine with mains power",
      "works with incandescent and halogen",
      "Operation without ground wire"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "light at sides/top of toggle switch from behind",
      "works fine with LED bulbs without flickering"
    ]
  },
  {
    "category": "Button and Control Interface",
    "categoryType": "Physical",
    "mentions": 20,
    "positiveCount": 17,
    "negativeCount": 3,
    "totalReviews": 20,
    "satisfactionRate": 85.0,
    "negativeRate": 15.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "physical switch button",
      "physical button that no longer moves",
      "no up switch"
    ],
    "topPositiveAspects": [
      "push button design",
      "physical button controls",
      "touch-sensitive buttons that don't physically push in",
      "nice large switches",
      "has physical switch right on unit"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Built-in Lighting",
    "categoryType": "Performance",
    "mentions": 21,
    "positiveCount": 18,
    "negativeCount": 3,
    "totalReviews": 21,
    "satisfactionRate": 85.7,
    "negativeRate": 14.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "blinding light at night",
      "doesn't work as night light",
      "night light doesn't work"
    ],
    "topPositiveAspects": [
      "makes switch visible in dark",
      "automatic night light activation",
      "LED comes on when area darkens",
      "provides adequate nightlight brightness",
      "lights up in low light conditions"
    ],
    "topNegativeReasons": [
      "light points up against wall",
      "defective switches",
      "not bright"
    ],
    "topPositiveReasons": [
      "easy to install (10x)",
      "day/night sensor (tiny hole) is sensitive (2x)"
    ]
  },
  {
    "category": "Physical Construction Quality",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 6,
    "negativeCount": 1,
    "totalReviews": 7,
    "satisfactionRate": 85.7,
    "negativeRate": 14.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "very cheap feeling switch"
    ],
    "topPositiveAspects": [
      "more sturdy than previous switch",
      "screw connectors don't break when tightening",
      "solid product",
      "high quality",
      "great quality"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "sturdy and well built",
      "all outputs function properly with no draw through when activated",
      "secure and reliable",
      "work well"
    ]
  },
  {
    "category": "Manufacturing Origin",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 6,
    "negativeCount": 1,
    "totalReviews": 7,
    "satisfactionRate": 85.7,
    "negativeRate": 14.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "made in Mexico not USA"
    ],
    "topPositiveAspects": [
      "made in USA (3x)",
      "made in Korea"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Advanced Features",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 6,
    "negativeCount": 1,
    "totalReviews": 7,
    "satisfactionRate": 85.7,
    "negativeRate": 14.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "scheduling to turn on/off at specific time doesn't work properly"
    ],
    "topPositiveAspects": [
      "Multiple connection options",
      "Draws less current than neon counterparts",
      "automation features",
      "delayed shutoff functionality",
      "auto-off timer"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Device Durability",
    "categoryType": "Performance",
    "mentions": 23,
    "positiveCount": 20,
    "negativeCount": 3,
    "totalReviews": 23,
    "satisfactionRate": 87.0,
    "negativeRate": 13.0,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "fragile",
      "Died from static electric shock",
      "switch failure after 10 years of use"
    ],
    "topPositiveAspects": [
      "durable (3x)",
      "seems like it will last",
      "durable and built to last",
      "Holding up well",
      "should work for years if not decades"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "solid build quality (3x)",
      "long-lasting reliability expected from brand (3x)",
      "heavy enough to suggest durability",
      "seems like it will last",
      "superior to other lighted switches"
    ]
  },
  {
    "category": "Power Specifications",
    "categoryType": "Physical",
    "mentions": 24,
    "positiveCount": 21,
    "negativeCount": 3,
    "totalReviews": 24,
    "satisfactionRate": 87.5,
    "negativeRate": 12.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "10 Amp capacity limitation",
      "15a current rating",
      "Actual product part number rated for 15 amps despite 20 amp advertising"
    ],
    "topPositiveAspects": [
      "20 amp rating (2x)",
      "15Amp 120V capacity",
      "rated for 15 Amp outlets",
      "current rating for LED lights considerably higher than alternatives",
      "15 amp rated"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Voice Control Integration",
    "categoryType": "Performance",
    "mentions": 26,
    "positiveCount": 23,
    "negativeCount": 3,
    "totalReviews": 26,
    "satisfactionRate": 88.5,
    "negativeRate": 11.5,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "rarely works with Alexa",
      "Alexa connection requires frequent reconnection",
      "app setup works but Alexa integration fails"
    ],
    "topPositiveAspects": [
      "works well with Alexa",
      "works well with Google Home",
      "Can turn on/off through voice command",
      "responds well to Alexa",
      "works with Alexa"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Core Functionality",
    "categoryType": "Performance",
    "mentions": 48,
    "positiveCount": 43,
    "negativeCount": 5,
    "totalReviews": 48,
    "satisfactionRate": 89.6,
    "negativeRate": 10.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Switch doesn't stay when switched",
      "Switch stays only 9 out of 10 times",
      "Light stops working after few weeks",
      "Burns out right after installation",
      "would not turn on the light despite app control working"
    ],
    "topPositiveAspects": [
      "works well (10x)",
      "Works very well (3x)",
      "Works well (3x)",
      "works very well (3x)",
      "works as expected"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "Not made of cheap flimsy materials",
      "Nice smooth click",
      "Work fine",
      "Durable switches to last a long time"
    ]
  },
  {
    "category": "Physical Build Quality",
    "categoryType": "Performance",
    "mentions": 39,
    "positiveCount": 35,
    "negativeCount": 4,
    "totalReviews": 39,
    "satisfactionRate": 89.7,
    "negativeRate": 10.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "sensitive to touch with loose parts",
      "lower quality than Leviton",
      "cheap and fragile",
      "cheap, shoddy, and dangerous"
    ],
    "topPositiveAspects": [
      "good quality (4x)",
      "very durable (2x)",
      "feel solid",
      "solidly constructed",
      "quality product"
    ],
    "topNegativeReasons": [
      "made of very delicate plastic",
      "one of switches failed after less than dozen cycles",
      "switches are very flimsy",
      "didn't last a year"
    ],
    "topPositiveReasons": [
      "solid and sturdy feel (3x)",
      "substantial feel (3x)",
      "good build quality (3x)",
      "works fine with mains power (3x)",
      "works with incandescent and halogen (3x)"
    ]
  },
  {
    "category": "Visual Appearance",
    "categoryType": "Performance",
    "mentions": 58,
    "positiveCount": 53,
    "negativeCount": 5,
    "totalReviews": 58,
    "satisfactionRate": 91.4,
    "negativeRate": 8.6,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Does not match with white wall plates",
      "not aesthetically pleasing",
      "Color difference noticeable from 10 feet away"
    ],
    "topPositiveAspects": [
      "looks great (5x)",
      "looks good (5x)",
      "Looks great (2x)",
      "nice appearance (2x)",
      "Looks identical to brand-name ones"
    ],
    "topNegativeReasons": [
      "Off-white color instead of white (3x)",
      "Tab breaks off causing switch cover to fly (3x)",
      "Mix of glossy and matte white finishes in same box",
      "Toggle cracks down the middle"
    ],
    "topPositiveReasons": [
      "available in black color (2x)",
      "works as it should (2x)",
      "sleek and modern design (2x)",
      "contemporary design",
      "minimalist style"
    ]
  },
  {
    "category": "Installation Ease",
    "categoryType": "Performance",
    "mentions": 131,
    "positiveCount": 120,
    "negativeCount": 11,
    "totalReviews": 131,
    "satisfactionRate": 91.6,
    "negativeRate": 8.4,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "makes it difficult to tie into romex",
      "hard to wire",
      "tricky to hook up lighted switch",
      "install/removal takes longer due to wire configuration",
      "not easy to install"
    ],
    "topPositiveAspects": [
      "easy to install (5x)",
      "super easy to install (2x)",
      "very easy to install (2x)",
      "easy to change out (2x)",
      "quick and easy installation"
    ],
    "topNegativeReasons": [
      "short wire length (2x)",
      "makes junction box tight (2x)",
      "extremely complex installation (2x)",
      "has 5 stranded wires with wire nuts",
      "both light and fan switches die simultaneously"
    ],
    "topPositiveReasons": [
      "levers on back to secure wires (2x)",
      "rock solid connection that withstands pulling (2x)",
      "can hook up line and load wires any way (2x)",
      "switch is intelligent enough to determine which is line and which is load (2x)",
      "super easy install (2x)"
    ]
  },
  {
    "category": "Construction Quality",
    "categoryType": "Physical",
    "mentions": 37,
    "positiveCount": 34,
    "negativeCount": 3,
    "totalReviews": 37,
    "satisfactionRate": 91.9,
    "negativeRate": 8.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "designed bend lines from fabrication",
      "plastic molded with side clips",
      "not real sturdy but good enough"
    ],
    "topPositiveAspects": [
      "well constructed (2x)",
      "Well constructed",
      "Good construction",
      "Appears to be well made",
      "solid and sturdy feel"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Electrical Wiring",
    "categoryType": "Physical",
    "mentions": 15,
    "positiveCount": 14,
    "negativeCount": 1,
    "totalReviews": 15,
    "satisfactionRate": 93.3,
    "negativeRate": 6.7,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "wiring design specifications require ingenuity for existing three-way switch"
    ],
    "topPositiveAspects": [
      "four connection wires pre-installed with plenty of slack",
      "includes neutral wire with tinned ends",
      "wire connectors are sturdy",
      "Comes with own stranded wires attached, no screw posts",
      "no neutral wire requirement"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Build Construction",
    "categoryType": "Physical",
    "mentions": 19,
    "positiveCount": 18,
    "negativeCount": 1,
    "totalReviews": 19,
    "satisfactionRate": 94.7,
    "negativeRate": 5.3,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Has gaps at the top of the switch"
    ],
    "topPositiveAspects": [
      "solidly made and not flimsy",
      "solid build construction",
      "Heavy duty construction",
      "Solid/sturdy build",
      "solidly built"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "User Interface Visibility",
    "categoryType": "Performance",
    "mentions": 39,
    "positiveCount": 37,
    "negativeCount": 2,
    "totalReviews": 39,
    "satisfactionRate": 94.9,
    "negativeRate": 5.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "difficult to tell switch position at glance",
      "Side visibility"
    ],
    "topPositiveAspects": [
      "easy to find in dark",
      "not visible during day",
      "Findability in dark conditions",
      "Easy to find in dark"
    ],
    "topNegativeReasons": [
      "light always stays on",
      "Clear switch bat material"
    ],
    "topPositiveReasons": [
      "LED light component that illuminates the switch (19x)",
      "LED produces cool white light (10x)",
      "Perfect brightness level (10x)",
      "has illuminated border/surround (7x)",
      "easy to install (7x)"
    ]
  },
  {
    "category": "Visual Aesthetics",
    "categoryType": "Physical",
    "mentions": 128,
    "positiveCount": 124,
    "negativeCount": 4,
    "totalReviews": 128,
    "satisfactionRate": 96.9,
    "negativeRate": 3.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "company name impressed into plastic",
      "look-and-feel of original Caseta dimmers",
      "Lacks metallic quality"
    ],
    "topPositiveAspects": [
      "clean look (5x)",
      "sleek design (3x)",
      "look great (2x)",
      "modern appearance (2x)",
      "Clean look (2x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Installation Process",
    "categoryType": "Performance",
    "mentions": 467,
    "positiveCount": 457,
    "negativeCount": 10,
    "totalReviews": 467,
    "satisfactionRate": 97.9,
    "negativeRate": 2.1,
    "averageRating": 3.0,
    "topNegativeAspects": [
      "Back holes don't work for hookup",
      "mounting screws strip easily in plastic boxes",
      "Difficult to push wires into place for screw down",
      "limited to 14 gauge wire, cannot accommodate 12 gauge",
      "More difficult installation than anticipated"
    ],
    "topPositiveAspects": [
      "easy to install (56x)",
      "Easy to install (15x)",
      "easy installation (10x)",
      "Easy installation (3x)",
      "easy to wire (2x)"
    ],
    "topNegativeReasons": [
      "Has holes on the back for hookup",
      "cheap mounting screws that strip easily",
      "lighter weight screws with low quality metal",
      "accepts 14 gauge wire only",
      "too small for 12 gauge wire"
    ],
    "topPositiveReasons": [
      "easy to install (15x)",
      "wires are easy to terminate (10x)",
      "press-in connections are really nice (9x)",
      "easy to install terminals (9x)",
      "1 gang standard size matching US household switches (7x)"
    ]
  },
  {
    "category": "Touch Interface",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "light touch feature that elevates the product"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Purchase Value",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 8,
    "negativeCount": 0,
    "totalReviews": 8,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "great value (2x)",
      "good value for money (2x)",
      "worth the money",
      "worth the price",
      "good value"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "high quality material (2x)",
      "easy to install (2x)",
      "nice feeling switch",
      "good value for money"
    ]
  },
  {
    "category": "Product Value",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "inexpensive",
      "excellent for the value"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "solidly built",
      "flip up to turn on and down to turn off"
    ]
  },
  {
    "category": "Color Options",
    "categoryType": "Physical",
    "mentions": 7,
    "positiveCount": 7,
    "negativeCount": 0,
    "totalReviews": 7,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "white color (3x)"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Circuit Configuration Support",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 5,
    "negativeCount": 0,
    "totalReviews": 5,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "can be used as 3 way as well as 4 way",
      "can be used for 2 way and 4 way",
      "can be used as single pole or 4 way",
      "Can be installed as single pole or 3-way"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Product Certification",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 3,
    "negativeCount": 0,
    "totalReviews": 3,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "meets CSA",
      "UL certified"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Noise Level",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "quiet operation"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Color and Finish Quality",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "nice finish"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi-Switch Configuration",
    "categoryType": "Physical",
    "mentions": 3,
    "positiveCount": 3,
    "negativeCount": 0,
    "totalReviews": 3,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "dual switches in single gang box",
      "two switches in the space of one"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Timer Operation",
    "categoryType": "Performance",
    "mentions": 6,
    "positiveCount": 6,
    "negativeCount": 0,
    "totalReviews": 6,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "automatically shuts off after programmed duration (20 minutes default)",
      "re-senses after 20 mins and runs additional 10 mins if needed",
      "can be set to run for time each hour to keep air fresh"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Terminal Design",
    "categoryType": "Physical",
    "mentions": 4,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "screw terminals with clamp down style",
      "multiple wire entries at each terminal",
      "all connections via screw terminals",
      "no wire leads from switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Switch Plate Design",
    "categoryType": "Physical",
    "mentions": 16,
    "positiveCount": 16,
    "negativeCount": 0,
    "totalReviews": 16,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "paddle rocker design",
      "paddle design is smooth",
      "paddle design matches existing switches",
      "toggle design with clean look",
      "modern looking paddle/rocker design"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Basic Operation",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Maintains light switch functionality as before",
      "flips on and off flawlessly"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Design Flexibility",
    "categoryType": "Performance",
    "mentions": 7,
    "positiveCount": 7,
    "negativeCount": 0,
    "totalReviews": 7,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Saves space where you need two switches",
      "can be used as single pole, 3 way, or 4 way switch",
      "portable switch is easily removed and replaced from wall mounted back plate",
      "remote is removable from switch plate",
      "can operate on wall or as switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "Well constructed",
      "Nice positive snap when it turns on and off"
    ]
  },
  {
    "category": "Advanced Configuration Options",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "allows setting maximum and minimum light intensity"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Specialized Controls",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "has two sensitivity settings",
      "can adjust noise sensitivity to high or low"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Value Proposition",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "provides great value for money"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Smart Device Pairing",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "worked right away without need to pair",
      "easy pairing - paired within seconds"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi Way Configuration",
    "categoryType": "Performance",
    "mentions": 5,
    "positiveCount": 5,
    "negativeCount": 0,
    "totalReviews": 5,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Works as advertised for 3-way switching"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Timer Functionality",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "has timer function"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Touchscreen Interface",
    "categoryType": "Physical",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "LCD touchscreen",
      "touch screen functionality"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Customization Options",
    "categoryType": "Performance",
    "mentions": 4,
    "positiveCount": 4,
    "negativeCount": 0,
    "totalReviews": 4,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "has lot of features that can be customized",
      "interface lighting and customization",
      "customization is easy",
      "fun to change the buttons"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "touch screen functionality",
      "needs router to be on 2.4 GHz for stable connection"
    ]
  },
  {
    "category": "Touch Interface Responsiveness",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "great touch response with no issues after nearly a year"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "LCD touchscreen"
    ]
  },
  {
    "category": "Initial Setup",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "initial setup is fast",
      "setup was not hard"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Manufacturing Consistency",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "consistent quality across multiple units"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "well made construction",
      "consistent quality across multiple units"
    ]
  },
  {
    "category": "Firmware Management",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "updateable"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi-Way Switching",
    "categoryType": "Performance",
    "mentions": 8,
    "positiveCount": 8,
    "negativeCount": 0,
    "totalReviews": 8,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "3 way works fine",
      "works as 3-way switch"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Illumination Features",
    "categoryType": "Physical",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "has indicator light"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Structural Durability",
    "categoryType": "Physical",
    "mentions": 11,
    "positiveCount": 11,
    "negativeCount": 0,
    "totalReviews": 11,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "well put together",
      "feels like good quality",
      "hefty and durable feeling",
      "rugged design",
      "sturdy build quality"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Network Integration",
    "categoryType": "Performance",
    "mentions": 9,
    "positiveCount": 9,
    "negativeCount": 0,
    "totalReviews": 9,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Alexa integration not too difficult",
      "easy setup with Alexa",
      "seamless app connectivity"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Dimming Control Performance",
    "categoryType": "Performance",
    "mentions": 2,
    "positiveCount": 2,
    "negativeCount": 0,
    "totalReviews": 2,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "Dims well",
      "Great dimming performance"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Multi-Circuit Control",
    "categoryType": "Performance",
    "mentions": 3,
    "positiveCount": 3,
    "negativeCount": 0,
    "totalReviews": 3,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "allows control of two separate circuits"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": [
      "space-saving design that fits two 3-way switches in one gang box (3x)",
      "works perfectly as intended (3x)"
    ]
  },
  {
    "category": "Heat Generation",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "won't get warm"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  },
  {
    "category": "Operational Noise Levels",
    "categoryType": "Performance",
    "mentions": 1,
    "positiveCount": 1,
    "negativeCount": 0,
    "totalReviews": 1,
    "satisfactionRate": 100.0,
    "negativeRate": 0.0,
    "averageRating": 3.0,
    "topNegativeAspects": [],
    "topPositiveAspects": [
      "quiet operating"
    ],
    "topNegativeReasons": [],
    "topPositiveReasons": []
  }
];

// Utility Functions
export function getCategoryFeedback(productType: ProductType = 'dimmer'): CategoryFeedbackData {
  if (productType === 'dimmer') {
    return {
      summary: dimmerSwitchesSummary,
      topNegativeCategories: topNegativeDimmerCategories,
      topPositiveCategories: topPositiveDimmerCategories,
      topUseCases: topUseCasesDimmer,
      allCategories: allDimmerCategories
    };
  } else {
    return {
      summary: lightSwitchesSummary,
      topNegativeCategories: topNegativeLightCategories,
      topPositiveCategories: topPositiveLightCategories,
      topUseCases: topUseCasesLight,
      allCategories: allLightCategories
    };
  }
}

export function getTopNegativeCategories(productType: ProductType = 'dimmer', limit: number = 10): CategoryFeedback[] {
  const data = getCategoryFeedback(productType);
  return data.topNegativeCategories.slice(0, limit);
}

export function getTopPositiveCategories(productType: ProductType = 'dimmer', limit: number = 10): CategoryFeedback[] {
  const data = getCategoryFeedback(productType);
  return data.topPositiveCategories.slice(0, limit);
}

export function getTopUseCases(productType: ProductType = 'dimmer', limit: number = 10): UseCaseFeedback[] {
  const data = getCategoryFeedback(productType);
  return data.topUseCases.slice(0, limit);
}

export function getCategoriesByType(categoryType: 'Physical' | 'Performance', productType: ProductType = 'dimmer'): CategoryFeedback[] {
  const data = getCategoryFeedback(productType);
  return data.allCategories.filter(cat => cat.categoryType === categoryType);
}

export function getAvailableProductTypes(): { value: ProductType; label: string }[] {
  return [
    { value: 'dimmer', label: 'Dimmer Switches' },
    { value: 'light', label: 'Light Switches' }
  ];
}
